"""
Analysis Service - Business logic for analysis operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
import logging
import uuid
from datetime import datetime
from ..storage.analysis_store import AnalysisStore
from ..call_center_agents.call_analysis_agent import CallAnalysisAgent

logger = logging.getLogger(__name__)
from ..infrastructure.events import (
    create_analysis_event,
    publish_event
)
from ..infrastructure.graph.predictive_knowledge_extractor import get_predictive_knowledge_extractor


class AnalysisService:
    """Service for analysis operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.store = AnalysisStore(db_path)
        self.analyzer = CallAnalysisAgent()
    
    async def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all analyses with optional limit."""
        analyses = self.store.get_all()
        if limit:
            analyses = analyses[:limit]
        # NO FALLBACK: Handle both object and dict types properly
        result = []
        for a in analyses:
            if hasattr(a, 'to_dict'):
                result.append(a.to_dict())  # Object with to_dict method
            elif isinstance(a, dict):
                result.append(a)  # Already a dictionary
            else:
                # Fail fast if unexpected type
                raise ValueError(f"Unexpected analysis type: {type(a)}")
        return result
    
    async def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new analysis from transcript."""
        # Set up tracing for analysis creation
        from src.infrastructure.telemetry import set_span_attributes, add_span_event
        transcript_id = request_data.get("transcript_id")
        if not transcript_id:
            raise ValueError("transcript_id is required")
        
        set_span_attributes(transcript_id=transcript_id, operation="create_analysis")
        add_span_event("analysis.creation_started", transcript_id=transcript_id)
        
        # Get transcript from store
        add_span_event("analysis.fetching_transcript", transcript_id=transcript_id)
        from ..storage.transcript_store import TranscriptStore
        transcript_store = TranscriptStore(self.db_path)
        transcript = transcript_store.get_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        message_count = len(transcript.messages) if hasattr(transcript, 'messages') else 0
        add_span_event("analysis.transcript_loaded", transcript_id=transcript_id, message_count=message_count)
        
        # Query relevant patterns before analysis to influence LLM decisions
        from ..infrastructure.graph.predictive_knowledge_extractor import get_predictive_knowledge_extractor
        knowledge_extractor = get_predictive_knowledge_extractor()

        # Get context for pattern matching
        context = {
            'customer_id': getattr(transcript, 'customer_id', 'UNKNOWN'),
            'topic': getattr(transcript, 'topic', 'unknown'),
            'urgency': getattr(transcript, 'urgency', 'medium')
        }

        # Retrieve relevant patterns to inform analysis
        relevant_patterns = await knowledge_extractor.get_relevant_patterns(context)
        pattern_insights = [f"{p.title}: {p.description}" for p in relevant_patterns[:3]] if relevant_patterns else []

        add_span_event("analysis.patterns_retrieved", transcript_id=transcript_id, pattern_count=len(relevant_patterns))

        # Generate analysis using call analyzer with pattern context
        add_span_event("analysis.analyzer_started", transcript_id=transcript_id)
        analysis_result = self.analyzer.analyze(transcript, pattern_insights)
        result_keys = list(analysis_result.keys()) if isinstance(analysis_result, dict) else []
        add_span_event("analysis.analyzer_completed", transcript_id=transcript_id, result_keys_count=len(result_keys))
        
        # Add metadata
        analysis_result["transcript_id"] = transcript_id
        analysis_result["analysis_id"] = f"ANALYSIS_{transcript_id}_{len(str(analysis_result))}"[:20]
        
        # Store if requested
        should_store = request_data.get("store", True)
        if should_store:
            self.store.store(analysis_result)

            # Extract predictive knowledge and publish events
            customer_id = getattr(transcript, 'customer_id', 'UNKNOWN')

            # Extract predictive knowledge from analysis insights (NO FALLBACK)
            predictive_insight = analysis_result.get('predictive_insight')
            if predictive_insight:
                # Convert to PredictiveInsight object and extract knowledge
                from ..infrastructure.graph.knowledge_types import PredictiveInsight, InsightContent, CustomerContext
                from datetime import datetime

                # Create structured content
                content = InsightContent(
                    key=predictive_insight.get('content', {}).get('key', 'Analysis pattern'),
                    value=predictive_insight.get('content', {}).get('value', 'Insight from call analysis'),
                    confidence=predictive_insight.get('content', {}).get('confidence', 0.7),
                    impact=predictive_insight.get('content', {}).get('impact', 'Medium impact')
                )

                # Create structured customer context
                customer_context = CustomerContext(
                    customer_id=customer_id,
                    loan_type='mortgage',  # Default to mortgage for this use case
                    tenure='existing',  # Default to existing customer
                    risk_profile='standard'  # Default risk profile
                )

                insight = PredictiveInsight(
                    insight_type=predictive_insight.get('insight_type', 'pattern'),
                    priority=predictive_insight.get('priority', 'medium'),
                    content=content,
                    reasoning=predictive_insight.get('reasoning', 'Analysis insight'),
                    learning_value=predictive_insight.get('learning_value', 'routine'),
                    source_stage='analysis',
                    transcript_id=transcript_id,
                    customer_context=customer_context,
                    timestamp=datetime.utcnow().isoformat() + 'Z'
                )

                knowledge_extractor = get_predictive_knowledge_extractor()
                context = {
                    'transcript_id': transcript_id,
                    'customer_id': customer_id,
                    'analysis_id': analysis_result["analysis_id"]
                }
                # NO FALLBACK: If knowledge extraction fails, entire operation fails
                await knowledge_extractor.extract_knowledge(insight, context)
                add_span_event("analysis.knowledge_extracted", analysis_id=analysis_result["analysis_id"])

            # Schedule prediction validation via event system (avoids circular dependency)
            # Use existing factory function for consistency and proper event structure
            validation_event = create_analysis_event(
                analysis_id=analysis_result["analysis_id"],
                transcript_id=transcript_id,
                customer_id=customer_id,
                intent=analysis_result.get('primary_intent', 'unknown'),
                urgency=analysis_result.get('urgency_level', 'medium'),
                sentiment=analysis_result.get('borrower_sentiment', {}).get('overall', 'neutral'),
                risk_score=analysis_result.get('borrower_risks', {}).get('delinquency_risk', 0.5)
            )
            publish_event(validation_event)

            add_span_event("analysis.predictions_validated", analysis_id=analysis_result["analysis_id"])

            # Publish standard analysis event
            analysis_event = create_analysis_event(
                analysis_id=analysis_result["analysis_id"],
                transcript_id=transcript_id,
                customer_id=customer_id,
                intent=analysis_result.get('primary_intent', 'unknown'),
                urgency=analysis_result.get('urgency_level', 'medium'),
                sentiment=analysis_result.get('borrower_sentiment', {}).get('overall', 'neutral'),
                risk_score=analysis_result.get('borrower_risks', {}).get('delinquency_risk', 0.5)
            )
            publish_event(analysis_event)
            add_span_event("analysis.event_published", analysis_id=analysis_result["analysis_id"])

        return analysis_result
    
    async def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        analysis = self.store.get_by_id(analysis_id)
        if not analysis:
            return None

        # NO FALLBACK: Handle both object and dict types properly
        if hasattr(analysis, 'to_dict'):
            return analysis.to_dict()  # Object with to_dict method
        elif isinstance(analysis, dict):
            return analysis  # Already a dictionary
        else:
            # Fail fast if unexpected type
            raise ValueError(f"Unexpected analysis type: {type(analysis)}")

    async def get_by_transcript_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by transcript ID."""
        analysis = self.store.get_by_transcript_id(transcript_id)
        if not analysis:
            return None

        # NO FALLBACK: Handle both object and dict types properly
        if hasattr(analysis, 'to_dict'):
            return analysis.to_dict()  # Object with to_dict method
        elif isinstance(analysis, dict):
            return analysis  # Already a dictionary
        else:
            # Fail fast if unexpected type
            raise ValueError(f"Unexpected analysis type: {type(analysis)}")

    async def delete(self, analysis_id: str) -> bool:
        """Delete analysis by ID."""
        return self.store.delete(analysis_id)
    
    async def delete_all(self) -> int:
        """Delete all analyses - returns count of deleted analyses."""
        return self.store.delete_all()
    
    async def search_by_transcript(self, transcript_id: str) -> List[Dict[str, Any]]:
        """Search analyses by transcript ID."""
        results = self.store.search_by_transcript(transcript_id)
        # NO FALLBACK: Handle both object and dict types properly
        result = []
        for a in results:
            if hasattr(a, 'to_dict'):
                result.append(a.to_dict())  # Object with to_dict method
            elif isinstance(a, dict):
                result.append(a)  # Already a dictionary
            else:
                # Fail fast if unexpected type
                raise ValueError(f"Unexpected analysis type: {type(a)}")
        return result
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get analysis statistics and metrics."""
        analyses = self.store.get_all()
        
        if not analyses:
            return {
                "total_analyses": 0,
                "completed_analyses": 0,
                "avg_confidence_score": 0.0,
                "analysis_types": {},
                "sentiments": {},
                "urgency_levels": {},
                "processing_times": {}
            }
        
        total = len(analyses)
        completed = sum(1 for a in analyses if getattr(a, 'status', 'pending') == 'completed')
        
        # Collect statistics
        confidence_scores = []
        analysis_types = {}
        sentiments = {}
        urgency_levels = {}
        processing_times = []
        
        for analysis in analyses:
            # Confidence scores
            confidence = getattr(analysis, 'confidence_score', 0.0)
            if confidence > 0:
                confidence_scores.append(confidence)
            
            # Analysis types
            analysis_type = getattr(analysis, 'analysis_type', 'Unknown')
            analysis_types[analysis_type] = analysis_types.get(analysis_type, 0) + 1
            
            # Sentiments
            sentiment = getattr(analysis, 'sentiment', 'Unknown')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Urgency levels
            urgency = getattr(analysis, 'urgency', 'Unknown')
            urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            # Processing times
            processing_time = getattr(analysis, 'processing_time_seconds', 0)
            if processing_time > 0:
                processing_times.append(processing_time)
        
        return {
            "total_analyses": total,
            "completed_analyses": completed,
            "completion_rate": completed / total if total > 0 else 0.0,
            "avg_confidence_score": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "analysis_types": dict(sorted(analysis_types.items(), key=lambda x: x[1], reverse=True)),
            "sentiments": sentiments,
            "urgency_levels": urgency_levels,
            "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0.0
        }