"""
Embedder module for AI Agent RAG pipeline.

Responsibilities:
- Load embedding model
- Convert text chunks into vector embeddings
- Support batch processing
"""

from typing import List, Optional
from sentence_transformers import SentenceTransformer
from src.utilities.logger import get_module_logger
from src.config import config

logger = get_module_logger("embedder")

# Global singleton instance - loaded once at startup
_embedder_instance: Optional['Embedder'] = None


class Embedder:
    """
    Generate embeddings using Sentence Transformers.
    Implements singleton pattern to load model once at startup.
    """

    def __init__(self, model_name: str = None):
        """
        Initialize embedding model.

        Args:
            model_name: HuggingFace embedding model (default from config)
        """
        model_name = model_name or config.EMBEDDING_MODEL
        logger.info("Loading embedding model: %s", model_name)

        try:
            self.model = SentenceTransformer(model_name)
            logger.info("Embedding model loaded successfully")
        except Exception:
            logger.exception("Failed to load embedding model")
            raise

    # -----------------------------
    # Embed single text
    # -----------------------------
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: input text

        Returns:
            embedding vector
        """

        embedding = self.model.encode(text, convert_to_numpy=True)

        return embedding.tolist()

    # -----------------------------
    # Singleton getter
    # -----------------------------
    @staticmethod
    def get_instance(model_name: str = None) -> 'Embedder':
        """
        Get singleton instance of Embedder.
        Load model only once when first called.
        
        Args:
            model_name: HuggingFace model (only used on first init)
            
        Returns:
            Singleton Embedder instance
        """
        global _embedder_instance
        if _embedder_instance is None:
            model_name = model_name or config.EMBEDDING_MODEL
            logger.info("[SINGLETON] Initializing Embedder with model: %s", model_name)
            _embedder_instance = Embedder(model_name)
            logger.info("[SINGLETON] Embedder ready for all requests")
        else:
            logger.debug("[SINGLETON] Reusing cached embedder instance")
        return _embedder_instance

    # -----------------------------
    # Embed batch of texts
    # -----------------------------
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: list of texts
            batch_size: batch size for processing

        Returns:
            list of embeddings
        """

        if texts is None:
            raise ValueError("texts cannot be None")
        if not isinstance(texts, list):
            raise TypeError("texts must be a list of strings")
        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError("batch_size must be a positive integer")

        # Filter invalid entries and keep only non-empty strings
        clean_texts = []
        for i, t in enumerate(texts):
            if not isinstance(t, str):
                logger.warning("Skipping non-string item at index %d: %r", i, t)
                continue
            normalized = t.strip()
            if not normalized:
                logger.warning("Skipping empty text at index %d", i)
                continue
            clean_texts.append(normalized)

        if not clean_texts:
            logger.warning("No valid texts to embed after filtering")
            return []

        logger.info("[BATCH_EMBED] Generating embeddings for %d chunks (batch_size=%d)", len(clean_texts), batch_size)

        try:
            embeddings = self.model.encode(
                clean_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            logger.info("[BATCH_EMBED] [OK] Successfully generated %d embeddings", len(embeddings))
        except Exception:
            logger.exception("Failed generating embeddings for batch")
            raise

        return embeddings.tolist()