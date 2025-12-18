import time
from collections import defaultdict
from typing import Dict
import threading
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, requests_per_minute: int = settings.rate_limit_per_minute):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)  # API key -> list of request timestamps
        self.lock = threading.Lock()

    def is_allowed(self, api_key: str) -> bool:
        """
        Check if a request from the given API key is allowed based on rate limits
        """
        with self.lock:
            current_time = time.time()

            # Clean old requests (older than 1 minute)
            self.requests[api_key] = [
                timestamp for timestamp in self.requests[api_key]
                if current_time - timestamp < 60  # 60 seconds = 1 minute
            ]

            # Check if the number of requests is under the limit
            if len(self.requests[api_key]) < self.requests_per_minute:
                # Add current request
                self.requests[api_key].append(current_time)
                return True
            else:
                logger.warning(f"Rate limit exceeded for API key: {api_key}")
                return False

# Create a global rate limiter instance
rate_limiter = RateLimiter()

def check_rate_limit(api_key: str) -> bool:
    """
    Check if the API key is within rate limits
    """
    return rate_limiter.is_allowed(api_key)