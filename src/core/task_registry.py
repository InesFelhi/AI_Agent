"""
Unified Task Registry — Single source of truth for all task management.

MERGED from:
- src/rag/task_registry.py (TaskNameRegistry)
- src/workflow/task_registry.py (TaskRegistry)

Responsibilities:
- Load all available tasks from Qdrant
- Provide task names, metadata, descriptions, and internal→display mapping
- Cache everything with configurable TTL (default 10 min)
- Used by BOTH QueryRewriter AND WorkflowPlanner

Scales from 30 to 120+ tasks with zero code changes.
"""

import re
import time
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.ingestion_pipeline.task_section_extractor import extract_task_sections
from src.ingestion_pipeline.vector_store import VectorStore
from src.utilities.logger import get_module_logger

logger = get_module_logger("task_registry")

EXCLUDED_TASKS = {
    "Start",
    "End",
    "Tasks Overview"
}


class UnifiedTaskRegistry:
    """
    Unified registry for task management — combines TaskNameRegistry and TaskRegistry.
    
    Provides:
    1. Task name list (for QueryRewriter)
    2. Task metadata with internal name mappings (for QueryRewriter)
    3. Task descriptions (for WorkflowPlanner)
    4. Document title resolution (for ChatAPI context building)
    
    Single cache with TTL covers all needs.
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        cache_ttl_seconds: int = 600
    ) -> None:
        """
        Args:
            qdrant_client: connected Qdrant client
            collection_name: name of the Qdrant collection
            cache_ttl_seconds: cache duration in seconds (default 10 min)
        """
        self.client = qdrant_client
        self.collection_name = collection_name
        self.cache_ttl = cache_ttl_seconds

        # Unified cache
        self._cached_tasks: List[Dict] = []
        self._cached_names: List[str] = []
        self._cached_metadata: List[Dict[str, str]] = []
        self._cached_internal_to_display: Dict[str, str] = {}
        self._cached_descriptions: Dict[str, Dict[str, str]] = {}
        self._last_loaded: float = 0.0

    # ==========================================================================
    # PUBLIC API — QueryRewriter methods
    # ==========================================================================

    def get_task_names(self) -> List[str]:
        """
        Return task names (e.g., ["CmdStage", "AppStage", ...])
        
        Used by:
        - QueryRewriter.rewrite()
        - WorkflowPlanner.plan()
        """
        now = time.time()
        if self._cached_names and (now - self._last_loaded) < self.cache_ttl:
            logger.debug(
                "[REGISTRY] Returning cached task names (%d tasks)",
                len(self._cached_names)
            )
            return self._cached_names

        logger.info("[REGISTRY] Loading task names from Qdrant...")
        self._refresh_cache()
        logger.info(
            "[REGISTRY] Loaded %d task names: %s",
            len(self._cached_names),
            self._cached_names
        )
        return self._cached_names

    def get_task_metadata(self) -> List[Dict[str, str]]:
        """
        Return task metadata (name + summary + purpose).
        
        Returns:
            List of {"name": str, "summary": str}
        
        Used by:
        - QueryRewriter to inject into LLM prompt
        """
        now = time.time()
        if self._cached_metadata and (now - self._last_loaded) < self.cache_ttl:
            logger.debug(
                "[REGISTRY] Returning cached task metadata (%d tasks)",
                len(self._cached_metadata)
            )
            return self._cached_metadata

        self._refresh_cache()
        logger.info(
            "[REGISTRY] Built internal→display mapping for %d tasks",
            len(self._cached_internal_to_display)
        )
        return self._cached_metadata

    def resolve_to_document_title(self, name: str) -> str:
        """
        Convert internal name to document title for Qdrant search.

        Ex: "CmdStage" → "Cmd Stage"
            "Cmd Stage" → "Cmd Stage" (already a document title, returned as-is)

        Args:
            name: internal name or document title

        Returns:
            document title corresponding to the name
        
        Used by:
        - ChatAPI.STEP 3 to resolve required_tasks
        """
        # Ensure mapping is loaded
        if not self._cached_internal_to_display:
            self.get_task_metadata()

        resolved = self._cached_internal_to_display.get(name, name)

        if resolved != name:
            logger.debug("[REGISTRY] Resolved '%s' → '%s'", name, resolved)

        return resolved

    def resolve_list_to_document_titles(self, names: List[str]) -> List[str]:
        """
        Convert list of names (internal or display) to document titles.

        Ex: ["CmdStage", "JavaCode", "SetAndromateVariable", "Text Report"]
            → ["Cmd Stage", "Java Code", "Set Variable", "Text Report"]

        Args:
            names: list of names to resolve

        Returns:
            deduplicated list of document titles in original order
        
        Used by:
        - ChatAPI.STEP 3: resolved_tasks = rewriter.registry.resolve_list_to_document_titles(required_tasks)
        """
        seen = set()
        resolved = []
        for name in names:
            title = self.resolve_to_document_title(name)
            if title not in seen:
                seen.add(title)
                resolved.append(title)
        return resolved

    def get_internal_to_display_mapping(self) -> Dict[str, str]:
        """
        Return complete internal name → document title mapping.

        Returns:
            Dict ex: {"CmdStage": "Cmd Stage", "JavaCode": "Java Code", ...}
        
        Used by:
        - Any component needing the full mapping
        """
        if not self._cached_internal_to_display:
            self.get_task_metadata()
        return dict(self._cached_internal_to_display)

    # ==========================================================================
    # PUBLIC API — WorkflowPlanner methods
    # ==========================================================================

    def get_all_tasks(self) -> List[Dict]:
        """
        Return list of all available tasks.
        
        Returns:
            List of {"name", "description", "category", "document_title", ...}
        
        Used by:
        - WorkflowPlanner to get all tasks
        """
        now = time.time()
        if self._cached_tasks and (now - self._last_loaded) < self.cache_ttl:
            logger.debug("[REGISTRY] Returning cached tasks (%d tasks)", len(self._cached_tasks))
            return self._cached_tasks

        logger.info("[REGISTRY] Loading tasks from Qdrant...")
        self._refresh_cache()
        logger.info(
            "[REGISTRY] Loaded %d tasks: %s",
            len(self._cached_tasks),
            [t["name"] for t in self._cached_tasks]
        )
        return self._cached_tasks

    def get_task_by_name(self, name: str) -> Optional[Dict]:
        """
        Retrieve a single task specification by name.
        
        Args:
            name: task name (e.g., "CmdStage")
        
        Returns:
            Task dict or None if not found
        
        Used by:
        - WorkflowPlanner for task lookup
        """
        for task in self.get_all_tasks():
            if task["name"] == name:
                return task
        return None

    def get_task_descriptions(self) -> Dict[str, Dict[str, str]]:
        """
        Retrieve task documentation sections dynamically from Qdrant.

        Returns:
            Dict mapping task name to extracted sections:
                {
                    "CmdStage": {
                        "summary": "...",
                        "detailed_description": "...",
                        "input_parameters": "...",
                        "outputs": "...",
                        "document_title": "Cmd Stage"
                    },
                    ...
                }
        
        Used by:
        - WorkflowPlanner.plan() to provide task context to LLM
        
        IMPORTANT: This is cached separately to avoid repeated DB queries.
        Each call to plan() without cache would trigger 120 DB queries!
        """
        now = time.time()
        if self._cached_descriptions and (now - self._last_loaded) < self.cache_ttl:
            logger.debug(
                "[REGISTRY] Returning cached task descriptions (%d tasks)",
                len(self._cached_descriptions)
            )
            return self._cached_descriptions

        logger.info("[REGISTRY] Loading task descriptions from Qdrant...")
        task_names = self.get_task_names()
        descriptions: Dict[str, Dict[str, str]] = {}
        store = VectorStore(collection_name=self.collection_name)

        for task_name in task_names:
            try:
                document_text = store.get_document_text_by_title(
                    document_title=task_name,
                    doc_type="task_doc"
                )

                if document_text:
                    sections = extract_task_sections(document_text)
                    descriptions[task_name] = {
                        "summary": sections.get("summary", "") or "",
                        "detailed_description": sections.get("detailed_description", "") or "",
                        "input_parameters": sections.get("input_parameters", "") or "",
                        "outputs": sections.get("outputs", "") or "",
                        "document_title": task_name
                    }
                else:
                    descriptions[task_name] = {
                        "summary": f"Task: {task_name}",
                        "detailed_description": "",
                        "input_parameters": "",
                        "outputs": "",
                        "document_title": task_name
                    }

            except Exception as e:
                logger.warning(
                    "[REGISTRY] Failed to get description for %s: %s",
                    task_name, str(e)
                )
                descriptions[task_name] = {
                    "summary": f"Task: {task_name}",
                    "detailed_description": "",
                    "input_parameters": "",
                    "outputs": "",
                    "document_title": task_name
                }

        self._cached_descriptions = descriptions
        logger.info("[REGISTRY] Loaded descriptions for %d tasks", len(descriptions))
        return self._cached_descriptions

    # ==========================================================================
    # PRIVATE — Cache refresh and loading
    # ==========================================================================

    def _refresh_cache(self) -> None:
        """
        Refresh ALL caches at once (called when TTL expires).
        
        This ensures consistency — all components get synchronized data.
        """
        now = time.time()
        self._last_loaded = now

        # Load all tasks from Qdrant
        self._cached_tasks = self._load_from_qdrant()
        self._cached_names = [t["name"] for t in self._cached_tasks]
        
        # Build metadata with internal→display mapping
        self._build_metadata()

        # Clear descriptions cache to force reload on next call
        self._cached_descriptions = {}

    def _build_metadata(self) -> None:
        """
        Build task metadata and internal→display mapping.
        
        Extracted into separate method for clarity.
        """
        metadata = []
        internal_to_display: Dict[str, str] = {}
        store = VectorStore(collection_name=self.collection_name)

        for task_name in self._cached_names:
            if task_name in EXCLUDED_TASKS:
                logger.debug("[REGISTRY] Skipping excluded task: %s", task_name)
                continue

            purpose = ""
            try:
                document_text = store.get_document_text_by_title(
                    document_title=task_name,
                    doc_type="task_doc"
                )
                if document_text:
                    sections = extract_task_sections(document_text)
                    summary_text = sections.get("summary") or ""
                    detailed_desc = sections.get("detailed_description") or ""

                    # Extract internal name from summary
                    internal_name = self._extract_internal_name(summary_text)
                    if internal_name:
                        internal_to_display[internal_name] = task_name
                        logger.debug(
                            "[REGISTRY] Mapping: %s → %s",
                            internal_name, task_name
                        )

                    # Extract purpose
                    if detailed_desc.strip():
                        purpose = self._extract_purpose_from_summary(detailed_desc, task_name)
                    elif summary_text.strip():
                        purpose = self._extract_purpose_from_summary(summary_text, task_name)

            except Exception:
                logger.exception(
                    "[REGISTRY] Failed to load description for task: %s", task_name
                )

            metadata.append({
                "name": task_name,
                "summary": purpose
            })

        self._cached_metadata = metadata
        self._cached_internal_to_display = internal_to_display

    def _load_from_qdrant(self) -> List[Dict]:
        """
        Scroll through all task_doc chunks and extract unique task specs.
        
        Used by both QueryRewriter and WorkflowPlanner.
        """
        task_map: Dict[str, Dict] = {}
        offset = None

        try:
            while True:
                result, next_offset = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=self._build_task_filter(),
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )

                for point in result:
                    payload = point.payload
                    doc_title = payload.get("document_title", "")
                    content = payload.get("content", "")
                    section = payload.get("section_title", "")

                    if doc_title and doc_title not in task_map:
                        task_map[doc_title] = self._parse_task_spec(
                            name=doc_title,
                            content=content,
                            section=section,
                            payload=payload
                        )

                if next_offset is None:
                    break

                offset = next_offset

        except Exception as e:
            logger.exception("[REGISTRY] Failed to load tasks from Qdrant: %s", str(e))
            return list(task_map.values())

        return sorted(task_map.values(), key=lambda t: t["name"])

    @staticmethod
    def _build_task_filter():
        """Filter only task_doc documents."""
        return Filter(
            must=[
                FieldCondition(key="type_doc", match=MatchValue(value="task_doc"))
            ]
        )

    @staticmethod
    def _parse_task_spec(name: str, content: str, section: str, payload: Dict) -> Dict:
        """Extract task metadata from document content."""
        category = section.split("/")[-1] if section else "Other"
        description = content[:200].strip() if content else ""

        return {
            "name": name,
            "description": description,
            "category": category,
            "document_title": name,
            "content_snippet": content[:500],
            "payload": payload
        }

    # ==========================================================================
    # PRIVATE — Text extraction helpers
    # ==========================================================================

    @staticmethod
    def _extract_internal_name(summary_text: str) -> Optional[str]:
        """
        Extract internal name from Summary section.

        Looks for: **Internal name**: `CmdStage`

        Args:
            summary_text: content of Summary section

        Returns:
            internal name (ex: "CmdStage") or None if not found
        """
        if not summary_text:
            return None

        match = re.search(
            r'\*\*Internal name\*\*\s*:\s*`([^`]+)`',
            summary_text
        )
        if match:
            return match.group(1).strip()

        # Fallback without backticks
        match = re.search(
            r'\*\*Internal name\*\*\s*:\s*(\S+)',
            summary_text
        )
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def _extract_purpose_from_summary(summary_text: str, task_name: str) -> str:
        """
        Extract purpose from Summary section.
        
        Filters out noise (metadata fields, code blocks, etc.)
        and returns clean purpose text.
        
        Args:
            summary_text: content of Summary section
            task_name: name of task (for fallback)
        
        Returns:
            cleaned purpose text (max ~200 chars)
        """
        if not summary_text:
            return ""

        lines = summary_text.splitlines()
        purpose_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if any(prefix in stripped for prefix in [
                "**Internal name**",
                "**Category**",
                "**Purpose**",
                "**Minimum AndroMate",
                "**Maximum AndroMate",
                "**Minimum Android",
                "**Maximum Android",
                "**Supported manufacturers",
                "**Required permissions",
                "✅",
                "⚠️",
                "### Supported manufacturers",
                "### Required permissions",
                "### Compatibility",
                "## Compatibility",
                "## Input parameters",
                "## Outputs",
                "## Code examples",
                "## Flowchart",
                "## How it works",
                "## Note",
                "- Parameter:",
                "- Field:",
                "- ActionType:",
                "- `Action`:",
                "- `PackageName`:",
                "- `ClassName`:",
                "- `Data`:",
                "- `ActionType`:",
                "- `cmd_text`:",
                "- `root`:",
                "- `Action`",
                "- `PackageName`",
                "- `ClassName`",
                "- `Data`",
                "- `cmd_text`",
                "- `root`",
                "ActionType:",
                "Parameter:",
                "Field:",
                "```json",
                "```",
            ]):
                continue

            purpose_lines.append(stripped)

            if len(purpose_lines) >= 4:
                break

        result = " ".join(purpose_lines)
        result = re.sub(r"\*\*(.*?)\*\*", r"\1", result)
        result = re.sub(r"__(.*?)__", r"\1", result)
        result = re.sub(r"`([^`]+)`", r"\1", result)

        return result.strip()
