"""
Wallet behavior classification. Heuristic, transparent — never definitive
claims. A wallet can match several classifications at once.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.analysis.nfts import NFTPortfolioAnalysis
from app.analysis.tokens import TokenPortfolioAnalysis
from app.analysis.transactions import TransactionAnalysis
from app.providers.base import WalletBalance

WHALE_ETH_THRESHOLD = 100.0
NFT_COLLECTOR_MIN_COUNT = 10
NFT_COLLECTOR_MIN_COLLECTIONS = 3
DIVERSIFIED_MIN_TOKENS = 5
CONCENTRATED_THRESHOLD_PCT = 80.0
NEW_WALLET_DAYS = 30
DORMANT_WALLET_DAYS = 90
HIGH_FREQUENCY_TX_PER_DAY = 5.0
VERY_HIGH_FREQUENCY_TX_PER_DAY = 20.0
LONG_TERM_HOLDER_MIN_AGE_DAYS = 365
LONG_TERM_HOLDER_MAX_TX_PER_DAY = 0.05
BOT_LIKE_MIN_TX_PER_DAY = 10.0
BOT_LIKE_MAX_AVG_VALUE_ETH = 0.001


@dataclass
class BehaviorClassification:
    label: str
    confidence: float
    factors: list[str] = field(default_factory=list)


def _days_ago(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    now = datetime.now(dt.tzinfo or timezone.utc)
    return (now - dt).days


def classify_wallet_behavior(
    balance: WalletBalance,
    transactions: TransactionAnalysis,
    tokens: TokenPortfolioAnalysis,
    nfts: NFTPortfolioAnalysis,
    wallet_age_days: int | None,
) -> list[BehaviorClassification]:
    results: list[BehaviorClassification] = []
    tx_per_day = transactions.average_transactions_per_day
    days_since_last = _days_ago(transactions.last_transaction_at)

    if balance.native_balance_native_unit >= WHALE_ETH_THRESHOLD:
        results.append(
            BehaviorClassification(
                label="Whale",
                confidence=min(95.0, 60.0 + (balance.native_balance_native_unit / WHALE_ETH_THRESHOLD) * 5),
                factors=[f"Holds {balance.native_balance_native_unit:,.2f} ETH (≥ {WHALE_ETH_THRESHOLD:.0f} ETH threshold)"],
            )
        )

    if wallet_age_days is not None and wallet_age_days <= NEW_WALLET_DAYS:
        results.append(
            BehaviorClassification(
                label="New Wallet",
                confidence=85.0 if wallet_age_days <= 7 else 65.0,
                factors=[f"First on-chain activity {wallet_age_days} day(s) ago"],
            )
        )

    if days_since_last is not None and days_since_last >= DORMANT_WALLET_DAYS:
        results.append(
            BehaviorClassification(
                label="Dormant Wallet",
                confidence=min(90.0, 50.0 + days_since_last / 10),
                factors=[f"No transactions in the last {days_since_last} day(s)"],
            )
        )

    if (
        wallet_age_days is not None
        and wallet_age_days >= LONG_TERM_HOLDER_MIN_AGE_DAYS
        and tx_per_day is not None
        and tx_per_day <= LONG_TERM_HOLDER_MAX_TX_PER_DAY
    ):
        results.append(
            BehaviorClassification(
                label="Long-Term Holder",
                confidence=70.0,
                factors=[
                    f"Wallet age: {wallet_age_days} day(s)",
                    f"Low transaction frequency: {tx_per_day:.3f}/day",
                ],
            )
        )

    if tx_per_day is not None:
        if tx_per_day >= VERY_HIGH_FREQUENCY_TX_PER_DAY:
            results.append(
                BehaviorClassification(
                    label="High-Frequency Trader",
                    confidence=80.0,
                    factors=[f"Average of {tx_per_day:.2f} transactions/day"],
                )
            )
        elif tx_per_day >= HIGH_FREQUENCY_TX_PER_DAY:
            results.append(
                BehaviorClassification(
                    label="Active Trader",
                    confidence=65.0,
                    factors=[f"Average of {tx_per_day:.2f} transactions/day"],
                )
            )

    if (
        tx_per_day is not None
        and tx_per_day >= BOT_LIKE_MIN_TX_PER_DAY
        and transactions.average_transaction_value_native is not None
        and transactions.average_transaction_value_native <= BOT_LIKE_MAX_AVG_VALUE_ETH
    ):
        results.append(
            BehaviorClassification(
                label="Potential Bot-Like Activity",
                confidence=55.0,
                factors=[
                    f"Very high transaction frequency ({tx_per_day:.2f}/day) combined with very low "
                    f"average transaction value ({transactions.average_transaction_value_native:.6f} ETH)",
                ],
            )
        )

    if nfts.total_nft_count >= NFT_COLLECTOR_MIN_COUNT and nfts.distinct_collections_count >= NFT_COLLECTOR_MIN_COLLECTIONS:
        results.append(
            BehaviorClassification(
                label="NFT Collector",
                confidence=min(90.0, 50.0 + nfts.distinct_collections_count),
                factors=[f"Holds {nfts.total_nft_count} NFTs across {nfts.distinct_collections_count} collections"],
            )
        )

    if len(tokens.holdings) >= DIVERSIFIED_MIN_TOKENS and (
        tokens.top_asset_pct is None or tokens.top_asset_pct < CONCENTRATED_THRESHOLD_PCT
    ):
        results.append(
            BehaviorClassification(
                label="Diversified Wallet",
                confidence=60.0,
                factors=[
                    f"Holds {len(tokens.holdings)} distinct tokens",
                    (
                        f"No single asset exceeds {CONCENTRATED_THRESHOLD_PCT:.0f}% of tracked portfolio"
                        if tokens.top_asset_pct is not None
                        else "Token concentration data unavailable"
                    ),
                ],
            )
        )

    if tokens.top_asset_pct is not None and tokens.top_asset_pct >= CONCENTRATED_THRESHOLD_PCT:
        results.append(
            BehaviorClassification(
                label="Highly Concentrated Wallet",
                confidence=min(90.0, 50.0 + (tokens.top_asset_pct - CONCENTRATED_THRESHOLD_PCT)),
                factors=[
                    f"Top asset represents {tokens.top_asset_pct:.2f}% of tracked "
                    f"{tokens.concentration_method.value.replace('_', ' ')} portfolio"
                ],
            )
        )

    results.sort(key=lambda c: c.confidence, reverse=True)
    return results