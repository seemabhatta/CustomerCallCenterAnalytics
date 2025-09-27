"""
Knowledge Types - Structures for storing predictive knowledge, patterns, and wisdom.

These models represent institutional learning that helps the system anticipate,
predict, and intervene proactively.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Pattern(BaseModel):
    """
    A learned pattern from customer interactions.

    Patterns represent recurring behaviors, outcomes, or conditions that
    the system has identified and can use for prediction.
    """
    pattern_id: str = Field(description="Unique pattern identifier")
    pattern_type: str = Field(description="Type: risk_escalation, success_workflow, intervention_trigger")
    title: str = Field(description="Human-readable pattern title")
    description: str = Field(description="What this pattern represents")

    # Pattern specifics
    conditions: Dict[str, Any] = Field(description="Conditions that indicate this pattern")
    outcomes: Dict[str, Any] = Field(description="Expected outcomes when this pattern occurs")
    confidence: float = Field(ge=0.0, le=1.0, description="Pattern confidence based on evidence")

    # Learning metadata
    occurrences: int = Field(description="Number of times this pattern was observed")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate when pattern conditions are met")
    last_observed: datetime = Field(description="When this pattern was last observed")
    source_pipeline: str = Field(description="Pipeline stage that discovered this pattern")


class Prediction(BaseModel):
    """
    A predictive insight about future events or outcomes.

    Predictions are living forecasts that evolve as new evidence becomes available.
    """
    prediction_id: str = Field(description="Unique prediction identifier")
    prediction_type: str = Field(description="Type: customer_risk, advisor_need, workflow_optimization")
    target_entity: str = Field(description="What entity this prediction is about")
    target_entity_id: str = Field(description="Specific entity ID")

    # Prediction content
    predicted_event: str = Field(description="What is predicted to happen")
    probability: float = Field(ge=0.0, le=1.0, description="Probability of predicted event")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this prediction")
    time_horizon: str = Field(description="When this is expected: immediate, short_term, long_term")

    # Supporting evidence
    supporting_patterns: List[str] = Field(description="Pattern IDs that support this prediction")
    evidence_strength: float = Field(ge=0.0, le=1.0, description="Strength of supporting evidence")

    # Prediction lifecycle
    created_at: datetime = Field(description="When prediction was made")
    expires_at: Optional[datetime] = Field(description="When prediction expires if not validated")
    validated: Optional[bool] = Field(description="Whether prediction came true")
    validation_date: Optional[datetime] = Field(description="When prediction was validated")


class Wisdom(BaseModel):
    """
    High-level strategic insights and institutional knowledge.

    Wisdom represents meta-learning about successful strategies, intervention points,
    and optimization opportunities.
    """
    wisdom_id: str = Field(description="Unique wisdom identifier")
    wisdom_type: str = Field(description="Type: strategic_insight, intervention_strategy, optimization_opportunity")
    domain: str = Field(description="Domain: customer_success, advisor_performance, operational_efficiency")

    # Wisdom content
    insight: str = Field(description="The strategic insight or learning")
    applications: List[str] = Field(description="How this wisdom can be applied")
    success_indicators: List[str] = Field(description="How to measure success of applying this wisdom")

    # Supporting evidence
    derived_from_patterns: List[str] = Field(description="Pattern IDs this wisdom is derived from")
    evidence_base: Dict[str, Any] = Field(description="Statistical evidence supporting this wisdom")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence in this wisdom")

    # Wisdom evolution
    discovered_at: datetime = Field(description="When this wisdom was discovered")
    times_applied: int = Field(description="Number of times this wisdom was applied")
    application_success_rate: float = Field(ge=0.0, le=1.0, description="Success rate of applications")


class MetaLearning(BaseModel):
    """
    Learning about the learning process itself.

    MetaLearning captures insights about how the system learns, predicts,
    and improves over time.
    """
    meta_id: str = Field(description="Unique meta-learning identifier")
    meta_type: str = Field(description="Type: prediction_accuracy, pattern_evolution, system_improvement")

    # Meta-learning content
    learning_insight: str = Field(description="What we learned about our learning process")
    improvement_opportunity: str = Field(description="How the system can improve")
    optimization_suggestion: str = Field(description="Specific optimization to implement")

    # Learning performance
    accuracy_metrics: Dict[str, float] = Field(description="Accuracy of predictions, patterns, etc.")
    learning_velocity: float = Field(description="How quickly system is improving")
    knowledge_gaps: List[str] = Field(description="Areas where more learning is needed")

    # Meta evolution
    observed_at: datetime = Field(description="When this meta-learning was observed")
    system_version: str = Field(description="System version when this was learned")


class InsightContent(BaseModel):
    """Structured content for predictive insights."""
    key: str = Field(description="Primary insight key or pattern identified")
    value: str = Field(description="Insight value or prediction details")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this insight")
    impact: str = Field(description="Expected impact or outcome")

    class Config:
        extra = "forbid"  # Required for OpenAI structured output


class CustomerContext(BaseModel):
    """Customer context for insights."""
    customer_id: str = Field(description="Customer identifier")
    loan_type: str = Field(description="Type of loan or product")
    tenure: str = Field(description="Customer tenure or relationship length")
    risk_profile: str = Field(description="Customer risk profile")

    class Config:
        extra = "forbid"  # Required for OpenAI structured output


class PredictiveInsight(BaseModel):
    """
    Simplified insight structure for pipeline contributions.

    This is what each pipeline stage contributes to the knowledge graph.
    """
    insight_type: str = Field(description="Type: pattern, prediction, wisdom, meta_learning")
    priority: str = Field(description="Priority: high, medium, low")
    content: InsightContent = Field(description="The actual insight content")
    reasoning: str = Field(description="Why this insight is valuable")
    learning_value: str = Field(description="Learning value: critical, exceptional, routine")
    source_stage: str = Field(description="Pipeline stage that generated this insight")

    # Context
    transcript_id: str = Field(description="Source transcript")
    customer_context: CustomerContext = Field(description="Customer context for this insight")
    timestamp: str = Field(description="ISO timestamp when insight was generated")

    class Config:
        extra = "forbid"  # Required for OpenAI structured output