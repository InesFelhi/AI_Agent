import json
import asyncio
import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient

from src.config import config

from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.vector_store import VectorStore

from src.ingestion_pipeline.task_section_extractor import (
    build_workflow_context_for_tasks
)

from src.llm import create_llm_client

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
# APP
# =========================================================

app = FastAPI(
    title=config.API_TITLE + " Chat API",
    version=config.API_VERSION
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
async def timeout_middleware(request: Request, call_next):
    """Add request timeout middleware (30 seconds)."""
    try:
        async with asyncio.timeout(30):
            response = await call_next(request)
            return response
    except asyncio.TimeoutError:
        logger.error("[TIMEOUT] Request timeout after 30s: %s %s", 
                    request.method, request.url.path)
        return JSONResponse(
            status_code=504,
            content={"detail": "Request processing timeout"}
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

@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(verify_api_key)]
)
async def chat_endpoint(payload: ChatRequest, request: Request):

    # INIT with comprehensive error handling
    try:
        provider = payload.provider or config.LLM_PROVIDER or "openai"
        logger.info("[CHAT] Initializing with provider: %s", provider)
        llm = create_llm_client(provider=provider)
        logger.debug("[CHAT] LLM client created")
    except ValueError as e:
        logger.error("[CHAT] Invalid LLM provider: %s", str(e))
        raise HTTPException(status_code=400, detail=f"Invalid LLM provider: {str(e)}")
    except Exception as e:
        logger.exception("[CHAT] Failed to create LLM client")
        raise HTTPException(status_code=500, detail="Failed to initialize language model")

    try:
        qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        logger.debug("[CHAT] Qdrant client created")
        # Quick connection test
        qdrant_client.get_collections()
        logger.debug("[CHAT] Qdrant connection verified")
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
            collection_name=config.QDRANT_COLLECTION_NAME
        )
        logger.debug("[CHAT] Vector store initialized")
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
    return ChatResponse(
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