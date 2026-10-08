"""
Report data orchestration. Assembles Phases 4-8 outputs into one structure
a PDF renderer can consume. No new blockchain/analysis logic lives here.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.analysis.behavior import BehaviorClassification, classify_wallet_behavior
from app.analysis.holders import CollectionHolderAnalysis, analyze_collection_holders
from app.analysis.nfts import NFTPortfolioAnalysis, analyze_nft_holdings
from app.analysis.risk import RiskAssessment, assess_wallet_risk
from app.analysis.tokens import TokenPortfolioAnalysis, analyze_token_portfolio
from app.analysis.transactions import TransactionAnalysis, analyze_transactions
from app.core.address import validate_ethereum_address
from app.llm.base import LLMProvider
from app.llm.wallet_narrative import generate_wallet_narrative
from app.providers.base import BlockchainProvider, ContractMetadata, WalletBalance
from app.providers.holder_provider import HolderProvider
from app.providers.price_provider import PriceProvider


@dataclass
class WalletReportData:
    address: str
    generated_at: datetime
    balance: WalletBalance
    transactions: TransactionAnalysis
    tokens: TokenPortfolioAnalysis
    nfts: NFTPortfolioAnalysis
    wallet_age_days: int | None = None
    classifications: list[BehaviorClassification] = field(default_factory=list)
    risk: RiskAssessment | None = None
    ai_narrative: str | None = None
    data_sources: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


@dataclass
class CollectionReportData:
    address: str
    generated_at: datetime
    metadata: ContractMetadata
    holders: CollectionHolderAnalysis
    data_sources: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


STANDARD_LIMITATIONS = [
    "Wallet ownership is not necessarily known — one person may control multiple wallets, "
    "or multiple people may share one wallet.",
    "Token and NFT prices can be volatile; USD figures reflect a single point in time.",
    "Heuristic and derived metrics (e.g. token holdings from transfer history) can differ "
    "slightly from a live on-chain read and are labeled ESTIMATED where this applies.",
    "This report reflects data available at generation time and does not update automatically.",
]


async def build_wallet_report(
    address: str,
    blockchain_provider: BlockchainProvider,
    price_provider: PriceProvider,
    llm_provider: LLMProvider,
) -> WalletReportData:
    checksummed = validate_ethereum_address(address)

    balance = await blockchain_provider.get_wallet_balance(checksummed)
    transactions_raw = await blockchain_provider.get_transactions(checksummed, offset=200, sort="desc")
    tx_analysis = analyze_transactions(transactions_raw)

    token_balances = await blockchain_provider.get_token_balances(checksummed)
    prices = await price_provider.get_usd_prices([t.contract_address for t in token_balances])
    token_analysis = analyze_token_portfolio(token_balances, prices)

    nft_holdings = await blockchain_provider.get_nfts(checksummed)
    nft_analysis = analyze_nft_holdings(nft_holdings)

    earliest_txs = await blockchain_provider.get_transactions(checksummed, offset=1, sort="asc")
    wallet_age_days = None
    if earliest_txs:
        wallet_age_days = (datetime.now(timezone.utc) - earliest_txs[0].timestamp).days

    classifications = classify_wallet_behavior(
        balance, tx_analysis, token_analysis, nft_analysis, wallet_age_days
    )
    risk = assess_wallet_risk(balance, tx_analysis, token_analysis, nft_analysis, wallet_age_days)

    ai_narrative = await generate_wallet_narrative(
        checksummed,
        balance,
        tx_analysis,
        token_analysis,
        nft_analysis,
        classifications,
        risk,
        wallet_age_days,
        llm_provider,
    )

    data_sources = [f"Blockchain data: {balance.meta.source}"]
    if any(v is not None for v in prices.values()):
        data_sources.append("Token pricing: CoinGecko")
    if ai_narrative:
        data_sources.append("AI narrative: Groq")

    limitations = list(STANDARD_LIMITATIONS)
    for note in (tx_analysis.data_note, token_analysis.data_note, nft_analysis.data_note):
        if note:
            limitations.append(note)

    return WalletReportData(
        address=checksummed,
        generated_at=datetime.now(timezone.utc),
        balance=balance,
        transactions=tx_analysis,
        tokens=token_analysis,
        nfts=nft_analysis,
        wallet_age_days=wallet_age_days,
        classifications=classifications,
        risk=risk,
        ai_narrative=ai_narrative,
        data_sources=data_sources,
        limitations=limitations,
    )


async def build_collection_report(
    address: str,
    blockchain_provider: BlockchainProvider,
    holder_provider: HolderProvider,
) -> CollectionReportData:
    checksummed = validate_ethereum_address(address)

    metadata = await blockchain_provider.get_contract_metadata(checksummed)
    holders_raw = await holder_provider.get_owners(checksummed)
    holder_analysis = analyze_collection_holders(holders_raw)

    data_sources = [f"Contract metadata: {metadata.meta.source}", "Holder data: Alchemy NFT API"]

    limitations = list(STANDARD_LIMITATIONS)
    if holder_analysis.data_note:
        limitations.append(holder_analysis.data_note)

    return CollectionReportData(
        address=checksummed,
        generated_at=datetime.now(timezone.utc),
        metadata=metadata,
        holders=holder_analysis,
        data_sources=data_sources,
        limitations=limitations,
    )