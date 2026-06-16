import json
import asyncio
import time
import hashlib
from typing import Any, Dict, List, Optional
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from pydantic import BaseModel, Field

from src.config import config
from src.monitoring import REQUEST_COUNTER, ACTIVE_REQUESTS, REQUEST_DURATION, HTTP_STATUS_CODE_TOTAL, SERVER_UP

from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.vector_store import VectorStore

from src.ingestion_pipeline.task_section_extractor import (
    build_workflow_context_for_tasks
)

from src.clients import get_qdrant_client, get_llm_client

from src.prompts import (
    build_workflow_generation_prompt,
    build_workflow_correction_prompt,
    build_qa_prompt
)

from src.rag.query_rewriter import QueryRewriter

from src.workflow.workflow_planner import WorkflowPlanner
from src.workflow.workflow_processor import WorkflowProcessor

from src.utilities.logger import get_module_logger

logger = get_module_logger("chat_api")

security = HTTPBearer()

# =========================================================
# GLOBAL STATE - Memory Management
# =========================================================

client_request_times: Dict[str, datetime] = {}
cleanup_task: Optional[asyncio.Task] = None

# Request response cache (1 hour TTL)
response_cache: Dict[str, tuple] = {}  # Format: {cache_key: (response_dict, timestamp)}
CACHE_TTL_SECONDS = 3600  # 1 hour


# =========================================================
# MODELS
# =========================================================

class ChatRequest(BaseModel):
    """Request model with comprehensive validation."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User query (1-5000 characters)"
    )
    type_intent: Optional[str] = Field(
        default=None,
        pattern="^(workflow_generation|workflow_correction|qa)?$",
        description="Optional: workflow_generation, workflow_correction, or qa"
    )
    workflow: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional workflow object for correction"
    )
    provider: Optional[str] = Field(
        default=None,
        pattern="^(openai|ollama|openrouter)?$",
        description="Optional LLM provider override"
    )


class WorkflowResult(BaseModel):
    """Structured result for workflow generation and correction."""
    workflow: Dict[str, Any]
    explanation: str
    validation_passed: bool
    retry_count: int
    errors_found: List[str] = []


class ChatResponse(BaseModel):
    intent: str
    task_names: List[str]
    result: Any  # Union[WorkflowResult, Dict[str, Any], str] depending on intent
    metadata: Dict[str, Any]


# =========================================================
# MEMORY CLEANUP
# =========================================================

async def cleanup_old_client_requests(interval_seconds: int = 300, max_age_hours: int = 1):
    """
    Background task to clean up stale client_request_times entries and expired cache.
    
    Runs every 'interval_seconds' and removes entries older than 'max_age_hours'.
    This prevents memory leaks from unbounded dict growth.
    
    Args:
        interval_seconds: How often to run cleanup (default: 300 = 5 min)
        max_age_hours: Remove entries older than this (default: 1 hour)
    """
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            now = datetime.now()
            cutoff_time = now - timedelta(hours=max_age_hours)
            
            # Find expired client entries
            expired_clients = [
                client_id for client_id, timestamp in client_request_times.items()
                if timestamp < cutoff_time
            ]
            
            # Remove expired client entries
            for client_id in expired_clients:
                del client_request_times[client_id]
            
            if expired_clients:
                logger.info(
                    "[MEMORY] Cleaned up %d stale client entries (older than %d hours). "
                    "Current clients tracked: %d",
                    len(expired_clients), max_age_hours, len(client_request_times)
                )
            
            # Cleanup expired cache entries
            expired_cache_keys = [
                key for key, (_, timestamp) in response_cache.items()
                if (now - timestamp).total_seconds() > CACHE_TTL_SECONDS
            ]
            
            for key in expired_cache_keys:
                del response_cache[key]
            
            if expired_cache_keys:
                logger.info(
                    "[CACHE] Cleaned up %d expired cache entries. "
                    "Current cache size: %d",
                    len(expired_cache_keys), len(response_cache)
                )
        except Exception as e:
            logger.error("[MEMORY] Error in cleanup task: %s", str(e))
            # Continue cleanup even on error
            continue


def generate_cache_key(query: str, intent: Optional[str], workflow: Optional[Dict]) -> str:
    """
    Generate a cache key for chat request.
    
    Uses MD5 hash of query + intent + workflow to create deterministic key.
    """
    cache_data = f"{query}|{intent}|{json.dumps(workflow, sort_keys=True) if workflow else ''}"
    return hashlib.md5(cache_data.encode()).hexdigest()


def get_cached_response(cache_key: str) -> Optional[Dict]:
    """
    Retrieve cached response if it exists and hasn't expired.
    """
    if cache_key not in response_cache:
        return None
    
    response_data, cached_time = response_cache[cache_key]
    age_seconds = (datetime.now() - cached_time).total_seconds()
    
    if age_seconds > CACHE_TTL_SECONDS:
        # Expired
        del response_cache[cache_key]
        return None
    
    logger.info("[CACHE] Cache HIT for key %s (age: %.1fs)", cache_key, age_seconds)
    return response_data


def set_cached_response(cache_key: str, response_data: Dict) -> None:
    """
    Store response in cache.
    """
    response_cache[cache_key] = (response_data, datetime.now())
    logger.info("[CACHE] Cached response for key %s (total cache size: %d)", cache_key, len(response_cache))


# =========================================================
# SECURITY
# =========================================================

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    if credentials.credentials != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )


# =========================================================
# LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for Chat API.
    
    Startup:
    - Initialize server health status
    - Start background cleanup task for memory management
    
    Shutdown:
    - Cancel cleanup task
    - Clean up resources
    """
    global cleanup_task
    
    # ===================== STARTUP =====================
    try:
        logger.info("=" * 70)
        logger.info("[STARTUP] Chat API initializing...")
        
        # Set server health to UP
        SERVER_UP.set(1)
        logger.info("[METRICS] Server health status set to UP")
        
        # Start memory cleanup task (runs every 5 minutes)
        cleanup_task = asyncio.create_task(
            cleanup_old_client_requests(interval_seconds=300, max_age_hours=1)
        )
        logger.info("[MEMORY] Background cleanup task started (runs every 5 min)")
        logger.info("=" * 70)
    except Exception as e:
        logger.error("CRITICAL: Failed to initialize Chat API")
        logger.exception("Startup error: %s", str(e))
        SERVER_UP.set(0)
        raise
    
    yield  # App runs here
    
    # ===================== SHUTDOWN =====================
    logger.info("=" * 70)
    logger.info("[SHUTDOWN] Chat API shutting down...")
    
    # Cancel cleanup task gracefully
    if cleanup_task and not cleanup_task.done():
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logger.info("[MEMORY] Cleanup task cancelled")
    
    SERVER_UP.set(0)
    logger.info("=" * 70)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title=config.API_TITLE + " Chat API",
    version=config.API_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.CORS_ALLOW_ORIGINS) if config.CORS_ALLOW_ORIGINS != ("*",) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MIDDLEWARE
