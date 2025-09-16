"""
Main orchestration pipeline flow
Connects: Transcript → Analysis → Plan → Workflows → Execution
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any, List
from prefect import flow, task
from prefect.futures import wait
import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from ..tasks.analysis_tasks import generate_analysis_task, validate_analysis_task
from ..tasks.plan_tasks import create_plan_task, validate_plan_task
from ..tasks.workflow_tasks import (
    extract_workflows_task, validate_workflow_task, check_auto_approval_task
)
from ..tasks.execution_tasks import execute_workflow_task, validate_execution_task
from ..tasks.approval_tasks import filter_approved_workflows_task
from src.orchestration.models.pipeline_models import PipelineResult, PipelineStage


@flow(name="call-center-pipeline", retries=0, log_prints=True)
async def call_center_pipeline(
    transcript_id: str, 
    auto_approve: bool = False,
    timeout_hours: int = 24
) -> Dict[str, Any]:
    """
    Complete call center analysis and workflow execution pipeline.
    
    Pipeline stages:
    1. Generate analysis from transcript
    2. Create action plan from analysis  
    3. Extract workflows from plan (4 types)
    4. Check auto-approval for LOW risk workflows
    5. Execute approved workflows in parallel
    
    Args:
        transcript_id: Transcript to process
        auto_approve: If True, approve all workflows regardless of risk
        timeout_hours: Hours to wait for manual approval
        
    Returns:
        Complete pipeline result with execution details
        
    Raises:
        Exception: If any stage fails (NO FALLBACK)
    """
    try:
        print(f"🚀 Starting pipeline for transcript: {transcript_id}")
        
        # Stage 1: Generate Analysis (1:1 relationship)
        print("📊 Stage 1: Generating analysis...")
        analysis = await generate_analysis_task(transcript_id)
        validated_analysis = await validate_analysis_task(analysis)
        print(f"✅ Analysis generated: {validated_analysis['id']}")
        
        # Stage 2: Create Plan (1:1 relationship)
        print("📋 Stage 2: Creating action plan...")
        plan = await create_plan_task(validated_analysis["id"])
        validated_plan = await validate_plan_task(plan)
        print(f"✅ Plan created: {validated_plan['id']}")
        
        # Stage 3: Extract Workflows (1:n relationship - 4 types)
        print("🔄 Stage 3: Extracting workflows...")
        workflows = await extract_workflows_task(validated_plan["id"])
        
        # Validate and check auto-approval for each workflow in parallel
        print("🔍 Stage 3b: Validating and checking auto-approval...")
        validated_workflows = []
        for workflow in workflows:
            validated = await validate_workflow_task(workflow)
            approved = await check_auto_approval_task(validated)
            validated_workflows.append(approved)
        
        print(f"✅ Extracted {len(validated_workflows)} workflows")
        
        # Stage 4: Filter approved workflows
        print("🎯 Stage 4: Filtering approved workflows...")
        if auto_approve:
            # Force approve all workflows
            for workflow in validated_workflows:
                workflow["status"] = "AUTO_APPROVED"
        
        approved_workflows = await filter_approved_workflows_task(validated_workflows)
        print(f"✅ {len(approved_workflows)} workflows approved for execution")
        
        # Stage 5: Execute workflows in parallel (n:n relationship)
        print("⚡ Stage 5: Executing workflows in parallel...")
        execution_results = []
        
        if approved_workflows:
            # Execute all approved workflows in parallel
            execution_futures = [
                execute_workflow_task(workflow["id"]) 
                for workflow in approved_workflows
            ]
            
            # Wait for all executions to complete
            execution_results = await asyncio.gather(*execution_futures)
            
            # Validate all execution results
            validated_results = []
            for result in execution_results:
                validated = await validate_execution_task(result)
                validated_results.append(validated)
            
            execution_results = validated_results
        
        print(f"✅ Executed {len(execution_results)} workflows")
        
        # Build final result
        pipeline_result = {
            "transcript_id": transcript_id,
            "analysis_id": validated_analysis["id"],
            "plan_id": validated_plan["id"],
            "workflow_count": len(validated_workflows),
            "executed_count": len(execution_results),
            "execution_results": execution_results,
            "stage": PipelineStage.COMPLETE.value,
            "success": True
        }
        
        print(f"🎉 Pipeline completed successfully!")
        print(f"📈 Summary: {len(validated_workflows)} workflows, {len(execution_results)} executed")
        
        return pipeline_result
        
    except Exception as e:
        # NO FALLBACK - fail immediately with detailed error
        print(f"💥 Pipeline failed: {e}")
        raise Exception(f"Pipeline execution failed for {transcript_id}: {e}")


@flow(name="approval-pipeline", retries=0, log_prints=True)
async def approval_pipeline(
    workflows: List[Dict[str, Any]],
    timeout_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Human approval pipeline for high-risk workflows.
    This flow can be paused and resumed for human-in-the-loop approval.
    
    Args:
        workflows: List of workflows requiring approval
        timeout_hours: Hours to wait for approval
        
    Returns:
        List of workflows with approval status updated
        
    Raises:
        Exception: If approval process fails (NO FALLBACK)
    """
    try:
        print(f"👥 Starting approval pipeline for {len(workflows)} workflows")
        
        # TODO: Implement human approval workflow
        # This would:
        # 1. Create approval requests in external system
        # 2. Pause flow execution using pause_flow_run()
        # 3. Resume when approvals are received
        # 4. Update workflow statuses based on approval responses
        
        raise NotImplementedError("Human approval pipeline not yet implemented")
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        print(f"💥 Approval pipeline failed: {e}")
        raise Exception(f"Approval pipeline execution failed: {e}")


@flow(name="resume-pipeline", retries=0, log_prints=True) 
async def resume_pipeline(transcript_id: str, stage: str) -> Dict[str, Any]:
    """
    Resume pipeline execution from a specific stage.
    Supports stop/resume functionality.
    
    Args:
        transcript_id: Transcript being processed
        stage: Stage to resume from
        
    Returns:
        Pipeline result from resumed execution
        
    Raises:
        Exception: If resume fails (NO FALLBACK)
    """
    try:
        print(f"🔄 Resuming pipeline for {transcript_id} from stage: {stage}")
        
        # TODO: Implement stage-specific resume logic
        # This would:
        # 1. Load pipeline state from database
        # 2. Resume execution from specified stage
        # 3. Skip already completed stages
        
        raise NotImplementedError("Pipeline resume not yet implemented")
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        print(f"💥 Pipeline resume failed: {e}")
        raise Exception(f"Pipeline resume failed for {transcript_id}: {e}")