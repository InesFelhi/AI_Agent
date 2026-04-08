"""Base LLM interface definitions."""

from typing import Protocol


class LLMClient(Protocol):
    def complete(
        self,
        system: str,
        user: str,
        max_tokens: int = 300,
        temperature: float = 0.0
    ) -> str:
        ...
