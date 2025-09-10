"""
OverrideManager: Emergency override controls with enhanced logging

Core Principles:
- Emergency override capability with strict audit trail
- Permission validation for authorized users only
- Complete audit logging for compliance
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from .audit_logger import AuditLogger


class InsufficientPermissionsError(Exception):
    """Raised when user lacks permissions for override operations."""
    pass


class OverrideManager:
    """
    Emergency override manager with enhanced logging and permission controls.
    
    Features:
    - Emergency override with justification requirements
    - Permission validation for authorized users
    - Complete audit trail for all override operations
    - Override impact tracking and reporting
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.audit_logger = AuditLogger(db_path)
        self._init_database()
        
        # Define override permissions (in production, this would come from a permission system)
        self.override_permissions = {
            "manager_bob": ["customer_escalation", "system_failure", "regulatory_deadline"],
            "director_alice": ["all"],  # Director has all override permissions
            "ceo_john": ["all"]
        }
    
    def _init_database(self):
        """Initialize override management database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS overrides (
                    override_id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    override_by TEXT NOT NULL,
                    emergency_type TEXT NOT NULL,
                    justification TEXT NOT NULL,
                    approval_level_bypassed TEXT,
                    override_executed_at TEXT NOT NULL,
                    impact_assessment TEXT,
                    followup_required BOOLEAN DEFAULT TRUE,
                    followup_completed BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS override_audit_events (
                    event_id TEXT PRIMARY KEY,
                    override_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_timestamp TEXT NOT NULL,
                    event_details TEXT,
                    FOREIGN KEY (override_id) REFERENCES overrides (override_id)
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_override_action ON overrides(action_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_override_user ON overrides(override_by)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_override_type ON overrides(emergency_type)")
            
            conn.commit()
    
    def execute_override(self, request: Dict[str, Any]) -> str:
        """
        Execute emergency override with proper validation and logging.
        
        Args:
            request: Override request with justification and emergency type
            
        Returns:
            Override ID for tracking
            
        Raises:
            InsufficientPermissionsError: If user lacks override permissions
        """
        override_by = request["override_by"]
        emergency_type = request["emergency_type"]
        
        # Validate permissions
        if not self._validate_override_permissions(override_by, emergency_type):
            raise InsufficientPermissionsError(
                f"User {override_by} lacks permissions for {emergency_type} override"
            )
        
        override_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Log pre-override audit event
        self.audit_logger.log_event({
            "event_type": "override_initiated",
            "action_id": request["action_id"],
            "user_id": override_by,
            "timestamp": now,
            "details": {
                "override_id": override_id,
                "emergency_type": emergency_type,
                "justification": request["justification"],
                "approval_level_bypassed": request.get("approval_level_bypassed")
            }
        })
        
        # Assess impact
        impact_assessment = self._assess_override_impact(request)
        
        # Store override record
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO overrides 
                (override_id, action_id, override_by, emergency_type, justification,
                 approval_level_bypassed, override_executed_at, impact_assessment, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                override_id,
                request["action_id"],
                override_by,
                emergency_type,
                request["justification"],
                request.get("approval_level_bypassed"),
                now.isoformat(),
                json.dumps(impact_assessment),
                now.isoformat()
            ))
            conn.commit()
        
        # Log override execution
        self.audit_logger.log_event({
            "event_type": "override_executed",
            "action_id": request["action_id"],
            "user_id": override_by,
            "timestamp": now,
            "details": {
                "override_id": override_id,
                "impact_assessment": impact_assessment,
                "followup_required": True
            }
        })
        
        # Store detailed audit event
        self._store_override_audit_event(override_id, "override_executed", now, {
            "emergency_type": emergency_type,
            "justification": request["justification"],
            "impact": impact_assessment
        })
        
        # Log completion
        self.audit_logger.log_event({
            "event_type": "override_completed",
            "action_id": request["action_id"],
            "user_id": override_by,
            "timestamp": now,
            "details": {
                "override_id": override_id,
                "status": "executed_successfully"
            }
        })
        
        return override_id
    
    def _validate_override_permissions(self, user_id: str, emergency_type: str) -> bool:
        """Validate if user has permissions for specific override type."""
        user_permissions = self.override_permissions.get(user_id, [])
        
        # Check if user has "all" permissions or specific emergency type
        return "all" in user_permissions or emergency_type in user_permissions
    
    def _assess_override_impact(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact of the override operation."""
        return {
            "risk_level": "high",  # All overrides are high risk
            "compliance_impact": "requires_review",
            "audit_visibility": "enhanced",
            "followup_deadline": (datetime.now().date() + 
                                timedelta(days=1)).isoformat(),
            "stakeholders_to_notify": ["compliance_team", "audit_committee"]
        }
    
    def _store_override_audit_event(self, override_id: str, event_type: str, 
                                   timestamp: datetime, details: Dict[str, Any]):
        """Store detailed override audit event."""
        event_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO override_audit_events 
                (event_id, override_id, event_type, event_timestamp, event_details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                event_id,
                override_id,
                event_type,
                timestamp.isoformat(),
                json.dumps(details)
            ))
            conn.commit()
    
    def get_override_log(self, override_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed override log by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM overrides WHERE override_id = ?
            """, (override_id,))
            result = cursor.fetchone()
            
            if result:
                override_log = dict(result)
                # Parse JSON fields
                if override_log["impact_assessment"]:
                    override_log["impact_assessment"] = json.loads(override_log["impact_assessment"])
                
                # Add logged_at for compatibility with tests
                override_log["logged_at"] = override_log["created_at"]
                return override_log
            
            return None
    
    def get_related_audit_events(self, override_id: str) -> List[Dict[str, Any]]:
        """Get all audit events related to an override."""
        # Get main audit events from audit logger
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get the override record to find action_id
            cursor = conn.execute("""
                SELECT action_id FROM overrides WHERE override_id = ?
            """, (override_id,))
            override_result = cursor.fetchone()
            
            if not override_result:
                return []
            
            action_id = override_result["action_id"]
            
            # Get audit events for this action that contain the override_id
            cursor = conn.execute("""
                SELECT * FROM audit_events 
                WHERE action_id = ? 
                AND (details LIKE ? OR details LIKE ? OR details LIKE ?)
                ORDER BY timestamp
            """, (action_id, f'%{override_id}%', '%override_initiated%', '%override_executed%'))
            
            audit_events = []
            for row in cursor.fetchall():
                event = dict(row)
                if event["details"]:
                    event["details"] = json.loads(event["details"])
                audit_events.append(event)
            
            # Add override-specific audit events
            cursor = conn.execute("""
                SELECT * FROM override_audit_events WHERE override_id = ?
                ORDER BY event_timestamp
            """, (override_id,))
            
            for row in cursor.fetchall():
                event = dict(row)
                event["event_type"] = event["event_type"]
                event["timestamp"] = event["event_timestamp"]
                if event["event_details"]:
                    event["details"] = json.loads(event["event_details"])
                audit_events.append(event)
            
            return audit_events