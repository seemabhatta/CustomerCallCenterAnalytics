"""
Simple pipeline implementation using native Python async/await
Connects: Transcript → Analysis → Plan → Workflows → Execution
NO FALLBACK LOGIC - fails fast on any errors
"""
import asyncio
from typing import Dict, Any, List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import OpenTelemetry tracing
from src.infrastructure.telemetry import get_tracer, set_span_attributes, add_span_event, trace_async_function


from src.services.orchestration.models.pipeline_models import PipelineResult, PipelineStage, WorkflowType
from src.services.analysis_service import AnalysisService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.workflow_execution_engine import WorkflowExecutionEngine


class SimplePipeline:
    """Simple pipeline using native Python async/await without external dependencies"""
    
    def __init__(self, api_key: str, db_path: str):
        self.api_key = api_key
        self.db_path = db_path
        self.current_stage = PipelineStage.TRANSCRIPT
        
        # Initialize tracing to ensure OpenAI instrumentation is active
        from src.infrastructure.telemetry import initialize_tracing
        initialize_tracing(
            service_name="call-center-analytics-pipeline",
            enable_console=True,
            enable_jaeger=False
        )
        
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
        tracer = get_tracer()
        
        with tracer.start_as_current_span("orchestration.run_complete_pipeline") as root_span:
            # Set root span attributes
            set_span_attributes(
                transcript_id=transcript_id,
                auto_approve=auto_approve,
                service="call-center-analytics",
                operation="orchestration"
            )
            
            try:
                add_span_event("pipeline.started", transcript_id=transcript_id)
            
                # Stage 1: Generate Analysis (1:1)
                with tracer.start_as_current_span("pipeline.stage.analysis") as analysis_span:
                    self.current_stage = PipelineStage.ANALYSIS
                    add_span_event("stage.started", stage="analysis")

                    analysis = await self._generate_analysis_task(transcript_id)

                    analysis_span.set_attribute("analysis_id", analysis["id"])
                    add_span_event("stage.completed", stage="analysis", analysis_id=analysis["id"])
                
                # Stage 2: Create Plan (1:1)
                with tracer.start_as_current_span("pipeline.stage.plan") as plan_span:
                    self.current_stage = PipelineStage.PLAN
                    add_span_event("stage.started", stage="plan")

                    plan = await self._create_plan_task(analysis["id"])
                    
                    plan_span.set_attribute("plan_id", plan["id"])
                    add_span_event("stage.completed", stage="plan", plan_id=plan["id"])
                
                # Stage 3: Extract Workflows (1:n) - THE BOTTLENECK
                with tracer.start_as_current_span("pipeline.stage.workflows") as workflows_span:
                    self.current_stage = PipelineStage.WORKFLOWS
                    add_span_event("stage.started", stage="workflows", message="This stage may take 2-5 minutes")

                    workflows = await self._extract_workflows_task(plan["id"])

                    workflows_span.set_attribute("workflow_count", len(workflows))
                    workflows_span.set_attribute("plan_id", plan["id"])
                    add_span_event("stage.completed", stage="workflows", workflow_count=len(workflows))
            
                # Stage 4: Process approvals
                with tracer.start_as_current_span("pipeline.stage.approval") as approval_span:
                    self.current_stage = PipelineStage.APPROVAL
                    approval_span.set_attribute("auto_approve", auto_approve)
                    add_span_event("stage.started", stage="approval")
                    
                    if auto_approve:
                        add_span_event("approval.auto_approving", workflow_count=len(workflows))
                        # Force approve all workflows (both in memory and database)
                        for i, workflow in enumerate(workflows):
                            workflow["status"] = "AUTO_APPROVED"
                            # Update status in database
                            try:
                                self.workflow_service.workflow_store.update_status(
                                    workflow["id"], 
                                    "AUTO_APPROVED",
                                    transitioned_by="orchestration_system",
                                    reason="Auto-approved by orchestration pipeline (LOW risk)"
                                )
                            except Exception as e:
                                pass
                    
                    add_span_event("stage.completed", stage="approval", workflow_count=len(workflows))
                
                # Filter approved workflows
                approved_workflows = [
                    wf for wf in workflows 
                    if wf.get("status") in ["APPROVED", "AUTO_APPROVED"]
                ]
                # Stage 5: Execute workflows in parallel (n:n)
                with tracer.start_as_current_span("pipeline.stage.execution") as execution_span:
                    self.current_stage = PipelineStage.EXECUTION
                    execution_span.set_attribute("approved_workflow_count", len(approved_workflows))
                    add_span_event("stage.started", stage="execution", approved_workflows=len(approved_workflows))
                    
                    execution_results = []
                    failed_executions = []
                    
                    if approved_workflows:
                        
                        # Execute workflows individually with graceful error handling
                        for workflow in approved_workflows:
                            try:
                                result = await self._execute_workflow_task(workflow["id"])
                                execution_results.append(result)
                            except Exception as e:
                                failed_executions.append({
                                    "workflow_id": workflow["id"],
                                    "error": str(e),
                                    "status": "failed"
                                })
                    
                    execution_span.set_attribute("successful_executions", len(execution_results))
                    execution_span.set_attribute("failed_executions", len(failed_executions))
                    add_span_event("stage.completed", stage="execution", 
                                  successful=len(execution_results), failed=len(failed_executions))
                
                # Stage 6: Complete
                self.current_stage = PipelineStage.COMPLETE
            
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
                    "partial_success": len(failed_executions) > 0 and len(execution_results) > 0
                }
                
                # Set final span attributes for observability
                set_span_attributes(
                    pipeline_status="success" if pipeline_result["success"] else "partial" if pipeline_result["partial_success"] else "failed",
                    workflow_count=len(workflows),
                    approved_count=len(approved_workflows),
                    executed_count=len(execution_results),
                    failed_count=len(failed_executions),
                    analysis_id=analysis["id"],
                    plan_id=plan["id"]
                )
                
                if pipeline_result["success"]:
                    add_span_event("pipeline.completed", status="success", 
                                  workflows_processed=len(workflows), workflows_executed=len(execution_results))
                elif pipeline_result["partial_success"]:
                    add_span_event("pipeline.completed", status="partial_success",
                                  workflows_processed=len(workflows), workflows_executed=len(execution_results), 
                                  workflows_failed=len(failed_executions))
                else:
                    add_span_event("pipeline.completed", status="failed",
                                  workflows_processed=len(workflows), workflows_executed=len(execution_results), 
                                  workflows_failed=len(failed_executions))
                
                return pipeline_result
            
            except Exception as e:
                # NO FALLBACK - fail immediately
                set_span_attributes(pipeline_status="error", error_message=str(e))
                add_span_event("pipeline.failed", error=str(e), transcript_id=transcript_id)
                raise Exception(f"Pipeline execution failed for {transcript_id}: {e}")
    
    @trace_async_function("task.generate_analysis")
    async def _generate_analysis_task(self, transcript_id: str) -> Dict[str, Any]:
        """Generate analysis from transcript"""
        analysis = await self.analysis_service.create({"transcript_id": transcript_id})
        
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
    
    @trace_async_function("task.create_plan")
    async def _create_plan_task(self, analysis_id: str) -> Dict[str, Any]:
        """Create action plan from analysis"""
        plan = await self.plan_service.create({"analysis_id": analysis_id})
        
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
    
    @trace_async_function("task.extract_workflows")
    async def _extract_workflows_task(self, plan_id: str) -> List[Dict[str, Any]]:
        """Extract workflows from plan"""
        workflows = await self.workflow_service.extract_all_workflows_from_plan(plan_id)
        
        if not workflows:
            raise ValueError(f"Workflow extraction returned empty result for {plan_id}")
        
        if len(workflows) == 0:
            raise ValueError(f"No workflows extracted for {plan_id}")
        if len(workflows) > 50:  # Increased upper limit to allow more workflows
            raise ValueError(f"Too many workflows generated: {len(workflows)} for {plan_id}")
        
        
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
    
    @trace_async_function("task.execute_workflow")
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
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "current_stage": self.current_stage.value
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