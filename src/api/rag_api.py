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
    try:
        # Validate file extension
        if not file.filename.endswith(".md"):
            raise HTTPException(status_code=400, detail="Only .md files are supported")

        # Determine doc_type with priority: explicit param > filename inference > default
        if not doc_type:
            doc_type = infer_doc_type(file.filename)
        
        # Read content
        content = await file.read()
        
        # Validate file size (max 50MB)
        max_size_bytes = 50 * 1024 * 1024  # 50MB
        if len(content) > max_size_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: 50MB, received: {len(content) / (1024*1024):.2f}MB"
            )
        
        # Validate UTF-8 encoding
        try:
            content.decode('utf-8')
        except UnicodeDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail=f"File must be UTF-8 encoded. Error: {str(e)}"
            )
        
        # Calculate doc hash
        doc_hash = hashlib.md5(content).hexdigest()
        document_id = Path(file.filename).stem

        logger.info("Processing document: %s (type: %s, size: %dB)", 
                   document_id, doc_type, len(content))

        # Check if document exists and is up to date
        try:
            store = VectorStore(collection_name="andromate_docs")
            existing_hits = store.search(
                query_vector=[0.0] * 384,  # dummy vector for existence check
                limit=1,
                filter_conditions={"document_id": document_id}
            )
        except Exception as e:
            logger.error("Failed to connect to vector store: %s", str(e))
            raise HTTPException(
                status_code=503,
                detail="Vector database temporarily unavailable"
            )

        # Check if document unchanged
        if existing_hits and existing_hits[0].payload.get("doc_hash") == doc_hash:
            logger.info("Document is up to date (hash match) - document_id: %s", document_id)
            return {"message": "Document is up to date", "document_id": document_id}

        # If document exists but content changed, delete old chunks
        if existing_hits:
            try:
                logger.info("Document exists but hash differs - deleting old version: %s", document_id)
                store.delete_documents(filter_conditions={"document_id": document_id})
            except Exception as e:
                logger.warning("Failed to delete old chunks: %s", str(e))
                # Continue anyway, upsert will overwrite

        # Save uploaded file temporarily
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_path = temp_dir / Path(file.filename).name  # Use .name for security

        try:
            with open(temp_path, "wb") as f:
                f.write(content)
        except IOError as e:
            logger.error("Failed to write temp file: %s", str(e))
            raise HTTPException(
                status_code=500,
                detail="Failed to save uploaded file"
            )

        # Run full ingestion pipeline
        try:
            raw_docs = temp_dir
            processed_docs = Path("data/processed")
            ingest_pipeline(
                raw_docs,
                processed_docs,
                collection_name="andromate_docs",
                base_metadata={"doc_hash": doc_hash, "type_doc": doc_type}
            )
        except ValueError as e:
            logger.error("Pipeline validation error: %s", str(e))
            raise HTTPException(
                status_code=400,
                detail=f"Document processing error: {str(e)}"
            )
        except Exception as e:
            logger.exception("Pipeline processing failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to process document. Check server logs."
            )
        finally:
            # Clean up temp file
            try:
                temp_path.unlink()
            except Exception as e:
                logger.warning("Failed to delete temp file: %s", str(e))

        logger.info("Document added and indexed successfully: %s", document_id)
        return {"message": "Document added and indexed", "document_id": document_id}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception("Unexpected error in add_document")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}