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
# TOOL INPUT SCHEMAS
# ========================================

# STEP 1: Create Transcript
CREATE_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": "Topic of the call (e.g., 'payment_inquiry', 'pmi_removal', 'hardship')",
        },
        "urgency": {
            "type": "string",
            "description": "Urgency level: 'low', 'medium', 'high', 'critical'",
        },
        "financial_impact": {
            "type": "boolean",
            "description": "Whether the call has financial impact",
        },
        "customer_sentiment": {
            "type": "string",
            "description": "Customer sentiment: 'positive', 'neutral', 'negative', 'frustrated'",
        },
        "customer_id": {
            "type": "string",
            "description": "Customer ID (e.g., 'CUST_001')",
        }
    },
    "required": [],
    "additionalProperties": False,
}

# STEP 2: Analyze Transcript
ANALYZE_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID from create_transcript (e.g., 'CALL_ABC123')",
        },
        "analysis_type": {
            "type": "string",
            "description": "Type of analysis: 'comprehensive', 'quick', 'detailed'",
        }
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

# STEP 3: Create Action Plan
CREATE_ACTION_PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_id": {
            "type": "string",
            "description": "Analysis ID from analyze_transcript (e.g., 'ANALYSIS_XYZ')",
        },
        "plan_type": {
            "type": "string",
            "description": "Plan type: 'standard', 'expedited', 'comprehensive'",
        },
        "urgency": {
            "type": "string",
            "description": "Urgency: 'low', 'medium', 'high', 'critical'",
        }
    },
    "required": ["analysis_id"],
    "additionalProperties": False,
}

# STEP 4: Extract Workflows
EXTRACT_WORKFLOWS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "plan_id": {
            "type": "string",
            "description": "Plan ID from create_action_plan (e.g., 'PLAN_123')",
        }
    },
    "required": ["plan_id"],
    "additionalProperties": False,
}

# STEP 5: Approve Workflow
APPROVE_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID from list_workflows",
        },
        "approved_by": {
            "type": "string",
            "description": "Name/ID of approver",
        },
        "reasoning": {
            "type": "string",
            "description": "Reason for approval",
        }
    },
    "required": ["workflow_id", "approved_by"],
    "additionalProperties": False,
}

# STEP 6A: Execute Workflow
EXECUTE_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID to execute",
        },
        "executed_by": {
            "type": "string",
            "description": "Name/ID of executor",
        }
    },
    "required": ["workflow_id", "executed_by"],
    "additionalProperties": False,
}

# Query Tools
GET_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID to retrieve",
        }
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

LIST_WORKFLOWS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "plan_id": {
            "type": "string",
            "description": "Filter by plan ID (optional)",
        },
        "status": {
            "type": "string",
            "description": "Filter by status: 'pending', 'approved', 'executing', 'completed' (optional)",
        },
        "risk_level": {
            "type": "string",
            "description": "Filter by risk level: 'low', 'medium', 'high' (optional)",
        },
        "limit": {
            "type": "integer",
            "description": "Max number of results (default: 10)",
        }
    },
    "required": [],
    "additionalProperties": False,
}

GET_EXECUTION_STATUS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "execution_id": {
            "type": "string",
            "description": "Execution ID to check status",
        }
    },
    "required": ["execution_id"],
    "additionalProperties": False,
}

# List Transcripts
LIST_TRANSCRIPTS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "Max number of results (default: 10)",
        },
        "customer_id": {
            "type": "string",
            "description": "Filter by customer ID (optional)",
        }
    },
    "required": [],
    "additionalProperties": False,
}

# Get Analysis
GET_ANALYSIS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID to get analysis for (e.g., 'CALL_ABC123')",
        }
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

# Get Action Plan
GET_ACTION_PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_id": {
            "type": "string",
            "description": "Analysis ID to get action plan for (e.g., 'ANALYSIS_XYZ')",
        }
    },
    "required": ["analysis_id"],
    "additionalProperties": False,
}

# Get Workflow
GET_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID to retrieve (e.g., 'a905585d-7b09-44fa-837b-45cada8115bf')",
        }
    },
    "required": ["workflow_id"],
    "additionalProperties": False,
}

# Orchestration Tools
RUN_ORCHESTRATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of transcript IDs to process (e.g., ['CALL_ABC123', 'CALL_XYZ789'])",
        },
        "auto_approve": {
            "type": "boolean",
            "description": "Automatically approve all workflows (default: false)",
        }
    },
    "required": ["transcript_ids"],
    "additionalProperties": False,
}

