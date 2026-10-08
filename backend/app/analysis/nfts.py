"""
NFT portfolio analysis. Concentration is by NFT COUNT per collection, not
floor-price value — that requires a specialized NFT pricing source not yet
integrated. Always labeled clearly, never presented as value-based.
"""
from dataclasses import dataclass, field
from datetime import datetime

from app.providers.base import NFTHolding

RECENT_ACQUISITIONS_LIMIT = 10


@dataclass
class CollectionHolding:
    collection_address: str
    count: int
    pct_of_portfolio: float
    token_ids: list[str]


@dataclass
class RecentAcquisition:
    collection_address: str
    token_id: str
    acquired_at: datetime | None


@dataclass
class NFTPortfolioAnalysis:
    total_nft_count: int
    distinct_collections_count: int
    collections: list[CollectionHolding] = field(default_factory=list)
    top_collection_pct: float | None = None
    recent_acquisitions: list[RecentAcquisition] = field(default_factory=list)
    data_note: str | None = None


def analyze_nft_holdings(holdings: list[NFTHolding]) -> NFTPortfolioAnalysis:
    if not holdings:
        return NFTPortfolioAnalysis(
            total_nft_count=0,
            distinct_collections_count=0,
            collections=[],
            top_collection_pct=None,
            recent_acquisitions=[],
            data_note="No NFT holdings found for this address.",
        )

    by_collection: dict[str, list[NFTHolding]] = {}
    for h in holdings:
        by_collection.setdefault(h.collection_address.lower(), []).append(h)

    total = len(holdings)
    collections = [
        CollectionHolding(
            collection_address=addr,
            count=len(items),
            pct_of_portfolio=len(items) / total * 100,
            token_ids=[i.token_id for i in items],
        )
        for addr, items in by_collection.items()
    ]
    collections.sort(key=lambda c: c.count, reverse=True)
    top_pct = collections[0].pct_of_portfolio if collections else None

    dated = [h for h in holdings if h.acquired_at is not None]
    dated.sort(key=lambda h: h.acquired_at, reverse=True)
    recent = [
        RecentAcquisition(collection_address=h.collection_address, token_id=h.token_id, acquired_at=h.acquired_at)
        for h in dated[:RECENT_ACQUISITIONS_LIMIT]
    ]

    missing_dates = total - len(dated)
    note = (
        f"{missing_dates} of {total} NFTs have no known acquisition date and are excluded "
        "from 'recent acquisitions'. Concentration below is by NFT COUNT per collection, "
        "not floor-price value — real market-value concentration requires a specialized "
        "NFT pricing source not yet integrated (see roadmap)."
        if missing_dates
        else (
            "Concentration below is by NFT COUNT per collection, not floor-price value — "
            "real market-value concentration requires a specialized NFT pricing source "
            "not yet integrated (see roadmap)."
        )
    )

    return NFTPortfolioAnalysis(
        total_nft_count=total,
        distinct_collections_count=len(collections),
        collections=collections,
        top_collection_pct=top_pct,
        recent_acquisitions=recent,
        data_note=note,
    )