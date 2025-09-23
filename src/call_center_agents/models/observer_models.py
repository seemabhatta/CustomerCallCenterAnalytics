from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ExecutionEvaluation(BaseModel):
    overall_satisfaction: str = Field(description="Overall satisfaction level")
    execution_quality: float = Field(ge=1.0, le=5.0, description="Execution quality score")
    identified_issues: List[str] = Field(description="List of identified issues")
    improvement_opportunities: List[str] = Field(description="List of improvement opportunities")
    feedback_for_decision_agent: str = Field(description="Feedback for decision agent")


class DecisionAgentFeedback(BaseModel):
    routing_adjustments: List[str] = Field(description="Routing adjustments")
    risk_assessment_updates: List[str] = Field(description="Risk assessment updates")
    process_improvements: List[str] = Field(description="Process improvements")
    training_recommendations: Dict[str, List[str]] = Field(description="Training recommendations")