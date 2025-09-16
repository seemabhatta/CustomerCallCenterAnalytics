from typing import List, Dict, Any
from pydantic import BaseModel, Field


class BorrowerSentiment(BaseModel):
    overall: str = Field(description="Overall sentiment")
    start: str = Field(description="Starting sentiment")
    end: str = Field(description="Ending sentiment")
    trend: str = Field(description="Sentiment trend")


class BorrowerRisks(BaseModel):
    delinquency_risk: float = Field(ge=0.0, le=1.0, description="Delinquency risk score")
    churn_risk: float = Field(ge=0.0, le=1.0, description="Churn risk score")
    complaint_risk: float = Field(ge=0.0, le=1.0, description="Complaint risk score")
    refinance_likelihood: float = Field(ge=0.0, le=1.0, description="Refinance likelihood score")


class AdvisorMetrics(BaseModel):
    empathy_score: float = Field(ge=0.0, le=10.0, description="Empathy score")
    compliance_adherence: float = Field(ge=0.0, le=10.0, description="Compliance adherence score")
    solution_effectiveness: float = Field(ge=0.0, le=10.0, description="Solution effectiveness score")
    coaching_opportunities: List[str] = Field(description="List of coaching opportunities")


class CallAnalysis(BaseModel):
    call_summary: str = Field(description="Summary of the call")
    primary_intent: str = Field(description="Primary intent of the call")
    urgency_level: str = Field(description="Urgency level")
    borrower_sentiment: BorrowerSentiment = Field(description="Borrower sentiment analysis")
    borrower_risks: BorrowerRisks = Field(description="Borrower risk assessment")
    advisor_metrics: AdvisorMetrics = Field(description="Advisor performance metrics")
    compliance_flags: List[str] = Field(description="Compliance flags")
    required_disclosures: List[str] = Field(description="Required disclosures")
    issue_resolved: bool = Field(description="Whether the issue was resolved")
    first_call_resolution: bool = Field(description="Whether it was resolved on first call")
    escalation_needed: bool = Field(description="Whether escalation is needed")
    topics_discussed: List[str] = Field(description="Topics discussed during the call")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Analysis confidence score")
    product_opportunities: List[str] = Field(description="Product opportunities identified")
    payment_concerns: List[str] = Field(description="Payment concerns")
    property_related_issues: List[str] = Field(description="Property-related issues")