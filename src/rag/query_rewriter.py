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
from src.rag.task_registry import TaskNameRegistry
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
# System prompt builder
# -------------------------------------------------------

def _build_system_prompt(task_metadata: List[Dict[str, str]]) -> str:
    return build_query_rewriter_prompt(task_metadata)


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

        # Step 1 — load task metadata from Qdrant (cached, refreshed every TTL)
        task_metadata = self.registry.get_task_metadata()

        # Step 2 — build prompt with current task list and summaries injected
        system_prompt = _build_system_prompt(task_metadata)

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