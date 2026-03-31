# src/api/rag_api.py
"""
RAG API for document ingestion and querying.

Provides endpoints to add documents and run the full ingestion pipeline.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import hashlib
import uuid
from typing import Optional, Literal
import time
from collections import defaultdict
from pydantic import BaseModel
from src.ingestion_pipeline.ingestion_service import ingest_pipeline
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.embedder import Embedder
from src.utilities.logger import get_module_logger
from src.llm.prompt import WORKFLOW_GENERATION_PROMPT, build_workflow_generation_prompt
from src.config import config

logger = get_module_logger("rag_api")

security = HTTPBearer()
client_request_times = defaultdict(list)


def _get_client_ip(request: Request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    provided_key = credentials.credentials if credentials else None
    if provided_key != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    client_ip = _get_client_ip(request)
    now = time.time()

    # Clean window and enforce rate limit
    window = [t for t in client_request_times[client_ip] if now - t < 60]
    if len(window) >= config.API_RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again later."
        )

    window.append(now)
    client_request_times[client_ip] = window


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Startup:
    - Load embedding model once at API startup (singleton pattern)
    
    Shutdown:
    - Clean up resources (optional)
    """
    # ===================== STARTUP =====================
    try:
        logger.info("=" * 70)
        logger.info("[STARTUP] Loading embedding model (lifespan)...")
        logger.info("=" * 70)
        Embedder.get_instance()
        logger.info("[SUCCESS] Embedding model loaded successfully at startup")
        logger.info("[SUCCESS] Model will be reused for ALL requests")
        logger.info("=" * 70)
    except Exception as e:
        logger.error("CRITICAL: Failed to load embedding model at startup")
        logger.exception("Startup error: %s", str(e))
        raise
    
    yield  # App runs here
    
    # ===================== SHUTDOWN =====================
    logger.info("=" * 70)
    logger.info("[SHUTDOWN] Cleaning up resources...")
    logger.info("=" * 70)


app = FastAPI(title=config.API_TITLE, version=config.API_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.CORS_ALLOW_ORIGINS) if config.CORS_ALLOW_ORIGINS != ("*",) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/health")
async def health_check():
    """Health check endpoint. No API key required."""
    try:
        # Optionally, verify Qdrant availability
        store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)
        # This call can raise if Qdrant unreachable
        store.client.get_collections()
        return {"status": "healthy", "qdrant": "available"}
    except Exception as e:
        logger.warning("Health check warning: %s", str(e))
        return {"status": "unhealthy", "error": str(e)}


