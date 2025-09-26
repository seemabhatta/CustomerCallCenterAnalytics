"""
Event Types for Knowledge Graph 2.0 Event-Driven Architecture.

Defines all system events that trigger knowledge graph updates.
NO FALLBACK PRINCIPLE: All events must be properly typed and validated.
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class EventType(Enum):
    """Comprehensive event types for knowledge graph updates."""

    # Transcript Events
    TRANSCRIPT_CREATED = "transcript.created"
    TRANSCRIPT_STARTED = "transcript.started"
    TRANSCRIPT_COMPLETED = "transcript.completed"
    TRANSCRIPT_DELETED = "transcript.deleted"

    # Customer Events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CUSTOMER_RISK_CHANGED = "customer.risk_changed"

    # Advisor Events
    ADVISOR_ASSIGNED = "advisor.assigned"
    ADVISOR_PERFORMANCE_UPDATED = "advisor.performance_updated"
    ADVISOR_SKILL_CERTIFIED = "advisor.skill_certified"

    # Analysis Events
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_RISK_DETECTED = "analysis.risk_detected"
    ANALYSIS_COMPLIANCE_FLAGGED = "analysis.compliance_flagged"

    # Plan Events
    PLAN_GENERATED = "plan.generated"
    PLAN_APPROVED = "plan.approved"
    PLAN_REJECTED = "plan.rejected"
    PLAN_EXECUTED = "plan.executed"

    # Workflow Events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_ASSIGNED = "workflow.assigned"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_ESCALATED = "workflow.escalated"

    # Execution Events
    EXECUTION_STARTED = "execution.started"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"
    EXECUTION_STEP_COMPLETED = "execution.step_completed"

    # Interaction Events
    CUSTOMER_CONTACTED_ADVISOR = "interaction.customer_contacted_advisor"
    ADVISOR_ESCALATED_TO_SUPERVISOR = "interaction.advisor_escalated_to_supervisor"
    SUPERVISOR_INTERVENED = "interaction.supervisor_intervened"

    # Document Events
    DOCUMENT_GENERATED = "document.generated"
    DOCUMENT_SENT = "document.sent"
    DOCUMENT_ACKNOWLEDGED = "document.acknowledged"
    DOCUMENT_EXPIRED = "document.expired"

    # Issue & Resolution Events
    ISSUE_CREATED = "issue.created"
    ISSUE_ESCALATED = "issue.escalated"
    ISSUE_RESOLVED = "issue.resolved"
    ISSUE_REOPENED = "issue.reopened"

    # Loan Events
    LOAN_CREATED = "loan.created"
    LOAN_MODIFIED = "loan.modified"
    LOAN_PAYMENT_RECEIVED = "loan.payment_received"
    LOAN_DELINQUENT = "loan.delinquent"


@dataclass
class Event:
    """Base event structure for all system events."""

    event_type: EventType
    event_id: str
    timestamp: datetime
    payload: Dict[str, Any]
    source_service: str
    correlation_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate event structure."""
        if not self.event_id:
            raise ValueError("event_id is required")
        if not self.payload:
            raise ValueError("payload is required")
        if not self.source_service:
            raise ValueError("source_service is required")


# Event Payload Schemas for validation
@dataclass
class TranscriptCreatedPayload:
    """Payload for TRANSCRIPT_CREATED event."""
    transcript_id: str
    customer_id: str
    advisor_id: str
    topic: str
    urgency: str
    channel: str  # phone, chat, email
    started_at: datetime
    expected_duration: Optional[int] = None  # seconds


@dataclass
class AnalysisCompletedPayload:
    """Payload for ANALYSIS_COMPLETED event."""
    analysis_id: str
    transcript_id: str
    customer_id: str
    intent: str
    urgency_level: str
    sentiment: str
    risk_score: float
    compliance_flags: list
    confidence_score: float
    processing_time_ms: int


@dataclass
class WorkflowEscalatedPayload:
    """Payload for WORKFLOW_ESCALATED event."""
    workflow_id: str
    escalated_from_advisor: str
    escalated_to_supervisor: str
    escalation_reason: str
    urgency_level: str
    escalated_at: datetime
    original_issue: str


@dataclass
class IssueResolvedPayload:
    """Payload for ISSUE_RESOLVED event."""
    issue_id: str
    resolution_id: str
    resolved_by_advisor: str
    resolved_by_supervisor: Optional[str]
    resolution_method: str
    resolution_time_minutes: int
    customer_satisfaction: Optional[float]
    resolved_at: datetime


@dataclass
class DocumentAcknowledgedPayload:
    """Payload for DOCUMENT_ACKNOWLEDGED event."""
    document_id: str
    customer_id: str
    document_type: str
    sent_at: datetime
    acknowledged_at: datetime
    acknowledgment_method: str  # email_click, phone_confirm, portal_sign


# Additional payload schemas for plan and workflow events
@dataclass
class PlanGeneratedPayload:
    """Payload for PLAN_GENERATED event."""
    plan_id: str
    analysis_id: str
    transcript_id: str
    customer_id: str
    priority_level: str
    action_count: int
    generated_at: datetime
    urgency_level: str


