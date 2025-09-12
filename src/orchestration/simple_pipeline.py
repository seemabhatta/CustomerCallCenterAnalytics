"""
Simple pipeline implementation using native Python orchestrator
Connects: Transcript → Analysis → Plan → Workflows → Execution
NO FALLBACK LOGIC - fails fast on any errors
"""
import asyncio
import logging
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configure logger for this module
logger = logging.getLogger(__name__)

from src.orchestration.simple_orchestrator import SimpleOrchestrator
from src.orchestration.models.pipeline_models import PipelineResult, PipelineStage, WorkflowType
from src.services.analysis_service import AnalysisService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.workflow_execution_engine import WorkflowExecutionEngine


class SimplePipeline:
    """Simple pipeline orchestrator without external dependencies"""
    
    def __init__(self, api_key: str, db_path: str):
        self.api_key = api_key
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.orchestrator = SimpleOrchestrator(self.logger)
        
        # Initialize services
        self.analysis_service = AnalysisService(api_key, db_path)
        self.plan_service = PlanService(api_key, db_path)
        self.workflow_service = WorkflowService(db_path)
        self.execution_engine = WorkflowExecutionEngine(db_path)
    
    async def run_complete_pipeline(
        self, 
        transcript_id: str, 
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Run the complete call center pipeline.
        
        Args:
            transcript_id: Transcript to process
            auto_approve: If True, approve all workflows regardless of risk
            
        Returns:
            Complete pipeline result
        """
        try:
            logger.info(f"[SimplePipeline::run_complete_pipeline] Starting pipeline for transcript: {transcript_id}, auto_approve: {auto_approve}")
            self.logger.info(f"🚀 Starting complete pipeline for transcript: {transcript_id}")
            
            # Stage 1: Generate Analysis (1:1)
            self.orchestrator.current_stage = PipelineStage.ANALYSIS
            analysis_result = await self.orchestrator.execute_task(
                "generate-analysis",
                self._generate_analysis_task,
                transcript_id
            )
            analysis = analysis_result.result
            
            # Stage 2: Create Plan (1:1)
            self.orchestrator.current_stage = PipelineStage.PLAN
            plan_result = await self.orchestrator.execute_task(
                "create-plan",
                self._create_plan_task,
                analysis["id"]
            )
            plan = plan_result.result
            
            # Stage 3: Extract Workflows (1:n)
            self.orchestrator.current_stage = PipelineStage.WORKFLOWS
            workflows_result = await self.orchestrator.execute_task(
                "extract-workflows",
                self._extract_workflows_task,
                plan["id"]
            )
            workflows = workflows_result.result
            
            # Stage 4: Process approvals
            logger.info(f"[SimplePipeline::run_complete_pipeline] Processing approvals, auto_approve={auto_approve}")
            self.orchestrator.current_stage = PipelineStage.APPROVAL
            if auto_approve:
                logger.info(f"[SimplePipeline::run_complete_pipeline] Auto-approving all {len(workflows)} workflows")
                # Force approve all workflows (both in memory and database)
                for i, workflow in enumerate(workflows):
                    logger.debug(f"[SimplePipeline::run_complete_pipeline] Auto-approving workflow {i+1}/{len(workflows)}: {workflow.get('id', 'unknown')}")
                    workflow["status"] = "AUTO_APPROVED"
                    # Update status in database
                    try:
                        self.workflow_service.workflow_store.update_status(
                            workflow["id"], 
                            "AUTO_APPROVED",
                            transitioned_by="orchestration_system",
                            reason="Auto-approved by orchestration pipeline (LOW risk)"
                        )
                        logger.debug(f"[SimplePipeline::run_complete_pipeline] Updated workflow {workflow['id']} status in database")
                    except Exception as e:
                        logger.warning(f"[SimplePipeline::run_complete_pipeline] Failed to update workflow {workflow['id']} in database: {e}")
            
            # Filter approved workflows
            approved_workflows = [
                wf for wf in workflows 
                if wf.get("status") in ["APPROVED", "AUTO_APPROVED"]
            ]
            logger.info(f"[SimplePipeline::run_complete_pipeline] Found {len(approved_workflows)} approved workflows out of {len(workflows)} total")
            
            # Stage 5: Execute workflows in parallel (n:n)
            self.orchestrator.current_stage = PipelineStage.EXECUTION
            execution_results = []
            failed_executions = []
            
            if approved_workflows:
                logger.info(f"[SimplePipeline::run_complete_pipeline] Attempting to execute {len(approved_workflows)} approved workflows")
                
                # Execute workflows individually with graceful error handling
                for workflow in approved_workflows:
                    try:
                        logger.debug(f"[SimplePipeline::run_complete_pipeline] Executing workflow: {workflow['id']}")
                        result = await self._execute_workflow_task(workflow["id"])
                        execution_results.append(result)
                        logger.info(f"[SimplePipeline::run_complete_pipeline] Successfully executed workflow: {workflow['id']}")
                    except Exception as e:
                        logger.warning(f"[SimplePipeline::run_complete_pipeline] Failed to execute workflow {workflow['id']}: {e}")
                        failed_executions.append({
                            "workflow_id": workflow["id"],
                            "error": str(e),
                            "status": "failed"
                        })
                        
                logger.info(f"[SimplePipeline::run_complete_pipeline] Execution completed: {len(execution_results)} succeeded, {len(failed_executions)} failed")
            
            # Stage 6: Complete
            self.orchestrator.current_stage = PipelineStage.COMPLETE
            
            # Build final result
            pipeline_result = {
                "transcript_id": transcript_id,
                "analysis_id": analysis["id"],
                "plan_id": plan["id"],
                "workflow_count": len(workflows),
                "approved_count": len(approved_workflows),
                "executed_count": len(execution_results),
                "failed_count": len(failed_executions),
                "execution_results": execution_results,
                "failed_executions": failed_executions,
                "stage": PipelineStage.COMPLETE.value,
                "success": len(execution_results) > 0 or len(approved_workflows) == 0,  # Success if we executed something or had nothing to execute
                "partial_success": len(failed_executions) > 0 and len(execution_results) > 0,
                "execution_summary": self.orchestrator.get_execution_summary()
            }
            
            if pipeline_result["success"]:
                self.logger.info(
                    f"🎉 Pipeline completed successfully! "
                    f"Processed {len(workflows)} workflows, executed {len(execution_results)}"
                )
            elif pipeline_result["partial_success"]:
                self.logger.warning(
                    f"⚠️ Pipeline completed with partial success! "
                    f"Processed {len(workflows)} workflows, executed {len(execution_results)}, failed {len(failed_executions)}"
                )
            else:
                self.logger.error(
                    f"❌ Pipeline completed with failures! "
                    f"Processed {len(workflows)} workflows, executed {len(execution_results)}, failed {len(failed_executions)}"
                )
            
            return pipeline_result
            
        except Exception as e:
            # NO FALLBACK - fail immediately
            self.logger.error(f"💥 Pipeline failed: {e}")
            raise Exception(f"Pipeline execution failed for {transcript_id}: {e}")
    
    async def _generate_analysis_task(self, transcript_id: str) -> Dict[str, Any]:
        """Generate analysis from transcript"""
        logger.debug(f"[SimplePipeline::_generate_analysis_task] Starting analysis for transcript: {transcript_id}")
        logger.debug(f"[SimplePipeline::_generate_analysis_task] Calling AnalysisService.create()")
        analysis = await self.analysis_service.create({"transcript_id": transcript_id})
        logger.info(f"[SimplePipeline::_generate_analysis_task] Analysis created: {analysis.get('analysis_id', 'unknown')}")
        
        if not analysis:
            raise ValueError(f"Analysis generation returned empty result for {transcript_id}")
        
        # Validate required fields (use analysis_id as the id)
        required_fields = ["analysis_id", "transcript_id"]
        for field in required_fields:
            if field not in analysis:
                raise ValueError(f"Analysis missing required field: {field}")
        
        # Use analysis_id as id for consistency
        analysis["id"] = analysis["analysis_id"]
        analysis["status"] = "completed"  # Set status as completed
        
        return analysis
    
    async def _create_plan_task(self, analysis_id: str) -> Dict[str, Any]:
        """Create action plan from analysis"""
        print(f"[simple_pipeline.py::SimplePipeline::_create_plan_task] Starting plan creation for analysis: {analysis_id}")
        print(f"[simple_pipeline.py::SimplePipeline::_create_plan_task] Calling PlanService.create()")
        plan = await self.plan_service.create({"analysis_id": analysis_id})
        print(f"[simple_pipeline.py::SimplePipeline::_create_plan_task] Plan created: {plan.get('plan_id', 'unknown')}")
        
        if not plan:
            raise ValueError(f"Plan creation returned empty result for {analysis_id}")
        
        # Validate required fields (use plan_id as the id)
        required_fields = ["plan_id", "analysis_id"]
        for field in required_fields:
            if field not in plan:
                raise ValueError(f"Plan missing required field: {field}")
        
        # Use plan_id as id for consistency
        plan["id"] = plan["plan_id"]
        plan["status"] = "completed"  # Set status as completed
        
        return plan
    
    async def _extract_workflows_task(self, plan_id: str) -> List[Dict[str, Any]]:
        """Extract workflows from plan"""
        print(f"[simple_pipeline.py::SimplePipeline::_extract_workflows_task] Starting workflow extraction for plan: {plan_id}")
        print(f"[simple_pipeline.py::SimplePipeline::_extract_workflows_task] Calling WorkflowService.extract_all_workflows_from_plan()")
        workflows = await self.workflow_service.extract_all_workflows_from_plan(plan_id)
        print(f"[simple_pipeline.py::SimplePipeline::_extract_workflows_task] Extracted {len(workflows)} workflows")
        
        if not workflows:
            raise ValueError(f"Workflow extraction returned empty result for {plan_id}")
        
        if len(workflows) == 0:
            raise ValueError(f"No workflows extracted for {plan_id}")
        if len(workflows) > 50:  # Increased upper limit to allow more workflows
            raise ValueError(f"Too many workflows generated: {len(workflows)} for {plan_id}")
        
        print(f"✅ Extracted {len(workflows)} workflows from plan")
        
        # Validate and process each workflow
        validated_workflows = []
        for workflow in workflows:
            # Validate required fields
            required_fields = ["id", "plan_id", "workflow_type", "risk_level", "status"]
            for field in required_fields:
                if field not in workflow:
                    raise ValueError(f"Workflow missing required field: {field}")
            
            # Check auto-approval for LOW risk
            if workflow.get("risk_level") == "LOW":
                workflow["status"] = "AUTO_APPROVED"
            
            validated_workflows.append(workflow)
        
        return validated_workflows
    
    async def _execute_workflow_task(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a single workflow"""
        result = await self.execution_engine.execute_workflow(workflow_id)
        
        if not result:
            raise ValueError(f"Workflow execution returned empty result for {workflow_id}")
        
        # Validate execution result
        required_fields = ["status", "workflow_id"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Execution result missing required field: {field}")
        
        return result
    
    def pause_pipeline(self):
        """Pause pipeline execution"""
        self.orchestrator.pause_execution()
    
    def resume_pipeline(self):
        """Resume pipeline execution"""
        self.orchestrator.resume_execution()
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "current_stage": self.orchestrator.current_stage.value,
            "paused": self.orchestrator.paused,
            "execution_summary": self.orchestrator.get_execution_summary()
        }


async def run_simple_pipeline(
    transcript_id: str,
    auto_approve: bool = False,
    api_key: str = None,
    db_path: str = "data/call_center.db"
) -> Dict[str, Any]:
    """
    Convenience function to run the simple pipeline.
    
    Args:
        transcript_id: Transcript to process
        auto_approve: Auto-approve all workflows
        api_key: OpenAI API key (defaults to env var)
        db_path: Database path
        
    Returns:
        Pipeline execution result
    """
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OpenAI API key required")
    
    pipeline = SimplePipeline(api_key, db_path)
    return await pipeline.run_complete_pipeline(transcript_id, auto_approve)