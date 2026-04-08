# ingestion_service.py

"""
Ingestion service for RAG pipeline.

Handles the full pipeline: clean -> chunk -> embed dense -> embed sparse -> store.

Changes from previous version:
    1. embed_sparse_chunks() — new function, generates BM25 sparse vectors
       using SparseEmbedder singleton, same pattern as embed_chunks().
    2. store_chunks() — accepts optional sparse_vectors parameter and
       passes it to VectorStore.add_documents().
    3. ingest_pipeline() — pipeline extended from 4 to 5 steps, adding
       sparse embedding between dense embedding and storage.
"""

from pathlib import Path
from typing import List, Dict, Optional
from src.ingestion_pipeline.document_cleaner import DocumentCleaner
from src.ingestion_pipeline.chunker import Chunker
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder   # NEW
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.schemas import Chunk
from src.utilities.logger import get_module_logger

logger = get_module_logger("ingestion_service")


# -------------------------------------------------------
# Helpers 
# -------------------------------------------------------

def _map_type_doc_by_folder(folder_name: str) -> str:
    name = folder_name.lower()
    if "task" in name:
        return "task_doc"
    if "workflow" in name or "workflows" in name:
        return "workflow_doc"
    if "app" in name:
        return "app_doc"
    return "general_doc"


# -------------------------------------------------------
# Step 1 — Clean
# -------------------------------------------------------

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


# -------------------------------------------------------
# Step 2 — Chunk
# -------------------------------------------------------

def chunk_documents(
    processed_files: List[Path],
    base_metadata: Dict[str, str],
    max_chunk_size: int = 250,
    overlap: int = 60
) -> List[Chunk]:
    chunker = Chunker(max_chunk_size=max_chunk_size, overlap=overlap)
    all_chunks: List[Chunk] = []

    for processed in processed_files:
        text = processed.read_text(encoding="utf-8")

        # Use type_doc from base_metadata if provided, otherwise deduce from folder
        if "type_doc" in base_metadata:
            type_doc = base_metadata["type_doc"]
        else:
            type_doc = _map_type_doc_by_folder(processed.parent.name)

        # Extract the real document title from the markdown content (# ... header)
        # Example: "cmd.md" -> read content -> find "# Cmd Stage" -> document_title = "Cmd Stage"
        document_title = chunker._extract_document_title(text)

        metadata = {
            "document_id": processed.stem,
            "file_name": processed.name,
            "type_doc": type_doc,
            "document_title": document_title,  # Use the real title, not just filename
        }

        # Always use the raw doc_hash from base_metadata (calculated on raw upload content)
        # This ensures consistency: same hash used in add_document check and chunk storage
        if "doc_hash" not in metadata and "doc_hash" in base_metadata:
            metadata["doc_hash"] = base_metadata["doc_hash"]

        metadata.update(base_metadata)
        chunks = chunker.chunk(text, metadata)
        all_chunks.extend(chunks)

    return all_chunks


# -------------------------------------------------------
# Step 3 — Embed dense  
# -------------------------------------------------------

