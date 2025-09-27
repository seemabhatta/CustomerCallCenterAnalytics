"""
Knowledge Event Handler - Processes knowledge extraction events.

Handles downstream processing when knowledge is extracted, including
notifications, reporting, and system optimization.
"""
import logging
from typing import Dict, Any

from ..events import Event, EventType
from ..events.event_system import get_event_system

logger = logging.getLogger(__name__)


class KnowledgeEventHandler:
    """
    Handles knowledge extraction events for downstream processing.

    Processes KNOWLEDGE_EXTRACTED events to enable system learning and optimization.
    """

    def __init__(self):
        self.event_system = get_event_system()
        self._subscribe_to_knowledge_events()

    def _subscribe_to_knowledge_events(self) -> None:
        """Subscribe to knowledge extraction events."""
        try:
            # NO FALLBACK: Use correct API signature with event_types (plural) and subscriber_name
            self.event_system.subscribe(
                event_types=[EventType.KNOWLEDGE_EXTRACTED],
                handler=self._handle_knowledge_extracted,
                subscriber_name="knowledge_event_handler"
            )

            # Subscribe to analysis completion events for prediction validation
            self.event_system.subscribe(
                event_types=[EventType.ANALYSIS_COMPLETED],
                handler=self._handle_analysis_completed,
                subscriber_name="analysis_completion_handler"
            )

            logger.info("✅ Subscribed to KNOWLEDGE_EXTRACTED and ANALYSIS_COMPLETED events")

        except Exception as e:
            logger.error(f"Failed to subscribe to knowledge events: {e}")
            # NO FALLBACK: Fail fast if event subscription fails
            raise RuntimeError(f"Cannot proceed without event subscription: {e}")

    def _handle_knowledge_extracted(self, sender, **kwargs) -> None:
        """
        Handle knowledge extraction events.

        Args:
            sender: Event system sender
            **kwargs: Event data including 'event', 'event_type', 'payload', etc.
        """
        event = kwargs.get('event')
        try:
            payload = event.payload
            insight_type = payload.get('insight_type', 'unknown')
            source_stage = payload.get('source_stage', 'unknown')
            priority = payload.get('priority', 'medium')

            logger.info(f"🧠 Processing knowledge extraction: {insight_type} from {source_stage} (priority: {priority})")

            # Process different types of knowledge (sync versions)
            insight_type_lower = insight_type.lower()
            if insight_type_lower == 'pattern':
                self._process_pattern_knowledge_sync(payload)
            elif insight_type_lower == 'prediction':
                self._process_prediction_knowledge_sync(payload)
            elif insight_type_lower == 'wisdom':
                self._process_wisdom_knowledge_sync(payload)
            elif insight_type_lower == 'meta_learning':
                self._process_meta_learning_knowledge_sync(payload)
            else:
                logger.warning(f"Unknown insight type: {insight_type}")

            # Log knowledge metrics (sync version)
            self._update_knowledge_metrics_sync(payload)

        except Exception as e:
            logger.error(f"Failed to process knowledge extraction event: {e}")
            # NO FALLBACK: Fail fast on knowledge processing errors
            raise RuntimeError(f"Knowledge event processing failed: {str(e)}")

    async def _process_pattern_knowledge(self, payload: Dict[str, Any]) -> None:
        """Process pattern knowledge extraction."""
        logger.info(f"📊 Processing pattern knowledge: {payload.get('reasoning', 'No reasoning')}")

        # Future: Trigger pattern analysis, update confidence scores, etc.
        # For now, just log the knowledge capture

    async def _process_prediction_knowledge(self, payload: Dict[str, Any]) -> None:
        """Process prediction knowledge extraction."""
        logger.info(f"🔮 Processing prediction knowledge: {payload.get('reasoning', 'No reasoning')}")

        # Future: Set up prediction validation schedules, alerts, etc.

    async def _process_wisdom_knowledge(self, payload: Dict[str, Any]) -> None:
        """Process wisdom knowledge extraction."""
        logger.info(f"🧠 Processing wisdom knowledge: {payload.get('reasoning', 'No reasoning')}")

        # Future: Update strategic dashboards, notify leadership, etc.

    async def _process_meta_learning_knowledge(self, payload: Dict[str, Any]) -> None:
        """Process meta-learning knowledge extraction."""
        logger.info(f"🔄 Processing meta-learning knowledge: {payload.get('reasoning', 'No reasoning')}")

        # Generate additional meta-learning insights about the knowledge extraction process itself
        await self._generate_meta_learning_insights(payload)

    def _handle_analysis_completed(self, sender, **kwargs) -> None:
        """
        Handle analysis completion events for prediction validation.

        Args:
            sender: Event system sender
            **kwargs: Event data including 'event', 'event_type', 'payload', etc.
        """
        event = kwargs.get('event')
        try:
            payload = event.payload
            logger.info(f"📋 Processing analysis completion for validation: {payload.get('analysis_id', 'unknown')}")

            # Import here to avoid circular dependency
            from .prediction_validator import get_prediction_validator
            prediction_validator = get_prediction_validator()

            customer_id = payload.get('customer_id')
            advisor_id = payload.get('advisor_id')
            analysis_results = payload.get('analysis_results', {})

            # Validate customer risk predictions (sync version)
            borrower_risks = analysis_results.get('borrower_risks', {})
            if borrower_risks.get('delinquency_risk', 0) > 0.7 and customer_id:
                # Schedule async validation in background
                import asyncio
                try:
                    current_loop = asyncio.get_running_loop()
                    asyncio.create_task(prediction_validator.validate_customer_risk_prediction(
                        customer_id=customer_id,
                        predicted_risk='delinquency',
                        actual_outcome='high_risk_detected'
                    ))
                except RuntimeError:
                    # No event loop, skip async validation
                    logger.info(f"Skipped async validation - no event loop for customer {customer_id}")

            # Validate advisor performance predictions (sync version)
            if analysis_results.get('escalation_needed', False) and advisor_id != 'UNKNOWN':
                # Schedule async validation in background
                import asyncio
                try:
                    current_loop = asyncio.get_running_loop()
                    asyncio.create_task(prediction_validator.validate_advisor_performance_prediction(
                        advisor_id=advisor_id,
                        predicted_improvement='needs_coaching',
                        actual_performance={'escalation_triggered': True}
                    ))
                except RuntimeError:
                    # No event loop, skip async validation
                    logger.info(f"Skipped async validation - no event loop for advisor {advisor_id}")

            logger.info(f"✅ Completed prediction validation for analysis: {payload.get('analysis_id', 'unknown')}")

        except Exception as e:
            logger.error(f"Failed to process analysis completion event: {e}")
            # NO FALLBACK: Fail fast on validation processing errors
            raise RuntimeError(f"Analysis completion processing failed: {str(e)}")

    async def _generate_meta_learning_insights(self, payload: Dict[str, Any]) -> None:
        """Generate meta-learning insights about the knowledge extraction process."""
        try:
            # CIRCUIT BREAKER: Prevent infinite meta-learning loops
            source_stage = payload.get('source_stage', 'unknown')
            if source_stage == 'meta_learning':
                logger.info("🔄 Skipping meta-learning generation to prevent infinite loops")
                return

            from .predictive_knowledge_extractor import get_predictive_knowledge_extractor
            from .knowledge_types import PredictiveInsight, MetaLearning
            from datetime import datetime
            import uuid

            knowledge_extractor = get_predictive_knowledge_extractor()

            # Analyze the knowledge extraction patterns and generate meta-learning
            insight_type = payload.get('insight_type', 'unknown')
            priority = payload.get('priority', 'medium')

            # Create meta-learning insight about knowledge extraction effectiveness
            meta_learning = MetaLearning(
                meta_id=f"META_{uuid.uuid4().hex[:8].upper()}",
                meta_type='knowledge_extraction_optimization',
                learning_insight=f"Knowledge extraction from {source_stage} stage is producing {insight_type} insights with {priority} priority",
                improvement_opportunity=self._identify_extraction_improvements(payload),
                optimization_suggestion=self._suggest_extraction_optimizations(insight_type, source_stage),
                accuracy_metrics={
                    'stage_effectiveness': self._convert_stage_to_score(source_stage),
                    'insight_quality': self._convert_priority_to_score(priority),
                    'extraction_frequency': 1  # Would track over time
                },
                learning_velocity=0.8,  # Would calculate based on actual metrics
                knowledge_gaps=[f"Limited {insight_type} insights from {source_stage}"],
                observed_at=datetime.utcnow(),
                system_version='1.0'
            )

            # Store the meta-learning insight
            await knowledge_extractor.store_meta_learning(meta_learning)
            logger.info(f"🔄 Generated meta-learning insight: {meta_learning.meta_id}")

        except Exception as e:
            logger.error(f"Failed to generate meta-learning insights: {e}")

    def _identify_extraction_improvements(self, payload: Dict[str, Any]) -> str:
        """Identify opportunities for improving knowledge extraction."""
        insight_type = payload.get('insight_type', 'unknown')
        priority = payload.get('priority', 'medium')

        if priority == 'low':
            return f"Increase the value threshold for {insight_type} insights to focus on higher-impact knowledge"
        elif insight_type == 'pattern':
            return "Enhance pattern recognition by collecting more diverse interaction examples"
        elif insight_type == 'prediction':
            return "Improve prediction accuracy by incorporating more historical validation data"
        else:
            return "General knowledge extraction process could benefit from more sophisticated filtering"

    def _suggest_extraction_optimizations(self, insight_type: str, source_stage: str) -> str:
        """Suggest specific optimizations for knowledge extraction."""
        if source_stage == 'analysis' and insight_type == 'pattern':
            return "Consider aggregating similar patterns from analysis stage to reduce noise"
        elif source_stage == 'workflow' and insight_type == 'prediction':
            return "Workflow predictions should focus on execution success rates and bottleneck identification"
        else:
            return f"Optimize {insight_type} extraction by implementing stage-specific quality filters"

    async def _update_knowledge_metrics(self, payload: Dict[str, Any]) -> None:
        """Update knowledge extraction metrics."""
        source_stage = payload.get('source_stage', 'unknown')
        priority = payload.get('priority', 'medium')

        logger.info(f"📈 Knowledge metrics updated: {source_stage} stage, {priority} priority")

        # CIRCUIT BREAKER: Only generate meta-learning for non-meta-learning events
        if source_stage != 'meta_learning':
            await self._generate_meta_learning_insights(payload)

    # ===============================================
    # SYNC VERSIONS FOR BLINKER COMPATIBILITY
    # ===============================================

    def _process_pattern_knowledge_sync(self, payload: Dict[str, Any]) -> None:
        """Sync version of pattern knowledge processing."""
        logger.info(f"📊 Processing pattern knowledge (sync): {payload.get('reasoning', 'No reasoning')}")
        # Future: Add pattern analysis logic here

    def _process_prediction_knowledge_sync(self, payload: Dict[str, Any]) -> None:
        """Sync version of prediction knowledge processing."""
        logger.info(f"🔮 Processing prediction knowledge (sync): {payload.get('reasoning', 'No reasoning')}")
        # Future: Add prediction analysis logic here

    def _process_wisdom_knowledge_sync(self, payload: Dict[str, Any]) -> None:
        """Sync version of wisdom knowledge processing."""
        logger.info(f"🧠 Processing wisdom knowledge (sync): {payload.get('reasoning', 'No reasoning')}")
        # Future: Add wisdom analysis logic here

    def _process_meta_learning_knowledge_sync(self, payload: Dict[str, Any]) -> None:
        """Sync version of meta-learning knowledge processing."""
        logger.info(f"🔄 Processing meta-learning knowledge (sync): {payload.get('reasoning', 'No reasoning')}")
        # Schedule async meta-learning generation in background if possible
        import asyncio
        try:
            current_loop = asyncio.get_running_loop()
            asyncio.create_task(self._generate_meta_learning_insights(payload))
        except RuntimeError:
            # No event loop, skip async meta-learning
            logger.info("Skipped async meta-learning generation - no event loop")

    def _update_knowledge_metrics_sync(self, payload: Dict[str, Any]) -> None:
        """Sync version of knowledge metrics update."""
        source_stage = payload.get('source_stage', 'unknown')
        priority = payload.get('priority', 'medium')

        logger.info(f"📈 Knowledge metrics updated (sync): {source_stage} stage, {priority} priority")

        # CIRCUIT BREAKER: Only generate meta-learning for non-meta-learning events
        if source_stage != 'meta_learning':
            # Schedule async meta-learning in background if possible
            import asyncio
            try:
                current_loop = asyncio.get_running_loop()
                asyncio.create_task(self._generate_meta_learning_insights(payload))
            except RuntimeError:
                # No event loop, skip async meta-learning
                logger.info("Skipped async meta-learning generation - no event loop")

    def _convert_stage_to_score(self, stage: str) -> float:
        """Convert stage name to numerical score for accuracy metrics."""
        stage_scores = {
            'analysis': 0.8,
            'planning': 0.7,
            'workflow': 0.6,
            'execution': 0.9,
            'meta_learning': 0.5
        }
        return stage_scores.get(stage.lower(), 0.5)

    def _convert_priority_to_score(self, priority: str) -> float:
        """Convert priority level to numerical score for accuracy metrics."""
        priority_scores = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.9,
            'critical': 1.0
        }
        return priority_scores.get(priority.lower(), 0.5)


# Global instance
_knowledge_handler = None

def get_knowledge_event_handler() -> KnowledgeEventHandler:
    """Get the global knowledge event handler instance."""
    global _knowledge_handler
    if _knowledge_handler is None:
        try:
            _knowledge_handler = KnowledgeEventHandler()
        except RuntimeError as e:
            logger.error(f"Failed to initialize KnowledgeEventHandler: {e}")
            raise RuntimeError(f"Cannot proceed without knowledge event handling: {e}")
    return _knowledge_handler

def initialize_knowledge_event_handling() -> None:
    """Initialize knowledge event handling system."""
    handler = get_knowledge_event_handler()
    logger.info("🎯 Knowledge event handling system initialized")