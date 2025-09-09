"""SQLite storage layer for action plans."""
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.transcript import Transcript


class ActionPlanStore:
    """SQLite-based storage for action plans.
    
    Follows the architecture pattern from transcript_store.py and analysis_store.py.
    Provides storage, retrieval, and querying for four-layer action plans.
    """
    
    def __init__(self, db_path: str):
        """Initialize the store with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema for action plans."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create action_plans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_plans (
                id TEXT PRIMARY KEY,
                analysis_id TEXT NOT NULL,
                transcript_id TEXT NOT NULL,
                plan_data TEXT NOT NULL,  -- JSON of all four plans
                
                -- Quick-access fields for filtering and routing
                risk_level TEXT,  -- high, medium, low
                approval_route TEXT,  -- supervisor_approval, advisor_approval, auto_approved
                queue_status TEXT,  -- pending_supervisor, pending_advisor, approved, rejected
                auto_executable BOOLEAN,
                
                -- Metadata
                generator_version TEXT,
                routing_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by TEXT,
                
                -- Foreign key relationships
                FOREIGN KEY (analysis_id) REFERENCES analysis (id),
                FOREIGN KEY (transcript_id) REFERENCES transcripts (id)
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action_plans_queue_status 
            ON action_plans (queue_status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action_plans_risk_level 
            ON action_plans (risk_level)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action_plans_approval_route 
            ON action_plans (approval_route)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_action_plans_transcript_id 
            ON action_plans (transcript_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def store(self, action_plan: Dict[str, Any]) -> str:
        """Store an action plan.
        
        Args:
            action_plan: Action plan dictionary with all four layers
            
        Returns:
            Plan ID of the stored plan
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            plan_id = action_plan.get('plan_id')
            
            cursor.execute('''
                INSERT OR REPLACE INTO action_plans 
                (id, analysis_id, transcript_id, plan_data, risk_level, approval_route, 
                 queue_status, auto_executable, generator_version, routing_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan_id,
                action_plan.get('analysis_id'),
                action_plan.get('transcript_id'),
                json.dumps(action_plan),
                action_plan.get('risk_level'),
                action_plan.get('approval_route'),
                action_plan.get('queue_status'),
                action_plan.get('auto_executable', False),
                action_plan.get('generator_version'),
                action_plan.get('routing_reason')
            ))
            
            conn.commit()
            return plan_id
            
        finally:
            conn.close()
    
    def get_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by ID.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            Action plan dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                       queue_status, auto_executable, generator_version, routing_reason,
                       created_at, approved_at, approved_by
                FROM action_plans WHERE id = ?
            ''', (plan_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Parse the stored action plan
            plan_data = json.loads(row[3])
            
            # Add metadata
            plan_data.update({
                'plan_id': row[0],
                'analysis_id': row[1],
                'transcript_id': row[2],
                'risk_level': row[4],
                'approval_route': row[5],
                'queue_status': row[6],
                'auto_executable': row[7],
                'generator_version': row[8],
                'routing_reason': row[9],
                'created_at': row[10],
                'approved_at': row[11],
                'approved_by': row[12]
            })
            
            return plan_data
            
        finally:
            conn.close()
    
    def get_by_transcript_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by transcript ID.
        
        Args:
            transcript_id: Transcript ID
            
        Returns:
            Latest action plan for the transcript or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                       queue_status, auto_executable, generator_version, routing_reason,
                       created_at, approved_at, approved_by
                FROM action_plans 
                WHERE transcript_id = ?
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (transcript_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Parse the stored action plan
            plan_data = json.loads(row[3])
            
            # Add metadata
            plan_data.update({
                'plan_id': row[0],
                'analysis_id': row[1],
                'transcript_id': row[2],
                'risk_level': row[4],
                'approval_route': row[5],
                'queue_status': row[6],
                'auto_executable': row[7],
                'generator_version': row[8],
                'routing_reason': row[9],
                'created_at': row[10],
                'approved_at': row[11],
                'approved_by': row[12]
            })
            
            return plan_data
            
        finally:
            conn.close()
    
    def get_approval_queue(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get action plans in approval queue.
        
        Args:
            status: Optional filter by queue status
            
        Returns:
            List of action plans pending approval
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if status:
                cursor.execute('''
                    SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                           queue_status, auto_executable, generator_version, routing_reason,
                           created_at, approved_at, approved_by
                    FROM action_plans 
                    WHERE queue_status = ?
                    ORDER BY created_at DESC
                ''', (status,))
            else:
                cursor.execute('''
                    SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                           queue_status, auto_executable, generator_version, routing_reason,
                           created_at, approved_at, approved_by
                    FROM action_plans 
                    WHERE queue_status IN ('pending_supervisor', 'pending_advisor')
                    ORDER BY created_at DESC
                ''')
            
            rows = cursor.fetchall()
            plans = []
            
            for row in rows:
                # Parse the stored action plan
                plan_data = json.loads(row[3])
                
                # Add metadata
                plan_data.update({
                    'plan_id': row[0],
                    'analysis_id': row[1],
                    'transcript_id': row[2],
                    'risk_level': row[4],
                    'approval_route': row[5],
                    'queue_status': row[6],
                    'auto_executable': row[7],
                    'generator_version': row[8],
                    'routing_reason': row[9],
                    'created_at': row[10],
                    'approved_at': row[11],
                    'approved_by': row[12]
                })
                
                plans.append(plan_data)
            
            return plans
            
        finally:
            conn.close()
    
    def get_by_risk_level(self, risk_level: str) -> List[Dict[str, Any]]:
        """Get action plans by risk level.
        
        Args:
            risk_level: Risk level (high, medium, low)
            
        Returns:
            List of action plans with specified risk level
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                       queue_status, auto_executable, generator_version, routing_reason,
                       created_at, approved_at, approved_by
                FROM action_plans 
                WHERE risk_level = ?
                ORDER BY created_at DESC
            ''', (risk_level,))
            
            rows = cursor.fetchall()
            plans = []
            
            for row in rows:
                # Parse the stored action plan
                plan_data = json.loads(row[3])
                
                # Add metadata
                plan_data.update({
                    'plan_id': row[0],
                    'analysis_id': row[1],
                    'transcript_id': row[2],
                    'risk_level': row[4],
                    'approval_route': row[5],
                    'queue_status': row[6],
                    'auto_executable': row[7],
                    'generator_version': row[8],
                    'routing_reason': row[9],
                    'created_at': row[10],
                    'approved_at': row[11],
                    'approved_by': row[12]
                })
                
                plans.append(plan_data)
            
            return plans
            
        finally:
            conn.close()
    
    def approve_plan(self, plan_id: str, approved_by: str) -> bool:
        """Approve an action plan.
        
        Args:
            plan_id: Action plan ID
            approved_by: Approver identifier
            
        Returns:
            True if approval was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE action_plans 
                SET queue_status = 'approved',
                    approved_at = CURRENT_TIMESTAMP,
                    approved_by = ?
                WHERE id = ?
            ''', (approved_by, plan_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
        finally:
            conn.close()
    
    def reject_plan(self, plan_id: str, rejected_by: str) -> bool:
        """Reject an action plan.
        
        Args:
            plan_id: Action plan ID
            rejected_by: Rejector identifier
            
        Returns:
            True if rejection was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE action_plans 
                SET queue_status = 'rejected',
                    approved_at = CURRENT_TIMESTAMP,
                    approved_by = ?
                WHERE id = ?
            ''', (rejected_by, plan_id))
            
            rows_updated = cursor.rowcount
            conn.commit()
            
            return rows_updated > 0
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all action plans.
        
        Args:
            limit: Optional limit on number of plans to return
            
        Returns:
            List of action plans ordered by creation time
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, analysis_id, transcript_id, plan_data, risk_level, approval_route,
                       queue_status, auto_executable, generator_version, routing_reason,
                       created_at, approved_at, approved_by
                FROM action_plans 
                ORDER BY created_at DESC
            '''
            
            if limit:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            plans = []
            
            for row in rows:
                # Parse the stored action plan
                plan_data = json.loads(row[3])
                
                # Add metadata
                plan_data.update({
                    'plan_id': row[0],
                    'analysis_id': row[1],
                    'transcript_id': row[2],
                    'risk_level': row[4],
                    'approval_route': row[5],
                    'queue_status': row[6],
                    'auto_executable': row[7],
                    'generator_version': row[8],
                    'routing_reason': row[9],
                    'created_at': row[10],
                    'approved_at': row[11],
                    'approved_by': row[12]
                })
                
                plans.append(plan_data)
            
            return plans
            
        finally:
            conn.close()
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for action plans.
        
        Returns:
            Dictionary with action plan metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total plans
            cursor.execute('SELECT COUNT(*) FROM action_plans')
            total_plans = cursor.fetchone()[0]
            
            # Plans by status
            cursor.execute('''
                SELECT queue_status, COUNT(*) 
                FROM action_plans 
                GROUP BY queue_status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # Plans by risk level
            cursor.execute('''
                SELECT risk_level, COUNT(*) 
                FROM action_plans 
                GROUP BY risk_level
            ''')
            risk_counts = dict(cursor.fetchall())
            
            # Plans by approval route
            cursor.execute('''
                SELECT approval_route, COUNT(*) 
                FROM action_plans 
                GROUP BY approval_route
            ''')
            route_counts = dict(cursor.fetchall())
            
            # Auto-executable percentage
            cursor.execute('''
                SELECT 
                    COUNT(CASE WHEN auto_executable = 1 THEN 1 END) * 100.0 / COUNT(*) 
                FROM action_plans
            ''')
            auto_executable_pct = cursor.fetchone()[0] or 0
            
            return {
                'total_plans': total_plans,
                'status_distribution': status_counts,
                'risk_distribution': risk_counts,
                'route_distribution': route_counts,
                'auto_executable_percentage': round(auto_executable_pct, 1),
                'pending_approvals': status_counts.get('pending_supervisor', 0) + 
                                   status_counts.get('pending_advisor', 0)
            }
            
        finally:
            conn.close()
    
    def delete(self, plan_id: str) -> bool:
        """Delete an action plan.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            True if deletion was successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM action_plans WHERE id = ?', (plan_id,))
            rows_deleted = cursor.rowcount
            conn.commit()
            
            return rows_deleted > 0
            
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """Delete all action plans.
        
        Returns:
            Number of plans deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM action_plans')
            rows_deleted = cursor.rowcount
            conn.commit()
            
            return rows_deleted
            
        finally:
            conn.close()