"""OpenAI chat-completions provider (plain httpx, no SDK dependency).

The API key is read from settings (environment) and never logged or
returned to clients.
"""
import httpx

from app.ai.llm.base import LLMProvider, LLMRequest
from app.core.config import get_settings
from app.core.errors import AIServiceError
from app.core.logging import get_logger, log_event

logger = get_logger(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self._api_key = api_key or settings.llm_api_key
        self._model = model or settings.llm_model
        self._timeout = settings.llm_timeout_seconds
        if not self._api_key:
            raise AIServiceError("LLM_API_KEY is not configured.")

    def generate(self, request: LLMRequest) -> str:
        payload: dict = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            response = httpx.post(
                OPENAI_URL,
                json=payload,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            log_event(logger, "llm_timeout", ai_operation=request.task)
            raise AIServiceError("The AI service timed out.") from exc
        except httpx.HTTPError as exc:
            log_event(logger, "llm_transport_error", ai_operation=request.task)
            raise AIServiceError() from exc

        if response.status_code == 429:
            raise AIServiceError("AI provider rate limit reached. Try again shortly.")
        if response.status_code >= 400:
            log_event(
                logger,
                "llm_api_error",
                ai_operation=request.task,
                status=response.status_code,
            )
            raise AIServiceError()

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIServiceError("Unexpected AI provider response format.") from exc
