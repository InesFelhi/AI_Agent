# chunker.py

"""
Chunker module for AI Agent RAG pipeline.

Responsibilities:
- Split cleaned documents into logical chunks
- Preserve header hierarchy (#, ##, ###)
- Handle overlap between chunks safely
- Assign metadata
- Avoid infinite loops for small texts
"""

from typing import List, Tuple
from src.ingestion_pipeline.schemas import Chunk
from src.utilities.logger import get_module_logger
import uuid
import re
from datetime import datetime

logger = get_module_logger("chunker")


class Chunker:
    def __init__(self, max_chunk_size: int = 500, overlap: int = 50):
        """
        Args:
            max_chunk_size: maximum number of words per chunk
            overlap: number of words to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

        if overlap >= max_chunk_size:
            raise ValueError("overlap must be smaller than max_chunk_size")

        logger.info(
            "Chunker initialized (max_chunk_size=%d, overlap=%d)",
            max_chunk_size,
            overlap
        )

    # ---------------- Public API ----------------
    def chunk(self, text: str, metadata: dict) -> List[Chunk]:
        """
        Split text into logical chunks respecting headers.

        Args:
            text: cleaned text
            metadata: metadata to add to each chunk

        Returns:
            List[Chunk]: list of Pydantic Chunk
        """
        logger.info(
            "Starting chunking process for document_id=%s",
            metadata.get("document_id")
        )

        # Extract document title from first main header if not provided
        if "document_title" not in metadata:
            metadata["document_title"] = self._extract_document_title(text)

        sections = self._split_by_headers(text)
        all_chunks: List[Chunk] = []
        chunk_index = 0

        for header_level, section_text, section_title in sections:

            section_meta = metadata.copy()
            section_meta.update({
                "header_level": header_level,
                "section_title": section_title,
                "hierarchy_path": f"{metadata.get('document_title', 'Unknown')} > {section_title}"
            })

            chunks_in_section = self._chunk_text(
                section_text,
                section_meta,
                header_level,
                section_title,
                chunk_index
            )

            all_chunks.extend(chunks_in_section)
            chunk_index += len(chunks_in_section)

            logger.info(
                "Created %d chunks for section '%s'",
                len(chunks_in_section),
                section_title
            )

        logger.info("Total chunks created: %d", len(all_chunks))
        return all_chunks

    # ---------------- Internal Methods ----------------
    def _split_by_headers(self, text: str) -> List[Tuple[int, str, str]]:
        """
        Split text into sections based on headers (#, ##, ###).

        Returns:
            List[Tuple[header_level, section_text, section_title]]
        """
        lines = text.splitlines()
        sections = []

        current_header = 0
        current_title = "Introduction"
        current_text: List[str] = []

        header_pattern = re.compile(r"^(#{1,3})\s+(.*)$")

        for line in lines:
            match = header_pattern.match(line)

            if match:
                # Save previous section
                if current_text:
                    sections.append(
                        (current_header,
                         "\n".join(current_text).strip(),
                         current_title)
                    )
                    current_text = []

                current_header = len(match.group(1))
                current_title = match.group(2).strip()
            else:
                current_text.append(line)

        # Add last section
        if current_text:
            sections.append(
                (current_header,
                 "\n".join(current_text).strip(),
                 current_title)
            )

        return sections

    def _extract_document_title(self, text: str) -> str:
        """
        Extract document title from first main header (#).
        Works for all document types (task_doc, workflow_doc, app_doc).
        
        Args:
            text: document text
        
        Returns:
            str: document title or 'Unknown Document'
        """
        lines = text.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return 'Unknown Document'

    def _chunk_text(
        self,
        text: str,
        metadata: dict,
        header_level: int,
        section_title: str,
        chunk_index: int = 0
    ) -> List[Chunk]:
        """
        Split a section into chunks with overlap.

        Args:
            text: section text
            metadata: metadata to attach to each chunk
            header_level: header level of section
            section_title: title of section

        Returns:
            List[Chunk]
        """
        words = text.split()

        if not words:
            return []

        chunks: List[Chunk] = []
        start = 0
        total_words = len(words)
        section_chunk_index = 0

        # Create header prefix to inject inside chunk content
        header_prefix = f"{'#' * header_level} {section_title}\n\n" if header_level > 0 else ""

        while start < total_words:

            end = min(start + self.max_chunk_size, total_words)

            chunk_body = " ".join(words[start:end])

            #  Inject header inside chunk content
            chunk_text = header_prefix + chunk_body

            chunk_id = str(uuid.uuid4())

            # Create enriched metadata for this chunk
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": chunk_index + section_chunk_index,
                "word_count": len(chunk_body.split()),
                "start_word": start,
                "end_word": end,
                "timestamp": datetime.now().isoformat()
            })

            chunks.append(
                Chunk(
                    id=chunk_id,
                    content=chunk_text,
                    metadata=chunk_metadata
                )
            )

            logger.debug(
                "Chunk %s created (words %d-%d)",
                chunk_id,
                start,
                end
            )

            section_chunk_index += 1

            # Stop if we reached end
            if end == total_words:
                break

            # Safe next start position
            start = end - self.overlap

            # Absolute safety guard
            if start < 0:
                start = 0

            if start >= total_words:
                break

        return chunks