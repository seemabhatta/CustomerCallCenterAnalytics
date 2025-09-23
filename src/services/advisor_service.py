"""
Advisor Service - Simplified using OpenAI Agents Python SDK.
NO FALLBACK LOGIC - fails fast with clear errors.
Clean agentic approach without complex session management.
"""
import os
from typing import Dict, Any, Optional
from agents import Runner, SQLiteSession

from src.call_center_agents.advisor_agent_v2 import advisor_agent


class AdvisorService:
    """Simplified service layer using OpenAI Agents.

    Uses OpenAI Agents Runner for conversation management.
    No complex manual session tracking - handled by SQLite sessions.
    """

    def __init__(self, db_path: str = "data/advisor_sessions.db"):
        """Initialize advisor service.

        Args:
            db_path: Database path for session storage

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path is required")

        self.db_path = db_path

    async def chat(self, advisor_id: str, message: str, session_id: Optional[str] = None,
                   transcript_id: Optional[str] = None, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat message using OpenAI Agents.

        Clean agentic approach - the LLM decides what tools to call.
        No complex session management - handled by OpenAI Agents.

        Args:
            advisor_id: Advisor identifier
            message: User's chat message
            session_id: Optional session to resume (defaults to advisor_id)
            transcript_id: Optional transcript for context (unused - agent manages context)
            plan_id: Optional plan for context (unused - agent manages context)

        Returns:
            Dictionary with response and session information

        Raises:
            ValueError: Invalid input parameters (NO FALLBACK)
            Exception: If chat processing fails (NO FALLBACK)
        """
        if not advisor_id or not message:
            raise ValueError("advisor_id and message are required")

        if not message.strip():
            return {
                "response": "I'm here to help with borrower workflows. What would you like to do?",
                "session_id": session_id or advisor_id
            }

        try:
            # Use session_id or advisor_id as the session identifier
            actual_session_id = session_id or advisor_id

            # Create SQLite session for conversation persistence
            session = SQLiteSession(actual_session_id, db_path=self.db_path)

            # Run the agent with the message - OpenAI Agents handles everything
            result = await Runner.run(advisor_agent, message, session=session)

            return {
                "response": result.final_output,
                "session_id": actual_session_id,
                "advisor_id": advisor_id
            }

        except Exception as e:
            # Fail fast with clear error message
            error_msg = str(e)
            raise Exception(f"Chat processing failed: {error_msg}")

    # Note: Session management is now handled by OpenAI Agents SQLiteSession
    # No need for complex session tracking methods