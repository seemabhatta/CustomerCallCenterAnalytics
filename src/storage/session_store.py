"""SQLite storage layer for leadership conversation sessions.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: No hardcoded routing logic - all decisions by LLM agents
- TDD: Designed to pass the comprehensive test suite
"""
import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class SessionStore:
    """SQLite-based storage for leadership conversation sessions.

    Implements pure data layer with NO FALLBACK logic.
    All business decisions delegated to LLM agents.
    """

    def __init__(self, db_path: str):
        """Initialize store with database path.

        Args:
            db_path: SQLite database file path

        Raises:
            Exception: If database initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize database schema from insights_schema.sql.

        Raises:
            Exception: If schema creation fails (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Enable foreign key enforcement
            cursor.execute('PRAGMA foreign_keys = ON')

            # Read and execute schema from file
            with open('data/insights_schema.sql', 'r') as f:
                schema_sql = f.read()
                cursor.executescript(schema_sql)

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Database initialization failed: {str(e)}")
        finally:
            conn.close()

    def create_session(self, executive_id: str, executive_role: str,
                      focus_area: str = None) -> Dict[str, Any]:
        """Create new leadership conversation session.

        Args:
            executive_id: Unique identifier for executive
            executive_role: VP, CCO, COO, Director, Manager
            focus_area: compliance, performance, risk, strategic, operational

        Returns:
            Session data dictionary

        Raises:
            Exception: If creation fails (NO FALLBACK)
        """
        if not executive_id:
            raise ValueError("executive_id cannot be empty")

        if executive_role not in ['VP', 'CCO', 'COO', 'Director', 'Manager']:
            raise ValueError(f"Invalid executive_role: {executive_role}")

        session_id = str(uuid.uuid4())
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO leadership_sessions
                (session_id, executive_id, executive_role, focus_area, started_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, executive_id, executive_role, focus_area, now, now))

            conn.commit()

            return {
                'session_id': session_id,
                'executive_id': executive_id,
                'executive_role': executive_role,
                'focus_area': focus_area,
                'started_at': now.isoformat(),
                'last_active': now.isoformat(),
                'status': 'active'
            }

        except Exception as e:
            conn.rollback()
            raise Exception(f"Session creation failed: {str(e)}")
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session data or None if not found

        Raises:
            Exception: If query fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM leadership_sessions
                WHERE session_id = ?
            ''', (session_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return dict(row)

        except Exception as e:
            raise Exception(f"Session retrieval failed: {str(e)}")
        finally:
            conn.close()

    def get_or_create_session(self, executive_id: str, executive_role: str,
                             focus_area: str = None) -> Dict[str, Any]:
        """Get active session or create new one.

        Args:
            executive_id: Executive identifier
            executive_role: Executive role
            focus_area: Focus area for new session

        Returns:
            Session data
        """
        # Look for active session for this executive
        active_session = self.get_active_session(executive_id)

        if active_session:
            return active_session

        # Create new session
        return self.create_session(executive_id, executive_role, focus_area)

    def get_active_session(self, executive_id: str) -> Optional[Dict[str, Any]]:
        """Get active session for executive.

        Args:
            executive_id: Executive identifier

        Returns:
            Active session or None
        """
        if not executive_id:
            raise ValueError("executive_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get most recent active session
            cursor.execute('''
                SELECT * FROM leadership_sessions
                WHERE executive_id = ? AND status = 'active'
                ORDER BY last_active DESC
                LIMIT 1
            ''', (executive_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return dict(row)

        except Exception as e:
            raise Exception(f"Active session retrieval failed: {str(e)}")
        finally:
            conn.close()

    def add_message(self, session_id: str, role: str, content: str,
                   metadata: Dict[str, Any] = None) -> str:
        """Add message to session.

        Args:
            session_id: Session identifier
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (classification, confidence, etc.)

        Returns:
            Message ID

        Raises:
            Exception: If addition fails (NO FALLBACK)
        """
        if not session_id or not role or not content:
            raise ValueError("session_id, role, and content are required")

        if role not in ['user', 'assistant']:
            raise ValueError(f"Invalid role: {role}")

        message_id = str(uuid.uuid4())
        now = datetime.now()

        # Extract metadata fields
        query_classification = None
        data_sources_used = None
        confidence_score = None
        token_count = 0
        response_time_ms = None
        cache_hit = False

        if metadata:
            query_classification = json.dumps(metadata.get('query_classification'))
            data_sources_used = json.dumps(metadata.get('data_sources_used'))
            confidence_score = metadata.get('confidence_score')
            token_count = metadata.get('token_count', 0)
            response_time_ms = metadata.get('response_time_ms')
            cache_hit = metadata.get('cache_hit', False)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO session_messages
                (message_id, session_id, role, content, query_classification,
                 data_sources_used, confidence_score, token_count,
                 response_time_ms, cache_hit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (message_id, session_id, role, content, query_classification,
                  data_sources_used, confidence_score, token_count,
                  response_time_ms, cache_hit, now))

            conn.commit()
            return message_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Message addition failed: {str(e)}")
        finally:
            conn.close()

    def get_session_messages(self, session_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get messages for session.

        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages

        Returns:
            List of message dictionaries
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            query = '''
                SELECT * FROM session_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            '''

            if limit:
                query += f' LIMIT {limit}'

            cursor.execute(query, (session_id,))
            rows = cursor.fetchall()

            messages = []
            for row in rows:
                message = dict(row)
                # Parse JSON fields
                if message['query_classification']:
                    message['query_classification'] = json.loads(message['query_classification'])
                if message['data_sources_used']:
                    message['data_sources_used'] = json.loads(message['data_sources_used'])
                messages.append(message)

            return messages

        except Exception as e:
            raise Exception(f"Message retrieval failed: {str(e)}")
        finally:
            conn.close()

    def update_session_context(self, session_id: str, context_data: Dict[str, Any]):
        """Update session context data.

        Args:
            session_id: Session identifier
            context_data: Context data to store
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE leadership_sessions
                SET context_data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (json.dumps(context_data), session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Context update failed: {str(e)}")
        finally:
            conn.close()

    def update_session_focus_area(self, session_id: str, focus_area: str):
        """Update session focus area determined by agent.

        Args:
            session_id: Session identifier
            focus_area: Focus area determined by agent
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        if not focus_area:
            raise ValueError("focus_area cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE leadership_sessions
                SET focus_area = ?, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (focus_area, session_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Session focus area update failed: {str(e)}")
        finally:
            conn.close()

    def archive_session(self, session_id: str):
        """Archive session.

        Args:
            session_id: Session identifier
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE leadership_sessions
                SET status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            ''', (session_id,))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Session archival failed: {str(e)}")
        finally:
            conn.close()

    def get_executive_sessions(self, executive_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions for executive.

        Args:
            executive_id: Executive identifier
            limit: Maximum number of sessions to return

        Returns:
            List of session dictionaries
        """
        if not executive_id:
            raise ValueError("executive_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM leadership_sessions
                WHERE executive_id = ?
                ORDER BY last_active DESC
                LIMIT ?
            ''', (executive_id, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            raise Exception(f"Executive sessions retrieval failed: {str(e)}")
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and all associated messages.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found

        Raises:
            Exception: If deletion fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("session_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # First check if session exists
            cursor.execute('''
                SELECT COUNT(*) FROM leadership_sessions WHERE session_id = ?
            ''', (session_id,))

            count = cursor.fetchone()[0]
            if count == 0:
                return False

            # Delete messages first (due to foreign key constraints)
            cursor.execute('''
                DELETE FROM session_messages WHERE session_id = ?
            ''', (session_id,))

            # Delete the session
            cursor.execute('''
                DELETE FROM leadership_sessions WHERE session_id = ?
            ''', (session_id,))

            conn.commit()
            return True

        except Exception as e:
            conn.rollback()
            raise Exception(f"Session deletion failed: {str(e)}")
        finally:
            conn.close()