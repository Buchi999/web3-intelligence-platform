"""
GroqLLMProvider — Groq's OpenAI-compatible chat completions API.
Every failure mode degrades to None rather than raising.
"""
import httpx

BASE_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqLLMProvider:
    def __init__(self, api_key: str, model: str, timeout: float = 30.0):
        self._api_key = api_key
        self._model = model
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def generate(self, system_prompt: str, user_prompt: str) -> str | None:
        try:
            response = await self._client.post(
                BASE_URL,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.3,  # lower temperature: factual synthesis, not creative writing
                    # max_tokens must be enough for all 9 required report sections to
                    # complete without truncation — 700 was verified live to cut the response
                    # off mid-sentence before finishing every section (see wallet_narrative.py).
                    "max_tokens": 1100,
                },
            )
        except httpx.RequestError:
            return None

        if response.status_code != 200:
            return None

        try:
            body = response.json()
            return body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, ValueError):
            return None