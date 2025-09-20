"""
Workflow Execution Store - Storage for workflow execution records and payloads.
Tracks execution history, payloads, and results for audit and analysis.
NO FALLBACK LOGIC - fails fast on database errors.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class WorkflowExecutionStore:
    """Storage system for workflow execution records.
    
    This store maintains a complete audit trail of workflow executions including:
    - Execution metadata (when, who, what)
    - Generated payloads for each executor type
    - Execution status and results
    - Performance metrics and timing
    
    NO FALLBACK LOGIC - all database errors are raised immediately.
    """
    
    def __init__(self, db_path: str = "data/call_center.db"):
        """Initialize execution store with database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._persistent_conn = None
        
        # For in-memory databases, maintain persistent connection
        if db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(db_path)
        
        self._init_db()
    
    def _init_db(self):
        """Initialize workflow execution tables.
        
        Creates tables for storing execution records, payloads, and metadata.
        
        Raises:
            Exception: Database initialization failure (NO FALLBACK)
        """
        try:
            if self._persistent_conn:
                conn = self._persistent_conn
                cursor = conn.cursor()
            else:
                conn = self._get_connection()
                cursor = conn.cursor()
            
            # Main workflow executions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    step_number INTEGER,  -- For step-by-step execution tracking
                    executor_type TEXT NOT NULL,
                    execution_status TEXT NOT NULL,
                    execution_payload TEXT NOT NULL,  -- JSON
                    executed_at TEXT NOT NULL,
                    executed_by TEXT NOT NULL,
                    execution_duration_ms INTEGER,
                    mock_execution BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    metadata TEXT,  -- JSON for additional execution metadata
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id)
                )
            ''')
            
            # Execution performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
                )
            ''')
            
            # Execution audit trail table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS execution_audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_description TEXT NOT NULL,
                    event_timestamp TEXT NOT NULL,
                    event_data TEXT,  -- JSON
                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_executions_workflow_id ON workflow_executions (workflow_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_executions_executor_type ON workflow_executions (executor_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_executions_executed_at ON workflow_executions (executed_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions (execution_status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_metrics_execution_id ON execution_metrics (execution_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_execution_audit_execution_id ON execution_audit_trail (execution_id)')
            
            conn.commit()
            
        except Exception as e:
            raise Exception(f"Failed to initialize workflow execution database: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    def _get_connection(self):
        """Get database connection, using persistent connection if available."""
        if self._persistent_conn:
            return self._persistent_conn
        else:
            return sqlite3.connect(self.db_path)
    
    async def create(self, execution_data: Dict[str, Any]) -> str:
        """Create new execution record.
        
        Args:
            execution_data: Dictionary containing:
                - workflow_id: ID of executed workflow
                - executor_type: Type of executor used
                - execution_payload: Generated payload data
                - execution_status: Status (executed, failed, etc.)
                - executed_by: Who executed the workflow
                - mock_execution: Boolean indicating mock vs real execution
                - metadata: Optional additional metadata
        
        Returns:
            Generated execution ID
            
        Raises:
            ValueError: Invalid execution data (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        # Validate required fields
        required_fields = ['workflow_id', 'executor_type', 'execution_payload', 'execution_status']
        for field in required_fields:
            if field not in execution_data:
                raise ValueError(f"Execution data missing required field: {field}")
        
        if not execution_data['workflow_id']:
            raise ValueError("workflow_id cannot be empty")
        
        if not execution_data['executor_type']:
            raise ValueError("executor_type cannot be empty")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Serialize payload and metadata
            payload_json = json.dumps(execution_data['execution_payload'])
            metadata_json = json.dumps(execution_data.get('metadata', {}))
            
            # Insert execution record
            cursor.execute('''
                INSERT INTO workflow_executions (
                    id, workflow_id, step_number, executor_type, execution_status,
                    execution_payload, executed_at, executed_by,
                    execution_duration_ms, mock_execution, error_message, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_id,
                execution_data['workflow_id'],
                execution_data.get('step_number'),  # Optional for backward compatibility
                execution_data['executor_type'],
                execution_data['execution_status'],
                payload_json,
                execution_data.get('executed_at', datetime.now(timezone.utc).isoformat()),
                execution_data.get('executed_by', 'system'),
                execution_data.get('execution_duration_ms'),
                execution_data.get('mock_execution', True),
                execution_data.get('error_message'),
                metadata_json
            ))
            
            # Add audit trail entry
            self._add_audit_entry(
                cursor, 
                execution_id, 
                'execution_created',
                f"Workflow execution record created for {execution_data['workflow_id']}",
                execution_data
            )
            
            # Add performance metrics if provided
            if 'metrics' in execution_data:
                for metric in execution_data['metrics']:
                    self._add_metric(cursor, execution_id, metric)
            
            conn.commit()
            return execution_id
            
        except Exception as e:
            raise Exception(f"Failed to create execution record: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    async def get_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution record by ID.
        
        Args:
            execution_id: Execution record ID
            
        Returns:
            Execution record dictionary or None if not found
            
        Raises:
            ValueError: Invalid execution_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("execution_id must be a non-empty string")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions 
                WHERE id = ?
            ''', (execution_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return self._row_to_dict(row)
            
        except Exception as e:
            raise Exception(f"Failed to retrieve execution record: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    async def get_by_workflow(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all execution records for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of execution records
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions
                WHERE workflow_id = ?
                ORDER BY executed_at DESC
            ''', (workflow_id,))
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve workflow executions: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()

    async def get_by_workflow_and_step(self, workflow_id: str, step_number: int) -> Optional[Dict[str, Any]]:
        """Get execution record for a specific workflow step.

        Args:
            workflow_id: Workflow ID
            step_number: Step number to query

        Returns:
            Execution record if found, None if not executed

        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")

        if not isinstance(step_number, int) or step_number <= 0:
            raise ValueError("step_number must be a positive integer")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions
                WHERE workflow_id = ? AND step_number = ?
                ORDER BY executed_at DESC
                LIMIT 1
            ''', (workflow_id, step_number))

            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

        except Exception as e:
            raise Exception(f"Failed to retrieve step execution: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()

    async def get_by_executor_type(self, executor_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution records by executor type.
        
        Args:
            executor_type: Type of executor (email, crm, disclosure, etc.)
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
            
        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not executor_type or not isinstance(executor_type, str):
            raise ValueError("executor_type must be a non-empty string")
        
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions 
                WHERE executor_type = ?
                ORDER BY executed_at DESC
                LIMIT ?
            ''', (executor_type, limit))
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve executions by type: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    async def get_recent_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent execution records.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of recent execution records
            
        Raises:
            ValueError: Invalid limit (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions 
                ORDER BY executed_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve recent executions: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()

    async def get_all_executions(self,
                                status_filter: Optional[str] = None,
                                executor_type_filter: Optional[str] = None,
                                limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all execution records with optional filtering.

        Args:
            status_filter: Optional status filter
            executor_type_filter: Optional executor type filter
            limit: Maximum number of records to return

        Returns:
            List of execution records matching filters

        Raises:
            ValueError: Invalid filter parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build query with filters
            query = '''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions
                WHERE 1=1
            '''
            params = []

            if status_filter:
                query += ' AND execution_status = ?'
                params.append(status_filter)

            if executor_type_filter:
                query += ' AND executor_type = ?'
                params.append(executor_type_filter)

            query += ' ORDER BY created_at DESC'

            if limit:
                query += ' LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            raise Exception(f"Failed to retrieve executions: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()

    async def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics and metrics.
        
        Returns:
            Dictionary containing execution statistics
            
        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total executions
            cursor.execute('SELECT COUNT(*) FROM workflow_executions')
            total_executions = cursor.fetchone()[0]
            
            # Executions by status
            cursor.execute('''
                SELECT execution_status, COUNT(*) 
                FROM workflow_executions 
                GROUP BY execution_status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Executions by executor type
            cursor.execute('''
                SELECT executor_type, COUNT(*) 
                FROM workflow_executions 
                GROUP BY executor_type
            ''')
            executor_counts = dict(cursor.fetchall())
            
            # Average execution duration
            cursor.execute('''
                SELECT AVG(execution_duration_ms) 
                FROM workflow_executions 
                WHERE execution_duration_ms IS NOT NULL
            ''')
            avg_duration_result = cursor.fetchone()[0]
            avg_duration = avg_duration_result if avg_duration_result else 0
            
            # Recent execution trends (last 7 days)
            cursor.execute('''
                SELECT DATE(executed_at) as exec_date, COUNT(*) 
                FROM workflow_executions 
                WHERE executed_at >= datetime('now', '-7 days')
                GROUP BY DATE(executed_at)
                ORDER BY exec_date
            ''')
            daily_counts = dict(cursor.fetchall())
            
            return {
                'total_executions': total_executions,
                'executions_by_status': status_counts,
                'executions_by_executor_type': executor_counts,
                'average_execution_duration_ms': round(avg_duration, 2),
                'daily_execution_counts_last_7_days': daily_counts,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate execution statistics: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    async def add_execution_metric(self, execution_id: str, metric_name: str, 
                                 metric_value: float, metric_unit: str) -> bool:
        """Add performance metric for execution.
        
        Args:
            execution_id: Execution record ID
            metric_name: Name of the metric
            metric_value: Numeric value of the metric
            metric_unit: Unit of measurement
            
        Returns:
            True if successful
            
        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not all([execution_id, metric_name, metric_unit]):
            raise ValueError("All metric parameters are required")
        
        if not isinstance(metric_value, (int, float)):
            raise ValueError("metric_value must be numeric")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO execution_metrics (
                    execution_id, metric_name, metric_value, metric_unit, recorded_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                execution_id,
                metric_name,
                float(metric_value),
                metric_unit,
                datetime.now(timezone.utc).isoformat()
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            raise Exception(f"Failed to add execution metric: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    async def get_execution_audit_trail(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get audit trail for execution.
        
        Args:
            execution_id: Execution record ID
            
        Returns:
            List of audit trail entries
            
        Raises:
            ValueError: Invalid execution_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("execution_id must be a non-empty string")
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, execution_id, event_type, event_description, 
                       event_timestamp, event_data
                FROM execution_audit_trail 
                WHERE execution_id = ?
                ORDER BY event_timestamp ASC
            ''', (execution_id,))
            
            rows = cursor.fetchall()
            audit_entries = []
            
            for row in rows:
                entry = {
                    'id': row[0],
                    'execution_id': row[1],
                    'event_type': row[2],
                    'event_description': row[3],
                    'event_timestamp': row[4],
                    'event_data': json.loads(row[5]) if row[5] else None
                }
                audit_entries.append(entry)
            
            return audit_entries
            
        except Exception as e:
            raise Exception(f"Failed to retrieve audit trail: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary.
        
        Args:
            row: Database row tuple
            
        Returns:
            Dictionary representation of execution record
            
        Raises:
            Exception: JSON parsing failure (NO FALLBACK)
        """
        try:
            return {
                'id': row[0],
                'workflow_id': row[1],
                'step_number': row[2],  # New field for step tracking
                'executor_type': row[3],
                'execution_status': row[4],
                'execution_payload': json.loads(row[5]),
                'executed_at': row[6],
                'executed_by': row[7],
                'execution_duration_ms': row[8],
                'mock_execution': bool(row[9]),
                'error_message': row[10],
                'metadata': json.loads(row[11]) if row[11] else {},
                'created_at': row[12]
            }
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse execution record JSON: {e}")
    
    def _add_audit_entry(self, cursor, execution_id: str, event_type: str, 
                        event_description: str, event_data: Dict[str, Any] = None):
        """Add entry to audit trail.
        
        Args:
            cursor: Database cursor
            execution_id: Execution record ID
            event_type: Type of event
            event_description: Description of event
            event_data: Optional event data
        """
        cursor.execute('''
            INSERT INTO execution_audit_trail (
                execution_id, event_type, event_description, 
                event_timestamp, event_data
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            execution_id,
            event_type,
            event_description,
            datetime.now(timezone.utc).isoformat(),
            json.dumps(event_data) if event_data else None
        ))
    
    def _add_metric(self, cursor, execution_id: str, metric: Dict[str, Any]):
        """Add performance metric.
        
        Args:
            cursor: Database cursor
            execution_id: Execution record ID
            metric: Metric data dictionary
        """
        cursor.execute('''
            INSERT INTO execution_metrics (
                execution_id, metric_name, metric_value, metric_unit, recorded_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            execution_id,
            metric['name'],
            metric['value'],
            metric['unit'],
            datetime.now(timezone.utc).isoformat()
        ))
    
    async def get_all(self, limit: Optional[int] = None, status: Optional[str] = None,
                     executor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all execution records with optional filters.

        Args:
            limit: Optional limit on number of records to return
            status: Optional filter by execution status
            executor_type: Optional filter by executor type

        Returns:
            List of execution records ordered by execution time (newest first)

        Raises:
            ValueError: Invalid filter parameters (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValueError("limit must be a positive integer")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build query with filters
            query = '''
                SELECT id, workflow_id, step_number, executor_type, execution_status,
                       execution_payload, executed_at, executed_by,
                       execution_duration_ms, mock_execution, error_message,
                       metadata, created_at
                FROM workflow_executions
            '''

            conditions = []
            params = []

            if status:
                conditions.append('execution_status = ?')
                params.append(status)

            if executor_type:
                conditions.append('executor_type = ?')
                params.append(executor_type)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            query += ' ORDER BY executed_at DESC'

            if limit:
                query += ' LIMIT ?'
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            raise Exception(f"Failed to retrieve all executions: {e}")
        finally:
            if not self._persistent_conn:
                conn.close()

    async def delete(self, execution_id: str) -> bool:
        """Delete execution record by ID.

        Args:
            execution_id: Execution record ID to delete

        Returns:
            True if execution was deleted, False if not found

        Raises:
            ValueError: Invalid execution_id (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not execution_id or not isinstance(execution_id, str):
            raise ValueError("execution_id must be a non-empty string")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete execution record (cascading deletes handle related tables)
            cursor.execute('DELETE FROM workflow_executions WHERE id = ?', (execution_id,))
            deleted_count = cursor.rowcount

            conn.commit()
            return deleted_count > 0

        except Exception as e:
            raise Exception(f"Failed to delete execution record: {e}")
        finally:
            if not self._persistent_conn:
                conn.close()

    async def delete_all(self, status: Optional[str] = None,
                        executor_type: Optional[str] = None) -> int:
        """Delete all execution records with optional filters.

        Args:
            status: Optional filter - only delete executions with this status
            executor_type: Optional filter - only delete executions of this type

        Returns:
            Number of execution records deleted

        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Build delete query with filters
            query = 'DELETE FROM workflow_executions'
            conditions = []
            params = []

            if status:
                conditions.append('execution_status = ?')
                params.append(status)

            if executor_type:
                conditions.append('executor_type = ?')
                params.append(executor_type)

            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)

            cursor.execute(query, params)
            deleted_count = cursor.rowcount

            conn.commit()
            return deleted_count

        except Exception as e:
            raise Exception(f"Failed to delete execution records: {e}")
        finally:
            if not self._persistent_conn:
                conn.close()

    async def cleanup_old_executions(self, days_to_keep: int = 90) -> int:
        """Clean up old execution records.

        Args:
            days_to_keep: Number of days of records to retain

        Returns:
            Number of records deleted

        Raises:
            ValueError: Invalid days_to_keep (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        if not isinstance(days_to_keep, int) or days_to_keep <= 0:
            raise ValueError("days_to_keep must be a positive integer")

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Delete old execution records (cascading deletes will handle related tables)
            cursor.execute('''
                DELETE FROM workflow_executions
                WHERE executed_at < datetime('now', '-{} days')
            '''.format(days_to_keep))

            deleted_count = cursor.rowcount
            conn.commit()

            return deleted_count

        except Exception as e:
            raise Exception(f"Failed to cleanup old executions: {e}")
        finally:
            # Only close if not using persistent connection
            if not self._persistent_conn:
                conn.close()