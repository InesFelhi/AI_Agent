"""
Qdrant connection pool management.

Provides a singleton QdrantClient instance to ensure:
- Single TCP connection pool reused across all requests
- No connection overhead per request
- Graceful reconnection on failure
"""

from typing import Optional
from qdrant_client import QdrantClient
from src.config import config
from src.utilities.logger import get_module_logger

logger = get_module_logger("qdrant_pool")

# Global client instance - initialized on first use
_qdrant_client: Optional[QdrantClient] = None


def get_qdrant_client() -> QdrantClient:
    """
    Get the singleton Qdrant client instance with connection pooling.
    
    The client is created once and reused for all requests.
    Uses gRPC for better performance and connection pooling.
    
    Returns:
        QdrantClient: Shared client instance with connection pool
        
    Raises:
        ConnectionError: If unable to connect to Qdrant server
    """
    global _qdrant_client
    
    if _qdrant_client is not None:
        return _qdrant_client
    
    logger.info(
        "[QDRANT] Initializing connection pool to %s:%d (gRPC)",
        config.QDRANT_HOST,
        config.QDRANT_PORT
    )
    
    try:
        _qdrant_client = QdrantClient(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            prefer_grpc=True,  # Use gRPC instead of HTTP for better performance
            timeout=30  # Connection timeout
        )
        
        # Test connection
        collections = _qdrant_client.get_collections()
        logger.info(
            "[QDRANT] Connection pool established successfully. "
            "Found %d collections", 
            len(collections.collections)
        )
        
        return _qdrant_client
        
    except Exception as e:
        logger.error("[QDRANT] Failed to establish connection pool: %s", str(e))
        _qdrant_client = None
        raise ConnectionError(f"Cannot connect to Qdrant at {config.QDRANT_HOST}:{config.QDRANT_PORT}") from e


def reset_qdrant_client():
    """
    Reset the client connection pool (useful for testing or recovery).
    
    Call this to force reconnection on next get_qdrant_client() call.
    """
    global _qdrant_client
    if _qdrant_client is not None:
        logger.info("[QDRANT] Resetting connection pool")
        _qdrant_client = None
