"""
Test script for API authentication functionality
"""
import asyncio
import sys
import os

# Add the backend directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath('.'))

from utils.auth import verify_api_key, validate_api_key_in_header
from utils.rate_limit import rate_limiter
from config.settings import settings

def test_api_key_validation():
    """Test API key validation functionality"""
    print("Testing API key validation...")

    # Test with correct API key
    try:
        is_valid = validate_api_key_in_header(settings.api_key)
        print(f"Valid API key validation: {'PASS' if is_valid else 'FAIL'}")
    except Exception as e:
        print(f"Valid API key validation failed: {e}")

    # Test with invalid API key
    try:
        is_valid = validate_api_key_in_header("invalid-api-key")
        print(f"Invalid API key validation: {'PASS' if not is_valid else 'FAIL'}")
    except Exception as e:
        print(f"Invalid API key validation failed: {e}")

def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\nTesting rate limiting...")

    # Test rate limiting with the same API key
    api_key = settings.api_key
    requests_allowed = 0
    total_requests = settings.rate_limit_per_minute + 2  # Request more than the limit

    for i in range(total_requests):
        is_allowed = rate_limiter.is_allowed(api_key)
        if is_allowed:
            requests_allowed += 1
        print(f"Request {i+1}: {'ALLOWED' if is_allowed else 'BLOCKED'}")

    print(f"Requests allowed: {requests_allowed}, Rate limit: {settings.rate_limit_per_minute}")
    expected_allowed = min(total_requests, settings.rate_limit_per_minute)
    print(f"Rate limiting: {'PASS' if requests_allowed <= expected_allowed else 'FAIL'}")

if __name__ == "__main__":
    test_api_key_validation()
    test_rate_limiting()
    print("\nAuthentication testing completed!")