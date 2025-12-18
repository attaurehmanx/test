from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, VectorParams, Distance
from typing import List, Optional, Dict, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class QdrantService:
    def __init__(self):
        # Initialize Qdrant client with settings
        try:
            if settings.qdrant_url:
                # Use cloud instance with URL
                self.client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                    https=True
                )
                logger.info(f"Connected to Qdrant cloud instance at {settings.qdrant_url}")
            else:
                # Use local instance
                self.client = QdrantClient(
                    host=settings.qdrant_host,
                    port=settings.qdrant_port,
                    https=settings.qdrant_https
                )
                logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise

        self.collection_name = settings.collection_name
        self.vector_size = 1536  # Standard size for OpenAI embeddings; adjust as needed
        self.distance = Distance.COSINE

    def create_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]

            if self.collection_name not in collection_names:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=self.vector_size, distance=self.distance)
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection {self.collection_name} already exists")
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            raise

    def search_documents(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """Search for documents similar to the query vector"""
        try:
            # Perform similarity search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )

            # Extract and format results
            results = []
            for hit in search_results:
                result = {
                    "document_id": hit.id,
                    "content": hit.payload.get("content", ""),
                    "title": hit.payload.get("title", ""),
                    "url": hit.payload.get("url", ""),
                    "text_snippet": hit.payload.get("content", "")[:500],  # First 500 chars as snippet
                    "relevance_score": float(hit.score),
                    "metadata": hit.payload.get("metadata", {})
                }
                results.append(result)

            logger.info(f"Found {len(results)} documents for query")
            return results
        except Exception as e:
            logger.error(f"Error searching documents in Qdrant: {e}")
            # Return empty list instead of raising exception to allow graceful degradation
            return []

    def add_document(self, document_id: str, content: str, title: str, url: str,
                     embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a document to the Qdrant collection"""
        try:
            # Prepare payload
            payload = {
                "content": content,
                "title": title,
                "url": url,
                "metadata": metadata or {}
            }

            # Add point to collection
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=document_id,
                        vector=embedding,
                        payload=payload
                    )
                ]
            )

            logger.info(f"Added document {document_id} to Qdrant")
            return True
        except Exception as e:
            logger.error(f"Error adding document {document_id} to Qdrant: {e}")
            return False

    def batch_add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add multiple documents to the Qdrant collection"""
        try:
            points = []
            for doc in documents:
                point = PointStruct(
                    id=doc["document_id"],
                    vector=doc["embedding"],
                    payload={
                        "content": doc["content"],
                        "title": doc["title"],
                        "url": doc["url"],
                        "metadata": doc.get("metadata", {})
                    }
                )
                points.append(point)

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

            logger.info(f"Added {len(documents)} documents to Qdrant in batch")
            return True
        except Exception as e:
            logger.error(f"Error adding documents to Qdrant in batch: {e}")
            return False

    def delete_collection(self):
        """Delete the collection (useful for testing/resetting)"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting Qdrant collection: {e}")
            raise

# Create a singleton instance
qdrant_service = QdrantService()