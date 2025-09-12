"""
Approval workflow tasks for orchestration pipeline
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any, List
from prefect import task
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@task(name="request-approval", retries=0, task_run_name="Approval for {workflow_id}")
async def request_approval_task(workflow: Dict[str, Any], timeout_hours: int = 24) -> Dict[str, Any]:
    """
    Request human approval for high-risk workflows.
    Creates approval request and waits for response.
    NO FALLBACK - fails fast if approval process fails.
    
    Args:
        workflow: Workflow requiring approval
        timeout_hours: Hours to wait for approval
        
    Returns:
        Approval response data
        
    Raises:
        Exception: If approval process fails (NO FALLBACK)
    """
    try:
        # Only HIGH and MEDIUM risk workflows need approval
        # LOW risk are auto-approved in workflow_tasks
        if workflow.get("risk_level") == "LOW":
            return {
                "workflow_id": workflow["id"],
                "approved": True,
                "approver": "system",
                "reason": "Auto-approved: LOW risk",
                "timestamp": "auto"
            }
        
        # For demo purposes, we'll simulate approval request
        # In production, this would integrate with approval system
        approval_request = {
            "workflow_id": workflow["id"],
            "action_item": workflow.get("workflow_data", {}).get("action_item", "Unknown action"),
            "risk_level": workflow["risk_level"],
            "workflow_type": workflow["workflow_type"],
            "requires_approval": True,
            "timeout_hours": timeout_hours
        }
        
        # TODO: Integrate with actual approval system
        # For now, we'll create a placeholder that fails fast
        raise NotImplementedError("Human approval system not yet implemented")
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Approval request failed: {e}")


@task(name="check-approval-status", retries=0)
async def check_approval_status_task(workflow_id: str) -> Dict[str, Any]:
    """
    Check status of approval request.
    NO FALLBACK - fails fast if status check fails.
    
    Args:
        workflow_id: Workflow ID to check approval for
        
    Returns:
        Current approval status
        
    Raises:
        Exception: If status check fails (NO FALLBACK)
    """
    try:
        # TODO: Implement approval status check
        # This would query the approval system for current status
        raise NotImplementedError("Approval status check not yet implemented")
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Approval status check failed: {e}")


@task(name="filter-approved-workflows", retries=0)
async def filter_approved_workflows_task(workflows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter workflows to only include approved ones (APPROVED or AUTO_APPROVED).
    
    Args:
        workflows: List of workflows to filter
        
    Returns:
        List of approved workflows ready for execution
    """
    approved_statuses = ["APPROVED", "AUTO_APPROVED"]
    approved_workflows = [
        workflow for workflow in workflows 
        if workflow.get("status") in approved_statuses
    ]
    
    return approved_workflows