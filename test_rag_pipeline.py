import unittest
from unittest.mock import patch, MagicMock
import os
from main import get_all_urls, extract_text_from_url, chunk_text, embed, create_collection, save_chunk_to_qdrant, DocumentChunk


class TestRAGPipeline(unittest.TestCase):

    def test_chunk_text_basic(self):
        """Test basic text chunking functionality"""
        text = "This is a sample text for testing. " * 10  # Create a longer text
        chunks = chunk_text(text, chunk_size=10, overlap=2)

        self.assertGreater(len(chunks), 0, "Should create at least one chunk")
        for chunk in chunks:
            self.assertIsInstance(chunk, DocumentChunk)
            self.assertGreater(len(chunk.content), 0, "Chunk content should not be empty")

    def test_chunk_text_empty(self):
        """Test chunking with empty text"""
        chunks = chunk_text("")
        self.assertEqual(len(chunks), 0, "Should return empty list for empty text")

    def test_document_chunk_creation(self):
        """Test DocumentChunk creation"""
        chunk = DocumentChunk(
            content="Test content",
            source_url="https://example.com",
            chunk_id="test-id",
            position=0,
            metadata={"test": "value"}
        )

        self.assertEqual(chunk.content, "Test content")
        self.assertEqual(chunk.source_url, "https://example.com")
        self.assertEqual(chunk.chunk_id, "test-id")
        self.assertEqual(chunk.position, 0)
        self.assertEqual(chunk.metadata["test"], "value")


if __name__ == '__main__':
    # Only run tests if environment variables are properly set
    if os.getenv("COHERE_API_KEY") and os.getenv("QDRANT_URL") and os.getenv("QDRANT_API_KEY"):
        unittest.main()
    else:
        print("Environment variables not set, running limited tests...")
        suite = unittest.TestSuite()
        suite.addTest(TestRAGPipeline('test_chunk_text_basic'))
        suite.addTest(TestRAGPipeline('test_chunk_text_empty'))
        suite.addTest(TestRAGPipeline('test_document_chunk_creation'))
        runner = unittest.TextTestRunner()
        runner.run(suite)