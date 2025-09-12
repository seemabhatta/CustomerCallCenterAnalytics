"""SQLite storage layer for workflow approval management.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: No hardcoded routing logic - all decisions by LLM agents
- TDD: Designed to pass the comprehensive test suite
"""
import sqlite3
import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime


class WorkflowStore:
    """SQLite-based storage for workflow approval management.
    
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
        """Initialize database schema.
        
        Raises:
            Exception: If schema creation fails (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Enable foreign key enforcement
            cursor.execute('PRAGMA foreign_keys = ON')
            
            # Workflows table - core entity
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    analysis_id TEXT NOT NULL,
                    transcript_id TEXT NOT NULL,
                    
                    -- Granular workflow categorization
                    workflow_type TEXT NOT NULL CHECK (workflow_type IN ('BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP')),
                    
                    -- Workflow content (JSON - LLM extracted)
                    workflow_data TEXT NOT NULL,
                    
                    -- LLM agent decisions (no hardcoded logic)
                    risk_level TEXT NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
                    status TEXT NOT NULL CHECK (status IN ('PENDING_ASSESSMENT', 'AWAITING_APPROVAL', 'AUTO_APPROVED', 'REJECTED', 'EXECUTED')),
                    
                    -- Context preservation for agent decisions
                    context_data TEXT NOT NULL,
                    risk_reasoning TEXT,
                    approval_reasoning TEXT,
                    
                    -- Approval workflow state
                    requires_human_approval BOOLEAN NOT NULL DEFAULT 0,
                    assigned_approver TEXT,
                    approved_by TEXT,
                    approved_at TIMESTAMP,
                    rejected_by TEXT,
                    rejected_at TIMESTAMP,
                    rejection_reason TEXT,
                    
                    -- Execution tracking
                    executed_at TIMESTAMP,
                    execution_results TEXT,
                    
                    -- Audit timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Foreign keys (strict referential integrity)
                    FOREIGN KEY (plan_id) REFERENCES action_plans (id),
                    FOREIGN KEY (analysis_id) REFERENCES analysis (id),
                    FOREIGN KEY (transcript_id) REFERENCES transcripts (id)
                )
            ''')
            
            # State transition audit log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS workflow_state_transitions (
                    id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    from_status TEXT,
                    to_status TEXT NOT NULL,
                    transition_reason TEXT,
                    transitioned_by TEXT NOT NULL,
                    transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (workflow_id) REFERENCES workflows (id) ON DELETE CASCADE
                )
            ''')
            
            # Performance indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows (status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_risk_level ON workflows (risk_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_plan_id ON workflows (plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflows_requires_approval ON workflows (requires_human_approval)')
            
            # Auto-update timestamp trigger
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_workflow_timestamp 
                AFTER UPDATE ON workflows
                BEGIN
                    UPDATE workflows SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
            
        finally:
            conn.close()
    
    def create(self, workflow_data: Dict[str, Any]) -> str:
        """Create workflow record.
        
        Args:
            workflow_data: Complete workflow data
            
        Returns:
            Workflow ID
            
        Raises:
            ValueError: Missing required fields (NO FALLBACK)
            Exception: Database operation failure (NO FALLBACK)
        """
        # Strict validation - fail fast on missing data
        required_fields = ['plan_id', 'analysis_id', 'transcript_id', 'workflow_data', 
                          'risk_level', 'status', 'context_data']
        
        for field in required_fields:
            if field not in workflow_data or workflow_data[field] is None:
                raise ValueError(f"Required field missing or null: {field}")
        
        # Validate enum values - no fallback to defaults
        if workflow_data['risk_level'] not in ['LOW', 'MEDIUM', 'HIGH']:
            raise ValueError(f"Invalid risk_level: {workflow_data['risk_level']}")
        
        valid_statuses = ['PENDING_ASSESSMENT', 'AWAITING_APPROVAL', 'AUTO_APPROVED', 'REJECTED', 'EXECUTED']
        if workflow_data['status'] not in valid_statuses:
            raise ValueError(f"Invalid status: {workflow_data['status']}")
        
        workflow_id = workflow_data.get('id', str(uuid.uuid4()))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO workflows 
                (id, plan_id, analysis_id, transcript_id, workflow_type, workflow_data, risk_level, status,
                 context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                 assigned_approver)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow_id,
                workflow_data['plan_id'],
                workflow_data['analysis_id'], 
                workflow_data['transcript_id'],
                workflow_data['workflow_type'],
                json.dumps(workflow_data['workflow_data']),
                workflow_data['risk_level'],
                workflow_data['status'],
                json.dumps(workflow_data['context_data']),
                json.dumps(workflow_data.get('risk_reasoning')) if isinstance(workflow_data.get('risk_reasoning'), dict) else workflow_data.get('risk_reasoning'),
                json.dumps(workflow_data.get('approval_reasoning')) if isinstance(workflow_data.get('approval_reasoning'), dict) else workflow_data.get('approval_reasoning'),
                workflow_data.get('requires_human_approval', False),
                json.dumps(workflow_data.get('assigned_approver')) if isinstance(workflow_data.get('assigned_approver'), dict) else workflow_data.get('assigned_approver')
            ))
            
            # Log initial state transition
            self._log_state_transition(
                cursor, workflow_id, None, workflow_data['status'],
                "Workflow created", "system"
            )
            
            conn.commit()
            return workflow_id
            
        finally:
            conn.close()
    
    def get_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by ID.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow data or None if not found
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows WHERE id = ?
            ''', (workflow_id,))
            
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
            
        finally:
            conn.close()
    
    def get_by_plan_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by plan ID.
        
        Args:
            plan_id: Action plan ID
            
        Returns:
            Latest workflow for plan or None
            
        Raises:
            ValueError: Invalid plan_id (NO FALLBACK)
        """
        if not plan_id or not isinstance(plan_id, str):
            raise ValueError("plan_id must be a non-empty string")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows 
                WHERE plan_id = ?
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (plan_id,))
            
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
            
        finally:
            conn.close()
    
    def get_by_status(self, status: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get workflows by status.
        
        Args:
            status: Workflow status
            limit: Optional result limit
            
        Returns:
            List of matching workflows
            
        Raises:
            ValueError: Invalid status (NO FALLBACK)
        """
        valid_statuses = ['PENDING_ASSESSMENT', 'AWAITING_APPROVAL', 'AUTO_APPROVED', 'REJECTED', 'EXECUTED']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows 
                WHERE status = ?
                ORDER BY created_at DESC
            '''
            
            params = [status]
            if limit and isinstance(limit, int) and limit > 0:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_by_risk_level(self, risk_level: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get workflows by risk level.
        
        Args:
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            limit: Optional result limit
            
        Returns:
            List of matching workflows
            
        Raises:
            ValueError: Invalid risk_level (NO FALLBACK)
        """
        if risk_level not in ['LOW', 'MEDIUM', 'HIGH']:
            raise ValueError(f"Invalid risk_level: {risk_level}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows 
                WHERE risk_level = ?
                ORDER BY created_at DESC
            '''
            
            params = [risk_level]
            if limit and isinstance(limit, int) and limit > 0:
                query += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def get_pending_approval(self) -> List[Dict[str, Any]]:
        """Get workflows requiring human approval.
        
        Returns:
            List of workflows awaiting approval
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows 
                WHERE status = 'AWAITING_APPROVAL' AND requires_human_approval = 1
                ORDER BY created_at ASC
            ''')
            
            rows = cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def update_status(self, workflow_id: str, new_status: str, 
                     transitioned_by: str, reason: Optional[str] = None,
                     additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Update workflow status with audit logging.
        
        Args:
            workflow_id: Workflow ID
            new_status: New status
            transitioned_by: Who made the transition
            reason: Transition reason
            additional_data: Additional fields to update
            
        Returns:
            True if successful, False if workflow not found
            
        Raises:
            ValueError: Invalid parameters (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        if not transitioned_by or not isinstance(transitioned_by, str):
            raise ValueError("transitioned_by must be a non-empty string")
        
        valid_statuses = ['PENDING_ASSESSMENT', 'AWAITING_APPROVAL', 'AUTO_APPROVED', 'REJECTED', 'EXECUTED']
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid new_status: {new_status}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get current status
            cursor.execute('SELECT status FROM workflows WHERE id = ?', (workflow_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            current_status = row[0]
            
            # Build update query
            update_fields = ['status = ?']
            update_params = [new_status]
            
            # Add additional data if provided
            if additional_data:
                allowed_fields = ['approved_by', 'approved_at', 'rejected_by', 'rejected_at',
                                'rejection_reason', 'executed_at', 'execution_results']
                
                for key, value in additional_data.items():
                    if key in allowed_fields:
                        update_fields.append(f'{key} = ?')
                        update_params.append(value)
            
            update_params.append(workflow_id)
            
            # Execute update
            cursor.execute(f'''
                UPDATE workflows 
                SET {', '.join(update_fields)}
                WHERE id = ?
            ''', update_params)
            
            # Log state transition
            self._log_state_transition(
                cursor, workflow_id, current_status, new_status, reason, transitioned_by
            )
            
            conn.commit()
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def delete(self, workflow_id: str) -> bool:
        """Delete workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM workflows WHERE id = ?', (workflow_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count > 0
            
        finally:
            conn.close()
    
    def delete_all(self) -> int:
        """Delete all workflows.
        
        Returns:
            Number of workflows deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('DELETE FROM workflows')
            deleted_count = cursor.rowcount
            conn.commit()
            
            return deleted_count
            
        finally:
            conn.close()
    
    def get_state_transitions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get state transition history.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            List of transitions ordered by time
            
        Raises:
            ValueError: Invalid workflow_id (NO FALLBACK)
        """
        if not workflow_id or not isinstance(workflow_id, str):
            raise ValueError("workflow_id must be a non-empty string")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, from_status, to_status, transition_reason, 
                       transitioned_by, transitioned_at
                FROM workflow_state_transitions 
                WHERE workflow_id = ?
                ORDER BY transitioned_at ASC
            ''', (workflow_id,))
            
            rows = cursor.fetchall()
            transitions = []
            
            for row in rows:
                transitions.append({
                    'id': row[0],
                    'from_status': row[1],
                    'to_status': row[2],
                    'transition_reason': row[3],
                    'transitioned_by': row[4],
                    'transitioned_at': row[5]
                })
            
            return transitions
            
        finally:
            conn.close()
    
    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all workflows.
        
        Args:
            limit: Optional result limit
            
        Returns:
            List of workflows ordered by creation time
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status,
                       context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                       assigned_approver, approved_by, approved_at, rejected_by, rejected_at,
                       rejection_reason, executed_at, execution_results, created_at, updated_at
                FROM workflows 
                ORDER BY created_at DESC
            '''
            
            if limit and isinstance(limit, int) and limit > 0:
                query += f' LIMIT {limit}'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary.
        
        Args:
            row: Database row tuple
            
        Returns:
            Dictionary representation
            
        Raises:
            Exception: JSON parsing failure (NO FALLBACK)
        """
        return {
            'id': row[0],
            'plan_id': row[1],
            'analysis_id': row[2],
            'transcript_id': row[3],
            'workflow_data': json.loads(row[4]),
            'risk_level': row[5],
            'status': row[6],
            'context_data': json.loads(row[7]),
            'risk_reasoning': row[8],
            'approval_reasoning': row[9],
            'requires_human_approval': bool(row[10]),
            'assigned_approver': row[11],
            'approved_by': row[12],
            'approved_at': row[13],
            'rejected_by': row[14],
            'rejected_at': row[15],
            'rejection_reason': row[16],
            'executed_at': row[17],
            'execution_results': json.loads(row[18]) if row[18] else None,
            'created_at': row[19],
            'updated_at': row[20],
            'workflow_type': row[21]
        }
    
    def _log_state_transition(self, cursor, workflow_id: str, from_status: Optional[str],
                            to_status: str, reason: Optional[str], transitioned_by: str):
        """Log state transition for audit trail.
        
        Args:
            cursor: Database cursor
            workflow_id: Workflow ID
            from_status: Previous status
            to_status: New status
            reason: Transition reason
            transitioned_by: Who made the transition
        """
        transition_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO workflow_state_transitions 
            (id, workflow_id, from_status, to_status, transition_reason, transitioned_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transition_id, workflow_id, from_status, to_status, reason, transitioned_by))
    
    def create_bulk(self, workflows_data: List[Dict[str, Any]]) -> List[str]:
        """Create multiple workflows in a single transaction.
        
        Args:
            workflows_data: List of workflow data dictionaries, each containing:
                - plan_id: Plan ID
                - analysis_id: Analysis ID  
                - transcript_id: Transcript ID
                - workflow_data: Action item data
                - workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
                - context_data: Additional context
                
        Returns:
            List of created workflow IDs
            
        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        workflow_ids = []
        
        try:
            cursor = conn.cursor()
            
            for workflow_data in workflows_data:
                workflow_id = str(uuid.uuid4())
                workflow_ids.append(workflow_id)
                
                # NO FALLBACK: Require all essential fields
                if not all(key in workflow_data for key in ['plan_id', 'analysis_id', 'transcript_id', 'workflow_data', 'workflow_type']):
                    raise ValueError(f"Missing required fields in workflow data: {workflow_data}")
                
                # Serialize dict fields to JSON
                workflow_data_json = json.dumps(workflow_data['workflow_data']) if isinstance(workflow_data['workflow_data'], dict) else workflow_data['workflow_data']
                context_data_json = json.dumps(workflow_data.get('context_data', {})) if isinstance(workflow_data.get('context_data', {}), dict) else workflow_data.get('context_data', '{}')
                
                cursor.execute('''
                    INSERT INTO workflows (
                        id, plan_id, analysis_id, transcript_id, workflow_data, risk_level, status, 
                        context_data, risk_reasoning, approval_reasoning, requires_human_approval,
                        assigned_approver, workflow_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    workflow_id,
                    workflow_data['plan_id'],
                    workflow_data['analysis_id'], 
                    workflow_data['transcript_id'],
                    workflow_data_json,
                    'PENDING',  # Will be assessed by risk agent
                    'PENDING_ASSESSMENT',
                    context_data_json,
                    '',  # Will be filled by risk assessment
                    '',  # Will be filled by approval process
                    True,  # Default to requiring approval
                    '',  # Will be assigned by risk assessment
                    workflow_data['workflow_type']
                ))
                
                # Log initial state
                self._log_state_transition(cursor, workflow_id, None, 'PENDING_ASSESSMENT', 
                                         'Initial workflow creation', 'SYSTEM')
            
            conn.commit()
            return workflow_ids
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Bulk workflow creation failed: {str(e)}")
        finally:
            conn.close()
    
    def get_by_plan_id(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a specific plan.
        
        Args:
            plan_id: Plan ID
            
        Returns:
            List of workflow dictionaries
            
        Raises:
            Exception: Database operation failure (NO FALLBACK)
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE plan_id = ?', (plan_id,))
            rows = cursor.fetchall()
            
            if not rows:
                return []
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve workflows for plan {plan_id}: {str(e)}")
        finally:
            conn.close()
    
    def get_by_type(self, workflow_type: str) -> List[Dict[str, Any]]:
        """Get all workflows of a specific type.
        
        Args:
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            
        Returns:
            List of workflow dictionaries
            
        Raises:
            Exception: Invalid type or database failure (NO FALLBACK)
        """
        # NO FALLBACK: Validate workflow type
        valid_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
        if workflow_type not in valid_types:
            raise ValueError(f"Invalid workflow type: {workflow_type}. Must be one of: {valid_types}")
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE workflow_type = ?', (workflow_type,))
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve workflows by type {workflow_type}: {str(e)}")
        finally:
            conn.close()
    
    def get_by_plan_and_type(self, plan_id: str, workflow_type: str) -> List[Dict[str, Any]]:
        """Get workflows for a specific plan and type combination.
        
        Args:
            plan_id: Plan ID
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            
        Returns:
            List of workflow dictionaries
            
        Raises:
            Exception: Invalid type or database failure (NO FALLBACK)
        """
        # NO FALLBACK: Validate workflow type
        valid_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
        if workflow_type not in valid_types:
            raise ValueError(f"Invalid workflow type: {workflow_type}. Must be one of: {valid_types}")
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM workflows WHERE plan_id = ? AND workflow_type = ?', 
                         (plan_id, workflow_type))
            rows = cursor.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        except Exception as e:
            raise Exception(f"Failed to retrieve workflows for plan {plan_id} and type {workflow_type}: {str(e)}")
        finally:
            conn.close()