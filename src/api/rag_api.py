# src/api/rag_api.py
"""
RAG API for document ingestion and querying.

Provides endpoints to add documents and run the full ingestion pipeline.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from pathlib import Path
import hashlib
from typing import Optional
from src.ingestion_pipeline.ingestion_service import ingest_pipeline
from src.ingestion_pipeline.vector_store import VectorStore
from src.utilities.logger import get_module_logger

logger = get_module_logger("rag_api")

app = FastAPI(title="AndroMate RAG API", version="1.0.0")


def infer_doc_type(filename: str) -> str:
    """
    Infer document type from filename.
    
    Priority: exact prefix match > substring match > general_doc
    Examples: task-cmd.md → task_doc, workflow-intro.md → workflow_doc
    """
    name_lower = filename.lower()
    
    # Check for task prefixes
    if name_lower.startswith("task") or "task" in name_lower:
        return "task_doc"
    
    # Check for workflow prefixes
    if name_lower.startswith("workflow") or "workflow" in name_lower:
        return "workflow_doc"
    
    # Check for app prefixes
    if name_lower.startswith("app") or "app" in name_lower:
        return "app_doc"
    
    return "general_doc"

@app.post("/add_document")
async def add_document(
    file: UploadFile = File(...),
    doc_type: Optional[str] = Query(
        None,
        enum=["task_doc", "workflow_doc", "app_doc", "general_doc"],
        description="Optional: explicitly set document type. If not provided, will be inferred from filename"
    )
):
    """
    Upload a Markdown document and run the full ingestion pipeline.

    - Cleans the document
    - Chunks it
    - Generates embeddings
    - Stores in vector database

    Handles updates if document already exists.
    
    Parameters:
        file: Markdown file to upload (.md extension required)
        doc_type: Optional document type (task_doc, workflow_doc, app_doc, or general_doc)
                 If not provided, will be inferred from filename
                 Examples: task-cmd.md → task_doc, workflow-intro.md → workflow_doc
    """
    if not file.filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Only .md files are supported")

    # Determine doc_type with priority: explicit param > filename inference > default
    if not doc_type:
        doc_type = infer_doc_type(file.filename)
    
    # Read content
    content = await file.read()
    doc_hash = hashlib.md5(content).hexdigest()
    document_id = Path(file.filename).stem

    logger.info("Processing document: %s (type: %s)", document_id, doc_type)

    # Check if document exists and is up to date
    store = VectorStore(collection_name="andromate_docs")
    existing_hits = store.search(
        query_vector=[0.0] * 384,  # dummy vector for existence check
        limit=1,
        filter_conditions={"document_id": document_id}
    )

    if existing_hits and existing_hits[0].payload.get("doc_hash") == doc_hash:
        logger.info("Document is up to date (hash match) - document_id: %s", document_id)
        return {"message": "Document is up to date", "document_id": document_id}

    # If document exists but content changed, delete old chunks
    if existing_hits:
        logger.info("Document exists but hash differs - deleting old version: %s", document_id)
        store.delete_documents(filter_conditions={"document_id": document_id})

    # Save uploaded file temporarily
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / file.filename

    with open(temp_path, "wb") as f:
        f.write(content)

    # Run full ingestion pipeline with document hash and type in metadata
    raw_docs = temp_dir
    processed_docs = Path("data/processed")
    ingest_pipeline(
        raw_docs,
        processed_docs,
        collection_name="andromate_docs",
        base_metadata={"doc_hash": doc_hash, "type_doc": doc_type}
    )

    # Clean up temp file
    temp_path.unlink()

    logger.info("Document added and indexed successfully: %s", document_id)
    return {"message": "Document added and indexed", "document_id": document_id}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}