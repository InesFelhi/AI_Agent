"""Factory for creating configured LLM clients."""

from typing import Optional

from src.config import config
from src.llm.base import LLMClient
from src.llm.openai_client import OpenAIChatClient
from src.llm.ollama_client import OllamaClient
from src.llm.openrouter_client import OpenRouterClient


def create_llm_client(provider: Optional[str] = None) -> LLMClient:
    provider = (provider or config.LLM_PROVIDER or "openai").strip().lower()
    if provider == "openai":
        return OpenAIChatClient(
            api_key=config.OPENAI_API_KEY or "",
            model=config.OPENAI_MODEL
        )
    if provider == "ollama":
        return OllamaClient(
            host=config.OLLAMA_HOST,
            model=config.OLLAMA_MODEL,
            timeout=config.OLLAMA_TIMEOUT
        )
    if provider == "openrouter":
        return OpenRouterClient()
    raise ValueError(f"Unsupported LLM provider: {provider}")
