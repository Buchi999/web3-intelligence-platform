"""
PriceProvider abstraction. Pricing is optional enrichment, never a hard
dependency. NullPriceProvider is the default when no key is configured.
"""
from abc import ABC, abstractmethod


class PriceProvider(ABC):
    @abstractmethod
    async def get_usd_prices(self, contract_addresses: list[str]) -> dict[str, float | None]:
        """Return a dict mapping each input contract address (lowercased) to
        its current USD price, or None if unavailable for that address."""
        ...


class NullPriceProvider(PriceProvider):
    async def get_usd_prices(self, contract_addresses: list[str]) -> dict[str, float | None]:
        return {addr.lower(): None for addr in contract_addresses}