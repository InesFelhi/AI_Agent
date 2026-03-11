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
        id (str): Unique identifier (UUID) for the chunk
        content (str): Text content of the chunk (includes section header)
        metadata (Dict): Dictionary of associated metadata including:
            Core identifiers:
                - document_id (str): Unique source document identifier
                - file_name (str): Original markdown filename
                - type_doc (str): Document type (task_doc, workflow_doc, app_doc)
                
            Hierarchical information:
                - task_name (str): Task or document title (extracted from # header)
                - section_title (str): Section/subsection header
                - section_level (int): Header level (1, 2, or 3)
                - hierarchy_path (str): Full hierarchical path (e.g., "Http Request > Input parameters")
                
            Chunk information:
                - chunk_index (int): Sequential position of chunk in entire document
                - word_count (int): Number of words in chunk content
                - start_word (int): Starting word position within section
                - end_word (int): Ending word position within section
                
            Tracking:
                - timestamp (str): ISO format creation timestamp
            
            Example:
            {
                "document_id": "f11c7cbd-fbd7-4e15-b3de-b1d4ca24818e",
                "file_name": "http-request.md",
                "type_doc": "task_doc",
                "task_name": "Http Request Stage",
                "section_title": "Input parameters",
                "section_level": 2,
                "hierarchy_path": "Http Request Stage > Input parameters",
                "chunk_index": 5,
                "word_count": 127,
                "start_word": 50,
                "end_word": 177,
                "timestamp": "2026-03-11T01:11:07.179254"
            }
    """
    id: str
    content: str
    metadata: Dict