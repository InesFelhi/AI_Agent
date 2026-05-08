"""OpenAI-compatible chat completion client."""

import json
from typing import Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.config import config
from src.utilities.logger import get_module_logger

logger = get_module_logger("llm")


class OpenAIChatClient:
    """Chat completion client for OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt‑4.1‑mini",
        base_url: str = "https://api.openai.com/v1"
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def _request(self, payload: Dict) -> Dict:
        if not self.api_key:
            raise ValueError("OpenAI API key is required for OpenAIChatClient")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urlopen(request, timeout=30) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as exc:
            try:
                error_body = exc.read().decode("utf-8")
                logger.error("OpenAI API request failed: %s - body: %s", exc, error_body)
            except Exception:
                logger.error("OpenAI API request failed: %s - could not read error body", exc)
            raise
        except URLError as exc:
            logger.error("OpenAI connection error: %s", exc)
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
            "temperature": temperature,
            "n": 1
        }

        response = self._request(payload)
        choices = response.get("choices")
        if not choices:
            raise ValueError("No response choices returned from OpenAI API")

        message = choices[0].get("message")
        if message and isinstance(message, dict):
            return message.get("content", "").strip()

        return str(choices[0].get("text", "")).strip()
