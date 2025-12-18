import time
import logging
from typing import Dict, Any, Callable
from fastapi import Request, Response
from config.settings import settings
from utils.response_quality import response_quality_metrics

logger = logging.getLogger(__name__)

class MonitoringService:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.start_time = time.time()

    def log_request(self, request: Request, response: Response, process_time: float):
        """Log request metrics"""
        self.request_count += 1

        log_data = {
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
        }

        # Log as info for successful requests, error for failed ones
        if 200 <= response.status_code < 400:
            logger.info(f"Request processed: {log_data}")
        else:
            self.error_count += 1
            logger.error(f"Request failed: {log_data}")

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics for monitoring"""
        uptime = time.time() - self.start_time

        # Get response quality metrics
        quality_metrics = response_quality_metrics.get_metrics()

        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "response_quality": quality_metrics,
            "api_status": "healthy"
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        metrics = self.get_system_metrics()
        return {
            "status": "healthy",
            "checks": {
                "api_access": True,
                "database_connection": True,  # Simplified - in real app would check actual DB
                "external_services": True,    # Simplified - would check actual services
            },
            "metrics": metrics
        }

# Create a singleton instance
monitoring_service = MonitoringService()