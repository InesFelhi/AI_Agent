"""
Vector store module for AI Agent RAG pipeline.

Responsibilities:
- Connect to Qdrant
- Create hybrid collection (dense + sparse)
- Store embeddings and chunks with both vector types
- Perform hybrid similarity search (dense cosine + sparse BM25 fused by RRF)
"""

from typing import List, Optional, Dict
from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    SparseVectorParams,
    SparseIndexParams,
    SparseVector,
    Prefetch,
    FusionQuery,
    Fusion,
)
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

    # -------------------------------------------------------
    # Create collection
    # -------------------------------------------------------
    def _create_collection(self):

        collections = self.client.get_collections().collections
        existing = [c.name for c in collections]

        if self.collection_name in existing:
            logger.info("Collection already exists: %s", self.collection_name)
            return

        logger.info("Creating hybrid collection (dense + sparse): %s", self.collection_name)

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config={
                #  "dense" — standard semantic embedding vector
                "dense": VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            },
            sparse_vectors_config={
                #  "sparse" — BM25 keyword matching vector
                # on_disk=False keeps the index in RAM for faster search
                "sparse": SparseVectorParams(
                    index=SparseIndexParams(on_disk=False)
                )
            }
        )

        logger.info("Hybrid collection created successfully")

    # -------------------------------------------------------
    # Insert chunks

    def add_documents(
        self,
        chunks: List[Chunk],
        dense_embeddings: List[List[float]],
        sparse_vectors: Optional[List[Dict]] = None
    ):
        logger.info("Storing %d chunks in vector database", len(chunks))

        if not chunks or not dense_embeddings:
            logger.info("No chunks or embeddings to store. Skipping upsert.")
            return

        points = []

        for i, (chunk, dense) in enumerate(zip(chunks, dense_embeddings)):
            payload = chunk.metadata.copy()
            payload["content"] = chunk.content

            # Build vector dict depending on sparse availability
            if sparse_vectors and i < len(sparse_vectors):
                sv = sparse_vectors[i]
                vector = {
                    "dense": dense,
                    "sparse": SparseVector(
                        indices=sv["indices"],
                        values=sv["values"]
                    )
                }
            else:
                # Fallback: dense only — still valid for the collection
                vector = {"dense": dense}

            point = PointStruct(
                id=chunk.id,
                vector=vector,
                payload=payload
            )

            points.append(point)

        if not points:
            logger.info("Zero points to upsert after processing. Skipping.")
            return

        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
        except Exception as e:
            logger.exception("Vector store upsert failed")
            raise RuntimeError(f"Vector store upsert failed: {e}")

        logger.info("Chunks stored successfully")

    # -------------------------------------------------------
    # Delete chunks
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # Build filter helper
    # -------------------------------------------------------
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

    # -------------------------------------------------------
    # Hybrid search  
    # -------------------------------------------------------
   
    def hybrid_search(
        self,
        dense_vector: List[float],
        sparse_vector: Optional[Dict] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, str]] = None
    ) -> list:
        """
        Perform hybrid similarity search (dense + sparse BM25 fused by RRF).

        Args:
            dense_vector:      float embedding of the query
            sparse_vector:     BM25 sparse dict {"indices": [...], "values": [...]}
                               Pass None to fall back to dense-only search.
            limit:             number of results to return (top_k)
            score_threshold:   minimum score filter applied after fusion
            filter_conditions: metadata key/value filter (e.g. {"type_doc": "task_doc"})

        Returns:
            List of scored points with payload
        """
        logger.info(
            "Performing %s search (top_k=%d)",
            "hybrid" if sparse_vector else "dense",
            limit
        )

        query_filter = self._build_query_filter(filter_conditions)

        if sparse_vector is not None:
            # --- Hybrid path: dense + sparse prefetch, RRF fusion ---
            results = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=[
                    Prefetch(
                        query=dense_vector,
                        using="dense",
                        limit=20,
                        filter=query_filter
                    ),
                    Prefetch(
                        query=SparseVector(
                            indices=sparse_vector["indices"],
                            values=sparse_vector["values"]
                        ),
                        using="sparse",
                        limit=20,
                        filter=query_filter
                    )
                ],
                query=FusionQuery(fusion=Fusion.RRF),
                limit=limit,
                with_payload=True
            )
        else:
            # --- Dense-only fallback ---
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=dense_vector,
                using="dense",
                limit=limit,
                query_filter=query_filter,
                with_payload=True
            )

        points = results.points

        if score_threshold is not None:
            points = [p for p in points if p.score is not None and p.score >= score_threshold]

        logger.info("Found %d results", len(points))

        return points

    # -------------------------------------------------------
    # search() — kept for backward compatibility
    # -------------------------------------------------------
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, str]] = None
    ) -> list:
        """
        Dense-only similarity search. Kept for backward compatibility.
        Prefer hybrid_search() for production RAG queries.
        """
        return self.hybrid_search(
            dense_vector=query_vector,
            sparse_vector=None,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions
        )

    def search_by_doc_type(
        self,
        query_vector: List[float],
        doc_type: str,
        limit: int = 5,
        score_threshold: Optional[float] = None,
    ) -> list:
        return self.search(
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions={"type_doc": doc_type}
        )

    def fetch_points_by_filter(
        self,
        filter_conditions: Optional[Dict[str, str]] = None,
        batch_size: int = 100
    ) -> list:
        """
        Fetch all points matching the given metadata filter using Qdrant scroll.
        """
        points = []
        offset = None
        query_filter = self._build_query_filter(filter_conditions)

        while True:
            result, next_offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )

            points.extend(result)

            if next_offset is None:
                break

            offset = next_offset

        return points

    def get_document_text_by_title(
        self,
        document_title: str,
        doc_type: str = "task_doc"
    ) -> Optional[str]:
        """
        Retrieve the full document text for a task document by title.

        This reconstructs the document from its Qdrant chunks by sorting
        them by chunk_index and joining their content.
        """
        points = self.fetch_points_by_filter(
            filter_conditions={
                "type_doc": doc_type,
                "document_title": document_title
            }
        )

        if not points:
            return None

        points.sort(key=lambda p: p.payload.get("chunk_index", 0))
        contents = [p.payload.get("content", "") for p in points if p.payload.get("content")]
        return "\n\n".join(contents).strip()

    # -------------------------------------------------------
    # Format results helper
    # -------------------------------------------------------
    def format_results(self, points) -> List[Dict]:
        """
        Format raw Qdrant points into clean dicts for RAG usage.
        """
        return [
            {
                "score": p.score,
                "content": p.payload.get("content"),
                "metadata": p.payload
            }
            for p in points
        ]