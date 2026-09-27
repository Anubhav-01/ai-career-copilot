from app.ai.llm.base import LLMProvider
from app.ai.llm.mock_provider import MockProvider
from app.ai.llm.openai_provider import OpenAIProvider
from app.core.config import get_settings

_provider: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    global _provider
    if _provider is None:
        settings = get_settings()
        if settings.llm_provider == "openai":
            _provider = OpenAIProvider()
        else:
            _provider = MockProvider()
    return _provider


def reset_llm_provider() -> None:
    """Test helper."""
    global _provider
    _provider = None
