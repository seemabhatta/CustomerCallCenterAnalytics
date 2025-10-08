"""
MCP Server for Customer Call Center Analytics

FastMCP-based server that exposes mortgage call center analytics tools
to ChatGPT via Model Context Protocol (MCP).

WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute

Implements manual tool registration following OpenAI pizzaz example pattern.

Usage:
    python src/infrastructure/mcp/mcp_server.py
"""

import os
import sys
import logging
import httpx
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, List
from copy import deepcopy

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from src.infrastructure.mcp.tool_definitions import get_all_tool_definitions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# FASTAPI CLIENT CONFIGURATION
# ========================================

# FastAPI server base URL
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

# HTTP client for calling FastAPI
http_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)

logger.info(f"🔧 MCP Server will proxy requests to: {API_BASE_URL}")
logger.info("✅ MCP HTTP client initialized")

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
# TOOL REGISTRATION HELPERS
# ========================================


def _tool_from_definition(definition: Dict[str, Any]) -> types.Tool:
    """Construct a FastMCP tool from canonical definition data."""

    return types.Tool(
        name=definition["name"],
        title=definition["title"],
        description=definition["description"],
        inputSchema=deepcopy(definition["input_schema"]),
        _meta=deepcopy(definition.get("_meta")),
    )


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    """Return list of all available tools using canonical definitions."""

    return [_tool_from_definition(defn) for defn in get_all_tool_definitions()]

# ========================================
# RESOURCES (Required by OpenAI Apps SDK)
# ========================================

@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    """Return empty list - we don't use resources, only tools."""
    return []

# ========================================
# TOOL EXECUTION HANDLERS
# ========================================

async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    """Handle tool execution requests."""
    tool_name = req.params.name
    arguments = req.params.arguments or {}

    logger.info(f"🔧 Tool called: {tool_name} with args: {arguments}")

    try:
        # Route to appropriate handler
        if tool_name == "create_transcript":
            result = await _handle_create_transcript(arguments)
        elif tool_name == "list_transcripts":
            result = await _handle_list_transcripts(arguments)
        elif tool_name == "analyze_transcript":
            result = await _handle_analyze_transcript(arguments)
        elif tool_name == "create_action_plan":
            result = await _handle_create_action_plan(arguments)
        elif tool_name == "extract_workflows":
            result = await _handle_extract_workflows(arguments)
        elif tool_name == "approve_workflow":
            result = await _handle_approve_workflow(arguments)
        elif tool_name == "execute_workflow":
            result = await _handle_execute_workflow(arguments)
        elif tool_name == "get_transcript":
            result = await _handle_get_transcript(arguments)
        elif tool_name == "get_analysis":
            result = await _handle_get_analysis(arguments)
        elif tool_name == "get_action_plan":
            result = await _handle_get_action_plan(arguments)
        elif tool_name == "get_workflow":
            result = await _handle_get_workflow(arguments)
        elif tool_name == "list_workflows":
            result = await _handle_list_workflows(arguments)
        elif tool_name == "get_execution_status":
            result = await _handle_get_execution_status(arguments)
        elif tool_name == "get_dashboard_metrics":
            result = await _handle_get_dashboard_metrics(arguments)
        elif tool_name == "get_workflow_steps":
            result = await _handle_get_workflow_steps(arguments)
        elif tool_name == "execute_workflow_step":
            result = await _handle_execute_workflow_step(arguments)
        elif tool_name == "get_step_status":
            result = await _handle_get_step_status(arguments)
        elif tool_name == "run_orchestration":
            result = await _handle_run_orchestration(arguments)
        elif tool_name == "get_orchestration_status":
            result = await _handle_get_orchestration_status(arguments)
        elif tool_name == "list_orchestration_runs":
            result = await _handle_list_orchestration_runs(arguments)
        else:
            return types.ServerResult(
                types.CallToolResult(
                    content=[types.TextContent(type="text", text=f"Unknown tool: {tool_name}")],
                    isError=True,
                )
            )

        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=result)],
                isError=False,
            )
        )

    except Exception as e:
        logger.error(f"❌ Tool execution failed: {e}", exc_info=True)
        return types.ServerResult(
            types.CallToolResult(
                content=[types.TextContent(type="text", text=f"Error: {str(e)}")],
                isError=True,
            )
        )

