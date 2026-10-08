"""
EtherscanProvider — Ethereum mainnet via Etherscan API V2.

Verified against current docs (docs.etherscan.io) as of this implementation:
- Base URL is https://api.etherscan.io/v2/api (the old per-chain subdomains
  are deprecated). A `chainid` query param selects the chain; 1 = Ethereum.
- Every request needs `apikey`.
- Free tier caps results at 1,000 records per request (reduced from 10,000
  effective July 2026) — pagination params (page/offset) are used to work
  within that.

Known free-tier limitations (do not paper over these — surface them):
- There is no endpoint that lists "all current token balances" for a wallet.
  We approximate this by scanning ERC-20 transfer history (`tokentx`) for
  contracts the wallet has touched, then querying the current balance for
  each one. This is an approximation, not a ledger — mark it ESTIMATED.
- There is no free-tier "list holders of a collection" endpoint. That needs
  Etherscan API Pro or a specialized indexer (Alchemy NFT API, Reservoir).
  get_collection_holders raises ProviderCapabilityError rather than
  fabricating a holder list.
"""
from datetime import datetime, timezone

import httpx

from app.core.exceptions import DataUnavailableError, ProviderCapabilityError, ProviderRateLimitError
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

BASE_URL = "https://api.etherscan.io/v2/api"

# How many distinct ERC-20 contracts we'll query current balances for per
# wallet lookup. Keeps a single "analyze this wallet" request from fanning
# out into dozens of API calls against a rate-limited free-tier key.
MAX_TOKEN_CONTRACTS_PER_WALLET = 25


