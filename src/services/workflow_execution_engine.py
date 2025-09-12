"""
Workflow Execution Engine - Orchestrates execution of approved workflows.
Coordinates between agents, executors, and storage systems.
NO FALLBACK LOGIC - fails fast on any execution issues.
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from src.agents.workflow_execution_agent import WorkflowExecutionAgent
from src.executors.workflow_mock_executors import (
    EmailMockExecutor,
    CRMockExecutor, 
    DisclosureMockExecutor,
    TaskMockExecutor,
    TrainingMockExecutor
)
from src.storage.workflow_store import WorkflowStore
from src.storage.workflow_execution_store import WorkflowExecutionStore


class WorkflowExecutionEngine:
    """Main orchestrator for workflow execution.
    
    This engine handles the complete workflow execution lifecycle:
    1. Validates workflow is ready for execution
    2. Uses LLM agent to analyze action and determine executor
    3. Routes to appropriate mock executor
    4. Stores execution results and updates workflow status
    5. Provides execution tracking and reporting
    
    NO FALLBACK LOGIC - any failure causes immediate exception.
    """
    
    def __init__(self, db_path: str = "data/call_center.db"):
        """Initialize execution engine with all dependencies.
        
        Args:
            db_path: Path to database file
        """
        # Initialize agent and storage
        self.execution_agent = WorkflowExecutionAgent()
        self.workflow_store = WorkflowStore(db_path)
        self.execution_store = WorkflowExecutionStore(db_path)
        
        # Initialize mock executors
        self.executors = {
            'email': EmailMockExecutor(),
            'crm': CRMockExecutor(),
            'disclosure': DisclosureMockExecutor(), 
            'task': TaskMockExecutor(),
            'training': TrainingMockExecutor()
        }
    
    async def execute_workflow(self, workflow_id: str, executed_by: str = "system_executor") -> Dict[str, Any]:
        """Execute a single approved workflow.
        
        Args:
            workflow_id: ID of workflow to execute
            executed_by: Who is executing the workflow
            
        Returns:
            Complete execution result with payload and metadata
            
        Raises:
            ValueError: Invalid workflow state or data (NO FALLBACK)
            Exception: Execution failure (NO FALLBACK)
        """
        execution_start_time = time.time()
        
        try:
            # Step 1: Get and validate workflow
            workflow = self.workflow_store.get_by_id(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Validate workflow status - accept both APPROVED and AUTO_APPROVED
            if workflow['status'] not in ['APPROVED', 'AUTO_APPROVED']:
                raise ValueError(
                    f"Workflow must be approved for execution. "
                    f"Current status: {workflow['status']}"
                )
            
            # Extract action item
            workflow_data = workflow.get('workflow_data', {})
            action_item = workflow_data.get('action_item')
            if not action_item:
                raise ValueError(
                    f"Workflow missing action_item: {workflow_id}"
                )
            
            # Step 2: LLM agent analyzes action and determines executor
            execution_decision = await self.execution_agent.analyze_workflow_action(workflow)
            executor_type = execution_decision['executor_type']
            parameters = execution_decision['parameters']
            
            # Validate executor exists
            if executor_type not in self.executors:
                raise ValueError(
                    f"No executor available for type: {executor_type}. "
                    f"Available: {list(self.executors.keys())}"
                )
            
            # Step 3: Generate execution payload using LLM
            execution_payload = await self.execution_agent.generate_execution_payload(
                workflow, executor_type
            )
            
            # Step 4: Execute using appropriate mock executor
            executor = self.executors[executor_type]
            execution_result = executor.execute(workflow, parameters)
            
            # Step 5: Calculate execution metrics
            execution_duration = int((time.time() - execution_start_time) * 1000)
            
            # Step 6: Store execution record
            execution_record = {
                'workflow_id': workflow_id,
                'executor_type': executor_type,
                'execution_payload': execution_result['payload'],
                'execution_status': 'executed',
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'executed_by': executed_by,
                'execution_duration_ms': execution_duration,
                'mock_execution': True,
                'metadata': {
                    'agent_decision': execution_decision,
                    'executor_result': execution_result,
                    'workflow_type': workflow.get('workflow_type'),
                    'plan_id': workflow.get('plan_id'),
                    'risk_level': workflow.get('risk_level')
                }
            }
            
            execution_id = await self.execution_store.create(execution_record)
            
            # Step 7: Update workflow status to EXECUTED
            success = self.workflow_store.update_status(
                workflow_id=workflow_id,
                new_status='EXECUTED',
                transitioned_by=executed_by,
                reason='Workflow executed successfully',
                additional_data={'execution_id': execution_id}
            )
            
            if not success:
                raise Exception(f"Failed to update workflow status: {workflow_id}")
            
            # Step 8: Return complete execution result
            return {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'status': 'executed',
                'executor_type': executor_type,
                'payload': execution_result['payload'],
                'mock': True,
                'executed_at': execution_record['executed_at'],
                'executed_by': executed_by,
                'execution_duration_ms': execution_duration,
                'agent_decision': execution_decision
            }
            
        except Exception as e:
            # Store failed execution record
            execution_duration = int((time.time() - execution_start_time) * 1000)
            
            try:
                failed_execution_record = {
                    'workflow_id': workflow_id,
                    'executor_type': 'unknown',
                    'execution_payload': {},
                    'execution_status': 'failed',
                    'executed_at': datetime.now(timezone.utc).isoformat(),
                    'executed_by': executed_by,
                    'execution_duration_ms': execution_duration,
                    'mock_execution': True,
                    'error_message': str(e),
                    'metadata': {'failure_reason': str(e)}
                }
                
                await self.execution_store.create(failed_execution_record)
                
            except Exception as store_error:
                # Even storage failed - log but don't mask original error
                print(f"Failed to store failed execution record: {store_error}")
            
            # Re-raise original exception - NO FALLBACK
            raise Exception(f"Workflow execution failed for {workflow_id}: {e}")
    
    async def execute_multiple_workflows(self, workflow_ids: list, 
                                       executed_by: str = "system_executor") -> Dict[str, Any]:
        """Execute multiple approved workflows in sequence.
        
        Args:
            workflow_ids: List of workflow IDs to execute
            executed_by: Who is executing the workflows
            
        Returns:
            Summary of all executions with results and failures
            
        Raises:
            ValueError: Invalid input parameters (NO FALLBACK)
        """
        if not workflow_ids or not isinstance(workflow_ids, list):
            raise ValueError("workflow_ids must be a non-empty list")
        
        if not all(isinstance(wf_id, str) for wf_id in workflow_ids):
            raise ValueError("All workflow_ids must be strings")
        
        results = {
            'total_workflows': len(workflow_ids),
            'successful_executions': [],
            'failed_executions': [],
            'execution_summary': {
                'success_count': 0,
                'failure_count': 0,
                'total_duration_ms': 0
            },
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        batch_start_time = time.time()
        
        # Execute each workflow
        for workflow_id in workflow_ids:
            try:
                execution_result = await self.execute_workflow(workflow_id, executed_by)
                results['successful_executions'].append(execution_result)
                results['execution_summary']['success_count'] += 1
                results['execution_summary']['total_duration_ms'] += execution_result.get('execution_duration_ms', 0)
                
            except Exception as e:
                failed_result = {
                    'workflow_id': workflow_id,
                    'status': 'failed',
                    'error': str(e),
                    'failed_at': datetime.now(timezone.utc).isoformat()
                }
                results['failed_executions'].append(failed_result)
                results['execution_summary']['failure_count'] += 1
        
        # Add batch timing
        batch_duration = int((time.time() - batch_start_time) * 1000)
        results['execution_summary']['batch_duration_ms'] = batch_duration
        results['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        return results
    
    async def execute_all_approved_workflows(self, workflow_type: Optional[str] = None,
                                           executed_by: str = "system_executor") -> Dict[str, Any]:
        """Execute all approved workflows, optionally filtered by type.
        
        Args:
            workflow_type: Optional filter by workflow type (BORROWER, ADVISOR, etc.)
            executed_by: Who is executing the workflows
            
        Returns:
            Summary of all executions
            
        Raises:
            Exception: Execution failure (NO FALLBACK)
        """
        try:
            # Get all approved workflows
            approved_workflows = []
            all_workflows = self.workflow_store.list_workflows()
            
            for workflow in all_workflows:
                if workflow['status'] == 'APPROVED':
                    if not workflow_type or workflow.get('workflow_type') == workflow_type:
                        approved_workflows.append(workflow['id'])
            
            if not approved_workflows:
                return {
                    'total_workflows': 0,
                    'successful_executions': [],
                    'failed_executions': [],
                    'execution_summary': {
                        'success_count': 0,
                        'failure_count': 0,
                        'total_duration_ms': 0
                    },
                    'message': f'No approved workflows found' + (f' for type {workflow_type}' if workflow_type else '')
                }
            
            # Execute all approved workflows
            return await self.execute_multiple_workflows(approved_workflows, executed_by)
            
        except Exception as e:
            raise Exception(f"Failed to execute all approved workflows: {e}")
    
    async def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get detailed execution status and results.
        
        Args:
            execution_id: Execution record ID
            
        Returns:
            Complete execution details including payload and metrics
            
        Raises:
            ValueError: Invalid execution_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("execution_id must be a non-empty string")
        
        try:
            # Get execution record
            execution_record = await self.execution_store.get_by_id(execution_id)
            if not execution_record:
                raise ValueError(f"Execution record not found: {execution_id}")
            
            # Get audit trail
            audit_trail = await self.execution_store.get_execution_audit_trail(execution_id)
            
            # Combine into complete status
            return {
                'execution_record': execution_record,
                'audit_trail': audit_trail,
                'retrieved_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to get execution status: {e}")
    
    async def get_workflow_execution_history(self, workflow_id: str) -> Dict[str, Any]:
        """Get complete execution history for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Complete execution history with all attempts
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        try:
            # Get workflow details
            workflow = self.workflow_store.get_by_id(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            # Get all execution records
            execution_records = await self.execution_store.get_by_workflow(workflow_id)
            
            return {
                'workflow': workflow,
                'execution_history': execution_records,
                'total_executions': len(execution_records),
                'last_execution': execution_records[0] if execution_records else None,
                'retrieved_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to get workflow execution history: {e}")
    
    async def get_execution_statistics(self) -> Dict[str, Any]:
        """Get comprehensive execution statistics and metrics.
        
        Returns:
            Complete execution statistics across all workflows
            
        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        try:
            # Get execution statistics from store
            store_stats = await self.execution_store.get_execution_statistics()
            
            # Add engine-specific statistics
            engine_stats = {
                'available_executors': list(self.executors.keys()),
                'total_executor_types': len(self.executors),
                'agent_version': self.execution_agent.agent_version,
                'engine_initialized_at': datetime.now(timezone.utc).isoformat()
            }
            
            return {
                'store_statistics': store_stats,
                'engine_statistics': engine_stats,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to get execution statistics: {e}")
    
    def validate_workflow_for_execution(self, workflow: Dict[str, Any]) -> bool:
        """Validate that workflow can be executed.
        
        Args:
            workflow: Workflow data to validate
            
        Returns:
            True if workflow is valid for execution
            
        Raises:
            ValueError: Workflow validation failure (NO FALLBACK)
        """
        # Check required fields
        if not workflow.get('id'):
            raise ValueError("Workflow missing ID")
        
        if workflow.get('status') not in ['APPROVED', 'AUTO_APPROVED']:
            raise ValueError(f"Workflow not approved: {workflow.get('status')}")
        
        # Check workflow data
        workflow_data = workflow.get('workflow_data', {})
        if not workflow_data.get('action_item'):
            raise ValueError("Workflow missing action_item")
        
        # Check workflow type
        valid_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
        if workflow.get('workflow_type') not in valid_types:
            raise ValueError(f"Invalid workflow type: {workflow.get('workflow_type')}")
        
        return True
    
    async def preview_execution(self, workflow_id: str) -> Dict[str, Any]:
        """Preview what would be executed without actually executing.
        
        Args:
            workflow_id: Workflow ID to preview
            
        Returns:
            Preview of execution plan and generated payload
            
        Raises:
            ValueError: Invalid workflow (NO FALLBACK)
            Exception: Preview generation failure (NO FALLBACK)
        """
        try:
            # Get and validate workflow
            workflow = self.workflow_store.get_by_id(workflow_id)
            if not workflow:
                raise ValueError(f"Workflow not found: {workflow_id}")
            
            self.validate_workflow_for_execution(workflow)
            
            # Get execution decision from agent
            execution_decision = await self.execution_agent.analyze_workflow_action(workflow)
            
            # Generate payload preview
            execution_payload = await self.execution_agent.generate_execution_payload(
                workflow, execution_decision['executor_type']
            )
            
            return {
                'workflow_id': workflow_id,
                'workflow_summary': {
                    'action_item': workflow['workflow_data'].get('action_item'),
                    'workflow_type': workflow.get('workflow_type'),
                    'status': workflow.get('status'),
                    'risk_level': workflow.get('risk_level')
                },
                'execution_plan': execution_decision,
                'payload_preview': execution_payload,
                'preview_generated_at': datetime.now(timezone.utc).isoformat(),
                'note': 'This is a preview only - no execution performed'
            }
            
        except Exception as e:
            raise Exception(f"Failed to preview execution: {e}")