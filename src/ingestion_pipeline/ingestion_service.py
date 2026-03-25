# ingestion_service.py

"""
Ingestion service for RAG pipeline.

Handles the full pipeline: clean -> chunk -> embed -> store.
"""

from pathlib import Path
from typing import List, Dict
from src.ingestion_pipeline.document_cleaner import DocumentCleaner
from src.ingestion_pipeline.chunker import Chunker
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.schemas import Chunk
from src.utilities.logger import get_module_logger

logger = get_module_logger("ingestion_service")


def _map_type_doc_by_folder(folder_name: str) -> str:
    name = folder_name.lower()
    if "task" in name:
        return "task_doc"
    if "workflow" in name or "workflows" in name:
        return "workflow_doc"
    if "app" in name:
        return "app_doc"
    return "general_doc"


def clean_documents(raw_base: Path, processed_base: Path) -> List[Path]:
    cleaner = DocumentCleaner()
    processed_files = []

    for md_file in raw_base.rglob("*.md"):
        rel_path = md_file.relative_to(raw_base)
        out_path = processed_base / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cleaner.clean_file(md_file, out_path)
        processed_files.append(out_path)

    return processed_files


def chunk_documents(processed_files: List[Path], base_metadata: Dict[str, str], max_chunk_size: int = 200, overlap: int = 50) -> List[Chunk]:
    chunker = Chunker(max_chunk_size=max_chunk_size, overlap=overlap)
    all_chunks: List[Chunk] = []

    for processed in processed_files:
        text = processed.read_text(encoding="utf-8")
        
        # Use type_doc from base_metadata if provided, otherwise deduce from folder
        if "type_doc" in base_metadata:
            type_doc = base_metadata["type_doc"]
        else:
            type_doc = _map_type_doc_by_folder(processed.parent.name)
        
        metadata = {
            "document_id": processed.stem,
            "file_name": processed.name,
            "type_doc": type_doc,
            "document_title": processed.stem,
        }
        # Always use the raw doc_hash from base_metadata (calculated on raw upload content)
        # This ensures consistency: same hash used in add_document check and chunk storage
        if "doc_hash" not in metadata and "doc_hash" in base_metadata:
            metadata["doc_hash"] = base_metadata["doc_hash"]
        metadata.update(base_metadata)
        chunks = chunker.chunk(text, metadata)
        all_chunks.extend(chunks)

    return all_chunks


def embed_chunks(chunks: List[Chunk], model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
    embedder = Embedder(model_name=model_name)
    texts = [chunk.content for chunk in chunks]
    return embedder.embed_batch(texts)


def store_chunks(chunks: List[Chunk], embeddings: List[List[float]], collection_name: str = "andromate_docs") -> VectorStore:
    store = VectorStore(collection_name=collection_name)
    store.add_documents(chunks, embeddings)
    return store


def ingest_pipeline(
    raw_docs_root: Path,
    processed_root: Path,
    collection_name: str = "andromate_docs",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    base_metadata: Dict[str, str] = None,
) -> VectorStore:
    if base_metadata is None:
        base_metadata = {}

    processed_root.mkdir(parents=True, exist_ok=True)

    logger.info("[PIPELINE] Cleaning Markdown documents...")
    processed_files = clean_documents(raw_docs_root, processed_root)
    logger.info("[PIPELINE] Cleaned %d files", len(processed_files))

    logger.info("[PIPELINE] Chunking documents...")
    chunks = chunk_documents(processed_files, base_metadata)
    logger.info("[PIPELINE] Created %d chunks", len(chunks))

    logger.info("[PIPELINE] Embedding chunks...")
    embeddings = embed_chunks(chunks, model_name=model_name)
    logger.info("[PIPELINE] Generated %d embeddings", len(embeddings))

    logger.info("[PIPELINE] Storing chunks in vector store...")
    store = store_chunks(chunks, embeddings, collection_name=collection_name)
    logger.info("[PIPELINE] Finished ingestion to collection: %s", collection_name)

    return store


if __name__ == "__main__":
    raw_docs = Path("data/raw")
    processed_docs = Path("data/processed")
    ingest_pipeline(raw_docs, processed_docs)
