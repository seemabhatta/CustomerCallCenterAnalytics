"""
API client tools for advisor agent.
Each method is a tool that calls an API endpoint - no direct storage access.
Follows microservices architecture: Agent → API → Service → Storage.
"""
import aiohttp
import json
from typing import List, Dict, Any, Optional


class APITools:
    """API client tools for the advisor agent.

    Each method corresponds to an API endpoint and serves as a tool
    that the LLM can invoke. No direct storage access - all data
    comes through REST APIs.
    """

    def __init__(self, base_url: str = "http://localhost:8000", advisor_id: str = None):
        """Initialize API tools client.

        Args:
            base_url: Base URL for API calls
            advisor_id: Advisor identifier for audit trail
        """
        self.base_url = base_url
        self.advisor_id = advisor_id

    async def _call_api(self, method: str, endpoint: str, params: Dict = None, json_data: Dict = None) -> Dict[str, Any]:
        """Make HTTP API call.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data

        Returns:
            API response data

        Raises:
            Exception: If API call fails (NO FALLBACK)
        """
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 404:
                    return None
                elif response.status >= 400:
                    error_text = await response.text()
                    raise Exception(f"API call failed {response.status}: {error_text}")

                return await response.json()

    # ============================================
    # TRANSCRIPT TOOLS
    # ============================================

    async def get_transcripts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Tool: List recent customer call transcripts.

        Args:
            limit: Maximum number of transcripts to return

        Returns:
            List of transcript summaries
        """
        return await self._call_api("GET", "/api/v1/transcripts", params={"limit": limit})

    async def get_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Tool: Get specific transcript details.

        Args:
            transcript_id: Transcript identifier

        Returns:
            Transcript details or None if not found
        """
        return await self._call_api("GET", f"/api/v1/transcripts/{transcript_id}")

    # ============================================
    # ANALYSIS TOOLS
    # ============================================

    async def get_transcript_analysis(self, transcript_id: str) -> Dict[str, Any]:
        """Tool: Get detailed analysis of a call transcript.

        This is the KEY MISSING TOOL that fixes the "show me analysis" bug.
        Returns sentiment analysis, risk scores, compliance issues.

        Args:
            transcript_id: Transcript identifier

        Returns:
            Analysis data with sentiment, risks, compliance details
        """
        return await self._call_api("GET", f"/api/v1/analyses/by-transcript/{transcript_id}")

    async def get_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Tool: Get analysis by analysis ID.

        Args:
            analysis_id: Analysis identifier

        Returns:
            Analysis details or None if not found
        """
        return await self._call_api("GET", f"/api/v1/analyses/{analysis_id}")


    # ============================================
    # PLAN TOOLS
    # ============================================

    async def get_plan_for_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Tool: Get action plan associated with a transcript.

        Args:
            transcript_id: Transcript identifier

        Returns:
            Action plan details or None if not found
        """
        return await self._call_api("GET", f"/api/v1/plans/by-transcript/{transcript_id}")

    async def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Tool: Get plan by plan ID.

        Args:
            plan_id: Plan identifier

        Returns:
            Plan details or None if not found
        """
        return await self._call_api("GET", f"/api/v1/plans/{plan_id}")

    # ============================================
    # WORKFLOW TOOLS
    # ============================================

    async def get_workflows_for_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Tool: Get BORROWER workflows for a specific plan.

        Args:
            plan_id: Plan identifier

        Returns:
            List of BORROWER workflows (filtered by API)
        """
        return await self._call_api("GET", "/api/v1/workflows", params={"plan_id": plan_id})

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Tool: Get workflow details.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Workflow details or None if not found
        """
        return await self._call_api("GET", f"/api/v1/workflows/{workflow_id}")

    async def get_workflow_steps(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Tool: Get all steps for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of workflow steps
        """
        result = await self._call_api("GET", f"/api/v1/workflows/{workflow_id}/steps")
        return result.get('steps', []) if result else []

    async def execute_workflow_step(self, workflow_id: str, step_number: int, executed_by: str = None) -> Dict[str, Any]:
        """Tool: Execute a single workflow step.

        Args:
            workflow_id: Workflow identifier
            step_number: Step number to execute
            executed_by: Who is executing the step

        Returns:
            Execution result
        """
        executed_by = executed_by or self.advisor_id or "advisor_agent"
        return await self._call_api(
            "POST",
            f"/api/v1/workflows/{workflow_id}/steps/{step_number}/execute",
            json_data={"executed_by": executed_by}
        )

    # ============================================
    # PIPELINE NAVIGATION TOOLS
    # ============================================

    async def get_full_pipeline_for_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Tool: Get complete pipeline data for a transcript - analysis, plan, and workflows.

        This is the KEY TOOL that solves the broken data flow identified in the logs.
        When user mentions a call ID, this gets all related data in one comprehensive call.

        Args:
            transcript_id: Transcript identifier

        Returns:
            Complete pipeline data: transcript → analysis → plan → workflows
        """
        pipeline_data = {
            "transcript_id": transcript_id,
            "transcript": None,
            "analysis": None,
            "plan": None,
            "workflows": []
        }

        try:
            # Get transcript details
            pipeline_data["transcript"] = await self.get_transcript(transcript_id)

            # Get analysis for this transcript
            pipeline_data["analysis"] = await self.get_transcript_analysis(transcript_id)

            # Get plan for this transcript
            pipeline_data["plan"] = await self.get_plan_for_transcript(transcript_id)

            # If we have a plan, get workflows
            if pipeline_data["plan"] and pipeline_data["plan"].get("id"):
                pipeline_data["workflows"] = await self.get_workflows_for_plan(pipeline_data["plan"]["id"])

        except Exception as e:
            # Fail fast - no fallback logic
            raise Exception(f"Failed to get pipeline data for transcript {transcript_id}: {str(e)}")

        return pipeline_data

    async def get_pending_borrower_workflows(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Tool: Get all pending BORROWER workflows across all plans.

        Args:
            limit: Maximum number of workflows to return

        Returns:
            List of pending BORROWER workflows with context
        """
        return await self._call_api("GET", "/api/v1/workflows", params={
            "status": "pending",
            "workflow_type": "BORROWER",
            "limit": limit
        })

    # ============================================
    # CONTEXTUAL GRAPH-AWARE TOOLS
    # ============================================

    async def get_pending_workflows_for_context(self, session_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tool: Get pending workflows using session context for resolution.

        This tool understands context like "show pending workflows" after user
        has mentioned a specific call, and automatically finds workflows for that call.

        Args:
            session_context: Current session context with entity references

        Returns:
            List of pending workflows with context resolution
        """
        # If we have an active transcript in context, get workflows for that
        if session_context.get('transcript_id'):
            transcript_id = session_context['transcript_id']
            pipeline_data = await self.get_full_pipeline_for_transcript(transcript_id)

            if pipeline_data.get('workflows'):
                # Filter for pending workflows
                pending_workflows = [
                    w for w in pipeline_data['workflows']
                    if w.get('status', '').lower() in ['pending', 'active', 'in_progress']
                ]
                return pending_workflows

        # Fallback to global pending workflows
        return await self.get_pending_borrower_workflows()

    async def get_analysis_for_context(self, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Get analysis using session context for resolution.

        When user says "show me the analysis" after mentioning a call,
        this tool knows which analysis they mean.

        Args:
            session_context: Current session context with entity references

        Returns:
            Analysis data for the contextual transcript
        """
        # Use analysis_id if directly available
        if session_context.get('analysis_id'):
            return await self.get_analysis(session_context['analysis_id'])

        # Use transcript_id to get analysis
        if session_context.get('transcript_id'):
            return await self.get_transcript_analysis(session_context['transcript_id'])

        # No context - fail fast
        raise Exception("No transcript or analysis context available. Please specify which call you want analysis for.")

    async def get_plan_for_context(self, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Tool: Get plan using session context for resolution.

        When user says "show me the plan" after mentioning a call,
        this tool knows which plan they mean.

        Args:
            session_context: Current session context with entity references

        Returns:
            Plan data for the contextual transcript
        """
        # Use plan_id if directly available
        if session_context.get('plan_id'):
            return await self.get_plan(session_context['plan_id'])

        # Use transcript_id to get plan
        if session_context.get('transcript_id'):
            return await self.get_plan_for_transcript(session_context['transcript_id'])

        # No context - fail fast
        raise Exception("No transcript or plan context available. Please specify which call you want the plan for.")

    def get_tool_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of all available tools for the LLM.

        Returns:
            List of tool descriptions with usage guidance
        """
        return [
            {
                "name": "get_transcripts",
                "description": "List recent customer call transcripts",
                "when_to_use": "When user asks to see recent calls, list transcripts, or show calls",
                "parameters": {"limit": "optional, default 10"},
                "returns": "List of transcripts with IDs, topics, urgency"
            },
            {
                "name": "get_transcript",
                "description": "Get specific transcript details and content",
                "when_to_use": "When user asks for details of a specific call",
                "parameters": {"transcript_id": "required"},
                "returns": "Full transcript with messages and metadata"
            },
            {
                "name": "get_transcript_analysis",
                "description": "Get detailed ANALYSIS data - sentiment, risk levels, compliance issues, emotions. ALWAYS USE for analysis requests: 'show me analysis', 'do we have analysis', 'sentiment', 'risk assessment', 'compliance issues'",
                "when_to_use": "ANY question about analysis, sentiment, emotions, risk, compliance. This returns the ACTUAL ANALYSIS DATA, not transcript summaries",
                "parameters": {"transcript_id": "required, from context"},
                "returns": "Sentiment scores, risk levels, compliance violations, empathy metrics, emotional analysis",
                "context_aware": "Use transcript_id from conversation context when user says 'this call' or 'the analysis'"
            },
            {
                "name": "get_plan_for_transcript",
                "description": "Get action plan associated with a transcript",
                "when_to_use": "When user asks for plan, action items, or next steps for a call",
                "parameters": {"transcript_id": "required, from context"},
                "returns": "Action plan with strategic items"
            },
            {
                "name": "get_workflows_for_plan",
                "description": "Get BORROWER workflows for a plan",
                "when_to_use": "When user asks for workflows, detailed steps, or execution plan",
                "parameters": {"plan_id": "required"},
                "returns": "List of BORROWER workflows with detailed steps"
            },
            {
                "name": "get_workflow",
                "description": "Get specific workflow details",
                "when_to_use": "When user asks for details of a specific workflow",
                "parameters": {"workflow_id": "required"},
                "returns": "Workflow details with steps and status"
            },
            {
                "name": "execute_workflow_step",
                "description": "Execute a single workflow step",
                "when_to_use": "When user asks to execute, run, or perform a specific step",
                "parameters": {"workflow_id": "required", "step_number": "required", "executed_by": "optional"},
                "returns": "Execution result and status"
            },
            {
                "name": "get_full_pipeline_for_transcript",
                "description": "Get complete pipeline data for a transcript - transcript, analysis, plan, and workflows in one call. CRITICAL TOOL for navigation.",
                "when_to_use": "When user mentions a call ID and you need to show related data. Use instead of multiple separate calls. ALWAYS use when user asks about 'pending workflows', 'action items', or 'what's next' for a specific call.",
                "parameters": {"transcript_id": "required, from context or user"},
                "returns": "Complete pipeline: transcript details, analysis data, action plan, and all BORROWER workflows",
                "context_aware": "When user says 'show pending workflows for this call' or 'what are the action items', use transcript_id from conversation context"
            },
            {
                "name": "get_pending_borrower_workflows",
                "description": "Get all pending BORROWER workflows across all plans",
                "when_to_use": "When user asks for 'pending workflows' without specifying a call, or 'show me all pending work'",
                "parameters": {"limit": "optional, default 10"},
                "returns": "List of all pending BORROWER workflows with context"
            },
        ]