from fastapi import APIRouter, HTTPException, Request
from typing import Optional
import time
import logging
from models.query import QueryRequest, QueryResponse, ErrorResponse
from services.rag_service import rag_service
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/query",
             response_model=QueryResponse,
             responses={
                 200: {"description": "Successful query response with citations"},
                 400: {"description": "Bad request - invalid query format", "model": ErrorResponse},
                 500: {"description": "Internal server error", "model": ErrorResponse}
             })
async def query_documentation(request: QueryRequest):
    """
    Submit a query to the RAG system
    Process a user query against documentation and return a grounded response with citations
    """
    try:
        logger.info(f"Processing query: {request.query[:100]}...")  # Log first 100 chars

        # Validate the query
        if not request.query or len(request.query.strip()) == 0:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        if len(request.query) > 2000:  # Max length from data model
            raise HTTPException(status_code=400, detail="Query exceeds maximum length of 2000 characters")

        # Process the query using the RAG service
        response = rag_service.query_documentation(request)

        logger.info(f"Query processed successfully, response length: {len(response.answer)}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (like 400) as they are
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Additional utility endpoints
@router.get("/health")
async def query_health():
    """Health check for the query service"""
    return {"status": "healthy", "service": "query-api"}

# Add more endpoints as needed