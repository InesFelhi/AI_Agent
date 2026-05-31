import pytest
from qdrant_client import QdrantClient

from src.config import config
from src.rag.task_registry import TaskNameRegistry


def test_task_registry_print_task_names():
    """Simple test that loads task names from Qdrant and prints them."""
    qdrant_client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    registry = TaskNameRegistry(
        qdrant_client=qdrant_client,
        collection_name=config.QDRANT_COLLECTION_NAME,
        cache_ttl_seconds=1
    )

    task_names = registry.get_task_names()

    print("\nLoaded task names from Qdrant:")
    for name in task_names:
        print(f"- {name}")

    assert isinstance(task_names, list)
    assert all(isinstance(name, str) and name.strip() for name in task_names)


if __name__ == "__main__":
    test_task_registry_print_task_names()