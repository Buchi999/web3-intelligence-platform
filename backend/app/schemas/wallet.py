"""
API response schemas for wallet endpoints.

Kept separate from app.providers.base models: the provider layer represents
what a chain data source returns, the API layer represents a stable public
contract the frontend builds against.
"""
from datetime import datetime

from pydantic import BaseModel

from app.providers.base import Confidence


class ProviderMetaResponse(BaseModel):
    source: str
    retrieved_at: datetime
    confidence: Confidence
    block_number: int | None = None


class WalletOverviewResponse(BaseModel):
    address: str
    native_balance_wei: str
    native_balance_native_unit: float
    meta: ProviderMetaResponse