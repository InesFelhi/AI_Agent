"""
Simple test for workflow correction
using the SAME logic as chat_api.py
WITH internal name -> document title resolution
"""

import json
import os
import pytest

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
    build_workflow_correction_prompt
)

from src.rag.query_rewriter import QueryRewriter

from src.workflow.workflow_planner import WorkflowPlanner
from src.workflow.workflow_processor import WorkflowProcessor

from src.utilities.logger import get_module_logger


logger = get_module_logger(
    "test_workflow_correction_simple"
)


# =========================================================
# BROKEN WORKFLOW
# =========================================================

BROKEN_WORKFLOW = {

    "Start": [
        {
            "id": "-1000",

            "variables": [
                {
                    "variableName": "$URL",

                    "variableValue":
                        "https://api.example.com/health"
                }
            ],

            "exec_policy": "1"
        }
    ],

    "HttpRequest": [
        {
            "id": "-1001",

            "url": "$URL",

            "method": "$METHOD",

            "http_response_output":
                "$HTTP_RESPONSE",

            "http_status_code":
                "$HTTP_STATUS_CODE"
        }
    ],

    "End": [
        {
            "id": "-2000"
        }
    ],

    "Links": [
        {
            "from": "-1000",
            "to": "-1001"
        }
    ]
}


# =========================================================
# HELPERS
# =========================================================

def extract_json_from_query(
    raw_query: str
):

    start = raw_query.find("{")

    end = raw_query.rfind("}")

    if start != -1 and end != -1 and end > start:

        return raw_query[start:end + 1]

    return None


def parse_llm_json_result(
    raw_text: str
):

    if not raw_text:
        return raw_text

    try:

        return json.loads(raw_text)

    except json.JSONDecodeError:

        fragment = extract_json_from_query(
            raw_text
        )

        if fragment:

            try:

                return json.loads(fragment)

            except json.JSONDecodeError:
                pass

    return raw_text


# =========================================================
# MAIN TEST
# =========================================================