@app.post("/add_document", dependencies=[Depends(verify_api_key)])
async def add_document(
    file: UploadFile = File(...),
    doc_type: Optional[Literal["task_doc", "workflow_doc", "app_doc", "general_doc"]] = Query(
        None,
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
        
        logger.info("[REQUEST] POST /add_document - Embedding model: REUSING singleton instance")
        
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
                collection_name=config.QDRANT_COLLECTION_NAME,
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
            low = str(e).lower()
            if "qdrant" in low or "vector store" in low or "timed out" in low or "timeout" in low:
                raise HTTPException(
                    status_code=503,
                    detail="Vector database temporarily unavailable"
                )
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
        lower = str(e).lower()
        if "vector store" in lower or "qdrant" in lower or "empty update request" in lower:
            raise HTTPException(
                status_code=503,
                detail="Vector database temporarily unavailable"
            )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

class QueryWorkflowRequest(BaseModel):
    question: str
    top_k: int = 5


@app.post("/query_workflow", dependencies=[Depends(verify_api_key)])
async def query_workflow(payload: QueryWorkflowRequest):
    """Embed user question, retrieve relevant docs and build prompt."""
    try:
        query_vector = Embedder.get_instance().embed_text(payload.question)
    except Exception as e:
        logger.exception("Failed creating embedding")
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")

    try:
        store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)
        points = store.search(query_vector=query_vector, limit=payload.top_k)
    except Exception as e:
        logger.exception("Failed vector search")
        raise HTTPException(status_code=503, detail=f"Vector store query error: {str(e)}")

    retrieved = [p.payload.get("content", "") for p in points]
    retrieved_content = "\n\n".join(retrieved).strip() or "No retrieved content"

    prompt = build_workflow_generation_prompt(
        context=retrieved_content,
        instruction=payload.question,
        examples=""
    )

    return {
        "question": payload.question,
        "prompt": prompt,
        "retrieved_content": retrieved,
        "top_k": payload.top_k
    }


@app.post("/add_documents", dependencies=[Depends(verify_api_key)])
async def add_documents(
    files: list[UploadFile] = File(...),
    doc_type: Optional[str] = Query(
        None,
        enum=["task_doc", "workflow_doc", "app_doc", "general_doc"],
        description="Optional: explicitly set document type for all files"
    )
):
    """
    Upload multiple Markdown documents in a single request.

    - Processes each document independently
    - Returns detailed report (success/failed)
    - Robust error handling per file
    - No halt on individual failures

    Parameters:
        files: Multiple Markdown files (.md extension required)
        doc_type: Optional type for all files (if not provided, inferred from filename)

    Returns:
        {
            "batch_id": "uuid",
            "total": 3,
            "success": 2,
            "failed": 1,
            "results": [
                {"file": "file1.md", "status": "success", "document_id": "file1"},
                {"file": "file2.md", "status": "success", "document_id": "file2"},
                {"file": "file3.md", "status": "error", "reason": "Invalid UTF-8"}
            ]
        }
    """
    
    batch_id = str(uuid.uuid4())[:8]
    results = []
    success_count = 0
    failed_count = 0

    logger.info("[BATCH %s] Starting batch ingestion with %d files", batch_id, len(files))
    logger.info("[BATCH %s] Embedding model: REUSING singleton instance", batch_id)

    for file in files:
        result = {
            "file": file.filename,
            "status": "error",
            "reason": None,
            "document_id": None
        }

        try:
            # Validate file extension
            if not file.filename.endswith(".md"):
                result["reason"] = "Only .md files are supported"
                failed_count += 1
                results.append(result)
                logger.warning("[BATCH %s] Skipped %s: invalid extension", batch_id, file.filename)
                continue

            # Determine doc_type
            file_doc_type = doc_type or infer_doc_type(file.filename)

            # Read content
            content = await file.read()

            # Validate file size
            max_size_bytes = 50 * 1024 * 1024
            if len(content) > max_size_bytes:
                result["reason"] = f"File too large ({len(content) / (1024*1024):.2f}MB, max 50MB)"
                failed_count += 1
                results.append(result)
                logger.warning("[BATCH %s] Skipped %s: size exceeds limit", batch_id, file.filename)
                continue

            # Validate UTF-8 encoding
            try:
                content.decode('utf-8')
            except UnicodeDecodeError as e:
                result["reason"] = f"Invalid UTF-8 encoding: {str(e)}"
                failed_count += 1
                results.append(result)
                logger.warning("[BATCH %s] Skipped %s: UTF-8 error", batch_id, file.filename)
                continue

            # Calculate doc hash
            doc_hash = hashlib.md5(content).hexdigest()
            document_id = Path(file.filename).stem

            logger.info("[BATCH %s] Processing: %s (type: %s, size: %dB)",
                       batch_id, document_id, file_doc_type, len(content))

            # Check if document exists
            try:
                store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)
                existing_hits = store.search(
                    query_vector=[0.0] * 384,
                    limit=1,
                    filter_conditions={"document_id": document_id}
                )
            except Exception as e:
                result["reason"] = f"Vector store connection failed: {str(e)}"
                failed_count += 1
                results.append(result)
                logger.error("[BATCH %s] Skipped %s: store error", batch_id, file.filename)
                continue

            # Check if unchanged
            if existing_hits and existing_hits[0].payload.get("doc_hash") == doc_hash:
                result["status"] = "skipped"
                result["reason"] = "Document up to date (hash match)"
                result["document_id"] = document_id
                success_count += 1
                results.append(result)
                logger.info("[BATCH %s] Skipped %s: unchanged", batch_id, file.filename)
                continue

            # Delete old chunks if needed
            if existing_hits:
                try:
                    store.delete_documents(filter_conditions={"document_id": document_id})
                    logger.info("[BATCH %s] Deleted old chunks for %s", batch_id, document_id)
                except Exception as e:
                    logger.warning("[BATCH %s] Failed to delete old chunks: %s", batch_id, str(e))

            # Save temp file
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            temp_path = temp_dir / Path(file.filename).name

            try:
                with open(temp_path, "wb") as f:
                    f.write(content)
            except IOError as e:
                result["reason"] = f"Failed to save file: {str(e)}"
                failed_count += 1
                results.append(result)
                logger.error("[BATCH %s] Failed to save %s", batch_id, file.filename)
                continue

            # Run ingestion pipeline
            try:
                raw_docs = temp_dir
                processed_docs = Path("data/processed")
                ingest_pipeline(
                    raw_docs,
                    processed_docs,
                    collection_name=config.QDRANT_COLLECTION_NAME,
                    base_metadata={"doc_hash": doc_hash, "type_doc": file_doc_type}
                )
                result["status"] = "success"
                result["document_id"] = document_id
                success_count += 1
                logger.info("[BATCH %s] Success: %s", batch_id, document_id)
            except ValueError as e:
                result["reason"] = f"Validation error: {str(e)}"
                failed_count += 1
                logger.error("[BATCH %s] Validation error for %s: %s", batch_id, document_id, str(e))
            except Exception as e:
                result["reason"] = f"Pipeline error: {str(e)}"
                failed_count += 1
                logger.exception("[BATCH %s] Pipeline failed for %s", batch_id, document_id)
            finally:
                # Cleanup
                try:
                    temp_path.unlink()
                except:
                    pass

            results.append(result)

        except Exception as e:
            result["reason"] = f"Unexpected error: {str(e)}"
            failed_count += 1
            results.append(result)
            logger.exception("[BATCH %s] Unexpected error for %s", batch_id, file.filename)

    logger.info("[BATCH %s] Completed: %d success, %d failed", batch_id, success_count, failed_count)

    return {
        "batch_id": batch_id,
        "total": len(files),
        "success": success_count,
        "failed": failed_count,
        "results": results
    }
