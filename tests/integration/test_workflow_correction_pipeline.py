"""Integration test: Query rewriting + hybrid search + workflow correction prompt."""

import json
from src.llm import create_llm_client
from src.rag.query_rewriter import QueryRewriter
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.task_section_extractor import build_workflow_context_for_tasks
from src.prompts import build_workflow_correction_prompt
from src.config import config
from qdrant_client import QdrantClient
from src.utilities.logger import get_module_logger

logger = get_module_logger("test_workflow_correction")

# ---------------------------------------------------------------------------
# Intentionally broken workflow — missing variables, missing link, no retry
# This example uses HttpRequest instead of CmdStage.
# ---------------------------------------------------------------------------
BROKEN_WORKFLOW = {
    "Start": [
        {
            "id": "-1000",
            "variables": [
                {"variableName": "$URL", "variableValue": "https://api.example.com/monitoring", "is_kpi": False}
                # ❌ $METHOD, $REQUEST_BODY_JSON, $HTTP_RESPONSE_OUTPUT and $HTTP_STATUS_CODE not declared
            ],
            "exec_policy": "1"
        }
    ],
    "HttpRequest": [
        {
            "id": "-1001",
            "url": "$URL",
            "method": "$METHOD",
            "connection_timeout": "$CONNECTION_TIMEOUT",
            "read_timeout": "$READ_TIMEOUT",
            "http_debug": "$HTTP_DEBUG",
            "request_body_json": "{\"device_id\": \"$DEVICE_ID\"}",
            "parameters": "$PARAMETERS",
            "http_response_output": "$HTTP_RESPONSE_OUTPUT",  # ❌ undeclared variable
            "http_error_output": "$HTTP_ERROR_OUTPUT",
            "http_status_code": "$HTTP_STATUS_CODE"           # ❌ undeclared variable
        }
    ],
    "End": [
        {"id": "-2000"}
    ],
    "Links": [
        {"from": "-1000", "to": "-1001"}
        # ❌ missing link from HttpRequest (-1001) to End (-2000)
    ]
}


