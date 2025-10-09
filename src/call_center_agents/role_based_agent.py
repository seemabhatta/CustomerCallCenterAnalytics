"""
Generic Role-Based Agent Factory.
Creates agents with role-specific prompts while maintaining the same tool set.
Follows core principles: agentic, no fallback logic, prompt separation.
"""
import os
import logging
import aiohttp
import yaml
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from agents import Agent, function_tool

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

# Configuration cache
_config_cache: Optional[Dict[str, Any]] = None
_workflow_config_cache: Optional[Dict[str, Any]] = None


def load_workflow_config(config_path: str = "config/workflow_config.yaml") -> Dict[str, Any]:
    """Load workflow configuration from YAML file.

    Args:
        config_path: Path to workflow config YAML file

    Returns:
        Workflow configuration dict
    """
    global _workflow_config_cache

    if _workflow_config_cache is not None:
        return _workflow_config_cache

    try:
        with open(config_path, 'r') as f:
            _workflow_config_cache = yaml.safe_load(f)
            logger.info(f"✅ Loaded workflow config from {config_path}")
            return _workflow_config_cache
    except Exception as e:
        logger.warning(f"⚠️ Failed to load workflow config from {config_path}: {e}")
        # Return default config
        return {
            "borrower_workflows": {
                "statuses": ["AWAITING_APPROVAL", "APPROVED"],
                "default_limit": 10
            }
        }


# ============================================
# TRANSCRIPT TOOLS
# ============================================

