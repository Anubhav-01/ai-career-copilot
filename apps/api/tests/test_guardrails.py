import pytest
from pydantic import BaseModel

from app.ai.guardrails import _extract_json, call_structured
from app.ai.llm.base import LLMProvider, LLMRequest
from app.core.errors import AIServiceError


class Sample(BaseModel):
    value: int
    label: str


class FlakyProvider(LLMProvider):
    """Returns garbage first, valid JSON on the second call."""

    name = "flaky"

    def __init__(self):
        self.calls = 0

    def generate(self, request: LLMRequest) -> str:
        self.calls += 1
        if self.calls == 1:
            return "definitely not json"
        return '{"value": 7, "label": "ok"}'


class AlwaysBrokenProvider(LLMProvider):
    name = "broken"

    def generate(self, request: LLMRequest) -> str:
        return '{"value": "not-an-int"}'


def test_extract_json_from_fenced_output():
    raw = '```json\n{"value": 1, "label": "x"}\n```'
    assert _extract_json(raw) == {"value": 1, "label": "x"}


def test_extract_json_with_surrounding_prose():
    raw = 'Here you go: {"value": 2, "label": "y"} hope that helps!'
    assert _extract_json(raw)["value"] == 2


def test_retry_recovers_from_invalid_output():
    provider = FlakyProvider()
    result = call_structured(provider, "test", "system", "prompt", Sample)
    assert result.value == 7
    assert provider.calls == 2


def test_exhausted_retries_raise_ai_error():
    with pytest.raises(AIServiceError):
        call_structured(AlwaysBrokenProvider(), "test", "system", "prompt", Sample)