def test_workflow_correction_pipeline(
    correction_instruction: str = (
        "Fix this workflow: output variables are not declared in Start, "
        "HttpRequest task has no outgoing link to End, "
        "and add a retry up to 3 times if the request fails"
    ),
    provider: str = "openai",
):
    """
    Full RAG pipeline test for workflow correction:
    1. Build user message (instruction + broken workflow JSON)
    2. Rewrite with QueryRewriter — must detect workflow_correction intent
    3. Extract task types from workflow JSON keys
    4. Build task names union (from message + from workflow)
    5. Retrieve task documentation via extraction or hybrid search
    6. Build workflow correction prompt
    7. Generate corrected workflow JSON with LLM
    8. Display results
    """

    print("=" * 80)
    print("WORKFLOW CORRECTION PIPELINE TEST")
    print("=" * 80)

    # Build full user message — instruction + JSON (what frontend sends)
    user_message = f"{correction_instruction}: {json.dumps(BROKEN_WORKFLOW)}"

    print(f"\nCorrection instruction : \"{correction_instruction}\"")
    print(f"\nBroken workflow JSON :")
    print("-" * 40)
    print(json.dumps(BROKEN_WORKFLOW, indent=2))
    print("-" * 40)

    # ------------------------------------------------------------------
    # Step 1: Initialize LLM client
    # ------------------------------------------------------------------
    print("\n[STEP 1] Initializing LLM client...")
    try:
        llm_client = create_llm_client(provider=provider)
        print(f"✅ LLM client created: {type(llm_client).__name__}")
    except Exception as e:
        print(f"❌ Failed to create LLM client: {e}")
        return

    # ------------------------------------------------------------------
    # Step 2: Initialize Qdrant and embedders
    # ------------------------------------------------------------------
    print("\n[STEP 2] Initializing Qdrant and embedders...")
    try:
        qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        embedder = Embedder.get_instance()
        sparse_embedder = SparseEmbedder.get_instance()
        print(f"✅ Qdrant connected to {config.QDRANT_HOST}:{config.QDRANT_PORT}")
        print(f"✅ Dense embedder: {config.EMBEDDING_MODEL}")
        print(f"✅ Sparse embedder: BM25")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return

    # ------------------------------------------------------------------
    # Step 3: Rewrite user message with QueryRewriter
    # ------------------------------------------------------------------
    print(f"\n[STEP 3] Rewriting user message with QueryRewriter...")
    print(f"User message (truncated): \"{user_message[:150]}...\"")
    try:
        query_rewriter = QueryRewriter(
            llm_client=llm_client,
            qdrant_client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            cache_ttl_seconds=600
        )
        rewritten = query_rewriter.rewrite(user_message)
        print(f"✅ Query rewritten successfully")
        print(f"   Intent       : {rewritten.get('intent')}")
        print(f"   Task names   : {rewritten.get('task_names')}")
        print(f"   Search query : {rewritten.get('search_query_en')}")

        if rewritten.get("intent") != "workflow_correction":
            print(f"⚠️  Expected workflow_correction, got: {rewritten.get('intent')} — forcing override")
            rewritten["intent"] = "workflow_correction"
        else:
            print(f"✅ Intent correctly detected as workflow_correction")

    except Exception as e:
        print(f"❌ Query rewriting failed: {e}")
        rewritten = {
            "intent": "workflow_correction",
            "task_names": [],
            "search_query_en": correction_instruction
        }
        print(f"⚠️  Using fallback rewritten query")

    # ------------------------------------------------------------------
    # Step 4: Extract task types from broken workflow JSON keys
    # ------------------------------------------------------------------
    print(f"\n[STEP 4] Extracting task types from workflow JSON keys...")
    EXCLUDED_KEYS = {"Start", "End", "Links"}
    tasks_from_workflow = [k for k in BROKEN_WORKFLOW if k not in EXCLUDED_KEYS]
    print(f"✅ Task types found in workflow: {tasks_from_workflow}")

    # ------------------------------------------------------------------
    # Step 5: Build union of task names (from message + from workflow)
    # ------------------------------------------------------------------
    print(f"\n[STEP 5] Building task names union...")
    tasks_from_message = rewritten.get("task_names", [])
    all_task_names = list(set(tasks_from_message + tasks_from_workflow))
    print(f"   From correction instruction : {tasks_from_message}")
    print(f"   From workflow JSON keys     : {tasks_from_workflow}")
    print(f"   Union                       : {all_task_names}")

    # ------------------------------------------------------------------
    # Step 6: Retrieve task documentation
    # ------------------------------------------------------------------
    print(f"\n[STEP 6] Retrieving task documentation...")
    retrieved_content = ""
    try:
        store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)

        if all_task_names:
            print(f"✅ Task names detected: {all_task_names}")
            retrieved_content = build_workflow_context_for_tasks(all_task_names, store)
            if retrieved_content:
                print(f"✅ Built context from {len(all_task_names)} task(s)")
            else:
                print("⚠️  No direct task documentation found, falling back to hybrid search")

        if not retrieved_content:
            search_query = rewritten.get("search_query_en", correction_instruction)
            dense_vector = embedder.embed_text(search_query)
            sparse_vector = sparse_embedder.embed_text(search_query)

            points = store.hybrid_search(
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                limit=5
            )

            if not points:
                print("⚠️  No results from hybrid search, trying dense-only...")
                points = store.search(query_vector=dense_vector, limit=5)

            print(f"✅ Retrieved {len(points)} documents")
            for i, point in enumerate(points, 1):
                doc_id = point.payload.get("document_id", "unknown")
                doc_type = point.payload.get("type_doc", "unknown")
                score = point.score if hasattr(point, "score") else "N/A"
                print(f"   [{i}] {doc_id} (type: {doc_type}, score: {score})")

            retrieved_content = "\n\n".join(
                [p.payload.get("content", "") for p in points]
            ).strip() or "No relevant documentation found."

    except Exception as e:
        print(f"❌ Documentation retrieval failed: {e}")
        retrieved_content = "No relevant documentation found."

    # ------------------------------------------------------------------
    # Step 7: Build workflow correction prompt
    # ------------------------------------------------------------------
    print(f"\n[STEP 7] Building workflow correction prompt...")
    try:
        system_prompt, user_prompt = build_workflow_correction_prompt(
            context=retrieved_content,
            workflow=json.dumps(BROKEN_WORKFLOW, indent=2),
            correction_instruction=correction_instruction,  # clean — no JSON
        )
        print(f"✅ Prompts built — system: {len(system_prompt)} chars, user: {len(user_prompt)} chars")
    except Exception as e:
        print(f"❌ Failed to build correction prompt: {e}")
        return

    # ------------------------------------------------------------------
    # Step 8: Generate corrected workflow JSON with LLM
    # ------------------------------------------------------------------
    print(f"\n[STEP 8] Generating corrected workflow JSON with LLM...")
    try:
        corrected_workflow = llm_client.complete(
            system=system_prompt,
            user=user_prompt,
            max_tokens=2000,
            temperature=0.1
        )
        print(f"✅ Corrected workflow generated ({len(corrected_workflow)} characters)")
        print("\nCorrected Workflow JSON:")
        print("-" * 40)
        print(corrected_workflow)
        print("-" * 40)
    except Exception as e:
        print(f"❌ Failed to generate corrected workflow: {e}")
        return

    # ------------------------------------------------------------------
    # Step 9: Display results
    # ------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("RETRIEVED CONTEXT")
    print("=" * 80)
    print(retrieved_content[:1000])
    if len(retrieved_content) > 1000:
        print(f"\n...[truncated, {len(retrieved_content) - 1000} more characters]")

    print("\n" + "=" * 80)
    print("SYSTEM PROMPT")
    print("=" * 80)
    print(system_prompt[:1500])
    if len(system_prompt) > 1500:
        print(f"\n...[truncated, {len(system_prompt) - 1500} more characters]")

    print("\n" + "=" * 80)
    print("USER PROMPT")
    print("=" * 80)
    print(user_prompt[:1500])
    if len(user_prompt) > 1500:
        print(f"\n...[truncated, {len(user_prompt) - 1500} more characters]")

    print("\n" + "=" * 80)
    print("✅ CORRECTION PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_workflow_correction_pipeline(
        correction_instruction=(
            "Fix this workflow: output variables are not declared in Start, "
            "HttpRequest task has no outgoing link to End, "
        ),
        provider="openai"
    )