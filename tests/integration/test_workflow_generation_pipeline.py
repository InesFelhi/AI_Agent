"""Integration test: Query rewriting + hybrid search + workflow generation prompt."""

from src.llm import create_llm_client
from src.rag.query_rewriter import QueryRewriter
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.ingestion_pipeline.task_section_extractor import build_workflow_context_for_tasks
from src.prompts import build_workflow_generation_prompt
from src.config import config
from src.workflow.json_validator import JSONValidator
from qdrant_client import QdrantClient
from src.utilities.logger import get_module_logger

logger = get_module_logger("test_workflow_generation")


def test_workflow_generation_pipeline(
    user_query: str = "Create a workflow using Cmd Stage to ping google.com and save the command output",
    provider: str = "ollama",
):
    """
    Full RAG pipeline test:
    1. Rewrite user query with QueryRewriter (using LLM)
    2. Perform hybrid search (dense + sparse embeddings)
    3. Build workflow generation prompt with retrieved context
    4. Display results
    """
    
    print("=" * 80)
    print("WORKFLOW GENERATION PIPELINE TEST")
    print("=" * 80)
    
    # Step 1: Initialize clients
    print("\n[STEP 1] Initializing LLM client...")
    try:
        llm_client = create_llm_client(provider=provider)
        print(f"✅ LLM client created: {type(llm_client).__name__}")
    except Exception as e:
        print(f"❌ Failed to create LLM client: {e}")
        return
    
    # Step 2: Initialize Qdrant and embedders
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
    
    # Step 3: Rewrite query with LLM
    print(f"\n[STEP 3] Rewriting query with QueryRewriter...")
    print(f"Original query: \"{user_query}\"")
    try:
        query_rewriter = QueryRewriter(
            llm_client=llm_client,
            qdrant_client=qdrant_client,
            collection_name=config.QDRANT_COLLECTION_NAME,
            cache_ttl_seconds=600
        )
        rewritten = query_rewriter.rewrite(user_query)
        print(f"✅ Query rewritten successfully")
        print(f"   Intent: {rewritten.get('intent')}")
        print(f"   Task names: {rewritten.get('task_names')}")
        print(f"   Search query: {rewritten.get('search_query_en')}")
    except Exception as e:
        print(f"❌ Query rewriting failed: {e}")
        rewritten = {
            "intent": "workflow_generation",
            "task_names": [],
            "search_query_en": user_query
        }
        print(f"⚠️ Using fallback query: {rewritten['search_query_en']}")
    
    # Step 4: Retrieve task documentation directly when task names are available
    print(f"\n[STEP 4] Retrieving task documentation...")
    retrieved_content = ""
    try:
        store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)

        task_names = rewritten.get("task_names", [])
        if task_names:
            print(f"✅ Task names detected: {task_names}")
            retrieved_content = build_workflow_context_for_tasks(task_names, store)
            if retrieved_content:
                print(f"✅ Built context from {len(task_names)} task(s)")
            else:
                print("⚠️ No direct task documentation found, falling back to hybrid search")

        if not retrieved_content:
            search_query = rewritten.get("search_query_en", user_query)
            dense_vector = embedder.embed_text(search_query)
            sparse_vector = sparse_embedder.embed_text(search_query)

            points = store.hybrid_search(
                dense_vector=dense_vector,
                sparse_vector=sparse_vector,
                limit=5
            )

            if not points:
                print("⚠️ No results from hybrid search, trying dense-only...")
                points = store.search(query_vector=dense_vector, limit=5)

            print(f"✅ Retrieved {len(points)} documents")
            for i, point in enumerate(points, 1):
                doc_id = point.payload.get("document_id", "unknown")
                doc_type = point.payload.get("type_doc", "unknown")
                score = point.score if hasattr(point, 'score') else "N/A"
                print(f"   [{i}] {doc_id} (type: {doc_type}, score: {score})")

            retrieved_content = "\n\n".join(
                [p.payload.get("content", "") for p in points]
            ).strip() or "No relevant documentation found"

    except Exception as e:
        print(f"❌ Documentation retrieval failed: {e}")
        retrieved_content = "No relevant documentation found"

    # Step 5: Build workflow generation prompt
    print(f"\n[STEP 5] Building workflow generation prompt...")
    try:
        system_prompt, user_prompt = build_workflow_generation_prompt(
            context=retrieved_content,
            instruction=user_query,
        )
        print(f"✅ Prompts built — system: {len(system_prompt)} chars, user: {len(user_prompt)} chars")
    except Exception as e:
        print(f"❌ Failed to build prompt: {e}")
        return
    
    # Step 6: Generate workflow JSON with LLM
    print(f"\n[STEP 6] Generating workflow JSON with LLM...")
    try:
        workflow_json = llm_client.complete(
            system=system_prompt,
            user=user_prompt,
            max_tokens=2000,
            temperature=0.1
        )
        print(f"✅ Workflow JSON generated successfully ({len(workflow_json)} characters)")
        print("\nGenerated Workflow JSON:")
        print("-" * 40)
        print(workflow_json)
        print("-" * 40)
    except Exception as e:
        print(f"❌ Failed to generate workflow JSON: {e}")
        return
    
    # Step 7: Validate generated workflow JSON
    print(f"\n[STEP 7] Validating generated workflow JSON...")
    try:
        validator = JSONValidator()
        validation_result = validator.validate(workflow_json)
        
        if validation_result.is_valid:
            print("✅ Workflow JSON validation PASSED")
            print("   - Syntax: OK")
            print("   - Structure: OK")
            print("   - Business rules: OK")
        else:
            print("❌ Workflow JSON validation FAILED")
            print(f"   - Found {len(validation_result.errors)} error(s):")
            for i, error in enumerate(validation_result.errors, 1):
                print(f"     [{i}] {error}")
                
        # Display parsed workflow if valid
        if validation_result.parsed:
            print(f"   - Parsed workflow contains:")
            for key, nodes in validation_result.parsed.items():
                if isinstance(nodes, list):
                    print(f"     - {key}: {len(nodes)} node(s)")
                else:
                    print(f"     - {key}: {type(nodes).__name__}")
                    
    except Exception as e:
        print(f"❌ Validation failed with exception: {e}")
    
    # Step 8: Display results
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
    print("✅ PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    test_workflow_generation_pipeline(
        provider="openai"
    )