# ========================================
# INDIVIDUAL TOOL HANDLERS
# ========================================

async def _handle_create_transcript(args: Dict[str, Any]) -> str:
    """STEP 1: Create transcript via FastAPI."""
    params = {
        "topic": args.get("topic", "payment_inquiry"),
        "urgency": args.get("urgency", "medium"),
        "financial_impact": args.get("financial_impact", False),
        "customer_sentiment": args.get("customer_sentiment", "neutral"),
        "customer_id": args.get("customer_id", "CUST_001"),
    }
    response = await http_client.post("/api/v1/transcripts", json=params)
    response.raise_for_status()
    result = response.json()

    transcript_id = result.get('transcript_id')
    if not transcript_id:
        raise ValueError("Transcript creation response missing transcript_id")

    return f"""✅ STEP 1 COMPLETE: Transcript created!

Transcript ID: {transcript_id}
Content preview: {result.get('content', '')[:300]}...

➡️ NEXT STEP: Use analyze_transcript with transcript_id="{transcript_id}" to analyze this call."""

async def _handle_analyze_transcript(args: Dict[str, Any]) -> str:
    """STEP 2: Analyze transcript via FastAPI."""
    transcript_id = args.get("transcript_id")
    if not transcript_id:
        raise ValueError("transcript_id is required")

    params = {
        "transcript_id": transcript_id,
        "analysis_type": args.get("analysis_type", "comprehensive"),
    }
    response = await http_client.post("/api/v1/analyses", json=params)
    response.raise_for_status()
    result = response.json()

    analysis_id = result.get('analysis_id')
    return f"""✅ STEP 2 COMPLETE: Analysis created!

Analysis ID: {analysis_id}
- Intent: {result.get('intent')}
- Urgency: {result.get('urgency')}
- Sentiment: {result.get('sentiment')}
- Risks: {len(result.get('risks', []))} identified
- Compliance Issues: {len(result.get('compliance_issues', []))} found

➡️ NEXT STEP: Use create_action_plan with analysis_id="{analysis_id}" to generate action plan."""

async def _handle_create_action_plan(args: Dict[str, Any]) -> str:
    """STEP 3: Create action plan via FastAPI."""
    analysis_id = args.get("analysis_id")
    if not analysis_id:
        raise ValueError("analysis_id is required")

    params = {
        "analysis_id": analysis_id,
        "plan_type": args.get("plan_type", "standard"),
        "urgency": args.get("urgency", "medium"),
    }
    response = await http_client.post("/api/v1/plans", json=params)
    response.raise_for_status()
    result = response.json()

    plan_id = result.get('plan_id')
    actions = result.get('actions', [])
    return f"""✅ STEP 3 COMPLETE: Action plan created!

Plan ID: {plan_id}
- Actions: {len(actions)}
- Priority: {result.get('priority')}
- Estimated completion: {result.get('estimated_completion')}

➡️ NEXT STEP: Use extract_workflows with plan_id="{plan_id}" to break plan into executable workflows."""

async def _handle_extract_workflows(args: Dict[str, Any]) -> str:
    """STEP 4: Extract workflows via FastAPI."""
    plan_id = args.get("plan_id")
    if not plan_id:
        raise ValueError("plan_id is required")

    response = await http_client.post("/api/v1/workflows/extract-all", json={"plan_id": plan_id})
    response.raise_for_status()
    result = response.json()
    return f"""✅ STEP 4 COMPLETE: Workflows extracted!

Plan ID: {plan_id}
- Status: {result.get('status')}
- Workflows created: {result.get('workflow_count', 0)}
- Message: {result.get('message')}

➡️ NEXT STEP: Use list_workflows with plan_id="{plan_id}" to see all workflows, then use approve_workflow to approve each one."""

