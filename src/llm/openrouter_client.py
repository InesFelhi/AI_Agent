import requests
from typing import Optional, Dict, Any
from src.llm.base import LLMClient
from src.config import Config
from src.utilities.logger import get_module_logger

logger = get_module_logger("llm")


class OpenRouterClient(LLMClient):
    """OpenRouter LLM client implementation."""

    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.model = Config.OPENROUTER_MODEL
        self.base_url = Config.OPENROUTER_BASE_URL
        self.timeout = 60  # Increased from 30s to 60s to handle SSL handshakes

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")

    def complete(self, system: str, user: str, max_tokens: int = 300, temperature: float = 0.0) -> str:
        """Generate a response using OpenRouter API."""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://your-app.com",  # Optional, for rankings
                "X-Title": "AI Agent",  # Optional, for rankings
            }

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": user})

            data = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                raise Exception(f"OpenRouter API error: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error with OpenRouter: {e}")
            raise Exception(f"Failed to communicate with OpenRouter: {e}")

    def is_available(self) -> bool:
        """Check if OpenRouter service is available."""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}/models", headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False