import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import json

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from ..config.settings import settings
from ..models.transcript import CallTranscript

class DatabaseManager:
    """Manages both TinyDB for transcripts and SQLite for structured data."""
    
    def __init__(self):
        # Initialize TinyDB for transcripts (unstructured/semi-structured data)
        self.transcripts_db = TinyDB(
            settings.TRANSCRIPTS_DB,
            storage=CachingMiddleware(JSONStorage)
        )
        
        # Initialize SQLite for structured data
        self.sessions_db_path = settings.SESSIONS_DB
        self._init_sqlite_schema()
    
    def _init_sqlite_schema(self):
        """Initialize SQLite database schema."""
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    input_data TEXT,
                    output_data TEXT,
                    metadata TEXT
                );
                
                CREATE TABLE IF NOT EXISTS analysis_results (
                    result_id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    confidence REAL,
                    result_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS actions (
                    action_id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    status TEXT DEFAULT 'draft',
                    priority INTEGER DEFAULT 3,
                    assigned_to TEXT,
                    due_date TIMESTAMP,
                    action_data TEXT NOT NULL,
                    approval_level TEXT DEFAULT 'advisor',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    approver_id TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    comments TEXT,
                    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (action_id) REFERENCES actions(action_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_transcript_id ON agent_sessions(transcript_id);
                CREATE INDEX IF NOT EXISTS idx_analysis_transcript ON analysis_results(transcript_id);
                CREATE INDEX IF NOT EXISTS idx_actions_transcript ON actions(transcript_id);
                CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);
            """)
    
    # Transcript Storage Methods (TinyDB)
    def store_transcript(self, transcript: CallTranscript) -> str:
        """Store a call transcript in TinyDB."""
        transcript_data = transcript.model_dump(mode='json')
        
        # Convert datetime objects to ISO strings for JSON storage
        transcript_data['created_at'] = transcript.created_at.isoformat()
        transcript_data['call_metadata']['call_date'] = transcript.call_metadata.call_date.isoformat()
        
        doc_id = self.transcripts_db.insert(transcript_data)
        return transcript.transcript_id
    
    def get_transcript(self, transcript_id: str) -> Optional[CallTranscript]:
        """Retrieve a transcript by ID."""
        TranscriptQuery = Query()
        result = self.transcripts_db.search(TranscriptQuery.transcript_id == transcript_id)
        
        if not result:
            return None
        
        # Convert ISO strings back to datetime objects
        transcript_data = result[0]
        transcript_data['created_at'] = datetime.fromisoformat(transcript_data['created_at'])
        transcript_data['call_metadata']['call_date'] = datetime.fromisoformat(
            transcript_data['call_metadata']['call_date']
        )
        
        return CallTranscript(**transcript_data)
    
    def list_transcripts(self, limit: Optional[int] = None, scenario: Optional[str] = None) -> List[Dict[str, Any]]:
        """List transcripts with optional filtering."""
        TranscriptQuery = Query()
        
        if scenario:
            results = self.transcripts_db.search(TranscriptQuery.scenario == scenario)
        else:
            results = self.transcripts_db.all()
        
        # Sort by created_at descending
        results.sort(key=lambda x: x['created_at'], reverse=True)
        
        if limit:
            results = results[:limit]
        
        # Return summary info only
        summaries = []
        for result in results:
            summaries.append({
                'transcript_id': result['transcript_id'],
                'call_id': result['call_metadata']['call_id'],
                'scenario': result['scenario'],
                'customer_name': result['customer']['name'],
                'advisor_name': result['advisor']['name'],
                'duration_minutes': result['call_metadata']['duration_seconds'] // 60,
                'created_at': result['created_at'],
                'tags': result.get('tags', [])
            })
        
        return summaries
    
    def search_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """Search transcripts by text content."""
        results = []
        for doc in self.transcripts_db.all():
            # Search in full transcript text
            segments_text = ' '.join([seg['text'] for seg in doc['segments']])
            if query.lower() in segments_text.lower():
                results.append({
                    'transcript_id': doc['transcript_id'],
                    'call_id': doc['call_metadata']['call_id'],
                    'scenario': doc['scenario'],
                    'customer_name': doc['customer']['name'],
                    'match_preview': self._get_match_preview(segments_text, query)
                })
        
        return results
    
    def _get_match_preview(self, text: str, query: str, context_chars: int = 100) -> str:
        """Get a preview of text around the matched query."""
        text_lower = text.lower()
        query_lower = query.lower()
        
        match_pos = text_lower.find(query_lower)
        if match_pos == -1:
            return ""
        
        start = max(0, match_pos - context_chars // 2)
        end = min(len(text), match_pos + len(query) + context_chars // 2)
        
        preview = text[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(text):
            preview = preview + "..."
        
        return preview
    
    # Agent Session Management (SQLite)
    def create_agent_session(self, transcript_id: str, agent_type: str, input_data: Dict[str, Any]) -> str:
        """Create a new agent processing session."""
        import uuid
        session_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.execute("""
                INSERT INTO agent_sessions (session_id, transcript_id, agent_type, input_data)
                VALUES (?, ?, ?, ?)
            """, (session_id, transcript_id, agent_type, json.dumps(input_data)))
        
        return session_id
    
    def update_agent_session(self, session_id: str, status: str, output_data: Optional[Dict[str, Any]] = None):
        """Update agent session with results."""
        with sqlite3.connect(self.sessions_db_path) as conn:
            if output_data:
                conn.execute("""
                    UPDATE agent_sessions 
                    SET status = ?, output_data = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, json.dumps(output_data), session_id))
            else:
                conn.execute("""
                    UPDATE agent_sessions 
                    SET status = ?, completed_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, session_id))
    
    def get_agent_sessions(self, transcript_id: str) -> List[Dict[str, Any]]:
        """Get all agent sessions for a transcript."""
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM agent_sessions 
                WHERE transcript_id = ? 
                ORDER BY started_at DESC
            """, (transcript_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # Analysis Results Storage
    def store_analysis_result(self, transcript_id: str, analysis_type: str, 
                            result_data: Dict[str, Any], confidence: Optional[float] = None) -> str:
        """Store analysis results."""
        import uuid
        result_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.execute("""
                INSERT INTO analysis_results (result_id, transcript_id, analysis_type, confidence, result_data)
                VALUES (?, ?, ?, ?, ?)
            """, (result_id, transcript_id, analysis_type, confidence, json.dumps(result_data)))
        
        return result_id
    
    def get_analysis_results(self, transcript_id: str, analysis_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get analysis results for a transcript."""
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if analysis_type:
                cursor = conn.execute("""
                    SELECT * FROM analysis_results 
                    WHERE transcript_id = ? AND analysis_type = ?
                    ORDER BY created_at DESC
                """, (transcript_id, analysis_type))
            else:
                cursor = conn.execute("""
                    SELECT * FROM analysis_results 
                    WHERE transcript_id = ?
                    ORDER BY created_at DESC
                """, (transcript_id,))
            
            results = []
            for row in cursor.fetchall():
                result_dict = dict(row)
                result_dict['result_data'] = json.loads(result_dict['result_data'])
                results.append(result_dict)
            
            return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        transcript_count = len(self.transcripts_db.all())
        
        with sqlite3.connect(self.sessions_db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM agent_sessions")
            session_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM analysis_results")
            analysis_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM actions")
            action_count = cursor.fetchone()[0]
        
        return {
            'transcripts': transcript_count,
            'agent_sessions': session_count,
            'analysis_results': analysis_count,
            'actions': action_count
        }
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old data (optional maintenance function)."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cutoff_iso = cutoff_date.isoformat()
        
        # Clean TinyDB
        TranscriptQuery = Query()
        self.transcripts_db.remove(TranscriptQuery.created_at < cutoff_iso)
        
        # Clean SQLite
        with sqlite3.connect(self.sessions_db_path) as conn:
            conn.execute("""
                DELETE FROM agent_sessions 
                WHERE started_at < datetime('now', '-{} days')
            """.format(days_old))
            
            conn.execute("""
                DELETE FROM analysis_results 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days_old))