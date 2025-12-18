from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class Citation(BaseModel):
    """
    Points to source documents in Qdrant that support the response
    """
    document_id: str = Field(..., description="Unique identifier of the source document")
    title: str = Field(..., description="Title of the source document")
    url: str = Field(..., description="URL to access the source document",
                     pattern=r"^https?://.+$|^/.*$")  # URL format validation
    text_snippet: str = Field(..., description="Relevant text snippet from the source",
                              min_length=10, max_length=1000)
    relevance_score: float = Field(..., description="Score indicating relevance",
                                   ge=0.0, le=1.0)


class QueryRequest(BaseModel):
    """
    Represents a user's query and optional selected text from the frontend
    """
    query: str = Field(..., description="The user's question or query text",
                       min_length=1, max_length=2000)
    selected_text: Optional[str] = Field(default="", description="Text selected by the user on the page",
                                         max_length=5000)
    session_id: Optional[str] = Field(default=None, description="Unique identifier for the conversation session")
    metadata: Optional[dict] = Field(default=None, description="Additional context information")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I configure ROS 2 parameters?",
                "selected_text": "",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class QueryResponse(BaseModel):
    """
    Contains the RAG-generated answer with source citations and metadata
    """
    answer: str = Field(..., description="The AI-generated response to the query",
                        min_length=1, max_length=10000)
    citations: List[Citation] = Field(..., description="List of source documents referenced",
                                      max_items=20)
    query_id: str = Field(..., description="Unique identifier for this query")
    timestamp: str = Field(..., description="ISO 8601 timestamp of response generation")
    metadata: Optional[dict] = Field(default=None, description="Additional response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To configure ROS 2 parameters, you can use the parameter_namespace approach...",
                "citations": [
                    {
                        "document_id": "doc-ros2-params-001",
                        "title": "ROS 2 Parameter Configuration Guide",
                        "url": "/docs/ros2/parameters/config",
                        "text_snippet": "Parameters in ROS 2 can be configured using parameter_namespace which allows grouping related parameters...",
                        "relevance_score": 0.92
                    }
                ],
                "query_id": "query-12345-abcde",
                "timestamp": "2025-12-15T10:30:00.000Z",
                "metadata": {
                    "processing_time_ms": 1250,
                    "model_used": "claude-sonnet-4-5"
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response format for API failures
    """
    error_code: str = Field(..., description="Machine-readable error code",
                            pattern=r"^ERROR_[A-Z_]+$")
    message: str = Field(..., description="Human-readable error description",
                         max_length=500)
    details: Optional[dict] = Field(default=None, description="Additional error details")
    timestamp: str = Field(..., description="ISO 8601 timestamp of error")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "ERROR_INVALID_QUERY",
                "message": "Query must be between 1 and 2000 characters",
                "timestamp": "2025-12-15T10:30:00.000Z"
            }
        }