"""Task registry for dynamic task metadata used by the query rewriter."""

import re
import time
from typing import Dict, List, Optional
from qdrant_client import QdrantClient
from src.ingestion_pipeline.task_section_extractor import extract_task_sections
from src.ingestion_pipeline.vector_store import VectorStore
from src.utilities.logger import get_module_logger

logger = get_module_logger("task_registry")

EXCLUDED_TASKS = {
    "Start",
    "End",
    "Tasks Overview"
}


class TaskNameRegistry:
    """Fetches and caches task names, summaries, and internal name mapping from Qdrant."""

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
        self._cached_metadata: List[Dict[str, str]] = []
        self._cached_internal_to_display: Dict[str, str] = {}  # {"CmdStage": "Cmd Stage"}
        self._last_loaded: float = 0.0

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------

    def get_task_names(self) -> List[str]:
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
        self._cached_metadata = []
        self._cached_internal_to_display = {}
        logger.info(
            "[REGISTRY] Loaded %d task names: %s",
            len(self._cached_names),
            self._cached_names
        )
        return self._cached_names

    def get_task_metadata(self) -> List[Dict[str, str]]:
        now = time.time()
        if self._cached_metadata and (now - self._last_loaded) < self.cache_ttl:
            logger.debug(
                "[REGISTRY] Returning cached task metadata (%d tasks)",
                len(self._cached_metadata)
            )
            return self._cached_metadata

        task_names = self.get_task_names()
        if not task_names:
            return []

        logger.info("[REGISTRY] Loading task summaries for %d tasks...", len(task_names))
        store = VectorStore(collection_name=self.collection_name)
        metadata = []
        internal_to_display: Dict[str, str] = {}

        for task_name in task_names:
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

                    # --- Extraire l'internal name depuis la summary ---
                    internal_name = self._extract_internal_name(summary_text)
                    if internal_name:
                        internal_to_display[internal_name] = task_name
                        logger.debug(
                            "[REGISTRY] Mapping: %s → %s",
                            internal_name, task_name
                        )

                    # --- Extraire le purpose ---
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

        logger.info(
            "[REGISTRY] Built internal→display mapping for %d tasks: %s",
            len(internal_to_display),
            internal_to_display
        )

        return self._cached_metadata

    def resolve_to_document_title(self, name: str) -> str:
        """
        Convertit un internal name en document title pour la recherche Qdrant.

        Ex: "CmdStage" → "Cmd Stage"
            "Cmd Stage" → "Cmd Stage" (déjà un document title, retourné tel quel)

        Args:
            name: internal name ou document title

        Returns:
            document title correspondant
        """
        # S'assurer que le mapping est chargé
        if not self._cached_internal_to_display:
            self.get_task_metadata()

        resolved = self._cached_internal_to_display.get(name, name)

        if resolved != name:
            logger.debug("[REGISTRY] Resolved '%s' → '%s'", name, resolved)

        return resolved

    def resolve_list_to_document_titles(self, names: List[str]) -> List[str]:
        """
        Convertit une liste de noms (internal ou display) en document titles.

        Ex: ["CmdStage", "JavaCode", "SetAndromateVariable", "Text Report"]
            → ["Cmd Stage", "Java Code", "Set Variable", "Text Report"]

        Args:
            names: liste de noms à résoudre

        Returns:
            liste de document titles dédupliquée en préservant l'ordre
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
        Retourne le mapping complet internal name → document title.

        Returns:
            Dict ex: {"CmdStage": "Cmd Stage", "JavaCode": "Java Code", ...}
        """
        if not self._cached_internal_to_display:
            self.get_task_metadata()
        return dict(self._cached_internal_to_display)

    # --------------------------------------------------
    # Private helpers
    # --------------------------------------------------

    @staticmethod
    def _extract_internal_name(summary_text: str) -> Optional[str]:
        """
        Extrait l'internal name depuis la section Summary.

        Cherche la ligne: **Internal name**: `CmdStage`

        Args:
            summary_text: contenu de la section Summary

        Returns:
            internal name (ex: "CmdStage") ou None si non trouvé
        """
        if not summary_text:
            return None

        match = re.search(
            r'\*\*Internal name\*\*\s*:\s*`([^`]+)`',
            summary_text
        )
        if match:
            return match.group(1).strip()

        # Fallback sans backticks
        match = re.search(
            r'\*\*Internal name\*\*\s*:\s*(\S+)',
            summary_text
        )
        if match:
            return match.group(1).strip()

        return None

    @staticmethod
    def _extract_purpose_from_summary(summary_text: str, task_name: str) -> str:
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

    def _load_from_qdrant(self) -> List[str]:
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
                    with_vectors=False
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