"""
HolderProvider abstraction — lists all current owners of an NFT collection.
No meaningful degraded fallback exists here (unlike pricing) — a missing
holder list is just missing data, not an estimate.
"""
from abc import ABC, abstractmethod

from app.core.exceptions import ProviderCapabilityError
from app.providers.base import HolderRecord


class HolderProvider(ABC):
    @abstractmethod
    async def get_owners(self, contract_address: str) -> list[HolderRecord]:
        ...


class NullHolderProvider(HolderProvider):
    async def get_owners(self, contract_address: str) -> list[HolderRecord]:
        raise ProviderCapabilityError(
            "NFT holder-list data requires a configured ALCHEMY_API_KEY (free tier "
            "available at https://dashboard.alchemy.com/signup). Etherscan's free tier "
            "has no endpoint for listing all holders of a collection."
        )