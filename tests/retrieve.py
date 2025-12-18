"""
RAG Pipeline Validation - Retrieval & Validation Module

This module provides functionality to:
- Load existing Qdrant collection and schema
- Embed user queries using Cohere
- Perform similarity search with optional metadata filters
- Inspect and log retrieved chunks and scores
- Validate retrieval accuracy with test queries
"""

import os
import logging
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import cohere
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class QueryRequest:
    """Data class for query request"""
    query_text: str
    filters: Optional[Dict] = None
    top_k: int = 5


@dataclass
class RetrievedChunk:
    """Data class for retrieved content chunk"""
    content: str
    id: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class RetrievalResult:
    """Data class for retrieval results"""
    query: QueryRequest
    results: List[RetrievedChunk]
    search_time_ms: float
    total_candidates: int
    validated: bool = False


@dataclass
class ValidationResult:
    """Data class for validation results"""
    test_name: str
    query: str
    expected_results: List[str]
    actual_results: List[RetrievedChunk]
    precision: float
    recall: float
    success: bool


class RAGValidator:
    """Main class for RAG pipeline validation"""

    def __init__(self):
        # Initialize Cohere client
        self.cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

        # Initialize Qdrant client - handle both cloud and local instances
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_host = os.getenv("QDRANT_HOST")
        qdrant_port = os.getenv("QDRANT_PORT")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")

        if qdrant_url:
            # Use cloud instance
            self.qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                https=True
            )
        else:
            # Use local instance
            self.qdrant_client = QdrantClient(
                host=qdrant_host or "localhost",
                port=int(qdrant_port or 6333)
            )

        # Get collection name from environment
        self.collection_name = os.getenv("COLLECTION_NAME")

        if not self.collection_name:
            # Try to get the first available collection if not specified
            collections = self.qdrant_client.get_collections()
            if collections.collections:
                self.collection_name = collections.collections[0].name
                logger.info(f"Using first available collection: {self.collection_name}")
            else:
                raise ValueError("No collection found in Qdrant and COLLECTION_NAME not set")

        logger.info(f"Initialized RAGValidator for collection: {self.collection_name}")

    def load_collection_schema(self) -> Dict[str, Any]:
        """Load and return the schema of the existing Qdrant collection"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            return {
                "name": collection_info.config.params.vectors.size,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance,
                "count": collection_info.points_count
            }
        except Exception as e:
            logger.error(f"Error loading collection schema: {e}")
            raise

    def embed_query(self, query_text: str) -> List[float]:
        """Embed the query text using Cohere"""
        try:
            response = self.cohere_client.embed(
                texts=[query_text],
                model="embed-english-v3.0",  # Using Cohere's latest embedding model
                input_type="search_query"
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

    def _convert_filters_to_qdrant(self, filters: Optional[Dict]) -> Optional[models.Filter]:
        """Convert simple dict filters to Qdrant filter format"""
        if not filters:
            return None

        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
            elif isinstance(value, list):
                # Handle list of values (OR condition)
                or_conditions = [
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=v)
                    ) for v in value
                ]
                conditions.append(models.Should(conditions=or_conditions))
            else:
                # Handle other types
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=str(value))
                    )
                )

        if conditions:
            return models.Filter(must=conditions)
        return None

    def retrieve(self, query_request: QueryRequest) -> RetrievalResult:
        """Perform semantic retrieval from Qdrant"""
        start_time = time.time()

        try:
            # Embed the query
            query_vector = self.embed_query(query_request.query_text)

            # Convert filters to Qdrant format
            qdrant_filters = self._convert_filters_to_qdrant(query_request.filters)

            # Perform search using search method (compatible with older Qdrant client versions)
            search_results = self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filters,
                limit=query_request.top_k,
                with_payload=True,
                with_vectors=False
            )

            # Convert results to our format
            retrieved_chunks = []
            for result in search_results:  # For older search method, iterate directly
                chunk = RetrievedChunk(
                    content=result.payload.get("content", "") if result.payload else "",
                    id=str(result.id),
                    score=result.score if result.score else 0.0,  # Score might be None for exact matches
                    metadata=result.payload if result.payload else {}
                )
                retrieved_chunks.append(chunk)

            # Calculate search time
            search_time = (time.time() - start_time) * 1000  # Convert to milliseconds

            # Get total candidate count
            total_candidates = self.qdrant_client.count(
                collection_name=self.collection_name,
                count_filter=qdrant_filters
            ).count

            logger.info(f"Retrieved {len(retrieved_chunks)} results in {search_time:.2f}ms")

            return RetrievalResult(
                query=query_request,
                results=retrieved_chunks,
                search_time_ms=search_time,
                total_candidates=total_candidates
            )

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            raise

    def inspect_results(self, retrieval_result: RetrievalResult) -> None:
        """Inspect and log retrieved chunks and scores"""
        logger.info(f"Query: {retrieval_result.query.query_text}")
        logger.info(f"Retrieved {len(retrieval_result.results)} results:")

        for i, chunk in enumerate(retrieval_result.results):
            logger.info(f"  {i+1}. Score: {chunk.score:.3f}, ID: {chunk.id}")
            logger.info(f"     Content preview: {chunk.content[:100]}...")
            logger.info(f"     Metadata: {chunk.metadata}")

    def validate_retrieval_accuracy(self, test_queries: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate retrieval accuracy with test queries"""
        validation_results = []

        for test_query in test_queries:
            query_text = test_query["query"]
            expected_content = test_query["expected_content"]
            filters = test_query.get("filters", None)
            top_k = test_query.get("top_k", 5)

            # Perform retrieval
            query_req = QueryRequest(query_text=query_text, filters=filters, top_k=top_k)
            retrieval_result = self.retrieve(query_req)

            # Calculate precision and recall
            relevant_retrieved = 0
            total_retrieved = len(retrieval_result.results)

            for chunk in retrieval_result.results:
                # Check if any expected content appears in the retrieved chunk
                for expected in expected_content:
                    if expected.lower() in chunk.content.lower():
                        relevant_retrieved += 1
                        break

            # Calculate precision
            precision = relevant_retrieved / total_retrieved if total_retrieved > 0 else 0

            # Calculate recall (how many relevant items were retrieved out of all relevant items)
            # For simplicity, we'll consider this as the ratio of relevant items retrieved
            recall = relevant_retrieved / len(expected_content) if len(expected_content) > 0 else 0

            # Determine success based on thresholds (85% precision as per spec)
            success = precision >= 0.85

            validation_result = ValidationResult(
                test_name=f"accuracy_test_{query_text[:20]}",
                query=query_text,
                expected_results=expected_content,
                actual_results=retrieval_result.results,
                precision=precision,
                recall=recall,
                success=success
            )

            validation_results.append(validation_result)

            logger.info(f"Validation for '{query_text[:30]}...': Precision={precision:.2f}, Recall={recall:.2f}, Success={success}")

        return validation_results

    def run_pipeline_validation(self) -> Dict[str, Any]:
        """Run comprehensive pipeline validation"""
        logger.info("Starting pipeline validation...")

        # Load collection schema
        schema = self.load_collection_schema()
        logger.info(f"Collection schema: {schema}")

        # Run accuracy tests
        test_queries = [
            {
                "query": "What is the ROS 2 architecture?",
                "expected_content": ["ROS 2", "DDS", "middleware", "nodes"],
                "top_k": 5
            },
            {
                "query": "Explain Gazebo simulation environment",
                "expected_content": ["Gazebo", "simulation", "physics", "robot"],
                "top_k": 5
            },
            {
                "query": "How does NVIDIA Isaac work?",
                "expected_content": ["Isaac", "NVIDIA", "AI", "robotics"],
                "top_k": 5
            }
        ]

        validation_results = self.validate_retrieval_accuracy(test_queries)

        # Calculate overall metrics
        total_tests = len(validation_results)
        successful_tests = sum(1 for vr in validation_results if vr.success)
        avg_precision = sum(vr.precision for vr in validation_results) / total_tests if total_tests > 0 else 0
        avg_recall = sum(vr.recall for vr in validation_results) / total_tests if total_tests > 0 else 0

        overall_success = successful_tests / total_tests >= 0.8  # 80% of tests should pass

        results = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "overall_success": overall_success,
            "validation_results": validation_results
        }

        logger.info(f"Pipeline validation complete: {results['success_rate']:.2%} success rate")
        return results


def main():
    """Main function to demonstrate usage"""
    import argparse

    parser = argparse.ArgumentParser(description="RAG Pipeline Validation Tool")
    parser.add_argument("--query", type=str, help="Query to test retrieval")
    parser.add_argument("--validate", action="store_true", help="Run validation tests")
    parser.add_argument("--filters", type=str, help="JSON string of filters")

    args = parser.parse_args()

    # Initialize validator
    validator = RAGValidator()

    if args.validate:
        # Run comprehensive validation
        results = validator.run_pipeline_validation()

        print(f"\nPipeline Validation Results:")
        print(f"Success Rate: {results['success_rate']:.2%}")
        print(f"Average Precision: {results['avg_precision']:.2f}")
        print(f"Average Recall: {results['avg_recall']:.2f}")
        print(f"Overall Success: {results['overall_success']}")

    elif args.query:
        # Parse filters if provided
        filters = None
        if args.filters:
            import json
            filters = json.loads(args.filters)

        # Create query request
        query_req = QueryRequest(query_text=args.query, filters=filters)

        # Perform retrieval
        result = validator.retrieve(query_req)

        # Inspect results
        validator.inspect_results(result)

    else:
        print("Please specify either --query or --validate")


if __name__ == "__main__":
    main()