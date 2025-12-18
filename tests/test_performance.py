"""
Performance test script to verify response time targets
"""
import asyncio
import time
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

from models.query import QueryRequest
from services.rag_service import rag_service

def test_response_performance():
    """Test that responses meet the < 5 seconds target"""
    print("Testing response performance...")

    # Sample query request
    query_request = QueryRequest(
        query="What is the purpose of ROS 2?",
        selected_text="",
        session_id="perf-test-session"
    )

    print(f"Query: {query_request.query}")

    # Time the query processing
    start_time = time.time()
    response = rag_service.query_documentation(query_request)
    end_time = time.time()

    response_time = end_time - start_time

    print(f"Response time: {response_time:.3f}s")
    print(f"Response length: {len(response.answer)} characters")
    print(f"Number of citations: {len(response.citations)}")

    # Check if response time is under the target
    target_time = 5.0  # 5 seconds
    if response_time < target_time:
        print(f"✅ Performance target met: {response_time:.3f}s < {target_time}s")
    else:
        print(f"❌ Performance target missed: {response_time:.3f}s >= {target_time}s")

    # Additional performance metrics
    print(f"Response per second potential: {1.0/response_time:.2f} RPS")

    return response_time < target_time

def test_caching_performance():
    """Test performance improvement with caching"""
    print("\nTesting caching performance improvement...")

    query_request = QueryRequest(
        query="What are ROS 2 parameters?",
        selected_text="",
        session_id="cache-test-session"
    )

    # First request (not cached)
    start_time = time.time()
    response1 = rag_service.query_documentation(query_request)
    first_response_time = time.time() - start_time

    # Second request (should be cached)
    start_time = time.time()
    response2 = rag_service.query_documentation(query_request)
    second_response_time = time.time() - start_time

    print(f"First request (uncached): {first_response_time:.3f}s")
    print(f"Second request (cached): {second_response_time:.3f}s")
    print(f"Speedup: {first_response_time/second_response_time:.2f}x faster")

    if second_response_time < first_response_time:
        print("✅ Caching provides performance improvement")
    else:
        print("⚠️  Caching may not be providing expected performance improvement")

    return second_response_time < first_response_time

if __name__ == "__main__":
    success1 = test_response_performance()
    success2 = test_caching_performance()

    print(f"\nPerformance testing completed!")
    print(f"Basic performance target: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Caching improvement: {'✅ PASS' if success2 else '⚠️  INFO'}")