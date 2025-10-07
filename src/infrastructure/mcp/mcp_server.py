"""
MCP Server for Customer Call Center Analytics

FastMCP-based server that exposes mortgage call center analytics tools
to ChatGPT via Model Context Protocol (MCP).

WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute

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
# TOOL IMPLEMENTATIONS
# ========================================
# FLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute

# STEP 1: CREATE TRANSCRIPT
@mcp.tool(
    name="create_transcript",
    title="Create Transcript",
    description="STEP 1 of workflow: Generate a customer call transcript. This is the starting point. After creating a transcript, use analyze_transcript with the transcript_id."
)
async def create_transcript(
    topic: str = "payment_inquiry",
    urgency: str = "medium",
    financial_impact: bool = False,
    customer_sentiment: str = "neutral",
    customer_id: str = "CUST_001"
) -> str:
    """STEP 1: Generate customer call transcript - the starting point of the workflow."""
    try:
        params = {
            "topic": topic,
            "urgency": urgency,
            "financial_impact": financial_impact,
            "customer_sentiment": customer_sentiment,
            "customer_id": customer_id
        }
        result = await transcript_service.create(params)
        transcript_id = result.get('transcript_id')
        return f"""✅ STEP 1 COMPLETE: Transcript created!

Transcript ID: {transcript_id}
Content preview: {result.get('content')[:300]}...

➡️ NEXT STEP: Use analyze_transcript with transcript_id="{transcript_id}" to analyze this call."""
    except Exception as e:
        logger.error(f"create_transcript failed: {e}")
        raise

# STEP 2: ANALYZE TRANSCRIPT
@mcp.tool(
    name="analyze_transcript",
    title="Analyze Transcript",
    description="STEP 2 of workflow: Analyze a transcript to extract intent, urgency, risks, compliance issues, and sentiment. Requires transcript_id from create_transcript. After analysis, use create_action_plan with the analysis_id."
)
async def analyze_transcript(
    transcript_id: str,
    analysis_type: str = "comprehensive"
) -> str:
    """STEP 2: Analyze transcript for risks, sentiment, and compliance."""
    try:
        params = {"transcript_id": transcript_id, "analysis_type": analysis_type}
        result = await analysis_service.create(params)
        analysis_id = result.get('analysis_id')
        return f"""✅ STEP 2 COMPLETE: Analysis created!

Analysis ID: {analysis_id}
- Intent: {result.get('intent')}
- Urgency: {result.get('urgency')}
- Sentiment: {result.get('sentiment')}
- Risks: {len(result.get('risks', []))} identified
- Compliance Issues: {len(result.get('compliance_issues', []))} found

➡️ NEXT STEP: Use create_action_plan with analysis_id="{analysis_id}" to generate action plan."""
    except Exception as e:
        logger.error(f"analyze_transcript failed: {e}")
        raise

# STEP 3: CREATE ACTION PLAN
@mcp.tool(
    name="create_action_plan",
    title="Create Action Plan",
    description="STEP 3 of workflow: Generate strategic action plan from analysis. Requires analysis_id from analyze_transcript. After creating plan, use extract_workflows with the plan_id to break it into executable workflows."
)
async def create_action_plan(
    analysis_id: str,
    plan_type: str = "standard",
    urgency: str = "medium"
) -> str:
    """STEP 3: Generate strategic action plan from analysis."""
    try:
        params = {"analysis_id": analysis_id, "plan_type": plan_type, "urgency": urgency}
        result = await plan_service.create(params)
        plan_id = result.get('plan_id')
        actions = result.get('actions', [])
        return f"""✅ STEP 3 COMPLETE: Action plan created!

Plan ID: {plan_id}
- Actions: {len(actions)}
- Priority: {result.get('priority')}
- Estimated completion: {result.get('estimated_completion')}

