"""
AuditLogger: Comprehensive audit trail with cryptographic integrity verification

Core Principles:
- Immutable audit logs (cannot be modified after creation)
- Cryptographic chain integrity
- Complete audit trail for compliance
- Fast query capabilities for large datasets
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional


class ImmutableAuditError(Exception):
    """Raised when attempting to modify immutable audit records."""
    pass


class AuditLogger:
    """
    Immutable audit logger with cryptographic integrity verification.
    
    Features:
    - Cryptographic hashing for integrity verification
    - Chain linking for tamper detection
    - Immutable records (cannot be modified)
    - Fast querying with indexes
    - Compliance reporting capabilities
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.last_hash = None
        self._init_database()
        self._load_last_hash()
    
    def _init_database(self):
        """Initialize audit trail database with proper schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    action_id TEXT,
                    user_id TEXT,
                    timestamp TEXT NOT NULL,
                    details TEXT,
                    integrity_hash TEXT NOT NULL,
                    chain_hash TEXT,
                    previous_hash TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for fast querying
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
            
            conn.commit()
    
    def _load_last_hash(self):
        """Load the hash of the last audit event for chain linking."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT integrity_hash FROM audit_events 
                ORDER BY created_at DESC LIMIT 1
            """)
            result = cursor.fetchone()
            self.last_hash = result[0] if result else "genesis"
    
    def log_event(self, event: Dict[str, Any]) -> str:
        """
        Log an immutable audit event with cryptographic integrity.
        
        Args:
            event: Audit event data
            
        Returns:
            Audit ID for the logged event
        """
        audit_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        # Prepare event data
        event_data = {
            "audit_id": audit_id,
            "event_type": event.get("event_type"),
            "action_id": event.get("action_id"),
            "user_id": event.get("user_id"),
            "timestamp": event.get("timestamp", datetime.now()).isoformat() if hasattr(event.get("timestamp", datetime.now()), 'isoformat') else str(event.get("timestamp", datetime.now())),
            "details": json.dumps(event.get("details", {})),
            "created_at": created_at
        }
        
        # Calculate integrity hash
        integrity_hash = self._calculate_integrity_hash(event_data)
        event_data["integrity_hash"] = integrity_hash
        
        # Link to previous event in chain
        event_data["previous_hash"] = self.last_hash
        event_data["chain_hash"] = self._calculate_chain_hash(integrity_hash, self.last_hash)
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_events 
                (audit_id, event_type, action_id, user_id, timestamp, details, 
                 integrity_hash, chain_hash, previous_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data["audit_id"],
                event_data["event_type"],
                event_data["action_id"],
                event_data["user_id"],
                event_data["timestamp"],
                event_data["details"],
                event_data["integrity_hash"],
                event_data["chain_hash"],
                event_data["previous_hash"],
                event_data["created_at"]
            ))
            conn.commit()
        
        # Update last hash for next event
        self.last_hash = integrity_hash
        
        return audit_id
    
    def _calculate_integrity_hash(self, event_data: Dict[str, Any]) -> str:
        """Calculate SHA-256 hash for event integrity."""
        # Create canonical representation for hashing
        hash_data = {
            "event_type": event_data["event_type"],
            "action_id": event_data["action_id"],
            "user_id": event_data["user_id"],
            "timestamp": event_data["timestamp"],
            "details": event_data["details"],
            "created_at": event_data["created_at"]
        }
        
        canonical_json = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    
    def _calculate_chain_hash(self, current_hash: str, previous_hash: str) -> str:
        """Calculate chain hash linking current event to previous."""
        chain_data = f"{previous_hash}:{current_hash}"
        return hashlib.sha256(chain_data.encode('utf-8')).hexdigest()
    
    def get_event(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve audit event by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM audit_events WHERE audit_id = ?
            """, (audit_id,))
            result = cursor.fetchone()
            
            if result:
                event = dict(result)
                # Parse JSON details
                if event["details"]:
                    event["details"] = json.loads(event["details"])
                return event
            return None
    
    def verify_integrity(self, audit_id: str) -> bool:
        """Verify cryptographic integrity of an audit event."""
        event = self.get_event(audit_id)
        if not event:
            return False
        
        # Prepare event data for hash calculation (convert details back to JSON string)
        event_for_hash = {
            "event_type": event["event_type"],
            "action_id": event["action_id"],
            "user_id": event["user_id"],
            "timestamp": event["timestamp"],
            "details": json.dumps(event["details"]) if isinstance(event["details"], dict) else event["details"],
            "created_at": event["created_at"]
        }
        
        # Recalculate integrity hash
        expected_hash = self._calculate_integrity_hash(event_for_hash)
        return event["integrity_hash"] == expected_hash
    
    def verify_chain_integrity(self) -> bool:
        """Verify integrity of the entire audit chain."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT audit_id, integrity_hash, previous_hash, chain_hash
                FROM audit_events ORDER BY created_at
            """)
            
            events = cursor.fetchall()
            if not events:
                return True
            
            # Verify each link in the chain
            for i, event in enumerate(events):
                # Verify individual event integrity
                if not self.verify_integrity(event["audit_id"]):
                    return False
                
                # Verify chain linking (skip first event)
                if i > 0:
                    previous_event = events[i-1]
                    if event["previous_hash"] != previous_event["integrity_hash"]:
                        return False
                    
                    # Verify chain hash
                    expected_chain_hash = self._calculate_chain_hash(
                        event["integrity_hash"], 
                        event["previous_hash"]
                    )
                    if event["chain_hash"] != expected_chain_hash:
                        return False
            
            return True
    
    def modify_event(self, audit_id: str, modifications: Dict[str, Any]):
        """Attempt to modify audit event - should always fail (immutable)."""
        raise ImmutableAuditError("Audit events are immutable and cannot be modified")
    
    def query_events(self, 
                    user_id: Optional[str] = None,
                    event_type: Optional[str] = None,
                    action_id: Optional[str] = None,
                    start_date: Optional[date] = None,
                    end_date: Optional[date] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query audit events with filtering options."""
        
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
            
        if action_id:
            query += " AND action_id = ?"
            params.append(action_id)
        
        if start_date:
            query += " AND date(timestamp) >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND date(timestamp) <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            
            events = []
            for row in results:
                event = dict(row)
                if event["details"]:
                    event["details"] = json.loads(event["details"])
                events.append(event)
            
            return events
    
    def generate_compliance_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Generate comprehensive compliance report from audit trail."""
        
        # Query events in date range
        events = self.query_events(start_date=start_date, end_date=end_date)
        
        # Calculate metrics
        total_actions = len([e for e in events if e["event_type"] == "action_created"])
        approval_events = [e for e in events if e["event_type"] == "approval_approved"]
        
        # Calculate approval rate
        approval_submissions = len([e for e in events if e["event_type"] == "approval_submitted"])
        approval_rate = len(approval_events) / approval_submissions if approval_submissions > 0 else 0
        
        # Calculate average approval time
        approval_times = []
        for approval in approval_events:
            # Find corresponding submission
            submission = next((e for e in events 
                             if e["event_type"] == "approval_submitted" 
                             and e["action_id"] == approval["action_id"]), None)
            if submission:
                submit_time = datetime.fromisoformat(submission["timestamp"])
                approve_time = datetime.fromisoformat(approval["timestamp"])
                approval_times.append((approve_time - submit_time).total_seconds() / 3600)  # hours
        
        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0
        
        # Check for compliance violations
        violations = [e for e in events if e["event_type"] == "compliance_violation"]
        
        # Verify audit trail integrity
        integrity_verified = self.verify_chain_integrity()
        
        return {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "total_actions": total_actions,
            "approval_rate": approval_rate,
            "average_approval_time": avg_approval_time,
            "compliance_violations": len(violations),
            "audit_trail_integrity": integrity_verified,
            "total_events": len(events),
            "event_types": {
                event_type: len([e for e in events if e["event_type"] == event_type])
                for event_type in set(e["event_type"] for e in events)
            },
            "generated_at": datetime.now().isoformat()
        }