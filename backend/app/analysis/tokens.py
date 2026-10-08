"""
Token portfolio analysis. Value-based concentration when prices are known,
balance-proportion fallback when they aren't — always labeled, never mixed.
"""
from dataclasses import dataclass, field
from enum import Enum

from app.providers.base import TokenBalance


class ConcentrationMethod(str, Enum):
    USD_VALUE = "usd_value"
    BALANCE_PROPORTION = "balance_proportion"
    NOT_APPLICABLE = "not_applicable"


@dataclass
class TokenHolding:
    contract_address: str
    symbol: str | None
    name: str | None
    balance_normalized: float | None
    usd_value: float | None
    pct_of_portfolio: float | None


@dataclass
class TokenPortfolioAnalysis:
    holdings: list[TokenHolding] = field(default_factory=list)
    total_value_usd: float | None = None
    concentration_method: ConcentrationMethod = ConcentrationMethod.NOT_APPLICABLE
    top_asset_pct: float | None = None
    data_note: str | None = None


def analyze_token_portfolio(
    balances: list[TokenBalance], prices_usd: dict[str, float | None]
) -> TokenPortfolioAnalysis:
    if not balances:
        return TokenPortfolioAnalysis(
            holdings=[],
            data_note="No ERC-20 token holdings found for this address.",
        )

    any_price_known = any(prices_usd.get(b.contract_address.lower()) is not None for b in balances)

    holdings: list[TokenHolding] = []
    if any_price_known:
        priced_values = {
            b.contract_address.lower(): (
                b.balance_normalized * prices_usd[b.contract_address.lower()]
                if b.balance_normalized is not None
                and prices_usd.get(b.contract_address.lower()) is not None
                else None
            )
            for b in balances
        }
        total_known_value = sum(v for v in priced_values.values() if v is not None)

        for b in balances:
            key = b.contract_address.lower()
            usd_value = priced_values.get(key)
            pct = (
                (usd_value / total_known_value * 100)
                if usd_value is not None and total_known_value > 0
                else None
            )
            holdings.append(
                TokenHolding(
                    contract_address=b.contract_address,
                    symbol=b.symbol,
                    name=b.name,
                    balance_normalized=b.balance_normalized,
                    usd_value=usd_value,
                    pct_of_portfolio=pct,
                )
            )

        holdings.sort(key=lambda h: h.usd_value or -1, reverse=True)
        top_pct = holdings[0].pct_of_portfolio if holdings and holdings[0].pct_of_portfolio else None
        note = None
        unknown_count = sum(1 for h in holdings if h.usd_value is None)
        if unknown_count:
            note = (
                f"{unknown_count} of {len(holdings)} tokens have no known USD price and are "
                "excluded from the concentration calculation and total value."
            )

        return TokenPortfolioAnalysis(
            holdings=holdings,
            total_value_usd=total_known_value if total_known_value > 0 else None,
            concentration_method=ConcentrationMethod.USD_VALUE,
            top_asset_pct=top_pct,
            data_note=note,
        )

    total_balance = sum(b.balance_normalized or 0 for b in balances)
    for b in balances:
        pct = (b.balance_normalized / total_balance * 100) if total_balance > 0 and b.balance_normalized else None
        holdings.append(
            TokenHolding(
                contract_address=b.contract_address,
                symbol=b.symbol,
                name=b.name,
                balance_normalized=b.balance_normalized,
                usd_value=None,
                pct_of_portfolio=pct,
            )
        )
    holdings.sort(key=lambda h: h.pct_of_portfolio or -1, reverse=True)
    top_pct = holdings[0].pct_of_portfolio if holdings else None

    return TokenPortfolioAnalysis(
        holdings=holdings,
        total_value_usd=None,
        concentration_method=ConcentrationMethod.BALANCE_PROPORTION,
        top_asset_pct=top_pct,
        data_note=(
            "No USD pricing available (configure COINGECKO_API_KEY for value-based "
            "concentration). Percentages below are based on raw token balance "
            "proportion, not dollar value — a token with a large raw supply can "
            "dominate this metric even if it has little or no market value."
        ),
    )