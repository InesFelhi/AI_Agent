"""
Utility script to clear Qdrant collection for fresh testing.
"""

from qdrant_client import QdrantClient

def clear_collection(collection_name: str = "andromate_docs"):
    """Delete and recreate collection for testing."""
    client = QdrantClient(host="localhost", port=6333)
    
    # Get existing collections
    collections = client.get_collections().collections
    existing = [c.name for c in collections]
    
    if collection_name in existing:
        print(f"Deleting collection: {collection_name}")
        client.delete_collection(collection_name=collection_name)
        print(f"✅ Collection deleted")
    else:
        print(f"Collection {collection_name} does not exist")

if __name__ == "__main__":
    clear_collection("andromate_docs")
    print("\n✅ Ready for fresh ingestion with corrected hash logic!")
