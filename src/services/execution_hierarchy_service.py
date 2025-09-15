"""Execution Hierarchy Service - Builds hierarchical execution structures.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: No hardcoded routing logic - all decisions by LLM agents
- Clean Architecture: Backend handles business logic, not frontend
"""
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.storage.workflow_execution_store import WorkflowExecutionStore
from src.telemetry import set_span_attributes, add_span_event, trace_async_function


class ExecutionHierarchyService:
    """Service for building hierarchical execution structures from flat execution data.

    Transforms flat execution records into hierarchical structure expected by tree UI.
    """

    def __init__(self, db_path: str):
        """Initialize hierarchy service with database path.

        Args:
            db_path: SQLite database file path

        Raises:
            Exception: If database initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.execution_store = WorkflowExecutionStore(db_path)

    @trace_async_function("hierarchy.get_executions")
    async def get_hierarchical_executions(self,
                                        status_filter: Optional[str] = None,
                                        executor_type_filter: Optional[str] = None,
                                        limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get executions in hierarchical structure for tree view.

        Groups flat execution records by workflow_id and builds parent-child relationships:
        - Workflow executions (executor_type = 'workflow') become parent nodes
        - Step executions (other executor_types) become child execution_steps

        Args:
            status_filter: Optional status filter
            executor_type_filter: Optional executor type filter
            limit: Optional result limit

        Returns:
            List of hierarchical execution structures with execution_steps

        Raises:
            ValueError: Invalid filter parameters (NO FALLBACK)
            Exception: Database or processing failures (NO FALLBACK)
        """
        set_span_attributes(
            operation="get_hierarchical_executions",
            status_filter=status_filter,
            executor_type_filter=executor_type_filter,
            limit=limit
        )
        add_span_event("hierarchy.fetch_started")

        try:
            # Get all executions from store
            executions = await self.execution_store.get_all_executions(
                status_filter=status_filter,
                executor_type_filter=executor_type_filter,
                limit=limit
            )

            add_span_event("hierarchy.executions_fetched", execution_count=len(executions))

            if not executions:
                add_span_event("hierarchy.no_executions_found")
                return []

            # Group executions by workflow_id
            workflow_groups = self._group_by_workflow(executions)
            add_span_event("hierarchy.grouped_by_workflow", workflow_count=len(workflow_groups))

            # Build hierarchical structures
            hierarchical_executions = []
            for workflow_id, execution_list in workflow_groups.items():
                try:
                    hierarchy = self._build_workflow_hierarchy(workflow_id, execution_list)
                    if hierarchy:
                        hierarchical_executions.append(hierarchy)
                except Exception as e:
                    add_span_event("hierarchy.workflow_failed",
                                  workflow_id=workflow_id, error=str(e))
                    # NO FALLBACK - fail fast for individual workflows
                    raise Exception(f"Failed to build hierarchy for workflow {workflow_id}: {str(e)}")

            add_span_event("hierarchy.hierarchies_built",
                          hierarchy_count=len(hierarchical_executions))

            # Sort by creation time (newest first)
            hierarchical_executions.sort(
                key=lambda x: x.get('created_at', ''),
                reverse=True
            )

            return hierarchical_executions

        except Exception as e:
            add_span_event("hierarchy.fetch_failed", error=str(e))
            raise Exception(f"Failed to build execution hierarchies: {str(e)}")

    def _group_by_workflow(self, executions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group executions by workflow_id.

        Args:
            executions: List of flat execution records

        Returns:
            Dictionary mapping workflow_id to list of executions

        Raises:
            ValueError: If executions missing required fields (NO FALLBACK)
        """
        grouped = {}

        for execution in executions:
            # Validate required fields - NO FALLBACK
            if 'workflow_id' not in execution:
                raise ValueError("Execution missing required field: workflow_id")

            workflow_id = execution['workflow_id']
            if not workflow_id:
                raise ValueError("workflow_id cannot be empty")

            if workflow_id not in grouped:
                grouped[workflow_id] = []

            grouped[workflow_id].append(execution)

        return grouped

    def _build_workflow_hierarchy(self, workflow_id: str,
                                 executions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Build hierarchical structure for a single workflow.

        Args:
            workflow_id: Workflow identifier
            executions: List of executions for this workflow

        Returns:
            Hierarchical execution structure or None if no main execution

        Raises:
            ValueError: Missing required data (NO FALLBACK)
        """
        if not executions:
            raise ValueError(f"No executions provided for workflow {workflow_id}")

        # Find main workflow execution (executor_type = 'workflow')
        main_execution = None
        step_executions = []

        for execution in executions:
            executor_type = execution.get('executor_type', '')

            if executor_type == 'workflow':
                if main_execution is not None:
                    # Multiple workflow executions - shouldn't happen, but handle gracefully
                    add_span_event("hierarchy.multiple_workflow_executions",
                                  workflow_id=workflow_id)
                main_execution = execution
            else:
                step_executions.append(execution)

        # NO FALLBACK - require main execution
        if not main_execution:
            raise ValueError(f"No main workflow execution found for workflow {workflow_id}")

        # Build execution_steps from step executions
        execution_steps = []
        for i, step_execution in enumerate(step_executions):
            step = self._build_execution_step(step_execution, i + 1)
            execution_steps.append(step)

        # Sort steps by executed_at time
        execution_steps.sort(
            key=lambda x: x.get('executed_at', ''),
            reverse=False  # Oldest first for steps
        )

        # Build hierarchical structure
        hierarchy = {
            'id': main_execution['id'],
            'workflow_id': workflow_id,
            'status': self._map_execution_status(main_execution.get('execution_status')),
            'risk_level': self._extract_risk_level(main_execution),
            'priority': 'normal',  # Default priority
            'workflow_type': self._extract_workflow_type(main_execution),
            'created_at': main_execution.get('created_at', ''),
            'action_item': self._extract_action_item(main_execution),
            'execution_steps': execution_steps
        }

        return hierarchy

    def _build_execution_step(self, step_execution: Dict[str, Any], step_number: int) -> Dict[str, Any]:
        """Build execution step from step execution record.

        Args:
            step_execution: Step execution record
            step_number: Sequential step number

        Returns:
            Execution step structure
        """
        executor_type = step_execution.get('executor_type', 'unknown')

        # Extract step details from execution payload if available
        step_action = f"{executor_type.replace('_', ' ').title()} execution"
        step_details = f"Execute using {executor_type}"

        # Try to extract more specific details from payload
        payload = step_execution.get('execution_payload', {})
        if isinstance(payload, dict):
            workflow_steps = payload.get('workflow_steps', [])
            if isinstance(workflow_steps, list) and len(workflow_steps) >= step_number:
                step_data = workflow_steps[step_number - 1]
                if isinstance(step_data, dict):
                    step_action = step_data.get('step_action', step_action)
                    step_details = step_data.get('details', step_details)

        return {
            'step_number': step_number,
            'action': step_action,
            'tool_needed': executor_type,
            'details': step_details,
            'status': self._map_execution_status(step_execution.get('execution_status')),
            'result': self._extract_step_result(step_execution),
            'executed_at': step_execution.get('executed_at')
        }

    def _map_execution_status(self, execution_status: str) -> str:
        """Map database execution status to UI status.

        Args:
            execution_status: Database status

        Returns:
            UI-compatible status
        """
        status_mapping = {
            'executed': 'EXECUTED',
            'failed': 'ERROR',
            'pending': 'PENDING',
            'in_progress': 'IN_PROGRESS'
        }

        return status_mapping.get(execution_status, 'PENDING')

    def _extract_risk_level(self, execution: Dict[str, Any]) -> Optional[str]:
        """Extract risk level from execution metadata.

        Args:
            execution: Execution record

        Returns:
            Risk level or None
        """
        metadata = execution.get('metadata', {})
        if isinstance(metadata, dict):
            risk_level = metadata.get('risk_level')
            if risk_level in ['LOW', 'MEDIUM', 'HIGH']:
                return risk_level

        return None

    def _extract_workflow_type(self, execution: Dict[str, Any]) -> Optional[str]:
        """Extract workflow type from execution metadata.

        Args:
            execution: Execution record

        Returns:
            Workflow type or None
        """
        metadata = execution.get('metadata', {})
        if isinstance(metadata, dict):
            workflow_type = metadata.get('workflow_type')
            if workflow_type in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
                return workflow_type

        return None

    def _extract_action_item(self, execution: Dict[str, Any]) -> str:
        """Extract action item description from execution.

        Args:
            execution: Execution record

        Returns:
            Action item description
        """
        # Try to extract from payload
        payload = execution.get('execution_payload', {})
        if isinstance(payload, dict):
            workflow_data = payload.get('workflow_data', {})
            if isinstance(workflow_data, dict):
                action = workflow_data.get('action')
                if action:
                    return action

        # Default description
        return "Workflow execution"

    def _extract_step_result(self, step_execution: Dict[str, Any]) -> Optional[str]:
        """Extract step execution result.

        Args:
            step_execution: Step execution record

        Returns:
            Step result or None
        """
        status = step_execution.get('execution_status')

        if status == 'executed':
            return 'Completed successfully'
        elif status == 'failed':
            return step_execution.get('error_message', 'Execution failed')

        return None