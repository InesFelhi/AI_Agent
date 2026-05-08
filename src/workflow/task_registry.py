"""
Task Registry — dynamically load all available tasks from Qdrant.

Responsibilities:
- Scroll through all task_doc chunks in Qdrant
- Extract unique task names (e.g., "CmdStage", "AppStage", "HttpRequest")
- Cache the list with TTL (default 10 min)
- Auto-refresh when TTL expires
- Provide tasks to LLM for informed decision-making

Enhanced Description Retrieval:
- Filter directly on section_title = "Summary"
- Extract ONLY the "Purpose" field from the summary
- Clean markdown and remove noise
- Return concise, structured descriptions optimized for LLM

Why this matters:
    With 120+ tasks, the system must KNOW all available options.

    This improved registry ensures:
    - Clean and precise task descriptions (no truncation noise)
    - Better LLM understanding (purpose-driven)
    - More accurate workflow generation
    - Scalable and dynamic (no hardcoded tasks)

    Add a new task doc → automatically available with clean description
"""

import re
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from src.ingestion_pipeline.task_section_extractor import extract_task_sections
from src.ingestion_pipeline.vector_store import VectorStore
from src.utilities.logger import get_module_logger

logger = get_module_logger("task_registry")


class TaskRegistry:
    """
    Dynamically load and cache all available Android workflow tasks.

    Example tasks: CmdStage, AppStage, HttpRequest, CompareStrings, etc.
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
        self._cached_tasks: List[Dict] = []
        self._last_loaded: float = 0.0

    def get_all_tasks(self) -> List[Dict]:
        """
        Return list of all available tasks, refreshing cache if TTL expired.
        """
        now = time.time()

        if self._cached_tasks and (now - self._last_loaded) < self.cache_ttl:
            logger.debug("[REGISTRY] Returning cached tasks (%d tasks)", len(self._cached_tasks))
            return self._cached_tasks

        logger.info("[REGISTRY] Loading tasks from Qdrant...")
        self._cached_tasks = self._load_from_qdrant()
        self._last_loaded = now

        logger.info(
            "[REGISTRY] Loaded %d tasks: %s",
            len(self._cached_tasks),
            [t["name"] for t in self._cached_tasks]
        )
        return self._cached_tasks

    def get_task_names(self) -> List[str]:
        """
        Return only task names (e.g., ["CmdStage", "AppStage", ...])
        """
        return [t["name"] for t in self.get_all_tasks()]

    def get_task_by_name(self, name: str) -> Optional[Dict]:
        """
        Retrieve a single task specification by name.
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
                    "summary": "...",
                    "detailed_description": "...",
                    "input_parameters": "...",
                    "outputs": "...",
                    "document_title": "..."
                }
        """
        descriptions: Dict[str, Dict[str, str]] = {}
        task_names = self.get_task_names()

        logger.info("[REGISTRY] Loading %d task descriptions from Qdrant...", len(task_names))
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

        logger.info("[REGISTRY] Loaded descriptions for %d tasks", len(descriptions))
        return descriptions

    @staticmethod
    def _extract_purpose(summary_text: str) -> str:
        """
        Extract the "Purpose" field from a Summary section.

        Example input:
            ## Summary
            - **Internal name**: `CmdStage`
            - **Category**: System
            - **Purpose**: Execute a shell command on the Android device

        Output:
            Execute a shell command on the Android device
        """
        purpose_match = re.search(
            r'\*\*Purpose\*\*\s*:\s*(.+?)(?:\n|$)',
            summary_text,
            re.IGNORECASE
        )
        if purpose_match:
            return purpose_match.group(1).strip()

        # Fallback cleaning
        clean = re.sub(r'#{1,6}\s+', '', summary_text)
        clean = re.sub(r'\*\*.*?\*\*\s*:\s*', '', clean)
        clean = re.sub(r'`[^`]+`', '', clean)
        clean = re.sub(r'[-•]\s+', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        return clean[:200] if clean else "Task available"

    def _load_from_qdrant(self) -> List[Dict]:
        """
        Scroll through all task_doc chunks and extract unique task specs.
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
        """
        Filter only task_doc documents.
        """
        return Filter(
            must=[
                FieldCondition(key="type_doc", match=MatchValue(value="task_doc"))
            ]
        )

    @staticmethod
    def _parse_task_spec(name: str, content: str, section: str, payload: Dict) -> Dict:
        """
        Extract task metadata from document content.
        """
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