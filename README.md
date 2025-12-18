# RAG Agent - Retrieval-Augmented Generation with Google Gemini and Qdrant

This project implements a RAG (Retrieval-Augmented Generation) agent that retrieves relevant content from a Qdrant vector database and uses it as context to answer user questions about book content.

## Features

- **Google Gemini Integration**: Uses Google's Gemini API via OpenAI-compatible endpoint for response generation
- **Google Embedding API**: Uses Google's embedding API via OpenAI-compatible endpoint for vector generation
- **Qdrant Vector Database**: Efficient similarity search in vector space
- **Configurable Retrieval**: Adjustable parameters for top-k results and similarity thresholds
- **Source Citations**: Responses include citations to the source documents
- **Confidence Scoring**: Responses include confidence scores based on similarity scores
- **Error Handling**: Comprehensive error handling and validation
- **Health Checks**: Built-in health check functionality

## Prerequisites

- Python 3.10+
- Google Gemini API key (free tier available)
- Qdrant instance (cloud or self-hosted)
- OpenAI-compatible agent library (for your custom agents)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the backend directory with the following variables:

```env
GEMINI_API_KEY=your_gemini_api_key_here
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
COLLECTION_NAME=book_content
GEMINI_MODEL=gemini-2.0-flash
EMBEDDING_MODEL=text-embedding-004
DEFAULT_TOP_K=5
DEFAULT_SIMILARITY_THRESHOLD=0.7
```

## Files

- `agent.py`: Main RAG agent implementation
- `connection.py`: Configuration for connecting to Google's API via OpenAI-compatible endpoint

## Usage

### Initialize the Agent

```python
from agent import RAGAgent

# Initialize the agent
agent = RAGAgent(
    collection_name="your_collection_name"
)

# Perform a health check
health = agent.health_check()
print(health)
```

### Query the Agent

```python
# Process a query
response = agent.query(
    query_text="What does the book say about artificial intelligence?",
    top_k=5,
    similarity_threshold=0.7
)

print(f"Response: {response['response_text']}")
print(f"Confidence: {response['confidence_score']}")
print(f"Processing time: {response['processing_time_ms']}ms")
```

### Connection Setup

The `connection.py` file provides the configuration for connecting to Google's API through the OpenAI-compatible endpoint:

```python
from connection import config, model, external_client
# Use these in your agent implementation
```

## Architecture

The agent is organized into the following components:

- **RAGAgent**: Main class that orchestrates the RAG process
- **QdrantRetriever**: Handles vector similarity search in Qdrant
- **Configuration**: Settings management and validation
- **Exception Handling**: Custom exception classes for different error scenarios
- **Utilities**: Embedding generation and helper functions

## Environment Variables

- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `QDRANT_URL`: URL of your Qdrant instance (required)
- `QDRANT_API_KEY`: Qdrant API key (required)
- `COLLECTION_NAME`: Name of the Qdrant collection containing your book content (default: book_content)
- `GEMINI_MODEL`: Gemini model to use for responses (default: gemini-2.0-flash)
- `EMBEDDING_MODEL`: Embedding model to use (default: text-embedding-004)
- `DEFAULT_TOP_K`: Default number of results to retrieve (default: 5)
- `DEFAULT_SIMILARITY_THRESHOLD`: Default similarity threshold (default: 0.7)
- `DEBUG`: Enable debug logging (default: False)

## Security Considerations

- API keys are loaded from environment variables and never stored in code
- Input validation is performed on all user inputs
- Proper error handling prevents sensitive information leakage
- Connection validation ensures services are properly authenticated

## Performance

- Efficient vector similarity search using Qdrant
- Configurable retrieval parameters for performance tuning
- Proper timeout handling to prevent hanging requests
- Logging for monitoring performance metrics

## Troubleshooting

- **API Key Issues**: Verify your Google Gemini and Qdrant API keys are correct and have proper permissions
- **Connection Problems**: Ensure your Qdrant instance is accessible and the URL is correct
- **Rate Limits**: If you get 429 errors, you may have exceeded free tier limits
- **No Results**: Make sure your Qdrant collection contains properly indexed content