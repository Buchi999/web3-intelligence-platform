"""
BlockchainProvider abstraction.

No other part of the application should ever import a concrete provider
(EtherscanProvider, etc.) directly — always depend on BlockchainProvider and
get a concrete instance from providers.factory.get_blockchain_provider().

This is what lets us add AlchemyProvider, SolanaProvider, etc. later without
touching analysis or API code (architecture doc §7 / §16).

Every returned object carries a ProviderMeta so downstream consumers always
know: where did this come from, when was it fetched, and how much should we
trust it (real chain data vs. estimated vs. synthetic demo data). This is the
"data provenance" requirement from architecture doc §22 / spec §22.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class Confidence(str, Enum):
    REAL = "real"  # Directly retrieved from a live provider
    ESTIMATED = "estimated"  # Derived/aggregated from real data with some approximation
    SYNTHETIC = "synthetic"  # Demo-mode fabricated data, never to be treated as fact


class ProviderMeta(BaseModel):
    source: str  # e.g. "etherscan", "demo"
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: Confidence
    block_number: int | None = None


class WalletBalance(BaseModel):
    address: str
    native_balance_wei: str
    native_balance_native_unit: float  # e.g. ETH
    meta: ProviderMeta


class TokenBalance(BaseModel):
    contract_address: str
    symbol: str | None = None
    name: str | None = None
    decimals: int | None = None
    balance_raw: str
    balance_normalized: float | None = None
    meta: ProviderMeta


class TransactionDirection(str, Enum):
    IN = "in"
    OUT = "out"
    SELF = "self"


class Transaction(BaseModel):
    hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str | None
    value_wei: str
    direction: TransactionDirection
    is_error: bool = False
    method: str | None = None
    meta: ProviderMeta


class NFTHolding(BaseModel):
    collection_address: str
    token_id: str
    meta: ProviderMeta


class HolderRecord(BaseModel):
    address: str
    quantity: int
    meta: ProviderMeta


class ContractMetadata(BaseModel):
    address: str
    name: str | None = None
    is_verified: bool
    meta: ProviderMeta


class BlockchainProvider(ABC):
    """Abstract interface every chain/data provider must implement."""

    @abstractmethod
    async def get_wallet_balance(self, address: str) -> WalletBalance: ...

    @abstractmethod
    async def get_token_balances(self, address: str) -> list[TokenBalance]: ...

    @abstractmethod
    async def get_transactions(
        self, address: str, page: int = 1, offset: int = 100, sort: str = "desc"
    ) -> list[Transaction]: ...

    @abstractmethod
    async def get_nfts(self, address: str) -> list[NFTHolding]: ...

    @abstractmethod
    async def get_collection_holders(self, contract_address: str) -> list[HolderRecord]: ...

    @abstractmethod
    async def get_contract_metadata(self, contract_address: str) -> ContractMetadata: ...
