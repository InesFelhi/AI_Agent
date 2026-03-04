# schemas.py

"""
Schemas for AI Agent RAG pipeline.

Responsibilities:
- Define data models for chunks and documents
- Ensure structured and validated data with Pydantic
- Facilitate metadata management for retrieval and indexing
"""

from pydantic import BaseModel
from typing import Dict

class Chunk(BaseModel):
    """
    Represents a single text chunk ready for RAG processing.

    Attributes:
        id (str): Unique identifier for the chunk
        content (str): Text content of the chunk
        metadata (Dict): Dictionary of associated metadata
            e.g. {
                "document_id": "123",
                "type_doc": "task_doc",
                "section_title": "Introduction",
                "header_level": 1,
                "timestamp": "2026-02-27T02:00:00"
            }
    """
    id: str
    content: str
    metadata: Dict