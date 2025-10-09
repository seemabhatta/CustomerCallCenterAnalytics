"""
Storage layer for caching GenAI-generated insights.

Caches expensive LLM calls to avoid regeneration within TTL window.
Supports persona-specific insights (leadership, servicing, marketing).
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path


class InsightStore:
    """SQLite storage for GenAI insights with TTL-based caching."""

    def __init__(self, db_path: str = "data/call_center.db"):
        self.db_path = db_path
        self._ensure_database_exists()
        self._create_tables()

    def _ensure_database_exists(self):
        """Ensure database directory and file exist."""
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

        if not db_file.exists():
            # Create empty database
            conn = sqlite3.connect(self.db_path)
            conn.close()

    def _create_tables(self):
        """Create insights storage table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS insights (
                id TEXT PRIMARY KEY,
                insight_type TEXT NOT NULL,
                persona TEXT NOT NULL,
                insight_data TEXT NOT NULL,
                metadata TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TIMESTAMP,
                generation_time_ms INTEGER,
                tokens_used INTEGER,
                confidence_score REAL
            )
        ''')

        # Index for efficient lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_insight_type_persona
            ON insights(insight_type, persona, expires_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires_at
            ON insights(expires_at)
        ''')

        conn.commit()
        conn.close()

    def store(
        self,
        insight_id: str,
        insight_type: str,
        persona: str,
        insight_data: Dict[str, Any],
        ttl_hours: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        generation_time_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
        confidence_score: Optional[float] = None
    ) -> str:
        """
        Store a GenAI insight with TTL.

        Args:
            insight_id: Unique identifier
            insight_type: briefing, dollar_impact, churn_analysis, etc.
            persona: leadership, servicing, marketing
            insight_data: The actual insight content
            ttl_hours: Time to live in hours
            metadata: Optional metadata about generation
            generation_time_ms: Time taken to generate (for monitoring)
            tokens_used: LLM tokens consumed (for cost tracking)
            confidence_score: LLM confidence in the insight

        Returns:
            insight_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        cursor.execute('''
            INSERT OR REPLACE INTO insights
            (id, insight_type, persona, insight_data, metadata, expires_at,
             generation_time_ms, tokens_used, confidence_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            insight_id,
            insight_type,
            persona,
            json.dumps(insight_data),
            json.dumps(metadata) if metadata else None,
            expires_at.isoformat(),
            generation_time_ms,
            tokens_used,
            confidence_score
        ))

        conn.commit()
        conn.close()

        return insight_id

    def get(
        self,
        insight_type: str,
        persona: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest non-expired insight for type/persona.

        Args:
            insight_type: Type of insight to retrieve
            persona: Persona the insight was generated for

        Returns:
            Insight data if found and not expired, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute('''
            SELECT id, insight_data, generated_at, expires_at, confidence_score, metadata
            FROM insights
            WHERE insight_type = ?
            AND persona = ?
            AND expires_at > ?
            ORDER BY generated_at DESC
            LIMIT 1
        ''', (insight_type, persona, now))

        result = cursor.fetchone()

        if result:
            # Update access tracking
            cursor.execute('''
                UPDATE insights
                SET access_count = access_count + 1,
                    last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (result[0],))
            conn.commit()

            insight_data = json.loads(result[1])
            insight_data['_cached'] = True
            insight_data['_generated_at'] = result[2]
            insight_data['_expires_at'] = result[3]
            insight_data['_confidence_score'] = result[4]
            if result[5]:
                insight_data['_metadata'] = json.loads(result[5])

            conn.close()
            return insight_data

        conn.close()
        return None

    def get_by_id(self, insight_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific insight by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT insight_data, generated_at, expires_at, confidence_score
            FROM insights
            WHERE id = ?
        ''', (insight_id,))

        result = cursor.fetchone()
        conn.close()

        if result:
            insight_data = json.loads(result[0])
            insight_data['_generated_at'] = result[1]
            insight_data['_expires_at'] = result[2]
            insight_data['_confidence_score'] = result[3]
            return insight_data

        return None

    def list_cached(
        self,
        persona: Optional[str] = None,
        only_active: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all cached insights, optionally filtered by persona.

        Args:
            persona: Filter by persona (None = all)
            only_active: Only return non-expired insights

        Returns:
            List of insight summaries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT id, insight_type, persona, generated_at, expires_at,
                   access_count, confidence_score
            FROM insights
        '''
        params = []

        conditions = []
        if persona:
            conditions.append('persona = ?')
            params.append(persona)

        if only_active:
            conditions.append('expires_at > ?')
            params.append(datetime.utcnow().isoformat())

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        query += ' ORDER BY generated_at DESC'

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        insights = []
        for row in results:
            insights.append({
                'id': row[0],
                'insight_type': row[1],
                'persona': row[2],
                'generated_at': row[3],
                'expires_at': row[4],
                'access_count': row[5],
                'confidence_score': row[6]
            })

        return insights

    def cleanup_expired(self) -> int:
        """
        Remove expired insights from storage.

        Returns:
            Number of insights deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        cursor.execute('''
            DELETE FROM insights
            WHERE expires_at <= ?
        ''', (now,))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def clear_cache(
        self,
        persona: Optional[str] = None,
        insight_type: Optional[str] = None
    ) -> int:
        """
        Clear cached insights, optionally filtered.

        Args:
            persona: Clear only this persona's cache (None = all)
            insight_type: Clear only this type (None = all)

        Returns:
            Number of insights deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = 'DELETE FROM insights'
        params = []
        conditions = []

        if persona:
            conditions.append('persona = ?')
            params.append(persona)

        if insight_type:
            conditions.append('insight_type = ?')
            params.append(insight_type)

        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)

        cursor.execute(query, params)
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics about cached insights
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()

        # Total insights
        cursor.execute('SELECT COUNT(*) FROM insights')
        total = cursor.fetchone()[0]

        # Active insights
        cursor.execute('SELECT COUNT(*) FROM insights WHERE expires_at > ?', (now,))
        active = cursor.fetchone()[0]

        # By persona
        cursor.execute('''
            SELECT persona, COUNT(*)
            FROM insights
            WHERE expires_at > ?
            GROUP BY persona
        ''', (now,))
        by_persona = dict(cursor.fetchall())

        # Most accessed
        cursor.execute('''
            SELECT id, insight_type, persona, access_count
            FROM insights
            WHERE expires_at > ?
            ORDER BY access_count DESC
            LIMIT 5
        ''', (now,))
        most_accessed = [
            {'id': row[0], 'type': row[1], 'persona': row[2], 'access_count': row[3]}
            for row in cursor.fetchall()
        ]

        # Average generation time
        cursor.execute('''
            SELECT AVG(generation_time_ms), AVG(tokens_used), AVG(confidence_score)
            FROM insights
            WHERE expires_at > ?
        ''', (now,))
        avgs = cursor.fetchone()

        conn.close()

        return {
            'total_insights': total,
            'active_insights': active,
            'expired_insights': total - active,
            'by_persona': by_persona,
            'most_accessed': most_accessed,
            'avg_generation_time_ms': avgs[0] if avgs[0] else None,
            'avg_tokens_used': avgs[1] if avgs[1] else None,
            'avg_confidence_score': avgs[2] if avgs[2] else None
        }
