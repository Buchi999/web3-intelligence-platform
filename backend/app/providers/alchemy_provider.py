"""
AlchemyHolderProvider — real NFT collection holder lists via Alchemy's NFT API.
"""
import httpx

from app.core.exceptions import DataUnavailableError, ProviderRateLimitError
from app.providers.base import Confidence, HolderRecord, ProviderMeta

BASE_URL_TEMPLATE = "https://eth-mainnet.g.alchemy.com/nft/v3/{api_key}/getOwnersForContract"
MAX_PAGES = 20


class AlchemyHolderProvider:
    def __init__(self, api_key: str, timeout: float = 20.0):
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_owners(self, contract_address: str) -> list[HolderRecord]:
        url = BASE_URL_TEMPLATE.format(api_key=self._api_key)
        holders: dict[str, int] = {}
        page_key: str | None = None
        pages_fetched = 0

        while True:
            params = {"contractAddress": contract_address, "withTokenBalances": "true"}
            if page_key:
                params["pageKey"] = page_key

            try:
                response = await self._client.get(url, params=params)
            except httpx.RequestError as exc:
                raise DataUnavailableError(
                    f"Could not reach Alchemy NFT API: {type(exc).__name__}: {exc}"
                ) from exc

            if response.status_code == 429:
                raise ProviderRateLimitError("Alchemy NFT API rate limit reached. Try again shortly.")
            if response.status_code != 200:
                raise DataUnavailableError(f"Alchemy NFT API error: HTTP {response.status_code}")

            body = response.json()
            for owner in body.get("owners", []):
                address = (owner.get("ownerAddress") or "").lower()
                if not address:
                    continue
                balances = owner.get("tokenBalances") or []
                quantity = sum(int(b.get("balance", 1)) for b in balances) if balances else 1
                holders[address] = holders.get(address, 0) + quantity

            page_key = body.get("pageKey")
            pages_fetched += 1
            if not page_key or pages_fetched >= MAX_PAGES:
                break

        return [
            HolderRecord(
                address=address,
                quantity=quantity,
                meta=ProviderMeta(source="alchemy", confidence=Confidence.REAL),
            )
            for address, quantity in holders.items()
        ]