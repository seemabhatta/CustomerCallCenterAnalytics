"""
ApprovalWorkflow: Enhanced multi-level approval orchestration

Core Principles:
- Intelligent routing based on LLM evaluation
- Conditional approvals with requirements tracking
- Bulk operations for efficiency
- Timeout handling with auto-escalation
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .audit_logger import AuditLogger
from .governance_engine import GovernanceEngine


class ApprovalWorkflow:
    """
    Enhanced approval workflow system with multi-level routing and intelligent escalation.
    
    Features:
    - LLM-based routing decisions
    - Conditional approvals with tracking
    - Bulk approval operations
    - Automatic timeout escalation
    - Complete audit integration
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.audit_logger = AuditLogger(db_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize approval workflow database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    approval_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending_approval',
                    routed_to TEXT,
                    urgency TEXT,
                    estimated_approval_time TEXT,
                    required_conditions TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    approval_conditions TEXT,
                    approval_notes TEXT,
                    rejected_by TEXT,
                    rejected_at TEXT,
                    rejection_reason TEXT,
                    rejection_feedback TEXT,
                    escalated BOOLEAN DEFAULT FALSE,
                    escalated_to TEXT,
                    escalated_at TEXT,
                    escalation_reason TEXT,
                    timeout_hours REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_status ON approvals(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_action ON approvals(action_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_routed_to ON approvals(routed_to)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_submitted_at ON approvals(submitted_at)")
            
            conn.commit()
    
    def submit_for_approval(self, request: Dict[str, Any]) -> str:
        """
        Submit action for approval with automatic routing.
        
        Args:
            request: Approval request containing action details
            
        Returns:
            Approval ID for tracking
        """
        approval_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Determine routing based on action characteristics
        routed_to = self._determine_routing(request)
        
        # Calculate timeout
        timeout_hours = request.get("timeout_hours", self._calculate_default_timeout(request))
        
        # Prepare approval record
        approval_data = {
            "approval_id": approval_id,
            "action_id": request["action_id"],
            "submitted_by": request["submitted_by"],
            "submitted_at": now.isoformat(),
            "status": "pending_approval",
            "routed_to": routed_to,
            "urgency": request.get("urgency", "medium"),
            "estimated_approval_time": str(request.get("estimated_approval_time", timedelta(hours=2))),
            "required_conditions": json.dumps(request.get("required_conditions", [])),
            "timeout_hours": timeout_hours,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO approvals 
                (approval_id, action_id, submitted_by, submitted_at, status, routed_to,
                 urgency, estimated_approval_time, required_conditions, timeout_hours,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                approval_data["approval_id"],
                approval_data["action_id"],
                approval_data["submitted_by"],
                approval_data["submitted_at"],
                approval_data["status"],
                approval_data["routed_to"],
                approval_data["urgency"],
                approval_data["estimated_approval_time"],
                approval_data["required_conditions"],
                approval_data["timeout_hours"],
                approval_data["created_at"],
                approval_data["updated_at"]
            ))
            conn.commit()
        
        # Log audit event
        self.audit_logger.log_event({
            "event_type": "approval_submitted",
            "action_id": request["action_id"],
            "user_id": request["submitted_by"],
            "timestamp": now,
            "details": {
                "approval_id": approval_id,
                "routed_to": routed_to,
                "urgency": request.get("urgency"),
                "timeout_hours": timeout_hours
            }
        })
        
        return approval_id
    
    def _determine_routing(self, request: Dict[str, Any]) -> str:
        """Determine approval routing based on request characteristics."""
        # For now, use simple logic - in full implementation, this would use GovernanceEngine
        urgency = request.get("urgency", "medium").lower()
        action_id = request.get("action_id", "")
        
        # Simple routing logic (would be replaced with LLM-based routing)
        if "financial" in action_id.lower() or urgency == "high":
            return "supervisor"
        elif urgency == "critical":
            return "leadership"
        else:
            return "advisor"
    
    def _calculate_default_timeout(self, request: Dict[str, Any]) -> float:
        """Calculate default timeout based on urgency."""
        urgency = request.get("urgency", "medium").lower()
        timeout_map = {
            "critical": 0.5,  # 30 minutes
            "high": 2.0,      # 2 hours
            "medium": 24.0,   # 24 hours
            "low": 72.0       # 72 hours
        }
        return timeout_map.get(urgency, 24.0)
    
    def get_status(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of approval request."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM approvals WHERE approval_id = ?
            """, (approval_id,))
            result = cursor.fetchone()
            
            if result:
                approval = dict(result)
                # Parse JSON fields
                if approval["required_conditions"]:
                    approval["required_conditions"] = json.loads(approval["required_conditions"])
                if approval["approval_conditions"]:
                    approval["approval_conditions"] = json.loads(approval["approval_conditions"])
                
                # Convert SQLite integers to booleans
                approval["escalated"] = bool(approval["escalated"])
                
                return approval
            return None
    
    def approve(self, approval_id: str, approved_by: str, 
               conditions: Optional[List[str]] = None,
               notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve request with optional conditions.
        
        Args:
            approval_id: ID of approval to approve
            approved_by: User approving the request
            conditions: Optional conditions that must be met
            notes: Optional approval notes
            
        Returns:
            Approval result with status and details
        """
        now = datetime.now()
        conditions = conditions or []
        
        # Determine status based on conditions
        status = "approved_with_conditions" if conditions else "approved"
        
        # Update approval record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE approvals SET
                    status = ?,
                    approved_by = ?,
                    approved_at = ?,
                    approval_conditions = ?,
                    approval_notes = ?,
                    updated_at = ?
                WHERE approval_id = ?
            """, (
                status,
                approved_by,
                now.isoformat(),
                json.dumps(conditions),
                notes,
                now.isoformat(),
                approval_id
            ))
            conn.commit()
        
        # Get updated approval for result
        approval = self.get_status(approval_id)
        
        # Log audit event
        self.audit_logger.log_event({
            "event_type": "approval_approved",
            "action_id": approval["action_id"],
            "user_id": approved_by,
            "timestamp": now,
            "details": {
                "approval_id": approval_id,
                "status": status,
                "conditions": conditions,
                "notes": notes
            }
        })
        
        return {
            "approval_id": approval_id,
            "status": status,
            "approved_by": approved_by,
            "approved_at": now.isoformat(),
            "conditions": conditions,
            "notes": notes
        }
    
    def reject(self, approval_id: str, rejected_by: str,
              reason: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """
        Reject approval request with reason.
        
        Args:
            approval_id: ID of approval to reject
            rejected_by: User rejecting the request
            reason: Reason for rejection
            feedback: Optional feedback for improvement
            
        Returns:
            Rejection result with details
        """
        now = datetime.now()
        
        # Update approval record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE approvals SET
                    status = 'rejected',
                    rejected_by = ?,
                    rejected_at = ?,
                    rejection_reason = ?,
                    rejection_feedback = ?,
                    updated_at = ?
                WHERE approval_id = ?
            """, (
                rejected_by,
                now.isoformat(),
                reason,
                feedback,
                now.isoformat(),
                approval_id
            ))
            conn.commit()
        
        # Get updated approval for result
        approval = self.get_status(approval_id)
        
        # Log audit event
        self.audit_logger.log_event({
            "event_type": "approval_rejected",
            "action_id": approval["action_id"],
            "user_id": rejected_by,
            "timestamp": now,
            "details": {
                "approval_id": approval_id,
                "reason": reason,
                "feedback": feedback
            }
        })
        
        return {
            "approval_id": approval_id,
            "status": "rejected",
            "rejected_by": rejected_by,
            "rejected_at": now.isoformat(),
            "reason": reason,
            "feedback": feedback
        }
    
    def bulk_approve(self, approval_ids: List[str], approved_by: str,
                    notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Approve multiple requests efficiently.
        
        Args:
            approval_ids: List of approval IDs to approve
            approved_by: User approving the requests
            notes: Optional bulk approval notes
            
        Returns:
            Bulk approval result with counts
        """
        now = datetime.now()
        approved_count = 0
        failed_count = 0
        
        notes = notes or "Bulk approval"
        
        for approval_id in approval_ids:
            try:
                # Check if approval exists and is pending
                approval = self.get_status(approval_id)
                if approval and approval["status"] == "pending_approval":
                    self.approve(approval_id, approved_by, notes=notes)
                    approved_count += 1
                else:
                    failed_count += 1
            except Exception:
                failed_count += 1
        
        # Log bulk approval event
        self.audit_logger.log_event({
            "event_type": "bulk_approval",
            "action_id": None,
            "user_id": approved_by,
            "timestamp": now,
            "details": {
                "approval_ids": approval_ids,
                "approved_count": approved_count,
                "failed_count": failed_count,
                "notes": notes
            }
        })
        
        return {
            "approved_count": approved_count,
            "failed_count": failed_count,
            "total_requested": len(approval_ids),
            "approved_by": approved_by,
            "bulk_approval_at": now.isoformat()
        }
    
    def check_and_escalate_timeouts(self):
        """Check for timed-out approvals and escalate automatically."""
        now = datetime.now()
        
        # Query pending approvals
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM approvals 
                WHERE status = 'pending_approval' 
                AND escalated = FALSE
                AND timeout_hours IS NOT NULL
            """)
            pending_approvals = cursor.fetchall()
        
        escalated_count = 0
        for approval in pending_approvals:
            submitted_at = datetime.fromisoformat(approval["submitted_at"])
            timeout_delta = timedelta(hours=approval["timeout_hours"])
            
            if now > submitted_at + timeout_delta:
                # Escalate this approval
                escalated_to = self._determine_escalation_target(approval["routed_to"])
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        UPDATE approvals SET
                            escalated = TRUE,
                            escalated_to = ?,
                            escalated_at = ?,
                            escalation_reason = 'approval_timeout',
                            routed_to = ?,
                            updated_at = ?
                        WHERE approval_id = ?
                    """, (
                        escalated_to,
                        now.isoformat(),
                        escalated_to,
                        now.isoformat(),
                        approval["approval_id"]
                    ))
                    conn.commit()
                
                # Log escalation
                self.audit_logger.log_event({
                    "event_type": "approval_escalated",
                    "action_id": approval["action_id"],
                    "user_id": "system",
                    "timestamp": now,
                    "details": {
                        "approval_id": approval["approval_id"],
                        "escalated_from": approval["routed_to"],
                        "escalated_to": escalated_to,
                        "reason": "approval_timeout",
                        "timeout_hours": approval["timeout_hours"]
                    }
                })
                
                escalated_count += 1
        
        return escalated_count
    
    def _determine_escalation_target(self, current_route: str) -> str:
        """Determine escalation target based on current routing."""
        escalation_map = {
            "advisor": "supervisor",
            "supervisor": "leadership",
            "leadership": "executive"  # Highest level
        }
        return escalation_map.get(current_route, "supervisor")
    
    def get_approval_queue(self, routed_to: Optional[str] = None, 
                          status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get approval queue with optional filtering."""
        query = "SELECT * FROM approvals WHERE 1=1"
        params = []
        
        if routed_to:
            query += " AND routed_to = ?"
            params.append(routed_to)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY submitted_at ASC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            
            approvals = []
            for row in results:
                approval = dict(row)
                # Parse JSON fields
                if approval["required_conditions"]:
                    approval["required_conditions"] = json.loads(approval["required_conditions"])
                if approval["approval_conditions"]:
                    approval["approval_conditions"] = json.loads(approval["approval_conditions"])
                approvals.append(approval)
            
            return approvals