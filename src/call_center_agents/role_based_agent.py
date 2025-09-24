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
async def get_transcript_analysis(transcript_id: str) -> Dict[str, Any]:
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
async def get_plan_for_transcript(transcript_id: str) -> Dict[str, Any]:
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
async def get_full_pipeline_for_transcript(transcript_id: str) -> Dict[str, Any]:
    """Get complete pipeline (analysis + plan + workflows) for a transcript.

    Args:
        transcript_id: Transcript identifier

    Returns:
        Complete pipeline data
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://localhost:8000/api/v1/orchestrate/transcript/{transcript_id}/pipeline"
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get pipeline: {response.status}")
            return await response.json()


@function_tool
async def get_pending_borrower_workflows(limit: int = 10) -> List[Dict[str, Any]]:
    """Get pending workflows that need borrower action.

    Args:
        limit: Maximum number of workflows to return

    Returns:
        List of pending workflows
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://localhost:8000/api/v1/workflows/pending/borrower",
            params={"limit": limit}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to get pending workflows: {response.status}")
            return await response.json()


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

    # Create agent with role-specific configuration
    agent = Agent(
        name=agent_name,
        model="gpt-4o-mini",  # Use cheaper model with higher token limits
        instructions=instructions,
        tools=[
            # All agents get the same tool set - the prompt determines behavior
            get_transcripts,
            get_transcript,
            get_transcript_analysis,
            get_plan_for_transcript,
            get_plan,
            get_workflows_for_plan,
            get_workflow,
            get_workflow_steps,
            execute_workflow_step,
            approve_workflow,
            get_full_pipeline_for_transcript,
            get_pending_borrower_workflows
        ]
    )

    return agent


# Create pre-configured agents for common roles
advisor_agent = create_role_based_agent("advisor")
leadership_agent = create_role_based_agent("leadership")