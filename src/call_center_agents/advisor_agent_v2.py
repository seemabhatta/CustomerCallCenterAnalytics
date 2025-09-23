"""
New Advisor Agent using OpenAI Agents Python SDK.
Replaces the complex manual implementation with clean function calling.
Follows core principles: agentic, no fallback logic, no if-then-else.
"""
import os
import aiohttp
import asyncio
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
    """Execute a specific workflow step.

    Args:
        workflow_id: Workflow identifier
        step_number: Step number to execute (1-based)
        executed_by: Who is executing the step (default: advisor)

    Returns:
        Execution result
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://localhost:8000/api/v1/workflows/{workflow_id}/steps/{step_number}/execute",
            json={"executed_by": executed_by}
        ) as response:
            if response.status != 200:
                raise Exception(f"Failed to execute step: {response.status}")
            return await response.json()


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


# ============================================
# AGENT DEFINITION
# ============================================

# Create the advisor agent with all tools
advisor_agent = Agent(
    name="Mortgage Advisor Assistant",
    model="gpt-4o-mini",  # Use cheaper model with higher token limits
    instructions="""You are a mortgage advisor assistant helping with borrower workflows.

Core Principles:
- NO FALLBACK LOGIC: If you can't understand something, ask for clarification
- COMPLETELY AGENTIC: You decide which tools to call based on user intent
- FAIL FAST: Don't guess - if information is missing, request it

Available Tools:
- get_transcripts: List recent call transcripts
- get_transcript: Get specific transcript details
- get_transcript_analysis: Get analysis for a call
- get_plan_for_transcript: Generate strategic plan
- get_workflows_for_plan: Get detailed workflows
- get_workflow: Get specific workflow details
- get_workflow_steps: Get workflow steps
- execute_workflow_step: Execute a workflow step
- get_full_pipeline_for_transcript: Get complete pipeline
- get_pending_borrower_workflows: Get pending workflows

Context Management:
- When user asks about "last call" or "most recent call", use get_transcripts(limit=1)
- Remember transcript IDs mentioned in conversation for follow-up questions
- For "show me the analysis", use get_transcript_analysis with the current transcript
- Always provide call IDs when referencing transcripts

Communication Style:
- Be concise and direct
- Always include relevant IDs (call ID, plan ID, workflow ID)
- Format responses clearly with bullet points when listing items
- If user asks about analysis/plan/workflow without specifying a transcript, ask which call they mean

Never make assumptions or provide fallback responses. Always use the tools to get real data.""",

    tools=[
        get_transcripts,
        get_transcript,
        get_transcript_analysis,
        get_plan_for_transcript,
        get_plan,
        get_workflows_for_plan,
        get_workflow,
        get_workflow_steps,
        execute_workflow_step,
        get_full_pipeline_for_transcript,
        get_pending_borrower_workflows
    ]
)