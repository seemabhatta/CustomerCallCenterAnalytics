"""
Graph Event Handlers for Knowledge Graph 2.0.

Event handlers that automatically update the knowledge graph based on system events.
NO FALLBACK PRINCIPLE: Graph updates must succeed or system fails fast.
"""
import logging
from typing import Dict, Any
from datetime import datetime

from .event_system import subscribe_to_events
from .event_types import EventType, Event
from ..graph.graph_manager import get_graph_manager, GraphManagerError

logger = logging.getLogger(__name__)


def handle_transcript_created(sender, **kwargs):
    """Handle TRANSCRIPT_CREATED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract data from payload
        transcript_id = payload['transcript_id']
        customer_id = payload['customer_id']
        advisor_id = payload['advisor_id']
        topic = payload['topic']
        urgency = payload['urgency']
        channel = payload['channel']
        started_at = payload['started_at']

        # Create or update entities
        graph_manager.create_or_update_customer(customer_id)
        graph_manager.create_or_update_advisor(advisor_id)

        # Create transcript node with rich attributes
        graph_manager.create_transcript(
            transcript_id=transcript_id,
            customer_id=customer_id,
            advisor_id=advisor_id,
            topic=topic,
            urgency=urgency,
            channel=channel,
            started_at=started_at,
            status='active'
        )

        logger.info(f"✅ Graph updated for transcript created: {transcript_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle TRANSCRIPT_CREATED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_analysis_completed(sender, **kwargs):
    """Handle ANALYSIS_COMPLETED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract analysis data
        analysis_id = payload['analysis_id']
        transcript_id = payload['transcript_id']
        customer_id = payload['customer_id']
        intent = payload['intent']
        urgency_level = payload['urgency_level']
        sentiment = payload['sentiment']
        risk_score = payload['risk_score']
        compliance_flags = payload.get('compliance_flags', [])
        confidence_score = payload.get('confidence_score', 0.0)

        # Create analysis node
        graph_manager.create_analysis(
            analysis_id=analysis_id,
            transcript_id=transcript_id,
            intent=intent,
            urgency_level=urgency_level,
            sentiment=sentiment,
            risk_score=risk_score,
            compliance_flags=compliance_flags,
            confidence_score=confidence_score
        )

        # Update customer risk profile based on analysis
        graph_manager.update_customer_risk_profile(
            customer_id=customer_id,
            risk_score=risk_score,
            compliance_flags=compliance_flags
        )

        logger.info(f"✅ Graph updated for analysis completed: {analysis_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle ANALYSIS_COMPLETED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_workflow_escalated(sender, **kwargs):
    """Handle WORKFLOW_ESCALATED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract escalation data
        workflow_id = payload['workflow_id']
        from_advisor = payload['escalated_from_advisor']
        to_supervisor = payload['escalated_to_supervisor']
        escalation_reason = payload['escalation_reason']
        urgency_level = payload['urgency_level']
        escalated_at = payload['escalated_at']

        # Create or update supervisor
        graph_manager.create_or_update_supervisor(to_supervisor)

        # Create escalation relationship
        graph_manager.create_escalation(
            workflow_id=workflow_id,
            from_advisor=from_advisor,
            to_supervisor=to_supervisor,
            reason=escalation_reason,
            urgency_level=urgency_level,
            escalated_at=escalated_at
        )

        # Update advisor performance metrics
        graph_manager.update_advisor_escalation_metrics(from_advisor)

        logger.info(f"✅ Graph updated for workflow escalated: {workflow_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle WORKFLOW_ESCALATED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_issue_resolved(sender, **kwargs):
    """Handle ISSUE_RESOLVED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract resolution data
        issue_id = payload['issue_id']
        resolution_id = payload['resolution_id']
        resolved_by_advisor = payload['resolved_by_advisor']
        resolved_by_supervisor = payload.get('resolved_by_supervisor')
        resolution_method = payload['resolution_method']
        resolution_time_minutes = payload['resolution_time_minutes']
        customer_satisfaction = payload.get('customer_satisfaction')
        resolved_at = payload['resolved_at']

        # Create resolution node
        graph_manager.create_resolution(
            resolution_id=resolution_id,
            issue_id=issue_id,
            resolved_by_advisor=resolved_by_advisor,
            resolved_by_supervisor=resolved_by_supervisor,
            method=resolution_method,
            resolution_time_minutes=resolution_time_minutes,
            customer_satisfaction=customer_satisfaction,
            resolved_at=resolved_at
        )

        # Update advisor performance metrics
        graph_manager.update_advisor_resolution_metrics(
            advisor_id=resolved_by_advisor,
            resolution_time=resolution_time_minutes,
            satisfaction_score=customer_satisfaction
        )

        if resolved_by_supervisor:
            graph_manager.update_supervisor_metrics(resolved_by_supervisor)

        logger.info(f"✅ Graph updated for issue resolved: {issue_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle ISSUE_RESOLVED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_document_acknowledged(sender, **kwargs):
    """Handle DOCUMENT_ACKNOWLEDGED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract document data
        document_id = payload['document_id']
        customer_id = payload['customer_id']
        document_type = payload['document_type']
        sent_at = payload['sent_at']
        acknowledged_at = payload['acknowledged_at']
        acknowledgment_method = payload['acknowledgment_method']

        # Create document acknowledgment
        graph_manager.create_document_acknowledgment(
            document_id=document_id,
            customer_id=customer_id,
            document_type=document_type,
            sent_at=sent_at,
            acknowledged_at=acknowledged_at,
            method=acknowledgment_method
        )

        # Update customer engagement metrics
        graph_manager.update_customer_engagement_metrics(customer_id)

        logger.info(f"✅ Graph updated for document acknowledged: {document_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle DOCUMENT_ACKNOWLEDGED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_customer_events(sender, **kwargs):
    """Handle customer creation and update events."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract customer data
        customer_id = payload['customer_id']

        # Create or update customer with any additional data
        customer_data = {k: v for k, v in payload.items() if k != 'customer_id'}
        graph_manager.create_or_update_customer(customer_id, **customer_data)

        logger.info(f"✅ Graph updated for customer event: {customer_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle customer event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_advisor_events(sender, **kwargs):
    """Handle advisor assignment and performance events."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_graph_manager()

        # Extract advisor data
        advisor_id = payload['advisor_id']

        # Create or update advisor with any additional data
        advisor_data = {k: v for k, v in payload.items() if k != 'advisor_id'}
        graph_manager.create_or_update_advisor(advisor_id, **advisor_data)

        logger.info(f"✅ Graph updated for advisor event: {advisor_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle advisor event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def initialize_graph_handlers():
    """
    Initialize all graph event handlers.

    This function ensures all handlers are registered with the event system.
    Call this during application startup.
    """
    try:
        # Register transcript handler
        subscribe_to_events(
            [EventType.TRANSCRIPT_CREATED],
            handle_transcript_created,
            "transcript_handler"
        )

        # Register analysis handler
        subscribe_to_events(
            [EventType.ANALYSIS_COMPLETED],
            handle_analysis_completed,
            "analysis_handler"
        )

        # Register escalation handler
        subscribe_to_events(
            [EventType.WORKFLOW_ESCALATED],
            handle_workflow_escalated,
            "escalation_handler"
        )

        # Register resolution handler
        subscribe_to_events(
            [EventType.ISSUE_RESOLVED],
            handle_issue_resolved,
            "resolution_handler"
        )

        # Register document handler
        subscribe_to_events(
            [EventType.DOCUMENT_ACKNOWLEDGED],
            handle_document_acknowledged,
            "document_handler"
        )

        # Register customer handler
        subscribe_to_events(
            [EventType.CUSTOMER_CREATED, EventType.CUSTOMER_UPDATED],
            handle_customer_events,
            "customer_handler"
        )

        # Register advisor handler
        subscribe_to_events(
            [EventType.ADVISOR_ASSIGNED, EventType.ADVISOR_PERFORMANCE_UPDATED],
            handle_advisor_events,
            "advisor_handler"
        )

        logger.info("✅ Graph event handlers initialized")
        logger.info("📊 Registered handlers for:")
        logger.info("  - TRANSCRIPT_CREATED")
        logger.info("  - ANALYSIS_COMPLETED")
        logger.info("  - WORKFLOW_ESCALATED")
        logger.info("  - ISSUE_RESOLVED")
        logger.info("  - DOCUMENT_ACKNOWLEDGED")
        logger.info("  - CUSTOMER_CREATED/UPDATED")
        logger.info("  - ADVISOR_ASSIGNED/PERFORMANCE_UPDATED")

        return True

    except Exception as e:
        logger.error(f"Failed to initialize graph handlers: {e}")
        raise


# Export for easy access
__all__ = [
    'handle_transcript_created',
    'handle_analysis_completed',
    'handle_workflow_escalated',
    'handle_issue_resolved',
    'handle_document_acknowledged',
    'handle_customer_events',
    'handle_advisor_events',
    'initialize_graph_handlers'
]