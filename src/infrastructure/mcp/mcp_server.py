"""
MCP Server for Customer Call Center Analytics

FastMCP-based server that exposes mortgage call center analytics tools
to ChatGPT via Model Context Protocol (MCP).

Uses official FastMCP library for proper SSE/HTTP transport.

Usage:
    python src/infrastructure/mcp/mcp_server.py
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp.server.fastmcp import FastMCP
import mcp.types as types
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional

# Import existing services
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.system_service import SystemService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# INITIALIZE SERVICES
# ========================================

# Validate configuration
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    logger.error("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

# Initialize services (reuse from main server)
db_path = os.getenv('DATABASE_PATH', './data/call_center.db')

logger.info("🔧 Initializing MCP services...")
transcript_service = TranscriptService(api_key=api_key)
analysis_service = AnalysisService(api_key=api_key)
plan_service = PlanService(api_key=api_key)
workflow_service = WorkflowService(db_path=db_path)
system_service = SystemService(api_key=api_key)
logger.info("✅ MCP services initialized")

# ========================================
# CREATE FASTMCP SERVER
# ========================================

mcp = FastMCP(
    name="call-center-analytics",
    sse_path="/mcp",
    message_path="/mcp/messages",
    stateless_http=True
)

# ========================================
# PYDANTIC MODELS FOR VALIDATION
# ========================================

class TranscriptParams(BaseModel):
    topic: Optional[str] = Field(default="payment_inquiry", description="Call topic")
    urgency: Optional[str] = Field(default="medium", description="Urgency level")
    financial_impact: Optional[bool] = Field(default=False, description="Financial impact")
    customer_sentiment: Optional[str] = Field(default="neutral", description="Customer sentiment")
    customer_id: Optional[str] = Field(default="CUST_001", description="Customer ID")

class AnalysisParams(BaseModel):
    transcript_id: str = Field(..., description="Transcript ID to analyze")
    analysis_type: Optional[str] = Field(default="comprehensive", description="Analysis type")

class PlanParams(BaseModel):
    analysis_id: str = Field(..., description="Analysis ID")
    plan_type: Optional[str] = Field(default="standard", description="Plan type")
    urgency: Optional[str] = Field(default="medium", description="Urgency level")

class WorkflowExtractParams(BaseModel):
    plan_id: str = Field(..., description="Plan ID")

class WorkflowApproveParams(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    approved_by: str = Field(..., description="Approver identifier")
    reasoning: Optional[str] = Field(default=None, description="Approval reasoning")

class WorkflowExecuteParams(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    executed_by: str = Field(..., description="Executor identifier")

class GetByIdParams(BaseModel):
    id: str = Field(..., description="Resource ID")

class ListWorkflowsParams(BaseModel):
    plan_id: Optional[str] = Field(default=None, description="Filter by plan ID")
    status: Optional[str] = Field(default=None, description="Filter by status")
    risk_level: Optional[str] = Field(default=None, description="Filter by risk level")
    limit: Optional[int] = Field(default=10, description="Result limit")

class WorkflowStepsParams(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")

class ExecuteStepParams(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    step_number: int = Field(..., description="Step number", ge=1)
    executed_by: str = Field(..., description="Executor identifier")

class StepStatusParams(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID")
    step_number: int = Field(..., description="Step number", ge=1)

# ========================================
# TOOL IMPLEMENTATIONS
# ========================================

@mcp.tool()
async def create_transcript(
    topic: str = "payment_inquiry",
    urgency: str = "medium",
    financial_impact: bool = False,
    customer_sentiment: str = "neutral",
    customer_id: str = "CUST_001"
) -> str:
    """Generate a customer call transcript for analysis"""
    try:
        params = {
            "topic": topic,
            "urgency": urgency,
            "financial_impact": financial_impact,
            "customer_sentiment": customer_sentiment,
            "customer_id": customer_id
        }
        result = await transcript_service.create(params)
        return f"Created transcript {result.get('transcript_id')}:\n{result.get('content')[:500]}..."
    except Exception as e:
        logger.error(f"create_transcript failed: {e}")
        raise

@mcp.tool()
async def analyze_transcript(
    transcript_id: str,
    analysis_type: str = "comprehensive"
) -> str:
    """Analyze call transcript for risks, sentiment, and compliance issues"""
    try:
        params = {"transcript_id": transcript_id, "analysis_type": analysis_type}
        result = await analysis_service.create(params)
        return f"""Analysis {result.get('analysis_id')} created:
