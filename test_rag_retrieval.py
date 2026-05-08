"""
FULL AGENTIC RAG PIPELINE DEBUG (KEEP ORIGINAL QUERIES)

Pipeline:
1. QueryRewriter
2. WorkflowPlanner
3. Context (Extraction / Retrieval)
"""

from qdrant_client import QdrantClient
from src.config import config

from src.llm import create_llm_client
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.vector_store import VectorStore

from src.rag.query_rewriter import QueryRewriter
from src.workflow.workflow_planner import WorkflowPlanner
from src.ingestion_pipeline.task_section_extractor import build_workflow_context_for_tasks

from src.utilities.logger import get_module_logger

logger = get_module_logger("test_full_agentic_pipeline")


# ✅ TES QUERIES ORIGINALES (inchangées)
TEST_QUERIES = [
    {
        "name": "PING Workflow (Extract min/max)",
        "query": "Give me a workflow that runs a PING to any server, then returns the minimum and maximum values of the results."
    },
    {
        "name": "iperf3 + PCAP",
        "query": "Can you run an iperf3 command to a server at 0.0.0.0 using a UDP upload test? If possible, also start a PCAP capture before running iperf3, stop it after the test, and then upload the PCAP file (named test.pcap) to www.andromate_upload.net."
    },
    {
        "name": "Intent QA",
        "query": "Hello, can you explain to me Intent tasks and Java code tasks? Also, regarding Intents, what is the difference between sendBroadcast and startActivity, and what are their parameters?"
    }
]


def test_full_pipeline():

    print("\n" + "=" * 80)
    print("🚀 FULL AGENTIC PIPELINE DEBUG (ORIGINAL QUERIES)")
    print("=" * 80 + "\n")

    # INIT
    llm = create_llm_client()
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)

    embedder = Embedder.get_instance()
    sparse_embedder = SparseEmbedder.get_instance()
    store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)

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

    for test in TEST_QUERIES:

        print("\n" + "-" * 80)
        print(f"TEST: {test['name']}")
        print("-" * 80)

        raw_query = test["query"]
        print(f"\n🧠 USER QUERY:\n{raw_query}\n")

        # =====================================================
        # STEP 1: REWRITER
        # =====================================================
        print("🔹 STEP 1: Query Rewriter")

        rewrite_result = rewriter.rewrite(raw_query)

        intent = rewrite_result["intent"]
        task_names = rewrite_result["task_names"]
        search_query = rewrite_result["search_query_en"]

        print(f"   intent: {intent}")
        print(f"   task_names: {task_names}")
        print(f"   search_query_en: {search_query}\n")

        # =====================================================
        # STEP 2: PLANNER (only for workflow generation/correction)
        # =====================================================
        plan = None
        
        if intent in {"workflow_generation", "workflow_correction"}:
            print("🔹 STEP 2: Workflow Planner")

            # IMPORTANT: Pass suggested_tasks from Rewriter to Planner
            plan_result = planner.plan(
                user_request=search_query,
                suggested_tasks=task_names
            )

            if not plan_result["success"]:
                print(f"   ❌ Planner error: {plan_result['error']}\n")
                continue

            plan = plan_result["plan"]

            print(f"   confidence: {plan_result['confidence']}%")
            print(f"   ambiguities: {plan_result['ambiguities']}\n")

            print("   USER INTENTION:")
            print(f"   {plan.get('user_intention')}\n")

            print("   REQUIRED TASKS:")
            print(f"   {plan.get('required_tasks')}\n")

            print("   STEPS:")
            for step in plan.get("steps", []):
                print(f"   - {step}")
            print()
        else:
            print("🔹 STEP 2: Workflow Planner")
            print("   ⏭️ SKIPPED (QA intent — no planning needed)\n")

        # =====================================================
        # STEP 3: CONTEXT
        # =====================================================
        print("🔹 STEP 3: Context Building")

        if intent == "workflow_generation":

            print("   → WORKFLOW → Extraction\n")

            # Use tasks from plan if available, otherwise use Rewriter suggestions
            required_tasks = plan.get("required_tasks", task_names) if plan else task_names

            context = build_workflow_context_for_tasks(
                task_names=required_tasks,
                store=store
            )

        else:
            print("   → QA → Retrieval\n")

            dense = embedder.embed_text(search_query)
            sparse = sparse_embedder.embed_text(search_query)

            points = store.hybrid_search(
                dense_vector=dense,
                sparse_vector=sparse,
                limit=5,
                filter_conditions={"type_doc": "task_doc"}
            )

            context = "\n\n".join([
                f"# {p.payload.get('document_title')} - {p.payload.get('section_title')}\n{p.payload.get('content')}"
                for p in points
            ])

        # =====================================================
        # STEP 4: OUTPUT
        # =====================================================
        print("🔹 STEP 4: Context Preview")
        print("-" * 60)
        print(context[:500], "...\n")


if __name__ == "__main__":
    test_full_pipeline()