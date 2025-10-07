"""
MCP Tool Handlers

Implements execution logic for all 14 MCP tools by integrating
with existing service layer. NO FALLBACK - fails fast on errors.

Architecture:
- MCP Server receives tool calls from ChatGPT
- Tool Handlers execute using existing services
- Services handle business logic
- Results return to ChatGPT via MCP protocol
"""

import logging
from typing import Dict, Any
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class MCPToolHandlers:
    """Handlers for all MCP tools - integrates with existing services."""

    def __init__(
        self,
        transcript_service,
        analysis_service,
        plan_service,
        workflow_service,
        system_service
    ):
        """Initialize with existing service instances - NO FALLBACK."""
        self.transcript_service = transcript_service
        self.analysis_service = analysis_service
        self.plan_service = plan_service
        self.workflow_service = workflow_service
        self.system_service = system_service

    # ========================================
    # PIPELINE TOOLS (6)
    # ========================================

    async def create_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer call transcript."""
        logger.info(f"MCP: Creating transcript with params: {params}")
        try:
            result = await self.transcript_service.create(params)
            return {
                "success": True,
                "transcript_id": result.get("transcript_id"),
                "content": result.get("content"),
                "metadata": result.get("metadata")
            }
        except Exception as e:
            logger.error(f"MCP: Failed to create transcript: {e}")
            raise HTTPException(status_code=500, detail=f"Transcript creation failed: {str(e)}")

    async def analyze_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze call transcript for risks, sentiment, compliance."""
        logger.info(f"MCP: Analyzing transcript {params.get('transcript_id')}")
        try:
            result = await self.analysis_service.create(params)
            return {
                "success": True,
                "analysis_id": result.get("analysis_id"),
                "intent": result.get("intent"),
                "urgency": result.get("urgency"),
                "risks": result.get("risks"),
                "compliance_issues": result.get("compliance_issues"),
                "sentiment": result.get("sentiment"),
                "recommendations": result.get("recommendations")
            }
        except Exception as e:
            logger.error(f"MCP: Failed to analyze transcript: {e}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    async def create_action_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate strategic action plan from analysis."""
        logger.info(f"MCP: Creating action plan from analysis {params.get('analysis_id')}")
        try:
            result = await self.plan_service.create(params)
            return {
                "success": True,
                "plan_id": result.get("plan_id"),
                "actions": result.get("actions"),
                "priority": result.get("priority"),
                "estimated_completion": result.get("estimated_completion")
            }
        except Exception as e:
            logger.error(f"MCP: Failed to create action plan: {e}")
            raise HTTPException(status_code=500, detail=f"Plan creation failed: {str(e)}")

    async def extract_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed workflows from action plan."""
        logger.info(f"MCP: Extracting workflows from plan {params.get('plan_id')}")
        try:
            plan_id = params["plan_id"]
            result = await self.workflow_service.extract_all_workflows_background(plan_id)
            return {
                "success": True,
                "plan_id": plan_id,
                "message": result.get("message"),
                "workflow_count": result.get("workflow_count", 0),
                "extraction_status": result.get("status")
            }
        except Exception as e:
            logger.error(f"MCP: Failed to extract workflows: {e}")
            raise HTTPException(status_code=500, detail=f"Workflow extraction failed: {str(e)}")

    async def approve_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Approve workflow for execution."""
        logger.info(f"MCP: Approving workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            approved_by = params["approved_by"]
            reasoning = params.get("reasoning")

            result = await self.workflow_service.approve_action_item_workflow(
                workflow_id=workflow_id,
                approved_by=approved_by,
                reasoning=reasoning
            )
            return {
                "success": True,
                "workflow_id": workflow_id,
                "status": "approved",
                "approved_by": approved_by,
                "approval_details": result
            }
        except Exception as e:
            logger.error(f"MCP: Failed to approve workflow: {e}")
            raise HTTPException(status_code=400, detail=f"Workflow approval failed: {str(e)}")

    async def execute_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved workflow."""
        logger.info(f"MCP: Executing workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            executed_by = params["executed_by"]

            result = await self.workflow_service.execute_workflow(
                workflow_id=workflow_id,
                executed_by=executed_by
            )
            return {
                "success": True,
                "workflow_id": workflow_id,
                "execution_id": result.get("execution_id"),
                "status": result.get("status"),
                "results": result.get("results"),
                "executed_by": executed_by
            }
        except Exception as e:
            logger.error(f"MCP: Failed to execute workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

    # ========================================
    # QUERY TOOLS (5)
    # ========================================

    async def get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve specific transcript by ID."""
        logger.info(f"MCP: Getting transcript {params.get('transcript_id')}")
        try:
            transcript_id = params["transcript_id"]
            result = await self.transcript_service.get_by_id(transcript_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MCP: Failed to get transcript: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")

    async def get_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed workflow information."""
        logger.info(f"MCP: Getting workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            result = await self.workflow_service.get_workflow(workflow_id)
            if not result:
                raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"MCP: Failed to get workflow: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")

    async def list_workflows(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List workflows with optional filters."""
        logger.info(f"MCP: Listing workflows with filters: {params}")
        try:
            result = await self.workflow_service.list_workflows(
                plan_id=params.get("plan_id"),
                status=params.get("status"),
                risk_level=params.get("risk_level"),
                limit=params.get("limit")
            )
            return result
        except Exception as e:
            logger.error(f"MCP: Failed to list workflows: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

    async def get_execution_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution status and results."""
        logger.info(f"MCP: Getting execution status for {params.get('execution_id')}")
        try:
            from src.services.workflow_execution_engine import WorkflowExecutionEngine
            execution_engine = WorkflowExecutionEngine()

            execution_id = params["execution_id"]
            result = await execution_engine.get_execution_status(execution_id)
            return result
        except Exception as e:
            logger.error(f"MCP: Failed to get execution status: {e}")
            raise HTTPException(status_code=404, detail=f"Execution {params.get('execution_id')} not found")

    async def get_dashboard_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get system-wide analytics and metrics."""
        logger.info("MCP: Getting dashboard metrics")
        try:
            result = await self.system_service.get_dashboard_metrics()
            return result
        except Exception as e:
            logger.error(f"MCP: Failed to get dashboard metrics: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")

    # ========================================
    # STEP EXECUTION TOOLS (3)
    # ========================================

    async def get_workflow_steps(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed breakdown of workflow steps."""
        logger.info(f"MCP: Getting steps for workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            result = self.workflow_service.get_workflow_steps(workflow_id)
            return result
        except Exception as e:
            logger.error(f"MCP: Failed to get workflow steps: {e}")
            raise HTTPException(status_code=404, detail=f"Workflow {params.get('workflow_id')} not found")

    async def execute_workflow_step(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        logger.info(f"MCP: Executing step {params.get('step_number')} of workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            step_number = params["step_number"]
            executed_by = params["executed_by"]

            result = await self.workflow_service.execute_workflow_step(
                workflow_id, step_number, executed_by
            )
            return {
                "success": True,
                "workflow_id": workflow_id,
                "step_number": step_number,
                "execution_result": result
            }
        except Exception as e:
            logger.error(f"MCP: Failed to execute workflow step: {e}")
            raise HTTPException(status_code=400, detail=f"Step execution failed: {str(e)}")

    async def get_step_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get execution status of specific workflow step."""
        logger.info(f"MCP: Getting status for step {params.get('step_number')} of workflow {params.get('workflow_id')}")
        try:
            workflow_id = params["workflow_id"]
            step_number = params["step_number"]

            result = await self.workflow_service.get_step_execution_status(
                workflow_id, step_number
            )
            return result
        except Exception as e:
            logger.error(f"MCP: Failed to get step status: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to get step status: {str(e)}")

    async def handle_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Route tool call to appropriate handler - NO FALLBACK."""
        logger.info(f"MCP: Handling tool call '{tool_name}' with params: {params}")

        # Map tool names to handler methods
        tool_map = {
            # Pipeline tools
            "create_transcript": self.create_transcript,
            "analyze_transcript": self.analyze_transcript,
            "create_action_plan": self.create_action_plan,
            "extract_workflows": self.extract_workflows,
            "approve_workflow": self.approve_workflow,
            "execute_workflow": self.execute_workflow,
            # Query tools
            "get_transcript": self.get_transcript,
            "get_workflow": self.get_workflow,
            "list_workflows": self.list_workflows,
            "get_execution_status": self.get_execution_status,
            "get_dashboard_metrics": self.get_dashboard_metrics,
            # Step execution tools
            "get_workflow_steps": self.get_workflow_steps,
            "execute_workflow_step": self.execute_workflow_step,
            "get_step_status": self.get_step_status,
        }

        handler = tool_map.get(tool_name)
        if not handler:
            # NO FALLBACK - fail if tool not found
            raise ValueError(f"Unknown tool: {tool_name}")

        return await handler(params)
