from fastapi import APIRouter
from .endpoints import query

api_router = APIRouter()
api_router.include_router(query.router, prefix="/v1", tags=["query"])

__all__ = ["api_router"]