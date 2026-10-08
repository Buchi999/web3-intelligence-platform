"""
LLM provider factory — mirrors providers/factory.py's pattern.
"""
from functools import lru_cache

from app.core.config import get_settings
from app.llm.base import LLMProvider, NullLLMProvider
from app.llm.groq_provider import GroqLLMProvider


@lru_cache
def _get_groq_provider() -> GroqLLMProvider:
    settings = get_settings()
    assert settings.GROQ_API_KEY, "GROQ_API_KEY must be set to build GroqLLMProvider"
    return GroqLLMProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)


@lru_cache
def _get_null_llm_provider() -> NullLLMProvider:
    return NullLLMProvider()


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.GROQ_API_KEY:
        return _get_groq_provider()
    return _get_null_llm_provider()