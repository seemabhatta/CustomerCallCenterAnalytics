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
            }
        ]