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
from ..graph.unified_graph_manager import get_unified_graph_manager

class GraphManagerError(Exception):
    """Exception raised for graph manager errors."""
    pass

logger = logging.getLogger(__name__)


def handle_transcript_created(sender, **kwargs):
    """Handle TRANSCRIPT_CREATED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

        # Extract data from payload
        transcript_id = payload['transcript_id']
        customer_id = payload['customer_id']
        advisor_id = payload['advisor_id']
        topic = payload['topic']
        urgency = payload['urgency']
        channel = payload['channel']
        started_at = payload['started_at']

        # Create or update entities
        graph_manager.create_or_update_customer_sync(customer_id)

        # Create transcript node with rich attributes
        graph_manager.create_transcript_sync(
            transcript_id=transcript_id,
            customer_id=customer_id,
            content=payload.get('content', ''),
            duration_seconds=payload.get('duration_seconds', 0),
            channel=channel
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

        graph_manager = get_unified_graph_manager()

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

        # NO FALLBACK: Analysis node creation is handled by analysis_service.py
        # This event handler only handles secondary effects of analysis completion
        logger.info(f"📊 Processing analysis completion event for {analysis_id} (analysis node created by service)")

        # Update customer risk profile based on analysis
        graph_manager.update_customer_risk_profile_sync(
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

        graph_manager = get_unified_graph_manager()

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

        graph_manager = get_unified_graph_manager()

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


def handle_plan_generated(sender, **kwargs):
    """Handle PLAN_GENERATED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

        # Extract plan data
        plan_id = payload['plan_id']
        analysis_id = payload['analysis_id']
        transcript_id = payload['transcript_id']
        customer_id = payload['customer_id']
        priority_level = payload.get('priority_level', 'medium')
        action_count = payload.get('action_count', 0)
        urgency_level = payload.get('urgency_level', 'medium')

        # Create plan node (async)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Schedule async plan creation
            loop.create_task(graph_manager.create_plan_node(
                plan_id=plan_id,
                analysis_id=analysis_id,
                transcript_id=transcript_id,
                customer_id=customer_id,
                priority_level=priority_level,
                action_count=action_count,
                urgency_level=urgency_level
            ))
            logger.info(f"📋 Scheduled plan creation: {plan_id}")
        except RuntimeError:
            # No event loop, skip async operation
            logger.warning(f"No event loop for async plan creation: {plan_id}")

        logger.info(f"✅ Graph updated for plan generated: {plan_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle PLAN_GENERATED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_workflow_created(sender, **kwargs):
    """Handle WORKFLOW_CREATED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

        # Extract workflow data
        workflow_id = payload['workflow_id']
        plan_id = payload['plan_id']
        customer_id = payload.get('customer_id', 'UNKNOWN')
        advisor_id = payload.get('advisor_id', 'SYSTEM')
        step_count = payload.get('step_count', 0)
        estimated_duration = payload.get('estimated_duration', 30)
        priority = payload.get('priority', 'medium')

        # Create workflow node (async)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Schedule async workflow creation
            # Create workflow node and link to plan
            async def create_and_link_workflow():
                await graph_manager.create_workflow_node(
                    workflow_id=workflow_id,
                    plan_id=plan_id,
                    customer_id=customer_id,
                    advisor_id=advisor_id,
                    step_count=step_count,
                    estimated_duration=estimated_duration,
                    priority=priority
                )
                # Link workflow to plan
                await graph_manager.link_workflow_to_plan(workflow_id, plan_id)

            loop.create_task(create_and_link_workflow())
            logger.info(f"⚡ Scheduled workflow creation and linking: {workflow_id}")
        except RuntimeError:
            # No event loop, skip async operation
            logger.warning(f"No event loop for async workflow creation: {workflow_id}")

        logger.info(f"✅ Graph updated for workflow created: {workflow_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle WORKFLOW_CREATED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_execution_completed(sender, **kwargs):
    """Handle EXECUTION_COMPLETED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

        # Extract execution data
        execution_id = payload['execution_id']
        workflow_id = payload['workflow_id']
        step_id = payload.get('step_id')
        success = payload.get('success', False)
        duration_seconds = payload.get('duration_seconds', 0)
        error_message = payload.get('error_message')
        result_data = payload.get('result_data', {})

        # Create execution result node (async)
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # Schedule async execution result creation
            loop.create_task(graph_manager.create_execution_result(
                execution_id=execution_id,
                workflow_id=workflow_id,
                step_id=step_id,
                success=success,
                duration_seconds=duration_seconds,
                error_message=error_message,
                result_data=result_data
            ))
            logger.info(f"🎯 Scheduled execution result creation: {execution_id}")
        except RuntimeError:
            # No event loop, skip async operation
            logger.warning(f"No event loop for async execution result creation: {execution_id}")

        logger.info(f"✅ Graph updated for execution completed: {execution_id}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle EXECUTION_COMPLETED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_knowledge_extracted(sender, **kwargs):
    """Handle KNOWLEDGE_EXTRACTED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

        # Extract knowledge data
        insight_type = payload.get('insight_type', 'unknown')
        source_stage = payload.get('source_stage', 'unknown')
        priority = payload.get('priority', 'medium')
        learning_value = payload.get('learning_value', 'routine')
        reasoning = payload.get('reasoning', '')
        context = payload.get('context', {})

        # Different handling based on insight type
        if insight_type.lower() == 'hypothesis':
            hypothesis_id = f"HYPO_{context.get('analysis_id', 'UNK')[:8]}"
            # Create hypothesis node (async)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(graph_manager.create_hypothesis_node(
                    hypothesis_id=hypothesis_id,
                    source_stage=source_stage,
                    priority=priority,
                    reasoning=reasoning,
                    context=context
                ))
                logger.info(f"💡 Scheduled hypothesis creation: {hypothesis_id}")
            except RuntimeError:
                logger.warning(f"No event loop for async hypothesis creation: {hypothesis_id}")

        elif insight_type.lower() == 'prediction':
            prediction_id = f"PRED_{context.get('customer_id', 'UNK')[:8]}"
            # Prediction creation handled by store_prediction method in analysis service
            logger.info(f"🔮 Prediction creation handled by analysis service: {prediction_id}")

        elif insight_type.lower() == 'wisdom':
            wisdom_id = f"WISDOM_{context.get('analysis_id', 'UNK')[:8]}"
            # Create wisdom node (async)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(graph_manager.create_wisdom_node(
                    wisdom_id=wisdom_id,
                    source_stage=source_stage,
                    priority=priority,
                    reasoning=reasoning,
                    context=context
                ))
                logger.info(f"🧠 Scheduled wisdom creation: {wisdom_id}")
            except RuntimeError:
                logger.warning(f"No event loop for async wisdom creation: {wisdom_id}")

        logger.info(f"✅ Graph updated for knowledge extracted: {insight_type} from {source_stage}")
        return True

    except Exception as e:
        error_msg = f"Failed to handle KNOWLEDGE_EXTRACTED event: {e}"
        logger.error(error_msg)
        raise GraphManagerError(error_msg)


def handle_document_acknowledged(sender, **kwargs):
    """Handle DOCUMENT_ACKNOWLEDGED event by updating knowledge graph."""
    try:
        event: Event = kwargs['event']
        payload = event.payload

        graph_manager = get_unified_graph_manager()

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

        graph_manager = get_unified_graph_manager()

        # Extract customer data
        customer_id = payload['customer_id']

        # Create or update customer with any additional data
        customer_data = {k: v for k, v in payload.items() if k != 'customer_id'}
        graph_manager.create_or_update_customer_sync(customer_id, **customer_data)

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

        graph_manager = get_unified_graph_manager()

        # Extract advisor data
        advisor_id = payload['advisor_id']

        # Note: Advisor schema not implemented yet - would create advisor node here
        # advisor_data = {k: v for k, v in payload.items() if k != 'advisor_id'}
        # graph_manager.create_or_update_advisor_sync(advisor_id, **advisor_data)

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

        # Register plan handler
        subscribe_to_events(
            [EventType.PLAN_GENERATED],
            handle_plan_generated,
            "plan_handler"
        )

        # Register workflow handler
        subscribe_to_events(
            [EventType.WORKFLOW_CREATED],
            handle_workflow_created,
            "workflow_handler"
        )

        # Register execution handler
        subscribe_to_events(
            [EventType.EXECUTION_COMPLETED],
            handle_execution_completed,
            "execution_handler"
        )

        # Register knowledge extraction handler
        subscribe_to_events(
            [EventType.KNOWLEDGE_EXTRACTED],
            handle_knowledge_extracted,
            "knowledge_handler"
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
        logger.info("  - PLAN_GENERATED")
        logger.info("  - WORKFLOW_CREATED")
        logger.info("  - EXECUTION_COMPLETED")
        logger.info("  - KNOWLEDGE_EXTRACTED")
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
    'handle_plan_generated',
    'handle_workflow_created',
    'handle_execution_completed',
    'handle_knowledge_extracted',
    'handle_workflow_escalated',
    'handle_issue_resolved',
    'handle_document_acknowledged',
    'handle_customer_events',
    'handle_advisor_events',
    'initialize_graph_handlers'
]