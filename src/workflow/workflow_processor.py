"""
Workflow Processor — orchestrator for LLM output post-processing.

Changes vs previous version:
    1. _unwrap_workflow_key() — new step inserted between extraction and
       validation.  The LLM is instructed to return:
           { "workflow": { ...real nodes... }, "explanation": "..." }
       The JSONValidator expects the real nodes at the top level.
       This method detects the wrapper and replaces the parsed dict with
       its "workflow" value before validation runs.
       The "explanation" is saved separately and included in the result.

    2. proc_result always contains "final_json" — even on extraction
       failure — so callers can safely use .get("final_json", "") without
       a KeyError.

    3. _unwrap_raw_json() — after unwrapping the parsed dict, serialise it
       back to a JSON string so the validator receives a proper string
       (JSONValidator.validate() takes a string, not a dict).
"""

import json
from typing import Any, Dict, Optional

from src.workflow.json_retry_handler import JSONRetryHandler
from src.workflow.json_validator import JSONValidator, ValidationResult
from src.workflow.json_extractor import JSONExtractor
from src.utilities.logger import get_module_logger

logger = get_module_logger("workflow_processor")


class WorkflowProcessor:
    """
    Single entry point for LLM workflow output post-processing.

    Pipeline per call:
        raw LLM string
          → JSONExtractor  (strip markdown, isolate JSON block)
          → _unwrap_workflow_key  (descend into {"workflow": ..., "explanation": ...})
          → JSONValidator  (syntax + structural business rules)
          → JSONRetryHandler  (up to 3 self-correction loops on failure)
    """

    def __init__(self, llm_client) -> None:
        self.retry_handler = JSONRetryHandler(llm_client)
        self.extractor     = JSONExtractor()
        self.validator     = JSONValidator()
        logger.info("WorkflowProcessor initialised")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, raw_llm_output: str) -> Dict[str, Any]:
        """
        Process raw LLM output through full validation pipeline.

        Returns:
            {
                "success":           bool
                "workflow":          dict | None   — parsed workflow if valid
                "explanation":       str  | None   — LLM explanation text
                "raw_json":          str           — final extracted JSON string
                "final_json":        str           — alias of raw_json (safe fallback key)
                "validation_passed": bool
                "retry_count":       int
                "errors_found":      List[str]
                "status":            "success" | "partial_failure"
            }
        """
        logger.info("[PROCESSOR] Processing LLM workflow output")

        explanation: Optional[str] = None

        # ── Step 1: extract clean JSON string ──────────────────────────
        try:
            json_string = self.extractor.extract(raw_llm_output)
        except ValueError as exc:
            logger.error("[PROCESSOR] JSON extraction failed: %s", str(exc))
            return self._failure_result(
                errors=[f"JSON extraction failed: {str(exc)}"],
                final_json="",
                explanation=None,
            )

        # ── Step 2: parse to dict ───────────────────────────────────────
        try:
            parsed = json.loads(json_string)
        except json.JSONDecodeError as exc:
            logger.error("[PROCESSOR] JSON parse failed: %s", str(exc))
            return self._failure_result(
                errors=[f"JSON syntax error: {str(exc)}"],
                final_json=json_string,
                explanation=None,
            )

        # ── Step 3: unwrap {"workflow": ..., "explanation": ...} ────────
        parsed, explanation = self._unwrap_workflow_key(parsed)

        # Serialise back to string for the validator / retry handler
        try:
            json_string = json.dumps(parsed, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            logger.error("[PROCESSOR] Re-serialisation failed: %s", str(exc))
            return self._failure_result(
                errors=[f"Re-serialisation error: {str(exc)}"],
                final_json=json_string,
                explanation=explanation,
            )

        # ── Step 4: validate + self-correction loop ─────────────────────
        handler_result = self.retry_handler.process(json_string)

        validation   = handler_result["validation"]
        success      = handler_result["success"]
        retry_count  = handler_result["retry_count"]
        final_json   = handler_result.get("final_json", json_string)
        errors       = validation.errors if validation else []

        if success:
            logger.info(
                "[PROCESSOR] Workflow valid — retry_count=%d", retry_count
            )
            return {
                "success":           True,
                "workflow":          validation.parsed,
                "explanation":       explanation,
                "raw_json":          final_json,
                "final_json":        final_json,   # safe alias
                "validation_passed": True,
                "retry_count":       retry_count,
                "errors_found":      [],
                "status":            "success",
            }

        logger.error(
            "[PROCESSOR] Workflow invalid after %d retries. Errors: %s",
            retry_count, errors,
        )
        return self._failure_result(
            errors=errors,
            final_json=final_json,
            explanation=explanation,
            retry_count=retry_count,
        )

    # ------------------------------------------------------------------
    # Unwrap helper
    # ------------------------------------------------------------------

    @staticmethod
    def _unwrap_workflow_key(parsed: Any):
        """
        If the LLM wrapped the workflow inside a "workflow" key
        (as instructed by the generation prompt), descend into it.

        Input:  {"workflow": {...real nodes...}, "explanation": "..."}
        Output: ({...real nodes...}, "explanation text or None")

        If there is no "workflow" key the dict is returned unchanged
        (backward compatible with callers that omit the wrapper).
        """
        if not isinstance(parsed, dict):
            return parsed, None

        explanation: Optional[str] = None

        # Extract explanation regardless of whether we unwrap
        if "explanation" in parsed and isinstance(parsed["explanation"], str):
            explanation = parsed["explanation"].strip() or None

        # Unwrap if the dict has a "workflow" key whose value is a dict
        if "workflow" in parsed and isinstance(parsed["workflow"], dict):
            logger.debug(
                "[PROCESSOR] Unwrapped 'workflow' key — "
                "explanation present: %s",
                explanation is not None,
            )
            return parsed["workflow"], explanation

        return parsed, explanation

    # ------------------------------------------------------------------
    # Failure result builder
    # ------------------------------------------------------------------

    @staticmethod
    def _failure_result(
        errors,
        final_json: str,
        explanation: Optional[str],
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        return {
            "success":           False,
            "workflow":          None,
            "explanation":       explanation,
            "raw_json":          final_json,
            "final_json":        final_json,   # safe alias, never missing
            "validation_passed": False,
            "retry_count":       retry_count,
            "errors_found":      errors,
            "status":            "partial_failure",
        }