def embed_chunks(
    chunks: List[Chunk],
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> List[List[float]]:
    """
    Generate dense float embeddings for chunks using singleton Embedder.

    Args:
        chunks:     list of Chunk objects
        model_name: model used only on first call, ignored on subsequent calls

    Returns:
        List of dense embedding vectors  [[float, ...], ...]
    """
    logger.info("[EMBED_DENSE] Using singleton embedder for %d chunks", len(chunks))
    embedder = Embedder.get_instance(model_name=model_name)
    texts = [chunk.content for chunk in chunks]
    embeddings = embedder.embed_batch(texts)
    logger.info("[EMBED_DENSE] [OK] Generated %d dense embeddings", len(embeddings))
    return embeddings


# -------------------------------------------------------
# Step 4 — Embed sparse 
# -------------------------------------------------------

def embed_sparse_chunks(chunks: List[Chunk]) -> List[Dict]:
    """
    Generate BM25 sparse vectors for chunks using singleton SparseEmbedder.

    Why: dense embeddings miss exact technical tokens like "CmdStage",
    "cmd_text", "IntegerSingleOps". BM25 sparse vectors score these
    rare tokens highly, enabling hybrid search to surface the right
    task documentation regardless of query language.

    Args:
        chunks: list of Chunk objects (same list passed to embed_chunks)

    Returns:
        List of sparse vector dicts: [{"indices": [...], "values": [...]}, ...]
        Each dict corresponds to one chunk in the same order.
        Passed directly to VectorStore.add_documents() as sparse_vectors.
    """
    logger.info("[EMBED_SPARSE] Using singleton sparse embedder for %d chunks", len(chunks))
    sparse_embedder = SparseEmbedder.get_instance()
    texts = [chunk.content for chunk in chunks]
    sparse_vectors = sparse_embedder.embed_batch(texts)
    logger.info("[EMBED_SPARSE] [OK] Generated %d sparse vectors", len(sparse_vectors))
    return sparse_vectors


# -------------------------------------------------------
# Step 5 — Store 
# -------------------------------------------------------

def store_chunks(
    chunks: List[Chunk],
    dense_embeddings: List[List[float]],
    sparse_vectors: Optional[List[Dict]] = None,    # NEW — optional for compatibility
    collection_name: str = "andromate_docs"
) -> VectorStore:
    """
    Store chunks with their dense and sparse vectors into Qdrant.

    Args:
        chunks:           list of Chunk objects
        dense_embeddings: dense float vectors from embed_chunks()
        sparse_vectors:   BM25 sparse dicts from embed_sparse_chunks()
                          Optional — if None, only dense vectors are stored
                          (backward compatible with old callers)
        collection_name:  Qdrant collection name

    Returns:
        VectorStore instance
    """
    store = VectorStore(collection_name=collection_name)
    store.add_documents(chunks, dense_embeddings, sparse_vectors)
    return store


# -------------------------------------------------------
# Full pipeline orchestrator  
# -------------------------------------------------------

def ingest_pipeline(
    raw_docs_root: Path,
    processed_root: Path,
    collection_name: str = "andromate_docs",
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    base_metadata: Dict[str, str] = None,
) -> VectorStore:
    """
    Run the full ingestion pipeline:
        STEP 1 — Clean Markdown documents
        STEP 2 — Chunk documents into sections
        STEP 3 — Generate dense embeddings  (semantic similarity)
        STEP 4 — Generate sparse vectors    (BM25 keyword matching)  NEW
        STEP 5 — Store all chunks in Qdrant with both vector types

    Args:
        raw_docs_root:  path to raw Markdown documents
        processed_root: path where cleaned documents are written
        collection_name: Qdrant collection name
        model_name:     dense embedding model (SentenceTransformer)
        base_metadata:  metadata added to every chunk

    Returns:
        VectorStore instance connected to the populated collection
    """
    if base_metadata is None:
        base_metadata = {}

    logger.info("=" * 70)
    logger.info("[PIPELINE] Starting ingestion pipeline")
    logger.info("[PIPELINE] Collection : %s", collection_name)
    logger.info("[PIPELINE] Dense model: %s", model_name)
    logger.info("[PIPELINE] Sparse model: Qdrant/bm25 (FastEmbed)")
    logger.info("=" * 70)

    processed_root.mkdir(parents=True, exist_ok=True)

    # --- STEP 1 ---
    logger.info("[PIPELINE] STEP 1/5: Cleaning Markdown documents...")
    processed_files = clean_documents(raw_docs_root, processed_root)
    logger.info("[PIPELINE] [OK] Cleaned %d files", len(processed_files))

    # --- STEP 2 ---
    logger.info("[PIPELINE] STEP 2/5: Chunking documents...")
    chunks = chunk_documents(processed_files, base_metadata)
    logger.info("[PIPELINE] [OK] Created %d chunks", len(chunks))

    # --- STEP 3 ---
    logger.info("[PIPELINE] STEP 3/5: Generating dense embeddings...")
    dense_embeddings = embed_chunks(chunks, model_name=model_name)
    logger.info("[PIPELINE] [OK] Generated %d dense embeddings", len(dense_embeddings))

    # --- STEP 4  ---
    logger.info("[PIPELINE] STEP 4/5: Generating sparse BM25 vectors...")
    sparse_vectors = embed_sparse_chunks(chunks)
    logger.info("[PIPELINE] [OK] Generated %d sparse vectors", len(sparse_vectors))

    # --- STEP 5 ---
    logger.info("[PIPELINE] STEP 5/5: Storing chunks in vector store...")
    store = store_chunks(
        chunks,
        dense_embeddings,
        sparse_vectors,
        collection_name=collection_name
    )
    logger.info("[PIPELINE] [OK] Finished ingestion to collection: %s", collection_name)
    logger.info("=" * 70)

    return store


if __name__ == "__main__":
    raw_docs = Path("data/raw")
    processed_docs = Path("data/processed")
    ingest_pipeline(raw_docs, processed_docs)