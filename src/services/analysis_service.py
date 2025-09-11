"""
Analysis Service - Business logic for analysis operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
from ..storage.analysis_store import AnalysisStore
from ..analyzers.call_analyzer import CallAnalyzer


class AnalysisService:
    """Service for analysis operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.store = AnalysisStore(db_path)
        self.analyzer = CallAnalyzer(api_key=api_key)
    
    async def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all analyses with optional limit."""
        analyses = self.store.get_all()
        if limit:
            analyses = analyses[:limit]
        return [a.to_dict() for a in analyses]
    
    async def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new analysis from transcript."""
        transcript_id = request_data.get("transcript_id")
        if not transcript_id:
            raise ValueError("transcript_id is required")
        
        # Get transcript from store
        from ..storage.transcript_store import TranscriptStore
        transcript_store = TranscriptStore(self.db_path)
        transcript = transcript_store.get_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Generate analysis using call analyzer
        analysis_result = self.analyzer.analyze(transcript)
        
        # Add metadata
        analysis_result["transcript_id"] = transcript_id
        analysis_result["analysis_id"] = f"ANALYSIS_{transcript_id}_{len(str(analysis_result))}"[:20]
        
        # Store if requested
        should_store = request_data.get("store", True)
        if should_store:
            self.store.store(analysis_result)
        
        return analysis_result
    
    async def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID."""
        analysis = self.store.get_by_id(analysis_id)
        if not analysis:
            return None
        return analysis.to_dict()
    
    async def delete(self, analysis_id: str) -> bool:
        """Delete analysis by ID."""
        return self.store.delete(analysis_id)
    
    async def search_by_transcript(self, transcript_id: str) -> List[Dict[str, Any]]:
        """Search analyses by transcript ID."""
        results = self.store.search_by_transcript(transcript_id)
        return [a.to_dict() for a in results]
    
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