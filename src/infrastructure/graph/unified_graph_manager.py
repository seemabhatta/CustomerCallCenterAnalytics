"""
Unified Knowledge Graph Manager - Combines business entities and learning nodes.

Merges GraphManager and PredictiveGraphManager into single system that handles:
- Business entities: Customer, Advisor, Call, Loan, etc.
- Learning nodes: Pattern, Prediction, Wisdom, MetaLearning
- Cross-domain relationships between business and learning
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import kuzu
import uuid
import json

from .knowledge_types import Pattern, Prediction, Wisdom, MetaLearning

logger = logging.getLogger(__name__)

# Global database instance to ensure only one database connection system-wide
_global_database = None
_global_database_path = None

def _get_global_database(db_path: str):
    """Get or create the global database instance."""
    global _global_database, _global_database_path

    if _global_database is None or _global_database_path != db_path:
        logger.info(f"🔄 Creating global database instance: {db_path}")
        _global_database = kuzu.Database(db_path)
        _global_database_path = db_path

    return _global_database


class UnifiedGraphManagerError(Exception):
    """Exception raised for unified graph manager errors."""
    pass


class UnifiedGraphManager:
    """
    Unified Knowledge Graph Manager combining business entities and learning nodes.

    Manages both operational entities (Customer, Advisor, Call) and intelligence
    nodes (Pattern, Prediction, Wisdom) in a single connected graph.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from ..config.database_config import get_knowledge_graph_database_path
            db_path = get_knowledge_graph_database_path()

        self.db_path = db_path

        # Use global database instance to prevent multiple database handles
        self.db = _get_global_database(db_path)

        # Single connection for ALL operations (reads and writes)
        # This eliminates transaction conflicts by using only one connection
        self.conn = kuzu.Connection(self.db)

        # Remove connection pool entirely - source of conflicts
        # self._connection_pool = []  # REMOVED
        # self._available_connections = None  # REMOVED

        # Single threaded executor for database operations
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="unified_kuzu_single")

        # Write queue system to serialize ALL operations (not just writes)
        self._write_queue = None  # Lazy-initialized in async context
        self._write_processor_task = None  # Background task for processing operations
        self._operation_counter = 0  # For unique operation IDs

        # Schema initialization flag
        self._schema_initialized = False

        # Don't initialize schema immediately - defer to write queue

    def _init_unified_schema(self) -> None:
        """Initialize unified schema with both business entities and learning nodes."""
        try:
            # === BUSINESS ENTITIES ===

            # Customer node
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
                    last_contact_date STRING,
                    status STRING DEFAULT 'active',
                    compliance_flags STRING,
                    created_at STRING,
                    updated_at STRING
                )
            """)

            # Call node (replacing Transcript for simplicity)
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Call(
                    call_id STRING PRIMARY KEY,
                    transcript_id STRING,
                    customer_id STRING,
                    advisor_id STRING,
                    topic STRING,
                    duration_minutes DOUBLE DEFAULT 0.0,
                    urgency_level STRING DEFAULT 'medium',
                    sentiment STRING DEFAULT 'neutral',
                    resolved BOOLEAN DEFAULT FALSE,
                    escalated BOOLEAN DEFAULT FALSE,
                    call_date STRING,
                    created_at STRING,
                    analysis_id STRING,
                    intent STRING,
                    confidence_score DOUBLE DEFAULT 0.0
                )
            """)

            # Advisor node
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
                    certifications STRING,
                    hire_date STRING,
                    status STRING DEFAULT 'active',
                    created_at STRING,
                    updated_at STRING
                )
            """)

            # Loan node
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Loan(
                    loan_id STRING PRIMARY KEY,
                    customer_id STRING,
                    loan_type STRING DEFAULT 'mortgage',
                    principal_amount DOUBLE,
                    current_balance DOUBLE,
                    interest_rate DOUBLE,
                    loan_status STRING DEFAULT 'active',
                    origination_date STRING,
                    maturity_date STRING,
                    has_pmi BOOLEAN DEFAULT FALSE,
                    current_ltv DOUBLE,
                    created_at STRING
                )
            """)

            # === LEARNING NODES ===

            # Pattern node
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Pattern(
                    pattern_id STRING PRIMARY KEY,
                    pattern_type STRING,
                    title STRING,
                    description STRING,
                    conditions STRING,
                    outcomes STRING,
                    confidence DOUBLE,
                    occurrences INT64,
                    success_rate DOUBLE,
                    last_observed STRING,
                    source_pipeline STRING
                )
            """)

            # Prediction node
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Prediction(
                    prediction_id STRING PRIMARY KEY,
                    prediction_type STRING,
                    target_entity STRING,
                    target_entity_id STRING,
                    predicted_event STRING,
                    probability DOUBLE,
                    confidence DOUBLE,
                    time_horizon STRING,
                    supporting_patterns STRING,
                    evidence_strength DOUBLE,
                    created_at STRING,
                    expires_at STRING,
                    validated BOOLEAN,
                    validation_date STRING
                )
            """)

            # Wisdom node
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Wisdom(
                    wisdom_id STRING PRIMARY KEY,
                    wisdom_type STRING,
                    domain STRING,
                    insight STRING,
                    applications STRING,
                    success_indicators STRING,
                    derived_from_patterns STRING,
                    evidence_base STRING,
                    confidence_level DOUBLE,
                    discovered_at STRING,
                    times_applied INT64,
                    application_success_rate DOUBLE
                )
            """)

            # MetaLearning node
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS MetaLearning(
                    meta_id STRING PRIMARY KEY,
                    meta_type STRING,
                    learning_insight STRING,
                    improvement_opportunity STRING,
                    optimization_suggestion STRING,
                    accuracy_metrics STRING,
                    learning_velocity DOUBLE,
                    knowledge_gaps STRING,
                    observed_at STRING,
                    system_version STRING
                )
            """)

            # === BUSINESS RELATIONSHIPS ===

            # Customer relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS HAS_LOAN(
                    FROM Customer TO Loan,
                    since STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS MADE_CALL(
                    FROM Customer TO Call,
                    contact_date STRING
                )
            """)

            # Call relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS HANDLED_BY(
                    FROM Call TO Advisor,
                    started_at STRING,
                    completed_at STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS ABOUT_LOAN(
                    FROM Call TO Loan,
                    related_topic STRING
                )
            """)

            # === LEARNING RELATIONSHIPS ===

            # Pattern relationships
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS SUPPORTS(
                    FROM Pattern TO Prediction,
                    strength DOUBLE,
                    evidence_type STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS DERIVES_FROM(
                    FROM Wisdom TO Pattern,
                    derivation_confidence DOUBLE
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS IMPROVES(
                    FROM MetaLearning TO Wisdom,
                    improvement_type STRING,
                    expected_impact DOUBLE
                )
            """)

            # === CROSS-DOMAIN RELATIONSHIPS ===

            # Business to Learning connections
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS GENERATES_PATTERN(
                    FROM Call TO Pattern,
                    pattern_strength DOUBLE,
                    generated_at STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS TARGETS_CUSTOMER(
                    FROM Prediction TO Customer,
                    prediction_scope STRING,
                    target_date STRING
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS LEARNED_BY_ADVISOR(
                    FROM Pattern TO Advisor,
                    learning_date STRING,
                    application_count INT64
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS TRIGGERS_LEARNING(
                    FROM Call TO MetaLearning,
                    learning_type STRING,
                    trigger_reason STRING
                )
            """)

            logger.info("✅ Unified Knowledge Graph schema initialized")

        except Exception as e:
            logger.error(f"Failed to initialize unified schema: {e}")
            raise UnifiedGraphManagerError(f"Schema initialization failed: {str(e)}")

    # Connection pool methods removed - using single connection only

    def _is_write_operation(self, query: str) -> bool:
        """Check if the query is a write operation (kept for compatibility)."""
        query_upper = query.strip().upper()
        write_operations = ['CREATE', 'MERGE', 'SET', 'DELETE', 'REMOVE', 'ALTER', 'DROP']
        return any(query_upper.startswith(op) for op in write_operations)

    async def _execute_async(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Execute ALL KuzuDB operations through the queue for complete serialization."""
        # Queue ALL operations (reads and writes) to prevent any transaction conflicts
        return await self._queue_write_operation(query, parameters)

    # _execute_query method removed - all operations go through queue

    # === WRITE QUEUE SYSTEM ===

    async def _initialize_write_queue(self):
        """Initialize the write queue and start the processor task."""
        if self._write_queue is None:
            self._write_queue = asyncio.Queue()
            self._write_processor_task = asyncio.create_task(self._process_write_queue())
            logger.info("🔄 Write queue processor started")

    async def _process_write_queue(self):
        """Background task that processes write operations sequentially."""
        logger.info("🔄 Write queue processor started")
        while True:
            try:
                # Get next write operation from queue
                operation = await self._write_queue.get()

                # Handle shutdown signal
                if operation is None:
                    logger.info("🔄 Write queue processor shutting down")
                    break

                try:
                    # Execute on single connection (no more dedicated write connection)
                    if operation['parameters']:
                        result = self.conn.execute(operation['query'], parameters=operation['parameters'])
                    else:
                        result = self.conn.execute(operation['query'])

                    # Return result to waiting coroutine
                    operation['future'].set_result(result)

                except Exception as e:
                    # NO FALLBACK: Fail fast on errors
                    error = RuntimeError(f"KuzuDB operation failed: {str(e)}")
                    operation['future'].set_exception(error)

                finally:
                    # Mark task as done
                    self._write_queue.task_done()

            except Exception as e:
                # Log unexpected errors but keep processor running
                logger.error(f"Write queue processor error: {e}")

    async def _queue_write_operation(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Queue a write operation and wait for its result."""
        # Lazy-initialize the write queue and schema
        if self._write_queue is None:
            await self._initialize_write_queue()

        # Ensure schema is initialized before any operation
        if not self._schema_initialized:
            await self._initialize_schema_async()

        # Create a future for the result
        future = asyncio.Future()

        # Create operation dict
        self._operation_counter += 1
        operation = {
            'id': self._operation_counter,
            'query': query,
            'parameters': parameters,
            'future': future
        }

        # Add to queue
        await self._write_queue.put(operation)

        # Wait for result
        return await future

    async def _shutdown_write_queue(self):
        """Shutdown the write queue processor."""
        if self._write_queue is not None and self._write_processor_task is not None:
            # Signal shutdown
            await self._write_queue.put(None)
            # Wait for processor to finish
            await self._write_processor_task
            logger.info("🔄 Write queue processor stopped")

    async def _initialize_schema_async(self):
        """Initialize schema through the write queue to avoid transaction conflicts."""
        if self._schema_initialized:
            return

        logger.info("🔄 Initializing database schema through write queue...")

        # Queue all schema creation operations
        schema_operations = [
            # Customer node
            """CREATE NODE TABLE IF NOT EXISTS Customer(
                customer_id STRING PRIMARY KEY,
                first_name STRING,
                last_name STRING,
                email STRING,
                phone STRING,
                risk_score DOUBLE DEFAULT 0.0,
                satisfaction_score DOUBLE DEFAULT 0.0,
                total_interactions INT64 DEFAULT 0,
                last_contact_date STRING,
                status STRING DEFAULT 'active',
                compliance_flags STRING,
                created_at STRING,
                updated_at STRING
            )""",

            # Call node
            """CREATE NODE TABLE IF NOT EXISTS Call(
                call_id STRING PRIMARY KEY,
                transcript_id STRING,
                customer_id STRING,
                advisor_id STRING,
                topic STRING,
                duration_minutes DOUBLE DEFAULT 0.0,
                urgency_level STRING DEFAULT 'medium',
                sentiment STRING DEFAULT 'neutral',
                resolved BOOLEAN DEFAULT FALSE,
                escalated BOOLEAN DEFAULT FALSE,
                call_date STRING,
                created_at STRING,
                analysis_id STRING,
                intent STRING,
                confidence_score DOUBLE DEFAULT 0.0
            )""",

            # Advisor node
            """CREATE NODE TABLE IF NOT EXISTS Advisor(
                advisor_id STRING PRIMARY KEY,
                name STRING,
                email STRING,
                department STRING,
                skill_level STRING DEFAULT 'junior',
                performance_score DOUBLE DEFAULT 0.0,
                total_cases_handled INT64 DEFAULT 0,
                escalation_rate DOUBLE DEFAULT 0.0,
                certifications STRING,
                hire_date STRING,
                status STRING DEFAULT 'active',
                created_at STRING,
                updated_at STRING
            )""",

            # Pattern node
            """CREATE NODE TABLE IF NOT EXISTS Pattern(
                pattern_id STRING PRIMARY KEY,
                pattern_type STRING,
                title STRING,
                description STRING,
                conditions STRING,
                outcomes STRING,
                confidence DOUBLE DEFAULT 0.0,
                occurrences INT64 DEFAULT 0,
                success_rate DOUBLE DEFAULT 0.0,
                last_observed STRING,
                source_pipeline STRING,
                created_at STRING
            )""",
        ]

        # Execute schema operations through write queue
        for operation in schema_operations:
            try:
                # Create a future for this schema operation
                future = asyncio.Future()

                self._operation_counter += 1
                schema_op = {
                    'id': self._operation_counter,
                    'query': operation,
                    'parameters': None,
                    'future': future
                }

                # Add directly to queue (bypassing _queue_write_operation to avoid recursion)
                await self._write_queue.put(schema_op)
                await future  # Wait for completion

            except Exception as e:
                logger.error(f"Failed to create schema: {e}")
                raise RuntimeError(f"Schema initialization failed: {str(e)}")

        # Create relationships
        relationship_operations = [
            "CREATE REL TABLE IF NOT EXISTS MADE_CALL(FROM Customer TO Call)",
            "CREATE REL TABLE IF NOT EXISTS HANDLED_BY(FROM Call TO Advisor)",
            "CREATE REL TABLE IF NOT EXISTS GENERATES_PATTERN(FROM Call TO Pattern)",
            "CREATE REL TABLE IF NOT EXISTS LEARNED_BY_ADVISOR(FROM Pattern TO Advisor, learning_date STRING, application_count INT64 DEFAULT 0)"
        ]

        for operation in relationship_operations:
            try:
                # Create a future for this relationship operation
                future = asyncio.Future()

                self._operation_counter += 1
                rel_op = {
                    'id': self._operation_counter,
                    'query': operation,
                    'parameters': None,
                    'future': future
                }

                await self._write_queue.put(rel_op)
                await future  # Wait for completion

            except Exception as e:
                logger.error(f"Failed to create relationships: {e}")
                raise RuntimeError(f"Relationship creation failed: {str(e)}")

        self._schema_initialized = True
        logger.info("✅ Database schema initialized successfully through write queue")

    # === BUSINESS ENTITY METHODS ===

    async def create_or_update_customer(self, customer_id: str, **kwargs) -> bool:
        """Create or update customer in the unified graph."""
        try:
            # Check if customer exists
            result = await self._execute_async(
                "MATCH (c:Customer {customer_id: $customer_id}) RETURN c.customer_id",
                {"customer_id": customer_id}
            )

            exists = result.has_next()

            if exists:
                # Update existing customer
                update_fields = []
                params = {"customer_id": customer_id, "updated_at": datetime.utcnow().isoformat()}

                for key, value in kwargs.items():
                    if key not in ['customer_id', 'created_at']:
                        update_fields.append(f"c.{key} = ${key}")
                        params[key] = value

                if update_fields:
                    query = f"""
                        MATCH (c:Customer {{customer_id: $customer_id}})
                        SET {', '.join(update_fields)}, c.updated_at = $updated_at
                    """
                    await self._execute_async(query, params)
            else:
                # Create new customer
                params = {
                    "customer_id": customer_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                params.update(kwargs)

                # Convert any complex objects to strings
                for key, value in params.items():
                    if isinstance(value, (dict, list)):
                        params[key] = json.dumps(value)

                await self._execute_async("""
                    CREATE (:Customer {
                        customer_id: $customer_id,
                        first_name: $first_name,
                        last_name: $last_name,
                        email: $email,
                        phone: $phone,
                        risk_score: $risk_score,
                        satisfaction_score: $satisfaction_score,
                        total_interactions: $total_interactions,
                        last_contact_date: $last_contact_date,
                        status: $status,
                        compliance_flags: $compliance_flags,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                """, {
                    'customer_id': customer_id,
                    'first_name': params.get('first_name', ''),
                    'last_name': params.get('last_name', ''),
                    'email': params.get('email', ''),
                    'phone': params.get('phone', ''),
                    'risk_score': params.get('risk_score', 0.0),
                    'satisfaction_score': params.get('satisfaction_score', 0.0),
                    'total_interactions': params.get('total_interactions', 0),
                    'last_contact_date': params.get('last_contact_date', datetime.utcnow().isoformat()),
                    'status': params.get('status', 'active'),
                    'compliance_flags': params.get('compliance_flags', '[]'),
                    'created_at': params['created_at'],
                    'updated_at': params['updated_at']
                })

            logger.info(f"✅ Customer {'updated' if exists else 'created'}: {customer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create/update customer {customer_id}: {e}")
            raise UnifiedGraphManagerError(f"Customer operation failed: {str(e)}")

    async def create_call_node(self, call_id: str, transcript_id: str, customer_id: str,
                              advisor_id: str = None, **kwargs) -> bool:
        """Create a call node in the unified graph."""
        try:
            params = {
                'call_id': call_id,
                'transcript_id': transcript_id,
                'customer_id': customer_id,
                'advisor_id': advisor_id or 'UNKNOWN',
                'topic': kwargs.get('topic', 'general inquiry'),
                'duration_minutes': kwargs.get('duration_minutes', 0.0),
                'urgency_level': kwargs.get('urgency_level', 'medium'),
                'sentiment': kwargs.get('sentiment', 'neutral'),
                'resolved': kwargs.get('resolved', False),
                'escalated': kwargs.get('escalated', False),
                'call_date': kwargs.get('call_date', datetime.utcnow().isoformat()),
                'created_at': datetime.utcnow().isoformat()
            }

            await self._execute_async("""
                CREATE (:Call {
                    call_id: $call_id,
                    transcript_id: $transcript_id,
                    customer_id: $customer_id,
                    advisor_id: $advisor_id,
                    topic: $topic,
                    duration_minutes: $duration_minutes,
                    urgency_level: $urgency_level,
                    sentiment: $sentiment,
                    resolved: $resolved,
                    escalated: $escalated,
                    call_date: $call_date,
                    created_at: $created_at
                })
            """, params)

            # Create relationship: Customer MADE_CALL Call
            await self._execute_async("""
                MATCH (c:Customer {customer_id: $customer_id})
                MATCH (call:Call {call_id: $call_id})
                CREATE (c)-[:MADE_CALL {contact_date: $call_date}]->(call)
            """, {
                'customer_id': customer_id,
                'call_id': call_id,
                'call_date': params['call_date']
            })

            # Create relationship: Call HANDLED_BY Advisor (if advisor exists)
            if advisor_id and advisor_id != 'UNKNOWN':
                await self._execute_async("""
                    MATCH (call:Call {call_id: $call_id})
                    MATCH (a:Advisor {advisor_id: $advisor_id})
                    CREATE (call)-[:HANDLED_BY {
                        started_at: $call_date,
                        completed_at: $call_date
                    }]->(a)
                """, {
                    'call_id': call_id,
                    'advisor_id': advisor_id,
                    'call_date': params['call_date']
                })

            logger.info(f"✅ Call node created: {call_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create call {call_id}: {e}")
            raise UnifiedGraphManagerError(f"Call creation failed: {str(e)}")

    async def create_or_update_advisor(self, advisor_id: str, **kwargs) -> bool:
        """Create or update advisor in the unified graph."""
        try:
            # Check if advisor exists
            result = await self._execute_async(
                "MATCH (a:Advisor {advisor_id: $advisor_id}) RETURN a.advisor_id",
                {"advisor_id": advisor_id}
            )

            exists = result.has_next()

            if exists:
                # Update existing advisor
                update_fields = []
                params = {"advisor_id": advisor_id, "updated_at": datetime.utcnow().isoformat()}

                for key, value in kwargs.items():
                    if key not in ['advisor_id', 'created_at']:
                        update_fields.append(f"a.{key} = ${key}")
                        params[key] = value

                if update_fields:
                    query = f"""
                        MATCH (a:Advisor {{advisor_id: $advisor_id}})
                        SET {', '.join(update_fields)}, a.updated_at = $updated_at
                    """
                    await self._execute_async(query, params)
            else:
                # Create new advisor
                params = {
                    "advisor_id": advisor_id,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                params.update(kwargs)

                # Convert any complex objects to strings
                for key, value in params.items():
                    if isinstance(value, (dict, list)):
                        params[key] = json.dumps(value)

                await self._execute_async("""
                    CREATE (:Advisor {
                        advisor_id: $advisor_id,
                        name: $name,
                        email: $email,
                        department: $department,
                        skill_level: $skill_level,
                        performance_score: $performance_score,
                        total_cases_handled: $total_cases_handled,
                        escalation_rate: $escalation_rate,
                        certifications: $certifications,
                        hire_date: $hire_date,
                        status: $status,
                        created_at: $created_at,
                        updated_at: $updated_at
                    })
                """, {
                    'advisor_id': advisor_id,
                    'name': params.get('name', ''),
                    'email': params.get('email', ''),
                    'department': params.get('department', ''),
                    'skill_level': params.get('skill_level', 'junior'),
                    'performance_score': params.get('performance_score', 0.0),
                    'total_cases_handled': params.get('total_cases_handled', 0),
                    'escalation_rate': params.get('escalation_rate', 0.0),
                    'certifications': params.get('certifications', '[]'),
                    'hire_date': params.get('hire_date', datetime.utcnow().isoformat()),
                    'status': params.get('status', 'active'),
                    'created_at': params['created_at'],
                    'updated_at': params['updated_at']
                })

            logger.info(f"✅ Advisor {'updated' if exists else 'created'}: {advisor_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create/update advisor {advisor_id}: {e}")
            raise UnifiedGraphManagerError(f"Advisor operation failed: {str(e)}")

    # === LEARNING NODE METHODS ===

    async def store_pattern(self, pattern: Pattern) -> bool:
        """Store a pattern in the unified graph."""
        try:
            await self._execute_async("""
                CREATE (:Pattern {
                    pattern_id: $pattern_id,
                    pattern_type: $pattern_type,
                    title: $title,
                    description: $description,
                    conditions: $conditions,
                    outcomes: $outcomes,
                    confidence: $confidence,
                    occurrences: $occurrences,
                    success_rate: $success_rate,
                    last_observed: $last_observed,
                    source_pipeline: $source_pipeline
                })
            """, {
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'title': pattern.title,
                'description': pattern.description,
                'conditions': json.dumps(pattern.conditions),
                'outcomes': json.dumps(pattern.outcomes),
                'confidence': pattern.confidence,
                'occurrences': pattern.occurrences,
                'success_rate': pattern.success_rate,
                'last_observed': pattern.last_observed.isoformat(),
                'source_pipeline': pattern.source_pipeline
            })

            logger.info(f"📊 Stored pattern: {pattern.pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store pattern {pattern.pattern_id}: {e}")
            raise UnifiedGraphManagerError(f"Pattern storage failed: {str(e)}")

    async def store_prediction(self, prediction: Prediction) -> bool:
        """Store a prediction in the unified graph."""
        try:
            await self._execute_async("""
                CREATE (:Prediction {
                    prediction_id: $prediction_id,
                    prediction_type: $prediction_type,
                    target_entity: $target_entity,
                    target_entity_id: $target_entity_id,
                    predicted_event: $predicted_event,
                    probability: $probability,
                    confidence: $confidence,
                    time_horizon: $time_horizon,
                    supporting_patterns: $supporting_patterns,
                    evidence_strength: $evidence_strength,
                    created_at: $created_at,
                    expires_at: $expires_at,
                    validated: $validated,
                    validation_date: $validation_date
                })
            """, {
                'prediction_id': prediction.prediction_id,
                'prediction_type': prediction.prediction_type,
                'target_entity': prediction.target_entity,
                'target_entity_id': prediction.target_entity_id,
                'predicted_event': prediction.predicted_event,
                'probability': prediction.probability,
                'confidence': prediction.confidence,
                'time_horizon': prediction.time_horizon,
                'supporting_patterns': json.dumps(prediction.supporting_patterns),
                'evidence_strength': prediction.evidence_strength,
                'created_at': prediction.created_at.isoformat(),
                'expires_at': prediction.expires_at.isoformat() if prediction.expires_at else None,
                'validated': prediction.validated,
                'validation_date': prediction.validation_date.isoformat() if prediction.validation_date else None
            })

            logger.info(f"🔮 Stored prediction: {prediction.prediction_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store prediction {prediction.prediction_id}: {e}")
            raise UnifiedGraphManagerError(f"Prediction storage failed: {str(e)}")

    async def store_wisdom(self, wisdom: Wisdom) -> bool:
        """Store wisdom in the unified graph."""
        try:
            await self._execute_async("""
                CREATE (:Wisdom {
                    wisdom_id: $wisdom_id,
                    wisdom_type: $wisdom_type,
                    domain: $domain,
                    insight: $insight,
                    applications: $applications,
                    success_indicators: $success_indicators,
                    derived_from_patterns: $derived_from_patterns,
                    evidence_base: $evidence_base,
                    confidence_level: $confidence_level,
                    discovered_at: $discovered_at,
                    times_applied: $times_applied,
                    application_success_rate: $application_success_rate
                })
            """, {
                'wisdom_id': wisdom.wisdom_id,
                'wisdom_type': wisdom.wisdom_type,
                'domain': wisdom.domain,
                'insight': wisdom.insight,
                'applications': json.dumps(wisdom.applications),
                'success_indicators': json.dumps(wisdom.success_indicators),
                'derived_from_patterns': json.dumps(wisdom.derived_from_patterns),
                'evidence_base': json.dumps(wisdom.evidence_base),
                'confidence_level': wisdom.confidence_level,
                'discovered_at': wisdom.discovered_at.isoformat(),
                'times_applied': wisdom.times_applied,
                'application_success_rate': wisdom.application_success_rate
            })

            logger.info(f"🧠 Stored wisdom: {wisdom.wisdom_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store wisdom {wisdom.wisdom_id}: {e}")
            raise UnifiedGraphManagerError(f"Wisdom storage failed: {str(e)}")

    async def store_meta_learning(self, meta_learning: MetaLearning) -> bool:
        """Store meta-learning in the unified graph."""
        try:
            await self._execute_async("""
                CREATE (:MetaLearning {
                    meta_id: $meta_id,
                    meta_type: $meta_type,
                    learning_insight: $learning_insight,
                    improvement_opportunity: $improvement_opportunity,
                    optimization_suggestion: $optimization_suggestion,
                    accuracy_metrics: $accuracy_metrics,
                    learning_velocity: $learning_velocity,
                    knowledge_gaps: $knowledge_gaps,
                    observed_at: $observed_at,
                    system_version: $system_version
                })
            """, {
                'meta_id': meta_learning.meta_id,
                'meta_type': meta_learning.meta_type,
                'learning_insight': meta_learning.learning_insight,
                'improvement_opportunity': meta_learning.improvement_opportunity,
                'optimization_suggestion': meta_learning.optimization_suggestion,
                'accuracy_metrics': json.dumps(meta_learning.accuracy_metrics),
                'learning_velocity': meta_learning.learning_velocity,
                'knowledge_gaps': json.dumps(meta_learning.knowledge_gaps),
                'observed_at': meta_learning.observed_at.isoformat(),
                'system_version': meta_learning.system_version
            })

            logger.info(f"🔄 Stored meta-learning: {meta_learning.meta_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to store meta-learning {meta_learning.meta_id}: {e}")
            raise UnifiedGraphManagerError(f"Meta-learning storage failed: {str(e)}")

    # === CROSS-DOMAIN RELATIONSHIP METHODS ===

    async def link_call_to_pattern(self, call_id: str, pattern_id: str, strength: float = 0.8) -> bool:
        """Create relationship: Call GENERATES_PATTERN Pattern."""
        try:
            await self._execute_async("""
                MATCH (call:Call {call_id: $call_id})
                MATCH (pattern:Pattern {pattern_id: $pattern_id})
                CREATE (call)-[:GENERATES_PATTERN {
                    pattern_strength: $strength,
                    generated_at: $generated_at
                }]->(pattern)
            """, {
                'call_id': call_id,
                'pattern_id': pattern_id,
                'strength': strength,
                'generated_at': datetime.utcnow().isoformat()
            })

            logger.info(f"🔗 Linked call {call_id} to pattern {pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link call to pattern: {e}")
            return False

    async def link_prediction_to_customer(self, prediction_id: str, customer_id: str, scope: str = "individual") -> bool:
        """Create relationship: Prediction TARGETS_CUSTOMER Customer."""
        try:
            await self._execute_async("""
                MATCH (pred:Prediction {prediction_id: $prediction_id})
                MATCH (customer:Customer {customer_id: $customer_id})
                CREATE (pred)-[:TARGETS_CUSTOMER {
                    prediction_scope: $scope,
                    target_date: $target_date
                }]->(customer)
            """, {
                'prediction_id': prediction_id,
                'customer_id': customer_id,
                'scope': scope,
                'target_date': datetime.utcnow().isoformat()
            })

            logger.info(f"🔗 Linked prediction {prediction_id} to customer {customer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link prediction to customer: {e}")
            return False

    async def link_pattern_to_advisor(self, pattern_id: str, advisor_id: str,
                                    learning_date: str = None, application_count: int = 1) -> bool:
        """Create relationship: Pattern LEARNED_BY_ADVISOR Advisor."""
        try:
            if learning_date is None:
                learning_date = datetime.utcnow().isoformat()

            await self._execute_async("""
                MATCH (pattern:Pattern {pattern_id: $pattern_id})
                MATCH (advisor:Advisor {advisor_id: $advisor_id})
                CREATE (pattern)-[:LEARNED_BY_ADVISOR {
                    learning_date: $learning_date,
                    application_count: $application_count
                }]->(advisor)
            """, {
                'pattern_id': pattern_id,
                'advisor_id': advisor_id,
                'learning_date': learning_date,
                'application_count': application_count
            })

            logger.info(f"🔗 Linked pattern {pattern_id} to advisor {advisor_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link pattern to advisor: {e}")
            return False

    # === QUERY METHODS ===

    async def get_patterns_by_context(self, context: Dict[str, Any]) -> List[Pattern]:
        """Get patterns relevant to the given context."""
        try:
            customer_id = context.get('customer_id', '')
            topic = context.get('topic', '')

            query = """
                MATCH (p:Pattern)
                WHERE p.source_pipeline = 'analysis'
                   OR p.title CONTAINS $topic
                   OR p.description CONTAINS $topic
                RETURN p
                ORDER BY p.confidence DESC, p.success_rate DESC
                LIMIT 5
            """

            result = await self._execute_async(query, {'topic': topic})
            patterns = []

            while result.has_next():
                row = result.get_next()
                pattern_data = row[0]

                try:
                    pattern = Pattern(
                        pattern_id=pattern_data['pattern_id'],
                        pattern_type=pattern_data['pattern_type'],
                        title=pattern_data['title'],
                        description=pattern_data['description'],
                        conditions=json.loads(pattern_data['conditions']),
                        outcomes=json.loads(pattern_data['outcomes']),
                        confidence=pattern_data['confidence'],
                        occurrences=pattern_data['occurrences'],
                        success_rate=pattern_data['success_rate'],
                        last_observed=datetime.fromisoformat(pattern_data['last_observed']),
                        source_pipeline=pattern_data['source_pipeline']
                    )
                    patterns.append(pattern)
                except Exception as parse_error:
                    logger.warning(f"Failed to parse pattern data: {parse_error}")
                    continue

            logger.info(f"🔍 Retrieved {len(patterns)} patterns for context")
            return patterns

        except Exception as e:
            logger.error(f"Failed to get patterns by context: {e}")
            raise UnifiedGraphManagerError(f"Pattern retrieval failed: {str(e)}")

    async def get_predictions_for_entity(self, entity_type: str, entity_id: str) -> List[Prediction]:
        """Get active predictions for a specific entity."""
        try:
            result = await self._execute_async("""
                MATCH (p:Prediction)
                WHERE p.target_entity = $entity_type
                  AND p.target_entity_id = $entity_id
                  AND (p.expires_at IS NULL OR p.expires_at > $current_time)
                  AND p.validated IS NULL
                RETURN p
                ORDER BY p.probability DESC, p.confidence DESC
            """, {
                'entity_type': entity_type,
                'entity_id': entity_id,
                'current_time': datetime.utcnow().isoformat()
            })

            predictions = []
            while result.has_next():
                row = result.get_next()
                prediction_data = row[0]

                try:
                    prediction = Prediction(
                        prediction_id=prediction_data['prediction_id'],
                        prediction_type=prediction_data['prediction_type'],
                        target_entity=prediction_data['target_entity'],
                        target_entity_id=prediction_data['target_entity_id'],
                        predicted_event=prediction_data['predicted_event'],
                        probability=prediction_data['probability'],
                        confidence=prediction_data['confidence'],
                        time_horizon=prediction_data['time_horizon'],
                        supporting_patterns=json.loads(prediction_data['supporting_patterns']),
                        evidence_strength=prediction_data['evidence_strength'],
                        created_at=datetime.fromisoformat(prediction_data['created_at']),
                        expires_at=datetime.fromisoformat(prediction_data['expires_at']) if prediction_data['expires_at'] else None,
                        validated=prediction_data['validated'],
                        validation_date=datetime.fromisoformat(prediction_data['validation_date']) if prediction_data['validation_date'] else None
                    )
                    predictions.append(prediction)
                except Exception as parse_error:
                    logger.warning(f"Failed to parse prediction data: {parse_error}")
                    continue

            logger.info(f"🔮 Retrieved {len(predictions)} active predictions for {entity_type}:{entity_id}")
            return predictions

        except Exception as e:
            logger.error(f"Failed to get predictions for {entity_type}:{entity_id}: {e}")
            raise UnifiedGraphManagerError(f"Prediction retrieval failed: {str(e)}")

    async def validate_prediction(self, prediction_id: str, outcome: bool) -> bool:
        """Validate a prediction with actual outcome."""
        try:
            await self._execute_async("""
                MATCH (p:Prediction {prediction_id: $prediction_id})
                SET p.validated = $outcome, p.validation_date = $validation_date
            """, {
                'prediction_id': prediction_id,
                'outcome': outcome,
                'validation_date': datetime.utcnow().isoformat()
            })
            logger.info(f"✅ Validated prediction {prediction_id}: {'SUCCESS' if outcome else 'FAILED'}")
            return True

        except Exception as e:
            logger.error(f"Failed to validate prediction {prediction_id}: {e}")
            return False

    async def update_pattern_evidence(self, pattern_id: str, new_observation: Dict[str, Any]) -> bool:
        """Update a pattern with new evidence."""
        try:
            await self._execute_async("""
                MATCH (p:Pattern {pattern_id: $pattern_id})
                SET p.occurrences = p.occurrences + 1, p.last_observed = $last_observed
            """, {
                'pattern_id': pattern_id,
                'last_observed': datetime.utcnow().isoformat()
            })
            logger.info(f"📊 Updated pattern {pattern_id} with new evidence")
            return True

        except Exception as e:
            logger.error(f"Failed to update pattern {pattern_id}: {e}")
            return False

    # ===============================================
    # EVENT HANDLER SUPPORT METHODS (SYNCHRONOUS WRAPPERS)
    # ===============================================

    def create_or_update_customer_sync(self, customer_id: str, **kwargs) -> bool:
        """Synchronous wrapper for create_or_update_customer."""
        try:
            import asyncio
            import concurrent.futures

            # Check if we're already in an event loop
            try:
                current_loop = asyncio.get_running_loop()
                # We're in an event loop, schedule the coroutine
                future = asyncio.create_task(
                    self.create_or_update_customer(customer_id=customer_id, **kwargs)
                )
                # Run in background and return immediately with default success
                # Event handlers should not block the main thread
                logger.info(f"Scheduled customer creation for {customer_id} in background")
                return True
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.create_or_update_customer(customer_id=customer_id, **kwargs)
                )
                loop.close()
                return result
        except Exception as e:
            logger.error(f"Failed to create/update customer {customer_id}: {e}")
            return False

    def create_or_update_advisor_sync(self, advisor_id: str, **kwargs) -> bool:
        """Synchronous wrapper for create_or_update_advisor."""
        try:
            import asyncio

            # Check if we're already in an event loop
            try:
                current_loop = asyncio.get_running_loop()
                # We're in an event loop, schedule the coroutine
                future = asyncio.create_task(
                    self.create_or_update_advisor(advisor_id=advisor_id, **kwargs)
                )
                # Run in background and return immediately with default success
                # Event handlers should not block the main thread
                logger.info(f"Scheduled advisor creation for {advisor_id} in background")
                return True
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.create_or_update_advisor(advisor_id=advisor_id, **kwargs)
                )
                loop.close()
                return result
        except Exception as e:
            logger.error(f"Failed to create/update advisor {advisor_id}: {e}")
            return False

    def create_transcript(self, transcript_id: str, customer_id: str, advisor_id: str,
                         topic: str, urgency: str, channel: str, started_at: str, status: str = 'active') -> bool:
        """Synchronous wrapper for create_call_node for event handlers."""
        try:
            import asyncio

            # Check if we're already in an event loop
            try:
                current_loop = asyncio.get_running_loop()
                # We're in an event loop, schedule the coroutine
                future = asyncio.create_task(
                    self.create_call_node(
                        call_id=transcript_id,
                        transcript_id=transcript_id,
                        customer_id=customer_id,
                        advisor_id=advisor_id,
                        topic=topic,
                        urgency_level=urgency,
                        sentiment="neutral",
                        resolved=status == 'resolved',
                        call_date=started_at
                    )
                )
                # Run in background and return immediately with default success
                # Event handlers should not block the main thread
                logger.info(f"Scheduled transcript creation for {transcript_id} in background")
                return True
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.create_call_node(
                        call_id=transcript_id,
                        transcript_id=transcript_id,
                        customer_id=customer_id,
                        advisor_id=advisor_id,
                        topic=topic,
                        urgency_level=urgency,
                        sentiment="neutral",
                        resolved=status == 'resolved',
                        call_date=started_at
                    )
                )
                loop.close()
                return result
        except Exception as e:
            logger.error(f"Failed to create transcript {transcript_id}: {e}")
            return False

    def create_analysis(self, analysis_id: str, transcript_id: str, intent: str,
                       urgency_level: str, sentiment: str, risk_score: float,
                       compliance_flags: List[str], confidence_score: float) -> bool:
        """Create analysis node - stores as Call metadata for now."""
        try:
            # Update the call with analysis results
            query = """
                MATCH (c:Call {call_id: $transcript_id})
                SET c.analysis_id = $analysis_id,
                    c.intent = $intent,
                    c.sentiment = $sentiment,
                    c.urgency_level = $urgency_level,
                    c.confidence_score = $confidence_score
                RETURN c
            """

            result = self.conn.execute(query, parameters={
                'transcript_id': transcript_id,
                'analysis_id': analysis_id,
                'intent': intent,
                'sentiment': sentiment,
                'urgency_level': urgency_level,
                'confidence_score': confidence_score
            })

            logger.info(f"✅ Analysis {analysis_id} linked to transcript {transcript_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create analysis {analysis_id}: {e}")
            return False

    def update_customer_risk_profile(self, customer_id: str, risk_score: float, compliance_flags: List[str]) -> bool:
        """Update customer risk profile."""
        try:
            import asyncio

            # Check if we're already in an event loop
            try:
                current_loop = asyncio.get_running_loop()
                # We're in an event loop, schedule the coroutine
                future = asyncio.create_task(
                    self.create_or_update_customer(
                        customer_id=customer_id,
                        risk_score=risk_score,
                        compliance_flags=','.join(compliance_flags) if compliance_flags else ''
                    )
                )
                # Run in background and return immediately with default success
                # Event handlers should not block the main thread
                logger.info(f"Scheduled customer risk profile update for {customer_id} in background")
                return True
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.create_or_update_customer(
                        customer_id=customer_id,
                        risk_score=risk_score,
                        compliance_flags=','.join(compliance_flags) if compliance_flags else ''
                    )
                )
                loop.close()
                return result
        except Exception as e:
            logger.error(f"Failed to update customer risk profile {customer_id}: {e}")
            return False

    def create_or_update_supervisor(self, supervisor_id: str, **kwargs) -> bool:
        """Create or update supervisor - treat as special advisor."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.create_or_update_advisor(
                    advisor_id=supervisor_id,
                    department="supervision",
                    skill_level="expert",
                    **kwargs
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to create/update supervisor {supervisor_id}: {e}")
            return False

    def create_escalation(self, workflow_id: str, from_advisor: str, to_supervisor: str,
                         reason: str, urgency_level: str, escalated_at: str) -> bool:
        """Create escalation relationship."""
        try:
            query = """
                MATCH (a:Advisor {advisor_id: $from_advisor}), (s:Advisor {advisor_id: $to_supervisor})
                CREATE (a)-[:ESCALATED_TO {
                    workflow_id: $workflow_id,
                    reason: $reason,
                    urgency_level: $urgency_level,
                    escalated_at: $escalated_at
                }]->(s)
                RETURN a, s
            """

            result = self.db.execute(query, parameters={
                'workflow_id': workflow_id,
                'from_advisor': from_advisor,
                'to_supervisor': to_supervisor,
                'reason': reason,
                'urgency_level': urgency_level,
                'escalated_at': escalated_at
            })

            logger.info(f"✅ Escalation created: {from_advisor} -> {to_supervisor}")
            return True
        except Exception as e:
            logger.error(f"Failed to create escalation {workflow_id}: {e}")
            return False

    def update_advisor_escalation_metrics(self, advisor_id: str) -> bool:
        """Update advisor escalation metrics."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Get current escalation count
            query = """
                MATCH (a:Advisor {advisor_id: $advisor_id})-[:ESCALATED_TO]->()
                RETURN count(*) as escalation_count
            """

            result = loop.run_until_complete(self._execute_async(query, {'advisor_id': advisor_id}))
            escalation_count = 0
            if result.has_next():
                escalation_count = result.get_next()[0]

            # Update advisor with new escalation rate
            result = loop.run_until_complete(
                self.create_or_update_advisor(
                    advisor_id=advisor_id,
                    escalation_rate=escalation_count
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to update escalation metrics for {advisor_id}: {e}")
            return False

    def create_resolution(self, resolution_id: str, issue_id: str, resolved_by_advisor: str,
                         resolved_by_supervisor: str, method: str, resolution_time_minutes: int,
                         customer_satisfaction: float, resolved_at: str) -> bool:
        """Create resolution tracking."""
        try:
            # For now, just update the call as resolved
            query = """
                MATCH (c:Call {call_id: $issue_id})
                SET c.resolved = true,
                    c.resolution_id = $resolution_id,
                    c.resolved_by = $resolved_by_advisor,
                    c.resolution_method = $method,
                    c.resolution_time_minutes = $resolution_time_minutes,
                    c.customer_satisfaction = $customer_satisfaction,
                    c.resolved_at = $resolved_at
                RETURN c
            """

            result = self.db.execute(query, parameters={
                'issue_id': issue_id,
                'resolution_id': resolution_id,
                'resolved_by_advisor': resolved_by_advisor,
                'method': method,
                'resolution_time_minutes': resolution_time_minutes,
                'customer_satisfaction': customer_satisfaction,
                'resolved_at': resolved_at
            })

            logger.info(f"✅ Resolution {resolution_id} created for issue {issue_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to create resolution {resolution_id}: {e}")
            return False

    def update_advisor_resolution_metrics(self, advisor_id: str, resolution_time: int, satisfaction_score: float) -> bool:
        """Update advisor resolution performance metrics."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.create_or_update_advisor(
                    advisor_id=advisor_id,
                    avg_resolution_time=resolution_time,
                    avg_satisfaction=satisfaction_score
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to update resolution metrics for {advisor_id}: {e}")
            return False

    def update_supervisor_metrics(self, supervisor_id: str) -> bool:
        """Update supervisor performance metrics."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.create_or_update_advisor(
                    advisor_id=supervisor_id,
                    total_supervisions=1  # Increment would be better but this is simple
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to update supervisor metrics for {supervisor_id}: {e}")
            return False

    def create_document_acknowledgment(self, document_id: str, customer_id: str, document_type: str,
                                     sent_at: str, acknowledged_at: str, method: str) -> bool:
        """Create document acknowledgment tracking."""
        try:
            # Create document acknowledgment relationship
            query = """
                MATCH (c:Customer {customer_id: $customer_id})
                CREATE (c)-[:ACKNOWLEDGED_DOCUMENT {
                    document_id: $document_id,
                    document_type: $document_type,
                    sent_at: $sent_at,
                    acknowledged_at: $acknowledged_at,
                    method: $method
                }]->(c)
                RETURN c
            """

            result = self.db.execute(query, parameters={
                'customer_id': customer_id,
                'document_id': document_id,
                'document_type': document_type,
                'sent_at': sent_at,
                'acknowledged_at': acknowledged_at,
                'method': method
            })

            logger.info(f"✅ Document acknowledgment {document_id} created")
            return True
        except Exception as e:
            logger.error(f"Failed to create document acknowledgment {document_id}: {e}")
            return False

    def update_customer_engagement_metrics(self, customer_id: str) -> bool:
        """Update customer engagement metrics."""
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Get document acknowledgment count
            query = """
                MATCH (c:Customer {customer_id: $customer_id})-[:ACKNOWLEDGED_DOCUMENT]->()
                RETURN count(*) as doc_count
            """

            result = loop.run_until_complete(self._execute_async(query, {'customer_id': customer_id}))
            doc_count = 0
            if result.has_next():
                doc_count = result.get_next()[0]

            # Update customer engagement
            result = loop.run_until_complete(
                self.create_or_update_customer(
                    customer_id=customer_id,
                    document_acknowledgments=doc_count
                )
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Failed to update engagement metrics for {customer_id}: {e}")
            return False

    def close(self) -> None:
        """Close all database connections and cleanup resources."""
        if hasattr(self, '_connection_pool'):
            for conn in self._connection_pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)

        logger.info("📝 Closed all unified graph connections")


# Global instance with thread safety
_unified_manager = None
import threading
_manager_lock = threading.Lock()

def get_unified_graph_manager() -> UnifiedGraphManager:
    """Get the global unified graph manager instance (thread-safe singleton)."""
    global _unified_manager
    if _unified_manager is None:
        with _manager_lock:
            # Double-check locking pattern
            if _unified_manager is None:
                try:
                    _unified_manager = UnifiedGraphManager()
                    logger.info("✅ Unified graph manager singleton created")
                except Exception as e:
                    logger.error(f"Failed to initialize UnifiedGraphManager: {e}")
                    raise RuntimeError(f"Cannot proceed without unified graph system: {e}")
    return _unified_manager

def close_unified_graph_manager() -> None:
    """Close the global unified graph manager and cleanup resources."""
    global _unified_manager
    if _unified_manager is not None:
        _unified_manager.close()
        _unified_manager = None
        logger.info("🔒 Unified graph manager singleton closed")