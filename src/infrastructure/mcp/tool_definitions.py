"""
MCP Tool Definitions for Customer Call Center Analytics

Defines 14 core tools that ChatGPT can use to interact with the
mortgage call center analytics system via Model Context Protocol.
"""

from typing import Dict, Any, List


def get_all_tool_definitions() -> List[Dict[str, Any]]:
    """Get all MCP tool definitions with JSON Schema."""
    return [
        # ========================================
        # PIPELINE TOOLS (6)
        # ========================================
        {
            "name": "create_transcript",
            "description": "Generate a customer call transcript for analysis. Creates realistic conversation between customer and advisor on specified topic.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Call topic (e.g., payment_inquiry, PMI_removal, hardship_assistance)",
                        "default": "payment_inquiry"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Urgency level of the call",
                        "default": "medium"
                    },
                    "financial_impact": {
                        "type": "boolean",
                        "description": "Whether call involves financial impact",
                        "default": False
                    },
                    "customer_sentiment": {
                        "type": "string",
                        "enum": ["positive", "neutral", "frustrated", "angry"],
                        "description": "Customer's emotional state",
                        "default": "neutral"
                    },
                    "customer_id": {
                        "type": "string",
                        "description": "Customer identifier",
                        "default": "CUST_001"
                    }
                },
                "required": []
            }
        },
        {
            "name": "analyze_transcript",
            "description": "Analyze a call transcript to extract intent, urgency, risks, compliance issues, and sentiment. Returns comprehensive analysis with action recommendations.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "transcript_id": {
                        "type": "string",
                        "description": "Transcript ID to analyze (e.g., TRANS_ABC123)"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["comprehensive", "quick", "compliance_focused"],
                        "description": "Type of analysis to perform",
                        "default": "comprehensive"
                    }
                },
                "required": ["transcript_id"]
            }
        },
        {
            "name": "create_action_plan",
            "description": "Generate strategic action plan from analysis results. Creates high-level actions to address customer needs, risks, and compliance issues.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "analysis_id": {
                        "type": "string",
                        "description": "Analysis ID to create plan from (e.g., ANA_XYZ789)"
                    },
                    "plan_type": {
                        "type": "string",
                        "enum": ["standard", "expedited", "compliance_priority"],
                        "description": "Type of action plan",
                        "default": "standard"
                    },
                    "urgency": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Plan urgency level",
                        "default": "medium"
                    }
                },
                "required": ["analysis_id"]
            }
        },
        {
            "name": "extract_workflows",
            "description": "Break down action plan into detailed, executable workflows. Each workflow contains granular steps with system navigation, data requirements, and validation.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "Action plan ID to extract workflows from (e.g., PLAN_DEF456)"
                    }
                },
                "required": ["plan_id"]
            }
        },
        {
            "name": "approve_workflow",
            "description": "Approve a workflow for execution. Validates workflow meets compliance and business rules before allowing execution.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to approve (e.g., WF_GHI789)"
                    },
                    "approved_by": {
                        "type": "string",
                        "description": "Identifier of approver (user, system, or ChatGPT)"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Optional approval reasoning or notes"
                    }
                },
                "required": ["workflow_id", "approved_by"]
            }
        },
        {
            "name": "execute_workflow",
            "description": "Execute an approved workflow. Runs all steps in the workflow using appropriate executors (API calls, document generation, email, etc.).",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to execute (e.g., WF_GHI789)"
                    },
                    "executed_by": {
                        "type": "string",
                        "description": "Identifier of executor (user, system, or ChatGPT)"
                    }
                },
                "required": ["workflow_id", "executed_by"]
            }
        },

        # ========================================
        # QUERY TOOLS (5)
        # ========================================
        {
            "name": "get_transcript",
            "description": "Retrieve a specific transcript by ID. Returns full conversation content and metadata.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "transcript_id": {
                        "type": "string",
                        "description": "Transcript ID to retrieve (e.g., TRANS_ABC123)"
                    }
                },
                "required": ["transcript_id"]
            }
        },
        {
            "name": "get_workflow",
            "description": "Get detailed information about a specific workflow including status, steps, and execution history.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to retrieve (e.g., WF_GHI789)"
                    }
                },
                "required": ["workflow_id"]
            }
        },
        {
            "name": "list_workflows",
            "description": "List workflows with optional filters. Useful for finding workflows by plan, status, or risk level.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "plan_id": {
                        "type": "string",
                        "description": "Filter by plan ID (optional)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "approved", "executing", "completed", "failed"],
                        "description": "Filter by workflow status (optional)"
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by risk level (optional)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": []
            }
        },
        {
            "name": "get_execution_status",
            "description": "Check execution status and results for a completed or in-progress execution. Shows step-by-step results and any errors.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "execution_id": {
                        "type": "string",
                        "description": "Execution ID to check (e.g., EXEC_JKL012)"
                    }
                },
                "required": ["execution_id"]
            }
        },
        {
            "name": "get_dashboard_metrics",
            "description": "Get system-wide analytics and metrics. Shows total transcripts, analyses, workflows, execution statistics, and performance trends.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },

        # ========================================
        # STEP EXECUTION TOOLS (3)
        # ========================================
        {
            "name": "get_workflow_steps",
            "description": "Get detailed breakdown of all steps in a workflow. Shows step number, description, executor type, and dependencies.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID to get steps from (e.g., WF_GHI789)"
                    }
                },
                "required": ["workflow_id"]
            }
        },
        {
            "name": "execute_workflow_step",
            "description": "Execute a single step within a workflow. Enables granular control for step-by-step execution.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID containing the step (e.g., WF_GHI789)"
                    },
                    "step_number": {
                        "type": "integer",
                        "description": "Step number to execute (1-based index)",
                        "minimum": 1
                    },
                    "executed_by": {
                        "type": "string",
                        "description": "Identifier of executor (user, system, or ChatGPT)"
                    }
                },
                "required": ["workflow_id", "step_number", "executed_by"]
            }
        },
        {
            "name": "get_step_status",
            "description": "Check execution status of a specific workflow step. Shows whether step is pending, executing, completed, or failed.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "description": "Workflow ID containing the step (e.g., WF_GHI789)"
                    },
                    "step_number": {
                        "type": "integer",
                        "description": "Step number to check (1-based index)",
                        "minimum": 1
                    }
                },
                "required": ["workflow_id", "step_number"]
            }
        }
    ]


def get_tool_by_name(tool_name: str) -> Dict[str, Any]:
    """Get a specific tool definition by name."""
    tools = get_all_tool_definitions()
    for tool in tools:
        if tool["name"] == tool_name:
            return tool
    raise ValueError(f"Tool not found: {tool_name}")