# =========================================================

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    """Middleware to capture metrics for all HTTP requests."""
    method = request.method
    endpoint = request.url.path
    
    # Increment active requests
    ACTIVE_REQUESTS.inc()
    
    # Measure request duration
    start_time = time.time()
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        logger.error("Request failed: %s %s - %s", method, endpoint, str(e))
        raise
    finally:
        # Record metrics
        duration = time.time() - start_time
        REQUEST_DURATION.labels(endpoint=endpoint, method=method).observe(duration)
        REQUEST_COUNTER.labels(method=method, endpoint=endpoint, http_status=status_code).inc()
        HTTP_STATUS_CODE_TOTAL.labels(http_status=status_code).inc()
        ACTIVE_REQUESTS.dec()
        
        logger.debug("[METRICS] %s %s - Status: %d - Duration: %.3fs", 
                    method, endpoint, status_code, duration)
    
    return response


@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    """Add request timeout middleware (200 seconds for LLM processing with retries)."""
    try:
        async with asyncio.timeout(200):  # Increased from 120s to 200s for LLM calls with retries
            response = await call_next(request)
            return response
    except asyncio.TimeoutError:
        logger.error("[TIMEOUT] Request timeout after 200s: %s %s", 
                    request.method, request.url.path)
        return JSONResponse(
            status_code=504,
            content={"detail": "Request processing timeout (>200s). Please try again or contact support."}
        )


# =========================================================
# HELPERS
# =========================================================

def _extract_json_from_query(raw_query: str) -> Optional[str]:
    start = raw_query.find("{")
    end = raw_query.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw_query[start:end + 1]
    return None


def _parse_workflow_llm_output(raw: Any) -> Dict[str, Any]:
    """
    Normalise LLM output to:
    {
        "workflow": {...},
        "explanation": "..."
    }
    """
    if isinstance(raw, dict):
        return raw

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            fragment = _extract_json_from_query(raw)
            if fragment:
                try:
                    return json.loads(fragment)
                except json.JSONDecodeError:
                    pass

    return {
        "workflow": raw,
        "explanation": ""
    }


# =========================================================
# ENDPOINT
# =========================================================