async def _handle_approve_workflow(args: Dict[str, Any]) -> str:
    """STEP 5: Approve workflow via FastAPI."""
    workflow_id = args.get("workflow_id")
    approved_by = args.get("approved_by")
    if not workflow_id or not approved_by:
        raise ValueError("workflow_id and approved_by are required")

    response = await http_client.post(f"/api/v1/workflows/{workflow_id}/approve", json={"approved_by": approved_by, "reasoning": args.get("reasoning", "")})
    response.raise_for_status()
    result = response.json()

    return f"""✅ STEP 5 COMPLETE: Workflow approved!

Workflow ID: {workflow_id}
Approved by: {approved_by}

➡️ NEXT STEP: Use execute_workflow with workflow_id="{workflow_id}" to run entire workflow."""

async def _handle_execute_workflow(args: Dict[str, Any]) -> str:
    """STEP 6A: Execute workflow via FastAPI."""
    workflow_id = args.get("workflow_id")
    executed_by = args.get("executed_by")
    if not workflow_id or not executed_by:
        raise ValueError("workflow_id and executed_by are required")

    response = await http_client.post(f"/api/v1/workflows/{workflow_id}/execute", json={"executed_by": executed_by})
    response.raise_for_status()
    result = response.json()
    execution_id = result.get('execution_id')
    return f"""✅ STEP 6A COMPLETE: Workflow executed!

Workflow ID: {workflow_id}
Execution ID: {execution_id}
Status: {result.get('status')}
Steps completed: {len(result.get('results', []))}

➡️ WORKFLOW COMPLETE! Use get_execution_status with execution_id="{execution_id}" to see detailed results."""

async def _handle_list_transcripts(args: Dict[str, Any]) -> str:
    """Query: List transcripts via FastAPI."""
    limit = args.get("limit", 10)

    response = await http_client.get(f"/api/v1/transcripts?limit={limit}")
    response.raise_for_status()
    result = response.json()

    transcripts = result.get('transcripts', [])
    if not transcripts:
        return "No call transcripts found in the system."

    # Include transcript IDs and topics for ChatGPT
    transcript_list = "\n".join([
        f"- {t.get('id')}: {t.get('topic', 'Unknown')}"
        for t in transcripts[:limit]
    ])

    return f"""Found {len(transcripts)} call transcript(s):

{transcript_list}"""

async def _handle_get_transcript(args: Dict[str, Any]) -> str:
    """Query: Get transcript via FastAPI."""
    transcript_id = args.get("transcript_id")
    if not transcript_id:
        raise ValueError("transcript_id is required")

    response = await http_client.get(f"/api/v1/transcripts/{transcript_id}")
    response.raise_for_status()
    result = response.json()
    if not result:
        return f"❌ Transcript {transcript_id} not found"

    # Format messages into readable transcript
    messages = result.get('messages', [])
    if not messages:
        return f"❌ Transcript {transcript_id} has no messages"

    formatted_messages = "\n".join([
        f"{msg.get('speaker', 'Unknown')}: {msg.get('text', '')}"
        for msg in messages
    ])

    return f"""Transcript {transcript_id}

Topic: {result.get('topic', 'Unknown')}
Customer: {result.get('customer_id', 'Unknown')}
Duration: {result.get('duration', 'Unknown')}
Urgency: {result.get('urgency', 'Unknown')}

{formatted_messages}"""

async def _handle_get_analysis(args: Dict[str, Any]) -> str:
    """Query: Get analysis for a transcript via FastAPI."""
    transcript_id = args.get("transcript_id")
    if not transcript_id:
        raise ValueError("transcript_id is required")

    response = await http_client.get(f"/api/v1/analyses?transcript_id={transcript_id}")
    response.raise_for_status()
    analyses = response.json()

    if not analyses or len(analyses) == 0:
        return f"""❌ No analysis found for transcript {transcript_id}

➡️ NEXT STEP: Use analyze_transcript with transcript_id="{transcript_id}" to create analysis."""

    # Get the most recent analysis
    analysis = analyses[0]
    analysis_id = analysis.get('analysis_id')

    return f"""✅ Analysis found for transcript {transcript_id}

Analysis ID: {analysis_id}
- Primary Intent: {analysis.get('primary_intent', 'N/A')}
- Urgency: {analysis.get('urgency_level', 'N/A')}
- Sentiment: {analysis.get('borrower_sentiment', {}).get('overall', 'N/A')}
- Issue Resolved: {analysis.get('issue_resolved', False)}
- First Call Resolution: {analysis.get('first_call_resolution', False)}
- Compliance Flags: {len(analysis.get('compliance_flags', []))}
- Topics: {', '.join(analysis.get('topics_discussed', []))}

➡️ NEXT STEP: Use get_action_plan with analysis_id="{analysis_id}" to check if plan exists, or create_action_plan to generate new plan."""

