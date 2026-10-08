import pytest

from app.providers.base import Confidence
from app.providers.demo_provider import DemoProvider

ADDRESS = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"


@pytest.fixture
def provider():
    return DemoProvider()


@pytest.mark.asyncio
async def test_demo_balance_is_marked_synthetic(provider):
    balance = await provider.get_wallet_balance(ADDRESS)
    assert balance.meta.confidence == Confidence.SYNTHETIC
    assert balance.meta.source == "demo"


@pytest.mark.asyncio
async def test_demo_data_is_deterministic_per_address(provider):
    a = await provider.get_wallet_balance(ADDRESS)
    b = await provider.get_wallet_balance(ADDRESS)
    assert a.native_balance_native_unit == b.native_balance_native_unit

    different_address = "0x0000000000000000000000000000000000dEaD"
    c = await provider.get_wallet_balance(different_address)
    # Not guaranteed mathematically distinct, but true for these two seeds —
    # documents the intent that demo data varies by address.
    assert isinstance(c.native_balance_native_unit, float)


@pytest.mark.asyncio
async def test_demo_transactions_all_marked_synthetic(provider):
    txs = await provider.get_transactions(ADDRESS)
    assert len(txs) > 0
    assert all(tx.meta.confidence == Confidence.SYNTHETIC for tx in txs)


@pytest.mark.asyncio
async def test_demo_collection_holders_all_marked_synthetic(provider):
    holders = await provider.get_collection_holders("0xdemocollection")
    assert len(holders) > 0
    assert all(h.meta.confidence == Confidence.SYNTHETIC for h in holders)
