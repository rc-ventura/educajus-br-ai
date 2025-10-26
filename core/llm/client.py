from __future__ import annotations
from typing import Any, Dict, List, Optional
import os

import litellm

from core.utils.logging import get_logger


logger = get_logger(__name__)

DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "openai")


def _ensure_provider_credentials(provider: str) -> None:
    """Validate that required credentials for the provider are present."""
    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not configured")


def chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.0,
    max_tokens: int = 512,
    provider: Optional[str] = None,
    **kwargs: Any,
) -> str:
    """Call LiteLLM completion compatible with OpenAI chat format."""
    model_name = model or DEFAULT_MODEL
    provider_name = provider or DEFAULT_PROVIDER

    _ensure_provider_credentials(provider_name)

    response = litellm.completion(
        model=model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        api_base=os.getenv("LITELLM_API_BASE"),
        **kwargs,
    )

    try:
        choice = response["choices"][0]["message"].get("content", "")
    except (KeyError, IndexError):
        logger.error("LiteLLM: unexpected response format: %s", response)
        raise RuntimeError("LLM response missing content")

    return choice.strip()
