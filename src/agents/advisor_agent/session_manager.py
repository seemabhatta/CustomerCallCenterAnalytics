"""
Session Manager for Advisor Agent.
Orchestrates session state and provides high-level session operations.
NO FALLBACK LOGIC - fails fast on errors.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.storage.advisor_session_store import AdvisorSessionStore


class SessionManager:
    """High-level session management for advisor chat sessions.

    Provides session lifecycle management and state orchestration
    for the advisor agent CLI interface.
    """

    def __init__(self, db_path: str):
        """Initialize session manager.

        Args:
            db_path: Database path for session storage

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path is required")

        self.db_path = db_path
        self.session_store = AdvisorSessionStore(db_path)

    def create_session(self, advisor_id: str, transcript_id: Optional[str] = None,
                      plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new advisor session.

        Args:
            advisor_id: Advisor identifier
            transcript_id: Optional transcript to pre-load
            plan_id: Optional plan to pre-load

        Returns:
            Complete session data dictionary

        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
            Exception: If session creation fails (NO FALLBACK)
        """
        if not advisor_id:
            raise ValueError("advisor_id is required")

        if transcript_id and plan_id:
            raise ValueError("Provide either transcript_id or plan_id, not both")

        try:
            # Create session in database
            session_id = self.session_store.create_session(
                advisor_id=advisor_id,
                plan_id=plan_id,
                transcript_id=transcript_id
            )

            # Get complete session data
            session = self.session_store.get_session(session_id)
            if not session:
                raise Exception(f"Failed to retrieve created session: {session_id}")

            return session

        except Exception as e:
            raise Exception(f"Failed to create session: {str(e)}")

    def resume_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Resume an existing session.

        Args:
            session_id: Session identifier to resume

        Returns:
            Session data if found, None if not found

        Raises:
            Exception: If resume operation fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        try:
            session = self.session_store.get_session(session_id)
            return session

        except Exception as e:
            raise Exception(f"Failed to resume session: {str(e)}")

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update

        Returns:
            True if update successful

        Raises:
            Exception: If update fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        try:
            return self.session_store.update_session(session_id, updates)

        except Exception as e:
            raise Exception(f"Failed to update session: {str(e)}")

    def set_active_workflow(self, session_id: str, workflow_id: str) -> bool:
        """Set the active workflow for a session.

        Args:
            session_id: Session identifier
            workflow_id: Workflow to make active

        Returns:
            True if successful

        Raises:
            Exception: If operation fails (NO FALLBACK)
        """
        if not session_id or not workflow_id:
            raise ValueError("session_id and workflow_id are required")

        return self.update_session(session_id, {
            'active_workflow_id': workflow_id,
            'cursor_step': 1,  # Reset to first step
            'step_statuses': {}  # Clear previous step statuses
        })

    def update_step_progress(self, session_id: str, step_number: int, status: str,
                           note: Optional[str] = None) -> bool:
        """Update progress for a specific step.

        Args:
            session_id: Session identifier
            step_number: Step number to update
            status: Step status (completed, skipped, failed, etc.)
            note: Optional note about the step

        Returns:
            True if successful

        Raises:
            Exception: If update fails (NO FALLBACK)
        """
        if not session_id or step_number < 1:
            raise ValueError("Valid session_id and step_number (>= 1) required")

        if not status:
            raise ValueError("Status is required")

        try:
            # Get current session
            session = self.session_store.get_session(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")

            # Update step statuses
            step_statuses = session.get('step_statuses', {})
            step_key = str(step_number)

            step_statuses[step_key] = {
                'status': status,
                'updated_at': datetime.utcnow().isoformat(),
                'note': note
            }

            # Update cursor if this is a forward progression
            current_cursor = session.get('cursor_step', 1)
            if step_number >= current_cursor and status in ['completed', 'skipped']:
                new_cursor = step_number + 1
            else:
                new_cursor = current_cursor

            return self.update_session(session_id, {
                'step_statuses': step_statuses,
                'cursor_step': new_cursor
            })

        except Exception as e:
            raise Exception(f"Failed to update step progress: {str(e)}")

    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of session progress.

        Args:
            session_id: Session identifier

        Returns:
            Summary of session state and progress

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        try:
            session = self.session_store.get_session(session_id)
            if not session:
                raise ValueError(f"Session not found: {session_id}")

            step_statuses = session.get('step_statuses', {})

            # Count step statuses
            completed_steps = [k for k, v in step_statuses.items() if v.get('status') == 'completed']
            skipped_steps = [k for k, v in step_statuses.items() if v.get('status') == 'skipped']
            failed_steps = [k for k, v in step_statuses.items() if v.get('status') == 'failed']

            return {
                'session_id': session_id,
                'advisor_id': session['advisor_id'],
                'active_workflow_id': session.get('active_workflow_id'),
                'current_step': session.get('cursor_step', 1),
                'progress': {
                    'completed_steps': len(completed_steps),
                    'skipped_steps': len(skipped_steps),
                    'failed_steps': len(failed_steps),
                    'total_actions': len(step_statuses)
                },
                'context': {
                    'plan_id': session.get('plan_id'),
                    'transcript_id': session.get('transcript_id')
                },
                'created_at': session.get('created_at'),
                'updated_at': session.get('updated_at')
            }

        except Exception as e:
            raise Exception(f"Failed to get session summary: {str(e)}")

    def list_advisor_sessions(self, advisor_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """List recent sessions for an advisor.

        Args:
            advisor_id: Advisor identifier
            limit: Maximum sessions to return

        Returns:
            List of session summaries

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not advisor_id:
            raise ValueError("advisor_id is required")

        try:
            return self.session_store.list_advisor_sessions(advisor_id, limit)

        except Exception as e:
            raise Exception(f"Failed to list advisor sessions: {str(e)}")

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
            return self.session_store.delete_session(session_id)

        except Exception as e:
            raise Exception(f"Failed to delete session: {str(e)}")