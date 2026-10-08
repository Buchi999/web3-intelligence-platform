"""
NFT Holder Intelligence. Computes what's answerable from a single
point-in-time snapshot: concentration, distribution, top holders.
Active/dormant status and growth/loss need historical snapshots (roadmap).
"""
import statistics
from dataclasses import dataclass, field

from app.providers.base import HolderRecord

TOP_HOLDERS_LIMIT = 10


@dataclass
class DistributionBucket:
    label: str
    holder_count: int


@dataclass
class TopHolder:
    address: str
    quantity: int
    pct_of_supply: float


@dataclass
class CollectionHolderAnalysis:
    total_holders: int
    total_supply_held: int
    top_10_concentration_pct: float | None
    top_50_concentration_pct: float | None
    average_holdings: float | None
    median_holdings: float | None
    distribution: list[DistributionBucket] = field(default_factory=list)
    top_holders: list[TopHolder] = field(default_factory=list)
    data_note: str | None = None


def _bucket_label(quantity: int) -> str:
    if quantity == 1:
        return "1 NFT"
    if 2 <= quantity <= 5:
        return "2-5 NFTs"
    if 6 <= quantity <= 10:
        return "6-10 NFTs"
    return "10+ NFTs"


def analyze_collection_holders(holders: list[HolderRecord]) -> CollectionHolderAnalysis:
    if not holders:
        return CollectionHolderAnalysis(
            total_holders=0,
            total_supply_held=0,
            top_10_concentration_pct=None,
            top_50_concentration_pct=None,
            average_holdings=None,
            median_holdings=None,
            distribution=[],
            top_holders=[],
            data_note="No holder data found for this collection.",
        )

    sorted_holders = sorted(holders, key=lambda h: h.quantity, reverse=True)
    total_supply = sum(h.quantity for h in holders)
    total_holders = len(holders)

    def concentration(top_n: int) -> float | None:
        if total_supply <= 0:
            return None
        top_n_qty = sum(h.quantity for h in sorted_holders[:top_n])
        return top_n_qty / total_supply * 100

    quantities = [h.quantity for h in holders]

    bucket_order = ["1 NFT", "2-5 NFTs", "6-10 NFTs", "10+ NFTs"]
    bucket_counts = {label: 0 for label in bucket_order}
    for h in holders:
        bucket_counts[_bucket_label(h.quantity)] += 1
    distribution = [DistributionBucket(label=label, holder_count=bucket_counts[label]) for label in bucket_order]

    top_holders = [
        TopHolder(
            address=h.address,
            quantity=h.quantity,
            pct_of_supply=(h.quantity / total_supply * 100) if total_supply > 0 else 0.0,
        )
        for h in sorted_holders[:TOP_HOLDERS_LIMIT]
    ]

    return CollectionHolderAnalysis(
        total_holders=total_holders,
        total_supply_held=total_supply,
        top_10_concentration_pct=concentration(10),
        top_50_concentration_pct=concentration(50),
        average_holdings=total_supply / total_holders if total_holders else None,
        median_holdings=statistics.median(quantities) if quantities else None,
        distribution=distribution,
        top_holders=top_holders,
        data_note=(
            "Active/dormant holder status and recent holder growth or loss require "
            "historical snapshots compared over time, which aren't available from a "
            "single point-in-time holder query (see roadmap)."
        ),
    )