async def _handle_get_action_plan(args: Dict[str, Any]) -> str:
    """Query: Get action plan for an analysis via FastAPI."""
    analysis_id = args.get("analysis_id")
    if not analysis_id:
        raise ValueError("analysis_id is required")

    response = await http_client.get(f"/api/v1/plans?analysis_id={analysis_id}")
    response.raise_for_status()
    plans = response.json()

    if not plans or len(plans) == 0:
        return f"""❌ No action plan found for analysis {analysis_id}

➡️ NEXT STEP: Use create_action_plan with analysis_id="{analysis_id}" to generate action plan."""

    # Get the most recent plan
    plan = plans[0]
    plan_id = plan.get('plan_id')

    borrower_actions = len(plan.get('borrower_plan', {}).get('immediate_actions', []))
    advisor_items = len(plan.get('advisor_plan', {}).get('coaching_items', []))
    supervisor_items = len(plan.get('supervisor_plan', {}).get('escalation_items', []))

    return f"""✅ Action plan found for analysis {analysis_id}

Plan ID: {plan_id}
- Borrower Immediate Actions: {borrower_actions}
- Advisor Coaching Items: {advisor_items}
- Supervisor Escalations: {supervisor_items}

➡️ NEXT STEP: Use list_workflows with plan_id="{plan_id}" to see extracted workflows, or extract_workflows to create them."""

async def _handle_get_workflow(args: Dict[str, Any]) -> str:
    """Query: Get specific workflow with steps via FastAPI."""
    workflow_id = args.get("workflow_id")
    if not workflow_id:
        raise ValueError("workflow_id is required")

    # Use list_workflows with limit=100 and filter by ID
    response = await http_client.get(f"/api/v1/workflows?limit=100")
    response.raise_for_status()
    workflows = response.json()

    # Find the specific workflow
    workflow = next((w for w in workflows if w.get('id') == workflow_id), None)

    if not workflow:
        return f"❌ Workflow {workflow_id} not found"

    steps = workflow.get('workflow_steps', [])
    action = workflow.get('workflow_data', {}).get('action_item', 'N/A')
    status = workflow.get('status', 'UNKNOWN')
    risk = workflow.get('risk_level', 'UNKNOWN')

    steps_text = "\n".join([
        f"  Step {s.get('step_number')}: {s.get('action')} (tool: {s.get('tool_needed')})"
        for s in steps
    ])

    return f"""✅ Workflow {workflow_id}

Action: {action}
Status: {status}
Risk Level: {risk}

Steps ({len(steps)}):
{steps_text}

➡️ NEXT STEP: Use approve_workflow with workflow_id="{workflow_id}" to approve, then execute_workflow to run."""

