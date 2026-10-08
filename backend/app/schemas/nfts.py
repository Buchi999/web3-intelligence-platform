"""
API response schemas for the wallet NFT holdings endpoint.
"""
from datetime import datetime

from pydantic import BaseModel


class NFTHoldingResponse(BaseModel):
    collection_address: str
    token_id: str
    acquired_at: datetime | None


class CollectionHoldingResponse(BaseModel):
    collection_address: str
    count: int
    pct_of_portfolio: float
    token_ids: list[str]


class RecentAcquisitionResponse(BaseModel):
    collection_address: str
    token_id: str
    acquired_at: datetime | None


class NFTsResponse(BaseModel):
    address: str
    holdings: list[NFTHoldingResponse]
    collections: list[CollectionHoldingResponse]
    distinct_collections_count: int
    top_collection_pct: float | None
    recent_acquisitions: list[RecentAcquisitionResponse]
    data_note: str | None