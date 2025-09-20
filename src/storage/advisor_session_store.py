"""
SQLite storage layer for advisor chat sessions.
Manages ephemeral session state for the CLI agent with full traceability.
NO FALLBACK LOGIC - fails fast on database errors.
"""
import sqlite3
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime


class AdvisorSessionStore:
    """SQLite-based storage for advisor chat sessions.

    Provides persistence for advisor CLI sessions including:
    - Session metadata (advisor, context)
    - Workflow state (active workflow, step progress)
    - Conversation history for context
    - Audit trail for compliance
    """

    def __init__(self, db_path: str):
        """Initialize the store with database path.

        Args:
            db_path: Path to SQLite database file

        Raises:
            Exception: If database initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema for advisor sessions."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create advisor_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS advisor_sessions (
                    session_id TEXT PRIMARY KEY,
                    advisor_id TEXT NOT NULL,
                    plan_id TEXT,
                    transcript_id TEXT,
                    active_workflow_id TEXT,
                    cursor_step INTEGER DEFAULT 1,
                    step_statuses TEXT,  -- JSON: {"1": "completed", "2": "skipped", ...}
                    conversation_history TEXT,  -- JSON: [{"role": "user", "content": "..."}, ...]
                    context_data TEXT,  -- JSON: additional session context
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes for common queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_advisor_sessions_advisor_id
                ON advisor_sessions (advisor_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_advisor_sessions_created_at
                ON advisor_sessions (created_at)
            ''')

            # Auto-update timestamp trigger
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_advisor_session_timestamp
                AFTER UPDATE ON advisor_sessions
                BEGIN
                    UPDATE advisor_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = NEW.session_id;
                END
            ''')

            conn.commit()

        finally:
            conn.close()

    def create_session(self, advisor_id: str, plan_id: Optional[str] = None,
                      transcript_id: Optional[str] = None) -> str:
        """Create a new advisor session.

        Args:
            advisor_id: Advisor identifier
            plan_id: Optional plan to pre-load
            transcript_id: Optional transcript to pre-load

        Returns:
            Session ID of the created session

        Raises:
            ValueError: Missing required fields (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not advisor_id:
            raise ValueError("advisor_id is required")

        session_id = f"SID-{uuid.uuid4().hex[:8]}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO advisor_sessions
                (session_id, advisor_id, plan_id, transcript_id, step_statuses,
                 conversation_history, context_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                advisor_id,
                plan_id,
                transcript_id,
                json.dumps({}),  # Empty step statuses
                json.dumps([]),  # Empty conversation history
                json.dumps({})   # Empty context
            ))

            conn.commit()
            return session_id

        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary or None if not found

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT session_id, advisor_id, plan_id, transcript_id, active_workflow_id,
                       cursor_step, step_statuses, conversation_history, context_data,
                       created_at, updated_at
                FROM advisor_sessions
                WHERE session_id = ?
            ''', (session_id,))

            row = cursor.fetchone()

            if not row:
                return None

            return {
                'session_id': row[0],
                'advisor_id': row[1],
                'plan_id': row[2],
                'transcript_id': row[3],
                'active_workflow_id': row[4],
                'cursor_step': row[5],
                'step_statuses': json.loads(row[6]) if row[6] else {},
                'conversation_history': json.loads(row[7]) if row[7] else [],
                'context_data': json.loads(row[8]) if row[8] else {},
                'created_at': row[9],
                'updated_at': row[10]
            }

        finally:
            conn.close()

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data.

        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update

        Returns:
            True if update successful, False if session not found

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id is required")

        # Build dynamic update query based on provided fields
        valid_fields = {
            'plan_id', 'transcript_id', 'active_workflow_id', 'cursor_step',
            'step_statuses', 'conversation_history', 'context_data'
        }

        update_fields = []
        update_values = []

        for field, value in updates.items():
            if field in valid_fields:
                update_fields.append(f"{field} = ?")
                if field in ['step_statuses', 'conversation_history', 'context_data']:
                    # JSON fields need serialization
                    update_values.append(json.dumps(value))
                else:
                    update_values.append(value)

        if not update_fields:
            return True  # No valid fields to update

        update_values.append(session_id)  # For WHERE clause

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(f'''
                UPDATE advisor_sessions
                SET {', '.join(update_fields)}
                WHERE session_id = ?
            ''', update_values)

            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()

    def add_conversation_turn(self, session_id: str, role: str, content: str) -> bool:
        """Add a conversation turn to session history.

        Args:
            session_id: Session identifier
            role: Either 'user' or 'assistant'
            content: Message content

        Returns:
            True if successful

        Raises:
            ValueError: Invalid role or missing data (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}")

        if not content:
            raise ValueError("Content cannot be empty")

        # Get current conversation history
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Add new turn
        conversation_history = session['conversation_history']
        conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.utcnow().isoformat()
        })

        # Keep only last 20 turns to prevent unbounded growth
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        # Update session
        return self.update_session(session_id, {
            'conversation_history': conversation_history
        })

    def list_advisor_sessions(self, advisor_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions for an advisor.

        Args:
            advisor_id: Advisor identifier
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT session_id, plan_id, transcript_id, active_workflow_id,
                       created_at, updated_at
                FROM advisor_sessions
                WHERE advisor_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            ''', (advisor_id, limit))

            rows = cursor.fetchall()

            return [
                {
                    'session_id': row[0],
                    'plan_id': row[1],
                    'transcript_id': row[2],
                    'active_workflow_id': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                }
                for row in rows
            ]

        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM advisor_sessions WHERE session_id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0

        finally:
            conn.close()