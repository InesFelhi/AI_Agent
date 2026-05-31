import pytest
from qdrant_client import QdrantClient

from src.config import config
from src.llm import create_llm_client
from src.rag.query_rewriter import QueryRewriter
from src.prompts.query_rewriter_prompt import build_query_rewriter_prompt


def test_query_rewriter_simple_display():
    query = (
        "Can you run an iperf3 command to a server at 0.0.0.0 using a UDP upload test? If possible, also start a PCAP capture before running iperf3, stop it after the test, and then upload the PCAP file (named test.pcap) to www.andromate_upload.net."
    )

    llm = create_llm_client()
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)

    rewriter = QueryRewriter(
        llm_client=llm,
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )

    # Test the new metadata-driven approach
    result = rewriter.rewrite(query)
    
    print("\n" + "="*80)
    print("QUERY REWRITER RESULT:")
    print("="*80)
    print(f"User query: {query}")
    print(f"Detected intent: {result['intent']}")
    print(f"Search query en: {result['search_query_en']}")
    print(f"Extracted tasks ({len(result['task_names'])}): {result['task_names']}")
    
    # Load task details for display
    from src.ingestion_pipeline.vector_store import VectorStore
    from src.ingestion_pipeline.task_section_extractor import extract_task_sections
    store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)
    
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
                print(f"  Key capabilities: {sections.get('detailed_description', 'N/A')}")
                print(f"  Input parameters: {sections.get('input_parameters', 'N/A')}")
                print(f"  Output variables: {sections.get('outputs', 'N/A')}")
            else:
                print("  Task document not found")
        except Exception as e:
            print(f"  Error loading task details: {e}")

    assert result.get("intent") in {"workflow_generation", "workflow_correction", "qa"}
    assert isinstance(result.get("task_names"), list)
    assert isinstance(result.get("search_query_en"), str)
    assert result.get("search_query_en").strip() != ""


if __name__ == "__main__":
    test_query_rewriter_simple_display()