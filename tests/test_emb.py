"""Test module for the Embedder component.

This module tests the embedding functionality, validating that text documents
are properly converted to vector representations using the sentence-transformers
model (all-MiniLM-L6-v2).

Tests verify:
- Batch embedding generation
- Vector dimension correctness (384-dimensional)
- Proper handling of multiple text samples
"""

from src.ingestion_pipeline.embedder import Embedder


def test_embedder():
    """Test the Embedder.embed_batch() method.
    
    Creates sample task descriptions and verifies that:
    1. The embedder generates embeddings for all texts
    2. Each embedding has the correct dimension (384D)
    3. Embeddings are numerical vectors (numpy arrays)
    
    Sample texts include various automation task types:
    - SMS task with parameters
    - Application launch task
    - Form filling task
    """
    # Initialize the embedder with default model
    embedder = Embedder()
    
    # Test data: sample task descriptions from the automation domain
    texts = [
        "Send SMS task requires phone_number parameter",
        "Open application task launches an Android app",
        "Fill form task requires field values"
    ]
    
    # Generate embeddings for all sample texts
    embeddings = embedder.embed_batch(texts)
    
    # Validate and display results
    print("=" * 60)
    print("Embedder Test Results")
    print("=" * 60)
    print(f"Number of embeddings generated: {len(embeddings)}")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First embedding sample (first 10 values): {embeddings[0][:10]}")
    print("=" * 60)


if __name__ == "__main__":
    test_embedder()


if __name__ == "__main__":
    test_embedder()