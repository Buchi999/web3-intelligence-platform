"""
API response schemas for the transactions endpoint.
"""
from datetime import datetime

from pydantic import BaseModel

from app.providers.base import TransactionDirection


class TransactionResponse(BaseModel):
    hash: str
    block_number: int
    timestamp: datetime
    from_address: str
    to_address: str | None
    value_wei: str
    value_native: float
    direction: TransactionDirection
    is_error: bool
    method: str | None


class LargestTransactionResponse(BaseModel):
    hash: str
    value_wei: str
    value_native: float
    timestamp: datetime


class DormantPeriodResponse(BaseModel):
    start: datetime
    end: datetime
    days: float


class TransactionSummaryResponse(BaseModel):
    total_transactions: int
    incoming_count: int
    outgoing_count: int
    self_count: int
    first_transaction_at: datetime | None
    last_transaction_at: datetime | None
    active_days: int
    average_transaction_value_native: float | None
    average_transactions_per_day: float | None
    largest_transaction: LargestTransactionResponse | None
    dormant_periods: list[DormantPeriodResponse]
    data_note: str | None


class TransactionsResponse(BaseModel):
    address: str
    transactions: list[TransactionResponse]
    summary: TransactionSummaryResponse