@pytest.mark.skipif(
    os.getenv("OPENAI_API_KEY", "").startswith("sk-test-"),
    reason="Requires real OpenAI API key (not test key)"
)
def test_workflow_correction_simple(

    correction_instruction: str = (
        "Fix this workflow: "
        "Monitor HTTP API availability "
        "by sending GET requests "
        "and capturing response status"
    ),

    provider: str = "openai"
):

    print("\n" + "=" * 100)
    print("WORKFLOW CORRECTION TEST")
    print("=" * 100 + "\n")

    # =====================================================
    # STEP 1 — INIT
    # =====================================================

    print("[STEP 1] Initializing...")

    llm = create_llm_client(
        provider=provider
    )

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
        collection_name=config.QDRANT_COLLECTION_NAME,
        cache_ttl_seconds=600
    )

    planner = WorkflowPlanner(
        llm_client=llm,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    processor = WorkflowProcessor(
        llm_client=llm
    )

    print("✅ Initialization completed\n")

    # =====================================================
    # STEP 2 — REWRITER
    # =====================================================

    print("[STEP 2] Running Query Rewriter...\n")

    rewrite = rewriter.rewrite(
        correction_instruction
    )

    print("=" * 100)
    print("REWRITER RESPONSE")
    print("=" * 100)

    print(
        json.dumps(
            rewrite,
            indent=2,
            ensure_ascii=False
        )
    )

    print()

    intent = rewrite["intent"]

    task_names = rewrite.get(
        "task_names",
        []
    )

    search_query = rewrite.get(
        "search_query_en",
        correction_instruction
    )

    # Force correction mode if needed
    if intent != "workflow_correction":

        print(
            f"⚠️ Expected workflow_correction "
            f"but got: {intent}"
        )

        print(
            "⚠️ Forcing workflow_correction\n"
        )

        intent = "workflow_correction"

    # =====================================================
    # STEP 3 — PLANNER
    # =====================================================

    print("[STEP 3] Running Workflow Planner...\n")

    plan_result = planner.plan(
        user_request=search_query,
        suggested_tasks=task_names
    )

    print("=" * 100)
    print("PLANNER RESPONSE")
    print("=" * 100)

    print(
        json.dumps(
            plan_result,
            indent=2,
            ensure_ascii=False
        )
    )

    print()

    plan = (
        plan_result.get("plan")
        if plan_result.get("success")
        else None
    )

    # =====================================================
    # STEP 4 — CONTEXT RETRIEVAL
    # SAME AS chat_api.py
    # =====================================================

    print("[STEP 4] Retrieving Context...\n")

    context = ""

    task_examples = ""

    required_tasks = (
        plan.get("required_tasks", task_names)
        if plan else task_names
    )

    logger.info(
        "[TEST] required_tasks "
        "(internal names): %s",
        required_tasks
    )

    print(
        f"Required tasks "
        f"(internal names):\n"
        f"{required_tasks}\n"
    )

    # =====================================================
    # RESOLVE INTERNAL NAMES
    # TO DOCUMENT TITLES
    # =====================================================

    resolved_tasks = (
        rewriter.registry
        .resolve_list_to_document_titles(
            required_tasks
        )
    )

    logger.info(
        "[TEST] resolved_tasks "
        "(document titles): %s",
        resolved_tasks
    )

    print(
        f"Resolved tasks "
        f"(document titles):\n"
        f"{resolved_tasks}\n"
    )

    # =====================================================
    # CONTEXT RETRIEVAL
    # =====================================================

    result_context = (
        build_workflow_context_for_tasks(
            task_names=resolved_tasks,
            store=store,
            internal_names=required_tasks
        )
    )

    context = result_context.get(
        "context",
        ""
    )

    task_examples = result_context.get(
        "task_examples",
        ""
    )

    print(
        f"Context length: {len(context)}"
    )

    print(
        f"Task examples length: "
        f"{len(task_examples)}"
    )

    # =====================================================
    # HYBRID SEARCH FALLBACK
    # =====================================================

    if not context:

        print(
            "\n⚠️ No context found "
            "→ using hybrid fallback..."
        )

        dense = embedder.embed_text(
            search_query
        )

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

        print(
            f"Fallback context length: "
            f"{len(context)}"
        )

    print()

    # =====================================================
    # STEP 5 — BUILD PROMPTS
    # =====================================================

    print("[STEP 5] Building prompts...\n")

    workflow_text = json.dumps(
        BROKEN_WORKFLOW,
        indent=2
    )

    system_prompt, user_prompt = (
        build_workflow_correction_prompt(
            context=context,

            workflow=workflow_text,

            correction_instruction=
                correction_instruction,

            task_examples=task_examples
        )
    )

    print(
        f"System prompt length: "
        f"{len(system_prompt)}"
    )

    print(
        f"User prompt length: "
        f"{len(user_prompt)}\n"
    )

    # =====================================================
    # STEP 6 — FINAL LLM
    # =====================================================

    print("[STEP 6] Generating workflow...\n")

    raw = llm.complete(
        system=system_prompt,

        user=user_prompt,

        max_tokens=2000,

        temperature=0.1
    )

    print("=" * 100)
    print("FINAL LLM RESPONSE")
    print("=" * 100)

    print(raw)

    print()

    # =====================================================
    # STEP 7 — VALIDATION
    # =====================================================

    print("[STEP 7] Validating workflow...\n")

    proc = processor.process(raw)

    if proc and isinstance(proc, dict) and proc.get("success"):

        corrected_workflow = (
            proc["workflow"]
        )

        print("✅ Validation PASSED")

        print(
            f"validation_passed="
            f"{proc['validation_passed']}"
        )

        print(
            f"retry_count="
            f"{proc['retry_count']}"
        )

        print(
            f"errors_found="
            f"{len(proc['errors_found'])}"
        )

        print(
            f"status={proc['status']}\n"
        )

    elif proc and isinstance(proc, dict):

        print("⚠️ Validation issues")

        print(
            f"status={proc.get('status', 'unknown')}"
        )

        print(
            f"errors={proc.get('errors_found', [])}\n"
        )

        final_json = proc.get("final_json")
        if final_json:
            corrected_workflow = (
                parse_llm_json_result(
                    final_json
                )
            )
        else:
            corrected_workflow = None
    
    else:
        
        print("⚠️ Processor returned invalid format")
        print(f"Processor output type: {type(proc)}")
        corrected_workflow = None

    # =====================================================
    # STEP 8 — FINAL RESULT
    # =====================================================

    print("=" * 100)
    print("CORRECTED WORKFLOW")
    print("=" * 100)

    if corrected_workflow:
        if isinstance(corrected_workflow, str):
            print(corrected_workflow)
        else:
            print(
                json.dumps(
                    corrected_workflow,
                    indent=2,
                    ensure_ascii=False
                )
            )
    else:
        print("(No corrected workflow generated)")

    print()

    # =====================================================
    # STEP 9 — DIFFS
    # =====================================================

    if corrected_workflow and isinstance(corrected_workflow, dict):

        print("=" * 100)
        print("CORRECTIONS DETECTED")
        print("=" * 100)

        broken_vars = (
            BROKEN_WORKFLOW
            .get("Start", [{}])[0]
            .get("variables", [])
        )

        corrected_vars = (
            corrected_workflow
            .get("Start", [{}])[0]
            .get("variables", [])
        )

        broken_var_names = {
            v["variableName"]
            for v in broken_vars
        }

        corrected_var_names = {
            v["variableName"]
            for v in corrected_vars
        }

        added_vars = (
            corrected_var_names
            - broken_var_names
        )

        if added_vars:

            print(
                f"✅ Variables added: "
                f"{added_vars}"
            )

        broken_links = len(
            BROKEN_WORKFLOW.get("Links", [])
        )

        corrected_links = len(
            corrected_workflow.get("Links", [])
        )

        if corrected_links > broken_links:

            print(
                f"✅ Links added: "
                f"{corrected_links - broken_links}"
            )

    print("\n" + "=" * 100)
    print("✅ TEST COMPLETED")
    print("=" * 100 + "\n")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":

    test_workflow_correction_simple(
        correction_instruction=(
            "Fix this workflow: "
            "Monitor HTTP API availability "
            "by sending GET requests "
            "and capturing response status"
        ),

        provider="openai"
    )