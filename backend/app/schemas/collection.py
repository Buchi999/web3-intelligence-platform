"""
API response schemas for collection endpoints.
"""
from pydantic import BaseModel

from app.schemas.wallet import ProviderMetaResponse


class ContractMetadataResponse(BaseModel):
    address: str
    name: str | None
    is_verified: bool
    meta: ProviderMetaResponse


class DistributionBucketResponse(BaseModel):
    label: str
    holder_count: int


class TopHolderResponse(BaseModel):
    address: str
    quantity: int
    pct_of_supply: float


class CollectionHoldersResponse(BaseModel):
    address: str
    total_holders: int
    total_supply_held: int
    top_10_concentration_pct: float | None
    top_50_concentration_pct: float | None
    average_holdings: float | None
    median_holdings: float | None
    distribution: list[DistributionBucketResponse]
    top_holders: list[TopHolderResponse]
    data_note: str | None