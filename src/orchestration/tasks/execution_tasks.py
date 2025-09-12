"""
Workflow execution tasks for orchestration pipeline
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any
from prefect import task
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@task(name="execute-workflow", retries=0, task_run_name="Execute {workflow_id}")
async def execute_workflow_task(workflow_id: str) -> Dict[str, Any]:
    """
    Execute approved workflow using execution engine.
    NO FALLBACK - fails fast if execution fails.
    
    Args:
        workflow_id: Workflow ID to execute
        
    Returns:
        Execution result with status and details
        
    Raises:
        Exception: If workflow execution fails (NO FALLBACK)
    """
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        
        # Initialize execution engine
        engine = WorkflowExecutionEngine(
            api_key=os.getenv("OPENAI_API_KEY"),
            db_path="data/call_center.db"
        )
        
        # Execute workflow
        result = await engine.execute_workflow(workflow_id)
        
        if not result:
            raise ValueError(f"Workflow execution returned empty result for {workflow_id}")
        
        # Verify execution status
        if not result.get("status"):
            raise ValueError(f"Execution result missing status for {workflow_id}")
        
        return result
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Workflow execution failed: {e}")


@task(name="validate-execution", retries=0)
async def validate_execution_task(execution_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate execution result has proper format.
    NO FALLBACK - fails fast if validation fails.
    
    Args:
        execution_result: Execution result to validate
        
    Returns:
        Validated execution result
        
    Raises:
        ValueError: If execution result is invalid (NO FALLBACK)
    """
    required_fields = ["status", "workflow_id"]
    
    for field in required_fields:
        if field not in execution_result:
            raise ValueError(f"Execution result missing required field: {field}")
    
    # Validate status indicates completion
    valid_statuses = ["executed", "completed", "success"]
    status = execution_result.get("status", "").lower()
    if status not in valid_statuses:
        raise ValueError(f"Invalid execution status: {status}")
    
    return execution_result