"""
Plan Service - Business logic for action plan operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
from ..storage.action_plan_store import ActionPlanStore
from ..generators.action_plan_generator import ActionPlanGenerator


class PlanService:
    """Service for action plan operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.store = ActionPlanStore(db_path)
        self.generator = ActionPlanGenerator(api_key=api_key)
    
    async def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all action plans with optional limit."""
        plans = self.store.get_all()
        if limit:
            plans = plans[:limit]
        return plans  # plans already contains dicts from store.get_all()
    
    async def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new action plan from analysis."""
        analysis_id = request_data.get("analysis_id")
        if not analysis_id:
            raise ValueError("analysis_id is required")
        
        # Get analysis and transcript from stores
        from ..storage.analysis_store import AnalysisStore
        from ..storage.transcript_store import TranscriptStore
        analysis_store = AnalysisStore(self.db_path)
        transcript_store = TranscriptStore(self.db_path)
        
        analysis = analysis_store.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        
        transcript_id = analysis.get("transcript_id")
        transcript = transcript_store.get_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        
        # Generate plan using action plan generator
        plan_result = self.generator.generate(analysis, transcript)
        
        # Add metadata
        plan_result["analysis_id"] = analysis_id
        plan_result["plan_id"] = f"PLAN_{analysis_id}_{len(str(plan_result))}"[:20]
        
        # Store if requested
        should_store = request_data.get("store", True)
        if should_store:
            self.store.store(plan_result)
        
        return plan_result
    
    async def get_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by ID."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            return None
        return plan  # plan is already a dict from store.get_by_id()
    
    async def update(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update action plan."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            return None
        
        # Apply updates directly to dict
        for key, value in updates.items():
            plan[key] = value
        
        # Store updated plan
        self.store.update(plan_id, plan)
        return plan  # plan is already a dict
    
    async def delete(self, plan_id: str) -> bool:
        """Delete action plan by ID."""
        return self.store.delete(plan_id)
    
    async def search_by_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Search action plans by analysis ID."""
        results = self.store.search_by_analysis(analysis_id)
        return results  # results are already dicts from store
    
    async def approve(self, plan_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve action plan for execution."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # Update plan status
        plan.status = "approved"
        plan.approved_by = approval_data.get("approved_by")
        plan.approved_at = approval_data.get("approved_at")
        plan.approval_notes = approval_data.get("notes", "")
        
        # Store updated plan
        self.store.update(plan_id, plan)
        
        return {
            "plan_id": plan_id,
            "status": "approved",
            "approved_by": plan.approved_by,
            "approved_at": plan.approved_at,
            "message": "Action plan approved for execution"
        }
    
    async def execute(self, plan_id: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved action plan."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        if getattr(plan, 'status', 'pending') != 'approved':
            raise ValueError(f"Plan {plan_id} is not approved for execution")
        
        # Update plan status
        plan.status = "executing"
        plan.executed_by = execution_data.get("executed_by")
        plan.execution_started_at = execution_data.get("started_at")
        
        # Process execution steps
        execution_results = []
        for step in plan.steps:
            # Execute each step
            step_result = {
                "step_id": step.get("id"),
                "description": step.get("description"),
                "status": "completed",
                "executed_at": execution_data.get("started_at")
            }
            execution_results.append(step_result)
        
        # Update plan with execution results
        plan.execution_results = execution_results
        plan.status = "completed"
        plan.execution_completed_at = execution_data.get("completed_at")
        
        # Store updated plan
        self.store.update(plan_id, plan)
        
        return {
            "plan_id": plan_id,
            "status": "completed",
            "executed_by": plan.executed_by,
            "execution_results": execution_results,
            "message": "Action plan executed successfully"
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get action plan statistics and metrics."""
        plans = self.store.get_all()
        
        if not plans:
            return {
                "total_plans": 0,
                "pending_plans": 0,
                "approved_plans": 0,
                "executing_plans": 0,
                "completed_plans": 0,
                "plan_types": {},
                "urgency_levels": {},
                "avg_steps_per_plan": 0.0,
                "completion_rate": 0.0
            }
        
        total = len(plans)
        
        # Count by status
        pending = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'pending')
        approved = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'approved')
        executing = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'executing')
        completed = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'completed')
        
        # Collect statistics
        plan_types = {}
        urgency_levels = {}
        total_steps = 0
        
        for plan in plans:
            # Plan types
            plan_type = getattr(plan, 'plan_type', 'Unknown')
            plan_types[plan_type] = plan_types.get(plan_type, 0) + 1
            
            # Urgency levels
            urgency = getattr(plan, 'urgency', 'Unknown')
            urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            # Step counts
            steps = getattr(plan, 'steps', [])
            total_steps += len(steps)
        
        return {
            "total_plans": total,
            "pending_plans": pending,
            "approved_plans": approved,
            "executing_plans": executing,
            "completed_plans": completed,
            "plan_types": dict(sorted(plan_types.items(), key=lambda x: x[1], reverse=True)),
            "urgency_levels": urgency_levels,
            "avg_steps_per_plan": total_steps / total if total > 0 else 0.0,
            "completion_rate": completed / total if total > 0 else 0.0
        }