- Intent: {result.get('intent')}
- Urgency: {result.get('urgency')}
- Sentiment: {result.get('sentiment')}
- Risks: {len(result.get('risks', []))} identified
- Compliance Issues: {len(result.get('compliance_issues', []))} found"""
    except Exception as e:
        logger.error(f"analyze_transcript failed: {e}")
        raise

@mcp.tool()
async def create_action_plan(
    analysis_id: str,
    plan_type: str = "standard",
    urgency: str = "medium"
) -> str:
    """Generate strategic action plan from analysis"""
    try:
        params = {"analysis_id": analysis_id, "plan_type": plan_type, "urgency": urgency}
        result = await plan_service.create(params)
        actions = result.get('actions', [])
        return f"""Action Plan {result.get('plan_id')} created:
- Actions: {len(actions)}
- Priority: {result.get('priority')}
- Estimated completion: {result.get('estimated_completion')}"""
    except Exception as e:
        logger.error(f"create_action_plan failed: {e}")
        raise

@mcp.tool()
async def extract_workflows(plan_id: str) -> str:
    """Extract detailed workflows from action plan"""
    try:
        result = await workflow_service.extract_all_workflows_background(plan_id)
        return f"""Workflow extraction initiated for {plan_id}:
- Status: {result.get('status')}
- Workflows: {result.get('workflow_count', 0)}
- Message: {result.get('message')}"""
    except Exception as e:
        logger.error(f"extract_workflows failed: {e}")
        raise

@mcp.tool()
async def approve_workflow(
    workflow_id: str,
    approved_by: str,
    reasoning: str = ""
) -> str:
    """Approve a workflow for execution"""
    try:
        result = await workflow_service.approve_action_item_workflow(
            workflow_id=workflow_id,
            approved_by=approved_by,
            reasoning=reasoning
        )
        return f"Workflow {workflow_id} approved by {approved_by}"
    except Exception as e:
        logger.error(f"approve_workflow failed: {e}")
        raise

@mcp.tool()
async def execute_workflow(
    workflow_id: str,
    executed_by: str
) -> str:
    """Execute an approved workflow"""
    try:
        result = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            executed_by=executed_by
        )
        return f"""Workflow {workflow_id} executed:
- Execution ID: {result.get('execution_id')}
- Status: {result.get('status')}
- Results: {len(result.get('results', []))} steps completed"""
    except Exception as e:
        logger.error(f"execute_workflow failed: {e}")
        raise

@mcp.tool()
async def get_transcript(transcript_id: str) -> str:
    """Retrieve a specific transcript by ID"""
    try:
        result = await transcript_service.get_by_id(transcript_id)
        if not result:
            return f"Transcript {transcript_id} not found"
        return f"""Transcript {transcript_id}:
{result.get('content')[:1000]}..."""
    except Exception as e:
        logger.error(f"get_transcript failed: {e}")
        raise

@mcp.tool()
async def get_workflow(workflow_id: str) -> str:
    """Get detailed workflow information and status"""
    try:
        result = await workflow_service.get_workflow(workflow_id)
        if not result:
            return f"Workflow {workflow_id} not found"
        return f"""Workflow {workflow_id}:
