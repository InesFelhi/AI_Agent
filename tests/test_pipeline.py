"""
Minimal Chat API Pipeline Test
Displays only:
1. Rewriter response
2. Planner response
3. Final LLM response
"""

import json

from qdrant_client import QdrantClient

from src.config import config

from src.llm import create_llm_client

from src.rag.query_rewriter import QueryRewriter

from src.workflow.workflow_planner import WorkflowPlanner
from src.workflow.workflow_processor import WorkflowProcessor

from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.vector_store import VectorStore

from src.ingestion_pipeline.task_section_extractor import (
    build_workflow_context_for_tasks
)

from src.prompts import (
    build_workflow_generation_prompt,
    build_workflow_correction_prompt,
    build_qa_prompt
)


QUERY = (
    "Give me a workflow that runs a PING to any server, "
    "then returns the minimum and maximum values of the results"
)


def test_chat_api_pipeline():

    # =====================================================
    # INIT
    # =====================================================

    llm = create_llm_client()

    qdrant_client = QdrantClient(
        host=config.QDRANT_HOST,
        port=config.QDRANT_PORT
    )

    embedder = Embedder.get_instance()

    sparse_embedder = SparseEmbedder.get_instance()

    store = VectorStore(
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    rewriter = QueryRewriter(
        llm_client=llm,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    planner = WorkflowPlanner(
        llm_client=llm,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    processor = WorkflowProcessor(
        llm_client=llm
    )

    # =====================================================
    # STEP 1 — REWRITER
    # =====================================================

    rewrite = rewriter.rewrite(QUERY)

    intent = rewrite["intent"]

    task_names = rewrite.get("task_names", [])

    search_query = rewrite.get(
        "search_query_en",
        QUERY
    )

    print("\n" + "=" * 100)
    print("REWRITER RESPONSE")
    print("=" * 100)

    print(
        json.dumps(
            rewrite,
            indent=2,
            ensure_ascii=False
        )
    )

    # =====================================================
    # STEP 2 — PLANNER
    # =====================================================

    plan_result = planner.plan(
        user_request=search_query,
        suggested_tasks=task_names
    )

    print("\n" + "=" * 100)
    print("PLANNER RESPONSE")
    print("=" * 100)

    print(
        json.dumps(
            plan_result,
            indent=2,
            ensure_ascii=False
        )
    )

    plan = plan_result["plan"]

    # =====================================================
    # STEP 3 — CONTEXT
    # EXACT SAME AS chat_api.py
    # =====================================================

    required_tasks = (
        plan.get("required_tasks", task_names)
        if plan else task_names
    )

    result_context = build_workflow_context_for_tasks(
        task_names=required_tasks,
        store=store,
        internal_names=required_tasks
    )

    context = result_context.get("context", "")

    task_examples = result_context.get(
        "task_examples",
        ""
    )

    # Hybrid fallback
    if not context:

        dense = embedder.embed_text(search_query)

        sparse = sparse_embedder.embed_text(
            search_query
        )

        points = store.hybrid_search(
            dense_vector=dense,
            sparse_vector=sparse,
            limit=5,
            filter_conditions={
                "type_doc": "task_doc"
            }
        )

        context = "\n\n".join([
            p.payload.get("content", "")
            for p in points
        ])

    # =====================================================
    # STEP 4 — PROMPTS
    # =====================================================

    if intent == "workflow_generation":

        system_prompt, user_prompt = (
            build_workflow_generation_prompt(
                context=context,
                instruction=QUERY,
                plan=plan,
                task_examples=task_examples
            )
        )

    elif intent == "workflow_correction":

        workflow_json = "{}"

        system_prompt, user_prompt = (
            build_workflow_correction_prompt(
                context=context,
                workflow=workflow_json,
                correction_instruction=QUERY,
                task_examples=task_examples
            )
        )

    else:

        user_prompt = build_qa_prompt(
            context=context,
            question=QUERY
        )

        system_prompt = (
            "You are a helpful assistant "
            "for Android workflow automation."
        )

    # =====================================================
    # STEP 5 — FINAL LLM
    # =====================================================

    raw = llm.complete(
        system=system_prompt,
        user=user_prompt,
        max_tokens=2000,
        temperature=0.1
    )

    # =====================================================
    # STEP 6 — PROCESSOR
    # =====================================================

    proc = processor.process(raw)

    if proc["success"]:

        result = proc["workflow"]

    else:

        result = proc["final_json"]

    print("\n" + "=" * 100)
    print("FINAL LLM RESPONSE")
    print("=" * 100)

    if isinstance(result, dict):

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

    else:

        print(result)

    print("\n" + "=" * 100)
    print("TEST COMPLETED")
    print("=" * 100 + "\n")


if __name__ == "__main__":

    test_chat_api_pipeline()