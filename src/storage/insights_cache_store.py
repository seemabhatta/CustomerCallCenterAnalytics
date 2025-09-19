"""SQLite storage layer for insights aggregation caching.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: No hardcoded routing logic - all decisions by LLM agents
- Performance: Cache expensive aggregations for rapid retrieval
"""
import sqlite3
import json
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class InsightsCacheStore:
    """SQLite-based storage for caching expensive aggregations.

    Implements intelligent caching to avoid re-computing expensive
    aggregations that LLM agents have already processed.
    """

    def __init__(self, db_path: str):
        """Initialize cache store with database path.

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
                WHERE type='table' AND name='aggregation_cache'
            ''')

            if not cursor.fetchone():
                # Read and execute schema from file if not exists
                with open('data/insights_schema.sql', 'r') as f:
                    schema_sql = f.read()
                    cursor.executescript(schema_sql)

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Cache database initialization failed: {str(e)}")
        finally:
            conn.close()

    def _generate_cache_key(self, query: str, filters: Dict[str, Any] = None,
                           timeframe: Dict[str, Any] = None) -> str:
        """Generate cache key from query parameters.

        Args:
            query: Original query string
            filters: Data filters applied
            timeframe: Time range filters

        Returns:
            Cache key hash
        """
        cache_input = {
            'query': query.strip().lower(),
            'filters': filters or {},
            'timeframe': timeframe or {}
        }

        cache_string = json.dumps(cache_input, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def _generate_query_hash(self, query: str) -> str:
        """Generate hash of just the query for similarity matching.

        Args:
            query: Query string

        Returns:
            Query hash
        """
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()

    def store_aggregation(self, query: str, aggregated_data: Dict[str, Any],
                         data_sources: List[str], record_count: int,
                         computation_time_ms: int, filters: Dict[str, Any] = None,
                         timeframe: Dict[str, Any] = None,
                         ttl_hours: int = 24) -> str:
        """Store aggregated data in cache.

        Args:
            query: Original query
            aggregated_data: Computed aggregation results
            data_sources: Which data stores were used
            record_count: Number of source records aggregated
            computation_time_ms: Time taken to compute
            filters: Data filters applied
            timeframe: Time range filters
            ttl_hours: Time to live in hours

        Returns:
            Cache key

        Raises:
            Exception: If storage fails (NO FALLBACK)
        """
        if not query or not aggregated_data:
            raise ValueError("query and aggregated_data are required")

        cache_key = self._generate_cache_key(query, filters, timeframe)
        query_hash = self._generate_query_hash(query)
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # First, clean up expired entries
            self._cleanup_expired_cache(cursor)

            # Store new cache entry
            cursor.execute('''
                INSERT OR REPLACE INTO aggregation_cache
                (cache_key, query_hash, aggregated_data, data_sources,
                 record_count, computation_time_ms, created_at, expires_at,
                 hit_count, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            ''', (cache_key, query_hash, json.dumps(aggregated_data),
                  json.dumps(data_sources), record_count, computation_time_ms,
                  now, expires_at, now))

            conn.commit()
            return cache_key

        except Exception as e:
            conn.rollback()
            raise Exception(f"Cache storage failed: {str(e)}")
        finally:
            conn.close()

    def get_cached_aggregation(self, query: str, filters: Dict[str, Any] = None,
                              timeframe: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Get cached aggregation if available and not expired.

        Args:
            query: Original query
            filters: Data filters applied
            timeframe: Time range filters

        Returns:
            Cached data or None if not found/expired
        """
        cache_key = self._generate_cache_key(query, filters, timeframe)
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT * FROM aggregation_cache
                WHERE cache_key = ? AND expires_at > ?
            ''', (cache_key, now))

            row = cursor.fetchone()
            if not row:
                return None

            # Update last accessed time and hit count
            cursor.execute('''
                UPDATE aggregation_cache
                SET last_accessed = ?, hit_count = hit_count + 1
                WHERE cache_key = ?
            ''', (now, cache_key))

            conn.commit()

            # Parse and return cached data
            cached_data = dict(row)
            cached_data['aggregated_data'] = json.loads(cached_data['aggregated_data'])
            cached_data['data_sources'] = json.loads(cached_data['data_sources'])

            return cached_data

        except Exception as e:
            raise Exception(f"Cache retrieval failed: {str(e)}")
        finally:
            conn.close()

    def get_similar_cached_queries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar cached queries for learning patterns.

        Args:
            query: Query to find similar entries for
            limit: Maximum number of similar queries

        Returns:
            List of similar cached entries
        """
        query_hash = self._generate_query_hash(query)
        now = datetime.now()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # For now, simple approach - look for entries with similar query hash
            # In future, could use embedding-based similarity
            cursor.execute('''
                SELECT cache_key, query_hash, data_sources, record_count,
                       computation_time_ms, hit_count, created_at
                FROM aggregation_cache
                WHERE expires_at > ? AND query_hash = ?
                ORDER BY hit_count DESC, created_at DESC
                LIMIT ?
            ''', (now, query_hash, limit))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        except Exception as e:
            raise Exception(f"Similar queries retrieval failed: {str(e)}")
        finally:
            conn.close()

    def invalidate_cache_by_data_source(self, data_source: str):
        """Invalidate cache entries that used specific data source.

        Args:
            data_source: Data source that was updated
        """
        if not data_source:
            raise ValueError("data_source cannot be empty")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Mark as expired entries that used this data source
            cursor.execute('''
                UPDATE aggregation_cache
                SET expires_at = CURRENT_TIMESTAMP
                WHERE data_sources LIKE ?
            ''', (f'%"{data_source}"%',))

            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Cache invalidation failed: {str(e)}")
        finally:
            conn.close()

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Total cache entries
            cursor.execute('SELECT COUNT(*) as total FROM aggregation_cache')
            total = cursor.fetchone()['total']

            # Active (non-expired) entries
            cursor.execute('''
                SELECT COUNT(*) as active FROM aggregation_cache
                WHERE expires_at > CURRENT_TIMESTAMP
            ''')
            active = cursor.fetchone()['active']

            # Total hits
            cursor.execute('SELECT SUM(hit_count) as total_hits FROM aggregation_cache')
            total_hits = cursor.fetchone()['total_hits'] or 0

            # Average computation time
            cursor.execute('''
                SELECT AVG(computation_time_ms) as avg_time FROM aggregation_cache
                WHERE expires_at > CURRENT_TIMESTAMP
            ''')
            avg_computation_time = cursor.fetchone()['avg_time'] or 0

            # Most hit queries
            cursor.execute('''
                SELECT query_hash, hit_count, computation_time_ms
                FROM aggregation_cache
                WHERE expires_at > CURRENT_TIMESTAMP
                ORDER BY hit_count DESC
                LIMIT 5
            ''')
            top_queries = [dict(row) for row in cursor.fetchall()]

            return {
                'total_entries': total,
                'active_entries': active,
                'expired_entries': total - active,
                'total_hits': total_hits,
                'average_computation_time_ms': round(avg_computation_time, 2),
                'hit_rate': round(total_hits / max(total, 1), 2),
                'top_queries': top_queries
            }

        except Exception as e:
            raise Exception(f"Cache statistics retrieval failed: {str(e)}")
        finally:
            conn.close()

    def _cleanup_expired_cache(self, cursor):
        """Clean up expired cache entries.

        Args:
            cursor: SQLite cursor
        """
        try:
            cursor.execute('''
                DELETE FROM aggregation_cache
                WHERE expires_at <= CURRENT_TIMESTAMP
            ''')
        except Exception as e:
            # Log error but don't fail the main operation
            print(f"Cache cleanup warning: {str(e)}")

    def clear_cache(self):
        """Clear all cache entries (for testing/maintenance).

        Raises:
            Exception: If clearing fails (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM aggregation_cache')
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise Exception(f"Cache clearing failed: {str(e)}")
        finally:
            conn.close()