"""
API response schemas for GET /wallet/{address}/analysis.
"""
from pydantic import BaseModel


class BehaviorClassificationResponse(BaseModel):
    label: str
    confidence: float
    factors: list[str]


class RiskFactorResponse(BaseModel):
    description: str
    points: int


class RiskAssessmentResponse(BaseModel):
    score: int
    factors: list[RiskFactorResponse]
    disclaimer: str


class WalletAnalysisResponse(BaseModel):
    address: str
    wallet_age_days: int | None
    classifications: list[BehaviorClassificationResponse]
    risk: RiskAssessmentResponse
    ai_summary: str | None = None