@function_tool
async def get_transcripts(limit: int = 10) -> Dict[str, Any]:
    """List recent customer call transcripts.

    Args:
        limit: Maximum number of transcripts to return (default 10)

    Returns:
        Dict containing transcripts and metadata about the request/response
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://localhost:8000/api/v1/transcripts",
            params={"limit": limit}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get transcripts: {response.status}")
            return await response.json()


@function_tool
async def get_transcript(transcript_id: str) -> Dict[str, Any]:
    """Get specific transcript details.

    Args:
        transcript_id: Transcript identifier (e.g., CALL_F1438D7A)

    Returns:
        Transcript details with messages and metadata
    """
    logger.info(f"🔍 get_transcript called with transcript_id: {transcript_id}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/transcripts/{transcript_id}"
        ) as response:
            logger.info(f"📡 Transcript API response status: {response.status}")
            if response.status == 404:
                logger.error(f"❌ Transcript {transcript_id} not found")
                raise Exception(f"Transcript {transcript_id} not found")
            elif response.status != 200:
                logger.error(f"❌ Failed to get transcript: HTTP {response.status}")
                raise Exception(f"Failed to get transcript: {response.status}")
            result = await response.json()
            logger.info(f"✅ Transcript retrieved successfully for {transcript_id}")
            return result


# ============================================
# ANALYSIS TOOLS
# ============================================

@function_tool
async def get_analysis_by_transcript(transcript_id: str) -> Dict[str, Any]:
    """Get detailed analysis of a call transcript.

    This provides sentiment analysis, risk scores, compliance issues.

    Args:
        transcript_id: Transcript identifier

    Returns:
        Analysis with sentiment, urgency, risks, compliance flags
    """
    logger.info(f"🔍 get_analysis_by_transcript called with transcript_id: {transcript_id}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/analyses/by-transcript/{transcript_id}"
        ) as response:
            logger.info(f"📡 Analysis API response status: {response.status}")
            if response.status == 404:
                logger.error(f"❌ Analysis for transcript {transcript_id} not found")
                raise Exception(f"Analysis for transcript {transcript_id} not found")
            elif response.status != 200:
                logger.error(f"❌ Failed to get analysis: HTTP {response.status}")
                raise Exception(f"Failed to get analysis: {response.status}")
            result = await response.json()
            logger.info(f"✅ Analysis retrieved successfully for {transcript_id}")
            return result


@function_tool
async def get_analysis(analysis_id: str) -> Dict[str, Any]:
    """Get analysis by ID.

    Args:
        analysis_id: Analysis identifier

    Returns:
        Analysis details
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/analyses/{analysis_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Analysis {analysis_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get analysis: {response.status}")
            return await response.json()


# ============================================
# PLAN TOOLS
# ============================================

@function_tool
async def get_plan_by_transcript(transcript_id: str) -> Dict[str, Any]:
    """Generate strategic plan for a call transcript.

    Args:
        transcript_id: Transcript identifier

    Returns:
        Strategic plan with high-level actions
    """
    logger.info(f"🔍 get_plan_by_transcript called with transcript_id: {transcript_id}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/plans/by-transcript/{transcript_id}"
        ) as response:
            logger.info(f"📡 Plan API response status: {response.status}")
            if response.status == 404:
                logger.error(f"❌ Plan for transcript {transcript_id} not found")
                raise Exception(f"Plan for transcript {transcript_id} not found")
            elif response.status != 200:
                logger.error(f"❌ Failed to get plan: HTTP {response.status}")
                raise Exception(f"Failed to get plan: {response.status}")
            result = await response.json()
            plan_id = result.get('plan_id', 'unknown')
            logger.info(f"✅ Plan retrieved successfully for {transcript_id}, plan_id: {plan_id}")
            return result


@function_tool
async def get_plan(plan_id: str) -> Dict[str, Any]:
    """Get plan by ID.

    Args:
        plan_id: Plan identifier

    Returns:
        Plan details
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/plans/{plan_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Plan {plan_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get plan: {response.status}")
            return await response.json()


# ============================================
# WORKFLOW TOOLS
# ============================================

@function_tool
async def get_workflows_for_plan(plan_id: str) -> List[Dict[str, Any]]:
    """Get detailed workflows for a plan.

    Args:
        plan_id: Plan identifier

    Returns:
        List of workflow details
    """
    logger.info(f"🔍 get_workflows_for_plan called with plan_id: {plan_id}")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/workflows",
            params={"plan_id": plan_id}
        ) as response:
            logger.info(f"📡 Workflows API response status: {response.status}")
            if response.status != 200:
                logger.error(f"❌ Failed to get workflows: HTTP {response.status}")
                raise Exception(f"Failed to get workflows: {response.status}")
            result = await response.json()
            workflow_count = len(result) if isinstance(result, list) else 0
            logger.info(f"✅ Workflows retrieved successfully for plan {plan_id}, count: {workflow_count}")
            return result


@function_tool
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get workflow by ID.

    Args:
        workflow_id: Workflow identifier

    Returns:
        Workflow details
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Workflow {workflow_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get workflow: {response.status}")
            return await response.json()


@function_tool
async def get_workflow_steps(workflow_id: str) -> List[Dict[str, Any]]:
    """Get detailed steps for a workflow.

    Args:
        workflow_id: Workflow identifier

    Returns:
        List of workflow steps
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}/steps"
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get workflow steps: {response.status}")
            return await response.json()


@function_tool
async def execute_workflow_step(workflow_id: str, step_number: int, executed_by: str = "advisor") -> Dict[str, Any]:
    """Execute a specific workflow step with approval error handling.

    Args:
        workflow_id: Workflow identifier
        step_number: Step number to execute (1-based)
        executed_by: Who is executing the step (default: advisor)

    Returns:
        Execution result or structured error information
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}/steps/{step_number}/execute",
            json={"executed_by": executed_by}
        ) as response:
            if response.status == 400:
                # Check if it's an approval error
                error_text = await response.text()
                if "must be approved" in error_text:
                    return {
                        "success": False,
                        "error_type": "approval_required",
                        "message": "Workflow requires approval before execution",
                        "workflow_id": workflow_id,
                        "step_number": step_number,
                        "requires_approval": True
                    }
                else:
                    return {
                        "success": False,
                        "error_type": "bad_request",
                        "message": error_text,
                        "workflow_id": workflow_id,
                        "step_number": step_number
                    }
            elif response.status != 200:
                return {
                    "success": False,
                    "error_type": "execution_failed",
                    "message": f"HTTP {response.status}",
                    "workflow_id": workflow_id,
                    "step_number": step_number
                }

            # Success case
            result = await response.json()
            result["success"] = True
            return result


@function_tool
async def get_transcript_pipeline(transcript_id: str) -> Dict[str, Any]:
    """Get complete pipeline (analysis + plan + workflows) for a transcript.

    Orchestrates multiple API calls to build the complete pipeline data.

    Args:
        transcript_id: Transcript identifier

    Returns:
        Complete pipeline data with transcript, analysis, plan, and workflows
    """
    logger.info(f"🚀 get_transcript_pipeline called with transcript_id: {transcript_id}")

    # Initialize pipeline data structure
    pipeline_data = {
        "transcript_id": transcript_id,
        "transcript": None,
        "analysis": None,
        "plan": None,
        "workflows": []
    }

    try:
        # Make direct API calls instead of calling @function_tool decorated functions
        # to avoid "FunctionTool object is not callable" error
        async with aiohttp.ClientSession() as session:
            # Get transcript data
            try:
                async with session.get(f"http://localhost:8000/api/v1/transcripts/{transcript_id}") as response:
                    if response.status == 200:
                        pipeline_data["transcript"] = await response.json()
                        logger.info(f"✅ Transcript retrieved for {transcript_id}")
            except Exception as e:
                logger.warning(f"❌ Transcript failed for {transcript_id}: {str(e)}")
                pass

            # Get analysis data
            try:
                async with session.get(f"http://localhost:8000/api/v1/analyses/by-transcript/{transcript_id}") as response:
                    if response.status == 200:
                        pipeline_data["analysis"] = await response.json()
                        logger.info(f"✅ Analysis retrieved for {transcript_id}")
            except Exception as e:
                logger.warning(f"❌ Analysis failed for {transcript_id}: {str(e)}")
                # Analysis might not exist yet, that's okay
                pass

            # Get plan data
            try:
                async with session.get(f"http://localhost:8000/api/v1/plans/by-transcript/{transcript_id}") as response:
                    if response.status == 200:
                        plan_data = await response.json()
                        pipeline_data["plan"] = plan_data
                        logger.info(f"✅ Plan retrieved for {transcript_id}")

                        # If plan exists, get associated workflows - check for plan_id field
                        plan_id = plan_data.get("plan_id") or plan_data.get("id")
                        if plan_data and plan_id:
                            try:
                                async with session.get(f"http://localhost:8000/api/v1/workflows?plan_id={plan_id}") as wf_response:
                                    if wf_response.status == 200:
                                        pipeline_data["workflows"] = await wf_response.json()
                                        workflow_count = len(pipeline_data["workflows"]) if isinstance(pipeline_data["workflows"], list) else 0
                                        logger.info(f"✅ Workflows retrieved for plan {plan_id}, count: {workflow_count}")
                            except Exception as e:
                                logger.error(f"❌ Workflows failed for plan {plan_id}: {str(e)}")
                                # Workflows might not exist yet, that's okay
                                pass
                        else:
                            logger.warning(f"⚠️ No plan_id found in plan data for {transcript_id}")
            except Exception as e:
                logger.warning(f"❌ Plan failed for {transcript_id}: {str(e)}")
                # Plan might not exist yet, that's okay
                pass

        final_workflow_count = len(pipeline_data["workflows"]) if isinstance(pipeline_data["workflows"], list) else 0
        logger.info(f"🎯 Pipeline complete for {transcript_id}: transcript={bool(pipeline_data['transcript'])}, analysis={bool(pipeline_data['analysis'])}, plan={bool(pipeline_data['plan'])}, workflows={final_workflow_count}")
        return pipeline_data

    except Exception as e:
        # NO FALLBACK: Fail fast for FunctionTool errors and transcript errors
        if "transcript" in str(e).lower() or "FunctionTool" in str(e):
            logger.error(f"💥 Critical error getting pipeline for {transcript_id}: {str(e)}")
            raise e
        # Otherwise, return partial pipeline data
        logger.warning(f"⚠️ Partial pipeline data returned for {transcript_id}: {str(e)}")
        return pipeline_data


@function_tool
async def get_borrower_pending_workflows(plan_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get pending workflows that need borrower action/approval.

    **IMPORTANT: Use this tool when the user asks for "all pending workflows" or "show me pending workflows"**

    This tool retrieves workflows with status AWAITING_APPROVAL or APPROVED. It can:
    - Get ALL pending/approved workflows across all plans (when plan_id is NOT provided)
    - Get pending/approved workflows for a SPECIFIC plan (when plan_id IS provided)

    **When to use:**
    - User asks: "show me all pending workflows" → Call WITHOUT plan_id parameter
    - User asks: "show me pending workflows for transcript X" → First get plan_id, then call WITH plan_id
    - User asks: "what workflows need my approval" → Call WITHOUT plan_id parameter

    Args:
        plan_id: Optional plan ID to filter workflows.
                 - If None/not provided: Returns ALL pending/approved workflows across all plans
                 - If provided: Returns only pending/approved workflows for that specific plan
        limit: Maximum number of workflows to return (default: 10)

    Returns:
        List of workflow dictionaries with status AWAITING_APPROVAL or APPROVED
    """
    # Load workflow config to get borrower statuses
    workflow_config = load_workflow_config()
    borrower_statuses = workflow_config.get("borrower_workflows", {}).get("statuses", ["AWAITING_APPROVAL", "APPROVED"])

    logger.info(f"🔍 Querying borrower workflows with statuses: {borrower_statuses}")

    async with aiohttp.ClientSession() as session:
        # Get workflows and filter by configured statuses
        params = {"limit": limit}
        if plan_id:
            params["plan_id"] = plan_id

        async with session.get(
            "http://localhost:8000/api/v1/workflows",
            params=params
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get pending workflows: {response.status}")
            all_workflows = await response.json()

            # Filter using configured borrower statuses
            filtered_workflows = [
                wf for wf in all_workflows
                if wf.get("status") in borrower_statuses
            ]
            logger.info(f"✅ Found {len(filtered_workflows)} borrower workflows")
            return filtered_workflows


@function_tool
async def get_pending_workflows_by_transcript(transcript_id: str, limit: int = 10) -> Dict[str, Any]:
    """Get pending workflows for a specific transcript.

    Orchestrates the complete flow: transcript → plan → pending workflows.

    Args:
        transcript_id: Transcript identifier (e.g., CALL_F1438D7A)
        limit: Maximum number of workflows to return

    Returns:
        Dict containing transcript_id, plan info, and pending workflows
    """
    result = {
        "transcript_id": transcript_id,
        "plan": None,
        "pending_workflows": [],
        "workflow_count": 0
    }

    try:
        # Use direct HTTP API calls instead of calling @function_tool decorated functions
        # to avoid "FunctionTool object is not callable" error
        async with aiohttp.ClientSession() as session:
            # Step 1: Get the plan for this transcript
            async with session.get(f"http://localhost:8000/api/v1/plans/by-transcript/{transcript_id}") as response:
                if response.status == 200:
                    plan_data = await response.json()
                    result["plan"] = plan_data
                else:
                    result["message"] = f"No plan found for transcript {transcript_id}"
                    return result

            if not plan_data or not plan_data.get("id"):
                result["message"] = f"No plan found for transcript {transcript_id}"
                return result

            plan_id = plan_data["id"]

            # Step 2: Get pending/approved workflows for this plan
            # Load workflow config to get borrower statuses
            workflow_config = load_workflow_config()
            borrower_statuses = workflow_config.get("borrower_workflows", {}).get("statuses", ["AWAITING_APPROVAL", "APPROVED"])

            async with session.get(
                "http://localhost:8000/api/v1/workflows",
                params={"plan_id": plan_id, "limit": limit}
            ) as response:
                if response.status == 200:
                    all_workflows = await response.json()
                    # Filter using configured borrower statuses
                    pending_workflows = [
                        wf for wf in all_workflows
                        if wf.get("status") in borrower_statuses
                    ]
                    result["pending_workflows"] = pending_workflows
                    result["workflow_count"] = len(pending_workflows) if pending_workflows else 0

            if result["workflow_count"] == 0:
                result["message"] = f"No pending workflows found for plan {plan_id} (transcript {transcript_id})"
            else:
                result["message"] = f"Found {result['workflow_count']} pending workflow(s) for transcript {transcript_id}"

            return result

    except Exception as e:
        result["error"] = str(e)
        result["message"] = f"Failed to get pending workflows for transcript {transcript_id}: {str(e)}"
        return result


# TODO functions removed - not registered with agent and unused


@function_tool
async def approve_workflow(workflow_id: str, approved_by: str, reasoning: str = "Approved by AI Agent on user's behalf") -> Dict[str, Any]:
    """Approve a workflow on behalf of the user.

    Args:
        workflow_id: Workflow identifier
        approved_by: User ID/name who is approving
        reasoning: Approval reasoning (optional)

    Returns:
        Updated workflow with APPROVED status
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}/approve",
            json={"approved_by": approved_by, "reasoning": reasoning}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to approve workflow: {response.status}")
            return await response.json()


@function_tool
async def query_knowledge_graph(question: str) -> Dict[str, Any]:
    """Query the knowledge graph using natural language.

    Use this to explore connections, patterns, and insights in the knowledge graph.
    Great for questions like:
    - "Show me all high-risk customers"
    - "What patterns lead to successful resolutions?"
    - "How are wisdom nodes connected to plans?"
    - "Show me all MetaLearning insights"
    - "What wisdom has been extracted from successful plans?"
    - "How many nodes are in the knowledge graph?"

    Args:
        question: Natural language question about the graph

    Returns:
        Graph query results with nodes, relationships, and explanation
    """
    logger.info(f"🔍 query_knowledge_graph called with question: {question}")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/graph/ask",
            json={"question": question}
        ) as response:
            logger.info(f"📡 Graph API response status: {response.status}")
            if response.status != 200:
                logger.error(f"❌ Failed to query graph: HTTP {response.status}")
                raise Exception(f"Failed to query graph: {response.status}")
            result = await response.json()
            logger.info(f"✅ Graph query executed successfully")
            return result


@function_tool
async def ask_intelligence_question(question: str, persona: str = None) -> Dict[str, Any]:
    """Ask natural language question to the intelligence system.

    The intelligence system combines Prophet forecasts with GenAI analysis to provide
    actionable insights across Leadership, Servicing Operations, and Marketing personas.

    Use this for analytical and strategic questions like:
    - "What is our biggest operational risk today?"
    - "How many advisors do we need tomorrow afternoon?"
    - "Which customer segment should we target for our next campaign?"
    - "What's the financial impact of our current churn risk?"
    - "Should I approve this staffing change?"
    - "What are the top 3 actions I should take this week?"

    Args:
        question: Natural language question about portfolio, operations, or marketing strategy
        persona: Optional persona filter (leadership|servicing|marketing).
                 If not specified, system will route to appropriate persona automatically.

    Returns:
        Comprehensive answer with recommendations, key numbers, actions, and confidence level
    """
    logger.info(f"🧠 ask_intelligence_question called: {question} (persona: {persona})")

    async with aiohttp.ClientSession() as session:
        payload = {"question": question}
        if persona:
            payload["persona"] = persona

        async with session.post(
            "http://localhost:8000/api/v1/intelligence/ask",
            json=payload
        ) as response:
            logger.info(f"📡 Intelligence API response status: {response.status}")
            if response.status != 200:
                logger.error(f"❌ Failed to get intelligence answer: HTTP {response.status}")
                raise Exception(f"Failed to get intelligence answer: {response.status}")
            result = await response.json()
            logger.info(f"✅ Intelligence answer retrieved successfully")
            return result


# ============================================
# CONFIGURATION MANAGEMENT
# ============================================

def load_prompt_config() -> Dict[str, Any]:
    """Load prompt configuration from YAML file with caching.

    Returns:
        Configuration dictionary containing role/mode mappings

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    config_file = "config/prompt_mapping.yaml"

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuration file not found: {config_file}")

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Validate required structure
        if 'roles' not in config:
            raise ValueError("Configuration missing 'roles' section")

        # Cache the configuration
        _config_cache = config
        logger.info(f"✅ Loaded prompt configuration from {config_file}")
        return config

    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")


def get_prompt_file_for_role_mode(role: str, mode: str = "borrower") -> str:
    """Get prompt file path for role and mode from configuration.

    Args:
        role: Role identifier (advisor, leadership)
        mode: Mode identifier (borrower, selfreflection)

    Returns:
        Prompt file path

    Raises:
        ValueError: If role or mode not found in configuration
    """
    config = load_prompt_config()

    # Check if role exists
    if role not in config['roles']:
        available_roles = list(config['roles'].keys())
        raise ValueError(f"Role '{role}' not found. Available roles: {available_roles}")

    role_config = config['roles'][role]

    # Check if mode exists for this role
    if 'modes' not in role_config or mode not in role_config['modes']:
        available_modes = list(role_config.get('modes', {}).keys())
        raise ValueError(f"Mode '{mode}' not found for role '{role}'. Available modes: {available_modes}")

    mode_config = role_config['modes'][mode]

    # Get prompt file path
    prompt_file = mode_config.get('prompt_file')
    if not prompt_file:
        raise ValueError(f"No prompt_file specified for role '{role}' mode '{mode}'")

    return prompt_file


def get_agent_display_name(role: str, mode: str = "borrower") -> str:
    """Get display name for agent from configuration.

    Args:
        role: Role identifier
        mode: Mode identifier

    Returns:
        Agent display name
    """
    try:
        config = load_prompt_config()
        role_config = config['roles'][role]
        base_name = role_config.get('display_name', f"{role.title()} Assistant")

        # Add mode to name if not default
        if mode != config.get('settings', {}).get('default_mode', 'borrower'):
            mode_display = mode.replace('_', ' ').title()
            return f"{base_name} ({mode_display} Mode)"

        return base_name

    except (KeyError, ValueError) as e:
        logger.warning(f"⚠️ Failed to get display name from config: {e}")
        # Fallback to hardcoded names
        agent_names = {
            "advisor": "Mortgage Advisor Assistant",
            "leadership": "Leadership Analytics Assistant"
        }
        base_name = agent_names.get(role, f"{role.title()} Assistant")
        if mode != "borrower":
            return f"{base_name} ({mode.title()} Mode)"
        return base_name


def load_prompt_from_file(role: str, mode: str = "borrower") -> str:
    """Load role and mode specific prompt from configuration.

    Args:
        role: Role identifier (advisor, leadership)
        mode: Mode identifier (borrower, selfreflection)

    Returns:
        Prompt text content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
        ValueError: If role/mode combination not found in configuration
    """
    try:
        # Get prompt file path from configuration
        prompt_file = get_prompt_file_for_role_mode(role, mode)
        logger.info(f"📄 Loading prompt from config: {role}/{mode} -> {prompt_file}")

    except ValueError as e:
        # Fallback to legacy path construction if config fails
        logger.warning(f"⚠️ Config lookup failed, using legacy path: {e}")
        prompt_file = f"prompts/{role}_agent/{mode}_system_prompt.md"

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        logger.info(f"✅ Loaded prompt for {role}/{mode} ({len(content)} characters)")
        return content


def create_role_based_agent(role: str, mode: str = "borrower") -> Agent:
    """Create an agent with role and mode specific prompts and YAML-configured tools.

    Tools are now loaded from config/prompt_mapping.yaml based on role+mode.
    This enables dynamic tool assignment without code changes.

    Args:
        role: Role identifier (advisor, leadership)
        mode: Mode identifier (borrower, selfreflection)

    Returns:
        Configured Agent instance

    Raises:
        ValueError: If role/mode not found or tools cannot be resolved
    """
    # Load role and mode specific prompt
    instructions = load_prompt_from_file(role, mode)

    # Get agent name from configuration
    agent_name = get_agent_display_name(role, mode)

    # Get model from environment variable, config, or use default
    model = os.getenv("OPENAI_AGENT_MODEL")
    if not model:
        try:
            config = load_prompt_config()
            model = config.get('settings', {}).get('default_model', 'gpt-4o-mini')
        except Exception:
            model = 'gpt-4o-mini'

    # Load tools from YAML configuration
    from src.infrastructure.config.tool_registry import get_agent_tool_config

    # Define tool function registry (maps tool names to actual functions)
    TOOL_FUNCTION_REGISTRY = {
        'get_transcripts': get_transcripts,
        'get_transcript': get_transcript,
        'get_analysis_by_transcript': get_analysis_by_transcript,
        'get_analysis': get_analysis,
        'get_plan_by_transcript': get_plan_by_transcript,
        'get_plan': get_plan,
        'get_workflows_for_plan': get_workflows_for_plan,
        'get_workflow': get_workflow,
        'get_workflow_steps': get_workflow_steps,
        'execute_workflow_step': execute_workflow_step,
        'approve_workflow': approve_workflow,
        'get_transcript_pipeline': get_transcript_pipeline,
        'get_borrower_pending_workflows': get_borrower_pending_workflows,
        'get_pending_workflows_by_transcript': get_pending_workflows_by_transcript,
        'query_knowledge_graph': query_knowledge_graph,
        'ask_intelligence_question': ask_intelligence_question
    }

    # Get tool configuration for this role+mode
    tool_config = get_agent_tool_config(
        role=role,
        mode=mode,
        config_path="config/prompt_mapping.yaml",
        tool_function_map=TOOL_FUNCTION_REGISTRY
    )

    # Create agent with YAML-configured tools
    agent = Agent(
        name=agent_name,
        model=model,
        instructions=instructions,
        tools=tool_config['tool_functions']  # Tools from YAML config
    )

    logger.info(f"✅ Created {role}/{mode} agent with {len(tool_config['tool_functions'])} tools: {tool_config['tool_names']}")

    return agent


# Create pre-configured agents for common roles
advisor_agent = create_role_based_agent("advisor", "borrower")
leadership_agent = create_role_based_agent("leadership", "borrower")

# Additional mode-specific agents
advisor_selfreflection_agent = create_role_based_agent("advisor", "selfreflection")