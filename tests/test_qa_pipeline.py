"""
QA (Question & Answer) pipeline test.

For QA use case:
- User asks a question about the application
- Use hybrid search (dense + sparse) to retrieve relevant documents
- Send retrieved context to LLM to answer the question
- NO extraction of sections (full document context is useful)
"""

from src.llm import create_llm_client
from src.ingestion_pipeline.vector_store import VectorStore
from src.ingestion_pipeline.embedder import Embedder
from src.ingestion_pipeline.sparse_embedder import SparseEmbedder
from src.config import config
from qdrant_client import QdrantClient
from src.utilities.logger import get_module_logger

logger = get_module_logger("test_qa_pipeline")


def test_qa_pipeline(
    user_question: str = "What is the Cmd Stage used for and what are its input parameters?",
    provider: str = "openai",
):
    """
    QA pipeline test:
    1. Initialize LLM and vector store
    2. Embed user question (dense + sparse)
    3. Perform hybrid search to retrieve relevant documents
    4. Build QA prompt with retrieved context
    5. Call LLM to answer the question
    """
    
    print("=" * 80)
    print("QA PIPELINE TEST")
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
    print("\n[STEP 2] Initializing vector store and embedders...")
    try:
        qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT
        )
        embedder = Embedder.get_instance()
        sparse_embedder = SparseEmbedder.get_instance()
        store = VectorStore(collection_name=config.QDRANT_COLLECTION_NAME)
        
        print(f"✅ Qdrant connected to {config.QDRANT_HOST}:{config.QDRANT_PORT}")
        print(f"✅ Dense embedder: {config.EMBEDDING_MODEL}")
        print(f"✅ Sparse embedder: BM25")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return
    
    # Step 3: Embed question (dense + sparse)
    print(f"\n[STEP 3] Embedding user question...")
    print(f"Question: \"{user_question}\"")
    try:
        dense_vector = embedder.embed_text(user_question)
        sparse_vector = sparse_embedder.embed_text(user_question)
        print(f"✅ Question embedded (dense: {len(dense_vector)} dims, sparse: {len(sparse_vector['indices'])} tokens)")
    except Exception as e:
        print(f"❌ Failed to embed question: {e}")
        return
    
    # Step 4: Perform hybrid search
    print(f"\n[STEP 4] Performing hybrid search...")
    try:
        points = store.hybrid_search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=5
        )
        
        if not points:
            print("⚠️ No results from hybrid search")
            return
        
        print(f"✅ Retrieved {len(points)} relevant documents")
        for i, point in enumerate(points, 1):
            doc_id = point.payload.get("document_id", "unknown")
            doc_type = point.payload.get("type_doc", "unknown")
            section = point.payload.get("section_title", "unknown")
            score = point.score if hasattr(point, 'score') else "N/A"
            print(f"   [{i}] {doc_id} > {section} (type: {doc_type}, score: {score})")
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        return
    
    # Step 5: Build context from retrieved documents
    print(f"\n[STEP 5] Building context from retrieved documents...")
    try:
        # Combine all document content for context
        context_parts = []
        for point in points:
            doc_id = point.payload.get("document_id", "unknown")
            section_title = point.payload.get("section_title", "unknown")
            content = point.payload.get("content", "")
            
            context_parts.append(f"# {doc_id} > {section_title}\n{content}")
        
        context = "\n\n---\n\n".join(context_parts)
        print(f"✅ Context built ({len(context)} characters)")
    except Exception as e:
        print(f"❌ Failed to build context: {e}")
        return
    
    # Step 6: Build QA prompt
    print(f"\n[STEP 6] Building QA prompt...")
    try:
        qa_system_prompt = """You are a helpful assistant for Android workflow automation.
Answer questions based on the provided documentation.
Be concise and accurate.
If you don't know the answer, say so."""

        qa_user_prompt = f"""Based on the following documentation, answer this question:

Question: {user_question}

Documentation:
{context}

Answer:"""
        
        print(f"✅ QA prompt built (system: {len(qa_system_prompt)} chars, user: {len(qa_user_prompt)} chars)")
    except Exception as e:
        print(f"❌ Failed to build prompt: {e}")
        return
    
    # Step 7: Get answer from LLM
    print(f"\n[STEP 7] Generating answer with LLM...")
    try:
        answer = llm_client.complete(
            system=qa_system_prompt,
            user=qa_user_prompt,
            max_tokens=1000,
            temperature=0.3
        )
        print(f"✅ Answer generated ({len(answer)} characters)")
        print("\n" + "=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(answer)
        print("=" * 80)
    except Exception as e:
        print(f"❌ Failed to generate answer: {e}")
        return
    
    # Step 8: Display full context
    print("\n" + "=" * 80)
    print("RETRIEVED CONTEXT")
    print("=" * 80)
    print(context[:2000])
    if len(context) > 2000:
        print(f"\n...[truncated, {len(context) - 2000} more characters]")
    
    print("\n" + "=" * 80)
    print("✅ QA PIPELINE TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    # Test 1: Question about Cmd Stage
    test_qa_pipeline(
        user_question="What is the Cmd Stage used for and what are its input parameters?",
        provider="openai"
    )
    
    print("\n\n")
    
    # Test 2: Question about Http Request Stage
    test_qa_pipeline(
        user_question="How do I send a POST request with JSON body using Http Request Stage?",
        provider="openai"
    )
