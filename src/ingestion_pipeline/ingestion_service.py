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
    4. ingest_pipeline() — hash-based deduplication BEFORE clean step:
       skip unchanged docs, delete old chunks for updated docs.
       Mirrors rag_api.py logic exactly.
    5. BUG FIX — per-file hash isolation: base_metadata is never mutated
       across files. Each file gets its own hash injected into chunk metadata
       independently, preventing hash cross-contamination in multi-file runs.
"""

from pathlib import Path
from typing import List, Dict, Optional
import hashlib
from src.ingestion_pipeline.document_cleaner import DocumentCleaner
from src.ingestion_pipeline.chunker import Chunker
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
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


def _compute_file_hash(file_path: Path) -> str:
    """Compute MD5 hash of a file's raw bytes (same algo as rag_api.py)."""
    return hashlib.md5(file_path.read_bytes()).hexdigest()


def _check_existing_hash(store: VectorStore, document_id: str) -> Optional[str]:
    """
    Return the stored doc_hash for document_id, or None if not found.
    Uses a dummy zero-vector to filter by document_id (same pattern as rag_api.py).
    """
    try:
        hits = store.search(
            query_vector=[0.0] * 384,
            limit=1,
            filter_conditions={"document_id": document_id}
        )
        if hits:
            return hits[0].payload.get("doc_hash")
    except Exception as e:
        logger.warning(
            "[HASH_CHECK] Could not check existing hash for %s: %s", document_id, str(e)
        )
    return None


def infer_doc_type_from_path(path: Path) -> str:
    """
    Infer document type from the file path.

    Rules:
    - if any path component contains 'task'         -> task_doc
    - if any path component contains 'workflow'     -> workflow_doc
    - otherwise                                     -> app_doc

    This supports nested folders under docs/en, for example:
    - tasks/...     => task_doc
    - workflows/... => workflow_doc
    - support/...   => app_doc
    """
    normalized_parts = [part.lower() for part in path.parts]

    if any("task" in part for part in normalized_parts):
        return "task_doc"
    if any("workflow" in part for part in normalized_parts):
        return "workflow_doc"
    return "app_doc"


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

        if "type_doc" in base_metadata:
            type_doc = base_metadata["type_doc"]
        else:
            type_doc = infer_doc_type_from_path(processed)

        document_title = chunker._extract_document_title(text)

        metadata = {
            "document_id": processed.stem,
            "file_name": processed.name,
            "type_doc": type_doc,
            "document_title": document_title,
        }

        if "doc_hash" not in metadata and "doc_hash" in base_metadata:
            metadata["doc_hash"] = base_metadata["doc_hash"]

        metadata.update(base_metadata)
        chunks = chunker.chunk(text, metadata)
        all_chunks.extend(chunks)

    return all_chunks


# -------------------------------------------------------
# Step 2b — Chunk single file (used internally by pipeline)
# -------------------------------------------------------

