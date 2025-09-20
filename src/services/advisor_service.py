"""
Advisor Service - Business logic layer for advisor chat interactions.
Follows microservices principle: API -> Service -> Agent -> Storage
NO FALLBACK LOGIC - fails fast with clear errors.
"""
import os
from typing import Dict, Any, Optional
from datetime import datetime

from src.agents.advisor_agent.advisor_agent import AdvisorAgent
from src.agents.advisor_agent.session_manager import SessionManager


class AdvisorService:
    """Service layer for advisor chat operations.

    Orchestrates chat interactions between CLI/API and the advisor agent.
    Maintains clean separation of concerns - this layer handles business logic,
    the agent handles LLM interactions, storage handles data persistence.
    """

    def __init__(self, db_path: str = "data/call_center.db"):
        """Initialize advisor service.

        Args:
            db_path: Database path for session storage

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path is required")

        self.db_path = db_path
        self.session_manager = SessionManager(db_path)

    async def chat(self, advisor_id: str, message: str, session_id: Optional[str] = None,
                   transcript_id: Optional[str] = None, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat message from an advisor.

        This is the main entry point that makes the system work like Claude Code.
        The advisor agent autonomously decides what tools to call and how to respond.

        Args:
            advisor_id: Advisor identifier
            message: User's chat message
            session_id: Optional session to resume
            transcript_id: Optional transcript for context
            plan_id: Optional plan for context

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
                "session_id": session_id or "new"
            }

        try:
            # Get or create session
            if session_id:
                session = self.session_manager.resume_session(session_id)
                if not session:
                    # Session not found, create new one
                    session = self.session_manager.create_session(
                        advisor_id=advisor_id,
                        transcript_id=transcript_id,
                        plan_id=plan_id
                    )
            else:
                session = self.session_manager.create_session(
                    advisor_id=advisor_id,
                    transcript_id=transcript_id,
                    plan_id=plan_id
                )

            # Initialize advisor agent for this session
            agent = AdvisorAgent(
                session_id=session["session_id"],
                advisor_id=advisor_id,
                db_path=self.db_path
            )

            # Process message through agent (fully agentic - agent decides everything)
            agent_response = await agent.process_message(message, session)

            # Update session after interaction
            self.session_manager.update_session(session["session_id"], session)

            return {
                "response": agent_response,
                "session_id": session["session_id"],
                "advisor_id": advisor_id
            }

        except Exception as e:
            # Fail fast with specific error details
            error_msg = str(e)

            # Provide helpful guidance based on error type
            if "not found" in error_msg.lower():
                guidance = "The requested resource was not found. Please check your input or try a different request."
            elif "access denied" in error_msg.lower() or "borrower" in error_msg.lower():
                guidance = "Access restricted to borrower workflows only. Use available commands to see what you can access."
            elif "llm" in error_msg.lower() or "openai" in error_msg.lower():
                guidance = "LLM service error. Please try again or contact support if the issue persists."
            else:
                guidance = "Please try rephrasing your request or say 'help' for available commands."

            raise Exception(f"Chat processing failed: {error_msg}. {guidance}")

    def get_recent_sessions(self, advisor_id: str, limit: int = 5) -> list:
        """Get recent sessions for an advisor.

        Args:
            advisor_id: Advisor identifier
            limit: Maximum number of sessions to return

        Returns:
            List of recent session summaries

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not advisor_id:
            raise ValueError("advisor_id is required")

        try:
            return self.session_manager.list_advisor_sessions(advisor_id, limit)

        except Exception as e:
            raise Exception(f"Failed to retrieve sessions: {str(e)}")

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of a specific session.

        Args:
            session_id: Session identifier

        Returns:
            Session summary with progress information

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        try:
            return self.session_manager.get_session_summary(session_id)

        except Exception as e:
            raise Exception(f"Failed to get session summary: {str(e)}")

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted

        Raises:
            Exception: If deletion fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        try:
            return self.session_manager.delete_session(session_id)

        except Exception as e:
            raise Exception(f"Failed to delete session: {str(e)}")