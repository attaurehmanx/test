"""
Test script for response quality and caching functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

from utils.response_quality import response_quality_metrics
from utils.cache import cache
from models.query import QueryResponse, Citation
import time

def test_response_quality_metrics():
    """Test response quality metrics functionality"""
    print("Testing response quality metrics...")

    # Reset metrics first
    response_quality_metrics.reset_metrics()

    # Simulate some queries
    for i in range(5):
        start_time = response_quality_metrics.log_query_start()
        # Simulate a successful query
        time.sleep(0.1)  # Simulate processing time
        response = QueryResponse(
            answer=f"Response to query {i}",
            citations=[Citation(
                document_id=f"doc_{i}",
                title="Test Document",
                url="/test",
                text_snippet="Test snippet",
                relevance_score=0.8
            )],
            query_id=f"query_{i}",
            timestamp="2025-12-15T10:30:00.000Z"
        )
        response_quality_metrics.log_query_end(start_time, success=True, response=response)

    # Test a failed query
    start_time = response_quality_metrics.log_query_end(time.time(), success=False)

    # Get metrics
    metrics = response_quality_metrics.get_metrics()
    print(f"Total queries: {metrics['total_queries']}")
    print(f"Successful queries: {metrics['successful_queries']}")
    print(f"Failed queries: {metrics['failed_queries']}")
    print(f"Avg response time: {metrics['avg_response_time']:.3f}s")
    print(f"Avg citations per response: {metrics['avg_citations_per_response']:.2f}")

    print("Response quality metrics test completed!")


def test_caching():
    """Test caching functionality"""
    print("\nTesting caching functionality...")

    # Test cache set
    test_query = "What is ROS 2?"
    test_response = {
        "answer": "ROS 2 is a flexible framework for writing robot software",
        "citations": [{
            "document_id": "doc_ros2_intro",
            "title": "ROS 2 Introduction",
            "url": "/docs/ros2/intro",
            "text_snippet": "ROS 2 is designed for...",
            "relevance_score": 0.95
        }],
        "query_id": "test-query-123",
        "timestamp": "2025-12-15T10:30:00.000Z"
    }

    print(f"Cache size before set: {cache.size()}")
    cache.set(test_query, "", test_response)
    print(f"Cache size after set: {cache.size()}")

    # Test cache get
    cached_result = cache.get(test_query, "")
    print(f"Cached result retrieved: {cached_result is not None}")
    if cached_result:
        print(f"Answer: {cached_result['answer'][:50]}...")

    # Test cache miss
    miss_result = cache.get("non-existent query", "")
    print(f"Cache miss result: {miss_result is None}")

    # Test cache cleanup
    cache.set("expired_query", "", test_response, ttl=1)  # 1 second TTL
    print(f"Cache size after adding expired item: {cache.size()}")
    time.sleep(2)  # Wait for item to expire
    removed_count = cache.cleanup_expired()
    print(f"Expired items removed: {removed_count}")
    print(f"Cache size after cleanup: {cache.size()}")

    print("Caching test completed!")


if __name__ == "__main__":
    test_response_quality_metrics()
    test_caching()
    print("\nResponse quality and caching testing completed!")