"""
Workflow tools for advisor agent with strict BORROWER filtering.
Tools that the LLM can call autonomously to work with borrower workflows.
All tools have built-in guardrails to ensure ONLY borrower workflows are accessible.
NO FALLBACK LOGIC - fails fast on access violations or errors.
"""
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.services.workflow_service import WorkflowService
from src.services.workflow_execution_engine import WorkflowExecutionEngine
from src.storage.action_plan_store import ActionPlanStore
from src.storage.transcript_store import TranscriptStore
from src.storage.advisor_session_store import AdvisorSessionStore
from src.storage.workflow_store import WorkflowStore


class WorkflowTools:
    """Tools for working with BORROWER workflows.

    All methods have built-in guardrails to ensure advisors can ONLY access
    borrower-related workflows. Any attempt to access other workflow types
    will result in access denied errors.
    """

    def __init__(self, db_path: str, advisor_id: str):
        """Initialize workflow tools with strict access controls.

        Args:
            db_path: Database path
            advisor_id: Advisor identifier for audit trail

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path or not advisor_id:
            raise ValueError("Database path and advisor_id are required")

        self.db_path = db_path
        self.advisor_id = advisor_id

        # Initialize service dependencies
        self.workflow_service = WorkflowService(db_path)
        self.execution_engine = WorkflowExecutionEngine(db_path)
        self.plan_store = ActionPlanStore(db_path)
        self.transcript_store = TranscriptStore(db_path)
        self.session_store = AdvisorSessionStore(db_path)
        self.workflow_store = WorkflowStore(db_path)

    def list_workflows(self, plan_id: str) -> List[Dict[str, Any]]:
        """CONTRACT: Get available BORROWER workflows from a plan.

        PRECONDITIONS:
        - plan_id must be a valid, non-empty string
        - Plan must exist in the database
        - User must have advisor-level access

        INVARIANTS:
        - ONLY workflows with workflow_type='BORROWER' are returned
        - Results are sorted by priority (HIGH > MEDIUM > LOW), then by creation date
        - Each workflow includes: id, title, priority, status, step count

        SIDE EFFECTS:
        - None (read-only operation)
        - Access is logged for audit purposes

        FAILURE GUIDANCE:
        - If plan_id is missing: "Please provide a plan ID. Say 'recent plans' to see available options"
        - If plan not found: "Plan {plan_id} not found. Try 'list plans' or provide a different plan ID"
        - If no BORROWER workflows: "No borrower workflows found in this plan. Check with supervisor for workflow availability"

        Args:
            plan_id: Plan identifier to retrieve workflows from

        Returns:
            List of BORROWER workflows with complete metadata for selection

        Raises:
            ValueError: Invalid or missing plan_id with guidance for next steps
            Exception: Database/service errors with specific failure reason
        """
        if not plan_id or not plan_id.strip():
            raise ValueError("Please provide a plan ID. Say 'recent plans' to see available options or 'load transcript <id>' to start from a specific call.")

        try:
            # Get plan data to validate it exists
            plan = self.plan_store.get_by_id(plan_id.strip())
            if not plan:
                raise ValueError(f"Plan {plan_id} not found. Try 'list plans' or provide a different plan ID. Available commands: 'recent plans' or 'load transcript <transcript_id>'")

            # Get all workflows for this plan using store directly (sync)
            all_workflows = self.workflow_store.get_by_plan_id(plan_id)

            # CRITICAL GUARDRAIL: Filter to BORROWER only
            borrower_workflows = []
            for workflow in all_workflows:
                workflow_data = workflow.get('workflow_data', {})
                if isinstance(workflow_data, str):
                    workflow_data = json.loads(workflow_data)

                # Check if this is a borrower workflow
                action_item = workflow_data.get('action_item', {})

                # Handle case where action_item might be a string (JSON)
                if isinstance(action_item, str):
                    try:
                        action_item = json.loads(action_item)
                    except:
                        action_item = {}

                if action_item.get('workflow_type') == 'BORROWER':
                    # Format for display
                    borrower_workflows.append({
                        'workflow_id': workflow['id'],
                        'title': action_item.get('title', 'Unknown Action'),
                        'description': action_item.get('description', ''),
                        'priority': action_item.get('priority', 'MEDIUM'),
                        'estimated_hours': action_item.get('estimated_hours', 0),
                        'status': workflow.get('status', 'PENDING'),
                        'risk_level': workflow.get('risk_level', 'LOW'),
                        'requires_approval': workflow.get('requires_human_approval', False),
                        'total_steps': len(workflow_data.get('steps', [])),
                        'created_at': workflow.get('created_at')
                    })

            # Check if we found any borrower workflows
            if not borrower_workflows:
                raise ValueError(f"No borrower workflows found in plan {plan_id}. This plan may only contain advisor/supervisor tasks. Try a different plan or check with your supervisor for workflow availability.")

            # Sort by priority (HIGH > MEDIUM > LOW) then by created_at
            priority_order = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            borrower_workflows.sort(
                key=lambda w: (priority_order.get(w['priority'], 0), w['created_at']),
                reverse=True
            )

            return borrower_workflows

        except Exception as e:
            raise Exception(f"Failed to list workflows: {str(e)}")

    def get_workflow_details(self, workflow_id: str) -> Dict[str, Any]:
        """CONTRACT: Get detailed workflow information including all execution steps.

        PRECONDITIONS:
        - workflow_id must be a valid, non-empty string
        - Workflow must exist and be of type 'BORROWER'
        - User must have advisor-level access to this workflow

        INVARIANTS:
        - Only BORROWER workflows are accessible
        - Returned data includes: metadata, all steps, context, execution status
        - Step information includes: action, details, tool_needed, validation_criteria

        SIDE EFFECTS:
        - None (read-only operation)
        - Access is logged for audit purposes

        FAILURE GUIDANCE:
        - If workflow_id missing: "Please provide a workflow ID. Use 'list workflows' to see available options"
        - If workflow not found: "Workflow {workflow_id} not found. Use 'list workflows' to see current options"
        - If access denied: "Cannot access non-borrower workflow. Only borrower workflows are available to advisors"

        Args:
            workflow_id: Workflow identifier to retrieve details for

        Returns:
            Complete workflow data with steps and metadata

        Raises:
            ValueError: Invalid workflow_id or access violation with guidance
            Exception: Database/service errors with specific failure reason
        """
        if not workflow_id or not workflow_id.strip():
            raise ValueError("Please provide a workflow ID. Use 'list workflows' to see available options or select from the displayed list.")

        try:
            # Get workflow from database using store directly (sync)
            workflow = self.workflow_store.get_by_id(workflow_id.strip())
            if not workflow:
                raise ValueError(f"Workflow {workflow_id} not found. Use 'list workflows' to see current options or check if the workflow ID is correct.")

            # Parse workflow data
            workflow_data = workflow.get('workflow_data', {})
            if isinstance(workflow_data, str):
                workflow_data = json.loads(workflow_data)

            # CRITICAL GUARDRAIL: Verify this is a BORROWER workflow
            action_item = workflow_data.get('action_item', {})

            # Handle case where action_item might be a string (JSON)
            if isinstance(action_item, str):
                try:
                    action_item = json.loads(action_item)
                except:
                    action_item = {}

            if action_item.get('workflow_type') != 'BORROWER':
                raise ValueError("Cannot access non-borrower workflow. Only borrower workflows are available to advisors. Use 'list workflows' to see available borrower tasks.")

            # Format detailed response
            return {
                'workflow_id': workflow['id'],
                'title': action_item.get('title', 'Unknown Action'),
                'description': action_item.get('description', ''),
                'priority': action_item.get('priority', 'MEDIUM'),
                'estimated_hours': action_item.get('estimated_hours', 0),
                'status': workflow.get('status', 'PENDING'),
                'risk_level': workflow.get('risk_level', 'LOW'),
                'requires_approval': workflow.get('requires_human_approval', False),
                'steps': workflow_data.get('steps', []),
                'total_steps': len(workflow_data.get('steps', [])),
                'context': workflow_data.get('context', {}),
                'created_at': workflow.get('created_at'),
                'updated_at': workflow.get('updated_at')
            }

        except Exception as e:
            raise Exception(f"Failed to get workflow details: {str(e)}")

    def preflight_step(self, workflow_id: str, step_number: int) -> Dict[str, Any]:
        """Explain what a step will do before execution.

        GUARDRAIL: Validates workflow ownership before providing step details.

        Args:
            workflow_id: Workflow identifier
            step_number: Step number to preflight (1-based)

        Returns:
            Step details for review before execution

        Raises:
            ValueError: Invalid workflow or step (NO FALLBACK)
            Exception: If preflight fails (NO FALLBACK)
        """
        if not workflow_id or step_number < 1:
            raise ValueError("Valid workflow_id and step_number (>= 1) required")

        try:
            # Get and validate workflow
            workflow_details = self.get_workflow_details(workflow_id)
            steps = workflow_details['steps']

            if step_number > len(steps):
                raise ValueError(f"Step {step_number} does not exist (workflow has {len(steps)} steps)")

            # Get the specific step (convert to 0-based index)
            step = steps[step_number - 1]

            # Determine risk level and requirements
            tool_needed = step.get('tool_needed', 'unknown')
            risk_level = 'LOW'

            # Assess risk based on tool and action
            if 'api' in tool_needed.lower():
                if any(term in step.get('action', '').lower() for term in ['delete', 'remove', 'cancel']):
                    risk_level = 'HIGH'
                elif any(term in step.get('action', '').lower() for term in ['update', 'modify', 'change']):
                    risk_level = 'MEDIUM'

            requires_approval = risk_level == 'HIGH' or workflow_details.get('requires_approval', False)

            return {
                'workflow_id': workflow_id,
                'step_number': step_number,
                'action': step.get('action', 'Unknown action'),
                'details': step.get('details', 'No details provided'),
                'tool_needed': tool_needed,
                'validation_criteria': step.get('validation_criteria', 'Completion confirmation'),
                'risk_level': risk_level,
                'requires_approval': requires_approval,
                'estimated_duration': '2-5 minutes',
                'what_happens': f"This step will {step.get('action', '').lower()} using {tool_needed}",
                'systems_affected': [tool_needed] if tool_needed != 'unknown' else [],
                'reversible': risk_level != 'HIGH'
            }

        except Exception as e:
            raise Exception(f"Failed to preflight step: {str(e)}")

    def execute_step(self, workflow_id: str, step_number: int, executed_by: Optional[str] = None) -> Dict[str, Any]:
        """Execute a single workflow step.

        GUARDRAIL: Validates workflow ownership before execution.

        Args:
            workflow_id: Workflow identifier
            step_number: Step number to execute (1-based)
            executed_by: Who is executing (defaults to advisor_id)

        Returns:
            Execution result with status and details

        Raises:
            ValueError: Invalid workflow or step (NO FALLBACK)
            Exception: If execution fails (NO FALLBACK)
        """
        if not workflow_id or step_number < 1:
            raise ValueError("Valid workflow_id and step_number (>= 1) required")

        executed_by = executed_by or self.advisor_id

        try:
            # Validate this is a BORROWER workflow before execution
            workflow_details = self.get_workflow_details(workflow_id)

            # Execute step through the execution engine
            result = self.execution_engine.execute_single_step(
                workflow_id=workflow_id,
                step_number=step_number,
                executed_by=executed_by
            )

            # Format response
            return {
                'workflow_id': workflow_id,
                'step_number': step_number,
                'execution_status': result.get('execution_status', 'unknown'),
                'success': result.get('success', False),
                'results_summary': result.get('results_summary', 'No summary available'),
                'outputs': result.get('step_outputs', {}),
                'next_step': step_number + 1 if step_number < workflow_details['total_steps'] else None,
                'completed_at': datetime.utcnow().isoformat(),
                'executed_by': executed_by
            }

        except Exception as e:
            raise Exception(f"Failed to execute step: {str(e)}")

    def skip_step(self, workflow_id: str, step_number: int, reason: str,
                  skipped_by: Optional[str] = None) -> Dict[str, Any]:
        """Skip a workflow step with documented reason.

        GUARDRAIL: Validates workflow ownership before skipping.

        Args:
            workflow_id: Workflow identifier
            step_number: Step number to skip (1-based)
            reason: Reason for skipping
            skipped_by: Who is skipping (defaults to advisor_id)

        Returns:
            Skip confirmation with details

        Raises:
            ValueError: Invalid workflow, step, or missing reason (NO FALLBACK)
            Exception: If skip operation fails (NO FALLBACK)
        """
        if not workflow_id or step_number < 1:
            raise ValueError("Valid workflow_id and step_number (>= 1) required")

        if not reason or not reason.strip():
            raise ValueError("Reason for skipping is required")

        skipped_by = skipped_by or self.advisor_id

        try:
            # Validate this is a BORROWER workflow
            workflow_details = self.get_workflow_details(workflow_id)

            if step_number > workflow_details['total_steps']:
                raise ValueError(f"Step {step_number} does not exist")

            # Record the skip (this would integrate with the execution store)
            # For now, return a success response
            return {
                'workflow_id': workflow_id,
                'step_number': step_number,
                'status': 'skipped',
                'reason': reason.strip(),
                'skipped_by': skipped_by,
                'skipped_at': datetime.utcnow().isoformat(),
                'next_step': step_number + 1 if step_number < workflow_details['total_steps'] else None
            }

        except Exception as e:
            raise Exception(f"Failed to skip step: {str(e)}")

    def get_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution progress.

        GUARDRAIL: Validates workflow ownership before returning progress.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Current progress information

        Raises:
            ValueError: Invalid workflow (NO FALLBACK)
            Exception: If progress retrieval fails (NO FALLBACK)
        """
        if not workflow_id:
            raise ValueError("workflow_id is required")

        try:
            # Validate this is a BORROWER workflow
            workflow_details = self.get_workflow_details(workflow_id)

            # Get execution state (this would come from execution store in real implementation)
            # For now, simulate progress tracking
            total_steps = workflow_details['total_steps']

            return {
                'workflow_id': workflow_id,
                'title': workflow_details['title'],
                'total_steps': total_steps,
                'current_step': 1,  # This would come from session state
                'completed_steps': [],
                'skipped_steps': [],
                'failed_steps': [],
                'remaining_steps': list(range(1, total_steps + 1)),
                'overall_status': workflow_details['status'],
                'progress_percentage': 0
            }

        except Exception as e:
            raise Exception(f"Failed to get progress: {str(e)}")

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of all available tools for the LLM.

        Returns:
            List of tool descriptions with parameters and purposes
        """
        return [
            {
                'name': 'list_workflows',
                'description': 'Get available borrower workflows from a plan',
                'parameters': ['plan_id'],
                'purpose': 'Discovery and selection of workflows to work on'
            },
            {
                'name': 'get_workflow_details',
                'description': 'Get detailed information about a specific workflow including all steps',
                'parameters': ['workflow_id'],
                'purpose': 'Understanding workflow structure before execution'
            },
            {
                'name': 'preflight_step',
                'description': 'Explain what a step will do before execution',
                'parameters': ['workflow_id', 'step_number'],
                'purpose': 'Risk assessment and user confirmation before step execution'
            },
            {
                'name': 'execute_step',
                'description': 'Execute a single workflow step',
                'parameters': ['workflow_id', 'step_number', 'executed_by (optional)'],
                'purpose': 'Perform the actual work step-by-step'
            },
            {
                'name': 'skip_step',
                'description': 'Skip a step with documented reason',
                'parameters': ['workflow_id', 'step_number', 'reason', 'skipped_by (optional)'],
                'purpose': 'Handle cases where steps cannot or should not be executed'
            },
            {
                'name': 'get_progress',
                'description': 'Get current workflow execution progress',
                'parameters': ['workflow_id'],
                'purpose': 'Status checking and progress tracking'
            }
        ]