async def _handle_list_workflows(args: Dict[str, Any]) -> str:
    """Query: List workflows via FastAPI."""
    params = {}
    if args.get("plan_id"):
        params["plan_id"] = args["plan_id"]

    # Map user-friendly status to database statuses
    status_filter = args.get("status")
    if status_filter:
        # "pending" = anything not REJECTED or EXECUTED
        if status_filter.lower() == "pending":
            # Get all workflows and filter client-side
            pass  # Don't send status param, filter after retrieval
        else:
            # Map friendly names to database values
            status_map = {
                "awaiting_approval": "AWAITING_APPROVAL",
                "approved": "APPROVED",
                "auto_approved": "AUTO_APPROVED",
                "rejected": "REJECTED",
                "executed": "EXECUTED",
                "pending_assessment": "PENDING_ASSESSMENT"
            }
            params["status"] = status_map.get(status_filter.lower(), status_filter.upper())

    if args.get("risk_level"):
        params["risk_level"] = args["risk_level"].upper()

    params["limit"] = args.get("limit", 100)  # Get more to filter client-side

    response = await http_client.get("/api/v1/workflows", params=params)
    response.raise_for_status()
    workflows = response.json()  # FastAPI returns list directly, not dict

    if not workflows or not isinstance(workflows, list):
        return "No workflows found with the given filters."

    # Filter for "pending" (not REJECTED or EXECUTED)
    if status_filter and status_filter.lower() == "pending":
        workflows = [
            w for w in workflows
            if w.get('status') not in ['REJECTED', 'EXECUTED']
        ]

    # Limit results
    limit = args.get("limit", 10)
    workflows = workflows[:limit]

    if not workflows:
        return "No pending workflows found."

    # Build detailed workflow list - NO FALLBACK, fail fast on missing data
    workflow_list = []
    for w in workflows:
        # Required fields - fail if missing
        workflow_id = w['id']
        workflow_type = w['workflow_type']
        status = w['status']
        risk_level = w['risk_level']

        # Action item from workflow_data (fail if missing)
        action = w['workflow_data']['action_item']

        # Steps (can be empty list, but must exist)
        workflow_steps = w['workflow_steps']
        step_count = len(workflow_steps)

        # Format: ID | Action | Type | Risk | Steps | Status
        workflow_list.append(
            f"• {workflow_id}\n"
            f"  Action: {action}\n"
            f"  Type: {workflow_type} | Risk: {risk_level} | Steps: {step_count} | Status: {status}"
        )

    workflows_text = "\n\n".join(workflow_list)
    return f"""Found {len(workflows)} workflows:

{workflows_text}

Use get_workflow with workflow_id to see details, or approve_workflow to approve."""

async def _handle_get_execution_status(args: Dict[str, Any]) -> str:
    """Query: Get execution status via FastAPI."""
    execution_id = args.get("execution_id")
    if not execution_id:
        raise ValueError("execution_id is required")

    response = await http_client.get(f"/api/v1/executions/{execution_id}")
    response.raise_for_status()
    result = response.json()

    # FastAPI returns {execution_record: {...}, audit_trail: [...]}
    exec_record = result.get('execution_record', {})

    status = exec_record.get('execution_status', 'Unknown')
    workflow_id = exec_record.get('workflow_id', 'Unknown')
    executed_at = exec_record.get('executed_at', 'Unknown')
    executor_type = exec_record.get('executor_type', 'Unknown')
    mock = exec_record.get('mock_execution', False)

    return f"""✅ Execution {execution_id}

Status: {status}
Workflow: {workflow_id}
Executor: {executor_type}
Executed At: {executed_at}
Mock Execution: {mock}

Use get_workflow with workflow_id="{workflow_id}" to see all workflow steps."""

async def _handle_get_dashboard_metrics(args: Dict[str, Any]) -> str:
    """Analytics: Fetch dashboard metrics via FastAPI."""
    response = await http_client.get("/api/v1/metrics")
    response.raise_for_status()
    metrics = response.json()

    total = metrics.get("totalTranscripts") or 0
    prev = metrics.get("transcriptsPrev") or 0
    delta = total - prev
    complete_rate = metrics.get("completeRate") or 0.0
    avg_processing = metrics.get("avgProcessingTime") or 0.0
    stage_data = metrics.get("stageData", {}) or {}

    stage_lines = []
    for stage, data in stage_data.items():
        if isinstance(data, dict) and data:
            pairs = ", ".join(f"{key}: {value}" for key, value in data.items())
            stage_lines.append(f"- {stage.title()}: {pairs}")
    stages_text = "\n".join(stage_lines) if stage_lines else "- No stage metrics available"

    return f"""📊 Dashboard Metrics

Transcripts (7d): {total} (Δ {delta:+})
Completion Rate: {complete_rate * 100:.1f}%
Avg Processing Time: {avg_processing:.1f}s

Stage Snapshot:
{stages_text}

Last Updated: {metrics.get('lastUpdated', 'N/A')}"""


