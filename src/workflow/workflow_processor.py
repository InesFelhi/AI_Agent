"""
Workflow Processor — orchestrator for LLM output post-processing.

Responsibilities:
- Single entry point called by chat_api.py after llm.complete()
- Coordinate JSONRetryHandler
- Return structured result with validation metadata
- Handle partial failure with structured fallback response

Why this module exists:
    chat_api.py should not know about extraction, validation, or retry logic.
    This module provides a single clean interface:
        processor.process(raw_llm_output) → result dict
    It also enriches ChatResponse metadata with validation info
    for MLOps monitoring (retry_count, errors_found, validation_passed).
"""

from typing import Any, Dict
from src.workflow.json_retry_handler import JSONRetryHandler
from src.utilities.logger import get_module_logger

logger = get_module_logger("workflow_processor")


class WorkflowProcessor:
    """
    Single entry point for LLM workflow output post-processing.
    Called by chat_api.py after every workflow_generation
    and workflow_correction LLM call.
    """

    def __init__(self, llm_client) -> None:
        """
        Args:
            llm_client: LLM client passed from chat_api context
        """
        self.retry_handler = JSONRetryHandler(llm_client)
        logger.info("WorkflowProcessor initialized")

    def process(self, raw_llm_output: str) -> Dict[str, Any]:
        """
        Process raw LLM output through full validation pipeline.

        Args:
            raw_llm_output: raw string from llm.complete()

        Returns:
            {
                "success":            bool
                "workflow":           dict | None  (parsed workflow if valid)
                "raw_json":           str          (final extracted JSON string)
                "validation_passed":  bool
                "retry_count":        int
                "errors_found":       List[str]
                "status":             "success" | "partial_failure"
            }
        """
        logger.info("[PROCESSOR] Processing LLM workflow output")

        handler_result = self.retry_handler.process(raw_llm_output)

        validation = handler_result["validation"]
        success = handler_result["success"]
        retry_count = handler_result["retry_count"]
        final_json = handler_result["final_json"]
        errors = validation.errors if validation else []

        if success:
            logger.info(
                "[PROCESSOR] Workflow valid — retry_count=%d", retry_count
            )
            return {
                "success": True,
                "workflow": validation.parsed,
                "raw_json": final_json,
                "validation_passed": True,
                "retry_count": retry_count,
                "errors_found": [],
                "status": "success"
            }

        # Partial failure — return structured error response
        logger.error(
            "[PROCESSOR] Workflow invalid after %d retries. Errors: %s",
            retry_count,
            errors
        )
        return {
            "success": False,
            "workflow": None,
            "raw_json": final_json,
            "validation_passed": False,
            "retry_count": retry_count,
            "errors_found": errors,
            "status": "partial_failure"
        }