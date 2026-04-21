"""
JSON Retry Handler for AI Agent workflow post-processing.

Responsibilities:
- Coordinate JSONExtractor + JSONValidator in a retry loop
- On failure: build precise error feedback prompt for LLM
- Re-call LLM with broken JSON + error list injected in prompt
- Limit retries to MAX_RETRIES (default: 2)
- Return final ValidationResult with retry metadata

Why this module exists:
    A single LLM call will sometimes produce broken JSON.
    Rather than failing immediately, this handler gives the LLM
    a second chance by telling it exactly what was wrong:
    "Your JSON had these errors: [list]. Fix only these points."
    This targeted feedback dramatically improves correction success
    compared to a blind retry with the same prompt.
    Retries are capped at 2 to avoid runaway API costs.
"""

from typing import Any, Dict, Optional
from src.workflow.json_extractor import JSONExtractor
from src.workflow.json_validator import JSONValidator, ValidationResult
from src.utilities.logger import get_module_logger

logger = get_module_logger("json_retry_handler")

MAX_RETRIES = 3

RETRY_SYSTEM_PROMPT = """You are an expert at correcting Android workflow JSON.
Your task is to fix the broken workflow JSON provided.
Fix the errors listed in the error report. This may require adding or modifying parts of the JSON as needed, including adding missing keys like "Links" and adding objects to arrays.
Do not rewrite the whole workflow unnecessarily.
Do not add any explanation or markdown.
Output must be valid strict JSON only."""

RETRY_USER_TEMPLATE = """The following workflow JSON has validation errors.

--- Broken JSON ---
{broken_json}

--- Error report ---
{error_list}

Fix ONLY the errors listed above. Return the corrected JSON."""


class JSONRetryHandler:
    """
    Orchestrate extract → validate → retry loop for LLM JSON output.

    Usage:
        handler = JSONRetryHandler(llm_client)
        result = handler.process(raw_llm_output)
        if result["validation"].is_valid:
            workflow = result["validation"].parsed
        else:
            # handle partial failure
    """

    def __init__(self, llm_client) -> None:
        """
        Args:
            llm_client: any LLM client with .complete(system, user, ...) method
        """
        self.llm = llm_client
        self.extractor = JSONExtractor()
        self.validator = JSONValidator()

    def process(self, raw_llm_output: str) -> Dict[str, Any]:
        """
        Run extract → validate → retry loop.

        Args:
            raw_llm_output: raw string returned by LLM after generation/correction

        Returns:
            {
                "validation":   ValidationResult (is_valid, errors, parsed),
                "retry_count":  int — number of retries performed (0, 1, or 2),
                "final_json":   str — last extracted JSON string (valid or not),
                "success":      bool — True if valid JSON was produced
            }
        """
        logger.info("[RETRY_HANDLER] Starting process (max_retries=%d)", MAX_RETRIES)

        retry_count = 0
        current_output = raw_llm_output
        last_json_string = ""
        last_result: Optional[ValidationResult] = None

        while retry_count <= MAX_RETRIES:

            attempt = retry_count + 1
            logger.info("[RETRY_HANDLER] Attempt %d/%d", attempt, MAX_RETRIES + 1)

            # Step 1 — Extract clean JSON string
            try:
                json_string = self.extractor.extract(current_output)
                last_json_string = json_string
            except ValueError as e:
                logger.warning(
                    "[RETRY_HANDLER] Extraction failed on attempt %d: %s",
                    attempt, str(e)
                )
                last_result = ValidationResult(
                    is_valid=False,
                    errors=[f"JSON extraction failed: {str(e)}"],
                    parsed=None
                )

                if retry_count < MAX_RETRIES:
                    retry_count += 1
                    current_output = self._build_retry_prompt_and_call(
                        broken_json=current_output,
                        errors=[f"JSON extraction failed: {str(e)}"]
                    )
                    continue
                else:
                    break

            # Step 2 — Validate extracted JSON
            result = self.validator.validate(json_string)
            last_result = result

            if result.is_valid:
                logger.info(
                    "[RETRY_HANDLER] Validation passed on attempt %d", attempt
                )
                return {
                    "validation": result,
                    "retry_count": retry_count,
                    "final_json": json_string,
                    "success": True
                }

            logger.warning(
                "[RETRY_HANDLER] Validation failed on attempt %d (%d errors): %s",
                attempt,
                len(result.errors),
                result.errors
            )

            # If retries exhausted — stop
            if retry_count >= MAX_RETRIES:
                logger.error(
                    "[RETRY_HANDLER] Max retries reached. Returning failure."
                )
                break

            # Build retry — inject errors into LLM prompt
            retry_count += 1
            logger.info(
                "[RETRY_HANDLER] Launching retry %d with error feedback",
                retry_count
            )
            current_output = self._build_retry_prompt_and_call(
                broken_json=json_string,
                errors=result.errors
            )

        # All attempts exhausted — return failure
        return {
            "validation": last_result,
            "retry_count": retry_count,
            "final_json": last_json_string,
            "success": False
        }

    # --------------------------------------------------
    # Build retry prompt and call LLM
    # --------------------------------------------------
    def _build_retry_prompt_and_call(
        self,
        broken_json: str,
        errors: list
    ) -> str:
        """
        Build error feedback prompt and call LLM for correction.

        Args:
            broken_json: the JSON string that failed validation
            errors:      list of error messages from JSONValidator

        Returns:
            Raw LLM output string (to be re-processed by extractor + validator)
        """
        error_list = "\n".join(f"- {e}" for e in errors)

        user_prompt = RETRY_USER_TEMPLATE.format(
            broken_json=broken_json,
            error_list=error_list
        )

        logger.debug("[RETRY_HANDLER] Retry prompt:\n%s", user_prompt[:500])

        try:
            response = self.llm.complete(
                system=RETRY_SYSTEM_PROMPT,
                user=user_prompt,
                max_tokens=2000,
                temperature=0.0
            )
            logger.info("[RETRY_HANDLER] LLM retry call successful")
            return response

        except Exception as e:
            logger.exception("[RETRY_HANDLER] LLM retry call failed: %s", str(e))
            # Return empty string — extractor will raise ValueError on next iteration
            return ""