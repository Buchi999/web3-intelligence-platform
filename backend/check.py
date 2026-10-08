import asyncio
from app.core.config import get_settings
from app.providers.etherscan_provider import EtherscanProvider


async def main():
    settings = get_settings()
    if not settings.ETHERSCAN_API_KEY:
        print("ETHERSCAN_API_KEY is not set in .env — check step 3 from before.")
        return

    provider = EtherscanProvider(api_key=settings.ETHERSCAN_API_KEY, chain_id=settings.CHAIN_ID)
    result = await provider.get_wallet_balance("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe")
    print(result.model_dump_json(indent=2))
    await provider.aclose()


asyncio.run(main())