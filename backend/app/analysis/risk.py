"""
Risk Indicator Engine. Transparent, additive, 0-100 score. Never accusatory
— flags patterns worth investigation, not a fraud determination.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.analysis.nfts import NFTPortfolioAnalysis
from app.analysis.tokens import TokenPortfolioAnalysis
from app.analysis.transactions import TransactionAnalysis
from app.providers.base import WalletBalance

DISCLAIMER = (
    "No direct evidence of malicious activity was established. This score reflects "
    "heuristic patterns only and should not be treated as a fraud determination."
)


@dataclass
class RiskFactor:
    description: str
    points: int


@dataclass
class RiskAssessment:
    score: int
    factors: list[RiskFactor] = field(default_factory=list)
    disclaimer: str = DISCLAIMER


def _days_ago(dt: datetime | None) -> int | None:
    if dt is None:
        return None
    now = datetime.now(dt.tzinfo or timezone.utc)
    return (now - dt).days


def assess_wallet_risk(
    balance: WalletBalance,
    transactions: TransactionAnalysis,
    tokens: TokenPortfolioAnalysis,
    nfts: NFTPortfolioAnalysis,
    wallet_age_days: int | None,
) -> RiskAssessment:
    factors: list[RiskFactor] = []

    if wallet_age_days is not None:
        if wallet_age_days <= 7:
            factors.append(RiskFactor("Very new wallet (first activity within the last week)", 20))
        elif wallet_age_days <= 30:
            factors.append(RiskFactor("Relatively new wallet (first activity within the last month)", 10))

    if tokens.top_asset_pct is not None:
        if tokens.top_asset_pct >= 90:
            factors.append(RiskFactor(f"Extreme portfolio concentration ({tokens.top_asset_pct:.1f}% in one asset)", 20))
        elif tokens.top_asset_pct >= 70:
            factors.append(RiskFactor(f"High portfolio concentration ({tokens.top_asset_pct:.1f}% in one asset)", 10))

    if nfts.top_collection_pct is not None and nfts.top_collection_pct >= 90:
        factors.append(
            RiskFactor(f"Extreme NFT concentration in a single collection ({nfts.top_collection_pct:.1f}%)", 10)
        )

    tx_per_day = transactions.average_transactions_per_day
    if tx_per_day is not None:
        if tx_per_day >= 20:
            factors.append(RiskFactor(f"Very high transaction frequency ({tx_per_day:.2f}/day)", 20))
        elif tx_per_day >= 5:
            factors.append(RiskFactor(f"High transaction frequency ({tx_per_day:.2f}/day)", 10))

    days_since_last = _days_ago(transactions.last_transaction_at)
    if transactions.dormant_periods and days_since_last is not None and days_since_last <= 7:
        factors.append(
            RiskFactor(
                f"Wallet reactivated after {len(transactions.dormant_periods)} dormant period(s), "
                "with renewed activity in the last week",
                10,
            )
        )

    score = min(100, sum(f.points for f in factors))
    return RiskAssessment(score=score, factors=factors)