➡️ NEXT STEP: Use extract_workflows with plan_id="{plan_id}" to break plan into executable workflows."""
    except Exception as e:
        logger.error(f"create_action_plan failed: {e}")
        raise

# STEP 4: EXTRACT WORKFLOWS
@mcp.tool(
    name="extract_workflows",
    title="Extract Workflows",
    description="STEP 4 of workflow: Break action plan into detailed, executable workflows. Requires plan_id from create_action_plan. After extraction, use list_workflows to see all workflows, then approve_workflow for each one."
)
async def extract_workflows(plan_id: str) -> str:
    """STEP 4: Extract detailed workflows from action plan."""
    try:
        result = await workflow_service.extract_all_workflows_background(plan_id)
        return f"""✅ STEP 4 COMPLETE: Workflows extracted!

Plan ID: {plan_id}
- Status: {result.get('status')}
- Workflows created: {result.get('workflow_count', 0)}
- Message: {result.get('message')}

➡️ NEXT STEP: Use list_workflows with plan_id="{plan_id}" to see all workflows, then use approve_workflow to approve each one."""
    except Exception as e:
        logger.error(f"extract_workflows failed: {e}")
        raise

# STEP 5: APPROVE WORKFLOW
@mcp.tool(
    name="approve_workflow",
    title="Approve Workflow",
    description="STEP 5 of workflow: Approve a workflow for execution. Requires workflow_id from list_workflows. After approval, use execute_workflow to run it, OR use get_workflow_steps to see individual steps first."
)
async def approve_workflow(
    workflow_id: str,
    approved_by: str,
    reasoning: str = ""
) -> str:
    """STEP 5: Approve workflow for execution."""
    try:
        result = await workflow_service.approve_action_item_workflow(
            workflow_id=workflow_id,
            approved_by=approved_by,
            reasoning=reasoning
        )
        return f"""✅ STEP 5 COMPLETE: Workflow approved!

Workflow ID: {workflow_id}
Approved by: {approved_by}

➡️ NEXT STEP:
  Option A: Use execute_workflow with workflow_id="{workflow_id}" to run entire workflow
  Option B: Use get_workflow_steps with workflow_id="{workflow_id}" to see individual steps first"""
    except Exception as e:
        logger.error(f"approve_workflow failed: {e}")
        raise

# STEP 6A: EXECUTE ENTIRE WORKFLOW
@mcp.tool(
    name="execute_workflow",
    title="Execute Workflow",
    description="STEP 6A of workflow: Execute an entire approved workflow. Requires workflow_id from approve_workflow. This runs all steps automatically. Alternatively, use execute_workflow_step to run steps one-by-one."
)
async def execute_workflow(
    workflow_id: str,
    executed_by: str
) -> str:
    """STEP 6A: Execute entire approved workflow."""
    try:
        result = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            executed_by=executed_by
        )
        execution_id = result.get('execution_id')
        return f"""✅ STEP 6A COMPLETE: Workflow executed!

Workflow ID: {workflow_id}
Execution ID: {execution_id}
Status: {result.get('status')}
Steps completed: {len(result.get('results', []))}

➡️ WORKFLOW COMPLETE! Use get_execution_status with execution_id="{execution_id}" to see detailed results."""
    except Exception as e:
        logger.error(f"execute_workflow failed: {e}")
        raise

# QUERY TOOLS - Supporting tools for the workflow

@mcp.tool(
    name="get_transcript",
    title="Get Transcript",
    description="Query tool: Retrieve a specific transcript by ID to view its full content and metadata."
)
async def get_transcript(transcript_id: str) -> str:
    """Query: Retrieve specific transcript by ID."""
    try:
        result = await transcript_service.get_by_id(transcript_id)
        if not result:
            return f"❌ Transcript {transcript_id} not found"
        return f"""Transcript {transcript_id}:
{result.get('content')[:1000]}..."""
    except Exception as e:
        logger.error(f"get_transcript failed: {e}")
        raise

@mcp.tool(
    name="get_workflow",
    title="Get Workflow",
    description="Query tool: Get detailed information about a specific workflow including status, steps, and risk level."
)
async def get_workflow(workflow_id: str) -> str:
    """Query: Get detailed workflow information."""
    try:
        result = await workflow_service.get_workflow(workflow_id)
        if not result:
            return f"❌ Workflow {workflow_id} not found"
        return f"""Workflow {workflow_id}:
