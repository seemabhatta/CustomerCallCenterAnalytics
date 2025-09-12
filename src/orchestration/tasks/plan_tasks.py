"""
Plan generation tasks for orchestration pipeline
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any
from prefect import task
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@task(name="create-plan", retries=0, task_run_name="Plan for {analysis_id}")
async def create_plan_task(analysis_id: str) -> Dict[str, Any]:
    """
    Create action plan from analysis using LLM agent.
    NO FALLBACK - fails fast if plan cannot be created.
    
    Args:
        analysis_id: Analysis ID to create plan from
        
    Returns:
        Plan data with ID
        
    Raises:
        Exception: If plan creation fails (NO FALLBACK)
    """
    try:
        from src.services.plan_service import PlanService
        
        # Initialize service
        service = PlanService(
            api_key=os.getenv("OPENAI_API_KEY"),
            db_path="data/call_center.db"
        )
        
        # Create plan
        plan = await service.create_plan(analysis_id)
        
        if not plan:
            raise ValueError(f"Plan creation returned empty result for {analysis_id}")
        
        return plan
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Plan creation failed: {e}")


@task(name="validate-plan", retries=0)
async def validate_plan_task(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate plan has required fields.
    NO FALLBACK - fails fast if validation fails.
    
    Args:
        plan: Plan data to validate
        
    Returns:
        Validated plan data
        
    Raises:
        ValueError: If plan is invalid (NO FALLBACK)
    """
    required_fields = ["id", "analysis_id", "status"]
    
    for field in required_fields:
        if field not in plan:
            raise ValueError(f"Plan missing required field: {field}")
    
    if plan.get("status") != "completed":
        raise ValueError(f"Plan not completed: {plan.get('status')}")
    
    return plan