GET_ORCHESTRATION_STATUS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Orchestration run ID (e.g., 'RUN_A1B2C3D4')",
        }
    },
    "required": ["run_id"],
    "additionalProperties": False,
}

# ========================================
# TOOL DEFINITIONS
# ========================================

@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    """Return list of all available tools with proper MCP types."""
    return [
        # STEP 1: CREATE TRANSCRIPT
        types.Tool(
            name="create_transcript",
            title="Create Transcript",
            description="Use this when the user wants to generate a customer call transcript, simulate a call, or start analyzing a mortgage/lending customer interaction. Creates realistic transcripts for scenarios like payment inquiries, PMI removal, hardship assistance, etc.",
            inputSchema=deepcopy(CREATE_TRANSCRIPT_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Generating call transcript",
                "openai/toolInvocation/invoked": "Transcript created",
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": False,
                }
            },
        ),
        # STEP 2: ANALYZE TRANSCRIPT
        types.Tool(
            name="analyze_transcript",
            title="Analyze Transcript",
            description="Use this when the user wants to analyze a call transcript for customer intent, sentiment, urgency, risks, or compliance issues. Extracts key insights from customer conversations.",
            inputSchema=deepcopy(ANALYZE_TRANSCRIPT_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Analyzing transcript",
                "openai/toolInvocation/invoked": "Analysis complete",
            
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # STEP 3: CREATE ACTION PLAN
        types.Tool(
            name="create_action_plan",
            title="Create Action Plan",
            description="Use this when the user wants to generate an action plan based on analysis results. Creates strategic recommendations and next steps for handling customer requests.",
            inputSchema=deepcopy(CREATE_ACTION_PLAN_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Creating action plan",
                "openai/toolInvocation/invoked": "Plan created",
            
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # STEP 4: EXTRACT WORKFLOWS
        types.Tool(
            name="extract_workflows",
            title="Extract Workflows",
            description="Use this when the user wants to break down an action plan into detailed, executable workflows. Converts high-level actions into step-by-step operational workflows.",
            inputSchema=deepcopy(EXTRACT_WORKFLOWS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Extracting workflows",
                "openai/toolInvocation/invoked": "Workflows extracted",
            
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # STEP 5: APPROVE WORKFLOW
        types.Tool(
            name="approve_workflow",
            title="Approve Workflow",
            description="Use this when the user wants to approve a workflow for execution. Marks a workflow as ready to run.",
            inputSchema=deepcopy(APPROVE_WORKFLOW_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Approving workflow",
                "openai/toolInvocation/invoked": "Workflow approved",
            
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # STEP 6A: EXECUTE WORKFLOW
        types.Tool(
            name="execute_workflow",
            title="Execute Workflow",
            description="Use this when the user wants to execute an approved workflow. Runs all workflow steps automatically and returns execution results.",
            inputSchema=deepcopy(EXECUTE_WORKFLOW_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Executing workflow",
                "openai/toolInvocation/invoked": "Workflow executed",
            
                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # QUERY TOOLS
        types.Tool(
            name="list_transcripts",
            title="List Transcripts",
            description="Use this when the user wants to see all calls, view call history, list transcripts, or count how many calls/transcripts exist. Returns a list of all call transcripts with metadata.",
            inputSchema=deepcopy(LIST_TRANSCRIPTS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Listing transcripts",
                "openai/toolInvocation/invoked": "Transcripts listed",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="get_transcript",
            title="Get Transcript",
            description="Use this when the user wants to view the full content of a specific transcript by its ID.",
            inputSchema=deepcopy(GET_TRANSCRIPT_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Fetching transcript",
                "openai/toolInvocation/invoked": "Transcript retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="get_analysis",
            title="Get Analysis",
            description="Use this when the user wants to check if analysis exists for a transcript, view existing analysis results, or see if a call has already been analyzed. Returns analysis details if it exists.",
            inputSchema=deepcopy(GET_ANALYSIS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Fetching analysis",
                "openai/toolInvocation/invoked": "Analysis retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="get_action_plan",
            title="Get Action Plan",
            description="Use this when the user wants to check if an action plan exists for an analysis, view existing plan details, or see borrower/advisor/supervisor plans. Returns plan if it exists.",
            inputSchema=deepcopy(GET_ACTION_PLAN_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Fetching action plan",
                "openai/toolInvocation/invoked": "Action plan retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="get_workflow",
            title="Get Workflow",
            description="Use this when the user wants to view a specific workflow's details including all steps, tools needed, and execution status.",
            inputSchema=deepcopy(GET_WORKFLOW_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Fetching workflow",
                "openai/toolInvocation/invoked": "Workflow retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="list_workflows",
            title="List Workflows",
            description="Use this when the user wants to see available workflows, filter workflows by status/risk, or find workflows for a specific plan.",
            inputSchema=deepcopy(LIST_WORKFLOWS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Listing workflows",
                "openai/toolInvocation/invoked": "Workflows listed",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="get_execution_status",
            title="Get Execution Status",
            description="Use this when the user wants to check the status and results of a workflow execution.",
            inputSchema=deepcopy(GET_EXECUTION_STATUS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Checking status",
                "openai/toolInvocation/invoked": "Status retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        # ORCHESTRATION TOOLS
        types.Tool(
            name="run_orchestration",
            title="Run Orchestration Pipeline",
            description="Use this when the user wants to run the COMPLETE pipeline for one or more transcripts automatically: Transcript → Analysis → Plan → Workflows → Execute. This orchestrates all steps end-to-end.",
            inputSchema=deepcopy(RUN_ORCHESTRATION_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Starting orchestration pipeline",
                "openai/toolInvocation/invoked": "Orchestration started",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": False,
                }
            },
        ),
        types.Tool(
            name="get_orchestration_status",
            title="Get Orchestration Status",
            description="Use this when the user wants to check the progress and status of an orchestration run, see how many transcripts were processed, or view results and errors.",
            inputSchema=deepcopy(GET_ORCHESTRATION_STATUS_SCHEMA),
            _meta={
                "openai/toolInvocation/invoking": "Checking orchestration status",
                "openai/toolInvocation/invoked": "Status retrieved",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
        types.Tool(
            name="list_orchestration_runs",
            title="List Orchestration Runs",
            description="Use this when the user wants to see all orchestration runs, view pipeline execution history, or check recent batch processing jobs.",
            inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
            _meta={
                "openai/toolInvocation/invoking": "Listing orchestration runs",
                "openai/toolInvocation/invoked": "Runs listed",

                "annotations": {
                    "destructiveHint": False,
                    "openWorldHint": False,
                    "readOnlyHint": True,
                }
            },
        ),
    ]

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
    if args.get("status"):
        params["status"] = args["status"]
    if args.get("risk_level"):
        params["risk_level"] = args["risk_level"]
    params["limit"] = args.get("limit", 10)
    response = await http_client.get("/api/v1/workflows", params=params)
    response.raise_for_status()
    workflows = response.json()  # FastAPI returns list directly, not dict

    if not workflows or not isinstance(workflows, list):
        return "No workflows found with the given filters."

    workflow_list = "\n".join([
        f"- {w.get('id')}: {w.get('workflow_type')} ({w.get('status')})"
        for w in workflows[:10]
    ])
    return f"""Found {len(workflows)} workflows:
{workflow_list}

Use approve_workflow with a workflow_id to approve."""

async def _handle_get_execution_status(args: Dict[str, Any]) -> str:
    """Query: Get execution status via FastAPI."""
    execution_id = args.get("execution_id")
    if not execution_id:
        raise ValueError("execution_id is required")

    response = await http_client.get(f"/api/v1/executions/{execution_id}")
    response.raise_for_status()
    result = response.json()
    return f"""Execution {execution_id}:
- Status: {result.get('status')}
- Workflow: {result.get('workflow_id')}
- Started: {result.get('started_at')}
- Completed: {result.get('completed_at', 'In progress')}"""

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

    return f"""📊 Orchestration Run {run_id}

Status: {status}
Current Stage: {stage}

Progress: {progress.get('processed', 0)}/{progress.get('total', 0)} ({progress.get('percentage', 0)}%)
- Successful: {successful}
- Failed: {failed}

Started: {result.get('started_at', 'N/A')}
Completed: {result.get('completed_at', 'In progress')}"""

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
    logger.info("🔧 Tools registered: 16")
    logger.info("=" * 60)
    logger.info("WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute")
    logger.info("ORCHESTRATION: Complete end-to-end pipeline automation")
    logger.info("=" * 60)

    uvicorn.run("src.infrastructure.mcp.mcp_server:app", host="0.0.0.0", port=8001, reload=False)
