"""
Case Service - Business logic for case management operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
from ..storage.transcript_store import TranscriptStore
from ..storage.analysis_store import AnalysisStore
from ..storage.action_plan_store import ActionPlanStore


class CaseService:
    """Service for case management operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.transcript_store = TranscriptStore(db_path)
        self.analysis_store = AnalysisStore(db_path)
        self.plan_store = ActionPlanStore(db_path)
    
    async def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all cases (aggregated view of transcripts with related data)."""
        transcripts = self.transcript_store.get_all()
        if limit:
            transcripts = transcripts[:limit]
        
        cases = []
        for transcript in transcripts:
            case = await self._build_case_view(transcript)
            cases.append(case)
        
        return cases
    
    async def get_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Get case by ID (transcript ID)."""
        transcript = self.transcript_store.get_by_id(case_id)
        if not transcript:
            return None
        
        return await self._build_case_view(transcript)
    
    async def get_transcripts(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all transcripts for a case."""
        # For now, case_id maps to transcript_id (1:1 relationship)
        transcript = self.transcript_store.get_by_id(case_id)
        if not transcript:
            return []
        
        return [transcript.to_dict()]
    
    async def get_analyses(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all analyses for a case."""
        analyses = self.analysis_store.search_by_transcript(case_id)
        return [a.to_dict() for a in analyses]
    
    async def get_plans(self, case_id: str) -> List[Dict[str, Any]]:
        """Get all action plans for a case."""
        # Find analyses for this case first
        analyses = self.analysis_store.search_by_transcript(case_id)
        
        plans = []
        for analysis in analyses:
            analysis_plans = self.plan_store.search_by_analysis(analysis.id)
            plans.extend([p.to_dict() for p in analysis_plans])
        
        return plans
    
    async def search(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search cases with various parameters."""
        customer = search_params.get("customer")
        status = search_params.get("status")
        priority = search_params.get("priority")
        date_range = search_params.get("date_range")
        
        # Start with transcript search
        if customer:
            transcripts = self.transcript_store.search_by_customer(customer)
        else:
            transcripts = self.transcript_store.get_all()
        
        cases = []
        for transcript in transcripts:
            case = await self._build_case_view(transcript)
            
            # Apply additional filters
            if status and case.get("status") != status:
                continue
            if priority and case.get("priority") != priority:
                continue
            if date_range:
                # Apply date filtering logic
                pass
            
            cases.append(case)
        
        return cases
    
    async def _build_case_view(self, transcript) -> Dict[str, Any]:
        """Build comprehensive case view from transcript and related data."""
        # Get related analyses
        analyses = self.analysis_store.search_by_transcript(transcript.id)
        
        # Get related action plans
        plans = []
        for analysis in analyses:
            analysis_plans = self.plan_store.search_by_analysis(analysis.id)
            plans.extend(analysis_plans)
        
        # Determine case status based on workflow progress
        case_status = "new"
        if analyses:
            case_status = "analyzed"
        if plans:
            if any(getattr(p, 'status', 'pending') == 'completed' for p in plans):
                case_status = "resolved"
            elif any(getattr(p, 'status', 'pending') == 'executing' for p in plans):
                case_status = "in_progress"
            elif any(getattr(p, 'status', 'pending') == 'approved' for p in plans):
                case_status = "approved"
            else:
                case_status = "planning"
        
        # Determine priority from sentiment and urgency
        priority = "medium"
        if hasattr(transcript, 'urgency'):
            priority = transcript.urgency
        elif analyses:
            # Use highest urgency from analyses
            urgencies = [getattr(a, 'urgency', 'medium') for a in analyses]
            if 'high' in urgencies:
                priority = "high"
            elif 'low' in urgencies:
                priority = "low"
        
        # Build case summary
        case = {
            "case_id": transcript.id,
            "customer_id": getattr(transcript, 'customer_id', 'Unknown'),
            "status": case_status,
            "priority": priority,
            "created_at": getattr(transcript, 'created_at', None),
            "updated_at": getattr(transcript, 'updated_at', None),
            "summary": {
                "transcript_count": 1,
                "analysis_count": len(analyses),
                "plan_count": len(plans),
                "topic": getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown')),
                "sentiment": getattr(transcript, 'sentiment', 'Unknown')
            },
            "latest_activity": {
                "type": "plan_execution" if any(getattr(p, 'status') == 'executing' for p in plans) else
                        "plan_approved" if any(getattr(p, 'status') == 'approved' for p in plans) else
                        "analysis_completed" if analyses else "transcript_created",
                "timestamp": max([getattr(p, 'updated_at', getattr(transcript, 'created_at', '')) for p in plans] + 
                                [getattr(a, 'updated_at', getattr(transcript, 'created_at', '')) for a in analyses] + 
                                [getattr(transcript, 'created_at', '')], default='')
            }
        }
        
        return case
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get case management statistics and metrics."""
        transcripts = self.transcript_store.get_all()
        
        if not transcripts:
            return {
                "total_cases": 0,
                "new_cases": 0,
                "analyzed_cases": 0,
                "planning_cases": 0,
                "approved_cases": 0,
                "in_progress_cases": 0,
                "resolved_cases": 0,
                "priority_distribution": {},
                "avg_resolution_time": 0.0
            }
        
        total = len(transcripts)
        
        # Build case views and count statuses
        status_counts = {
            "new": 0,
            "analyzed": 0,
            "planning": 0,
            "approved": 0,
            "in_progress": 0,
            "resolved": 0
        }
        
        priority_distribution = {}
        
        for transcript in transcripts:
            case = await self._build_case_view(transcript)
            status = case.get("status", "new")
            priority = case.get("priority", "medium")
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
        
        return {
            "total_cases": total,
            "new_cases": status_counts["new"],
            "analyzed_cases": status_counts["analyzed"],
            "planning_cases": status_counts["planning"],
            "approved_cases": status_counts["approved"],
            "in_progress_cases": status_counts["in_progress"],
            "resolved_cases": status_counts["resolved"],
            "priority_distribution": priority_distribution,
            "resolution_rate": status_counts["resolved"] / total if total > 0 else 0.0
        }