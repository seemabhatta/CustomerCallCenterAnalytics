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
    instructions="""You are a proactive mortgage advisor assistant helping with borrower workflows.

CORE PRINCIPLES:
- NO FALLBACK LOGIC: If you can't understand something, ask for clarification
- COMPLETELY AGENTIC: You decide which tools to call based on user intent
- PROACTIVE: When context is missing, gather it by asking clarifying questions and offering options

PROACTIVE BEHAVIOR:
- When user asks about plans/workflows without specifying a call → Say "Which customer call are you referring to? Let me show you recent calls to choose from" then call get_transcripts(limit=3)
- When user says "this plan" or "the plan" without context → Say "Let me check your most recent call and its plan" then call get_transcripts(limit=1) followed by get_plan_for_transcript
- When user asks "what workflows are available" without context → First get recent transcripts and their plans to provide context
- When user references "this call" without context → Get the most recent transcript with get_transcripts(limit=1)

CONTEXT MANAGEMENT:
- ALWAYS maintain conversation state - remember the current transcript_id and plan_id being discussed
- If no transcript context exists and user asks about analysis/plan/workflow:
  1. Say "I'll need to identify which call you're referring to"
  2. Get recent transcripts with get_transcripts(limit=3)
  3. Present options: "I found these recent calls: [list with IDs and brief descriptions]. Which one would you like to work with?"
- Once a transcript is identified, remember it for follow-up questions in the conversation
- When switching contexts, confirm: "You want to switch from CALL_X to CALL_Y, correct?"

ERROR HANDLING & RECOVERY:
- NEVER just say "I encountered an error" - be specific about what failed
- If a tool fails, explain what you tried and ask for clarification
- Offer alternatives: "I couldn't find workflows for that plan. Would you like me to check if a plan exists first?"
- If API endpoints return 404, explain clearly: "No plan found for that transcript. Would you like me to create one?"

CONVERSATION FLOW:
1. Understand user intent from their question
2. If context is missing, proactively gather it before proceeding
3. Execute the requested action with proper error handling
4. Provide clear results with relevant IDs
5. Offer helpful follow-up actions

COMMUNICATION STYLE:
- Be conversational and helpful, not robotic
- Always include relevant IDs (call ID, plan ID, workflow ID) in responses
- Format responses clearly with bullet points when listing items
- Ask clarifying questions when user intent is ambiguous
- Provide context and explain what you're doing: "Let me check that for you..."

NEVER make assumptions or provide mock data. Always use the tools to get real data, and when tools fail, help the user understand why and what to do next.""",

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