class EtherscanProvider(BlockchainProvider):
    def __init__(self, api_key: str, chain_id: int = 1, timeout: float = 15.0):
        self._api_key = api_key
        self._chain_id = chain_id
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()

    # -- internal helpers -------------------------------------------------

    async def _get(self, params: dict) -> dict:
        request_params = {
            "chainid": self._chain_id,
            "apikey": self._api_key,
            **params,
        }
        try:
            response = await self._client.get("", params=request_params)
        except httpx.RequestError as exc:
            raise DataUnavailableError(f"Could not reach Etherscan API: {exc}") from exc

        if response.status_code == 429:
            raise ProviderRateLimitError("Etherscan API rate limit reached. Try again shortly.")

        body = response.json()
        message = body.get("message", "")
        result = body.get("result")

        # Etherscan uses status "0" both for real errors and for "no records
        # found" (e.g. a fresh wallet with zero transactions). We only treat
        # it as an error if the message or result text says so. Note: rate
        # limit text can appear in either field ("NOTOK"/"Max rate limit
        # reached" or "OK-Missing/Invalid API Key, rate limit..."), so both
        # must be checked — checking `message` alone misses real cases.
        if body.get("status") == "0" and isinstance(result, str):
            combined = f"{message} {result}".lower()
            if "rate limit" in combined or "max calls" in combined:
                raise ProviderRateLimitError(f"Etherscan API rate limit: {message} — {result}")
            if message.lower() not in ("no transactions found", "no records found", "ok"):
                raise DataUnavailableError(f"Etherscan API error: {message} — {result}")

        return body

    @staticmethod
    def _meta(block_number: int | None = None) -> ProviderMeta:
        return ProviderMeta(
            source="etherscan",
            retrieved_at=datetime.now(timezone.utc),
            confidence=Confidence.REAL,
            block_number=block_number,
        )

    # -- BlockchainProvider interface --------------------------------------

    async def get_wallet_balance(self, address: str) -> WalletBalance:
        body = await self._get({"module": "account", "action": "balance", "address": address, "tag": "latest"})
        wei = body.get("result", "0")
        try:
            eth_value = int(wei) / 10**18
        except (TypeError, ValueError):
            eth_value = 0.0
        return WalletBalance(
            address=address,
            native_balance_wei=str(wei),
            native_balance_native_unit=eth_value,
            meta=self._meta(),
        )

    async def get_transactions(
        self, address: str, page: int = 1, offset: int = 100, sort: str = "desc"
    ) -> list[Transaction]:
        body = await self._get(
            {
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999999,
                "page": page,
                "offset": offset,
                "sort": sort,
            }
        )
        result = body.get("result", [])
        if not isinstance(result, list):
            return []

        address_lower = address.lower()
        transactions = []
        for tx in result:
            from_addr = (tx.get("from") or "").lower()
            to_addr = (tx.get("to") or "").lower()
            if from_addr == address_lower and to_addr == address_lower:
                direction = TransactionDirection.SELF
            elif from_addr == address_lower:
                direction = TransactionDirection.OUT
            else:
                direction = TransactionDirection.IN

            transactions.append(
                Transaction(
                    hash=tx["hash"],
                    block_number=int(tx["blockNumber"]),
                    timestamp=datetime.fromtimestamp(int(tx["timeStamp"]), tz=timezone.utc),
                    from_address=tx.get("from", ""),
                    to_address=tx.get("to") or None,
                    value_wei=str(tx.get("value", "0")),
                    direction=direction,
                    is_error=tx.get("isError") == "1",
                    method=tx.get("functionName") or None,
                    meta=self._meta(block_number=int(tx["blockNumber"])),
                )
            )
        return transactions

    async def get_token_balances(self, address: str) -> list[TokenBalance]:
        # Step 1: find contracts this wallet has touched via ERC-20 transfer history.
        body = await self._get(
            {
                "module": "account",
                "action": "tokentx",
                "address": address,
                "page": 1,
                "offset": 1000,
                "sort": "desc",
            }
        )
        transfers = body.get("result", [])
        if not isinstance(transfers, list):
            transfers = []

        seen: dict[str, dict] = {}
        for t in transfers:
            contract = (t.get("contractAddress") or "").lower()
            if contract and contract not in seen:
                seen[contract] = t
            if len(seen) >= MAX_TOKEN_CONTRACTS_PER_WALLET:
                break

        # Step 2: query the current balance for each contract touched.
        # This is an approximation (ESTIMATED): a wallet could hold a token
        # it never received via a standard Transfer event (rare), and if it
        # has touched more than MAX_TOKEN_CONTRACTS_PER_WALLET contracts we
        # silently cap the list rather than hammering the rate limit.
        balances: list[TokenBalance] = []
        for contract, sample_tx in seen.items():
            bal_body = await self._get(
                {
                    "module": "account",
                    "action": "tokenbalance",
                    "address": address,
                    "contractaddress": contract,
                    "tag": "latest",
                }
            )
            raw_balance = bal_body.get("result", "0")
            if not raw_balance or raw_balance == "0":
                continue

            decimals = sample_tx.get("tokenDecimal")
            try:
                decimals_int = int(decimals) if decimals is not None else None
                normalized = int(raw_balance) / (10**decimals_int) if decimals_int is not None else None
            except (TypeError, ValueError):
                decimals_int, normalized = None, None

            balances.append(
                TokenBalance(
                    contract_address=contract,
                    symbol=sample_tx.get("tokenSymbol"),
                    name=sample_tx.get("tokenName"),
                    decimals=decimals_int,
                    balance_raw=str(raw_balance),
                    balance_normalized=normalized,
                    meta=ProviderMeta(
                        source="etherscan",
                        confidence=Confidence.ESTIMATED,
                    ),
                )
            )
        return balances

    async def get_nfts(self, address: str) -> list[NFTHolding]:
        body = await self._get(
            {
                "module": "account",
                "action": "tokennfttx",
                "address": address,
                "page": 1,
                "offset": 1000,
                "sort": "asc",
            }
        )
        transfers = body.get("result", [])
        if not isinstance(transfers, list):
            transfers = []

        address_lower = address.lower()
        # Walk transfer history chronologically; last event per (contract, tokenId)
        # tells us who currently holds it.
        current_owner: dict[tuple[str, str], str] = {}
        for t in transfers:
            key = (t.get("contractAddress", "").lower(), t.get("tokenID", ""))
            current_owner[key] = (t.get("to") or "").lower()

        holdings = [
            NFTHolding(
                collection_address=contract,
                token_id=token_id,
                meta=ProviderMeta(source="etherscan", confidence=Confidence.ESTIMATED),
            )
            for (contract, token_id), owner in current_owner.items()
            if owner == address_lower
        ]
        return holdings

    async def get_collection_holders(self, contract_address: str) -> list[HolderRecord]:
        raise ProviderCapabilityError(
            "Etherscan's free API tier has no endpoint for listing all holders of a "
            "collection. This requires Etherscan API Pro or a specialized NFT indexer "
            "(e.g. Alchemy NFT API, Reservoir) — see architecture doc §7 and roadmap Phase 8."
        )

    async def get_contract_metadata(self, contract_address: str) -> ContractMetadata:
        body = await self._get(
            {"module": "contract", "action": "getsourcecode", "address": contract_address}
        )
        result = body.get("result", [])
        if not result or not isinstance(result, list):
            raise DataUnavailableError(f"No contract metadata found for {contract_address}")

        info = result[0]
        contract_name = info.get("ContractName") or None
        is_verified = bool(contract_name) and info.get("SourceCode") not in (None, "")

        return ContractMetadata(
            address=contract_address,
            name=contract_name,
            is_verified=is_verified,
            meta=self._meta(),
        )
