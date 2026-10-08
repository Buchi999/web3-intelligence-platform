"""
DemoProvider — used automatically when settings.DEMO_MODE is True (i.e. no
ETHERSCAN_API_KEY configured).

Every value returned here is fabricated and every ProviderMeta is marked
Confidence.SYNTHETIC so nothing downstream can mistake it for real chain
data (spec §37, §22). Values are deterministic (seeded from the address)
so the same demo address always returns the same demo report — useful for
screenshots, tests, and reproducible sales demos.
"""
import hashlib
from datetime import datetime, timedelta, timezone

from app.providers.base import (
    BlockchainProvider,
    Confidence,
    ContractMetadata,
    HolderRecord,
    NFTHolding,
    ProviderMeta,
    Transaction,
    TransactionDirection,
    TokenBalance,
    WalletBalance,
)


def _seed(address: str) -> int:
    return int(hashlib.sha256(address.lower().encode()).hexdigest(), 16)


def _synthetic_meta() -> ProviderMeta:
    return ProviderMeta(source="demo", confidence=Confidence.SYNTHETIC)


class DemoProvider(BlockchainProvider):
    async def get_wallet_balance(self, address: str) -> WalletBalance:
        seed = _seed(address)
        eth = (seed % 5_000_000) / 100_000  # 0 - 50 ETH, deterministic
        return WalletBalance(
            address=address,
            native_balance_wei=str(int(eth * 10**18)),
            native_balance_native_unit=round(eth, 4),
            meta=_synthetic_meta(),
        )

    async def get_transactions(
        self, address: str, page: int = 1, offset: int = 100, sort: str = "desc"
    ) -> list[Transaction]:
        seed = _seed(address)
        count = min(offset, 5 + (seed % 20))
        now = datetime.now(timezone.utc)
        txs = []
        for i in range(count):
            direction = TransactionDirection.OUT if i % 2 == 0 else TransactionDirection.IN
            txs.append(
                Transaction(
                    hash=f"0xdemo{seed % 10**12:012x}{i:04d}",
                    block_number=18_000_000 + i,
                    timestamp=now - timedelta(days=i * 3),
                    from_address=address if direction == TransactionDirection.OUT else "0xdemo0000000000000000000000000000000000",
                    to_address="0xdemo0000000000000000000000000000000000" if direction == TransactionDirection.OUT else address,
                    value_wei=str((seed + i) % 10**18),
                    direction=direction,
                    is_error=False,
                    method="transfer" if i % 3 == 0 else None,
                    meta=_synthetic_meta(),
                )
            )
        return txs

    async def get_token_balances(self, address: str) -> list[TokenBalance]:
        seed = _seed(address)
        sample_tokens = [("USDC", 6), ("DEMO", 18), ("SAMPLE", 18)]
        balances = []
        for i, (symbol, decimals) in enumerate(sample_tokens):
            if (seed >> i) % 3 == 0:
                continue  # not every demo wallet holds every demo token
            raw = (seed % 10_000) * 10**decimals
            balances.append(
                TokenBalance(
                    contract_address=f"0xdemo{'0' * 30}{i:04d}",
                    symbol=symbol,
                    name=f"{symbol} (Demo Token)",
                    decimals=decimals,
                    balance_raw=str(raw),
                    balance_normalized=raw / (10**decimals),
                    meta=_synthetic_meta(),
                )
            )
        return balances

    async def get_nfts(self, address: str) -> list[NFTHolding]:
        seed = _seed(address)
        count = seed % 4
        return [
            NFTHolding(
                collection_address="0xdemoNFTCollection0000000000000000000001",
                token_id=str(1000 + i),
                meta=_synthetic_meta(),
            )
            for i in range(count)
        ]

    async def get_collection_holders(self, contract_address: str) -> list[HolderRecord]:
        seed = _seed(contract_address)
        holder_count = 5 + (seed % 15)
        return [
            HolderRecord(
                address=f"0xdemoHolder{'0' * 27}{i:04d}",
                quantity=1 + (seed + i) % 5,
                meta=_synthetic_meta(),
            )
            for i in range(holder_count)
        ]

    async def get_contract_metadata(self, contract_address: str) -> ContractMetadata:
        return ContractMetadata(
            address=contract_address,
            name="Demo Contract",
            is_verified=True,
            meta=_synthetic_meta(),
        )
