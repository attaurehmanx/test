from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from config.settings import settings
from models.query import QueryRequest, QueryResponse, Citation
from services.qdrant_service import qdrant_service
from services.agent_service import agent_service
from utils.response_quality import response_quality_metrics
from utils.cache import cache
import openai  # For embedding generation

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # Initialize the required services
        self.qdrant_service = qdrant_service
        self.agent_service = agent_service
        self.openai_client = None
        self.cohere_client = None

        # Try to initialize Cohere client first (as used in retrieve.py)
        if settings.cohere_api_key:
            try:
                import cohere
                self.cohere_client = cohere.Client(settings.cohere_api_key)
                logger.info("Cohere client initialized for embeddings")
            except ImportError:
                logger.warning("Cohere library not installed, falling back to other embedding methods")

        # Initialize OpenAI client for embeddings using Gemini API via OpenAI-compatible endpoint as fallback
        if not self.cohere_client:
            gemini_api_key = getattr(settings, 'gemini_api_key', None) or getattr(settings, 'openai_api_key', None)
            if gemini_api_key:
                self.openai_client = openai.OpenAI(
                    api_key=gemini_api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                logger.info("OpenAI client initialized for embeddings via Gemini endpoint")

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for the given text using Cohere first, then fallback to OpenAI-compatible endpoint"""
        # Try Cohere first (as used in retrieve.py)
        if self.cohere_client:
            try:
                response = self.cohere_client.embed(
                    texts=[text],
                    model="embed-english-v3.0",  # Using Cohere's latest embedding model
                    input_type="search_query"
                )
                return response.embeddings[0]
            except Exception as e:
                logger.error(f"Error generating embedding with Cohere: {e}")
                # Continue to try other methods

        # Try OpenAI-compatible endpoint with Gemini
        if self.openai_client:
            try:
                response = self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-004"  # Use Google's embedding model via OpenAI-compatible endpoint
                )
                return response.data[0].embedding
            except Exception as e:
                logger.error(f"Error generating embedding with OpenAI-compatible endpoint: {e}")

        # Fallback to mock embedding
        logger.warning("No embedding client available, using mock embedding")
        # Qdrant expects 1024 dimensions based on the error, so return that size
        return [0.0] * 1024  # Size expected by Qdrant

    def validate_citation_links(self, citations: List[Citation]) -> List[Citation]:
        """Validate citation links and clean up any invalid ones"""
        validated_citations = []
        for citation in citations:
            # Basic validation for URL format
            if citation.url and (citation.url.startswith('http') or citation.url.startswith('/')):
                validated_citations.append(citation)
            else:
                logger.warning(f"Invalid URL in citation: {citation.url}")
        return validated_citations

    def enhance_citation_relevance(self, citations: List[Citation], query: str) -> List[Citation]:
        """Enhance citation relevance by potentially re-ranking based on query"""
        # For now, we'll just return the citations as is
        # In a more advanced implementation, we could re-rank based on semantic similarity
        # to the original query
        return citations

    def query_documentation(self, query_request: QueryRequest) -> QueryResponse:
        """
        Main method to process a query request and return a response with citations
        """
        # Record start time for metrics
        start_time = response_quality_metrics.log_query_start()

        try:
            # Check cache first
            cached_response = cache.get(query_request.query, query_request.selected_text)
            if cached_response:
                logger.info("Returning cached response")
                # Update the response with fresh timestamp and new query ID
                cached_response["query_id"] = str(uuid.uuid4())
                cached_response["timestamp"] = datetime.utcnow().isoformat() + "Z"

                response = QueryResponse(**cached_response)
                response_quality_metrics.log_query_end(start_time, success=True, response=response)
                return response

            # Generate embedding for the query
            query_text = query_request.query
            if query_request.selected_text:
                # Combine query with selected text if provided
                query_text = f"{query_request.selected_text} {query_request.query}"

            query_embedding = self.generate_embedding(query_text)
            if not query_embedding:
                raise Exception("Failed to generate query embedding")

            # Search for relevant documents in Qdrant
            relevant_docs = self.qdrant_service.search_documents(
                query_vector=query_embedding,
                limit=5  # Get top 5 most relevant documents
            )

            # If no relevant documents found, return appropriate response
            if not relevant_docs:
                logger.info("No relevant documents found for query")
                response = QueryResponse(
                    answer="I couldn't find any relevant documents to answer your question.",
                    citations=[],
                    query_id=str(uuid.uuid4()),
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )
                # Log the failed query
                response_quality_metrics.log_query_end(start_time, success=False, response=response)
                return response

            # Generate response using the agent with retrieved context
            agent_response = self.agent_service.generate_response(
                query=query_request.query,
                context=relevant_docs,
                selected_text=query_request.selected_text
            )

            # Create citations from the retrieved documents
            raw_citations = []
            for doc in relevant_docs:
                citation = Citation(
                    document_id=doc.get("document_id", ""),
                    title=doc.get("title", ""),
                    url=doc.get("url", ""),
                    text_snippet=doc.get("text_snippet", "")[:500],  # Limit snippet length
                    relevance_score=doc.get("relevance_score", 0.0)
                )
                raw_citations.append(citation)

            # Enhance citation relevance and validate links
            enhanced_citations = self.enhance_citation_relevance(raw_citations, query_request.query)
            validated_citations = self.validate_citation_links(enhanced_citations)

            # Generate unique query ID
            query_id = str(uuid.uuid4())

            # Create and return the response
            response = QueryResponse(
                answer=agent_response["answer"],
                citations=validated_citations,
                query_id=query_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                metadata=agent_response.get("metadata", {})
            )

            # Validate response accuracy against source context
            validation_result = response_quality_metrics.validate_response_accuracy(response, relevant_docs)

            # Cache the response (only cache responses that have content)
            if response.answer and len(response.answer.strip()) > 0:
                cache.set(
                    query_request.query,
                    response.model_dump(),
                    query_request.selected_text,
                    ttl=7200  # Cache for 2 hours
                )

            logger.info(f"Successfully processed query {query_id}")

            # Log the successful query with metrics
            response_quality_metrics.log_query_end(start_time, success=True, response=response)

            return response

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            # Create error response
            error_response = QueryResponse(
                answer="Sorry, I encountered an error while processing your request.",
                citations=[],
                query_id=str(uuid.uuid4()),
                timestamp=datetime.utcnow().isoformat() + "Z",
                metadata={"error": str(e)}
            )
            # Log the failed query
            response_quality_metrics.log_query_end(start_time, success=False, response=error_response)
            return error_response

    def add_document_to_index(self, content: str, title: str, url: str,
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a document to the Qdrant index"""
        try:
            # Generate embedding for the document content
            embedding = self.generate_embedding(content)
            if not embedding:
                logger.error("Failed to generate embedding for document")
                return False

            # Generate document ID
            doc_id = str(uuid.uuid4())

            # Add to Qdrant
            success = self.qdrant_service.add_document(
                document_id=doc_id,
                content=content,
                title=title,
                url=url,
                embedding=embedding,
                metadata=metadata
            )

            if success:
                logger.info(f"Successfully added document {doc_id} to index")
            else:
                logger.error(f"Failed to add document {doc_id} to index")

            return success
        except Exception as e:
            logger.error(f"Error adding document to index: {e}")
            return False

# Create a singleton instance
rag_service = RAGService()