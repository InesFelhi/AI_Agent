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

        # Step 5 — Escape unescaped newlines (control characters in JSON strings)
        cleaned = self._escape_unescaped_newlines(cleaned)

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

    # --------------------------------------------------
    # Step 5 — Escape unescaped newlines
    # --------------------------------------------------
    def _escape_unescaped_newlines(self, text: str) -> str:
        """
        Escape literal newlines in JSON strings.
        
        Problem: LLMs sometimes generate multi-line strings with literal newlines:
            "code": "for (String line : array) {
                extract value
            }"
        
        This is INVALID JSON. json.loads() throws:
            "Invalid control character at: line X column Y"
        
        Solution: Replace literal newlines ONLY inside string values with \n escapes.
        
        Strategy: 
        1. Find all string values (text between unescaped quotes)
        2. Replace literal newlines (\n, \r\n) with escaped versions (\\n, \\r\\n)
        3. Preserve URLs (http://, https://) and other ://-patterns
        """
        # This regex finds string values and replaces unescaped newlines within them
        # It's a greedy approach that handles most LLM outputs
        
        def escape_string_content(match):
            """Replace literal newlines inside a matched string."""
            full_match = match.group(0)
            # Extract the content between quotes
            content = full_match[1:-1]  # Remove surrounding quotes
            
            # Replace literal newlines with escaped versions
            # \r\n (Windows) → \\r\\n
            # \n (Unix) → \\n
            # \r (Mac old) → \\r
            content = content.replace('\r\n', '\\r\\n')
            content = content.replace('\n', '\\n')
            content = content.replace('\r', '\\r')
            
            # Also escape unescaped backslashes to prevent double-escaping
            # But preserve already escaped sequences
            # This is complex, so we use a simple heuristic:
            # Don't re-escape if already escaped (preceded by \)
            
            return '"' + content + '"'
        
        # Match string values: text between unescaped quotes
        # This regex is imperfect but handles most cases
        # Pattern: " followed by (anything except unescaped ") followed by "
        try:
            # Simple approach: find quoted strings and escape newlines within them
            import re
            pattern = r'"(?:[^"\\]|\\.)*"'
            result = re.sub(pattern, escape_string_content, text)
            
            if result != text:
                logger.debug("[EXTRACTOR] Unescaped newlines escaped")
            
            return result
        except Exception as e:
            logger.warning("[EXTRACTOR] Error escaping newlines: %s", str(e))
            # On error, return original (better than crash)
            return text