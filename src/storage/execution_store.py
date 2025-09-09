"""
Execution Store - Simple tracking of execution history
Tracks what actions have been executed and their results.
"""
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


class ExecutionStore:
    """Simple execution tracking and history storage"""
    
    def __init__(self, db_path: str = "data/call_center.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize execution tracking tables"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                execution_id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                status TEXT NOT NULL,
                mode TEXT DEFAULT 'auto',
                artifacts_created INTEGER DEFAULT 0,
                errors_count INTEGER DEFAULT 0,
                results TEXT,  -- JSON of execution results
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES action_plans (plan_id)
            )
        ''')
        
        # Individual action executions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_source TEXT NOT NULL, -- borrower/advisor/supervisor/leadership
                tool_used TEXT,
                status TEXT NOT NULL,
                artifact_path TEXT,
                error_message TEXT,
                llm_reasoning TEXT,
                executed_at TEXT NOT NULL,
                FOREIGN KEY (execution_id) REFERENCES executions (execution_id)
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_plan_id ON executions (plan_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_executed_at ON executions (executed_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_executions_execution_id ON action_executions (execution_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_action_executions_action_source ON action_executions (action_source)')
        
        conn.commit()
        conn.close()
    
    def store_execution(self, execution_result: Dict[str, Any]) -> str:
        """Store execution result and return execution_id"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            execution_id = execution_result['execution_id']
            
            # Count artifacts and errors
            all_results = []
            for action_type, results in execution_result.get('results', {}).items():
                all_results.extend(results)
            
            artifacts_count = len(execution_result.get('artifacts_created', []))
            errors_count = len(execution_result.get('errors', []))
            
            # Store main execution record
            cursor.execute('''
                INSERT OR REPLACE INTO executions 
                (execution_id, plan_id, executed_at, status, artifacts_created, 
                 errors_count, results)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                execution_id,
                execution_result['plan_id'],
                execution_result['executed_at'],
                execution_result['status'],
                artifacts_count,
                errors_count,
                json.dumps(execution_result)
            ))
            
            # Store individual action executions
            for action_type, results in execution_result.get('results', {}).items():
                for result in results:
                    cursor.execute('''
                        INSERT INTO action_executions
                        (execution_id, action_type, action_source, tool_used, status,
                         artifact_path, error_message, llm_reasoning, executed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        execution_id,
                        result.get('action', result.get('action_source', 'unknown')),
                        action_type.replace('_actions', ''),  # borrower/advisor/etc
                        result.get('tool_used', 'unknown'),
                        result.get('status', 'unknown'),
                        result.get('file_path') or result.get('artifact_path'),
                        result.get('error'),
                        result.get('reasoning'),
                        execution_result['executed_at']
                    ))
            
            conn.commit()
            return execution_id
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Failed to store execution: {str(e)}")
        finally:
            conn.close()
    
    def get_execution_by_id(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details by ID"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT execution_id, plan_id, executed_at, status, mode,
                       artifacts_created, errors_count, results, created_at
                FROM executions WHERE execution_id = ?
            ''', (execution_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            execution = {
                'execution_id': row[0],
                'plan_id': row[1],
                'executed_at': row[2],
                'status': row[3],
                'mode': row[4],
                'artifacts_created': row[5],
                'errors_count': row[6],
                'results': json.loads(row[7]) if row[7] else {},
                'created_at': row[8]
            }
            
            # Get individual action details
            cursor.execute('''
                SELECT action_type, action_source, tool_used, status,
                       artifact_path, error_message, llm_reasoning, executed_at
                FROM action_executions WHERE execution_id = ?
                ORDER BY executed_at
            ''', (execution_id,))
            
            actions = []
            for action_row in cursor.fetchall():
                actions.append({
                    'action_type': action_row[0],
                    'action_source': action_row[1],
                    'tool_used': action_row[2],
                    'status': action_row[3],
                    'artifact_path': action_row[4],
                    'error_message': action_row[5],
                    'llm_reasoning': action_row[6],
                    'executed_at': action_row[7]
                })
            
            execution['action_details'] = actions
            return execution
            
        finally:
            conn.close()
    
    def get_executions_by_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all executions for a specific plan"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT execution_id, executed_at, status, artifacts_created, errors_count
                FROM executions 
                WHERE plan_id = ?
                ORDER BY executed_at DESC
            ''', (plan_id,))
            
            executions = []
            for row in cursor.fetchall():
                executions.append({
                    'execution_id': row[0],
                    'executed_at': row[1],
                    'status': row[2],
                    'artifacts_created': row[3],
                    'errors_count': row[4]
                })
            
            return executions
            
        finally:
            conn.close()
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent executions across all plans"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT execution_id, plan_id, executed_at, status, 
                       artifacts_created, errors_count
                FROM executions 
                ORDER BY executed_at DESC 
                LIMIT ?
            ''', (limit,))
            
            executions = []
            for row in cursor.fetchall():
                executions.append({
                    'execution_id': row[0],
                    'plan_id': row[1], 
                    'executed_at': row[2],
                    'status': row[3],
                    'artifacts_created': row[4],
                    'errors_count': row[5]
                })
            
            return executions
            
        finally:
            conn.close()
    
    def get_execution_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get execution statistics for the last N days"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get date cutoff
            from datetime import timedelta
            cutoff_date = (datetime.now() - 
                          timedelta(days=days)).isoformat()
            
            # Total executions
            cursor.execute('''
                SELECT COUNT(*) FROM executions 
                WHERE executed_at >= ?
            ''', (cutoff_date,))
            total_executions = cursor.fetchone()[0]
            
            # Success/failure breakdown
            cursor.execute('''
                SELECT status, COUNT(*) FROM executions 
                WHERE executed_at >= ?
                GROUP BY status
            ''', (cutoff_date,))
            status_breakdown = dict(cursor.fetchall())
            
            # Actions by source
            cursor.execute('''
                SELECT action_source, COUNT(*) FROM action_executions ae
                JOIN executions e ON ae.execution_id = e.execution_id
                WHERE e.executed_at >= ?
                GROUP BY action_source
            ''', (cutoff_date,))
            actions_by_source = dict(cursor.fetchall())
            
            # Tools usage
            cursor.execute('''
                SELECT tool_used, COUNT(*) FROM action_executions ae
                JOIN executions e ON ae.execution_id = e.execution_id
                WHERE e.executed_at >= ? AND tool_used IS NOT NULL
                GROUP BY tool_used
            ''', (cutoff_date,))
            tools_usage = dict(cursor.fetchall())
            
            # Total artifacts created
            cursor.execute('''
                SELECT SUM(artifacts_created) FROM executions
                WHERE executed_at >= ?
            ''', (cutoff_date,))
            total_artifacts = cursor.fetchone()[0] or 0
            
            return {
                'period_days': days,
                'total_executions': total_executions,
                'status_breakdown': status_breakdown,
                'actions_by_source': actions_by_source,
                'tools_usage': tools_usage,
                'total_artifacts_created': total_artifacts,
                'success_rate': round(
                    status_breakdown.get('success', 0) / max(total_executions, 1) * 100, 2
                )
            }
            
        finally:
            conn.close()
    
    def search_executions(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search executions with various filters"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT DISTINCT e.execution_id, e.plan_id, e.executed_at, 
                       e.status, e.artifacts_created, e.errors_count
                FROM executions e
            '''
            
            conditions = []
            params = []
            
            if search_params.get('plan_id'):
                conditions.append('e.plan_id = ?')
                params.append(search_params['plan_id'])
            
            if search_params.get('status'):
                conditions.append('e.status = ?')
                params.append(search_params['status'])
            
            if search_params.get('date_from'):
                conditions.append('e.executed_at >= ?')
                params.append(search_params['date_from'])
            
            if search_params.get('date_to'):
                conditions.append('e.executed_at <= ?')
                params.append(search_params['date_to'])
            
            if search_params.get('action_source'):
                query += ' JOIN action_executions ae ON e.execution_id = ae.execution_id'
                conditions.append('ae.action_source = ?')
                params.append(search_params['action_source'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            query += ' ORDER BY e.executed_at DESC'
            
            if search_params.get('limit'):
                query += ' LIMIT ?'
                params.append(search_params['limit'])
            
            cursor.execute(query, params)
            
            executions = []
            for row in cursor.fetchall():
                executions.append({
                    'execution_id': row[0],
                    'plan_id': row[1],
                    'executed_at': row[2],
                    'status': row[3],
                    'artifacts_created': row[4],
                    'errors_count': row[5]
                })
            
            return executions
            
        finally:
            conn.close()
    
    def delete_execution(self, execution_id: str) -> bool:
        """Delete an execution and its action details"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete action executions first (foreign key)
            cursor.execute('DELETE FROM action_executions WHERE execution_id = ?', (execution_id,))
            
            # Delete main execution
            cursor.execute('DELETE FROM executions WHERE execution_id = ?', (execution_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
            
        except Exception:
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def delete_all_executions(self) -> int:
        """Delete all execution records (for testing/demo reset)"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM action_executions')
            cursor.execute('DELETE FROM executions')
            
            deleted = cursor.rowcount
            conn.commit()
            return deleted
            
        except Exception:
            conn.rollback()
            return 0
        finally:
            conn.close()