- Status: {result.get('status')}
- Type: {result.get('workflow_type')}
- Steps: {len(result.get('steps', []))}
- Risk Level: {result.get('risk_level')}"""
    except Exception as e:
        logger.error(f"get_workflow failed: {e}")
        raise

@mcp.tool(
    name="list_workflows",
    title="List Workflows",
    description="Query tool: List all workflows with optional filters by plan_id, status, or risk_level. Use this after extract_workflows to see all workflows that were created."
)
async def list_workflows(
    plan_id: str = "",
    status: str = "",
    risk_level: str = "",
    limit: int = 10
) -> str:
    """Query: List workflows with optional filters."""
    try:
        result = await workflow_service.list_workflows(
            plan_id=plan_id or None,
            status=status or None,
            risk_level=risk_level or None,
            limit=limit
        )
        workflows = result.get('workflows', [])
        if not workflows:
            return f"No workflows found with the given filters."

        workflow_list = "\n".join([
            f"- {w.get('workflow_id')}: {w.get('workflow_type')} ({w.get('status')})"
            for w in workflows[:10]
        ])
        return f"""Found {len(workflows)} workflows:
{workflow_list}

Use approve_workflow with a workflow_id to approve, or get_workflow to see details."""
    except Exception as e:
        logger.error(f"list_workflows failed: {e}")
        raise

@mcp.tool(
    name="get_execution_status",
    title="Get Execution Status",
    description="Query tool: Check execution status and detailed results for a completed or in-progress workflow execution."
)
async def get_execution_status(execution_id: str) -> str:
    """Query: Check execution status and results."""
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

@mcp.tool(
    name="get_dashboard_metrics",
    title="Get Dashboard Metrics",
    description="Query tool: Get system-wide analytics including total transcripts, analyses, workflows, and execution statistics."
)
async def get_dashboard_metrics() -> str:
    """Query: Get system-wide analytics and metrics."""
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

# STEP 6B: STEP-BY-STEP EXECUTION (Alternative to execute_workflow)

@mcp.tool(
    name="get_workflow_steps",
    title="Get Workflow Steps",
    description="STEP 6B alternative: Get detailed breakdown of all steps in a workflow. Use this to see what steps will execute before running them. After viewing, use execute_workflow_step to run steps one-by-one."
)
async def get_workflow_steps(workflow_id: str) -> str:
    """STEP 6B: Get detailed breakdown of workflow steps."""
    try:
        result = workflow_service.get_workflow_steps(workflow_id)
        steps = result.get('steps', [])
        step_list = "\n".join([
            f"{i+1}. {step.get('description')} (Executor: {step.get('executor_type')})"
            for i, step in enumerate(steps[:20])
        ])
        return f"""Workflow {workflow_id} has {len(steps)} steps:

{step_list}

➡️ Use execute_workflow_step to run individual steps, or execute_workflow to run all steps automatically."""
    except Exception as e:
        logger.error(f"get_workflow_steps failed: {e}")
        raise

@mcp.tool(
    name="execute_workflow_step",
    title="Execute Workflow Step",
    description="STEP 6B alternative: Execute a single step within a workflow. Use get_workflow_steps first to see available steps. Run steps sequentially (step 1, then 2, then 3, etc.)."
)
async def execute_workflow_step(
    workflow_id: str,
    step_number: int,
    executed_by: str
) -> str:
    """STEP 6B: Execute single workflow step."""
    try:
        result = await workflow_service.execute_workflow_step(
            workflow_id, step_number, executed_by
        )
        return f"""✅ Step {step_number} executed!

Workflow: {workflow_id}
Status: {result.get('status')}
Executor: {result.get('executor_type')}
Result: {result.get('result', 'Success')}

➡️ NEXT: Execute step {step_number + 1}, or use get_step_status to check progress."""
    except Exception as e:
        logger.error(f"execute_workflow_step failed: {e}")
        raise

@mcp.tool(
    name="get_step_status",
    title="Get Step Status",
    description="Query tool: Get execution status of a specific workflow step to check if it's pending, executing, completed, or failed."
)
async def get_step_status(
    workflow_id: str,
    step_number: int
) -> str:
    """Query: Get execution status of specific workflow step."""
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
    logger.info("WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute")
    logger.info("=" * 60)

    # Get the FastAPI app with SSE support from FastMCP
    app = mcp.sse_app

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
