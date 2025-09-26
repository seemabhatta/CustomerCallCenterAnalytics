"""
Event Infrastructure for Knowledge Graph 2.0.

Provides event-driven architecture for automatic graph updates.
"""
from .event_types import (
    EventType,
    Event,
    TranscriptCreatedPayload,
    AnalysisCompletedPayload,
    WorkflowEscalatedPayload,
    IssueResolvedPayload,
    DocumentAcknowledgedPayload,
    PlanGeneratedPayload,
    WorkflowCreatedPayload,
    ExecutionStepCompletedPayload,
    create_transcript_event,
    create_escalation_event,
    create_analysis_event,
    create_plan_generated_event,
    create_workflow_created_event,
    create_execution_step_completed_event
)
from .event_system import (
    EventSystem,
    EventSystemError,
    get_event_system,
    publish_event,
    subscribe_to_events,
    event_handler
)

__all__ = [
    'EventType',
    'Event',
    'EventSystem',
    'EventSystemError',
    'TranscriptCreatedPayload',
    'AnalysisCompletedPayload',
    'WorkflowEscalatedPayload',
    'IssueResolvedPayload',
    'DocumentAcknowledgedPayload',
    'PlanGeneratedPayload',
    'WorkflowCreatedPayload',
    'ExecutionStepCompletedPayload',
    'create_transcript_event',
    'create_escalation_event',
    'create_analysis_event',
    'create_plan_generated_event',
    'create_workflow_created_event',
    'create_execution_step_completed_event',
    'get_event_system',
    'publish_event',
    'subscribe_to_events',
    'event_handler'
]