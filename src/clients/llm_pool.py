"""
LLM client pool management.

Provides singleton LLM client instances for each provider to ensure:
- Single connection per provider (no repeated initialization)
- Session reuse (persistent for OpenAI, Ollama clients)
- Efficient resource usage with connection pooling
"""

from typing import Dict, Optional, Any
from src.llm import create_llm_client
from src.config import config
from src.utilities.logger import get_module_logger

logger = get_module_logger("llm_pool")

# Global client pool - one client per provider
_llm_clients: Dict[str, Any] = {}


def get_llm_client(provider: Optional[str] = None) -> Any:
    """
    Get or create a singleton LLM client for the specified provider.
    
    Clients are cached by provider to reuse connections and sessions.
    This avoids repeated initialization overhead for each request.
    
    Args:
        provider: LLM provider ('openai', 'ollama', 'openrouter', or None for default)
        
    Returns:
        LLM client instance (OpenAI, Ollama, OpenRouter, etc.)
        
    Raises:
        ValueError: If invalid provider specified
    """
    # Use default provider if none specified
    if provider is None:
        provider = config.LLM_PROVIDER or "openai"
    
    # Check if client already cached
    if provider in _llm_clients:
        logger.debug("[LLM_POOL] Reusing cached %s client", provider)
        return _llm_clients[provider]
    
    logger.info("[LLM_POOL] Initializing connection pool for provider: %s", provider)
    
    try:
        client = create_llm_client(provider=provider)
        _llm_clients[provider] = client
        logger.info("[LLM_POOL] %s client initialized and pooled", provider)
        return client
        
    except ValueError as e:
        logger.error("[LLM_POOL] Invalid provider '%s': %s", provider, str(e))
        raise
    except Exception as e:
        logger.error("[LLM_POOL] Failed to initialize %s client: %s", provider, str(e))
        raise


def reset_llm_client(provider: Optional[str] = None):
    """
    Reset LLM client pool for specified provider (or all if None).
    
    Useful for testing or switching providers dynamically.
    
    Args:
        provider: Provider to reset ('openai', 'ollama', etc.) or None to reset all
    """
    global _llm_clients
    
    if provider is None:
        logger.info("[LLM_POOL] Resetting all LLM client pools")
        _llm_clients.clear()
    elif provider in _llm_clients:
        logger.info("[LLM_POOL] Resetting %s client pool", provider)
        del _llm_clients[provider]


def get_cached_providers() -> list:
    """
    Get list of currently cached LLM providers.
    
    Returns:
        List of provider names with active client pools
    """
    return list(_llm_clients.keys())
