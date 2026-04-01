"""
Sparse Embedder module for AI Agent RAG pipeline.

Responsibilities:
- Load BM25 sparse embedding model (via FastEmbed)
- Convert text chunks into sparse vectors for keyword-based retrieval
- Support batch processing
- Follow singleton pattern identical to embedder.py

Why sparse vectors:
    Dense embeddings capture semantic meaning but struggle with exact
    technical terms like "CmdStage", "cmd_text", "IntegerSingleOps".
    BM25 sparse vectors score tokens by their frequency in the document
    and rarity across the corpus — rare technical tokens like "CmdStage"
    get a high score, common words like "the" get near zero.

Output format per chunk:
    {
        "indices": [42, 187, 903],   # token IDs present in the text
        "values":  [2.1, 1.8, 0.9]  # BM25 score for each token
    }
    This dict is passed directly to Qdrant's SparseVector(indices, values).
"""

from typing import List, Optional, Dict
from fastembed import SparseTextEmbedding
from src.utilities.logger import get_module_logger

logger = get_module_logger("sparse_embedder")

# BM25 model name — provided by Qdrant via FastEmbed
# Local execution, no cloud dependency
_SPARSE_MODEL_NAME = "Qdrant/bm25"

# Global singleton instance — loaded once at startup
_sparse_embedder_instance: Optional["SparseEmbedder"] = None


class SparseEmbedder:
    """
    Generate BM25 sparse vectors using FastEmbed.
    Implements singleton pattern identical to embedder.py.

    Used alongside Embedder (dense) to enable hybrid search in Qdrant.
    """

    def __init__(self, model_name: str = _SPARSE_MODEL_NAME) -> None:
        """
        Load the BM25 sparse embedding model.

        Args:
            model_name: FastEmbed sparse model identifier.
                        Default: "Qdrant/bm25"
        """
        logger.info("Loading sparse embedding model: %s", model_name)

        try:
            self.model = SparseTextEmbedding(model_name=model_name)
            self.model_name = model_name
            logger.info("Sparse embedding model loaded successfully")
        except Exception:
            logger.exception("Failed to load sparse embedding model")
            raise

    # --------------------------------------------------
    # Singleton getter — mirrors embedder.py pattern
    # --------------------------------------------------
    @staticmethod
    def get_instance(model_name: str = _SPARSE_MODEL_NAME) -> "SparseEmbedder":
        """
        Get singleton instance of SparseEmbedder.
        Model is loaded only once on first call.

        Args:
            model_name: only used on first initialization,
                        ignored on subsequent calls.

        Returns:
            Singleton SparseEmbedder instance
        """
        global _sparse_embedder_instance

        if _sparse_embedder_instance is None:
            logger.info(
                "[SINGLETON] Initializing SparseEmbedder with model: %s",
                model_name
            )
            _sparse_embedder_instance = SparseEmbedder(model_name)
            logger.info("[SINGLETON] SparseEmbedder ready for all requests")
        else:
            logger.debug("[SINGLETON] Reusing cached sparse embedder instance")

        return _sparse_embedder_instance

    # --------------------------------------------------
    # Embed single text
    # --------------------------------------------------
    def embed_text(self, text: str) -> Dict:
        """
        Generate sparse BM25 vector for a single text.
        Used at query time to embed the user query before hybrid search.

        Args:
            text: input text (query or chunk content)

        Returns:
            {"indices": List[int], "values": List[float]}
        """
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text must be a non-empty string")

        results = list(self.model.embed([text.strip()]))
        embedding = results[0]

        return {
            "indices": embedding.indices.tolist(),
            "values": embedding.values.tolist()
        }

    # --------------------------------------------------
    # Embed batch of texts
    # --------------------------------------------------
    def embed_batch(self, texts: List[str]) -> List[Dict]:
        """
        Generate BM25 sparse vectors for a list of texts.
        Used at ingestion time to embed all chunks.

        Args:
            texts: list of chunk content strings

        Returns:
            List of dicts: [{"indices": [...], "values": [...]}, ...]
            Each dict corresponds to one input text in the same order.
            Invalid or empty texts are skipped and returned as empty vectors.
        """
        if texts is None:
            raise ValueError("texts cannot be None")
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")
        if not texts:
            logger.warning("Empty texts list passed to embed_batch")
            return []

        # Validate and clean inputs — mirrors embedder.py behavior
        clean_texts = []
        skipped_indices = []

        for i, text in enumerate(texts):
            if not isinstance(text, str):
                logger.warning(
                    "Skipping non-string item at index %d: %r", i, text
                )
                skipped_indices.append(i)
                continue

            normalized = text.strip()
            if not normalized:
                logger.warning("Skipping empty text at index %d", i)
                skipped_indices.append(i)
                continue

            clean_texts.append(normalized)

        if not clean_texts:
            logger.warning("No valid texts to embed after filtering")
            return []

        logger.info(
            "[SPARSE_BATCH] Generating BM25 vectors for %d texts",
            len(clean_texts)
        )

        try:
            # FastEmbed returns a generator — consume fully into list
            raw_embeddings = list(self.model.embed(clean_texts))
        except Exception:
            logger.exception("Failed generating sparse embeddings for batch")
            raise

        # Convert to plain dicts for Qdrant compatibility
        results = []
        for embedding in raw_embeddings:
            results.append({
                "indices": embedding.indices.tolist(),
                "values": embedding.values.tolist()
            })

        logger.info(
            "[SPARSE_BATCH] [OK] Generated %d sparse vectors",
            len(results)
        )

        return results