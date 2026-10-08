"""
Transaction analysis. Pure functions only — no network, no provider dependency.
"""
from dataclasses import dataclass, field
from datetime import datetime

from app.providers.base import Transaction, TransactionDirection

DORMANT_THRESHOLD_DAYS = 30


@dataclass
class LargestTransaction:
    hash: str
    value_wei: str
    value_native: float
    timestamp: datetime


@dataclass
class DormantPeriod:
    start: datetime
    end: datetime
    days: float


@dataclass
class TransactionAnalysis:
    total_transactions: int
    incoming_count: int
    outgoing_count: int
    self_count: int
    first_transaction_at: datetime | None
    last_transaction_at: datetime | None
    active_days: int
    average_transaction_value_native: float | None
    average_transactions_per_day: float | None
    largest_transaction: LargestTransaction | None
    dormant_periods: list[DormantPeriod] = field(default_factory=list)
    data_note: str | None = None


def _empty_analysis(note: str) -> TransactionAnalysis:
    return TransactionAnalysis(
        total_transactions=0,
        incoming_count=0,
        outgoing_count=0,
        self_count=0,
        first_transaction_at=None,
        last_transaction_at=None,
        active_days=0,
        average_transaction_value_native=None,
        average_transactions_per_day=None,
        largest_transaction=None,
        dormant_periods=[],
        data_note=note,
    )


def analyze_transactions(transactions: list[Transaction]) -> TransactionAnalysis:
    if not transactions:
        return _empty_analysis("No transactions found for this address.")

    sorted_txs = sorted(transactions, key=lambda t: t.timestamp)

    incoming = sum(1 for t in sorted_txs if t.direction == TransactionDirection.IN)
    outgoing = sum(1 for t in sorted_txs if t.direction == TransactionDirection.OUT)
    self_tx = sum(1 for t in sorted_txs if t.direction == TransactionDirection.SELF)

    active_days = len({t.timestamp.date() for t in sorted_txs})

    positive_values: list[float] = []
    largest: LargestTransaction | None = None
    for t in sorted_txs:
        try:
            wei = int(t.value_wei)
        except (TypeError, ValueError):
            continue
        native = wei / 10**18
        if native > 0:
            positive_values.append(native)
        if largest is None or native > largest.value_native:
            largest = LargestTransaction(
                hash=t.hash, value_wei=t.value_wei, value_native=native, timestamp=t.timestamp
            )

    average_value = sum(positive_values) / len(positive_values) if positive_values else None

    first_at = sorted_txs[0].timestamp
    last_at = sorted_txs[-1].timestamp
    span_days = max((last_at - first_at).total_seconds() / 86400, 1.0)
    average_per_day = len(sorted_txs) / span_days

    dormant_periods = []
    for prev, curr in zip(sorted_txs, sorted_txs[1:]):
        gap_days = (curr.timestamp - prev.timestamp).total_seconds() / 86400
        if gap_days >= DORMANT_THRESHOLD_DAYS:
            dormant_periods.append(DormantPeriod(start=prev.timestamp, end=curr.timestamp, days=gap_days))

    data_note = None
    if len(transactions) >= 1000:
        data_note = (
            "This wallet has 1000+ recent transactions on the free Etherscan tier; "
            "history beyond this page is not reflected in this summary."
        )

    return TransactionAnalysis(
        total_transactions=len(sorted_txs),
        incoming_count=incoming,
        outgoing_count=outgoing,
        self_count=self_tx,
        first_transaction_at=first_at,
        last_transaction_at=last_at,
        active_days=active_days,
        average_transaction_value_native=average_value,
        average_transactions_per_day=average_per_day,
        largest_transaction=largest,
        dormant_periods=dormant_periods,
        data_note=data_note,
    )