"""
Request schema for POST /api/v1/reports.
"""
from enum import Enum

from pydantic import BaseModel, Field


class ReportTargetType(str, Enum):
    WALLET = "wallet"
    COLLECTION = "collection"


class ReportRequest(BaseModel):
    target_type: ReportTargetType
    address: str = Field(..., description="Wallet address (target_type=wallet) or contract address (target_type=collection)")