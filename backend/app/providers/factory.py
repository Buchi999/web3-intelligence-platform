"""
Provider factory.

This is the *only* place in the application allowed to decide which
concrete BlockchainProvider to use. Routers and analysis code depend on
BlockchainProvider (the abstract type) and get an instance via
get_blockchain_provider() — a FastAPI dependency — so they never know or
care whether they're talking to Etherscan or the demo provider.
"""
from functools import lru_cache

from app.core.config import get_settings
from app.providers.base import BlockchainProvider
from app.providers.demo_provider import DemoProvider
from app.providers.etherscan_provider import EtherscanProvider


@lru_cache
def _get_etherscan_provider() -> EtherscanProvider:
    settings = get_settings()
    assert settings.ETHERSCAN_API_KEY, "ETHERSCAN_API_KEY must be set to build EtherscanProvider"
    return EtherscanProvider(api_key=settings.ETHERSCAN_API_KEY, chain_id=settings.CHAIN_ID)


@lru_cache
def _get_demo_provider() -> DemoProvider:
    return DemoProvider()


def get_blockchain_provider() -> BlockchainProvider:
    """FastAPI dependency: `provider: BlockchainProvider = Depends(get_blockchain_provider)`."""
    settings = get_settings()
    if settings.DEMO_MODE:
        return _get_demo_provider()
    return _get_etherscan_provider()
