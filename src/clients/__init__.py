"""
Centralized client management for connection pooling.

This module provides singleton instances of external service clients
to maximize connection reuse and minimize resource overhead.
"""

from .qdrant_pool import get_qdrant_client
from .llm_pool import get_llm_client

__all__ = ["get_qdrant_client", "get_llm_client"]