async def _handle_get_workflow_steps(args: Dict[str, Any]) -> str:
    """Step control: Fetch workflow step breakdown via FastAPI."""
    workflow_id = args.get("workflow_id")
    if not workflow_id:
        raise ValueError("workflow_id is required")

    response = await http_client.get(f"/api/v1/workflows/{workflow_id}/steps")
    response.raise_for_status()
    payload = response.json()

    steps = payload.get("steps", []) or []
    if not steps:
        return f"Workflow {workflow_id} has no recorded steps."

    lines = []
    for idx, step in enumerate(steps, start=1):
        number = step.get("step_number") or step.get("number") or idx
        action = step.get("action") or step.get("description") or "(no description)"
        tool_needed = step.get("tool_needed") or step.get("tool") or "--"
        lines.append(f"  Step {number}: {action} (tool: {tool_needed})")

    return f"""🧭 Workflow {workflow_id} Steps ({len(steps)} total)

{"\n".join(lines)}

Use execute_workflow_step to run an individual step or get_step_status to inspect progress."""


async def _handle_execute_workflow_step(args: Dict[str, Any]) -> str:
    """Step control: Execute a single workflow step via FastAPI."""
    workflow_id = args.get("workflow_id")
    step_number = args.get("step_number")
    executed_by = args.get("executed_by")

    if not workflow_id:
        raise ValueError("workflow_id is required")
    if step_number is None:
        raise ValueError("step_number is required")
    if executed_by is None or executed_by == "":
        raise ValueError("executed_by is required")

    try:
        step_number_int = int(step_number)
    except (TypeError, ValueError):
        raise ValueError("step_number must be an integer")

    response = await http_client.post(
        f"/api/v1/workflows/{workflow_id}/steps/{step_number_int}/execute",
        json={"executed_by": executed_by},
    )
    response.raise_for_status()
    result = response.json()

    execution_id = result.get("execution_id")
    status = result.get("status")
    executed_at = result.get("executed_at", "N/A")
    duration_ms = result.get("duration_ms")

    duration_text = f"{duration_ms} ms" if duration_ms is not None else "Unknown"

    return f"""✅ Step {step_number_int} executed for workflow {workflow_id}

Execution ID: {execution_id}
Status: {status}
Executed By: {result.get('executed_by', executed_by)}
Executed At: {executed_at}
Duration: {duration_text}

Use get_step_status with the same step to review stored execution details."""


async def _handle_get_step_status(args: Dict[str, Any]) -> str:
    """Step control: Fetch execution status for a specific step via FastAPI."""
    workflow_id = args.get("workflow_id")
    step_number = args.get("step_number")

    if not workflow_id:
        raise ValueError("workflow_id is required")
    if step_number is None:
        raise ValueError("step_number is required")

    try:
        step_number_int = int(step_number)
    except (TypeError, ValueError):
        raise ValueError("step_number must be an integer")

    response = await http_client.get(
        f"/api/v1/workflows/{workflow_id}/steps/{step_number_int}/status"
    )
    response.raise_for_status()
    status_payload = response.json()

    if not status_payload.get("executed"):
        return f"Step {step_number_int} for workflow {workflow_id} has not been executed yet."

    details = status_payload.get("execution_details", {}) or {}
    execution_id = details.get("execution_id")
    executed_by = details.get("executed_by")
    executed_at = details.get("executed_at", "N/A")
    result_summary = details.get("result")
    if isinstance(result_summary, dict):
        items = list(result_summary.items())
        preview = ", ".join(f"{key}: {value}" for key, value in items[:3])
        if len(items) > 3:
            preview += ", …"
        result_summary = preview
    elif isinstance(result_summary, list):
        preview = ", ".join(str(item) for item in result_summary[:3])
        if len(result_summary) > 3:
            preview += ", …"
        result_summary = preview

    return f"""📝 Step {step_number_int} status for workflow {workflow_id}

Status: {details.get('status', 'Unknown')}
Execution ID: {execution_id}
Executed By: {executed_by}
Executed At: {executed_at}
Result: {result_summary or 'No result payload recorded.'}"""