@app.get("/health")
async def health():
    """Health check endpoint. No API key required."""
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint. No API key required."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(verify_api_key)]
)
async def chat_endpoint(payload: ChatRequest, request: Request):
    """
    Main chat endpoint for workflow generation, correction, and Q&A.
    
    Tracks client activity for memory management (stale entries cleaned up automatically).
    Caches responses for 1 hour to optimize repeated identical requests.
    """
    # Track client request time for memory management
    client_id = request.client.host if request.client else "unknown"
    client_request_times[client_id] = datetime.now()

    # ====== CHECK CACHE ======
    cache_key = generate_cache_key(
        query=payload.query,
        intent=payload.type_intent,
        workflow=payload.workflow
    )
    
    cached_result = get_cached_response(cache_key)
    if cached_result is not None:
        logger.info("[CHAT] Returning cached response for client: %s", client_id)
        return ChatResponse(**cached_result)

    # INIT with comprehensive error handling
    try:
        provider = payload.provider or config.LLM_PROVIDER or "openai"
        logger.info("[CHAT] Initializing with provider: %s", provider)
        llm = get_llm_client(provider=provider)
        logger.debug("[CHAT] LLM client retrieved from pool")
    except ValueError as e:
        logger.error("[CHAT] Invalid LLM provider: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Invalid LLM provider: {str(e)}")
    except Exception as e:
        logger.exception("[CHAT] Failed to initialize LLM client")
        raise HTTPException(status_code=500, detail="Failed to initialize language model")

    try:
        qdrant_client = get_qdrant_client()
        logger.debug("[CHAT] Qdrant client retrieved from pool")
    except ConnectionError as e:
        logger.error("[CHAT] Cannot connect to Qdrant: %s", str(e))
        raise HTTPException(status_code=503, detail="Vector database temporarily unavailable")
    except Exception as e:
        logger.exception("[CHAT] Qdrant initialization failed")
        raise HTTPException(status_code=503, detail="Vector database error")

    try:
        embedder = Embedder.get_instance()
        sparse_embedder = SparseEmbedder.get_instance()
        logger.debug("[CHAT] Embedding models loaded")
    except Exception as e:
        logger.exception("[CHAT] Failed to load embedding models")
        raise HTTPException(status_code=503, detail="Embedding models unavailable")

    try:
        store = VectorStore(
            collection_name=config.QDRANT_COLLECTION_NAME,
            client=qdrant_client
        )
        logger.debug("[CHAT] Vector store initialized with pooled client")
    except Exception as e:
        logger.exception("[CHAT] Vector store initialization failed")
        raise HTTPException(status_code=503, detail="Vector store unavailable")

    try:
        rewriter = QueryRewriter(
            llm_client=llm,
            qdrant_client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            cache_ttl_seconds=600
        )
        logger.debug("[CHAT] Query rewriter initialized")
    except Exception as e:
        logger.exception("[CHAT] Query rewriter initialization failed")
        raise HTTPException(status_code=500, detail="Query rewriter initialization failed")

    try:
        planner = WorkflowPlanner(
            llm_client=llm,
            qdrant_client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME
        )
        logger.debug("[CHAT] Workflow planner initialized")
    except Exception as e:
        logger.exception("[CHAT] Workflow planner initialization failed")
        raise HTTPException(status_code=500, detail="Workflow planner initialization failed")

    processor = WorkflowProcessor(llm_client=llm)
    logger.debug("[CHAT] Workflow processor initialized")

    # STEP 1 — REWRITE (pass user intent hint for fallback priority)
    rewrite = rewriter.rewrite(payload.query, user_intent=payload.type_intent)

    # User choice is EXPLICIT and must be respected
    valid_intents = {"workflow_generation", "workflow_correction", "qa"}
    intent_source = "user_choice"
    
    if payload.type_intent and payload.type_intent in valid_intents:
        # User made a conscious choice → use it directly
        intent = payload.type_intent
        logger.info("[CHAT] Using user-selected intent: %s", intent)
    else:
        # No user choice → rewriter detects automatically (respects hint even in fallback)
        intent = rewrite["intent"]
        intent_source = "rewriter_detection"
        logger.info("[CHAT] Intent auto-detected by rewriter: %s", intent)
    
    task_names = rewrite.get("task_names", [])
    search_query = rewrite.get("search_query_en", payload.query)

    # STEP 2 — PLANNER
    plan = None
    plan_result = None

    if intent in {"workflow_generation", "workflow_correction"}:
        plan_result = planner.plan(
            user_request=search_query,
            suggested_tasks=task_names
        )

        if plan_result.get("success"):
            plan = plan_result["plan"]

    # STEP 3 — CONTEXT
    context = ""
    task_examples = ""

    if intent in {"workflow_generation", "workflow_correction"}:

        required_tasks = plan.get("required_tasks", task_names) if plan else task_names

        resolved_tasks = rewriter.registry.resolve_list_to_document_titles(required_tasks)

        result_context = build_workflow_context_for_tasks(
            task_names=resolved_tasks,
            store=store,
            internal_names=required_tasks
        )

        context = result_context.get("context", "")
        task_examples = result_context.get("task_examples", "")

        if not context:
            dense = embedder.embed_text(search_query)
            sparse = sparse_embedder.embed_text(search_query)

            points = store.hybrid_search(
                dense_vector=dense,
                sparse_vector=sparse,
                limit=5,
                filter_conditions={"type_doc": "task_doc"}
            )

            context = "\n\n".join([p.payload.get("content", "") for p in points])

    elif intent == "qa":

        dense = embedder.embed_text(search_query)
        sparse = sparse_embedder.embed_text(search_query)

        points = store.hybrid_search(
            dense_vector=dense,
            sparse_vector=sparse,
            limit=5,
            filter_conditions={"type_doc": "task_doc"}
        )

        context = "\n\n".join([
            f"# {p.payload.get('section_title')}\n{p.payload.get('content')}"
            for p in points
        ])

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")

    # STEP 4 — LLM
    validation_meta = {}
    result = None

    # =========================
    # GENERATION
    # =========================
    if intent == "workflow_generation":

        system_prompt, user_prompt = build_workflow_generation_prompt(
            context=context,
            instruction=payload.query,
            plan=plan,
            task_examples=task_examples
        )

        raw = llm.complete(system=system_prompt, user=user_prompt, max_tokens=2000, temperature=0.1)

        proc = processor.process(raw)

        # Extract workflow and explanation directly from processor output
        workflow_dict = proc.get("workflow") or {}
        explanation = proc.get("explanation") or ""

        result = WorkflowResult(
            workflow=workflow_dict,
            explanation=explanation,
            validation_passed=proc.get("validation_passed", False),
            retry_count=proc.get("retry_count", 0),
            errors_found=proc.get("errors_found", [])
        )

        validation_meta = {
            "validation_passed": proc["validation_passed"],
            "retry_count": proc["retry_count"],
            "errors_found": proc["errors_found"],
            "processor_status": proc["status"]
        }

    # =========================
    # CORRECTION
    # =========================
    elif intent == "workflow_correction":

        workflow_text = (
            json.dumps(payload.workflow, indent=2)
            if payload.workflow
            else (_extract_json_from_query(payload.query) or "{}")
        )

        system_prompt, user_prompt = build_workflow_correction_prompt(
            context=context,
            workflow=workflow_text,
            correction_instruction=payload.query,
            task_examples=task_examples
        )

        raw = llm.complete(system=system_prompt, user=user_prompt, max_tokens=2000, temperature=0.1)

        proc = processor.process(raw)

        # Extract workflow and explanation directly from processor output
        workflow_dict = proc.get("workflow") or {}
        explanation = proc.get("explanation") or ""

        result = WorkflowResult(
            workflow=workflow_dict,
            explanation=explanation,
            validation_passed=proc.get("validation_passed", False),
            retry_count=proc.get("retry_count", 0),
            errors_found=proc.get("errors_found", [])
        )

        validation_meta = {
            "validation_passed": proc["validation_passed"],
            "retry_count": proc["retry_count"],
            "errors_found": proc["errors_found"],
            "processor_status": proc["status"]
        }

    # =========================
    # QA
    # =========================
    else:

        user_prompt = build_qa_prompt(context=context, question=payload.query)

        result = llm.complete(
            system="You are a helpful assistant for Android workflow automation.",
            user=user_prompt,
            max_tokens=1000,
            temperature=0.3
        )

        validation_meta = {
            "validation_passed": None,
            "retry_count": 0,
            "errors_found": [],
            "processor_status": "not_applicable"
        }

    # FINAL RESPONSE
    response = ChatResponse(
        intent=intent,
        task_names=task_names,
        result=result,
        metadata={
            "plan": plan if plan_result and plan_result.get("success") else None,
            "plan_confidence": plan_result.get("confidence") if plan_result else None,
            "plan_ambiguities": plan_result.get("ambiguities", []) if plan_result else [],
            "context_length": len(context),
            "intent_source": intent_source,
            **validation_meta
        }
    )
    
    # Cache the response for future identical requests
    # IMPORTANT: Only cache SUCCESSFUL responses for workflow tasks
    # Failed responses should be retried on next request
    response_dict = response.model_dump()
    
    if intent in {"workflow_generation", "workflow_correction"}:
        # Only cache if validation passed
        if response.metadata.get("validation_passed", False):
            set_cached_response(cache_key, response_dict)
            logger.info("[CACHE] Cached SUCCESSFUL response for key %s", cache_key)
        else:
            logger.warning("[CACHE] NOT caching FAILED response for key %s (validation_passed=false)", cache_key)
    elif intent == "qa":
        # QA responses don't have validation, always cache
        set_cached_response(cache_key, response_dict)
    
    return response