- Status: {result.get('status')}
- Type: {result.get('workflow_type')}
- Steps: {len(result.get('steps', []))}
- Risk Level: {result.get('risk_level')}"""
    except Exception as e:
        logger.error(f"get_workflow failed: {e}")
        raise

@mcp.tool()
async def list_workflows(
    plan_id: str = "",
    status: str = "",
    risk_level: str = "",
    limit: int = 10
) -> str:
    """List workflows with optional filters"""
    try:
        result = await workflow_service.list_workflows(
            plan_id=plan_id or None,
            status=status or None,
            risk_level=risk_level or None,
            limit=limit
        )
        workflows = result.get('workflows', [])
        return f"Found {len(workflows)} workflows:\n" + "\n".join([
            f"- {w.get('workflow_id')}: {w.get('workflow_type')} ({w.get('status')})"
            for w in workflows[:5]
        ])
    except Exception as e:
        logger.error(f"list_workflows failed: {e}")
        raise

@mcp.tool()
async def get_execution_status(execution_id: str) -> str:
    """Check execution status and results"""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()
        result = await execution_engine.get_execution_status(execution_id)
        return f"""Execution {execution_id}:
- Status: {result.get('status')}
- Workflow: {result.get('workflow_id')}
- Started: {result.get('started_at')}
- Completed: {result.get('completed_at', 'In progress')}"""
    except Exception as e:
        logger.error(f"get_execution_status failed: {e}")
        raise

@mcp.tool()
async def get_dashboard_metrics() -> str:
    """Get system-wide analytics and metrics"""
    try:
        result = await system_service.get_dashboard_metrics()
        return f"""Dashboard Metrics:
- Total Transcripts: {result.get('total_transcripts', 0)}
- Total Analyses: {result.get('total_analyses', 0)}
- Total Workflows: {result.get('total_workflows', 0)}
- Pending Workflows: {result.get('pending_workflows', 0)}
- Completed Executions: {result.get('completed_executions', 0)}"""
    except Exception as e:
        logger.error(f"get_dashboard_metrics failed: {e}")
        return "Dashboard metrics temporarily unavailable"

@mcp.tool()
async def get_workflow_steps(workflow_id: str) -> str:
    """Get detailed breakdown of workflow steps"""
    try:
        result = workflow_service.get_workflow_steps(workflow_id)
        steps = result.get('steps', [])
        return f"Workflow {workflow_id} has {len(steps)} steps:\n" + "\n".join([
            f"{i+1}. {step.get('description')} (Executor: {step.get('executor_type')})"
            for i, step in enumerate(steps[:10])
        ])
    except Exception as e:
        logger.error(f"get_workflow_steps failed: {e}")
        raise

@mcp.tool()
async def execute_workflow_step(
    workflow_id: str,
    step_number: int,
    executed_by: str
) -> str:
    """Execute a single workflow step"""
    try:
        result = await workflow_service.execute_workflow_step(
            workflow_id, step_number, executed_by
        )
        return f"""Step {step_number} of workflow {workflow_id} executed:
- Status: {result.get('status')}
- Executor: {result.get('executor_type')}
- Result: {result.get('result', 'Success')}"""
    except Exception as e:
        logger.error(f"execute_workflow_step failed: {e}")
        raise

@mcp.tool()
async def get_step_status(
    workflow_id: str,
    step_number: int
) -> str:
    """Get execution status of a specific workflow step"""
    try:
        result = await workflow_service.get_step_execution_status(
            workflow_id, step_number
        )
        return f"""Step {step_number} of workflow {workflow_id}:
- Status: {result.get('status')}
- Executed: {result.get('executed', 'Not yet')}"""
    except Exception as e:
        logger.error(f"get_step_status failed: {e}")
        raise

# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting MCP Server for Customer Call Center Analytics")
    logger.info("🌐 Server will run on http://0.0.0.0:8001")
    logger.info("📡 SSE endpoint: /mcp")
    logger.info("💬 Messages endpoint: /mcp/messages")
    logger.info("🔧 Tools registered: 14")
    logger.info("=" * 60)

    # Get the FastAPI app with SSE support from FastMCP
    app = mcp.sse_app

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
