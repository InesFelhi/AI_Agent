"""
Vector store module for AI Agent RAG pipeline.

Responsibilities:
- Connect to Qdrant
- Create collection
- Store embeddings and chunks
- Perform similarity search
"""

from typing import List, Optional, Dict
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
from src.ingestion_pipeline.schemas import Chunk
from src.utilities.logger import get_module_logger
from src.config import config

logger = get_module_logger("vector_store")


class VectorStore:

    def __init__(
        self,
        collection_name: str = None,
        host: str = None,
        port: int = None,
        vector_size: int = None
    ):
        self.collection_name = collection_name or config.QDRANT_COLLECTION_NAME
        self.vector_size = vector_size or config.QDRANT_VECTOR_SIZE

        host = host or config.QDRANT_HOST
        port = port or config.QDRANT_PORT

        logger.info("Connecting to Qdrant at %s:%d", host, port)

        self.client = QdrantClient(
            host=host,
            port=port
        )

        self._create_collection()

    # -----------------------------
    # Create collection
    # -----------------------------
    def _create_collection(self):

        collections = self.client.get_collections().collections
        existing = [c.name for c in collections]

        if self.collection_name in existing:
            logger.info("Collection already exists")
            return

        logger.info("Creating collection: %s", self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            )
        )

    # -----------------------------
    # Insert chunks
    # -----------------------------
    def add_documents(
        self,
        chunks: List[Chunk],
        embeddings: List[List[float]]
    ):
        logger.info("Storing %d chunks in vector database", len(chunks))

        points = []

        for chunk, vector in zip(chunks, embeddings):

            payload = chunk.metadata.copy()
            payload["content"] = chunk.content

            point = PointStruct(
                id=chunk.id,
                vector=vector,
                payload=payload
            )

            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

        logger.info("Chunks stored successfully")

    # -----------------------------
    # Delete chunks
    # -----------------------------
    def delete_documents(self, filter_conditions: Optional[Dict[str, str]] = None):
        """
        Delete points matching the filter conditions.
        """
        logger.info("Deleting documents with filter: %s", filter_conditions)

        query_filter = self._build_query_filter(filter_conditions)

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=query_filter)
        )

        logger.info("Documents deleted successfully")

    # -----------------------------
    # Search (Similarity Search)
    # -----------------------------
    def _build_query_filter(self, filter_conditions: Optional[Dict[str, str]] = None):
        if not filter_conditions:
            return None
        conditions = [
            models.FieldCondition(
                key=key,
                match=models.MatchValue(value=value)
            )
            for key, value in filter_conditions.items()
        ]
        return models.Filter(must=conditions)

    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, str]] = None
    ):
        """
        Perform similarity search in Qdrant

        Args:
            query_vector: embedding of the query
            limit: number of results (top_k)
            score_threshold: minimum similarity score
            filter_conditions: dict for metadata filtering

        Returns:
            List of points
        """

        logger.info("Performing similarity search (top_k=%d)", limit)

        query_filter = self._build_query_filter(filter_conditions)

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True
        )

        points = results.points

        if score_threshold is not None:
            points = [p for p in points if p.score is not None and p.score >= score_threshold]

        logger.info("Found %d results", len(points))

        return points

    def search_by_doc_type(
        self,
        query_vector: List[float],
        doc_type: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ):
        return self.search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions={"type_doc": doc_type}
        )

    # -----------------------------
    # Optional: Format results
    # -----------------------------
    def format_results(self, points):
        """
        Format results for easier usage in RAG
        """

        return [
            {
                "score": p.score,
                "content": p.payload.get("content"),
                "metadata": p.payload
            }
            for p in points
        ]