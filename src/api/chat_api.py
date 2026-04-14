import json
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from qdrant_client import QdrantClient

from src.config import config
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.task_section_extractor import build_workflow_context_for_tasks
from src.ingestion_pipeline.vector_store import VectorStore
from src.llm import create_llm_client
from src.prompts import build_workflow_generation_prompt, build_workflow_correction_prompt, build_qa_prompt
from src.rag.query_rewriter import QueryRewriter
from src.utilities.logger import get_module_logger

logger = get_module_logger("chat_api")
security = HTTPBearer()


class ChatRequest(BaseModel):
    query: str
    workflow: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None


class ChatResponse(BaseModel):
    intent: str
    task_names: List[str]
    result: str
    metadata: Dict[str, Any]


def _get_client_ip(request) -> str:
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != config.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"}
        )


app = FastAPI(title=config.API_TITLE + " Chat API", version=config.API_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.CORS_ALLOW_ORIGINS) if config.CORS_ALLOW_ORIGINS != ("*",) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _extract_json_from_query(raw_query: str) -> Optional[str]:
    # If the user query contains an embedded JSON workflow, extract the first JSON object.
    start = raw_query.find("{")
    end = raw_query.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw_query[start:end + 1]
    return None


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
async def chat_endpoint(payload: ChatRequest):
    provider = payload.provider or config.LLM_PROVIDER or "openai"
    llm_client = create_llm_client(provider=provider)
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    embedder = Embedder.get_instance()
    sparse_embedder = SparseEmbedder.get_instance()
    store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)

    query_rewriter = QueryRewriter(
        llm_client=llm_client,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME,
        cache_ttl_seconds=600
    )

    rewritten = query_rewriter.rewrite(payload.query)
    intent = rewritten["intent"]
    task_names = rewritten.get("task_names", [])
    search_query = rewritten.get("search_query_en", payload.query)

    context = ""
    workflow_text = ""

    if intent == "qa":
        dense_vector = embedder.embed_text(search_query)
        sparse_vector = sparse_embedder.embed_text(search_query)
        points = store.hybrid_search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=5,
            filter_conditions={"type_doc": "task_doc"}
        )

        if not points:
            points = store.search(query_vector=dense_vector, limit=5, score_threshold=None)

        context_parts = []
        for point in points:
            section_title = point.payload.get("section_title", "unknown")
            content = point.payload.get("content", "")
            context_parts.append(f"# {section_title}\n{content}")
        context = "\n\n---\n\n".join(context_parts)

        user_prompt = build_qa_prompt(
            context=context,
            question=payload.query
        )
        result = llm_client.complete(
            system="You are a helpful assistant for Android workflow automation.",
            user=user_prompt,
            max_tokens=1000,
            temperature=0.3
        )

        return ChatResponse(
            intent=intent,
            task_names=task_names,
            result=result,
            metadata={
                "retrieved_documents": [
                    {
                        "document_id": p.payload.get("document_id"),
                        "section_title": p.payload.get("section_title"),
                        "score": getattr(p, "score", None)
                    }
                    for p in points
                ]
            }
        )

    if intent in {"workflow_generation", "workflow_correction"}:
        if task_names:
            context = build_workflow_context_for_tasks(task_names, store)

        if not context:
            dense_vector = embedder.embed_text(search_query)
            sparse_vector = sparse_embedder.embed_text(search_query)
            points = store.hybrid_search(
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                limit=5,
                filter_conditions={"type_doc": "task_doc"}
            )
            if not points:
                points = store.search(query_vector=dense_vector, limit=5, score_threshold=None)
            context = "\n\n".join([p.payload.get("content", "") for p in points])

        if intent == "workflow_generation":
            system_prompt, user_prompt = build_workflow_generation_prompt(
                context=context,
                instruction=payload.query
            )
            result = llm_client.complete(
                system=system_prompt,
                user=user_prompt,
                max_tokens=2000,
                temperature=0.1
            )

            return ChatResponse(
                intent=intent,
                task_names=task_names,
                result=result,
                metadata={"context_length": len(context)}
            )

        if intent == "workflow_correction":
            if payload.workflow is not None:
                workflow_text = json.dumps(payload.workflow, indent=2)
            else:
                candidate_json = _extract_json_from_query(payload.query)
                workflow_text = candidate_json or "{}"

            system_prompt, user_prompt = build_workflow_correction_prompt(
                context=context,
                workflow=workflow_text,
                correction_instruction=payload.query
            )
            result = llm_client.complete(
                system=system_prompt,
                user=user_prompt,
                max_tokens=2000,
                temperature=0.1
            )

            return ChatResponse(
                intent=intent,
                task_names=task_names,
                result=result,
                metadata={"workflow_provided": bool(payload.workflow), "context_length": len(context)}
            )

    raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")
