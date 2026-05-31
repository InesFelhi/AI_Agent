import json
from qdrant_client import QdrantClient

from src.config import config
from src.llm import create_llm_client
from src.rag.query_rewriter import QueryRewriter
from src.workflow.workflow_planner import WorkflowPlanner


def test_query_rewriter_and_planner():
    queries = [
        "Give me a workflow that runs a PING to any server, then returns the minimum and maximum values of the results.",
        "Can you run an iperf3 command to a server at 0.0.0.0 using a UDP upload test? If possible, also start a PCAP capture before running iperf3, stop it after the test, and then upload the PCAP file (named test.pcap) to www.andromate_upload.net."
    ]

    llm = create_llm_client()
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)

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

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*100}")
        print(f"QUERY {i}: {query}")
        print(f"{'='*100}")

        rewrite = rewriter.rewrite(query)
        print(f"Detected intent: {rewrite['intent']}")
        print(f"Search query en: {rewrite['search_query_en']}")
        print(f"Extracted tasks ({len(rewrite['task_names'])}): {rewrite['task_names']}")

        if rewrite['intent'] in {"workflow_generation", "workflow_correction"}:
            plan_result = planner.plan(
                user_request=rewrite['search_query_en'],
                suggested_tasks=rewrite['task_names']
            )

            print(f"Planner success: {plan_result['success']}")
            print(f"Planner confidence: {plan_result['confidence']}")
            print(f"Planner ambiguities: {plan_result['ambiguities']}")

            if plan_result['plan']:
                print("\n" + "="*100)
                print("PLANNER RESPONSE (COMPLETE):")
                print("="*100)
                print(json.dumps(plan_result['plan'], indent=2, ensure_ascii=False))
                print("="*100 + "\n")
            else:
                print(f"Planner returned no plan. Error: {plan_result.get('error')}")

            assert plan_result['success'] is True, f"Planner failed for query {i}: {plan_result.get('error')}"
            assert isinstance(plan_result['plan'], dict)
            assert 'steps' in plan_result['plan']
        else:
            print("QA intent detected — planner is not executed for QA requests.")
            assert rewrite['intent'] == 'qa'


if __name__ == '__main__':
    test_query_rewriter_and_planner()
