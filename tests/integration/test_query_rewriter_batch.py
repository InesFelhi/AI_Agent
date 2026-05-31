import pytest
from qdrant_client import QdrantClient

from src.config import config
from src.llm import create_llm_client
from src.rag.query_rewriter import QueryRewriter
from src.prompts.query_rewriter_prompt import build_query_rewriter_prompt


def test_query_rewriter_batch():
    queries = [
        "Hello, can you explain to me Intent tasks and Java code tasks? Also, regarding Intents, what is the difference between sendBroadcast and startActivity, and what are their parameters?",
        "Give me a workflow that runs a PING to any server, then returns the minimum and maximum values of the results.",
        "Can you run an iperf3 command to a server at 0.0.0.0 using a UDP upload test? If possible, also start a PCAP capture before running iperf3, stop it after the test, and then upload the PCAP file (named test.pcap) to www.andromate_upload.net.",
        "Can you create a workflow to check whether the device is rooted or not? You can use a CMD task that requires root permission. If it returns an error, write \"not rooted device\", otherwise write \"rooted device\".",
        "Can you create a workflow that prints a multiplication table using arithmetic operations?",
        "Try to test the download speed using a download task and print the bitrate.",
        "Finally, tell me who you are."
    ]

    llm = create_llm_client()
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)

    rewriter = QueryRewriter(
        llm_client=llm,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    # Load task details store
    from src.ingestion_pipeline.vector_store import VectorStore
    from src.ingestion_pipeline.task_section_extractor import extract_task_sections
    store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*100}")
        print(f"QUERY {i}: {query}")
        print(f"{'='*100}")

        try:
            result = rewriter.rewrite(query)
            
            print(f"Detected intent: {result['intent']}")
            print(f"Search query en: {result['search_query_en']}")
            print(f"Extracted tasks ({len(result['task_names'])}): {result['task_names']}")
            
            for task_name in result['task_names']:
                print(f"\nTask: {task_name}")
                try:
                    doc_content = store.get_document_text_by_title(
                        document_title=task_name,
                        doc_type="task_doc"
                    )
                    if doc_content:
                        sections = extract_task_sections(doc_content)
                        print(f"  Purpose: {sections.get('summary', 'N/A')}")
                    else:
                        print("  Task document not found")
                except Exception as e:
                    print(f"  Error loading task details: {e}")

            # Basic assertions
            assert result.get("intent") in {"workflow_generation", "workflow_correction", "qa"}
            assert isinstance(result.get("task_names"), list)
            assert isinstance(result.get("search_query_en"), str)
            assert result.get("search_query_en").strip() != ""

        except Exception as e:
            print(f"ERROR processing query {i}: {e}")
            raise


if __name__ == "__main__":
    test_query_rewriter_batch()