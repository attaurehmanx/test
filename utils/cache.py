import hashlib
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, default_ttl: int = 3600):  # 1 hour default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def _generate_key(self, query: str, selected_text: str = "") -> str:
        """Generate a cache key based on the query and selected text"""
        cache_input = f"{query}::{selected_text}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, query: str, selected_text: str = "") -> Optional[Dict[str, Any]]:
        """Get a value from the cache"""
        key = self._generate_key(query, selected_text)

        if key in self.cache:
            cached_item = self.cache[key]

            # Check if the item has expired
            if time.time() > cached_item["expiry"]:
                # Remove expired item
                del self.cache[key]
                logger.info(f"Cache miss: {key} (expired)")
                return None

            logger.info(f"Cache hit: {key}")
            return cached_item["value"]

        logger.info(f"Cache miss: {key} (not found)")
        return None

    def set(self, query: str, value: Dict[str, Any], selected_text: str = "", ttl: Optional[int] = None) -> None:
        """Set a value in the cache"""
        key = self._generate_key(query, selected_text)

        if ttl is None:
            ttl = self.default_ttl

        expiry_time = time.time() + ttl

        self.cache[key] = {
            "value": value,
            "expiry": expiry_time
        }

        logger.info(f"Cache set: {key} (ttl: {ttl}s)")

    def delete(self, query: str, selected_text: str = "") -> bool:
        """Delete a value from the cache"""
        key = self._generate_key(query, selected_text)

        if key in self.cache:
            del self.cache[key]
            logger.info(f"Cache delete: {key}")
            return True

        return False

    def clear(self) -> None:
        """Clear all items from the cache"""
        self.cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired items from the cache and return count of removed items"""
        current_time = time.time()
        initial_count = len(self.cache)

        expired_keys = [
            key for key, item in self.cache.items()
            if current_time > item["expiry"]
        ]

        for key in expired_keys:
            del self.cache[key]

        removed_count = initial_count - len(self.cache)
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired cache entries")

        return removed_count

    def size(self) -> int:
        """Get the number of items in the cache"""
        return len(self.cache)

# Create a singleton instance
cache = SimpleCache()