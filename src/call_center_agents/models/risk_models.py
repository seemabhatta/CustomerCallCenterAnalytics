from typing import List, Literal
from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Risk level classification")
    reasoning: str = Field(description="Detailed reasoning for the risk assessment")
    factors: List[str] = Field(description="Key risk factors identified")
    score: float = Field(ge=0.0, le=1.0, description="Risk score between 0 and 1")


class ApprovalRouting(BaseModel):
    approval_level: Literal["ADVISOR", "SUPERVISOR", "LEADERSHIP"] = Field(description="Required approval level")
    reasoning: str = Field(description="Reasoning for the approval level decision")
    urgency: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Urgency level")
    estimated_time_days: int = Field(ge=1, description="Estimated approval time in days")