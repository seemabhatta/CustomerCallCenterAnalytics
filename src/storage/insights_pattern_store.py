"""SQLite storage layer for learned insights patterns.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: No hardcoded routing logic - all decisions by LLM agents
- Learning: Store patterns to improve agent performance over time
"""
import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime


class InsightsPatternStore:
    """SQLite-based storage for learned insights patterns.

    Stores successful patterns discovered by the learning agent
    to improve future query processing and response quality.
    """

    def __init__(self, db_path: str):
        """Initialize pattern store with database path.

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

            # Schema is already created by session_store, just verify table exists
            cursor.execute('''
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='insight_patterns'
            ''')

            if not cursor.fetchone():
                # Read and execute schema from file if not exists
                with open('data/insights_schema.sql', 'r') as f:
                    schema_sql = f.read()
                    cursor.executescript(schema_sql)

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Pattern database initialization failed: {str(e)}")
        finally:
            conn.close()

    def store_pattern(self, pattern_type: str, query_pattern: str,
                     successful_approach: Dict[str, Any], effectiveness_score: float,
                     executive_roles: List[str] = None, focus_areas: List[str] = None) -> str:
        """Store a successful pattern for future use.

        Args:
            pattern_type: Type of pattern (query_classification, data_strategy, etc.)
            query_pattern: Pattern or template for matching queries
            successful_approach: What worked (strategy, tools, format)
            effectiveness_score: Success score (0-100)
            executive_roles: Which executive roles this works for
            focus_areas: Which focus areas this applies to

        Returns:
            Pattern ID

        Raises:
            Exception: If storage fails (NO FALLBACK)
        """
        valid_types = ['query_classification', 'data_strategy', 'aggregation_method', 'response_format']
        if pattern_type not in valid_types:
            raise ValueError(f"Invalid pattern_type: {pattern_type}")

        if not query_pattern or not successful_approach:
            raise ValueError("query_pattern and successful_approach are required")

        if not (0 <= effectiveness_score <= 100):
            raise ValueError("effectiveness_score must be between 0 and 100")

        pattern_id = str(uuid.uuid4())
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO insight_patterns
                (pattern_id, pattern_type, query_pattern, successful_approach,
                 effectiveness_score, usage_count, executive_roles, focus_areas,
                 created_at, last_used, updated_at)
                VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
            ''', (pattern_id, pattern_type, query_pattern,
                  json.dumps(successful_approach), effectiveness_score,
                  json.dumps(executive_roles or []), json.dumps(focus_areas or []),
                  now, now, now))

            conn.commit()
            return pattern_id

        except Exception as e:
            conn.rollback()
            raise Exception(f"Pattern storage failed: {str(e)}")
        finally:
            conn.close()

    def get_patterns_by_type(self, pattern_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get patterns by type, ordered by effectiveness.

        Args:
            pattern_type: Type of pattern to retrieve
            limit: Maximum number of patterns

        Returns:
            List of pattern dictionaries
        """
        if not pattern_type:
            raise ValueError("pattern_type cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM insight_patterns
                WHERE pattern_type = ?
                ORDER BY effectiveness_score DESC, usage_count DESC
                LIMIT ?
            ''', (pattern_type, limit))

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                pattern = dict(row)
                # Parse JSON fields
                pattern['successful_approach'] = json.loads(pattern['successful_approach'])
                pattern['executive_roles'] = json.loads(pattern['executive_roles'])
                pattern['focus_areas'] = json.loads(pattern['focus_areas'])
                patterns.append(pattern)

            return patterns

        except Exception as e:
            raise Exception(f"Pattern retrieval failed: {str(e)}")
        finally:
            conn.close()

    def get_matching_patterns(self, query: str, executive_role: str = None,
                             focus_area: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Get patterns that might match the query.

        Args:
            query: Query to find patterns for
            executive_role: Executive role for filtering
            focus_area: Focus area for filtering
            limit: Maximum patterns to return

        Returns:
            List of matching patterns
        """
        if not query:
            raise ValueError("query cannot be empty")

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Basic pattern matching - could be enhanced with embeddings
            base_query = '''
                SELECT * FROM insight_patterns
                WHERE (
                    query_pattern LIKE ? OR
                    ? LIKE query_pattern OR
                    query_pattern = 'GENERAL'
                )
            '''

            params = [f'%{query.lower()}%', query.lower()]

            # Add role filtering if specified
            if executive_role:
                base_query += ' AND (executive_roles LIKE ? OR executive_roles = "[]")'
                params.append(f'%"{executive_role}"%')

            # Add focus area filtering if specified
            if focus_area:
                base_query += ' AND (focus_areas LIKE ? OR focus_areas = "[]")'
                params.append(f'%"{focus_area}"%')

            base_query += '''
                ORDER BY effectiveness_score DESC, usage_count DESC
                LIMIT ?
            '''
            params.append(limit)

            cursor.execute(base_query, params)
            rows = cursor.fetchall()

            patterns = []
            for row in rows:
                pattern = dict(row)
                # Parse JSON fields
                pattern['successful_approach'] = json.loads(pattern['successful_approach'])
                pattern['executive_roles'] = json.loads(pattern['executive_roles'])
                pattern['focus_areas'] = json.loads(pattern['focus_areas'])
                patterns.append(pattern)

            return patterns

        except Exception as e:
            raise Exception(f"Pattern matching failed: {str(e)}")
        finally:
            conn.close()

    def update_pattern_usage(self, pattern_id: str, effectiveness_feedback: float = None):
        """Update pattern usage statistics.

        Args:
            pattern_id: Pattern identifier
            effectiveness_feedback: Optional feedback on effectiveness (0-100)
        """
        if not pattern_id:
            raise ValueError("pattern_id cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            now = datetime.now()

            if effectiveness_feedback is not None:
                if not (0 <= effectiveness_feedback <= 100):
                    raise ValueError("effectiveness_feedback must be between 0 and 100")

                # Update effectiveness with weighted average
                cursor.execute('''
                    UPDATE insight_patterns
                    SET usage_count = usage_count + 1,
                        effectiveness_score = (effectiveness_score * usage_count + ?) / (usage_count + 1),
                        last_used = ?,
                        updated_at = ?
                    WHERE pattern_id = ?
                ''', (effectiveness_feedback, now, now, pattern_id))
            else:
                # Just increment usage
                cursor.execute('''
                    UPDATE insight_patterns
                    SET usage_count = usage_count + 1,
                        last_used = ?,
                        updated_at = ?
                    WHERE pattern_id = ?
                ''', (now, now, pattern_id))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Pattern usage update failed: {str(e)}")
        finally:
            conn.close()

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern learning statistics.

        Returns:
            Pattern statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Total patterns by type
            cursor.execute('''
                SELECT pattern_type, COUNT(*) as count,
                       AVG(effectiveness_score) as avg_effectiveness,
                       SUM(usage_count) as total_usage
                FROM insight_patterns
                GROUP BY pattern_type
                ORDER BY count DESC
            ''')
            by_type = [dict(row) for row in cursor.fetchall()]

            # Most effective patterns
            cursor.execute('''
                SELECT pattern_type, query_pattern, effectiveness_score, usage_count
                FROM insight_patterns
                ORDER BY effectiveness_score DESC, usage_count DESC
                LIMIT 10
            ''')
            top_patterns = [dict(row) for row in cursor.fetchall()]

            # Most used patterns
            cursor.execute('''
                SELECT pattern_type, query_pattern, effectiveness_score, usage_count
                FROM insight_patterns
                WHERE usage_count > 0
                ORDER BY usage_count DESC, effectiveness_score DESC
                LIMIT 10
            ''')
            most_used = [dict(row) for row in cursor.fetchall()]

            # Overall statistics
            cursor.execute('''
                SELECT COUNT(*) as total_patterns,
                       AVG(effectiveness_score) as avg_effectiveness,
                       SUM(usage_count) as total_usage,
                       MAX(effectiveness_score) as best_effectiveness
                FROM insight_patterns
            ''')
            overall = dict(cursor.fetchone())

            return {
                'patterns_by_type': by_type,
                'top_patterns': top_patterns,
                'most_used_patterns': most_used,
                'overall_statistics': overall
            }

        except Exception as e:
            raise Exception(f"Pattern statistics retrieval failed: {str(e)}")
        finally:
            conn.close()

    def delete_low_performing_patterns(self, min_effectiveness: float = 30.0,
                                      min_usage: int = 5):
        """Clean up patterns that consistently perform poorly.

        Args:
            min_effectiveness: Minimum effectiveness score to keep
            min_usage: Minimum usage count to consider for deletion
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                DELETE FROM insight_patterns
                WHERE effectiveness_score < ? AND usage_count >= ?
            ''', (min_effectiveness, min_usage))

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

        except Exception as e:
            conn.rollback()
            raise Exception(f"Pattern cleanup failed: {str(e)}")
        finally:
            conn.close()

    def export_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """Export patterns for analysis or backup.

        Args:
            pattern_type: Optional type filter

        Returns:
            List of all pattern data
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if pattern_type:
                cursor.execute('''
                    SELECT * FROM insight_patterns
                    WHERE pattern_type = ?
                    ORDER BY created_at DESC
                ''', (pattern_type,))
            else:
                cursor.execute('''
                    SELECT * FROM insight_patterns
                    ORDER BY created_at DESC
                ''')

            rows = cursor.fetchall()
            patterns = []

            for row in rows:
                pattern = dict(row)
                # Parse JSON fields for export
                pattern['successful_approach'] = json.loads(pattern['successful_approach'])
                pattern['executive_roles'] = json.loads(pattern['executive_roles'])
                pattern['focus_areas'] = json.loads(pattern['focus_areas'])
                patterns.append(pattern)

            return patterns

        except Exception as e:
            raise Exception(f"Pattern export failed: {str(e)}")
        finally:
            conn.close()