async def _handle_run_orchestration(args: Dict[str, Any]) -> str:
    """Orchestration: Run complete pipeline via FastAPI."""
    transcript_ids = args.get("transcript_ids", [])
    auto_approve = args.get("auto_approve", False)

    if not transcript_ids:
        raise ValueError("transcript_ids is required")

    response = await http_client.post("/api/v1/orchestrate/run", json={
        "transcript_ids": transcript_ids,
        "auto_approve": auto_approve
    })
    response.raise_for_status()
    result = response.json()

    run_id = result.get('run_id')
    transcript_count = result.get('transcript_count', len(transcript_ids))

    return f"""🚀 Orchestration pipeline started!

Run ID: {run_id}
Transcripts to process: {transcript_count}
Auto-approve: {auto_approve}
Status: {result.get('status')}

Pipeline: Transcript → Analysis → Plan → Workflows → Execute

➡️ NEXT STEP: Use get_orchestration_status with run_id="{run_id}" to check progress."""

async def _handle_get_orchestration_status(args: Dict[str, Any]) -> str:
    """Orchestration: Get orchestration status via FastAPI."""
    run_id = args.get("run_id")
    if not run_id:
        raise ValueError("run_id is required")

    response = await http_client.get(f"/api/v1/orchestrate/status/{run_id}")
    response.raise_for_status()
    result = response.json()

    progress = result.get('progress', {})
    status = result.get('status')
    stage = result.get('stage')

    successful = len(result.get('results', []))
    failed = len(result.get('errors', []))

    # Extract pipeline IDs for ChatGPT to use in follow-up queries
    analysis_id = result.get('analysis_id', 'N/A')
    plan_id = result.get('plan_id', 'N/A')
    workflow_count = result.get('workflow_count', 0)

    # Build response with IDs included
    response_text = f"""📊 Orchestration Run {run_id}

Status: {status}
Current Stage: {stage}

Progress: {progress.get('processed', 0)}/{progress.get('total', 0)} ({progress.get('percentage', 0)}%)
- Successful: {successful}
- Failed: {failed}

Started: {result.get('started_at', 'N/A')}
Completed: {result.get('completed_at', 'In progress')}"""

    # Add pipeline IDs if available (helps ChatGPT query workflows correctly)
    if analysis_id != 'N/A' or plan_id != 'N/A':
        response_text += f"""

Pipeline IDs:
- Analysis ID: {analysis_id}
- Plan ID: {plan_id}
- Workflows Created: {workflow_count}"""

    return response_text

async def _handle_list_orchestration_runs(args: Dict[str, Any]) -> str:
    """Orchestration: List all orchestration runs via FastAPI."""
    response = await http_client.get("/api/v1/orchestrate/runs")
    response.raise_for_status()
    runs = response.json()

    if not runs:
        return "No orchestration runs found."

    runs_list = "\n".join([
        f"- {r.get('id')}: {r.get('status')} ({len(r.get('transcript_ids', []))} transcripts)"
        for r in runs[:10]
    ])

    return f"""Found {len(runs)} orchestration run(s):

{runs_list}

Use get_orchestration_status with run_id to see details."""

# ========================================
# REGISTER REQUEST HANDLERS
# ========================================

mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request

# ========================================
# CREATE HTTP APP
# ========================================

app = mcp.streamable_http_app()

# Add CORS middleware
try:
    from starlette.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass

# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting MCP Server for Customer Call Center Analytics")
    logger.info("🌐 Server will run on http://0.0.0.0:8001")
    logger.info("📡 SSE endpoint: /mcp")
    logger.info("💬 Messages endpoint: /mcp/messages")
    tool_count = len(get_all_tool_definitions())
    logger.info(f"🔧 Tools registered: {tool_count}")
    logger.info("=" * 60)
    logger.info("WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute")
    logger.info("ORCHESTRATION: Complete end-to-end pipeline automation")
    logger.info("=" * 60)

    uvicorn.run("src.infrastructure.mcp.mcp_server:app", host="0.0.0.0", port=8001, reload=False)
