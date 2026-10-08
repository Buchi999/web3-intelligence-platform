"""
API response schemas for the token portfolio endpoint.
"""
from pydantic import BaseModel

from app.analysis.tokens import ConcentrationMethod


class TokenHoldingResponse(BaseModel):
    contract_address: str
    symbol: str | None
    name: str | None
    balance_normalized: float | None
    usd_value: float | None
    pct_of_portfolio: float | None


class TokensResponse(BaseModel):
    address: str
    holdings: list[TokenHoldingResponse]
    total_value_usd: float | None
    concentration_method: ConcentrationMethod
    top_asset_pct: float | None
    data_note: str | None