"""
LLMProvider abstraction. Optional enrichment, same pattern as pricing and
holder providers — never a hard requirement. Returns None on any failure
so report generation never breaks because of the AI layer.
"""
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str | None:
        ...


class NullLLMProvider(LLMProvider):
    async def generate(self, system_prompt: str, user_prompt: str) -> str | None:
        return None