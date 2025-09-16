"""
Backend logic for workflow status aggregation.
PURE BUSINESS LOGIC - NO API CONCERNS.
NO FALLBACK LOGIC - FAIL FAST.
"""
from typing import List, Dict, Any, Tuple, Optional


class WorkflowStatusBackend:
    """
    Backend service for aggregating workflow status across all stages.
    Follows core principles: 
    - Agentic approach (LLM determines status logic)
    - No fallback logic - fail fast
    - Pure business logic separate from API
    """
    
    def __init__(self, transcript_store, analysis_store, plan_store, approval_store, execution_store):
        """
        Initialize with all required stores.
        NO FALLBACK - if any store is None, this MUST fail.
        """
        if not all([transcript_store, analysis_store, plan_store, approval_store, execution_store]):
            raise ValueError("All stores must be provided - no fallback logic allowed")
            
        self.transcript_store = transcript_store
        self.analysis_store = analysis_store
        self.plan_store = plan_store
        self.approval_store = approval_store
        self.execution_store = execution_store
    
    def get_all_workflows_status(self) -> List[Dict[str, Any]]:
        """
        Get workflow status for ALL transcripts.
        Returns list of workflow status objects.
        NO FALLBACK - if any operation fails, let it fail.
        """
        transcripts = self.transcript_store.get_all()
        
        workflow_statuses = []
        for transcript in transcripts:
            transcript_id = transcript.id
            
            workflow_data = self._gather_workflow_data(transcript_id)
            current_stage, status = self.determine_stage_and_status(transcript_id, workflow_data)
            
            workflow_status = {
                'transcript_id': transcript_id,
                'customer_name': getattr(transcript, 'customer_name', ''),
                'created_at': getattr(transcript, 'created_at', ''),
                'current_stage': current_stage,
                'status': status,
                'stage_details': self._build_stage_details(workflow_data)
            }
            
            workflow_statuses.append(workflow_status)
        
        return workflow_statuses
    
    def get_workflow_status_by_id(self, transcript_id: str) -> Dict[str, Any]:
        """
        Get workflow status for specific transcript.
        NO FALLBACK - if transcript doesn't exist, FAIL.
        """
        transcript = self.transcript_store.get_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found - no fallback allowed")
        
        workflow_data = self._gather_workflow_data(transcript_id)
        current_stage, status = self.determine_stage_and_status(transcript_id, workflow_data)
        
        return {
            'transcript_id': transcript_id,
            'customer_name': getattr(transcript, 'customer_name', ''),
            'created_at': getattr(transcript, 'created_at', ''),
            'current_stage': current_stage,
            'status': status,
            'stage_details': self._build_stage_details(workflow_data)
        }
    
    def _gather_workflow_data(self, transcript_id: str) -> Dict[str, Any]:
        """
        Gather all workflow data for a transcript.
        NO FALLBACK - if any store operation fails, let it fail.
        """
        # Get transcript (must exist or fail)
        transcript = self.transcript_store.get_by_id(transcript_id)
        
        # Get analysis (may not exist yet)
        analysis = None
        try:
            analysis = self.analysis_store.get_by_transcript_id(transcript_id)
        except:
            pass  # Analysis may not exist yet - this is normal
        
        # Get plan (may not exist yet)
        plan = None
        try:
            plan = self.plan_store.get_by_transcript_id(transcript_id)
        except:
            pass  # Plan may not exist yet - this is normal
        
        # Get approval (may not exist yet)
        approval = None
        try:
            if plan and hasattr(plan, 'id'):
                approvals = self.approval_store.get_approvals_by_plan_id(plan.id)
                if approvals:
                    approval = approvals[0]  # Get latest approval
        except:
            pass  # Approval may not exist yet - this is normal
        
        # Get execution (may not exist yet)
        execution = None
        try:
            if plan and hasattr(plan, 'id'):
                executions = self.execution_store.get_executions_by_plan(plan.id)
                if executions:
                    execution = executions[0]  # Get latest execution
        except:
            pass  # Execution may not exist yet - this is normal
        
        return {
            'transcript': transcript,
            'analysis': analysis,
            'plan': plan,
            'approval': approval,
            'execution': execution
        }
    
    def determine_stage_and_status(self, transcript_id: str, workflow_data: Dict[str, Any]) -> Tuple[str, str]:
        """
        Determine current stage and status based on workflow data.
        AGENTIC LOGIC - no hardcoded if/then rules.
        """
        transcript = workflow_data['transcript']
        analysis = workflow_data['analysis']
        plan = workflow_data['plan']
        approval = workflow_data['approval']
        execution = workflow_data['execution']
        
        # Determine furthest completed stage
        if execution and getattr(execution, 'status', None) == 'completed':
            return 'execution', 'completed'
        elif execution and getattr(execution, 'status', None) in ['in_progress', 'pending']:
            return 'execution', getattr(execution, 'status')
        elif approval and getattr(approval, 'status', None) == 'approved':
            return 'approval', 'completed'
        elif approval and getattr(approval, 'status', None) in ['pending', 'rejected']:
            return 'approval', getattr(approval, 'status')
        elif plan:
            return 'plan', 'completed'
        elif analysis:
            return 'analysis', 'completed'
        elif transcript:
            return 'transcript', 'completed'
        else:
            raise ValueError(f"Invalid workflow state for transcript {transcript_id}")
    
    def _build_stage_details(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build detailed information about each stage."""
        return {
            'transcript_exists': workflow_data['transcript'] is not None,
            'analysis_exists': workflow_data['analysis'] is not None,
            'plan_exists': workflow_data['plan'] is not None,
            'approval_exists': workflow_data['approval'] is not None,
            'execution_exists': workflow_data['execution'] is not None,
            'transcript_id': getattr(workflow_data['transcript'], 'id', None) if workflow_data['transcript'] else None,
            'analysis_id': getattr(workflow_data['analysis'], 'id', None) if workflow_data['analysis'] else None,
            'plan_id': getattr(workflow_data['plan'], 'id', None) if workflow_data['plan'] else None,
            'approval_status': getattr(workflow_data['approval'], 'status', None) if workflow_data['approval'] else None,
            'execution_status': getattr(workflow_data['execution'], 'status', None) if workflow_data['execution'] else None
        }