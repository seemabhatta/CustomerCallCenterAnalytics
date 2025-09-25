"""
Generic Role-Based Agent Factory.
Creates agents with role-specific prompts while maintaining the same tool set.
Follows core principles: agentic, no fallback logic, prompt separation.
"""
import os
import aiohttp
from typing import Dict, Any, List
from dotenv import load_dotenv
from agents import Agent, function_tool

# Load environment variables from .env file
load_dotenv()


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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/transcripts/{transcript_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Transcript {transcript_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get transcript: {response.status}")
            return await response.json()


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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/analyses/by-transcript/{transcript_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Analysis for transcript {transcript_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get analysis: {response.status}")
            return await response.json()


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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/plans/by-transcript/{transcript_id}"
        ) as response:
            if response.status == 404:
                raise Exception(f"Plan for transcript {transcript_id} not found")
            elif response.status != 200:
                raise Exception(f"Failed to get plan: {response.status}")
            return await response.json()


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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/workflows",
            params={"plan_id": plan_id}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get workflows: {response.status}")
            return await response.json()


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
    # Initialize pipeline data structure
    pipeline_data = {
        "transcript_id": transcript_id,
        "transcript": None,
        "analysis": None,
        "plan": None,
        "workflows": []
    }

    try:
        # Get transcript data
        pipeline_data["transcript"] = await get_transcript(transcript_id)

        # Get analysis data
        try:
            pipeline_data["analysis"] = await get_analysis_by_transcript(transcript_id)
        except Exception:
            # Analysis might not exist yet, that's okay
            pass

        # Get plan data
        try:
            plan_data = await get_plan_by_transcript(transcript_id)
            pipeline_data["plan"] = plan_data

            # If plan exists, get associated workflows
            if plan_data and plan_data.get("id"):
                try:
                    pipeline_data["workflows"] = await get_workflows_for_plan(plan_data["id"])
                except Exception:
                    # Workflows might not exist yet, that's okay
                    pass
        except Exception:
            # Plan might not exist yet, that's okay
            pass

        return pipeline_data

    except Exception as e:
        # If we can't get the transcript, that's a real error
        if "transcript" in str(e).lower():
            raise e
        # Otherwise, return partial pipeline data
        return pipeline_data


@function_tool
async def get_borrower_pending_workflows(plan_id: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Get pending workflows that need borrower action.

    Uses the existing workflows endpoint with status and optional plan filtering.

    Args:
        plan_id: Optional plan ID to filter workflows (if None, gets all pending workflows)
        limit: Maximum number of workflows to return

    Returns:
        List of workflows awaiting approval
    """
    async with aiohttp.ClientSession() as session:
        params = {"status": "AWAITING_APPROVAL", "limit": limit}
        if plan_id:
            params["plan_id"] = plan_id

        async with session.get(
            "http://localhost:8000/api/v1/workflows",
            params=params
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get pending workflows: {response.status}")
            return await response.json()


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
        # Step 1: Get the plan for this transcript
        plan_data = await get_plan_by_transcript(transcript_id)
        result["plan"] = plan_data

        if not plan_data or not plan_data.get("id"):
            result["message"] = f"No plan found for transcript {transcript_id}"
            return result

        plan_id = plan_data["id"]

        # Step 2: Get pending workflows for this plan
        pending_workflows = await get_borrower_pending_workflows(plan_id=plan_id, limit=limit)
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


def load_prompt_from_file(role: str) -> str:
    """Load role-specific prompt from prompts folder.

    Args:
        role: Role identifier (advisor, leadership)

    Returns:
        Prompt text content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_file = f"prompts/{role}_agent/system_prompt.txt"

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def create_role_based_agent(role: str) -> Agent:
    """Create an agent with role-specific prompts and shared tools.

    Args:
        role: Role identifier (advisor, leadership)

    Returns:
        Configured Agent instance
    """
    # Load role-specific prompt
    instructions = load_prompt_from_file(role)

    # Agent name mapping
    agent_names = {
        "advisor": "Mortgage Advisor Assistant",
        "leadership": "Leadership Analytics Assistant"
    }

    agent_name = agent_names.get(role, f"{role.title()} Assistant")

    # Get model from environment variable or use default
    model = os.getenv("OPENAI_AGENT_MODEL", "gpt-4o-mini")

    # Create agent with role-specific configuration
    agent = Agent(
        name=agent_name,
        model=model,
        instructions=instructions,
        tools=[
            # All agents get the same tool set - the prompt determines behavior
            get_transcripts,
            get_transcript,
            get_analysis_by_transcript,
            get_analysis,  # Added missing tool for direct analysis access
            get_plan_by_transcript,
            get_plan,
            get_workflows_for_plan,
            get_workflow,
            get_workflow_steps,
            execute_workflow_step,
            approve_workflow,
            get_transcript_pipeline,
            get_borrower_pending_workflows,
            get_pending_workflows_by_transcript
        ]
    )

    return agent


# Create pre-configured agents for common roles
advisor_agent = create_role_based_agent("advisor")
leadership_agent = create_role_based_agent("leadership")