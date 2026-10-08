import asyncio
from app.providers.factory import get_blockchain_provider


async def main():
    provider = get_blockchain_provider()
    print(f"Using provider: {type(provider).__name__}")
    result = await provider.get_wallet_balance("0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe")
    print(result.model_dump_json(indent=2))


asyncio.run(main())