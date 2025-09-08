"""
SQLite-based storage for transcripts and analysis results.
Provides performance, querying capabilities, data integrity, and action queue management.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from .config import settings


class SQLiteStorage:
    """SQLite-based storage for transcripts and analysis results."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or settings.DATABASE_PATH)
        self.db_path.parent.mkdir(exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with schema and indexes."""
        with self._get_connection() as conn:
            # Create tables
            conn.executescript("""
                -- Transcripts table (call recordings/generated content)
                CREATE TABLE IF NOT EXISTS transcripts (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'generated',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Analyses table (multi-agent analysis results)
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    confidence_score REAL,
                    risk_level TEXT CHECK(risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
                    resolution_status TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transcript_id) REFERENCES transcripts(id) ON DELETE CASCADE
                );

                -- Action items table (extracted from analyses)
                CREATE TABLE IF NOT EXISTS action_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    action_type TEXT,
                    description TEXT,
                    priority TEXT CHECK(priority IN ('LOW', 'MEDIUM', 'HIGH')) DEFAULT 'MEDIUM',
                    due_date TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                );

                -- Predictions table (FCR, churn, etc.)
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id TEXT NOT NULL,
                    prediction_type TEXT,
                    value REAL,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (analysis_id) REFERENCES analyses(id) ON DELETE CASCADE
                );

                -- Sessions table (agent execution tracking)
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE,
                    agent_type TEXT,
                    input_prompt TEXT,
                    output_result TEXT,
                    execution_time_ms INTEGER,
                    status TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_transcripts_created ON transcripts(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_transcripts_source ON transcripts(source);
                CREATE INDEX IF NOT EXISTS idx_analyses_transcript ON analyses(transcript_id);
                CREATE INDEX IF NOT EXISTS idx_analyses_risk ON analyses(risk_level);
                CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(status);
                CREATE INDEX IF NOT EXISTS idx_action_items_type ON action_items(action_type);
                CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
                CREATE INDEX IF NOT EXISTS idx_sessions_agent ON sessions(agent_type);
            """)
            
            # Enable full-text search
            try:
                conn.execute("DROP TABLE IF EXISTS transcripts_fts")
                conn.execute("""
                    CREATE VIRTUAL TABLE transcripts_fts USING fts5(
                        id UNINDEXED,
                        content,
                        source UNINDEXED
                    )
                """)
            except sqlite3.OperationalError:
                # FTS not available, skip
                pass
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling."""
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def save_transcript(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save transcript with auto-generated ID."""
        timestamp = datetime.now()
        transcript_id = f"CALL_{timestamp:%Y%m%d_%H%M%S}"
        
        metadata_json = json.dumps(metadata or {})
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO transcripts (id, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (transcript_id, content, metadata_json, timestamp.isoformat(), timestamp.isoformat()))
            
            # Update FTS if available
            try:
                conn.execute("""
                    INSERT INTO transcripts_fts (id, content, source) 
                    VALUES (?, ?, ?)
                """, (transcript_id, content, 'generated'))
            except sqlite3.OperationalError:
                pass  # FTS not available
        
        return transcript_id
    
    def load_transcript(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Load transcript by ID or partial ID."""
        with self._get_connection() as conn:
            # Try exact match first
            row = conn.execute("""
                SELECT id, content, source, metadata, created_at 
                FROM transcripts 
                WHERE id = ?
            """, (transcript_id,)).fetchone()
            
            if row:
                return self._row_to_dict(row)
            
            # Try partial match
            rows = conn.execute("""
                SELECT id, content, source, metadata, created_at 
                FROM transcripts 
                WHERE id LIKE ?
                ORDER BY created_at DESC
            """, (f"%{transcript_id}%",)).fetchall()
            
            if not rows:
                return None
            
            if len(rows) > 1:
                return {
                    "error": "Multiple matches found",
                    "matches": [row["id"] for row in rows],
                    "suggestion": "Use a more specific ID or choose from the matches above"
                }
            
            return self._row_to_dict(rows[0])
    
    def list_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent transcripts and analyses."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT 
                    t.id,
                    CASE 
                        WHEN t.content LIKE '%ANALYSIS_START%' THEN 'analysis'
                        ELSE 'transcript'
                    END as type,
                    SUBSTR(t.content, 1, 80) || '...' as summary,
                    t.created_at as created,
                    json_extract(t.metadata, '$.type') as metadata_type
                FROM transcripts t
                ORDER BY t.created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            results = []
            for row in rows:
                # Clean up summary - find first meaningful line
                content = row["summary"].replace("**", "").replace("═", "").strip()
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                first_line = lines[0] if lines else "Empty content"
                
                results.append({
                    "id": row["id"],
                    "summary": first_line[:80] + "..." if len(first_line) > 80 else first_line,
                    "created": row["created"],
                    "type": row["metadata_type"] or row["type"],
                    "has_metadata": True
                })
            
            return results
    
    def save_analysis(self, transcript_id: str, analysis_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save analysis results linked to a transcript."""
        timestamp = datetime.now()
        analysis_id = f"ANALYSIS_{transcript_id}_{timestamp:%H%M%S}"
        
        # Parse analysis for structured data
        confidence_score, risk_level, resolution_status = self._parse_analysis(analysis_content)
        
        analysis_metadata = metadata or {}
        analysis_metadata.update({
            "type": "analysis",
            "transcript_id": transcript_id,
            "analysis_timestamp": timestamp.isoformat()
        })
        metadata_json = json.dumps(analysis_metadata)
        
        with self._get_connection() as conn:
            # Insert analysis as transcript (backward compatibility)
            conn.execute("""
                INSERT INTO transcripts (id, content, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (analysis_id, analysis_content, metadata_json, timestamp.isoformat(), timestamp.isoformat()))
            
            # Insert into analyses table
            conn.execute("""
                INSERT INTO analyses (id, transcript_id, content, confidence_score, risk_level, 
                                    resolution_status, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (analysis_id, transcript_id, analysis_content, confidence_score, 
                  risk_level, resolution_status, metadata_json, timestamp.isoformat()))
            
            # Update FTS if available
            try:
                conn.execute("""
                    INSERT INTO transcripts_fts (id, content, source) 
                    VALUES (?, ?, ?)
                """, (analysis_id, analysis_content, 'analysis'))
            except sqlite3.OperationalError:
                pass
        
        return analysis_id
    
    def get_transcript_with_analysis(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get transcript along with any associated analysis."""
        transcript = self.load_transcript(transcript_id)
        if not transcript or 'error' in transcript:
            return transcript
        
        with self._get_connection() as conn:
            # Get related analyses
            rows = conn.execute("""
                SELECT id, content, confidence_score, risk_level, resolution_status, 
                       metadata, created_at
                FROM analyses 
                WHERE transcript_id = ?
                ORDER BY created_at DESC
            """, (transcript_id,)).fetchall()
            
            analyses = [self._row_to_dict(row) for row in rows]
            
            result = transcript.copy()
            result['analyses'] = analyses
            return result
    
    def search_transcripts(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search transcripts by content using FTS or LIKE."""
        with self._get_connection() as conn:
            try:
                # Try FTS first
                rows = conn.execute("""
                    SELECT t.id, t.created_at, snippet(transcripts_fts, 1, '<mark>', '</mark>', '...', 50) as match_context
                    FROM transcripts_fts 
                    JOIN transcripts t ON transcripts_fts.id = t.id
                    WHERE transcripts_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit)).fetchall()
            except sqlite3.OperationalError:
                # Fallback to LIKE search
                rows = conn.execute("""
                    SELECT id, created_at, 
                           SUBSTR(content, MAX(1, INSTR(LOWER(content), LOWER(?)) - 50), 100) as match_context
                    FROM transcripts 
                    WHERE content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (query, f"%{query}%", limit)).fetchall()
            
            return [
                {
                    "id": row["id"],
                    "match_context": row["match_context"],
                    "created": row["created_at"]
                }
                for row in rows
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        try:
            with self._get_connection() as conn:
                stats = conn.execute("""
                    SELECT 
                        (SELECT COUNT(*) FROM transcripts) as total_files,
                        (SELECT COUNT(*) FROM transcripts WHERE metadata NOT LIKE '%"type":"analysis"%') as transcripts,
                        (SELECT COUNT(*) FROM analyses) as analyses,
                        (SELECT COUNT(*) FROM action_items) as action_items,
                        (SELECT COUNT(*) FROM predictions) as predictions,
                        (SELECT COUNT(*) FROM sessions) as sessions
                """).fetchone()
                
                # Get database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    "total_files": stats["total_files"],
                    "transcripts": stats["transcripts"], 
                    "analyses": stats["analyses"],
                    "action_items": stats["action_items"],
                    "predictions": stats["predictions"],
                    "sessions": stats["sessions"],
                    "total_size_mb": round(db_size / (1024 * 1024), 2),
                    "storage_path": str(self.db_path.absolute()),
                    "storage_type": "SQLite"
                }
        except Exception as e:
            return {
                "error": str(e),
                "storage_path": str(self.db_path.absolute()),
                "storage_type": "SQLite"
            }
    
    def log_session(self, session_id: str, agent_type: str, input_prompt: str, 
                   output_result: str, execution_time_ms: int, status: str, 
                   error_message: Optional[str] = None) -> int:
        """Log agent session for tracking and debugging."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO sessions (session_id, agent_type, input_prompt, output_result, 
                                    execution_time_ms, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, agent_type, input_prompt, output_result, execution_time_ms, status, error_message))
            return cursor.lastrowid
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics and insights from stored data."""
        with self._get_connection() as conn:
            # Daily call volume
            daily_stats = conn.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM transcripts 
                WHERE metadata NOT LIKE '%"type":"analysis"%'
                GROUP BY DATE(created_at)
                ORDER BY date DESC
                LIMIT 7
            """).fetchall()
            
            # Risk distribution
            risk_stats = conn.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM analyses 
                WHERE risk_level IS NOT NULL
                GROUP BY risk_level
            """).fetchall()
            
            # Resolution status
            resolution_stats = conn.execute("""
                SELECT resolution_status, COUNT(*) as count
                FROM analyses 
                WHERE resolution_status IS NOT NULL
                GROUP BY resolution_status
            """).fetchall()
            
            # Pending actions
            pending_actions = conn.execute("""
                SELECT action_type, COUNT(*) as count
                FROM action_items 
                WHERE status = 'pending'
                GROUP BY action_type
            """).fetchall()
            
            return {
                "daily_calls": [dict(row) for row in daily_stats],
                "risk_distribution": [dict(row) for row in risk_stats],
                "resolution_status": [dict(row) for row in resolution_stats],
                "pending_actions": [dict(row) for row in pending_actions]
            }
    
    def _parse_analysis(self, analysis_content: str) -> tuple:
        """Extract structured data from analysis content."""
        confidence_score = None
        risk_level = None
        resolution_status = None
        
        lines = analysis_content.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'confidence_score:' in line_lower:
                try:
                    confidence_score = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'risk_level:' in line_lower:
                try:
                    risk_level = line.split(':')[1].strip().upper()
                    if risk_level not in ['LOW', 'MEDIUM', 'HIGH']:
                        risk_level = None
                except IndexError:
                    pass
            elif 'resolution_status:' in line_lower:
                try:
                    resolution_status = line.split(':')[1].strip().upper()
                except IndexError:
                    pass
        
        return confidence_score, risk_level, resolution_status
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert SQLite row to dictionary with JSON parsing."""
        result = dict(row)
        
        # Parse JSON metadata if present
        if 'metadata' in result and result['metadata']:
            try:
                result['metadata'] = json.loads(result['metadata'])
            except (json.JSONDecodeError, TypeError):
                result['metadata'] = {}
        
        return result


# Singleton instance
_storage = None

def get_storage() -> SQLiteStorage:
    """Get the global storage instance."""
    global _storage
    if _storage is None:
        _storage = SQLiteStorage()
    return _storage

# Backward compatibility alias
get_sqlite_storage = get_storage