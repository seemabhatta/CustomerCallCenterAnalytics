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
    LEGACY: A learned pattern from customer interactions.

    ⚠️  DEPRECATED: This class represents the old pattern system where
    single LLM observations were immediately treated as "patterns".

    Use the new hybrid approach instead:
    - Single observation → Hypothesis
    - Multiple observations → CandidatePattern
    - Statistical validation → ValidatedPattern

    This class is kept for backward compatibility and will be removed
    in a future version after data migration.
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
    wisdom_type: str = Field(description="Type: coaching_insight, strategic_insight, intervention_strategy")
    title: str = Field(description="Brief title for the wisdom")
    content: str = Field(description="The wisdom content or insight")
    source_context: Dict[str, Any] = Field(description="Context where this wisdom was derived")
    learning_domain: str = Field(description="Domain: customer_service, advisor_performance, operational_efficiency")
    applicability: str = Field(description="How broadly this wisdom applies: specific, general, universal")
    validated: bool = Field(description="Whether this wisdom has been validated")
    validation_count: int = Field(description="Number of times this wisdom was validated")
    effectiveness_score: float = Field(ge=0.0, le=1.0, description="Effectiveness score of this wisdom")
    created_at: datetime = Field(description="When this wisdom was discovered")
    last_applied: Optional[datetime] = Field(description="When this wisdom was last applied")
    application_count: int = Field(description="Number of times this wisdom was applied")


class MetaLearning(BaseModel):
    """
    Learning about the learning process itself.

    MetaLearning captures insights about how the system learns, predicts,
    and improves over time.
    """
    meta_learning_id: str = Field(description="Unique meta-learning identifier")
    learning_type: str = Field(description="Type: system_optimization, prediction_accuracy, pattern_evolution")
    insight_source: str = Field(description="Source of the insight: workflow_generation, analysis, planning")
    meta_insight: str = Field(description="What we learned about our learning process")
    improvement_area: str = Field(description="Specific area for improvement")
    system_component: str = Field(description="System component this relates to")
    learning_context: Dict[str, Any] = Field(description="Context information for this learning")
    impact_assessment: str = Field(description="Assessment of potential impact: low, medium, high")
    validation_status: bool = Field(description="Whether this meta-learning has been validated")
    validation_count: int = Field(description="Number of times this has been validated")
    created_at: datetime = Field(description="When this meta-learning was created")
    last_updated: datetime = Field(description="When this was last updated")


class Hypothesis(BaseModel):
    """
    An unvalidated observation from a single interaction.

    Hypotheses are LLM-generated insights that require evidence accumulation
    and statistical validation before becoming patterns.
    """
    hypothesis_id: str = Field(description="Unique hypothesis identifier")
    hypothesis_type: str = Field(description="Type: behavioral, risk, operational, outcome")
    title: str = Field(description="Human-readable hypothesis title")
    description: str = Field(description="What this hypothesis suggests")

    # LLM-generated fields
    llm_confidence: float = Field(ge=0.0, le=1.0, description="LLM's confidence in this hypothesis")
    reasoning: str = Field(description="LLM's reasoning for this hypothesis")

    # Evidence tracking
    evidence_count: int = Field(default=1, description="Number of observations supporting this hypothesis")
    source_calls: List[str] = Field(description="Call IDs that contributed evidence")
    first_observed: datetime = Field(description="When this hypothesis was first generated")
    last_evidence: datetime = Field(description="When evidence was last added")

    # Context
    source_stage: str = Field(description="Pipeline stage that generated this hypothesis")
    customer_context: Dict[str, Any] = Field(description="Customer context for this hypothesis")

    # Status
    status: str = Field(default="unvalidated", description="Status: unvalidated, accumulating_evidence, promoted")


class CandidatePattern(BaseModel):
    """
    A hypothesis with multiple observations awaiting statistical validation.

    Candidate patterns have accumulated enough evidence to warrant validation
    but haven't yet been statistically confirmed.
    """
    candidate_id: str = Field(description="Unique candidate pattern identifier")
    hypothesis_id: str = Field(description="Original hypothesis this was promoted from")
    pattern_type: str = Field(description="Type: behavioral, risk, operational, outcome")
    title: str = Field(description="Human-readable pattern title")
    description: str = Field(description="What this pattern represents")

    # Evidence accumulation
    evidence_count: int = Field(description="Total number of supporting observations")
    source_calls: List[str] = Field(description="All call IDs that provided evidence")
    occurrence_frequency: float = Field(ge=0.0, le=1.0, description="Frequency of occurrence in dataset")

    # Statistical readiness
    awaiting_validation: bool = Field(default=True, description="Whether awaiting statistical validation")
    validation_threshold_met: bool = Field(description="Whether minimum evidence threshold is met")
    sample_size: int = Field(description="Current sample size for validation")

    # Timing
    promoted_at: datetime = Field(description="When promoted from hypothesis")
    ready_for_validation_at: Optional[datetime] = Field(description="When became ready for validation")

    # Context preservation
    original_llm_confidence: float = Field(description="Original LLM confidence from hypothesis")
    source_stage: str = Field(description="Pipeline stage that generated original hypothesis")


class ValidatedPattern(BaseModel):
    """
    A statistically validated pattern with real confidence metrics.

    This replaces the old Pattern class for patterns that have been
    validated through traditional ML statistical analysis.
    """
    pattern_id: str = Field(description="Unique pattern identifier")
    candidate_id: str = Field(description="Candidate pattern this was validated from")
    pattern_type: str = Field(description="Type: behavioral, risk, operational, outcome")
    title: str = Field(description="Human-readable pattern title")
    description: str = Field(description="What this pattern represents")

    # Pattern conditions and outcomes
    conditions: Dict[str, Any] = Field(description="Conditions that indicate this pattern")
    outcomes: Dict[str, Any] = Field(description="Expected outcomes when pattern occurs")

    # Statistical validation
    statistical_confidence: float = Field(ge=0.0, le=1.0, description="Statistical confidence based on data")
    p_value: float = Field(ge=0.0, le=1.0, description="Statistical significance p-value")
    sample_size: int = Field(description="Sample size used for validation")
    validation_method: str = Field(description="Statistical method used for validation")

    # Performance metrics
    occurrence_rate: float = Field(ge=0.0, le=1.0, description="Rate of occurrence in population")
    success_rate: float = Field(ge=0.0, le=1.0, description="Success rate when pattern conditions are met")
    effect_size: float = Field(description="Statistical effect size")

    # Validation metadata
    validated_at: datetime = Field(description="When pattern was statistically validated")
    validated_by: str = Field(description="Validation method/system used")
    validation_dataset_size: int = Field(description="Size of dataset used for validation")

    # Learning metadata
    total_occurrences: int = Field(description="Total times pattern was observed")
    last_observed: datetime = Field(description="When pattern was last observed")
    source_pipeline: str = Field(description="Pipeline stage that discovered this pattern")

    # Continuous validation
    revalidation_due: datetime = Field(description="When pattern should be revalidated")
    validation_status: str = Field(default="active", description="Status: active, deprecated, under_review")


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
    insight_type: str = Field(description="Type: hypothesis, candidate_pattern, validated_pattern, prediction, wisdom, meta_learning")
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