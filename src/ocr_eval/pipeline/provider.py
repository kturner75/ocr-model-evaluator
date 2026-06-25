from dataclasses import dataclass
from typing import Any, Protocol

import litellm

from ocr_eval.models.domain import ModelConfig


@dataclass
class ProviderResponse:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class Provider(Protocol):
    def extract(self, messages: list[dict], model_config: ModelConfig) -> ProviderResponse: ...


class LiteLLMProvider:
    def extract(self, messages: list[dict], model_config: ModelConfig) -> ProviderResponse:
        kwargs: dict[str, Any] = {
            "model": model_config.model_id,
            "messages": messages,
        }

        if model_config.api_base:
            kwargs["api_base"] = model_config.api_base

        params = model_config.parameters
        if "temperature" in params:
            kwargs["temperature"] = params["temperature"]
        if "max_tokens" in params:
            kwargs["max_tokens"] = params["max_tokens"]

        try:
            kwargs["response_format"] = {"type": "json_object"}
            response = litellm.completion(**kwargs)
        except Exception:
            kwargs.pop("response_format", None)
            response = litellm.completion(**kwargs)

        usage = response.usage
        return ProviderResponse(
            content=response.choices[0].message.content,
            input_tokens=usage.prompt_tokens or 0,
            output_tokens=usage.completion_tokens or 0,
            total_tokens=usage.total_tokens or 0,
        )
