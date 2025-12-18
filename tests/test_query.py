"""
Simple test script to verify the query functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

from models.query import QueryRequest
from services.rag_service import rag_service

def test_query_functionality():
    """Test the RAG query functionality with sample data"""
    print("Testing RAG query functionality...")

    # Sample query request
    query_request = QueryRequest(
        query="What is ROS 2?",
        selected_text="",
        session_id="test-session-123"
    )

    print(f"Query: {query_request.query}")

    # Process the query
    response = rag_service.query_documentation(query_request)

    print(f"Response: {response.answer[:200]}...")  # First 200 chars
    print(f"Number of citations: {len(response.citations)}")
    print(f"Query ID: {response.query_id}")
    print(f"Timestamp: {response.timestamp}")

    if response.citations:
        print("Sample citation:")
        first_citation = response.citations[0]
        print(f"  Document ID: {first_citation.document_id}")
        print(f"  Title: {first_citation.title}")
        print(f"  URL: {first_citation.url}")
        print(f"  Relevance: {first_citation.relevance_score}")

    print("Query functionality test completed!")

if __name__ == "__main__":
    test_query_functionality()