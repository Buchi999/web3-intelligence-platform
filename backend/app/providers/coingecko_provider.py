"""
CoinGeckoPriceProvider — optional USD pricing via CoinGecko's free "Demo" tier.
Requires a free API key (x-cg-demo-api-key header) from coingecko.com/en/api/pricing.
Any failure degrades to None per-address rather than raising.
"""
import httpx

BASE_URL = "https://api.coingecko.com/api/v3/simple/token_price/ethereum"


class CoinGeckoPriceProvider:
    def __init__(self, api_key: str, timeout: float = 10.0):
        self._api_key = api_key
        self._client = httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_usd_prices(self, contract_addresses: list[str]) -> dict[str, float | None]:
        if not contract_addresses:
            return {}

        lowered = [a.lower() for a in contract_addresses]
        result: dict[str, float | None] = {a: None for a in lowered}

        try:
            response = await self._client.get(
                BASE_URL,
                params={"contract_addresses": ",".join(lowered), "vs_currencies": "usd"},
                headers={"x-cg-demo-api-key": self._api_key},
            )
            if response.status_code != 200:
                return result

            body = response.json()
            for addr, data in body.items():
                if isinstance(data, dict) and "usd" in data:
                    result[addr.lower()] = data["usd"]
        except httpx.RequestError:
            pass

        return result