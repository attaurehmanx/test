import logging
from typing import Dict, Any, List
from models.query import QueryResponse, Citation
import time

logger = logging.getLogger(__name__)

class ResponseQualityMetrics:
    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "avg_citations_per_response": 0,
            "total_citations": 0
        }
        self.response_times = []

    def log_query_start(self) -> float:
        """Record the start time of a query"""
        return time.time()

    def log_query_end(self, start_time: float, success: bool, response: QueryResponse = None):
        """Record the end of a query and update metrics"""
        end_time = time.time()
        response_time = end_time - start_time

        self.metrics["total_queries"] += 1
        self.response_times.append(response_time)
        self.metrics["total_response_time"] += response_time

        if success:
            self.metrics["successful_queries"] += 1
            if response:
                self.metrics["total_citations"] += len(response.citations)
        else:
            self.metrics["failed_queries"] += 1

        # Update averages
        self.metrics["avg_response_time"] = (
            self.metrics["total_response_time"] / self.metrics["successful_queries"]
            if self.metrics["successful_queries"] > 0 else 0
        )
        self.metrics["avg_citations_per_response"] = (
            self.metrics["total_citations"] / self.metrics["successful_queries"]
            if self.metrics["successful_queries"] > 0 else 0
        )

    def validate_response_accuracy(self, response: QueryResponse, source_context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate response accuracy against source documents
        This is a basic implementation - in a real system, you'd want more sophisticated validation
        """
        validation_result = {
            "is_accurate": True,
            "confidence_score": 1.0,
            "citations_validated": True,
            "sources_used": [],
            "validation_notes": []
        }

        # Check if citations are properly linked to source context
        if response.citations and source_context:
            cited_sources = {cit.document_id for cit in response.citations}
            available_sources = {doc.get("document_id") for doc in source_context if doc.get("document_id")}

            # Check for citation accuracy
            if cited_sources.issubset(available_sources):
                validation_result["sources_used"] = list(cited_sources.intersection(available_sources))
            else:
                validation_result["is_accurate"] = False
                validation_result["confidence_score"] = 0.5
                validation_result["validation_notes"].append("Some citations reference sources not in context")

        # Basic check: if there are citations, the response should be non-empty
        if response.citations and not response.answer.strip():
            validation_result["is_accurate"] = False
            validation_result["confidence_score"] = 0.0
            validation_result["validation_notes"].append("Response has citations but no content")

        # Log validation result
        logger.info(f"Response validation: accurate={validation_result['is_accurate']}, "
                   f"confidence={validation_result['confidence_score']}, "
                   f"citations={len(response.citations)}")

        return validation_result

    def get_metrics(self) -> Dict[str, Any]:
        """Get current quality metrics"""
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset all metrics to initial state"""
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "avg_citations_per_response": 0,
            "total_citations": 0
        }
        self.response_times = []

# Create a singleton instance
response_quality_metrics = ResponseQualityMetrics()