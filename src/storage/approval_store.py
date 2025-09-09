"""
Approval Store - Database schema and operations for action approvals.
Supports the Decision Agent approval workflow with individual action tracking.
"""

import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.transcript import Transcript


class ApprovalStore:
    """
    SQLite-based storage for action approvals.
    Tracks individual action approval status, approver information, and audit trail.
    """
    
    def __init__(self, db_path: str):
        """Initialize the approval store with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema for action approvals."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create action_approvals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_approvals (
                id TEXT PRIMARY KEY,
                plan_id TEXT NOT NULL,
                action_id TEXT NOT NULL,
                transcript_id TEXT,
                analysis_id TEXT,
                
                -- Action details
                action_text TEXT NOT NULL,
                action_description TEXT,
                action_layer TEXT,  -- borrower, advisor, supervisor, leadership
                action_type TEXT,   -- customer_communication, financial_transaction, etc.
                
                -- Risk assessment
                risk_score REAL,
                risk_level TEXT,    -- low, medium, high
                financial_impact BOOLEAN DEFAULT FALSE,
                compliance_impact BOOLEAN DEFAULT FALSE,
                customer_facing BOOLEAN DEFAULT FALSE,
                
                -- Approval workflow
                needs_approval BOOLEAN DEFAULT FALSE,
                approval_status TEXT DEFAULT 'pending',  -- pending, approved, rejected, auto_approved
                approval_route TEXT,  -- auto_approved, advisor_approval, supervisor_approval
                approval_reason TEXT,
                
                -- Approver information
                approved_by TEXT,
                approved_at TIMESTAMP,
                rejection_reason TEXT,
                
                -- Execution tracking (for feedback loop)
                execution_id TEXT,
                executed_at TIMESTAMP,
                execution_status TEXT,  -- success, failed, partial, skipped
                execution_result TEXT,  -- JSON with execution details
                assigned_actor TEXT,    -- advisor, supervisor, leadership, customer
                actor_assignment_reason TEXT,
                execution_artifacts TEXT, -- JSON array of created artifacts
                execution_errors TEXT,   -- JSON array of errors encountered
                
                -- Audit trail
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                decision_agent_version TEXT,
                
                -- Foreign key relationships
                FOREIGN KEY (plan_id) REFERENCES action_plans (id),
                FOREIGN KEY (transcript_id) REFERENCES transcripts (id),
                FOREIGN KEY (analysis_id) REFERENCES analysis (id)
            )
        ''')
        
        # Create approval_queue_metrics table for dashboard
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_queue_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date DATE DEFAULT CURRENT_DATE,
                
                -- Queue counts
                pending_supervisor_count INTEGER DEFAULT 0,
                pending_advisor_count INTEGER DEFAULT 0,
                auto_approved_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                
                -- Performance metrics
                avg_approval_time_hours REAL,
                approval_rate REAL,
                
                -- Risk distribution
                high_risk_actions INTEGER DEFAULT 0,
                medium_risk_actions INTEGER DEFAULT 0,
                low_risk_actions INTEGER DEFAULT 0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_approval_status 
            ON action_approvals (approval_status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_approval_route 
            ON action_approvals (approval_route)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_needs_approval 
            ON action_approvals (needs_approval, approval_status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_plan_id 
            ON action_approvals (plan_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action_id 
            ON action_approvals (action_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_risk_level 
            ON action_approvals (risk_level)
        ''')
        
        conn.commit()
        conn.close()
    
    def store_action_approval(self, action_approval: Dict[str, Any]) -> str:
        """Store an action approval record.
        
        Args:
            action_approval: Action approval data dictionary
            
        Returns:
            Approval ID of the stored record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            approval_id = action_approval.get('id', f"APPR_{action_approval.get('action_id', 'UNK')}")
            
            cursor.execute('''
                INSERT OR REPLACE INTO action_approvals 
                (id, plan_id, action_id, transcript_id, analysis_id, action_text, action_description,
                 action_layer, action_type, risk_score, risk_level, financial_impact, compliance_impact,
                 customer_facing, needs_approval, approval_status, approval_route, approval_reason,
                 decision_agent_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                approval_id,
                action_approval.get('plan_id'),
                action_approval.get('action_id'),
                action_approval.get('transcript_id'),
                action_approval.get('analysis_id'),
                action_approval.get('action_text', ''),
                # NO FALLBACK: Serialize lists/dicts to JSON strings for SQLite
                json.dumps(action_approval.get('action_description', '')) if isinstance(action_approval.get('action_description', ''), (list, dict)) else action_approval.get('action_description', ''),
                action_approval.get('action_layer'),
                action_approval.get('action_type'),
                action_approval.get('risk_score', 0),
                action_approval.get('risk_level'),
                action_approval.get('financial_impact', False),
                action_approval.get('compliance_impact', False),
                action_approval.get('customer_facing', False),
                action_approval.get('needs_approval', False),
                action_approval.get('approval_status', 'pending'),
                json.dumps(action_approval.get('approval_route')) if isinstance(action_approval.get('approval_route'), (list, dict)) else action_approval.get('approval_route'),
                action_approval.get('approval_reason', ''),
                action_approval.get('decision_agent_version', 'v1.0')
            ))
            
            conn.commit()
            return approval_id
            
        finally:
            conn.close()
    
    def get_approval_queue(self, route: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get actions pending approval.
        
        Args:
            route: Optional filter by approval route (advisor_approval, supervisor_approval)
            
        Returns:
            List of actions pending approval
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if route:
                cursor.execute('''
                    SELECT * FROM action_approvals 
                    WHERE approval_status = 'pending' AND approval_route = ?
                    ORDER BY created_at ASC
                ''', (route,))
            else:
                cursor.execute('''
                    SELECT * FROM action_approvals 
                    WHERE approval_status = 'pending'
                    ORDER BY approval_route DESC, created_at ASC
                ''')
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        finally:
            conn.close()
    
    def approve_action(self, action_id: str, approved_by: str, notes: str = '') -> bool:
        """Approve an action.
        
        Args:
            action_id: Action ID to approve
            approved_by: Approver identifier
            notes: Optional approval notes
            
        Returns:
            True if approval was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE action_approvals 
                SET approval_status = 'approved',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    approval_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE action_id = ? AND approval_status = 'pending'
            ''', (approved_by, notes or 'Approved by ' + approved_by, action_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
        finally:
            conn.close()
    
    def reject_action(self, action_id: str, rejected_by: str, reason: str) -> bool:
        """Reject an action.
        
        Args:
            action_id: Action ID to reject
            rejected_by: Rejector identifier
            reason: Rejection reason
            
        Returns:
            True if rejection was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE action_approvals 
                SET approval_status = 'rejected',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    rejection_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE action_id = ? AND approval_status = 'pending'
            ''', (rejected_by, reason, action_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
        finally:
            conn.close()
    
    def bulk_approve(self, action_ids: List[str], approved_by: str, notes: str = '') -> int:
        """Bulk approve multiple actions.
        
        Args:
            action_ids: List of action IDs to approve
            approved_by: Approver identifier
            notes: Optional approval notes
            
        Returns:
            Number of actions successfully approved
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?' for _ in action_ids])
            cursor.execute(f'''
                UPDATE action_approvals 
                SET approval_status = 'approved',
                    approved_by = ?,
                    approved_at = CURRENT_TIMESTAMP,
                    approval_reason = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE action_id IN ({placeholders}) AND approval_status = 'pending'
            ''', [approved_by, notes or 'Bulk approved by ' + approved_by] + action_ids)
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated
            
        finally:
            conn.close()
    
    def get_approval_by_action_id(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Get approval record by action ID.
        
        Args:
            action_id: Action ID
            
        Returns:
            Approval record or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM action_approvals WHERE action_id = ?', (action_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
            
        finally:
            conn.close()
    
    def get_approvals_by_plan_id(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all approval records for a plan.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            List of approval records for the plan
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM action_approvals WHERE plan_id = ? ORDER BY created_at', (plan_id,))
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
            
        finally:
            conn.close()
    
    def get_approval_metrics(self) -> Dict[str, Any]:
        """Get approval queue and performance metrics.
        
        Returns:
            Dictionary with approval metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Queue counts
            cursor.execute('''
                SELECT approval_route, approval_status, COUNT(*) 
                FROM action_approvals 
                GROUP BY approval_route, approval_status
            ''')
            queue_data = cursor.fetchall()
            
            # Risk distribution
            cursor.execute('''
                SELECT risk_level, COUNT(*) 
                FROM action_approvals 
                GROUP BY risk_level
            ''')
            risk_data = cursor.fetchall()
            
            # Approval timing (for approved items in last 7 days)
            cursor.execute('''
                SELECT AVG(
                    (julianday(approved_at) - julianday(created_at)) * 24
                ) as avg_hours
                FROM action_approvals 
                WHERE approval_status = 'approved' 
                AND approved_at > datetime('now', '-7 days')
            ''')
            avg_approval_time = cursor.fetchone()[0] or 0
            
            # Build metrics
            metrics = {
                'queue_status': {},
                'risk_distribution': {},
                'avg_approval_time_hours': round(avg_approval_time, 2),
                'total_actions': 0
            }
            
            # Process queue data
            for route, status, count in queue_data:
                if route not in metrics['queue_status']:
                    metrics['queue_status'][route] = {}
                metrics['queue_status'][route][status] = count
                metrics['total_actions'] += count
            
            # Process risk data
            for risk_level, count in risk_data:
                metrics['risk_distribution'][risk_level or 'unknown'] = count
            
            # Calculate approval rate
            total_decided = sum(
                metrics['queue_status'].get(route, {}).get('approved', 0) + 
                metrics['queue_status'].get(route, {}).get('rejected', 0)
                for route in metrics['queue_status']
            )
            total_pending = sum(
                metrics['queue_status'].get(route, {}).get('pending', 0)
                for route in metrics['queue_status']
            )
            
            metrics['approval_rate'] = round(
                (total_decided / (total_decided + total_pending)) * 100, 1
            ) if (total_decided + total_pending) > 0 else 0
            
            metrics['pending_approvals'] = total_pending
            
            return metrics
            
        finally:
            conn.close()
    
    def delete_approval(self, action_id: str) -> bool:
        """Delete an approval record.
        
        Args:
            action_id: Action ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM action_approvals WHERE action_id = ?', (action_id,))
            rows_deleted = cursor.rowcount
            conn.commit()
            
            return rows_deleted > 0
            
        finally:
            conn.close()
    
    def delete_all_approvals(self) -> int:
        """Delete all approval records.
        
        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM action_approvals')
            rows_deleted = cursor.rowcount
            conn.commit()
            
            return rows_deleted
            
        finally:
            conn.close()
    
    def update_execution_result(self, action_id: str, execution_data: Dict[str, Any]) -> bool:
        """Update approval record with execution results.
        
        Args:
            action_id: Action ID that was executed
            execution_data: Dictionary containing execution details:
                - execution_id: Unique execution identifier
                - execution_status: 'success', 'failed', 'partial', 'skipped'
                - execution_result: Dict with execution outcome details
                - assigned_actor: Actor who executed ('advisor', 'supervisor', etc.)
                - actor_assignment_reason: Why this actor was chosen
                - execution_artifacts: List of artifacts created
                - execution_errors: List of errors encountered
                
        Returns:
            True if update was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE action_approvals 
                SET execution_id = ?,
                    executed_at = CURRENT_TIMESTAMP,
                    execution_status = ?,
                    execution_result = ?,
                    assigned_actor = ?,
                    actor_assignment_reason = ?,
                    execution_artifacts = ?,
                    execution_errors = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE action_id = ?
            ''', (
                execution_data.get('execution_id'),
                execution_data.get('execution_status', 'unknown'),
                json.dumps(execution_data.get('execution_result', {})),
                execution_data.get('assigned_actor'),
                execution_data.get('actor_assignment_reason'),
                json.dumps(execution_data.get('execution_artifacts', [])),
                json.dumps(execution_data.get('execution_errors', [])),
                action_id
            ))
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
        finally:
            conn.close()
    
    def get_execution_results_by_execution_id(self, execution_id: str) -> List[Dict[str, Any]]:
        """Get all execution results for a specific execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            List of action records with execution results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM action_approvals 
                WHERE execution_id = ? AND executed_at IS NOT NULL
                ORDER BY executed_at
            ''', (execution_id,))
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                record = dict(zip(columns, row))
                # Parse JSON fields
                if record.get('execution_result'):
                    try:
                        record['execution_result'] = json.loads(record['execution_result'])
                    except json.JSONDecodeError:
                        pass
                        
                if record.get('execution_artifacts'):
                    try:
                        record['execution_artifacts'] = json.loads(record['execution_artifacts'])
                    except json.JSONDecodeError:
                        record['execution_artifacts'] = []
                        
                if record.get('execution_errors'):
                    try:
                        record['execution_errors'] = json.loads(record['execution_errors'])
                    except json.JSONDecodeError:
                        record['execution_errors'] = []
                        
                results.append(record)
                
            return results
            
        finally:
            conn.close()
    
    def get_actor_performance_metrics(self, actor: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics for actors.
        
        Args:
            actor: Specific actor to get metrics for, or None for all actors
            
        Returns:
            Dictionary with actor performance metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            base_query = '''
                SELECT assigned_actor, execution_status, COUNT(*) as count
                FROM action_approvals 
                WHERE executed_at IS NOT NULL
            '''
            
            if actor:
                cursor.execute(base_query + ' AND assigned_actor = ? GROUP BY assigned_actor, execution_status', (actor,))
            else:
                cursor.execute(base_query + ' GROUP BY assigned_actor, execution_status')
            
            performance_data = cursor.fetchall()
            
            # Calculate success rates by actor
            metrics = {}
            for assigned_actor, status, count in performance_data:
                if not assigned_actor:
                    continue
                    
                if assigned_actor not in metrics:
                    metrics[assigned_actor] = {
                        'total_executions': 0,
                        'successful_executions': 0,
                        'failed_executions': 0,
                        'success_rate': 0.0
                    }
                
                metrics[assigned_actor]['total_executions'] += count
                
                if status == 'success':
                    metrics[assigned_actor]['successful_executions'] += count
                elif status == 'failed':
                    metrics[assigned_actor]['failed_executions'] += count
            
            # Calculate success rates
            for actor_name in metrics:
                total = metrics[actor_name]['total_executions']
                successful = metrics[actor_name]['successful_executions']
                metrics[actor_name]['success_rate'] = round((successful / total) * 100, 1) if total > 0 else 0
            
            return metrics
            
        finally:
            conn.close()