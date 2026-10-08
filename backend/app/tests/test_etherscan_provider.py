import re

import httpx
import pytest
import respx

from app.core.exceptions import DataUnavailableError, ProviderCapabilityError, ProviderRateLimitError
from app.providers.base import Confidence, TransactionDirection
from app.providers.etherscan_provider import BASE_URL, EtherscanProvider

ADDRESS = "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"

# httpx's AsyncClient(base_url=...) normalizes GET("", ...) to BASE_URL + "/",
# so match on that pattern rather than the exact BASE_URL string.
MOCK_URL = re.compile(rf"^{re.escape(BASE_URL)}/?(\?.*)?$")


def mock_get(**kwargs):
    return respx.get(url__regex=MOCK_URL, **kwargs)


@pytest.fixture
def provider():
    p = EtherscanProvider(api_key="test-key", chain_id=1)
    yield p


@pytest.mark.asyncio
@respx.mock
async def test_get_wallet_balance_parses_wei_to_eth(provider):
    mock_get().mock(
        return_value=httpx.Response(200, json={"status": "1", "message": "OK", "result": "1500000000000000000"})
    )
    balance = await provider.get_wallet_balance(ADDRESS)
    assert balance.native_balance_wei == "1500000000000000000"
    assert balance.native_balance_native_unit == 1.5
    assert balance.meta.source == "etherscan"
    assert balance.meta.confidence == Confidence.REAL


@pytest.mark.asyncio
@respx.mock
async def test_get_wallet_balance_zero_balance_not_an_error(provider):
    # A wallet with a zero balance still returns status "1" from Etherscan.
    mock_get().mock(
        return_value=httpx.Response(200, json={"status": "1", "message": "OK", "result": "0"})
    )
    balance = await provider.get_wallet_balance(ADDRESS)
    assert balance.native_balance_native_unit == 0.0


@pytest.mark.asyncio
@respx.mock
async def test_get_transactions_direction_classification(provider):
    mock_get().mock(
        return_value=httpx.Response(
            200,
            json={
                "status": "1",
                "message": "OK",
                "result": [
                    {
                        "hash": "0xabc",
                        "blockNumber": "100",
                        "timeStamp": "1700000000",
                        "from": ADDRESS.lower(),
                        "to": "0x0000000000000000000000000000000000dead",
                        "value": "1000000000000000000",
                        "isError": "0",
                        "functionName": "transfer(address,uint256)",
                    },
                    {
                        "hash": "0xdef",
                        "blockNumber": "101",
                        "timeStamp": "1700000100",
                        "from": "0x0000000000000000000000000000000000dead",
                        "to": ADDRESS.lower(),
                        "value": "2000000000000000000",
                        "isError": "0",
                        "functionName": "",
                    },
                ],
            },
        )
    )
    txs = await provider.get_transactions(ADDRESS)
    assert len(txs) == 2
    assert txs[0].direction == TransactionDirection.OUT
    assert txs[1].direction == TransactionDirection.IN


@pytest.mark.asyncio
@respx.mock
async def test_empty_transaction_history_is_not_an_error(provider):
    # Etherscan returns status "0" with message "No transactions found" for
    # a fresh wallet — this must NOT be treated as a provider error.
    mock_get().mock(
        return_value=httpx.Response(
            200, json={"status": "0", "message": "No transactions found", "result": []}
        )
    )
    txs = await provider.get_transactions(ADDRESS)
    assert txs == []


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_message_raises_provider_rate_limit_error(provider):
    mock_get().mock(
        return_value=httpx.Response(
            200, json={"status": "0", "message": "NOTOK", "result": "Max rate limit reached"}
        )
    )
    with pytest.raises(ProviderRateLimitError):
        await provider.get_wallet_balance(ADDRESS)


@pytest.mark.asyncio
@respx.mock
async def test_http_429_raises_provider_rate_limit_error(provider):
    mock_get().mock(return_value=httpx.Response(429))
    with pytest.raises(ProviderRateLimitError):
        await provider.get_wallet_balance(ADDRESS)


@pytest.mark.asyncio
@respx.mock
async def test_network_failure_raises_data_unavailable_error(provider):
    mock_get().mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(DataUnavailableError):
        await provider.get_wallet_balance(ADDRESS)


@pytest.mark.asyncio
@respx.mock
async def test_get_token_balances_derives_from_transfer_history(provider):
    tokentx_response = httpx.Response(
        200,
        json={
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "contractAddress": "0xtoken1",
                    "tokenSymbol": "TK1",
                    "tokenName": "Token One",
                    "tokenDecimal": "18",
                }
            ],
        },
    )
    tokenbalance_response = httpx.Response(
        200, json={"status": "1", "message": "OK", "result": "5000000000000000000"}
    )

    route = mock_get()
    route.side_effect = [tokentx_response, tokenbalance_response]

    balances = await provider.get_token_balances(ADDRESS)
    assert len(balances) == 1
    assert balances[0].symbol == "TK1"
    assert balances[0].balance_normalized == 5.0
    assert balances[0].meta.confidence == Confidence.ESTIMATED


@pytest.mark.asyncio
async def test_get_collection_holders_raises_capability_error(provider):
    # Free-tier Etherscan has no holder-list endpoint — must fail loudly,
    # never fabricate a holder list.
    with pytest.raises(ProviderCapabilityError):
        await provider.get_collection_holders("0xsomecollection")
