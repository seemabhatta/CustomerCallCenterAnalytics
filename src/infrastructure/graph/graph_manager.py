"""
Knowledge Graph Manager 2.0 for Customer Call Center Analytics.

Enhanced graph management with comprehensive entity model and relationships.
NO FALLBACK PRINCIPLE: All graph operations must succeed or fail fast.
"""
import logging
import kuzu
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class GraphManagerError(Exception):
    """Exception raised for graph manager errors."""
    pass


class GraphManager:
    """
    Enhanced Knowledge Graph Manager for comprehensive customer analytics.

    Manages entities: Customer, Advisor, Supervisor, Transcript, Analysis,
    Resolution, Document, Loan, and their relationships.
    """

    def __init__(self, db_path: str = "data/knowledge_graph_v2.db"):
        """Initialize graph manager with enhanced schema."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.db = kuzu.Database(str(self.db_path))
            self.conn = kuzu.Connection(self.db)
            self._initialize_schema()
            logger.info(f"✅ GraphManager initialized: {self.db_path}")
        except Exception as e:
            raise GraphManagerError(f"Failed to initialize graph database: {e}")

    def _initialize_schema(self):
        """Create comprehensive graph schema for Knowledge Graph 2.0."""
        try:
            # Customer node - comprehensive customer profile
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Customer(
                    customer_id STRING PRIMARY KEY,
                    first_name STRING,
                    last_name STRING,
                    email STRING,
                    phone STRING,
                    risk_score DOUBLE DEFAULT 0.0,
                    satisfaction_score DOUBLE DEFAULT 0.0,
                    total_interactions INT64 DEFAULT 0,
                    last_contact_date TIMESTAMP,
                    status STRING DEFAULT 'active',
                    compliance_flags STRING[],
                    created_at TIMESTAMP DEFAULT current_timestamp(),
                    updated_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Advisor node - advisor profile and performance
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Advisor(
                    advisor_id STRING PRIMARY KEY,
                    name STRING,
                    email STRING,
                    department STRING,
                    skill_level STRING DEFAULT 'junior',
                    performance_score DOUBLE DEFAULT 0.0,
                    total_cases_handled INT64 DEFAULT 0,
                    escalation_rate DOUBLE DEFAULT 0.0,
                    avg_resolution_time_minutes DOUBLE DEFAULT 0.0,
                    customer_satisfaction_avg DOUBLE DEFAULT 0.0,
                    certifications STRING[],
                    hire_date TIMESTAMP,
                    status STRING DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT current_timestamp(),
                    updated_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Supervisor node - supervision and management
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Supervisor(
                    supervisor_id STRING PRIMARY KEY,
                    name STRING,
                    email STRING,
                    department STRING,
                    team_size INT64 DEFAULT 0,
                    total_escalations_handled INT64 DEFAULT 0,
                    avg_escalation_resolution_time DOUBLE DEFAULT 0.0,
                    team_performance_score DOUBLE DEFAULT 0.0,
                    status STRING DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT current_timestamp(),
                    updated_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Transcript node - enhanced conversation tracking
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Transcript(
                    transcript_id STRING PRIMARY KEY,
                    topic STRING,
                    urgency STRING,
                    channel STRING,
                    duration_minutes DOUBLE DEFAULT 0.0,
                    message_count INT64 DEFAULT 0,
                    status STRING DEFAULT 'active',
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Analysis node - AI analysis results
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Analysis(
                    analysis_id STRING PRIMARY KEY,
                    intent STRING,
                    urgency_level STRING,
                    sentiment STRING,
                    risk_score DOUBLE,
                    confidence_score DOUBLE,
                    compliance_flags STRING[],
                    key_topics STRING[],
                    processing_time_ms INT64,
                    created_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Resolution node - issue resolution tracking
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Resolution(
                    resolution_id STRING PRIMARY KEY,
                    method STRING,
                    resolution_time_minutes INT64,
                    customer_satisfaction DOUBLE,
                    resolution_type STRING,
                    outcome_status STRING DEFAULT 'resolved',
                    notes STRING,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Document node - document management
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Document(
                    document_id STRING PRIMARY KEY,
                    document_type STRING,
                    title STRING,
                    status STRING DEFAULT 'sent',
                    sent_at TIMESTAMP,
                    acknowledged_at TIMESTAMP,
                    acknowledgment_method STRING,
                    expiry_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Loan node - loan information
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Loan(
                    loan_id STRING PRIMARY KEY,
                    loan_type STRING,
                    principal_amount DOUBLE,
                    current_balance DOUBLE,
                    interest_rate DOUBLE,
                    payment_status STRING,
                    delinquency_days INT64 DEFAULT 0,
                    last_payment_date TIMESTAMP,
                    next_payment_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT current_timestamp(),
                    updated_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Issue node - specific issues and problems
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Issue(
                    issue_id STRING PRIMARY KEY,
                    issue_type STRING,
                    priority STRING,
                    description STRING,
                    status STRING DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT current_timestamp(),
                    resolved_at TIMESTAMP
                )
            """)

            # Workflow node - workflow and process tracking
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Workflow(
                    workflow_id STRING PRIMARY KEY,
                    workflow_type STRING,
                    status STRING DEFAULT 'active',
                    steps_completed INT64 DEFAULT 0,
                    total_steps INT64,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Create relationships
            self._create_relationships()

            logger.info("✅ Knowledge Graph 2.0 schema initialized")

        except Exception as e:
            raise GraphManagerError(f"Failed to initialize schema: {e}")

    def _create_relationships(self):
        """Create all relationship tables for the knowledge graph."""
        try:
            # Customer relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS OWNS(
                    FROM Customer TO Loan,
                    since TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS CONTACTED(
                    FROM Customer TO Advisor,
                    via_transcript STRING,
                    contact_date TIMESTAMP,
                    contact_channel STRING,
                    duration_minutes DOUBLE DEFAULT 0.0,
                    satisfaction_rating DOUBLE
                )
            """)

            # Advisor relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS HANDLES(
                    FROM Advisor TO Transcript,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    outcome STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS ESCALATES_TO(
                    FROM Advisor TO Supervisor,
                    via_workflow STRING,
                    escalation_reason STRING,
                    escalated_at TIMESTAMP,
                    resolved_at TIMESTAMP
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS RESOLVES(
                    FROM Advisor TO Issue,
                    via_resolution STRING,
                    resolution_time_minutes INT64,
                    satisfaction_score DOUBLE
                )
            """)

            # Supervisor relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS SUPERVISES(
                    FROM Supervisor TO Advisor,
                    since TIMESTAMP DEFAULT current_timestamp(),
                    performance_reviews INT64 DEFAULT 0
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS REVIEWS(
                    FROM Supervisor TO Resolution,
                    review_date TIMESTAMP,
                    approval_status STRING,
                    feedback STRING
                )
            """)

            # Transcript relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS ANALYZED_BY(
                    FROM Transcript TO Analysis,
                    analysis_date TIMESTAMP DEFAULT current_timestamp(),
                    processing_time_ms INT64
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS GENERATES(
                    FROM Transcript TO Issue,
                    identified_at TIMESTAMP DEFAULT current_timestamp(),
                    priority_level STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS TRIGGERS(
                    FROM Transcript TO Workflow,
                    trigger_reason STRING,
                    triggered_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Analysis relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS IDENTIFIES(
                    FROM Analysis TO Issue,
                    confidence_score DOUBLE,
                    risk_level STRING,
                    identified_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            # Document relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS SENT_TO(
                    FROM Document TO Customer,
                    sent_via STRING,
                    sent_at TIMESTAMP,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS GENERATED_FROM(
                    FROM Document TO Transcript,
                    generation_reason STRING,
                    generated_at TIMESTAMP DEFAULT current_timestamp()
                )
            """)

            logger.info("✅ Relationship tables created")

        except Exception as e:
            raise GraphManagerError(f"Failed to create relationships: {e}")

    # Entity creation and update methods
    def create_or_update_customer(self, customer_id: str, **kwargs) -> bool:
        """Create or update customer entity."""
        try:
            # Check if customer exists
            result = self.conn.execute(
                "MATCH (c:Customer {customer_id: $customer_id}) RETURN c.customer_id",
                {"customer_id": customer_id}
            )

            exists = len(result.get_as_df()) > 0

            if exists:
                # Update existing customer
                update_fields = []
                params = {"customer_id": customer_id, "updated_at": datetime.utcnow()}

                for key, value in kwargs.items():
                    if key not in ['customer_id', 'created_at']:
                        update_fields.append(f"c.{key} = ${key}")
                        params[key] = value

                if update_fields:
                    query = f"""
                        MATCH (c:Customer {{customer_id: $customer_id}})
                        SET {', '.join(update_fields)}, c.updated_at = $updated_at
                    """
                    self.conn.execute(query, params)
            else:
                # Create new customer
                params = {
                    "customer_id": customer_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                params.update(kwargs)

                query = "CREATE (:Customer $params)"
                self.conn.execute(query, {"params": params})

            logger.info(f"✅ Customer {'updated' if exists else 'created'}: {customer_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create/update customer {customer_id}: {e}")

    def create_or_update_advisor(self, advisor_id: str, **kwargs) -> bool:
        """Create or update advisor entity."""
        try:
            # Check if advisor exists
            result = self.conn.execute(
                "MATCH (a:Advisor {advisor_id: $advisor_id}) RETURN a.advisor_id",
                {"advisor_id": advisor_id}
            )

            exists = len(result.get_as_df()) > 0

            if exists:
                # Update existing advisor
                update_fields = []
                params = {"advisor_id": advisor_id, "updated_at": datetime.utcnow()}

                for key, value in kwargs.items():
                    if key not in ['advisor_id', 'created_at']:
                        update_fields.append(f"a.{key} = ${key}")
                        params[key] = value

                if update_fields:
                    query = f"""
                        MATCH (a:Advisor {{advisor_id: $advisor_id}})
                        SET {', '.join(update_fields)}, a.updated_at = $updated_at
                    """
                    self.conn.execute(query, params)
            else:
                # Create new advisor
                params = {
                    "advisor_id": advisor_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                params.update(kwargs)

                query = "CREATE (:Advisor $params)"
                self.conn.execute(query, {"params": params})

            logger.info(f"✅ Advisor {'updated' if exists else 'created'}: {advisor_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create/update advisor {advisor_id}: {e}")

    def create_or_update_supervisor(self, supervisor_id: str, **kwargs) -> bool:
        """Create or update supervisor entity."""
        try:
            # Check if supervisor exists
            result = self.conn.execute(
                "MATCH (s:Supervisor {supervisor_id: $supervisor_id}) RETURN s.supervisor_id",
                {"supervisor_id": supervisor_id}
            )

            exists = len(result.get_as_df()) > 0

            if exists:
                # Update existing supervisor
                update_fields = []
                params = {"supervisor_id": supervisor_id, "updated_at": datetime.utcnow()}

                for key, value in kwargs.items():
                    if key not in ['supervisor_id', 'created_at']:
                        update_fields.append(f"s.{key} = ${key}")
                        params[key] = value

                if update_fields:
                    query = f"""
                        MATCH (s:Supervisor {{supervisor_id: $supervisor_id}})
                        SET {', '.join(update_fields)}, s.updated_at = $updated_at
                    """
                    self.conn.execute(query, params)
            else:
                # Create new supervisor
                params = {
                    "supervisor_id": supervisor_id,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                params.update(kwargs)

                query = "CREATE (:Supervisor $params)"
                self.conn.execute(query, {"params": params})

            logger.info(f"✅ Supervisor {'updated' if exists else 'created'}: {supervisor_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create/update supervisor {supervisor_id}: {e}")

    def create_transcript(self, transcript_id: str, customer_id: str, advisor_id: str,
                         topic: str, urgency: str, channel: str, started_at: datetime,
                         status: str = 'active', **kwargs) -> bool:
        """Create transcript with relationships."""
        try:
            # Create transcript node
            params = {
                "transcript_id": transcript_id,
                "topic": topic,
                "urgency": urgency,
                "channel": channel,
                "status": status,
                "started_at": started_at,
                "created_at": datetime.utcnow()
            }
            params.update(kwargs)

            self.conn.execute("CREATE (:Transcript $params)", {"params": params})

            # Create relationships
            # Customer -> contacted -> Advisor
            self.conn.execute("""
                MATCH (c:Customer {customer_id: $customer_id}), (a:Advisor {advisor_id: $advisor_id})
                CREATE (c)-[:CONTACTED {via_transcript: $transcript_id, contact_date: $started_at, contact_channel: $channel}]->(a)
            """, {
                "customer_id": customer_id,
                "advisor_id": advisor_id,
                "transcript_id": transcript_id,
                "started_at": started_at,
                "channel": channel
            })

            # Advisor -> handles -> Transcript
            self.conn.execute("""
                MATCH (a:Advisor {advisor_id: $advisor_id}), (t:Transcript {transcript_id: $transcript_id})
                CREATE (a)-[:HANDLES {started_at: $started_at}]->(t)
            """, {
                "advisor_id": advisor_id,
                "transcript_id": transcript_id,
                "started_at": started_at
            })

            logger.info(f"✅ Transcript created with relationships: {transcript_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create transcript {transcript_id}: {e}")

    def create_analysis(self, analysis_id: str, transcript_id: str, intent: str,
                       urgency_level: str, sentiment: str, risk_score: float,
                       compliance_flags: List[str], confidence_score: float, **kwargs) -> bool:
        """Create analysis node with relationship to transcript."""
        try:
            # Create analysis node
            params = {
                "analysis_id": analysis_id,
                "intent": intent,
                "urgency_level": urgency_level,
                "sentiment": sentiment,
                "risk_score": risk_score,
                "confidence_score": confidence_score,
                "compliance_flags": compliance_flags,
                "created_at": datetime.utcnow()
            }
            params.update(kwargs)

            self.conn.execute("CREATE (:Analysis $params)", {"params": params})

            # Create relationship: Transcript -> analyzed_by -> Analysis
            self.conn.execute("""
                MATCH (t:Transcript {transcript_id: $transcript_id}), (a:Analysis {analysis_id: $analysis_id})
                CREATE (t)-[:ANALYZED_BY {analysis_date: $analysis_date}]->(a)
            """, {
                "transcript_id": transcript_id,
                "analysis_id": analysis_id,
                "analysis_date": datetime.utcnow()
            })

            logger.info(f"✅ Analysis created with relationship: {analysis_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create analysis {analysis_id}: {e}")

    # Additional methods for escalations, resolutions, documents, etc.
    def create_escalation(self, workflow_id: str, from_advisor: str, to_supervisor: str,
                         reason: str, urgency_level: str, escalated_at: datetime) -> bool:
        """Create escalation relationship between advisor and supervisor."""
        try:
            self.conn.execute("""
                MATCH (a:Advisor {advisor_id: $from_advisor}), (s:Supervisor {supervisor_id: $to_supervisor})
                CREATE (a)-[:ESCALATES_TO {
                    via_workflow: $workflow_id,
                    escalation_reason: $reason,
                    escalated_at: $escalated_at
                }]->(s)
            """, {
                "from_advisor": from_advisor,
                "to_supervisor": to_supervisor,
                "workflow_id": workflow_id,
                "reason": reason,
                "escalated_at": escalated_at
            })

            logger.info(f"✅ Escalation created: {from_advisor} -> {to_supervisor}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create escalation: {e}")

    def create_resolution(self, resolution_id: str, issue_id: str, resolved_by_advisor: str,
                         resolved_by_supervisor: Optional[str], method: str,
                         resolution_time_minutes: int, customer_satisfaction: Optional[float],
                         resolved_at: datetime) -> bool:
        """Create resolution node and relationships."""
        try:
            # Create resolution node
            params = {
                "resolution_id": resolution_id,
                "method": method,
                "resolution_time_minutes": resolution_time_minutes,
                "customer_satisfaction": customer_satisfaction,
                "resolved_at": resolved_at,
                "created_at": datetime.utcnow()
            }

            self.conn.execute("CREATE (:Resolution $params)", {"params": params})

            # Create advisor -> resolves -> issue relationship
            self.conn.execute("""
                MATCH (a:Advisor {advisor_id: $advisor_id}), (i:Issue {issue_id: $issue_id})
                CREATE (a)-[:RESOLVES {
                    via_resolution: $resolution_id,
                    resolution_time_minutes: $resolution_time_minutes,
                    satisfaction_score: $customer_satisfaction
                }]->(i)
            """, {
                "advisor_id": resolved_by_advisor,
                "issue_id": issue_id,
                "resolution_id": resolution_id,
                "resolution_time_minutes": resolution_time_minutes,
                "customer_satisfaction": customer_satisfaction
            })

            if resolved_by_supervisor:
                # Create supervisor review relationship
                self.conn.execute("""
                    MATCH (s:Supervisor {supervisor_id: $supervisor_id}), (r:Resolution {resolution_id: $resolution_id})
                    CREATE (s)-[:REVIEWS {
                        review_date: $resolved_at,
                        approval_status: 'approved'
                    }]->(r)
                """, {
                    "supervisor_id": resolved_by_supervisor,
                    "resolution_id": resolution_id,
                    "resolved_at": resolved_at
                })

            logger.info(f"✅ Resolution created: {resolution_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create resolution {resolution_id}: {e}")

    def create_document_acknowledgment(self, document_id: str, customer_id: str,
                                     document_type: str, sent_at: datetime,
                                     acknowledged_at: datetime, method: str) -> bool:
        """Create document and acknowledgment relationship."""
        try:
            # Create document node
            params = {
                "document_id": document_id,
                "document_type": document_type,
                "status": "acknowledged",
                "sent_at": sent_at,
                "acknowledged_at": acknowledged_at,
                "acknowledgment_method": method,
                "created_at": datetime.utcnow()
            }

            self.conn.execute("CREATE (:Document $params)", {"params": params})

            # Create document -> sent_to -> customer relationship
            self.conn.execute("""
                MATCH (d:Document {document_id: $document_id}), (c:Customer {customer_id: $customer_id})
                CREATE (d)-[:SENT_TO {
                    sent_via: $method,
                    sent_at: $sent_at,
                    acknowledged: TRUE
                }]->(c)
            """, {
                "document_id": document_id,
                "customer_id": customer_id,
                "method": method,
                "sent_at": sent_at
            })

            logger.info(f"✅ Document acknowledgment created: {document_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to create document acknowledgment {document_id}: {e}")

    # Analytics and metrics methods
    def update_customer_risk_profile(self, customer_id: str, risk_score: float,
                                   compliance_flags: List[str]) -> bool:
        """Update customer risk profile based on analysis."""
        try:
            self.conn.execute("""
                MATCH (c:Customer {customer_id: $customer_id})
                SET c.risk_score = $risk_score,
                    c.compliance_flags = $compliance_flags,
                    c.updated_at = $updated_at
            """, {
                "customer_id": customer_id,
                "risk_score": risk_score,
                "compliance_flags": compliance_flags,
                "updated_at": datetime.utcnow()
            })

            logger.info(f"✅ Customer risk profile updated: {customer_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to update customer risk profile {customer_id}: {e}")

    def update_advisor_escalation_metrics(self, advisor_id: str) -> bool:
        """Update advisor escalation metrics."""
        try:
            # Calculate escalation rate
            self.conn.execute("""
                MATCH (a:Advisor {advisor_id: $advisor_id})
                OPTIONAL MATCH (a)-[e:ESCALATES_TO]->()
                OPTIONAL MATCH (a)-[h:HANDLES]->()
                WITH a, COUNT(e) as escalations, COUNT(h) as total_cases
                SET a.escalation_rate = CASE WHEN total_cases > 0 THEN toFloat(escalations) / toFloat(total_cases) ELSE 0.0 END,
                    a.updated_at = $updated_at
            """, {
                "advisor_id": advisor_id,
                "updated_at": datetime.utcnow()
            })

            logger.info(f"✅ Advisor escalation metrics updated: {advisor_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to update advisor metrics {advisor_id}: {e}")

    def update_advisor_resolution_metrics(self, advisor_id: str, resolution_time: int,
                                        satisfaction_score: Optional[float]) -> bool:
        """Update advisor resolution metrics."""
        try:
            self.conn.execute("""
                MATCH (a:Advisor {advisor_id: $advisor_id})
                OPTIONAL MATCH (a)-[r:RESOLVES]->()
                WITH a, AVG(r.resolution_time_minutes) as avg_time, AVG(r.satisfaction_score) as avg_satisfaction
                SET a.avg_resolution_time_minutes = avg_time,
                    a.customer_satisfaction_avg = avg_satisfaction,
                    a.updated_at = $updated_at
            """, {
                "advisor_id": advisor_id,
                "updated_at": datetime.utcnow()
            })

            logger.info(f"✅ Advisor resolution metrics updated: {advisor_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to update advisor resolution metrics {advisor_id}: {e}")

    def update_supervisor_metrics(self, supervisor_id: str) -> bool:
        """Update supervisor performance metrics."""
        try:
            self.conn.execute("""
                MATCH (s:Supervisor {supervisor_id: $supervisor_id})
                OPTIONAL MATCH (s)<-[e:ESCALATES_TO]-()
                OPTIONAL MATCH (s)-[r:REVIEWS]->()
                WITH s, COUNT(e) as escalations, COUNT(r) as reviews
                SET s.total_escalations_handled = escalations,
                    s.updated_at = $updated_at
            """, {
                "supervisor_id": supervisor_id,
                "updated_at": datetime.utcnow()
            })

            logger.info(f"✅ Supervisor metrics updated: {supervisor_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to update supervisor metrics {supervisor_id}: {e}")

    def update_customer_engagement_metrics(self, customer_id: str) -> bool:
        """Update customer engagement metrics."""
        try:
            self.conn.execute("""
                MATCH (c:Customer {customer_id: $customer_id})
                OPTIONAL MATCH (c)<-[contacted:CONTACTED]-()
                OPTIONAL MATCH (c)<-[sent:SENT_TO]-()
                WITH c, COUNT(contacted) as interactions, COUNT(sent) as documents
                SET c.total_interactions = interactions,
                    c.updated_at = $updated_at
            """, {
                "customer_id": customer_id,
                "updated_at": datetime.utcnow()
            })

            logger.info(f"✅ Customer engagement metrics updated: {customer_id}")
            return True

        except Exception as e:
            raise GraphManagerError(f"Failed to update customer engagement metrics {customer_id}: {e}")

    def close(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
        logger.info("✅ GraphManager connection closed")


# Global graph manager instance
_global_graph_manager: Optional[GraphManager] = None


def get_graph_manager() -> GraphManager:
    """Get the global graph manager instance (singleton)."""
    global _global_graph_manager

    if _global_graph_manager is None:
        _global_graph_manager = GraphManager()

    return _global_graph_manager


# Export for easy access
__all__ = [
    'GraphManager',
    'GraphManagerError',
    'get_graph_manager'
]