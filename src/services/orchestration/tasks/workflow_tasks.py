"""
Workflow extraction tasks for orchestration pipeline
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any, List
from prefect import task
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@task(name="extract-workflows", retries=0, task_run_name="Workflows for {plan_id}")
async def extract_workflows_task(plan_id: str) -> List[Dict[str, Any]]:
    """
    Extract all 4 workflow types from plan using LLM agent.
    NO FALLBACK - fails fast if extraction fails.
    
    Args:
        plan_id: Plan ID to extract workflows from
        
    Returns:
        List of workflow data (4 types: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
        
    Raises:
        Exception: If workflow extraction fails (NO FALLBACK)
    """
    try:
        from src.services.workflow_service import WorkflowService
        
        # Initialize service
        service = WorkflowService(db_path="data/call_center.db")
        
        # Extract all workflows (4 types)
        workflows = await service.extract_all_workflows(plan_id)
        
        if not workflows:
            raise ValueError(f"Workflow extraction returned empty result for {plan_id}")
        
        if len(workflows) != 4:
            raise ValueError(f"Expected 4 workflows, got {len(workflows)} for {plan_id}")
        
        return workflows
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Workflow extraction failed: {e}")


@task(name="validate-workflow", retries=0)
async def validate_workflow_task(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate workflow has required fields and proper risk assessment.
    NO FALLBACK - fails fast if validation fails.
    
    Args:
        workflow: Workflow data to validate
        
    Returns:
        Validated workflow data
        
    Raises:
        ValueError: If workflow is invalid (NO FALLBACK)
    """
    required_fields = ["id", "plan_id", "workflow_type", "risk_level", "status"]
    
    for field in required_fields:
        if field not in workflow:
            raise ValueError(f"Workflow missing required field: {field}")
    
    # Validate workflow_type
    valid_types = ["BORROWER", "ADVISOR", "SUPERVISOR", "LEADERSHIP"]
    if workflow.get("workflow_type") not in valid_types:
        raise ValueError(f"Invalid workflow_type: {workflow.get('workflow_type')}")
    
    # Validate risk_level
    valid_risks = ["LOW", "MEDIUM", "HIGH"]
    if workflow.get("risk_level") not in valid_risks:
        raise ValueError(f"Invalid risk_level: {workflow.get('risk_level')}")
    
    # Validate status
    valid_statuses = ["AWAITING_APPROVAL", "AUTO_APPROVED", "APPROVED", "REJECTED"]
    if workflow.get("status") not in valid_statuses:
        raise ValueError(f"Invalid status: {workflow.get('status')}")
    
    return workflow


@task(name="check-auto-approval", retries=0)
async def check_auto_approval_task(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if workflow qualifies for auto-approval (LOW risk).
    Updates status if eligible.
    
    Args:
        workflow: Workflow data to check
        
    Returns:
        Workflow with updated status if auto-approved
    """
    # LOW risk workflows are auto-approved
    if workflow.get("risk_level") == "LOW":
        workflow["status"] = "AUTO_APPROVED"
    
    return workflow