@dataclass
class WorkflowCreatedPayload:
    """Payload for WORKFLOW_CREATED event."""
    workflow_id: str
    plan_id: str
    workflow_type: str
    approval_status: str
    risk_level: str
    step_count: int
    created_at: datetime


@dataclass
class ExecutionStepCompletedPayload:
    """Payload for EXECUTION_STEP_COMPLETED event."""
    execution_id: str
    workflow_id: str
    step_number: int
    step_description: str
    executor_type: str
    execution_result: str
    executed_by: str
    executed_at: datetime
    execution_time_ms: int


# Event Factory Functions
def create_transcript_event(transcript_id: str, customer_id: str, advisor_id: str,
                          topic: str, urgency: str, channel: str) -> Event:
    """Create a TRANSCRIPT_CREATED event."""
    payload = TranscriptCreatedPayload(
        transcript_id=transcript_id,
        customer_id=customer_id,
        advisor_id=advisor_id,
        topic=topic,
        urgency=urgency,
        channel=channel,
        started_at=datetime.utcnow()
    ).__dict__

    return Event(
        event_type=EventType.TRANSCRIPT_CREATED,
        event_id=f"transcript_{transcript_id}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="transcript_service"
    )


def create_escalation_event(workflow_id: str, from_advisor: str, to_supervisor: str,
                          reason: str, urgency: str) -> Event:
    """Create a WORKFLOW_ESCALATED event."""
    payload = WorkflowEscalatedPayload(
        workflow_id=workflow_id,
        escalated_from_advisor=from_advisor,
        escalated_to_supervisor=to_supervisor,
        escalation_reason=reason,
        urgency_level=urgency,
        escalated_at=datetime.utcnow(),
        original_issue=f"Workflow {workflow_id} escalation"
    ).__dict__

    return Event(
        event_type=EventType.WORKFLOW_ESCALATED,
        event_id=f"escalation_{workflow_id}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="workflow_service"
    )


def create_analysis_event(analysis_id: str, transcript_id: str, customer_id: str,
                         intent: str, urgency: str, sentiment: str, risk_score: float) -> Event:
    """Create an ANALYSIS_COMPLETED event."""
    payload = AnalysisCompletedPayload(
        analysis_id=analysis_id,
        transcript_id=transcript_id,
        customer_id=customer_id,
        intent=intent,
        urgency_level=urgency,
        sentiment=sentiment,
        risk_score=risk_score,
        compliance_flags=[],
        confidence_score=0.85,
        processing_time_ms=1500
    ).__dict__

    return Event(
        event_type=EventType.ANALYSIS_COMPLETED,
        event_id=f"analysis_{analysis_id}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="analysis_service"
    )


def create_plan_generated_event(plan_id: str, analysis_id: str, transcript_id: str,
                              customer_id: str, priority_level: str, action_count: int,
                              urgency_level: str) -> Event:
    """Create a PLAN_GENERATED event."""
    payload = PlanGeneratedPayload(
        plan_id=plan_id,
        analysis_id=analysis_id,
        transcript_id=transcript_id,
        customer_id=customer_id,
        priority_level=priority_level,
        action_count=action_count,
        generated_at=datetime.utcnow(),
        urgency_level=urgency_level
    ).__dict__

    return Event(
        event_type=EventType.PLAN_GENERATED,
        event_id=f"plan_{plan_id}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="plan_service"
    )


def create_workflow_created_event(workflow_id: str, plan_id: str, workflow_type: str,
                                approval_status: str, risk_level: str, step_count: int) -> Event:
    """Create a WORKFLOW_CREATED event."""
    payload = WorkflowCreatedPayload(
        workflow_id=workflow_id,
        plan_id=plan_id,
        workflow_type=workflow_type,
        approval_status=approval_status,
        risk_level=risk_level,
        step_count=step_count,
        created_at=datetime.utcnow()
    ).__dict__

    return Event(
        event_type=EventType.WORKFLOW_CREATED,
        event_id=f"workflow_{workflow_id}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="workflow_service"
    )


def create_execution_step_completed_event(execution_id: str, workflow_id: str, step_number: int,
                                        step_description: str, executor_type: str, execution_result: str,
                                        executed_by: str, execution_time_ms: int) -> Event:
    """Create an EXECUTION_STEP_COMPLETED event."""
    payload = ExecutionStepCompletedPayload(
        execution_id=execution_id,
        workflow_id=workflow_id,
        step_number=step_number,
        step_description=step_description,
        executor_type=executor_type,
        execution_result=execution_result,
        executed_by=executed_by,
        executed_at=datetime.utcnow(),
        execution_time_ms=execution_time_ms
    ).__dict__

    return Event(
        event_type=EventType.EXECUTION_STEP_COMPLETED,
        event_id=f"execution_{execution_id}_{step_number}_{int(datetime.utcnow().timestamp())}",
        timestamp=datetime.utcnow(),
        payload=payload,
        source_service="execution_service"
    )