"""LLM provider abstraction.

Providers implement a single `generate` method that returns raw text.
Structured output, JSON parsing, validation and retries are handled by
`app.ai.guardrails` so provider implementations stay thin.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMRequest:
    task: str  # semantic task name, e.g. "resume_extraction"
    system: str
    prompt: str
    max_tokens: int = 1500
    temperature: float = 0.2
    json_mode: bool = True


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    name: str = "base"

    @abstractmethod
    def generate(self, request: LLMRequest) -> str:
        """Return the raw model completion text. Raise AIServiceError on
        transport/model failures."""
        raise NotImplementedError
