"""
Query Rewriter module for AI Agent RAG pipeline.

Responsibilities:
- Load task names dynamically from Qdrant (no hardcoded list)
- Translate user query to English
- Extract detected intent (workflow_generation, workflow_correction, qa)
- Identify implied task names from the dynamic list
- Build an enriched English search query containing technical terms
- Return structured JSON used by RAGRetriever before embedding

Why dynamic task names:
    Task names are read from Qdrant at runtime by scanning all chunks
    where type_doc=task_doc and extracting their document_title metadata.
    This means the LLM always knows the full list of available tasks
    without any code change — adding a new task = add its .md + re-index.

Output contract:
    {
        "intent":          "workflow_generation" | "workflow_correction" | "qa",
        "task_names":      ["CmdStage", "IntegerSingleOps", ...],
        "search_query_en": "enriched english query with technical terms"
    }
"""

import json
import re
import time
from typing import Dict, List
from qdrant_client import QdrantClient
from src.llm import LLMClient
from src.prompts.query_rewriter_prompt import build_query_rewriter_prompt
from src.utilities.logger import get_module_logger

logger = get_module_logger("query_rewriter")


# -------------------------------------------------------
# Fallback result
# -------------------------------------------------------

def _fallback_result(raw_query: str) -> Dict:
    logger.warning("[REWRITER] Using fallback — raw query passed as-is")
    return {
        "intent": "workflow_generation",
        "task_names": [],
        "search_query_en": raw_query
    }


# -------------------------------------------------------
# TaskNameRegistry
# -------------------------------------------------------

class TaskNameRegistry:
    """
    Fetches and caches task names from Qdrant collection metadata.

    How it works:
        - Scrolls through all points where type_doc = "task_doc"
        - Extracts unique document_title values from their payload
        - Caches the result for `cache_ttl_seconds` (default 10 min)
        - Refreshes automatically when TTL expires

    This means:
        - 30 tasks today   -> 30 names in the prompt
        - 120 tasks later  -> 120 names in the prompt
        - Zero code change required
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        cache_ttl_seconds: int = 600
    ) -> None:
        self.client = qdrant_client
        self.collection_name = collection_name
        self.cache_ttl = cache_ttl_seconds

        self._cached_names: List[str] = []
        self._last_loaded: float = 0.0

    def get_task_names(self) -> List[str]:
        """
        Return list of task names, refreshing cache if TTL expired.

        Returns:
            List of task document titles e.g. ["CmdStage", "AppStage", ...]
            Returns empty list if Qdrant is unreachable (non-blocking).
        """
        now = time.time()

        if self._cached_names and (now - self._last_loaded) < self.cache_ttl:
            logger.debug(
                "[REGISTRY] Returning cached task names (%d tasks)",
                len(self._cached_names)
            )
            return self._cached_names

        logger.info("[REGISTRY] Loading task names from Qdrant...")
        self._cached_names = self._load_from_qdrant()
        self._last_loaded = now
        logger.info(
            "[REGISTRY] Loaded %d task names: %s",
            len(self._cached_names),
            self._cached_names
        )
        return self._cached_names

    def _load_from_qdrant(self) -> List[str]:
        """
        Scroll through Qdrant and collect unique document_title values
        from all chunks where type_doc = task_doc.

        Returns:
            Sorted list of unique task names
        """
        task_names = set()
        offset = None

        try:
            while True:
                result, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=self._build_task_filter(),
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False      # metadata only, no vectors needed
                )

                for point in result:
                    title = point.payload.get("document_title")
                    if title and isinstance(title, str) and title.strip():
                        task_names.add(title.strip())

                if next_offset is None:
                    break

                offset = next_offset

        except Exception:
            logger.exception(
                "[REGISTRY] Failed to load task names from Qdrant. "
                "Using cached list if available."
            )
            return self._cached_names or []

        return sorted(task_names)

    @staticmethod
    def _build_task_filter():
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        return Filter(
            must=[
                FieldCondition(
                    key="type_doc",
                    match=MatchValue(value="task_doc")
                )
            ]
        )


# -------------------------------------------------------
# System prompt builder
# -------------------------------------------------------

def _build_system_prompt(task_names: List[str]) -> str:
    return build_query_rewriter_prompt(task_names)


# -------------------------------------------------------
# QueryRewriter
# -------------------------------------------------------

class QueryRewriter:
    """
    Rewrite and enrich user queries before embedding.

    Uses TaskNameRegistry to dynamically inject the current list
    of available task names into the LLM system prompt.
    Scales from 30 to 120+ tasks with zero code changes.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        qdrant_client: QdrantClient,
        collection_name: str,
        cache_ttl_seconds: int = 600
    ) -> None:
        """
        Args:
            llm_client:        your existing LLM client instance
            qdrant_client:     connected QdrantClient instance
            collection_name:   Qdrant collection name
            cache_ttl_seconds: task name cache duration in seconds (default 10 min)
        """
        self.llm = llm_client
        self.registry = TaskNameRegistry(
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            cache_ttl_seconds=cache_ttl_seconds
        )
        logger.info("QueryRewriter initialized with dynamic task registry")

    def rewrite(self, raw_query: str) -> Dict:
        """
        Analyze and enrich a user query for hybrid RAG retrieval.

        Args:
            raw_query: raw user input in any language

        Returns:
            {
                "intent":          str  — workflow_generation | workflow_correction | qa
                "task_names":      list — task types implied by the query
                "search_query_en": str  — enriched English query ready for embedding
            }

        Never raises — returns fallback dict on any error.
        """
        if not raw_query or not raw_query.strip():
            logger.warning("[REWRITER] Empty query received")
            return _fallback_result(raw_query or "")

        logger.info("[REWRITER] Rewriting query: %.80s", raw_query)

        # Step 1 — load task names from Qdrant (cached, refreshed every TTL)
        task_names = self.registry.get_task_names()

        # Step 2 — build prompt with current task list injected
        system_prompt = _build_system_prompt(task_names)

        # Step 3 — call LLM
        try:
            response = self.llm.complete(
                system=system_prompt,
                user=raw_query.strip(),
                max_tokens=300,
                temperature=0.0
            )
        except Exception:
            logger.exception("[REWRITER] LLM call failed")
            return _fallback_result(raw_query)

        # Step 4 — parse and validate
        result = self._parse_response(response, raw_query)

        logger.info(
            "[REWRITER] [OK] intent=%s  tasks=%s",
            result.get("intent"),
            result.get("task_names")
        )
        return result

    def _parse_response(self, response: str, raw_query: str) -> Dict:
        if not response or not response.strip():
            logger.warning("[REWRITER] LLM returned empty response")
            return _fallback_result(raw_query)

        # Strip markdown fences if LLM adds ```json ... ```
        clean = re.sub(r"```(?:json)?", "", response).strip().strip("`").strip()

        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            logger.warning(
                "[REWRITER] Could not parse JSON: %.200s", response
            )
            return _fallback_result(raw_query)

        # Validate intent
        intent = parsed.get("intent", "workflow_generation")
        if intent not in {"workflow_generation", "workflow_correction", "qa"}:
            logger.warning("[REWRITER] Unknown intent '%s', using default", intent)
            intent = "workflow_generation"

        # Validate task_names
        task_names = parsed.get("task_names", [])
        if not isinstance(task_names, list):
            task_names = []

        # Validate search_query_en
        search_query_en = parsed.get("search_query_en", "")
        if not isinstance(search_query_en, str) or not search_query_en.strip():
            search_query_en = raw_query

        return {
            "intent": intent,
            "task_names": task_names,
            "search_query_en": search_query_en.strip()
        }