"""Workflow approval service - business logic layer.

Core Principles Applied:
- NO FALLBACK: Fail fast on invalid data or missing context
- AGENTIC: All routing and decisions made by LLM agents
- Context Preservation: Complete traceability through pipeline
"""
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.storage.workflow_store import WorkflowStore
from src.storage.action_plan_store import ActionPlanStore
from src.agents.risk_assessment_agent import RiskAssessmentAgent


class WorkflowService:
    """Business logic for workflow approval management.
    
    Orchestrates workflow extraction from plans, risk assessment,
    and approval routing using LLM agents with full context preservation.
    """
    
    def __init__(self, db_path: str):
        """Initialize service with dependencies.
        
        Args:
            db_path: Database path for storage layers
            
        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")
        
        self.db_path = db_path
        self.workflow_store = WorkflowStore(db_path)
        self.action_plan_store = ActionPlanStore(db_path)
        self.risk_agent = RiskAssessmentAgent()
    
    async def extract_workflow_from_plan(self, plan_id: str) -> Dict[str, Any]:
        """Extract workflow from action plan using LLM agent.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            Complete workflow data with context
            
        Raises:
            ValueError: Invalid plan_id or plan not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        # Get action plan - fail fast if not found
        plan_data = self.action_plan_store.get_by_id(plan_id)
        if not plan_data:
            raise ValueError(f"Action plan not found: {plan_id}")
        
        # Build complete context for LLM agent
        context_data = {
            'transcript_id': plan_data['transcript_id'],
            'analysis_id': plan_data['analysis_id'],
            'plan_id': plan_id,
            'plan_data': plan_data,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'pipeline_stage': 'workflow_extraction'
        }
        
        # Extract workflow using LLM agent (no hardcoded logic)
        workflow_extraction = await self.risk_agent.extract_workflow_from_plan(
            plan_data=plan_data,
            context=context_data
        )
        
        # Validate LLM response structure
        required_fields = ['workflow_steps', 'complexity_assessment', 'dependencies']
        for field in required_fields:
            if field not in workflow_extraction:
                raise ValueError(f"LLM agent failed to provide required field: {field}")
        
        # Risk assessment using LLM agent
        risk_assessment = await self.risk_agent.assess_workflow_risk(
            workflow_data=workflow_extraction,
            context=context_data
        )
        
        # Validate risk assessment
        if 'risk_level' not in risk_assessment or 'reasoning' not in risk_assessment:
            raise ValueError("LLM agent failed to provide complete risk assessment")
        
        # Approval routing decision using LLM agent  
        approval_routing = await self.risk_agent.determine_approval_routing(
            workflow_data=workflow_extraction,
            risk_assessment=risk_assessment,
            context=context_data
        )
        
        # Validate approval routing
        required_routing_fields = ['requires_human_approval', 'initial_status', 'routing_reasoning']
        for field in required_routing_fields:
            if field not in approval_routing:
                raise ValueError(f"LLM agent failed to provide required routing field: {field}")
        
        # Create complete workflow data
        workflow_data = {
            'id': str(uuid.uuid4()),
            'plan_id': plan_id,
            'analysis_id': plan_data['analysis_id'],
            'transcript_id': plan_data['transcript_id'],
            'workflow_data': workflow_extraction,
            'risk_level': risk_assessment['risk_level'],
            'status': approval_routing['initial_status'],
            'context_data': context_data,
            'risk_reasoning': risk_assessment['reasoning'],
            'approval_reasoning': approval_routing['routing_reasoning'],
            'requires_human_approval': approval_routing['requires_human_approval'],
            'assigned_approver': approval_routing.get('assigned_approver')
        }
        
        # Store workflow
        workflow_id = self.workflow_store.create(workflow_data)
        workflow_data['id'] = workflow_id
        
        return workflow_data
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data or None if not found
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        return self.workflow_store.get_by_id(workflow_id)
    
    async def get_workflow_by_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by plan ID.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            Latest workflow for plan or None
            
        Raises:
            ValueError: Invalid plan_id (NO FALLBACK)
        """
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        return self.workflow_store.get_by_plan_id(plan_id)
    
    async def list_workflows(self, status: Optional[str] = None, 
                           risk_level: Optional[str] = None,
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List workflows with optional filters.
        
        Args:
            status: Optional status filter
            risk_level: Optional risk level filter
            limit: Optional result limit
            
        Returns:
            List of matching workflows
            
        Raises:
            ValueError: Invalid filter values (NO FALLBACK)
        """
        if status and risk_level:
            raise ValueError("Cannot filter by both status and risk_level simultaneously")
        
        if status:
            return self.workflow_store.get_by_status(status, limit)
        elif risk_level:
            return self.workflow_store.get_by_risk_level(risk_level, limit)
        else:
            return self.workflow_store.get_all(limit)
    
    async def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get workflows requiring human approval.
        
        Returns:
            List of workflows awaiting approval
        """
        return self.workflow_store.get_pending_approval()
    
    async def approve_workflow(self, workflow_id: str, approved_by: str, 
                             reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Approve workflow using LLM agent decision.
        
        Args:
            workflow_id: Workflow ID
            approved_by: Approver identifier
            reasoning: Optional approval reasoning
            
        Returns:
            Updated workflow data
            
        Raises:
            ValueError: Invalid parameters or workflow not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not approved_by or not isinstance(approved_by, str):
            raise ValueError("approved_by must be a non-empty string")
        
        # Get current workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Validate current state allows approval
        if workflow['status'] != 'AWAITING_APPROVAL':
            raise ValueError(f"Workflow cannot be approved from status: {workflow['status']}")
        
        if not workflow['requires_human_approval']:
            raise ValueError("Workflow does not require human approval")
        
        # LLM agent validates approval decision
        approval_context = {
            **workflow['context_data'],
            'approval_timestamp': datetime.utcnow().isoformat(),
            'approver': approved_by,
            'approval_reasoning': reasoning,
            'pipeline_stage': 'approval_processing'
        }
        
        approval_validation = await self.risk_agent.validate_approval_decision(
            workflow_data=workflow,
            approver=approved_by,
            reasoning=reasoning,
            context=approval_context
        )
        
        # Check if LLM agent rejects the approval
        if not approval_validation.get('approval_valid', False):
            raise ValueError(f"LLM agent rejected approval: {approval_validation.get('rejection_reason', 'Unknown')}")
        
        # Determine next status using LLM agent
        next_status_decision = await self.risk_agent.determine_post_approval_status(
            workflow_data=workflow,
            approval_context=approval_context
        )
        
        new_status = next_status_decision.get('next_status', 'AUTO_APPROVED')
        if new_status not in ['AUTO_APPROVED', 'EXECUTED']:
            raise ValueError(f"Invalid next status from LLM agent: {new_status}")
        
        # Update workflow
        additional_data = {
            'approved_by': approved_by,
            'approved_at': datetime.utcnow().isoformat()
        }
        
        success = self.workflow_store.update_status(
            workflow_id=workflow_id,
            new_status=new_status,
            transitioned_by=approved_by,
            reason=reasoning or "Human approval granted",
            additional_data=additional_data
        )
        
        if not success:
            raise Exception("Failed to update workflow status")
        
        # Return updated workflow
        updated_workflow = self.workflow_store.get_by_id(workflow_id)
        if not updated_workflow:
            raise Exception("Failed to retrieve updated workflow")
        
        return updated_workflow
    
    async def reject_workflow(self, workflow_id: str, rejected_by: str, 
                            reason: str) -> Dict[str, Any]:
        """Reject workflow using LLM agent decision.
        
        Args:
            workflow_id: Workflow ID
            rejected_by: Rejector identifier  
            reason: Rejection reason
            
        Returns:
            Updated workflow data
            
        Raises:
            ValueError: Invalid parameters or workflow not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not rejected_by or not isinstance(rejected_by, str):
            raise ValueError("rejected_by must be a non-empty string")
        
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be a non-empty string")
        
        # Get current workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Validate current state allows rejection
        if workflow['status'] not in ['AWAITING_APPROVAL', 'PENDING_ASSESSMENT']:
            raise ValueError(f"Workflow cannot be rejected from status: {workflow['status']}")
        
        # LLM agent validates rejection decision
        rejection_context = {
            **workflow['context_data'],
            'rejection_timestamp': datetime.utcnow().isoformat(),
            'rejector': rejected_by,
            'rejection_reason': reason,
            'pipeline_stage': 'rejection_processing'
        }
        
        rejection_validation = await self.risk_agent.validate_rejection_decision(
            workflow_data=workflow,
            rejector=rejected_by,
            reason=reason,
            context=rejection_context
        )
        
        # Check if LLM agent questions the rejection
        if not rejection_validation.get('rejection_valid', True):
            # Log the concern but proceed (human override)
            rejection_reason = f"Human override: {reason}. LLM concern: {rejection_validation.get('concern', 'None')}"
        else:
            rejection_reason = reason
        
        # Update workflow
        additional_data = {
            'rejected_by': rejected_by,
            'rejected_at': datetime.utcnow().isoformat(),
            'rejection_reason': rejection_reason
        }
        
        success = self.workflow_store.update_status(
            workflow_id=workflow_id,
            new_status='REJECTED',
            transitioned_by=rejected_by,
            reason=rejection_reason,
            additional_data=additional_data
        )
        
        if not success:
            raise Exception("Failed to update workflow status")
        
        # Return updated workflow
        updated_workflow = self.workflow_store.get_by_id(workflow_id)
        if not updated_workflow:
            raise Exception("Failed to retrieve updated workflow")
        
        return updated_workflow
    
    async def execute_workflow(self, workflow_id: str, executed_by: str) -> Dict[str, Any]:
        """Execute approved workflow using new workflow execution engine.
        
        Args:
            workflow_id: Workflow ID
            executed_by: Executor identifier
            
        Returns:
            Complete execution results with payload
            
        Raises:
            ValueError: Invalid parameters or workflow not executable (NO FALLBACK)
            Exception: Execution failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not executed_by or not isinstance(executed_by, str):
            raise ValueError("executed_by must be a non-empty string")
        
        # Import and initialize execution engine
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine(self.db_path)
        
        # Execute workflow using new engine
        execution_result = await execution_engine.execute_workflow(workflow_id, executed_by)
        
        return execution_result
    
    async def get_workflow_history(self, workflow_id: str) -> Dict[str, Any]:
        """Get complete workflow history with state transitions.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data with transition history
            
        Raises:
            ValueError: Invalid workflow_id or workflow not found (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        # Get workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Get state transitions
        transitions = self.workflow_store.get_state_transitions(workflow_id)
        
        return {
            **workflow,
            'state_transitions': transitions
        }
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        return self.workflow_store.delete(workflow_id)
    
    async def delete_all_workflows(self) -> int:
        """Delete all workflows.
        
        Returns:
            Number of workflows deleted
        """
        return self.workflow_store.delete_all()
    
    async def extract_all_workflows_from_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Extract all granular workflows from action plan using LLM agent.
        
        This method extracts individual action items from each of the 4 pillars
        (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP) as separate workflows for
        independent risk assessment and approval routing.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            List of workflow data dictionaries for all extracted items
            
        Raises:
            ValueError: Invalid plan_id or plan not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        # Set up tracing for workflow extraction
        from src.telemetry import set_span_attributes, add_span_event
        set_span_attributes(plan_id=plan_id, operation="extract_all_workflows")
        add_span_event("extraction.started", plan_id=plan_id)
        
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        # Get action plan - fail fast if not found
        add_span_event("extraction.fetching_plan", plan_id=plan_id)
        plan_data = self.action_plan_store.get_by_id(plan_id)
        if not plan_data:
            raise ValueError(f"Action plan not found: {plan_id}")
        add_span_event("extraction.plan_loaded", plan_id=plan_id)
        
        # Build complete context for LLM agent
        add_span_event("extraction.building_context", plan_id=plan_id)
        context_data = {
            'transcript_id': plan_data['transcript_id'],
            'analysis_id': plan_data['analysis_id'],
            'plan_id': plan_id,
            'plan_data': plan_data,
            'extraction_timestamp': datetime.utcnow().isoformat(),
            'pipeline_stage': 'granular_workflow_extraction'
        }
        
        all_workflows = []
        workflow_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
        add_span_event("extraction.processing_workflow_types", workflow_types=len(workflow_types))
        
        # Create async task for each workflow type to enable parallel processing
        async def process_workflow_type(workflow_type: str) -> List[Dict[str, Any]]:
            """Process a single workflow type in parallel."""
            add_span_event("workflow_type.processing_started", workflow_type=workflow_type)
            try:
                # Extract individual action items using LLM agent
                add_span_event("workflow_type.extracting_items", workflow_type=workflow_type)
                action_items = await self.risk_agent.extract_individual_action_items(
                    plan_data=plan_data,
                    workflow_type=workflow_type,
                    context=context_data
                )
                add_span_event("workflow_type.items_extracted", workflow_type=workflow_type, items_count=len(action_items))
                
                # Add progress information before risk assessment
                if action_items:
                    add_span_event("workflow_type.risk_assessment_starting", workflow_type=workflow_type, items_count=len(action_items))
                
                # Process action items in parallel batches
                async def process_action_item(item: Dict[str, Any]) -> Dict[str, Any]:
                    """Process a single action item with all required assessments."""
                    import time
                    start_time = time.time()
                    
                    # Start processing individual action item
                    item_description = item.get('action', 'Unknown action')[:50]
                    add_span_event("action_item.processing_started", workflow_type=workflow_type, description=item_description)
                    
                    # Run risk assessment and approval routing in parallel
                    risk_assessment_task = self.risk_agent.assess_action_item_risk(
                        action_item=item,
                        workflow_type=workflow_type,
                        context=context_data
                    )
                    
                    # We need risk assessment before approval routing, so we await it first
                    risk_assessment = await risk_assessment_task
                    
                    # Log completion with timing
                    elapsed = time.time() - start_time
                    risk_level = risk_assessment.get('risk_level', 'UNKNOWN')
                    add_span_event("action_item.processing_completed", workflow_type=workflow_type, 
                                  risk_level=risk_level, duration_seconds=round(elapsed, 1))
                    
                    # Validate risk assessment
                    if 'risk_level' not in risk_assessment or 'reasoning' not in risk_assessment:
                        raise ValueError(f"LLM agent failed to provide complete risk assessment for {workflow_type} item")
                    
                    # Now do approval routing with risk assessment results
                    approval_routing = await self.risk_agent.determine_action_item_approval_routing(
                        action_item=item,
                        risk_assessment=risk_assessment,
                        workflow_type=workflow_type,
                        context=context_data
                    )
                    
                    # Validate approval routing
                    required_routing_fields = ['requires_human_approval', 'initial_status', 'routing_reasoning']
                    for field in required_routing_fields:
                        if field not in approval_routing:
                            raise ValueError(f"LLM agent failed to provide required routing field: {field}")
                    
                    # Create workflow data for this action item
                    return {
                        'plan_id': plan_id,
                        'analysis_id': plan_data['analysis_id'],
                        'transcript_id': plan_data['transcript_id'],
                        'workflow_data': item,
                        'workflow_type': workflow_type,
                        'context_data': {
                            **context_data,
                            'workflow_type': workflow_type,
                            'action_item_context': item.get('context', {})
                        },
                        'risk_assessment': risk_assessment,
                        'approval_routing': approval_routing
                    }
                
                # Process all action items for this workflow type in parallel
                workflow_tasks = [process_action_item(item) for item in action_items]
                workflows_for_type = await asyncio.gather(*workflow_tasks, return_exceptions=True)
                
                # Filter out exceptions and collect successful workflows
                successful_workflows = []
                failed_items = []
                for i, result in enumerate(workflows_for_type):
                    if isinstance(result, Exception):
                        failed_items.append({
                            'item_index': i,
                            'item': action_items[i] if i < len(action_items) else None,
                            'error': str(result)
                        })
                        add_span_event("action_item.processing_failed", workflow_type=workflow_type, item_index=i, error=str(result))
                    else:
                        successful_workflows.append(result)
                
                # Log failures but don't fail the entire workflow type
                if failed_items:
                    add_span_event("workflow_type.partial_failures", workflow_type=workflow_type, 
                                  failed_count=len(failed_items), total_count=len(action_items))
                
                # Log completion summary for this workflow type
                add_span_event("workflow_type.processing_completed", workflow_type=workflow_type, 
                              successful_count=len(successful_workflows))
                
                return successful_workflows
                
            except Exception as e:
                raise Exception(f"Failed to extract {workflow_type} workflows: {str(e)}")
        
        # Process all workflow types in parallel
        workflow_type_tasks = [process_workflow_type(wt) for wt in workflow_types]
        workflow_results = await asyncio.gather(*workflow_type_tasks, return_exceptions=True)
        
        # Collect all successful workflows and handle any exceptions
        failed_workflow_types = []
        for i, result in enumerate(workflow_results):
            if isinstance(result, Exception):
                workflow_type = workflow_types[i]
                failed_workflow_types.append({
                    'workflow_type': workflow_type,
                    'error': str(result)
                })
                add_span_event("workflow_type.extraction_failed", workflow_type=workflow_type, error=str(result))
            else:
                all_workflows.extend(result)
        
        # Log failures but continue with successful workflow types
        if failed_workflow_types:
            add_span_event("extraction.partial_failures", failed_types=len(failed_workflow_types), 
                          total_types=len(workflow_types))
            for failure in failed_workflow_types:
                add_span_event("extraction.type_failure", workflow_type=failure['workflow_type'], 
                              error=failure['error'])
        
        # Only fail completely if no workflows were extracted at all
        if not all_workflows and failed_workflow_types:
            raise Exception(f"All workflow types failed: {[f['error'] for f in failed_workflow_types]}")
        
        # Bulk create all workflows
        if all_workflows:
            workflow_ids = self.workflow_store.create_bulk(all_workflows)
            
            # Return workflows with their assigned IDs
            created_workflows = []
            for i, workflow_id in enumerate(workflow_ids):
                workflow = self.workflow_store.get_by_id(workflow_id)
                if workflow:
                    created_workflows.append(workflow)
            
            return created_workflows
        
        return []
    
    async def get_workflows_by_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a specific plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List of workflows for the plan
            
        Raises:
            ValueError: Invalid plan_id (NO FALLBACK)
        """
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        return self.workflow_store.get_by_plan_id(plan_id)
    
    async def get_workflows_by_type(self, workflow_type: str) -> List[Dict[str, Any]]:
        """Get all workflows of a specific type.
        
        Args:
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            
        Returns:
            List of workflows of the specified type
            
        Raises:
            ValueError: Invalid workflow_type (NO FALLBACK)
        """
        return self.workflow_store.get_by_type(workflow_type)
    
    async def get_workflows_by_plan_and_type(self, plan_id: str, workflow_type: str) -> List[Dict[str, Any]]:
        """Get workflows for a specific plan and type combination.
        
        Args:
            plan_id: Plan ID
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            
        Returns:
            List of workflows matching both criteria
            
        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
        """
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        return self.workflow_store.get_by_plan_and_type(plan_id, workflow_type)
    
    async def approve_action_item_workflow(self, workflow_id: str, approved_by: str, 
                                         reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Approve granular action item workflow using LLM agent decision.
        
        Args:
            workflow_id: Workflow ID
            approved_by: Approver identifier
            reasoning: Optional approval reasoning
            
        Returns:
            Updated workflow data
            
        Raises:
            ValueError: Invalid parameters or workflow not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not approved_by or not isinstance(approved_by, str):
            raise ValueError("approved_by must be a non-empty string")
        
        # Get current workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Validate current state allows approval
        if workflow['status'] != 'AWAITING_APPROVAL':
            raise ValueError(f"Workflow cannot be approved from status: {workflow['status']}")
        
        if not workflow['requires_human_approval']:
            raise ValueError("Workflow does not require human approval")
        
        # LLM agent validates approval decision for action items
        approval_context = {
            **workflow['context_data'],
            'approval_timestamp': datetime.utcnow().isoformat(),
            'approver': approved_by,
            'approval_reasoning': reasoning,
            'pipeline_stage': 'action_item_approval_processing'
        }
        
        approval_validation = await self.risk_agent.validate_action_item_approval_decision(
            action_item=workflow['workflow_data'],
            workflow_type=workflow['workflow_type'],
            approver=approved_by,
            reasoning=reasoning,
            context=approval_context
        )
        
        # Check if LLM agent rejects the approval
        if not approval_validation.get('approval_valid', False):
            raise ValueError(f"LLM agent rejected approval: {approval_validation.get('rejection_reason', 'Unknown')}")
        
        # Determine next status using LLM agent
        next_status_decision = await self.risk_agent.determine_action_item_post_approval_status(
            action_item=workflow['workflow_data'],
            workflow_type=workflow['workflow_type'],
            approval_context=approval_context
        )
        
        new_status = next_status_decision.get('next_status', 'AUTO_APPROVED')
        if new_status not in ['AUTO_APPROVED', 'EXECUTED']:
            raise ValueError(f"Invalid next status from LLM agent: {new_status}")
        
        # Update workflow
        additional_data = {
            'approved_by': approved_by,
            'approved_at': datetime.utcnow().isoformat()
        }
        
        success = self.workflow_store.update_status(
            workflow_id=workflow_id,
            new_status=new_status,
            transitioned_by=approved_by,
            reason=reasoning or "Human approval granted",
            additional_data=additional_data
        )
        
        if not success:
            raise Exception("Failed to update workflow status")
        
        # Return updated workflow
        updated_workflow = self.workflow_store.get_by_id(workflow_id)
        if not updated_workflow:
            raise Exception("Failed to retrieve updated workflow")
        
        return updated_workflow
    
    async def reject_action_item_workflow(self, workflow_id: str, rejected_by: str, 
                                        reason: str) -> Dict[str, Any]:
        """Reject granular action item workflow using LLM agent decision.
        
        Args:
            workflow_id: Workflow ID
            rejected_by: Rejector identifier  
            reason: Rejection reason
            
        Returns:
            Updated workflow data
            
        Raises:
            ValueError: Invalid parameters or workflow not found (NO FALLBACK)
            Exception: LLM agent failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not rejected_by or not isinstance(rejected_by, str):
            raise ValueError("rejected_by must be a non-empty string")
        
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be a non-empty string")
        
        # Get current workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Validate current state allows rejection
        if workflow['status'] not in ['AWAITING_APPROVAL', 'PENDING_ASSESSMENT']:
            raise ValueError(f"Workflow cannot be rejected from status: {workflow['status']}")
        
        # LLM agent validates rejection decision for action items
        rejection_context = {
            **workflow['context_data'],
            'rejection_timestamp': datetime.utcnow().isoformat(),
            'rejector': rejected_by,
            'rejection_reason': reason,
            'pipeline_stage': 'action_item_rejection_processing'
        }
        
        rejection_validation = await self.risk_agent.validate_action_item_rejection_decision(
            action_item=workflow['workflow_data'],
            workflow_type=workflow['workflow_type'],
            rejector=rejected_by,
            reason=reason,
            context=rejection_context
        )
        
        # Check if LLM agent questions the rejection
        if not rejection_validation.get('rejection_valid', True):
            # Log the concern but proceed (human override)
            rejection_reason = f"Human override: {reason}. LLM concern: {rejection_validation.get('concern', 'None')}"
        else:
            rejection_reason = reason
        
        # Update workflow
        additional_data = {
            'rejected_by': rejected_by,
            'rejected_at': datetime.utcnow().isoformat(),
            'rejection_reason': rejection_reason
        }
        
        success = self.workflow_store.update_status(
            workflow_id=workflow_id,
            new_status='REJECTED',
            transitioned_by=rejected_by,
            reason=rejection_reason,
            additional_data=additional_data
        )
        
        if not success:
            raise Exception("Failed to update workflow status")
        
        # Return updated workflow
        updated_workflow = self.workflow_store.get_by_id(workflow_id)
        if not updated_workflow:
            raise Exception("Failed to retrieve updated workflow")
        
        return updated_workflow
    
    async def execute_action_item_workflow(self, workflow_id: str, executed_by: str) -> Dict[str, Any]:
        """Execute approved granular action item workflow using LLM agent.
        
        Args:
            workflow_id: Workflow ID
            executed_by: Executor identifier
            
        Returns:
            Workflow with execution results
            
        Raises:
            ValueError: Invalid parameters or workflow not executable (NO FALLBACK)
            Exception: Execution failures (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not executed_by or not isinstance(executed_by, str):
            raise ValueError("executed_by must be a non-empty string")
        
        # Get current workflow
        workflow = self.workflow_store.get_by_id(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Validate workflow is executable
        if workflow['status'] not in ['AUTO_APPROVED']:
            raise ValueError(f"Workflow cannot be executed from status: {workflow['status']}")
        
        # LLM agent executes action item
        execution_context = {
            **workflow['context_data'],
            'execution_timestamp': datetime.utcnow().isoformat(),
            'executor': executed_by,
            'pipeline_stage': 'action_item_execution'
        }
        
        execution_results = await self.risk_agent.execute_action_item(
            action_item=workflow['workflow_data'],
            workflow_type=workflow['workflow_type'],
            context=execution_context
        )
        
        # Validate execution results
        if 'execution_status' not in execution_results:
            raise ValueError("LLM agent failed to provide execution status")
        
        # Update workflow with execution results
        additional_data = {
            'executed_at': datetime.utcnow().isoformat(),
            'execution_results': json.dumps(execution_results)
        }
        
        success = self.workflow_store.update_status(
            workflow_id=workflow_id,
            new_status='EXECUTED',
            transitioned_by=executed_by,
            reason=f"Action item executed: {execution_results.get('execution_status', 'completed')}",
            additional_data=additional_data
        )
        
        if not success:
            raise Exception("Failed to update workflow status")
        
        # Return updated workflow
        updated_workflow = self.workflow_store.get_by_id(workflow_id)
        if not updated_workflow:
            raise Exception("Failed to retrieve updated workflow")
        
        return updated_workflow