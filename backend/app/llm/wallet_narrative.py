"""
AI narrative generation for wallet reports. The LLM only ever receives the
structured summary built below — never raw transaction lists.
"""
import json

from app.analysis.behavior import BehaviorClassification
from app.analysis.nfts import NFTPortfolioAnalysis
from app.analysis.risk import RiskAssessment
from app.analysis.tokens import TokenPortfolioAnalysis
from app.analysis.transactions import TransactionAnalysis
from app.llm.base import LLMProvider
from app.providers.base import WalletBalance

SYSTEM_PROMPT = """You are a blockchain intelligence analyst writing a section of a wallet \
intelligence report. You will be given ONLY structured, pre-computed data — you must never \
invent, assume, or infer any numeric fact that is not present in that data.

Never state anything as definitive proof of identity, fraud, or criminal activity. Use \
hedged, professional language such as "exhibits patterns associated with" or "may indicate" \
rather than asserting conclusions as fact.

Write the following NINE sections, each with a short heading, in this order:
Executive Summary, Wallet Behavior, Portfolio Analysis, NFT Analysis, Transaction Behavior, \
Risk Indicators, Notable Patterns, Data Limitations, Recommended Further Investigation.

You MUST include all nine sections in your response — do not spend so much length on early \
sections that you run out of room for later ones. Keep each section to 2-4 short sentences or \
bullet points. If a section has nothing notable to report from the given data, write "No \
notable findings." for that section rather than fabricating content or skipping it. Do not \
restate the raw input verbatim — synthesize it into readable analysis. Keep the entire \
response under 400 words total, prioritizing covering all nine sections over writing at length \
about any single one."""


def _build_user_prompt(
    address: str,
    balance: WalletBalance,
    transactions: TransactionAnalysis,
    tokens: TokenPortfolioAnalysis,
    nfts: NFTPortfolioAnalysis,
    classifications: list[BehaviorClassification],
    risk: RiskAssessment,
    wallet_age_days: int | None,
) -> str:
    data = {
        "wallet_address": address,
        "wallet_age_days": wallet_age_days,
        "native_balance_eth": balance.native_balance_native_unit,
        "balance_confidence": balance.meta.confidence.value,
        "transactions": {
            "total_retrieved": transactions.total_transactions,
            "incoming": transactions.incoming_count,
            "outgoing": transactions.outgoing_count,
            "active_days": transactions.active_days,
            "avg_transactions_per_day": transactions.average_transactions_per_day,
            "avg_transaction_value_eth": transactions.average_transaction_value_native,
            "dormant_periods_count": len(transactions.dormant_periods),
            "data_note": transactions.data_note,
        },
        "token_portfolio": {
            "distinct_tokens": len(tokens.holdings),
            "concentration_method": tokens.concentration_method.value,
            "top_asset_pct": tokens.top_asset_pct,
            "total_value_usd": tokens.total_value_usd,
            "top_holdings": [
                {"symbol": h.symbol, "pct_of_portfolio": h.pct_of_portfolio} for h in tokens.holdings[:5]
            ],
            "data_note": tokens.data_note,
        },
        "nft_holdings": {
            "total_count": nfts.total_nft_count,
            "distinct_collections": nfts.distinct_collections_count,
            "top_collection_pct": nfts.top_collection_pct,
            "data_note": nfts.data_note,
        },
        "behavior_classifications": [
            {"label": c.label, "confidence": c.confidence, "factors": c.factors} for c in classifications
        ],
        "risk_assessment": {
            "score": risk.score,
            "factors": [{"description": f.description, "points": f.points} for f in risk.factors],
        },
    }
    return (
        "Here is the structured wallet data. Write the report sections described in your "
        "instructions, using only these numbers:\n\n" + json.dumps(data, indent=2, default=str)
    )


async def generate_wallet_narrative(
    address: str,
    balance: WalletBalance,
    transactions: TransactionAnalysis,
    tokens: TokenPortfolioAnalysis,
    nfts: NFTPortfolioAnalysis,
    classifications: list[BehaviorClassification],
    risk: RiskAssessment,
    wallet_age_days: int | None,
    llm_provider: LLMProvider,
) -> str | None:
    user_prompt = _build_user_prompt(
        address, balance, transactions, tokens, nfts, classifications, risk, wallet_age_days
    )
    return await llm_provider.generate(SYSTEM_PROMPT, user_prompt)