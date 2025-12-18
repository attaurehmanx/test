from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from config.settings import settings
from .rate_limit import check_rate_limit
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

def verify_api_key(auth: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Verify the API key from the Authorization header and check rate limits
    """
    if not auth or not auth.credentials:
        logger.warning("No API key provided in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Compare the provided API key with the expected one
    if auth.credentials != settings.api_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check rate limit
    if not check_rate_limit(auth.credentials):
        logger.warning(f"Rate limit exceeded for API key: {auth.credentials}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )

    logger.info("API key validated successfully")
    return auth.credentials

def validate_api_key_in_header(api_key_header: str) -> bool:
    """
    Validate the API key provided in the header
    """
    return api_key_header == settings.api_key