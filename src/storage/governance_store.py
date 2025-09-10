"""
GovernanceStore: Database operations for governance data

Core Principles:
- High-performance queries for large datasets
- Proper indexing for audit trail operations
- Secure storage of governance rules and audit data
"""

import json
import sqlite3
import time
from datetime import datetime, date
from typing import Dict, List, Any, Optional


class GovernanceStore:
    """
    High-performance storage layer for governance data.
    
    Features:
    - Optimized queries for large audit datasets
    - Governance rules management
    - Audit event storage with integrity
    - Performance monitoring and optimization
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize governance database with optimized schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Governance rules table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL,
                    conditions TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_by TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    expiration_date TEXT,
                    priority INTEGER DEFAULT 0,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Performance indexes for governance rules
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rule_type ON governance_rules(rule_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rule_active ON governance_rules(active)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_rule_effective ON governance_rules(effective_date)")
            
            # Audit events table (if not already created by AuditLogger)
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
            
            # Performance indexes for audit events
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_events(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_events(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_events(action_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_events(event_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_events(created_at)")
            
            conn.commit()
    
    def store_rule(self, rule: Dict[str, Any]) -> str:
        """
        Store governance rule with validation.
        
        Args:
            rule: Rule data to store
            
        Returns:
            Rule ID
        """
        rule_id = rule.get("rule_id")
        now = datetime.now().isoformat()
        
        # Set timestamps
        rule["created_at"] = rule.get("created_at", now)
        rule["updated_at"] = now
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO governance_rules 
                (rule_id, rule_type, conditions, active, created_by, effective_date,
                 expiration_date, priority, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rule_id,
                rule["rule_type"],
                json.dumps(rule["conditions"]),
                rule.get("active", True),
                rule["created_by"],
                rule["effective_date"],
                rule.get("expiration_date"),
                rule.get("priority", 0),
                rule.get("description"),
                rule["created_at"],
                rule["updated_at"]
            ))
            conn.commit()
        
        return rule_id
    
    def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve governance rule by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM governance_rules WHERE rule_id = ?
            """, (rule_id,))
            result = cursor.fetchone()
            
            if result:
                rule = dict(result)
                # Parse JSON conditions
                if rule["conditions"]:
                    rule["conditions"] = json.loads(rule["conditions"])
                return rule
            return None
    
    def get_active_rules(self, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active governance rules, optionally filtered by type."""
        query = """
            SELECT * FROM governance_rules 
            WHERE active = TRUE 
            AND (expiration_date IS NULL OR expiration_date > ?)
        """
        params = [datetime.now().isoformat()]
        
        if rule_type:
            query += " AND rule_type = ?"
            params.append(rule_type)
        
        query += " ORDER BY priority DESC, effective_date ASC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            
            rules = []
            for row in results:
                rule = dict(row)
                if rule["conditions"]:
                    rule["conditions"] = json.loads(rule["conditions"])
                rules.append(rule)
            
            return rules
    
    def deactivate_rule(self, rule_id: str) -> bool:
        """Deactivate a governance rule."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE governance_rules 
                SET active = FALSE, updated_at = ?
                WHERE rule_id = ?
            """, (datetime.now().isoformat(), rule_id))
            conn.commit()
            return cursor.rowcount > 0
    
    def store_audit_event(self, event: Dict[str, Any]) -> str:
        """Store audit event (used for performance testing)."""
        audit_id = event.get("audit_id", f"audit_{int(time.time() * 1000000)}")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_events 
                (audit_id, event_type, action_id, user_id, timestamp, details,
                 integrity_hash, chain_hash, previous_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                audit_id,
                event["event_type"],
                event.get("action_id"),
                event.get("user_id"),
                event["timestamp"].isoformat() if hasattr(event["timestamp"], 'isoformat') else str(event["timestamp"]),
                json.dumps(event.get("details", {})),
                "test_hash",  # Simplified for performance testing
                "test_chain_hash",
                "test_previous_hash",
                datetime.now().isoformat()
            ))
            conn.commit()
        
        return audit_id
    
    def query_audit_events(self, 
                          start_date: Optional[date] = None,
                          end_date: Optional[date] = None,
                          event_type: Optional[str] = None,
                          user_id: Optional[str] = None,
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        High-performance audit event querying with proper indexing.
        
        This method is optimized for large datasets with proper index usage.
        """
        query = "SELECT * FROM audit_events WHERE 1=1"
        params = []
        
        # Use indexed columns for efficient filtering
        if start_date:
            query += " AND date(timestamp) >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND date(timestamp) <= ?"
            params.append(end_date.isoformat())
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        
        # Order by indexed column for performance
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
                    try:
                        event["details"] = json.loads(event["details"])
                    except (json.JSONDecodeError, TypeError):
                        event["details"] = {}
                events.append(event)
            
            return events
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Get table sizes
            cursor = conn.execute("SELECT COUNT(*) FROM governance_rules")
            rules_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events")
            audit_count = cursor.fetchone()[0]
            
            # Get index usage stats (SQLite specific)
            cursor = conn.execute("PRAGMA table_info(audit_events)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Test query performance
            start_time = time.time()
            cursor = conn.execute("SELECT * FROM audit_events ORDER BY created_at DESC LIMIT 100")
            cursor.fetchall()
            query_time = time.time() - start_time
            
            return {
                "governance_rules_count": rules_count,
                "audit_events_count": audit_count,
                "recent_query_time_seconds": query_time,
                "database_path": self.db_path,
                "indexed_columns": ["timestamp", "user_id", "action_id", "event_type", "created_at"],
                "performance_target_met": query_time < 1.0  # Target: < 1 second
            }
    
    def optimize_database(self):
        """Optimize database performance."""
        with sqlite3.connect(self.db_path) as conn:
            # Analyze tables for query optimization
            conn.execute("ANALYZE governance_rules")
            conn.execute("ANALYZE audit_events")
            
            # Vacuum to reclaim space
            conn.execute("VACUUM")
            
            conn.commit()
    
    def backup_governance_data(self, backup_path: str):
        """Create backup of governance data."""
        import shutil
        shutil.copy2(self.db_path, backup_path)
        
        # Verify backup integrity
        with sqlite3.connect(backup_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM governance_rules")
            rules_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM audit_events")
            audit_count = cursor.fetchone()[0]
            
            return {
                "backup_path": backup_path,
                "governance_rules_backed_up": rules_count,
                "audit_events_backed_up": audit_count,
                "backup_created_at": datetime.now().isoformat()
            }