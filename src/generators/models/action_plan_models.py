from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ImmediateAction(BaseModel):
    action: str = Field(description="Action description")
    timeline: str = Field(description="Timeline for completion")
    priority: str = Field(description="Priority level")
    auto_executable: bool = Field(description="Whether action is auto-executable")
    description: str = Field(description="Detailed description")


class FollowUp(BaseModel):
    action: str = Field(description="Follow-up action")
    due_date: str = Field(description="Due date")
    owner: str = Field(description="Owner of the action")
    trigger_condition: str = Field(description="Trigger condition")


class BorrowerPlan(BaseModel):
    immediate_actions: List[ImmediateAction] = Field(description="List of immediate actions")
    follow_ups: List[FollowUp] = Field(description="List of follow-up actions")
    personalized_offers: List[str] = Field(description="List of personalized offers")
    risk_mitigation: List[str] = Field(description="List of risk mitigation strategies")


class CoachingItem(BaseModel):
    action: str = Field(description="Coaching action")
    coaching_point: str = Field(description="Coaching point")
    expected_improvement: str = Field(description="Expected improvement")
    priority: str = Field(description="Priority level")


class PerformanceFeedback(BaseModel):
    strengths: List[str] = Field(description="List of strengths")
    improvements: List[str] = Field(description="List of improvements")
    score_explanations: List[str] = Field(description="List of score explanations")


class AdvisorPlan(BaseModel):
    coaching_items: List[CoachingItem] = Field(description="List of coaching items")
    performance_feedback: PerformanceFeedback = Field(description="Performance feedback")
    training_recommendations: List[str] = Field(description="List of training recommendations")
    next_actions: List[str] = Field(description="List of next actions")


class EscalationItem(BaseModel):
    item: str = Field(description="Escalation item")
    reason: str = Field(description="Reason for escalation")
    priority: str = Field(description="Priority level")
    action_required: str = Field(description="Action required")


class SupervisorPlan(BaseModel):
    escalation_items: List[EscalationItem] = Field(description="List of escalation items")
    team_patterns: List[str] = Field(description="List of team patterns")
    compliance_review: List[str] = Field(description="List of compliance review items")
    approval_required: bool = Field(description="Whether approval is required")
    process_improvements: List[str] = Field(description="List of process improvements")


class LeadershipPlan(BaseModel):
    portfolio_insights: List[str] = Field(description="List of portfolio insights")
    strategic_opportunities: List[str] = Field(description="List of strategic opportunities")
    risk_indicators: List[str] = Field(description="List of risk indicators")
    trend_analysis: List[str] = Field(description="List of trend analysis")
    resource_allocation: List[str] = Field(description="List of resource allocation recommendations")


class FourLayerActionPlan(BaseModel):
    borrower_plan: BorrowerPlan = Field(description="Borrower action plan")
    advisor_plan: AdvisorPlan = Field(description="Advisor action plan")
    supervisor_plan: SupervisorPlan = Field(description="Supervisor action plan")
    leadership_plan: LeadershipPlan = Field(description="Leadership action plan")