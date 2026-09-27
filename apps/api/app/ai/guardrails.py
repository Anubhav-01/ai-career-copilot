"""Guardrails around LLM calls: JSON extraction, schema validation,
bounded retries, and AI usage counters for observability.

No raw LLM output is ever trusted or persisted without passing Pydantic
validation here.
"""
import json
import time
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.ai.llm.base import LLMProvider, LLMRequest
from app.core.cache import get_cache
from app.core.config import get_settings
from app.core.errors import AIServiceError
from app.core.logging import get_logger, log_event

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


def _extract_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from model output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return json.loads(cleaned[start : end + 1])


def _count(metric: str) -> None:
    cache = get_cache()
    current = cache.get(f"metrics:{metric}") or 0
    cache.set(f"metrics:{metric}", int(current) + 1)


def call_structured(
    provider: LLMProvider,
    task: str,
    system: str,
    prompt: str,
    schema: type[T],
    max_tokens: int = 1500,
) -> T:
    """Call the LLM and validate output against `schema`.

    Retries (with the validation error appended to the prompt) up to
    settings.llm_max_retries times, then raises AIServiceError.
    """
    settings = get_settings()
    attempts = settings.llm_max_retries + 1
    last_error: Exception | None = None
    current_prompt = prompt

    for attempt in range(attempts):
        started = time.perf_counter()
        _count("ai_requests")
        try:
            raw = provider.generate(
                LLMRequest(task=task, system=system, prompt=current_prompt, max_tokens=max_tokens)
            )
            data = _extract_json(raw)
            result = schema.model_validate(data)
            log_event(
                logger,
                "ai_call_ok",
                ai_operation=task,
                provider=provider.name,
                latency_ms=round((time.perf_counter() - started) * 1000),
                attempt=attempt + 1,
            )
            return result
        except (ValueError, ValidationError, json.JSONDecodeError) as exc:
            last_error = exc
            _count("ai_errors")
            log_event(
                logger,
                "ai_call_invalid_output",
                ai_operation=task,
                provider=provider.name,
                attempt=attempt + 1,
                error=type(exc).__name__,
            )
            current_prompt = (
                f"{prompt}\n\nYour previous output was invalid"
                f" ({type(exc).__name__}). Return ONLY a valid JSON object"
                f" matching the schema."
            )
        except AIServiceError:
            _count("ai_errors")
            raise

    raise AIServiceError(
        "The AI service returned an invalid response. Please try again."
    ) from last_error
