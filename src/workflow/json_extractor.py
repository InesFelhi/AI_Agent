"""
JSON Extractor for AI Agent workflow post-processing.

Responsibilities:
- Strip markdown fences (```json ... ```)
- Extract first valid JSON block by brace position
- Remove inline comments (//)
- Remove trailing commas before } and ]
- Return clean raw string ready for json.loads()

Why this module exists:
    LLMs often wrap JSON in markdown fences or add comments even when
    instructed not to. This defensive pre-parser handles all known
    failure modes before any structural validation occurs.
"""

import re
from src.utilities.logger import get_module_logger

logger = get_module_logger("json_extractor")


class JSONExtractor:
    """
    Clean and extract raw JSON string from LLM output.
    Always runs before JSONValidator.
    """

    def extract(self, raw_output: str) -> str:
        """
        Extract clean JSON string from raw LLM output.

        Args:
            raw_output: raw string returned by LLM

        Returns:
            Clean JSON string ready for json.loads()

        Raises:
            ValueError: if no JSON block could be found
        """
        if not raw_output or not raw_output.strip():
            raise ValueError("LLM returned empty output")

        logger.debug("[EXTRACTOR] Raw output length: %d chars", len(raw_output))

        # Step 1 — Strip markdown fences
        cleaned = self._strip_markdown_fences(raw_output)

        # Step 2 — Extract first JSON block by brace position
        cleaned = self._extract_json_block(cleaned)

        # Step 3 — Remove inline comments
        cleaned = self._remove_inline_comments(cleaned)

        # Step 4 — Remove trailing commas
        cleaned = self._remove_trailing_commas(cleaned)

        logger.debug("[EXTRACTOR] Extracted JSON length: %d chars", len(cleaned))
        return cleaned.strip()

    # --------------------------------------------------
    # Step 1 — Strip markdown fences
    # --------------------------------------------------
    def _strip_markdown_fences(self, text: str) -> str:
        """
        Remove ```json ... ``` or ``` ... ``` wrappers.
        Handles variations: ```JSON, ``` json, ```json\n
        """
        # Remove opening fence with optional language tag
        text = re.sub(r"```(?:json|JSON)?\s*\n?", "", text)
        # Remove closing fence
        text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
        logger.debug("[EXTRACTOR] Markdown fences stripped")
        return text.strip()

    # --------------------------------------------------
    # Step 2 — Extract first JSON block
    # --------------------------------------------------
    def _extract_json_block(self, text: str) -> str:
        """
        Find first { and last } to isolate the JSON object.
        Handles cases where LLM adds explanation text before or after JSON.
        """
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            logger.error("[EXTRACTOR] No JSON block found in LLM output")
            logger.debug("[EXTRACTOR] Raw text: %.300s", text)
            raise ValueError(
                "No JSON object found in LLM output. "
                "The model may have returned a text explanation instead of JSON."
            )

        if end <= start:
            raise ValueError(
                "Invalid JSON block boundaries: closing brace before opening brace."
            )

        extracted = text[start:end + 1]
        logger.debug("[EXTRACTOR] JSON block extracted (chars %d to %d)", start, end)
        return extracted

    # --------------------------------------------------
    # Step 3 — Remove inline comments
    # --------------------------------------------------
    def _remove_inline_comments(self, text: str) -> str:
        """
        Remove // inline comments that are invalid in JSON.
        LLMs sometimes add explanatory comments inside JSON.
        Example: "id": "-1001"  // this is the first task
        """
        # Remove // comments — careful not to remove URLs (http://)
        cleaned = re.sub(r'(?<!:)//[^\n"]*', "", text)

        if cleaned != text:
            logger.debug("[EXTRACTOR] Inline comments removed")

        return cleaned

    # --------------------------------------------------
    # Step 4 — Remove trailing commas
    # --------------------------------------------------
    def _remove_trailing_commas(self, text: str) -> str:
        """
        Remove trailing commas before } or ] which are invalid in JSON.
        Example: {"key": "value",} → {"key": "value"}
        """
        # Trailing comma before closing brace or bracket
        cleaned = re.sub(r",\s*([}\]])", r"\1", text)

        if cleaned != text:
            logger.debug("[EXTRACTOR] Trailing commas removed")

        return cleaned