def _chunk_single_file(
    processed_file: Path,
    file_metadata: Dict[str, str],
    max_chunk_size: int = 250,
    overlap: int = 60
) -> List[Chunk]:
    """
    Chunk a single processed file with its own isolated metadata.

    Used by ingest_pipeline() so each file carries its own doc_hash
    without polluting base_metadata shared across files.
    """
    chunker = Chunker(max_chunk_size=max_chunk_size, overlap=overlap)
    text = processed_file.read_text(encoding="utf-8")

    if "type_doc" not in file_metadata:
        file_metadata["type_doc"] = infer_doc_type_from_path(processed_file)

    document_title = chunker._extract_document_title(text)

    metadata = {
        "document_id": processed_file.stem,
        "file_name": processed_file.name,
        "type_doc": file_metadata["type_doc"],
        "document_title": document_title,
    }
    metadata.update(file_metadata)

    return chunker.chunk(text, metadata)


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
    sparse_vectors: Optional[List[Dict]] = None,
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
        HASH CHECK — Before any I/O, skip unchanged docs / delete stale chunks
        STEP 1 — Clean Markdown documents       (only files that changed)
        STEP 2 — Chunk documents into sections  (per-file isolated metadata)
        STEP 3 — Generate dense embeddings      (semantic similarity)
        STEP 4 — Generate sparse vectors        (BM25 keyword matching)
        STEP 5 — Store all chunks in Qdrant with both vector types

    Hash-based deduplication (mirrors rag_api.py logic, runs BEFORE clean):
        - If stored hash == current file hash  →  skip entirely (no I/O)
        - If stored hash != current file hash  →  delete old chunks, re-ingest
        - If no stored hash                    →  ingest as new document

    Multi-file hash isolation:
        - base_metadata is NEVER mutated — each file gets its own copy
          with its own doc_hash injected independently.
        - When called from rag_api (single file), base_metadata already
          contains doc_hash — used as-is.
        - When called standalone (multiple files), hash is computed per
          raw file and injected into a fresh copy of base_metadata.

    Args:
        raw_docs_root:   path to raw Markdown documents
        processed_root:  path where cleaned documents are written
        collection_name: Qdrant collection name
        model_name:      dense embedding model (SentenceTransformer)
        base_metadata:   metadata added to every chunk (never mutated)

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

    # --- HASH CHECK (BEFORE clean — same as rag_api.py) ---
    # Iterate raw files, check hash against Qdrant BEFORE any cleaning or I/O.
    # Only files that are new or changed will be cleaned and ingested.
    #
    # IMPORTANT: base_metadata is never mutated here.
    # Each file gets its own metadata dict with its own doc_hash.
    # This prevents hash cross-contamination across files in standalone runs.
    store = VectorStore(collection_name=collection_name)

    # List of (raw_file, file_metadata) tuples — one per file to ingest
    files_to_ingest: List[tuple[Path, Dict[str, str]]] = []
    all_raw_files = list(raw_docs_root.rglob("*.md"))

    for raw_file in all_raw_files:
        document_id = raw_file.stem

        # Determine hash for this specific file:
        # - rag_api path: base_metadata already has doc_hash (computed on upload bytes)
        # - standalone path: compute from raw file now
        if "doc_hash" in base_metadata:
            # Called from rag_api — use the injected hash directly
            current_hash = base_metadata["doc_hash"]
        else:
            # Called standalone — compute per file independently
            current_hash = _compute_file_hash(raw_file)

        stored_hash = _check_existing_hash(store, document_id)

        if stored_hash == current_hash:
            logger.info(
                "[PIPELINE] [SKIP] %s — hash unchanged (%s)", document_id, current_hash[:8]
            )
            continue  # already up to date, skip before any I/O

        if stored_hash is not None:
            # Document exists but content changed → delete old chunks before re-ingesting
            logger.info(
                "[PIPELINE] [UPDATE] %s — hash changed (%s → %s), deleting old chunks",
                document_id, stored_hash[:8], current_hash[:8]
            )
            try:
                store.delete_documents(filter_conditions={"document_id": document_id})
            except Exception as e:
                logger.warning(
                    "[PIPELINE] Could not delete old chunks for %s: %s", document_id, str(e)
                )
        else:
            logger.info("[PIPELINE] [NEW] %s — not found in store, ingesting", document_id)

        # Build this file's own metadata dict — never mutate base_metadata
        # so the next file in the loop starts clean.
        file_metadata = {**base_metadata, "doc_hash": current_hash}
        files_to_ingest.append((raw_file, file_metadata))

    if not files_to_ingest:
        logger.info("[PIPELINE] All documents are up to date — nothing to ingest.")
        logger.info("=" * 70)
        return store

    logger.info(
        "[PIPELINE] %d/%d file(s) need ingestion",
        len(files_to_ingest),
        len(all_raw_files)
    )

    # --- STEP 1 --- (only on files that passed hash check)
    logger.info("[PIPELINE] STEP 1/5: Cleaning Markdown documents...")
    cleaner = DocumentCleaner()

    # List of (processed_file, file_metadata) — preserves per-file metadata
    processed_pairs: List[tuple[Path, Dict[str, str]]] = []
    for raw_file, file_metadata in files_to_ingest:
        rel_path = raw_file.relative_to(raw_docs_root)
        out_path = processed_root / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cleaner.clean_file(raw_file, out_path)
        processed_pairs.append((out_path, file_metadata))

    logger.info("[PIPELINE] [OK] Cleaned %d files", len(processed_pairs))

    # --- STEP 2 --- (chunk each file with its own isolated metadata)
    logger.info("[PIPELINE] STEP 2/5: Chunking documents...")
    all_chunks: List[Chunk] = []
    for processed_file, file_metadata in processed_pairs:
        file_chunks = _chunk_single_file(processed_file, file_metadata)
        all_chunks.extend(file_chunks)
    logger.info("[PIPELINE] [OK] Created %d chunks", len(all_chunks))

    # --- STEP 3 ---
    logger.info("[PIPELINE] STEP 3/5: Generating dense embeddings...")
    dense_embeddings = embed_chunks(all_chunks, model_name=model_name)
    logger.info("[PIPELINE] [OK] Generated %d dense embeddings", len(dense_embeddings))

    # --- STEP 4 ---
    logger.info("[PIPELINE] STEP 4/5: Generating sparse BM25 vectors...")
    sparse_vectors = embed_sparse_chunks(all_chunks)
    logger.info("[PIPELINE] [OK] Generated %d sparse vectors", len(sparse_vectors))

    # --- STEP 5 ---
    logger.info("[PIPELINE] STEP 5/5: Storing chunks in vector store...")
    store = store_chunks(
        all_chunks,
        dense_embeddings,
        sparse_vectors,
        collection_name=collection_name
    )
    logger.info("[PIPELINE] [OK] Finished ingestion to collection: %s", collection_name)
    logger.info("=" * 70)

    return store


if __name__ == "__main__":
    raw_docs = Path("andromate_docs/docs/en")
    processed_docs = Path("data/processed")
    ingest_pipeline(raw_docs, processed_docs)