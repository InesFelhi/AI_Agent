"""Local Ollama chat completion client."""

import json
from typing import Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.utilities.logger import get_module_logger

logger = get_module_logger("llm")


class OllamaClient:
    """Local Ollama client using the Ollama HTTP API."""

    def __init__(
        self,
        host: str = "http://127.0.0.1:11434",
        model: str = "llama2",
        timeout: int = 180
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, payload: Dict) -> Dict:
        url = f"{self.host}/api/chat"
        headers = {"Content-Type": "application/json"}
        payload["stream"] = False  # Disable streaming to get single response
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as exc:
            logger.error("Ollama request failed: %s", exc)
            raise
        except URLError as exc:
            logger.error("Ollama connection error: %s", exc)
            raise
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse Ollama response: %s", exc)
            raise

    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 300,
        temperature: float = 0.0
    ) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        response = self._request(payload)
        
        # Ollama /api/chat returns {"message": {"content": "..."}}
        message = response.get("message")
        if not message or not isinstance(message, dict):
            raise ValueError("No message returned from Ollama")
        
        content = message.get("content", "").strip()
        if not content:
            raise ValueError("Empty content returned from Ollama")
        
        return content
