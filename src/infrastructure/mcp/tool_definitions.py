"""
Canonical MCP tool definitions for Customer Call Center Analytics.

Provides a single source of truth for tool schemas, metadata, and
activation status so the MCP server and any documentation stay in sync.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# JSON SCHEMA DEFINITIONS
# ---------------------------------------------------------------------------

CREATE_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": "Topic of the call (e.g., payment_inquiry, pmi_removal, hardship)",
        },
        "urgency": {
            "type": "string",
            "description": "Urgency level: low, medium, high, critical",
        },
        "financial_impact": {
            "type": "boolean",
            "description": "Whether the call has financial impact",
        },
        "customer_sentiment": {
            "type": "string",
            "description": "Customer sentiment: positive, neutral, negative, frustrated",
        },
        "customer_id": {
            "type": "string",
            "description": "Customer ID (e.g., CUST_001)",
        },
    },
    "required": [],
    "additionalProperties": False,
}

ANALYZE_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID from create_transcript (e.g., CALL_ABC123)",
        },
        "analysis_type": {
            "type": "string",
            "description": "Type of analysis: comprehensive, quick, detailed",
        },
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

CREATE_ACTION_PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_id": {
            "type": "string",
            "description": "Analysis ID from analyze_transcript (e.g., ANALYSIS_XYZ)",
        },
        "plan_type": {
            "type": "string",
            "description": "Plan type: standard, expedited, comprehensive",
        },
        "urgency": {
            "type": "string",
            "description": "Urgency: low, medium, high, critical",
        },
    },
    "required": ["analysis_id"],
    "additionalProperties": False,
}

EXTRACT_WORKFLOWS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "plan_id": {
            "type": "string",
            "description": "Plan ID from create_action_plan (e.g., PLAN_123)",
        }
    },
    "required": ["plan_id"],
    "additionalProperties": False,
}

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
        },
    },
    "required": ["workflow_id", "approved_by"],
    "additionalProperties": False,
}

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
        },
    },
    "required": ["workflow_id", "executed_by"],
    "additionalProperties": False,
}

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
        },
    },
    "required": [],
    "additionalProperties": False,
}

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

GET_ANALYSIS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID to get analysis for",
        }
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

GET_ACTION_PLAN_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_id": {
            "type": "string",
            "description": "Analysis ID to get action plan for",
        }
    },
    "required": ["analysis_id"],
    "additionalProperties": False,
}

GET_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID to retrieve",
        }
    },
    "required": ["workflow_id"],
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
            "description": "Filter by status: pending, awaiting_approval, approved, rejected, executed",
        },
        "risk_level": {
            "type": "string",
            "description": "Filter by risk level: low, medium, high",
        },
        "limit": {
            "type": "integer",
            "description": "Max number of results (default: 10)",
        },
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

LIST_EXECUTIONS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Filter by workflow ID (optional)",
        },
        "limit": {
            "type": "integer",
            "description": "Max number of results (optional)",
        },
        "status": {
            "type": "string",
            "description": "Filter by execution status (optional)",
        },
        "executor_type": {
            "type": "string",
            "description": "Filter by executor type (optional)",
        },
    },
    "required": [],
    "additionalProperties": False,
}

GET_EXECUTION_STATISTICS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False,
}

LIST_ANALYSES_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {
            "type": "integer",
            "description": "Max number of analyses to return (optional)",
        }
    },
    "required": [],
    "additionalProperties": False,
}

GET_ANALYSIS_BY_ID_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "analysis_id": {
            "type": "string",
            "description": "Analysis ID to retrieve",
        }
    },
    "required": ["analysis_id"],
    "additionalProperties": False,
}

GET_PLAN_BY_ID_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "plan_id": {
            "type": "string",
            "description": "Plan ID to retrieve",
        }
    },
    "required": ["plan_id"],
    "additionalProperties": False,
}

GET_PLAN_BY_TRANSCRIPT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_id": {
            "type": "string",
            "description": "Transcript ID to get plan for",
        }
    },
    "required": ["transcript_id"],
    "additionalProperties": False,
}

RUN_ORCHESTRATION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "transcript_ids": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of transcript IDs to process",
        },
        "auto_approve": {
            "type": "boolean",
            "description": "Automatically approve all workflows (default: false)",
        },
    },
    "required": ["transcript_ids"],
    "additionalProperties": False,
}

GET_ORCHESTRATION_STATUS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "run_id": {
            "type": "string",
            "description": "Orchestration run ID",
        }
    },
    "required": ["run_id"],
    "additionalProperties": False,
}

LIST_ORCHESTRATION_RUNS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

GET_DASHBOARD_METRICS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

GET_WORKFLOW_STEPS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID to get steps from",
        }
    },
    "required": ["workflow_id"],
    "additionalProperties": False,
}

EXECUTE_WORKFLOW_STEP_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID containing the step",
        },
        "step_number": {
            "type": "integer",
            "description": "Step number to execute (1-based index)",
        },
        "executed_by": {
            "type": "string",
            "description": "Identifier of executor",
        },
    },
    "required": ["workflow_id", "step_number", "executed_by"],
    "additionalProperties": False,
}

GET_STEP_STATUS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "workflow_id": {
            "type": "string",
            "description": "Workflow ID containing the step",
        },
        "step_number": {
            "type": "integer",
            "description": "Step number to check (1-based index)",
        },
    },
    "required": ["workflow_id", "step_number"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS
# ---------------------------------------------------------------------------

ToolDefinition = Dict[str, Any]

TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
    "create_transcript": {
        "name": "create_transcript",
        "title": "Create Transcript",
        "description": (
            "Use this when the user needs to generate a customer call transcript, "
            "simulate a call, or start analyzing a mortgage/lending interaction."
        ),
        "input_schema": CREATE_TRANSCRIPT_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Generating call transcript",
            "openai/toolInvocation/invoked": "Transcript created",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": False,
            },
        },
        "active": True,
    },
    "analyze_transcript": {
        "name": "analyze_transcript",
        "title": "Analyze Transcript",
        "description": (
            "Use this to analyze a call transcript for customer intent, sentiment, "
            "urgency, risks, or compliance issues."
        ),
        "input_schema": ANALYZE_TRANSCRIPT_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Analyzing transcript",
            "openai/toolInvocation/invoked": "Analysis complete",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "create_action_plan": {
        "name": "create_action_plan",
        "title": "Create Action Plan",
        "description": (
            "Use this to generate an action plan based on analysis results."
        ),
        "input_schema": CREATE_ACTION_PLAN_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Creating action plan",
            "openai/toolInvocation/invoked": "Plan created",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "extract_workflows": {
        "name": "extract_workflows",
        "title": "Extract Workflows",
        "description": (
            "Use this to break an action plan into detailed, executable workflows."
        ),
        "input_schema": EXTRACT_WORKFLOWS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Extracting workflows",
            "openai/toolInvocation/invoked": "Workflows extracted",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "approve_workflow": {
        "name": "approve_workflow",
        "title": "Approve Workflow",
        "description": "Use this to approve a workflow for execution.",
        "input_schema": APPROVE_WORKFLOW_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Approving workflow",
            "openai/toolInvocation/invoked": "Workflow approved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "execute_workflow": {
        "name": "execute_workflow",
        "title": "Execute Workflow",
        "description": "Use this to execute an approved workflow.",
        "input_schema": EXECUTE_WORKFLOW_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Executing workflow",
            "openai/toolInvocation/invoked": "Workflow executed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "list_transcripts": {
        "name": "list_transcripts",
        "title": "List Transcripts",
        "description": (
            "Use this to view call history, list transcripts, or count recorded calls."
        ),
        "input_schema": LIST_TRANSCRIPTS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Listing transcripts",
            "openai/toolInvocation/invoked": "Transcripts listed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_transcript": {
        "name": "get_transcript",
        "title": "Get Transcript",
        "description": "Use this to view the full content of a specific transcript.",
        "input_schema": GET_TRANSCRIPT_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching transcript",
            "openai/toolInvocation/invoked": "Transcript retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_analysis": {
        "name": "get_analysis",
        "title": "Get Analysis",
        "description": (
            "Use this to check whether analysis exists for a transcript and view it."
        ),
        "input_schema": GET_ANALYSIS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching analysis",
            "openai/toolInvocation/invoked": "Analysis retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_action_plan": {
        "name": "get_action_plan",
        "title": "Get Action Plan",
        "description": (
            "Use this to see whether an action plan exists for an analysis and view it."
        ),
        "input_schema": GET_ACTION_PLAN_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching action plan",
            "openai/toolInvocation/invoked": "Action plan retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "list_analyses": {
        "name": "list_analyses",
        "title": "List Analyses",
        "description": "Use this to list all analyses in the system with optional limit.",
        "input_schema": LIST_ANALYSES_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Listing analyses",
            "openai/toolInvocation/invoked": "Analyses listed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_analysis_by_id": {
        "name": "get_analysis_by_id",
        "title": "Get Analysis By ID",
        "description": "Use this to retrieve a specific analysis by its analysis ID.",
        "input_schema": GET_ANALYSIS_BY_ID_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching analysis by ID",
            "openai/toolInvocation/invoked": "Analysis retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_plan_by_id": {
        "name": "get_plan_by_id",
        "title": "Get Plan By ID",
        "description": "Use this to retrieve a specific plan by its plan ID.",
        "input_schema": GET_PLAN_BY_ID_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching plan by ID",
            "openai/toolInvocation/invoked": "Plan retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_plan_by_transcript": {
        "name": "get_plan_by_transcript",
        "title": "Get Plan By Transcript",
        "description": "Use this to retrieve a plan by its transcript ID.",
        "input_schema": GET_PLAN_BY_TRANSCRIPT_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching plan by transcript",
            "openai/toolInvocation/invoked": "Plan retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_workflow": {
        "name": "get_workflow",
        "title": "Get Workflow",
        "description": "Use this to view a workflow's details, steps, and current status.",
        "input_schema": GET_WORKFLOW_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching workflow",
            "openai/toolInvocation/invoked": "Workflow retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "list_workflows": {
        "name": "list_workflows",
        "title": "List Workflows",
        "description": "Use this to find workflows by plan, status, or risk level.",
        "input_schema": LIST_WORKFLOWS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Listing workflows",
            "openai/toolInvocation/invoked": "Workflows listed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_execution_status": {
        "name": "get_execution_status",
        "title": "Get Execution Status",
        "description": "Use this to check the status and results of a workflow execution.",
        "input_schema": GET_EXECUTION_STATUS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Checking status",
            "openai/toolInvocation/invoked": "Status retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "list_executions": {
        "name": "list_executions",
        "title": "List Executions",
        "description": "Use this to list all workflow executions with optional filters (workflow_id, status, executor_type).",
        "input_schema": LIST_EXECUTIONS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Listing executions",
            "openai/toolInvocation/invoked": "Executions listed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_execution_statistics": {
        "name": "get_execution_statistics",
        "title": "Get Execution Statistics",
        "description": "Use this to get comprehensive statistics about workflow executions (success rates, timing, etc.).",
        "input_schema": GET_EXECUTION_STATISTICS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching statistics",
            "openai/toolInvocation/invoked": "Statistics retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "run_orchestration": {
        "name": "run_orchestration",
        "title": "Run Orchestration Pipeline",
        "description": (
            "Use this to run the complete pipeline automatically for one or more transcripts."
        ),
        "input_schema": RUN_ORCHESTRATION_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Starting orchestration pipeline",
            "openai/toolInvocation/invoked": "Orchestration started",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": False,
            },
        },
        "active": True,
    },
    "get_orchestration_status": {
        "name": "get_orchestration_status",
        "title": "Get Orchestration Status",
        "description": "Use this to check the progress and status of an orchestration run.",
        "input_schema": GET_ORCHESTRATION_STATUS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Checking orchestration status",
            "openai/toolInvocation/invoked": "Status retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "list_orchestration_runs": {
        "name": "list_orchestration_runs",
        "title": "List Orchestration Runs",
        "description": "Use this to view orchestration history and recent batch jobs.",
        "input_schema": LIST_ORCHESTRATION_RUNS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Listing orchestration runs",
            "openai/toolInvocation/invoked": "Runs listed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    # Additional tools defined but not yet exposed by the MCP server.
    "get_dashboard_metrics": {
        "name": "get_dashboard_metrics",
        "title": "Get Dashboard Metrics",
        "description": "Retrieve system-wide analytics and KPIs.",
        "input_schema": GET_DASHBOARD_METRICS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Gathering dashboard metrics",
            "openai/toolInvocation/invoked": "Metrics retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "get_workflow_steps": {
        "name": "get_workflow_steps",
        "title": "Get Workflow Steps",
        "description": "Retrieve a detailed breakdown of steps within a workflow.",
        "input_schema": GET_WORKFLOW_STEPS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Fetching workflow steps",
            "openai/toolInvocation/invoked": "Steps retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
    "execute_workflow_step": {
        "name": "execute_workflow_step",
        "title": "Execute Workflow Step",
        "description": "Execute a single step within a workflow for granular control.",
        "input_schema": EXECUTE_WORKFLOW_STEP_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Executing workflow step",
            "openai/toolInvocation/invoked": "Step executed",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": False,
            },
        },
        "active": True,
    },
    "get_step_status": {
        "name": "get_step_status",
        "title": "Get Step Status",
        "description": "Check the execution status of a specific workflow step.",
        "input_schema": GET_STEP_STATUS_SCHEMA,
        "_meta": {
            "openai/toolInvocation/invoking": "Checking step status",
            "openai/toolInvocation/invoked": "Step status retrieved",
            "annotations": {
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        },
        "active": True,
    },
}

# ---------------------------------------------------------------------------
# PUBLIC HELPERS
# ---------------------------------------------------------------------------

def _to_public_tool(tool: ToolDefinition) -> ToolDefinition:
    """Return a copy of the tool definition suitable for consumers."""
    return {
        "name": tool["name"],
        "title": tool["title"],
        "description": tool["description"],
        "input_schema": deepcopy(tool["input_schema"]),
        "_meta": deepcopy(tool.get("_meta")),
    }


def get_all_tool_definitions(active_only: bool = True) -> List[ToolDefinition]:
    """Return tool definitions, optionally filtered by activation flag."""
    tools: List[ToolDefinition] = []
    for tool in TOOL_DEFINITIONS.values():
        if active_only and not tool.get("active", True):
            continue
        tools.append(_to_public_tool(tool))
    return tools


def get_tool_by_name(tool_name: str, active_only: bool = True) -> ToolDefinition:
    """Fetch a tool definition by name."""
    tool = TOOL_DEFINITIONS.get(tool_name)
    if not tool:
        raise ValueError(f"Tool not found: {tool_name}")
    if active_only and not tool.get("active", True):
        raise ValueError(f"Tool not active: {tool_name}")
    return _to_public_tool(tool)
