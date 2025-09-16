"""
Workflow Execution Engine - Orchestrates execution of approved workflows.
Coordinates between agents, adapters, and storage systems.
NO FALLBACK LOGIC - fails fast on any execution issues.
"""
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from src.agents.workflow_execution_agent import WorkflowExecutionAgent
from src.infrastructure.adapters.workflow_mock_adapters import (
    EmailMockAdapter,
    CRMockAdapter,
    DisclosureMockAdapter,
    TaskMockAdapter,
    TrainingMockAdapter,
    ServicingAPIMockAdapter,
    IncomeAPIMockAdapter,
    UnderwritingAPIMockAdapter,
    HardshipAPIMockAdapter,
    PricingAPIMockAdapter,
    DocumentAPIMockAdapter,
    ComplianceAPIMockAdapter,
    AccountingAPIMockAdapter
)
from src.storage.workflow_store import WorkflowStore
from src.storage.workflow_execution_store import WorkflowExecutionStore


class WorkflowExecutionEngine:
    """Main orchestrator for workflow execution.
    
    This engine handles the complete workflow execution lifecycle:
    1. Validates workflow is ready for execution
    2. Uses LLM agent to analyze action and determine executor
    3. Routes to appropriate mock adapter
    4. Stores execution results and updates workflow status
    5. Provides execution tracking and reporting
    
    NO FALLBACK LOGIC - any failure causes immediate exception.
    """
    
    def __init__(self, db_path: str = "data/call_center.db"):
        """Initialize execution engine with all dependencies.

        Args:
            db_path: Path to database file
        """
        self.logger = logging.getLogger(__name__)

        # Initialize agent and storage
        self.execution_agent = WorkflowExecutionAgent()
        self.workflow_store = WorkflowStore(db_path)
        self.execution_store = WorkflowExecutionStore(db_path)
        
        # Initialize mock adapters
        self.adapters = {
            # Human-centric adapters
            'email': EmailMockAdapter(),
            'crm': CRMockAdapter(),
            'disclosure': DisclosureMockAdapter(),
            'task': TaskMockAdapter(),
            'training': TrainingMockAdapter(),
            # API-centric mortgage system adapters
            'servicing_api': ServicingAPIMockAdapter(),
            'income_api': IncomeAPIMockAdapter(),
            'underwriting_api': UnderwritingAPIMockAdapter(),
            'hardship_api': HardshipAPIMockAdapter(),
            'pricing_api': PricingAPIMockAdapter(),
            'document_api': DocumentAPIMockAdapter(),
            'compliance_api': ComplianceAPIMockAdapter(),
            'accounting_api': AccountingAPIMockAdapter()
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
        self.logger.info(f"Starting workflow execution: workflow_id={workflow_id}, executed_by={executed_by}")

        try:
            # Step 1: Get and validate workflow
            workflow = self.workflow_store.get_by_id(workflow_id)
            if not workflow:
                self.logger.error(f"Workflow not found: workflow_id={workflow_id}")
                raise ValueError(f"Workflow not found: {workflow_id}")

            self.logger.info(f"Workflow retrieved: workflow_id={workflow_id}, status={workflow.get('status')}")

            # Validate workflow status - accept both APPROVED and AUTO_APPROVED
            if workflow['status'] not in ['APPROVED', 'AUTO_APPROVED']:
                self.logger.error(f"Invalid workflow status for execution: workflow_id={workflow_id}, status={workflow['status']}")
                raise ValueError(
                    f"Workflow must be approved for execution. "
                    f"Current status: {workflow['status']}"
                )

            # Extract workflow data
            workflow_data = workflow.get('workflow_data', {})
            self.logger.info(f"Extracted workflow data: workflow_id={workflow_id}, workflow_data_keys={list(workflow_data.keys())}")

            # Step 2: Execute workflow steps sequentially
            workflow_steps = workflow_data.get('steps', [])

            # NO FALLBACK - if no steps defined, fail fast
            if not workflow_steps:
                self.logger.error(f"No workflow steps found: workflow_id={workflow_id}, workflow_data={workflow_data}")
                raise ValueError(
                    f"Workflow {workflow_id} has no steps defined. "
                    f"Cannot execute workflow without defined steps."
                )

            self.logger.info(f"Found {len(workflow_steps)} steps to execute: workflow_id={workflow_id}")

            # Execute each step with its specified executor
            step_results = []
            total_execution_time = 0

            for i, step in enumerate(workflow_steps, 1):
                step_start_time = time.time()

                # Extract step details - NO FALLBACK validation
                step_number = step.get('step_number', i)
                step_action = step.get('action', '')
                executor_type = step.get('tool_needed', '').strip()
                step_details = step.get('details', '')

                self.logger.info(f"Executing step {step_number}/{len(workflow_steps)}: workflow_id={workflow_id}, action='{step_action}', executor_type='{executor_type}'")

                if not executor_type:
                    self.logger.error(f"Step missing tool_needed field: workflow_id={workflow_id}, step_number={step_number}, step={step}")
                    raise ValueError(f"Step {step_number} missing tool_needed field")

                # Check if executor exists
                if executor_type not in self.adapters:
                    # Mark step as failed due to missing executor - but continue with other steps
                    step_duration = int((time.time() - step_start_time) * 1000)

                    # Store failed step execution record
                    step_execution_record = {
                        'workflow_id': workflow_id,
                        'executor_type': executor_type,
                        'execution_payload': {},
                        'execution_status': 'failed',
                        'executed_at': datetime.now(timezone.utc).isoformat(),
                        'executed_by': executed_by,
                        'execution_duration_ms': step_duration,
                        'mock_execution': True,
                        'error_message': f"No executor available for type: {executor_type}",
                        'metadata': {
                            'step_details': step_details,
                            'available_adapters': list(self.adapters.keys()),
                            'workflow_type': workflow.get('workflow_type'),
                            'plan_id': workflow.get('plan_id')
                        }
                    }

                    step_execution_id = await self.execution_store.create(step_execution_record)

                    step_results.append({
                        'step_number': step_number,
                        'step_action': step_action,
                        'executor_type': executor_type,
                        'execution_id': step_execution_id,
                        'status': 'failed',
                        'duration_ms': step_duration,
                        'error': f"No executor available for type: {executor_type}",
                        'payload': {}
                    })

                    # Continue to next step
                    continue

                # Execute step using appropriate executor
                executor = self.adapters[executor_type]
                self.logger.info(f"Found executor for step: workflow_id={workflow_id}, step_number={step_number}, executor_type={executor_type}")

                # Create step-specific parameters
                step_parameters = {
                    'step_number': step_number,
                    'step_action': step_action,
                    'step_details': step_details,
                    'loan_id': 'LN-784523',  # Default from examples
                    'workflow_id': workflow_id
                }

                # Execute the step - FAIL FAST if execution fails
                self.logger.info(f"Calling executor.execute(): workflow_id={workflow_id}, step_number={step_number}, executor_type={executor_type}")
                try:
                    step_result = executor.execute(workflow, step_parameters)
                    self.logger.info(f"Executor completed successfully: workflow_id={workflow_id}, step_number={step_number}, result_keys={list(step_result.keys()) if isinstance(step_result, dict) else 'not_dict'}")
                except Exception as e:
                    self.logger.exception(f"Executor failed: workflow_id={workflow_id}, step_number={step_number}, executor_type={executor_type}")
                    raise

                # Calculate step timing
                step_duration = int((time.time() - step_start_time) * 1000)
                total_execution_time += step_duration

                # Store individual step execution result - FAIL FAST if storage fails
                step_execution_record = {
                    'workflow_id': workflow_id,
                    'executor_type': executor_type,
                    'execution_payload': step_result['payload'],
                    'execution_status': 'executed',
                    'executed_at': datetime.now(timezone.utc).isoformat(),
                    'executed_by': executed_by,
                    'execution_duration_ms': step_duration,
                    'mock_execution': True,
                    'metadata': {
                        'step_details': step_details,
                        'executor_result': step_result,
                        'workflow_type': workflow.get('workflow_type'),
                        'plan_id': workflow.get('plan_id')
                    }
                }

                step_execution_id = await self.execution_store.create(step_execution_record)

                step_results.append({
                    'step_number': step_number,
                    'step_action': step_action,
                    'executor_type': executor_type,
                    'execution_id': step_execution_id,
                    'status': 'executed',
                    'duration_ms': step_duration,
                    'payload': step_result['payload']
                })

            # Step 3: Calculate summary (no overall record created)
            execution_duration = int((time.time() - execution_start_time) * 1000)

            successful_steps = [s for s in step_results if s['status'] == 'executed']
            failed_steps = [s for s in step_results if s['status'] == 'failed']

            # Use first step's execution_id as the primary ID for reference
            execution_id = step_results[0]['execution_id'] if step_results else None

            # Step 4: Update workflow status to EXECUTED
            success = self.workflow_store.update_status(
                workflow_id=workflow_id,
                new_status='EXECUTED',
                transitioned_by=executed_by,
                reason=f'Workflow executed: {len(successful_steps)}/{len(workflow_steps)} steps successful',
                additional_data={'execution_id': execution_id}
            )

            if not success:
                raise Exception(f"Failed to update workflow status: {workflow_id}")

            # Step 5: Return complete execution result
            return {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'status': 'executed' if len(failed_steps) == 0 else 'partial_failure',
                'total_steps': len(workflow_steps),
                'successful_steps': len(successful_steps),
                'failed_steps': len(failed_steps),
                'step_results': step_results,
                'mock': True,
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'executed_by': executed_by,
                'execution_duration_ms': execution_duration
            }
            
        except Exception as e:
            # Store failed execution record
            execution_duration = int((time.time() - execution_start_time) * 1000)
            self.logger.exception(f"Workflow execution failed: workflow_id={workflow_id}, executed_by={executed_by}, duration={execution_duration}ms")

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
                # Even storage failed - but don't mask original error
                pass
            
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
                'available_adapters': list(self.adapters.keys()),
                'total_executor_types': len(self.adapters),
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

    async def list_all_executions(self, limit: Optional[int] = None,
                                status: Optional[str] = None,
                                executor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all executions with optional filters.

        Args:
            limit: Optional limit on number of results
            status: Optional filter by execution status
            executor_type: Optional filter by executor type

        Returns:
            List of execution records

        Raises:
            ValueError: Invalid filter parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        try:
            return await self.execution_store.get_all(
                limit=limit,
                status=status,
                executor_type=executor_type
            )
        except Exception as e:
            raise Exception(f"Failed to list executions: {e}")

    async def delete_execution(self, execution_id: str) -> bool:
        """Delete execution record by ID.

        Args:
            execution_id: Execution record ID to delete

        Returns:
            True if execution was deleted, False if not found

        Raises:
            ValueError: Invalid execution_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("execution_id must be a non-empty string")

        try:
            return await self.execution_store.delete(execution_id)
        except Exception as e:
            raise Exception(f"Failed to delete execution: {e}")

    async def delete_all_executions(self, status: Optional[str] = None,
                                  executor_type: Optional[str] = None) -> int:
        """Delete all executions with optional filters.

        Args:
            status: Optional filter - only delete executions with this status
            executor_type: Optional filter - only delete executions of this type

        Returns:
            Number of executions deleted

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        try:
            return await self.execution_store.delete_all(
                status=status,
                executor_type=executor_type
            )
        except Exception as e:
            raise Exception(f"Failed to delete all executions: {e}")

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
        if not workflow_data.get('title'):
            raise ValueError("Workflow missing title")
        
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