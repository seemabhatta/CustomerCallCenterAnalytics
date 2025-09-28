"""
Unified Knowledge Graph Manager - Clean Implementation

Manages the complete agentic knowledge graph including:
- Business entities: Customer, Advisor, Call, Loan
- Operational pipeline: Analysis, Plan, Workflow, ExecutionStep, ExecutionResult
- Learning system: Hypothesis, CandidatePattern, ValidatedPattern, Prediction, Wisdom, MetaLearning
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import kuzu
import uuid
import json

from .knowledge_types import (
    Hypothesis, CandidatePattern, ValidatedPattern,
    Prediction, Wisdom, MetaLearning
)

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
    Clean Unified Knowledge Graph Manager for Agentic Customer Service System.

    Supports complete operational pipeline and learning system with no legacy code.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from ..config.database_config import get_knowledge_graph_database_path
            db_path = get_knowledge_graph_database_path()

        self.db_path = db_path
        self.db = _get_global_database(db_path)
        self.conn = kuzu.Connection(self.db)

        # Single threaded executor for database operations
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="unified_kuzu_single")

        # Write queue system to serialize ALL operations
        self._write_queue = None
        self._write_processor_task = None
        self._operation_counter = 0

        # Schema initialization flag
        self._schema_initialized = False

    async def _execute_async(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Execute ALL KuzuDB operations through the queue for complete serialization."""
        return await self._queue_write_operation(query, parameters)

    async def _queue_write_operation(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Queue a database operation for sequential execution."""
        # Initialize write queue if needed
        if self._write_queue is None:
            self._write_queue = asyncio.Queue()
            self._write_processor_task = asyncio.create_task(self._process_write_queue())

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

        # Queue the operation
        await self._write_queue.put(operation)

        # Wait for and return the result
        return await future

    async def _process_write_queue(self):
        """Background task that processes database operations sequentially."""
        while True:
            try:
                operation = await self._write_queue.get()

                if operation is None:  # Shutdown signal
                    break

                try:
                    # Execute the operation using the single connection
                    if operation['parameters']:
                        result = self.conn.execute(operation['query'], operation['parameters'])
                    else:
                        result = self.conn.execute(operation['query'])

                    # Set the result
                    operation['future'].set_result(result)
                except Exception as e:
                    logger.error(f"Database operation {operation['id']} failed: {e}")
                    operation['future'].set_exception(e)

            except Exception as e:
                logger.error(f"Write queue processor error: {e}")
                break

    async def _initialize_schema_async(self):
        """Initialize clean schema with operational pipeline and learning system."""
        if self._schema_initialized:
            return

        logger.info("🔄 Initializing clean knowledge graph schema...")

        # Define all schema operations
        schema_operations = [
            # === BUSINESS ENTITIES ===

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
                last_contact_date TIMESTAMP,
                status STRING DEFAULT 'active',
                compliance_flags STRING,
                created_at STRING,
                updated_at STRING
            )""",

            # Call node (cleaned - no analysis duplication)
            """CREATE NODE TABLE IF NOT EXISTS Call(
                call_id STRING PRIMARY KEY,
                transcript_id STRING,
                customer_id STRING,
                advisor_id STRING,
                topic STRING,
                duration_minutes DOUBLE DEFAULT 0.0,
                resolved BOOLEAN DEFAULT FALSE,
                escalated BOOLEAN DEFAULT FALSE,
                call_date STRING,
                created_at STRING
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

            # Loan node
            """CREATE NODE TABLE IF NOT EXISTS Loan(
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
            )""",

            # === OPERATIONAL PIPELINE ===

            # Analysis node
            """CREATE NODE TABLE IF NOT EXISTS Analysis(
                analysis_id STRING PRIMARY KEY,
                call_id STRING,
                transcript_id STRING,
                intent STRING,
                urgency_level STRING,
                sentiment STRING,
                confidence_score DOUBLE DEFAULT 0.0,
                risk_factors STRING,
                compliance_issues STRING,
                customer_satisfaction STRING,
                analysis_summary STRING,
                llm_reasoning STRING,
                analyzed_at STRING,
                analyzer_version STRING,
                processing_time_ms INT64
            )""",

            # Plan node
            """CREATE NODE TABLE IF NOT EXISTS Plan(
                plan_id STRING PRIMARY KEY,
                analysis_id STRING,
                plan_type STRING,
                title STRING,
                description STRING,
                priority STRING DEFAULT 'medium',
                strategic_actions STRING,
                expected_outcomes STRING,
                risk_assessment STRING,
                compliance_requirements STRING,
                estimated_duration_minutes INT64,
                llm_reasoning STRING,
                planned_at STRING,
                planner_version STRING,
                approval_status STRING DEFAULT 'pending'
            )""",

            # Workflow node
            """CREATE NODE TABLE IF NOT EXISTS Workflow(
                workflow_id STRING PRIMARY KEY,
                plan_id STRING,
                workflow_type STRING,
                title STRING,
                description STRING,
                total_steps INT64,
                detailed_steps STRING,
                execution_order STRING,
                dependencies STRING,
                required_tools STRING,
                estimated_duration_minutes INT64,
                complexity_score DOUBLE DEFAULT 0.0,
                llm_reasoning STRING,
                created_at STRING,
                workflow_version STRING,
                status STRING DEFAULT 'created'
            )""",

            # ExecutionStep node (step definition)
            """CREATE NODE TABLE IF NOT EXISTS ExecutionStep(
                step_id STRING PRIMARY KEY,
                workflow_id STRING,
                step_number INT64,
                step_title STRING,
                step_description STRING,
                executor_type STRING,
                executor_config STRING,
                dependencies STRING,
                created_at STRING
            )""",

            # ExecutionResult node (actual execution outcome)
            """CREATE NODE TABLE IF NOT EXISTS ExecutionResult(
                result_id STRING PRIMARY KEY,
                step_id STRING,
                execution_status STRING DEFAULT 'pending',
                started_at STRING,
                completed_at STRING,
                duration_ms INT64,
                success BOOLEAN DEFAULT FALSE,
                result_data STRING,
                error_message STRING,
                retry_count INT64 DEFAULT 0,
                executed_by STRING
            )""",

            # === LEARNING SYSTEM ===

            # Hypothesis node (single LLM observation)
            """CREATE NODE TABLE IF NOT EXISTS Hypothesis(
                hypothesis_id STRING PRIMARY KEY,
                hypothesis_type STRING,
                title STRING,
                description STRING,
                llm_confidence DOUBLE DEFAULT 0.0,
                reasoning STRING,
                evidence_count INT64 DEFAULT 1,
                first_observed STRING,
                last_evidence STRING,
                source_stage STRING,
                customer_context STRING,
                status STRING DEFAULT 'unvalidated'
            )""",

            # CandidatePattern node (multiple observations awaiting validation)
            """CREATE NODE TABLE IF NOT EXISTS CandidatePattern(
                candidate_id STRING PRIMARY KEY,
                hypothesis_id STRING,
                pattern_type STRING,
                title STRING,
                description STRING,
                evidence_count INT64,
                occurrence_frequency DOUBLE,
                awaiting_validation BOOLEAN DEFAULT TRUE,
                validation_threshold_met BOOLEAN DEFAULT FALSE,
                sample_size INT64,
                promoted_at STRING,
                ready_for_validation_at STRING,
                original_llm_confidence DOUBLE,
                source_stage STRING
            )""",

            # ValidatedPattern node (statistically confirmed)
            """CREATE NODE TABLE IF NOT EXISTS ValidatedPattern(
                pattern_id STRING PRIMARY KEY,
                candidate_id STRING,
                pattern_type STRING,
                title STRING,
                description STRING,
                conditions STRING,
                outcomes STRING,
                statistical_confidence DOUBLE,
                p_value DOUBLE,
                sample_size INT64,
                validation_method STRING,
                occurrence_rate DOUBLE,
                success_rate DOUBLE,
                effect_size DOUBLE,
                validated_at STRING,
                validated_by STRING,
                validation_dataset_size INT64,
                total_occurrences INT64,
                last_observed STRING,
                source_pipeline STRING,
                revalidation_due STRING,
                validation_status STRING DEFAULT 'active'
            )""",

            # Prediction node
            """CREATE NODE TABLE IF NOT EXISTS Prediction(
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
            )""",

            # Wisdom node
            """CREATE NODE TABLE IF NOT EXISTS Wisdom(
                wisdom_id STRING PRIMARY KEY,
                wisdom_type STRING,
                title STRING,
                content STRING,
                source_context STRING,
                learning_domain STRING,
                applicability STRING,
                validated BOOLEAN DEFAULT FALSE,
                validation_count INT64 DEFAULT 0,
                effectiveness_score DOUBLE DEFAULT 0.0,
                created_at STRING,
                last_applied STRING,
                application_count INT64 DEFAULT 0
            )""",

            # MetaLearning node
            """CREATE NODE TABLE IF NOT EXISTS MetaLearning(
                meta_learning_id STRING PRIMARY KEY,
                learning_type STRING,
                insight_source STRING,
                meta_insight STRING,
                improvement_area STRING,
                system_component STRING,
                learning_context STRING,
                impact_assessment STRING,
                validation_status BOOLEAN DEFAULT FALSE,
                validation_count INT64 DEFAULT 0,
                created_at STRING,
                last_updated STRING
            )""",
        ]

        # Execute schema operations through write queue
        for operation in schema_operations:
            try:
                future = asyncio.Future()
                self._operation_counter += 1
                schema_op = {
                    'id': self._operation_counter,
                    'query': operation,
                    'parameters': None,
                    'future': future
                }
                await self._write_queue.put(schema_op)
                await future
            except Exception as e:
                logger.error(f"Failed to create schema: {e}")
                raise RuntimeError(f"Schema initialization failed: {str(e)}")

        # Create relationships
        relationship_operations = [
            # === BUSINESS RELATIONSHIPS ===
            "CREATE REL TABLE IF NOT EXISTS HAS_LOAN(FROM Customer TO Loan, since STRING)",
            "CREATE REL TABLE IF NOT EXISTS ABOUT_LOAN(FROM Call TO Loan, related_topic STRING)",
            "CREATE REL TABLE IF NOT EXISTS HANDLED_BY(FROM Call TO Advisor, started_at STRING, completed_at STRING)",

            # === OPERATIONAL PIPELINE RELATIONSHIPS ===
            "CREATE REL TABLE IF NOT EXISTS INVOLVES_CUSTOMER(FROM Call TO Customer, involvement_type STRING, contact_date STRING)",
            "CREATE REL TABLE IF NOT EXISTS GENERATES_ANALYSIS(FROM Call TO Analysis, generated_at STRING, processing_time_ms INT64)",
            "CREATE REL TABLE IF NOT EXISTS GENERATES_PLAN(FROM Analysis TO Plan, generated_at STRING, confidence_score DOUBLE)",
            "CREATE REL TABLE IF NOT EXISTS HAS_WORKFLOW(FROM Plan TO Workflow, created_at STRING, workflow_type STRING)",
            "CREATE REL TABLE IF NOT EXISTS HAS_STEP(FROM Workflow TO ExecutionStep, step_order INT64, created_at STRING)",
            "CREATE REL TABLE IF NOT EXISTS EXECUTED_AS(FROM ExecutionStep TO ExecutionResult, execution_attempt INT64, created_at STRING)",

            # Advisor operational relationships
            "CREATE REL TABLE IF NOT EXISTS ANALYZED_BY(FROM Analysis TO Advisor, analyzed_at STRING, review_status STRING)",
            "CREATE REL TABLE IF NOT EXISTS PLANNED_BY(FROM Plan TO Advisor, planned_at STRING, approval_status STRING)",
            "CREATE REL TABLE IF NOT EXISTS REVIEWED_BY(FROM Workflow TO Advisor, reviewed_at STRING, approval_status STRING)",
            "CREATE REL TABLE IF NOT EXISTS EXECUTED_BY_ADVISOR(FROM ExecutionResult TO Advisor, executed_at STRING, success BOOLEAN)",

            # === LEARNING SYSTEM RELATIONSHIPS ===
            "CREATE REL TABLE IF NOT EXISTS GENERATES_HYPOTHESIS(FROM Analysis TO Hypothesis, llm_confidence DOUBLE, generated_at STRING)",
            "CREATE REL TABLE IF NOT EXISTS TRIGGERED_HYPOTHESIS(FROM Customer TO Hypothesis, trigger_strength DOUBLE, triggered_at STRING)",
            "CREATE REL TABLE IF NOT EXISTS PROVIDES_EVIDENCE(FROM Call TO Hypothesis, evidence_strength DOUBLE, added_at STRING)",

            # Operational-to-Learning connections
            "CREATE REL TABLE IF NOT EXISTS EXECUTION_EVIDENCE(FROM ExecutionResult TO Hypothesis, evidence_type STRING, success_weight DOUBLE)",
            "CREATE REL TABLE IF NOT EXISTS WORKFLOW_VALIDATES(FROM Workflow TO CandidatePattern, validation_strength DOUBLE, validated_at STRING)",
            "CREATE REL TABLE IF NOT EXISTS PLAN_SUPPORTS(FROM Plan TO Hypothesis, support_reasoning STRING, confidence DOUBLE)",

            # Source tracking relationships
            "CREATE REL TABLE IF NOT EXISTS HYPOTHESIS_SOURCE(FROM Call TO Hypothesis, contribution_type STRING, evidence_weight DOUBLE)",
            "CREATE REL TABLE IF NOT EXISTS CANDIDATE_SOURCE(FROM Call TO CandidatePattern, contribution_type STRING, evidence_weight DOUBLE)",

            # Pattern evolution relationships
            "CREATE REL TABLE IF NOT EXISTS PROMOTED_FROM(FROM CandidatePattern TO Hypothesis, promoted_at STRING, evidence_threshold_met BOOLEAN)",
            "CREATE REL TABLE IF NOT EXISTS AWAITS_VALIDATION(FROM CandidatePattern TO Hypothesis, awaiting_since STRING, threshold_met BOOLEAN)",
            "CREATE REL TABLE IF NOT EXISTS VALIDATED_FROM(FROM ValidatedPattern TO CandidatePattern, validated_at STRING, validation_method STRING)",
            "CREATE REL TABLE IF NOT EXISTS STATISTICALLY_SUPPORTS(FROM ValidatedPattern TO Hypothesis, confidence DOUBLE, p_value DOUBLE)",
            "CREATE REL TABLE IF NOT EXISTS EVIDENCE_FOR_VALIDATED(FROM Call TO ValidatedPattern, evidence_type STRING, contribution_weight DOUBLE)",

            # Cross-type relationships
            "CREATE REL TABLE IF NOT EXISTS CONTRADICTS(FROM ValidatedPattern TO Hypothesis, contradiction_strength DOUBLE, identified_at STRING)",

            # Traditional learning relationships
            "CREATE REL TABLE IF NOT EXISTS TARGETS_CUSTOMER(FROM Prediction TO Customer, prediction_scope STRING, target_date STRING)",
            "CREATE REL TABLE IF NOT EXISTS TRIGGERS_LEARNING(FROM Call TO MetaLearning, learning_type STRING, trigger_reason STRING)",
            "CREATE REL TABLE IF NOT EXISTS APPLIES_TO(FROM Wisdom TO Advisor, relevance_score DOUBLE, applied_at STRING)",
        ]

        for operation in relationship_operations:
            try:
                future = asyncio.Future()
                self._operation_counter += 1
                rel_op = {
                    'id': self._operation_counter,
                    'query': operation,
                    'parameters': None,
                    'future': future
                }
                await self._write_queue.put(rel_op)
                await future
            except Exception as e:
                logger.error(f"Failed to create relationship: {e}")
                raise RuntimeError(f"Relationship creation failed: {str(e)}")

        self._schema_initialized = True
        logger.info("✅ Clean knowledge graph schema initialized successfully")

    # === CORE CRUD OPERATIONS ===

    async def create_call(self, call_data: Dict[str, Any]) -> str:
        """Create a new call node."""
        call_id = call_data.get('call_id', f"CALL_{uuid.uuid4().hex[:8]}")

        query = """
        CREATE (c:Call {
            call_id: $call_id,
            transcript_id: $transcript_id,
            customer_id: $customer_id,
            advisor_id: $advisor_id,
            topic: $topic,
            duration_minutes: $duration_minutes,
            resolved: $resolved,
            escalated: $escalated,
            call_date: $call_date,
            created_at: $created_at
        })
        """

        params = {
            'call_id': call_id,
            'transcript_id': call_data.get('transcript_id'),
            'customer_id': call_data.get('customer_id'),
            'advisor_id': call_data.get('advisor_id'),
            'topic': call_data.get('topic', ''),
            'duration_minutes': call_data.get('duration_minutes', 0.0),
            'resolved': call_data.get('resolved', False),
            'escalated': call_data.get('escalated', False),
            'call_date': call_data.get('call_date', datetime.utcnow()),
            'created_at': datetime.utcnow()
        }

        await self._execute_async(query, params)
        return call_id

    async def create_analysis(self, analysis_data: Dict[str, Any]) -> str:
        """Create a new analysis node."""
        analysis_id = analysis_data.get('analysis_id', f"ANALYSIS_{uuid.uuid4().hex[:8]}")

        query = """
        CREATE (a:Analysis {
            analysis_id: $analysis_id,
            call_id: $call_id,
            transcript_id: $transcript_id,
            intent: $intent,
            urgency_level: $urgency_level,
            sentiment: $sentiment,
            confidence_score: $confidence_score,
            risk_factors: $risk_factors,
            compliance_issues: $compliance_issues,
            customer_satisfaction: $customer_satisfaction,
            analysis_summary: $analysis_summary,
            llm_reasoning: $llm_reasoning,
            analyzed_at: $analyzed_at,
            analyzer_version: $analyzer_version,
            processing_time_ms: $processing_time_ms
        })
        """

        params = {
            'analysis_id': analysis_id,
            'call_id': analysis_data.get('call_id'),
            'transcript_id': analysis_data.get('transcript_id'),
            'intent': analysis_data.get('intent'),
            'urgency_level': analysis_data.get('urgency_level'),
            'sentiment': analysis_data.get('sentiment'),
            'confidence_score': analysis_data.get('confidence_score', 0.0),
            'risk_factors': analysis_data.get('risk_factors', ''),
            'compliance_issues': analysis_data.get('compliance_issues', ''),
            'customer_satisfaction': analysis_data.get('customer_satisfaction', ''),
            'analysis_summary': analysis_data.get('analysis_summary', ''),
            'llm_reasoning': analysis_data.get('llm_reasoning', ''),
            'analyzed_at': analysis_data.get('analyzed_at', datetime.utcnow()),
            'analyzer_version': analysis_data.get('analyzer_version', 'v1.0'),
            'processing_time_ms': analysis_data.get('processing_time_ms', 0)
        }

        await self._execute_async(query, params)
        return analysis_id

    async def create_hypothesis(self, hypothesis_data: Dict[str, Any]) -> str:
        """Create a new hypothesis from analysis."""
        hypothesis_id = hypothesis_data.get('hypothesis_id', f"HYPO_{uuid.uuid4().hex[:8]}")

        query = """
        CREATE (h:Hypothesis {
            hypothesis_id: $hypothesis_id,
            hypothesis_type: $hypothesis_type,
            title: $title,
            description: $description,
            llm_confidence: $llm_confidence,
            reasoning: $reasoning,
            evidence_count: $evidence_count,
            first_observed: $first_observed,
            last_evidence: $last_evidence,
            source_stage: $source_stage,
            customer_context: $customer_context,
            status: $status
        })
        """

        params = {
            'hypothesis_id': hypothesis_id,
            'hypothesis_type': hypothesis_data.get('hypothesis_type', 'behavioral'),
            'title': hypothesis_data.get('title'),
            'description': hypothesis_data.get('description'),
            'llm_confidence': hypothesis_data.get('llm_confidence', 0.0),
            'reasoning': hypothesis_data.get('reasoning', ''),
            'evidence_count': hypothesis_data.get('evidence_count', 1),
            'first_observed': hypothesis_data.get('first_observed', datetime.utcnow()),
            'last_evidence': hypothesis_data.get('last_evidence', datetime.utcnow()),
            'source_stage': hypothesis_data.get('source_stage', 'analysis'),
            'customer_context': hypothesis_data.get('customer_context', ''),
            'status': hypothesis_data.get('status', 'unvalidated')
        }

        await self._execute_async(query, params)
        return hypothesis_id

    async def link_call_to_analysis(self, call_id: str, analysis_id: str, processing_time_ms: int = 0) -> bool:
        """Create relationship: Call GENERATES_ANALYSIS Analysis."""
        query = """
        MATCH (c:Call {call_id: $call_id})
        MATCH (a:Analysis {analysis_id: $analysis_id})
        CREATE (c)-[:GENERATES_ANALYSIS {
            generated_at: $generated_at,
            processing_time_ms: $processing_time_ms
        }]->(a)
        """

        params = {
            'call_id': call_id,
            'analysis_id': analysis_id,
            'generated_at': datetime.utcnow(),
            'processing_time_ms': processing_time_ms
        }

        try:
            await self._execute_async(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to link call to analysis: {e}")
            return False

    async def link_analysis_to_hypothesis(self, analysis_id: str, hypothesis_id: str, confidence: float) -> bool:
        """Create relationship: Analysis GENERATES_HYPOTHESIS Hypothesis."""
        query = """
        MATCH (a:Analysis {analysis_id: $analysis_id})
        MATCH (h:Hypothesis {hypothesis_id: $hypothesis_id})
        CREATE (a)-[:GENERATES_HYPOTHESIS {
            llm_confidence: $llm_confidence,
            generated_at: $generated_at
        }]->(h)
        """

        params = {
            'analysis_id': analysis_id,
            'hypothesis_id': hypothesis_id,
            'llm_confidence': confidence,
            'generated_at': datetime.utcnow()
        }

        try:
            await self._execute_async(query, params)
            return True
        except Exception as e:
            logger.error(f"Failed to link analysis to hypothesis: {e}")
            return False

    async def get_call_by_id(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve call by ID."""
        query = """
        MATCH (c:Call {call_id: $call_id})
        RETURN c.*
        """

        try:
            result = await self._execute_async(query, {'call_id': call_id})
            rows = result.get_next()
            if rows:
                return dict(rows[0])
            return None
        except Exception as e:
            logger.error(f"Failed to get call: {e}")
            return None

    async def create_plan_node(self, plan_id: str, analysis_id: str, transcript_id: str,
                              customer_id: str, priority_level: str, action_count: int, urgency_level: str) -> str:
        """Create a Plan node in the knowledge graph."""
        try:
            query = """
            CREATE (p:Plan {
                plan_id: $plan_id,
                analysis_id: $analysis_id,
                transcript_id: $transcript_id,
                customer_id: $customer_id,
                priority_level: $priority_level,
                action_count: $action_count,
                urgency_level: $urgency_level,
                created_at: $created_at,
                status: 'generated'
            })
            """

            parameters = {
                'plan_id': plan_id,
                'analysis_id': analysis_id,
                'transcript_id': transcript_id,
                'customer_id': customer_id,
                'priority_level': priority_level,
                'action_count': action_count,
                'urgency_level': urgency_level,
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"📋 Created Plan node: {plan_id}")
            return plan_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Plan creation failed: {str(e)}")

    async def create_workflow_node(self, workflow_id: str, plan_id: str, customer_id: str,
                                  advisor_id: str, step_count: int, estimated_duration: int, priority: str) -> str:
        """Create a Workflow node in the knowledge graph."""
        try:
            query = """
            CREATE (w:Workflow {
                workflow_id: $workflow_id,
                plan_id: $plan_id,
                customer_id: $customer_id,
                advisor_id: $advisor_id,
                step_count: $step_count,
                estimated_duration: $estimated_duration,
                priority: $priority,
                created_at: $created_at,
                status: 'created'
            })
            """

            parameters = {
                'workflow_id': workflow_id,
                'plan_id': plan_id,
                'customer_id': customer_id,
                'advisor_id': advisor_id,
                'step_count': step_count,
                'estimated_duration': estimated_duration,
                'priority': priority,
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"⚡ Created Workflow node: {workflow_id}")
            return workflow_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Workflow creation failed: {str(e)}")

    async def create_execution_result(self, execution_id: str, workflow_id: str, step_id: Optional[str],
                                     success: bool, duration_seconds: int, error_message: Optional[str],
                                     result_data: Dict[str, Any]) -> str:
        """Create an ExecutionResult node in the knowledge graph."""
        try:
            query = """
            CREATE (e:ExecutionResult {
                execution_id: $execution_id,
                workflow_id: $workflow_id,
                step_id: $step_id,
                success: $success,
                duration_seconds: $duration_seconds,
                error_message: $error_message,
                result_data: $result_data,
                created_at: $created_at
            })
            """

            parameters = {
                'execution_id': execution_id,
                'workflow_id': workflow_id,
                'step_id': step_id,
                'success': success,
                'duration_seconds': duration_seconds,
                'error_message': error_message,
                'result_data': str(result_data),  # Convert to string for storage
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🎯 Created ExecutionResult node: {execution_id}")
            return execution_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"ExecutionResult creation failed: {str(e)}")

    async def create_hypothesis_node(self, hypothesis_id: str, source_stage: str, priority: str,
                                    reasoning: str, context: Dict[str, Any]) -> str:
        """Create a Hypothesis node in the knowledge graph."""
        try:
            query = """
            CREATE (h:Hypothesis {
                hypothesis_id: $hypothesis_id,
                source_stage: $source_stage,
                priority: $priority,
                reasoning: $reasoning,
                context: $context,
                evidence_count: 1,
                status: 'unvalidated',
                created_at: $created_at
            })
            """

            parameters = {
                'hypothesis_id': hypothesis_id,
                'source_stage': source_stage,
                'priority': priority,
                'reasoning': reasoning,
                'context': str(context),  # Convert to string for storage
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"💡 Created Hypothesis node: {hypothesis_id}")
            return hypothesis_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Hypothesis creation failed: {str(e)}")

    async def create_prediction_node(self, prediction_id: str, source_stage: str, priority: str,
                                    reasoning: str, context: Dict[str, Any]) -> str:
        """Create a Prediction node in the knowledge graph."""
        try:
            query = """
            CREATE (p:Prediction {
                prediction_id: $prediction_id,
                source_stage: $source_stage,
                priority: $priority,
                reasoning: $reasoning,
                context: $context,
                probability: 0.7,
                confidence: 0.7,
                time_horizon: 'short_term',
                created_at: $created_at,
                status: 'active'
            })
            """

            parameters = {
                'prediction_id': prediction_id,
                'source_stage': source_stage,
                'priority': priority,
                'reasoning': reasoning,
                'context': str(context),  # Convert to string for storage
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔮 Created Prediction node: {prediction_id}")
            return prediction_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Prediction creation failed: {str(e)}")

    async def create_wisdom_node(self, wisdom_id: str, source_stage: str, priority: str,
                                reasoning: str, context: Dict[str, Any]) -> str:
        """Create a Wisdom node in the knowledge graph."""
        try:
            query = """
            CREATE (w:Wisdom {
                wisdom_id: $wisdom_id,
                source_stage: $source_stage,
                priority: $priority,
                reasoning: $reasoning,
                context: $context,
                effectiveness_score: 0.8,
                application_count: 0,
                created_at: $created_at,
                status: 'active'
            })
            """

            parameters = {
                'wisdom_id': wisdom_id,
                'source_stage': source_stage,
                'priority': priority,
                'reasoning': reasoning,
                'context': str(context),  # Convert to string for storage
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🧠 Created Wisdom node: {wisdom_id}")
            return wisdom_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Wisdom creation failed: {str(e)}")

    def create_or_update_customer_sync(self, customer_id: str, **kwargs):
        """Synchronous wrapper for customer creation."""
        try:
            # Create sync connection for event handlers
            conn = kuzu.Connection(self.db)

            query = """
            MERGE (c:Customer {customer_id: $customer_id})
            ON CREATE SET
                c.created_at = $created_at,
                c.name = $name,
                c.email = $email,
                c.phone = $phone
            ON MATCH SET
                c.name = coalesce($name, c.name),
                c.email = coalesce($email, c.email),
                c.phone = coalesce($phone, c.phone)
            """

            parameters = {
                'customer_id': customer_id,
                'created_at': datetime.utcnow(),
                'name': kwargs.get('name', f'Customer_{customer_id}'),
                'email': kwargs.get('email', f'{customer_id}@example.com'),
                'phone': kwargs.get('phone', '555-0000')
            }

            conn.execute(query, parameters)
            logger.info(f"📞 Created/updated customer: {customer_id}")
            return customer_id

        except Exception as e:
            logger.error(f"Failed to create customer {customer_id}: {e}")
            raise UnifiedGraphManagerError(f"Customer creation failed: {str(e)}")

    def create_transcript_sync(self, transcript_id: str, **kwargs):
        """Synchronous wrapper for transcript creation."""
        try:
            # Create sync connection for event handlers
            conn = kuzu.Connection(self.db)

            query = """
            CREATE (t:Transcript {
                transcript_id: $transcript_id,
                customer_id: $customer_id,
                content: $content,
                duration_seconds: $duration_seconds,
                channel: $channel,
                created_at: $created_at
            })
            """

            parameters = {
                'transcript_id': transcript_id,
                'customer_id': kwargs.get('customer_id', 'unknown'),
                'content': kwargs.get('content', ''),
                'duration_seconds': kwargs.get('duration_seconds', 0),
                'channel': kwargs.get('channel', 'phone'),
                'created_at': datetime.utcnow()
            }

            conn.execute(query, parameters)
            logger.info(f"📝 Created transcript: {transcript_id}")
            return transcript_id

        except Exception as e:
            logger.error(f"Failed to create transcript {transcript_id}: {e}")
            raise UnifiedGraphManagerError(f"Transcript creation failed: {str(e)}")

    def create_analysis_sync(self, analysis_data: Dict[str, Any]) -> str:
        """Synchronous wrapper for analysis creation."""
        try:
            # Create sync connection for event handlers
            conn = kuzu.Connection(self.db)
            analysis_id = analysis_data.get('analysis_id', f"ANALYSIS_{uuid.uuid4().hex[:8]}")
            query = """
            CREATE (a:Analysis {
                analysis_id: $analysis_id,
                call_id: $call_id,
                transcript_id: $transcript_id,
                intent: $intent,
                urgency_level: $urgency_level,
                sentiment: $sentiment,
                confidence_score: $confidence_score,
                risk_factors: $risk_factors,
                compliance_issues: $compliance_issues,
                customer_satisfaction: $customer_satisfaction,
                analysis_summary: $analysis_summary,
                llm_reasoning: $llm_reasoning,
                analyzed_at: $analyzed_at,
                analyzer_version: $analyzer_version,
                processing_time_ms: $processing_time_ms
            })
            """
            params = {
                'analysis_id': analysis_id,
                'call_id': analysis_data.get('call_id'),
                'transcript_id': analysis_data.get('transcript_id'),
                'intent': analysis_data.get('intent'),
                'urgency_level': analysis_data.get('urgency_level'),
                'sentiment': analysis_data.get('sentiment'),
                'confidence_score': analysis_data.get('confidence_score', 0.0),
                'risk_factors': analysis_data.get('risk_factors', ''),
                'compliance_issues': analysis_data.get('compliance_issues', ''),
                'customer_satisfaction': analysis_data.get('customer_satisfaction', ''),
                'analysis_summary': analysis_data.get('analysis_summary', ''),
                'llm_reasoning': analysis_data.get('llm_reasoning', ''),
                'analyzed_at': analysis_data.get('analyzed_at', datetime.utcnow()),
                'analyzer_version': analysis_data.get('analyzer_version', 'v1.0'),
                'processing_time_ms': analysis_data.get('processing_time_ms', 0)
            }
            conn.execute(query, params)
            logger.info(f"📊 Created analysis: {analysis_id}")
            return analysis_id
        except Exception as e:
            logger.error(f"Failed to create analysis {analysis_id}: {e}")
            raise UnifiedGraphManagerError(f"Analysis creation failed: {str(e)}")

    def update_customer_risk_profile_sync(self, customer_id: str, risk_score: float, compliance_flags: list) -> None:
        """Synchronous wrapper for customer risk profile update."""
        try:
            # Create sync connection for event handlers
            conn = kuzu.Connection(self.db)
            query = """
            MATCH (c:Customer {customer_id: $customer_id})
            SET c.risk_score = $risk_score,
                c.compliance_flags = $compliance_flags,
                c.last_updated = $last_updated
            """
            params = {
                'customer_id': customer_id,
                'risk_score': risk_score,
                'compliance_flags': str(compliance_flags),  # Convert list to string for storage
                'last_updated': datetime.utcnow()
            }
            conn.execute(query, params)
            logger.info(f"🎯 Updated risk profile for customer: {customer_id}")
        except Exception as e:
            logger.error(f"Failed to update customer risk profile {customer_id}: {e}")
            raise UnifiedGraphManagerError(f"Customer risk profile update failed: {str(e)}")

    def create_transcript(self, transcript_id: str, customer_id: str, advisor_id: str,
                         topic: str, urgency: str, channel: str, started_at: str, status: str):
        """Synchronous wrapper for transcript creation."""
        try:
            # Create the Call node (transcript becomes a call)
            query = """
            CREATE (c:Call {
                call_id: $transcript_id,
                customer_id: $customer_id,
                advisor_id: $advisor_id,
                topic: $topic,
                urgency_level: $urgency,
                channel: $channel,
                started_at: $started_at,
                status: $status,
                created_at: $created_at
            })
            """

            parameters = {
                'transcript_id': transcript_id,
                'customer_id': customer_id,
                'advisor_id': advisor_id,
                'topic': topic,
                'urgency': urgency,
                'channel': channel,
                'started_at': started_at,
                'status': status,
                'created_at': datetime.utcnow()
            }

            self._connection.execute(query, parameters)

            # Create relationships
            rel_query = """
            MATCH (c:Call {call_id: $transcript_id}), (cust:Customer {customer_id: $customer_id}), (adv:Advisor {advisor_id: $advisor_id})
            CREATE (cust)-[:MADE_CALL]->(c)
            CREATE (adv)-[:HANDLED_CALL]->(c)
            """

            self._connection.execute(rel_query, parameters)
            logger.info(f"📞 Created call and relationships: {transcript_id}")
            return transcript_id

        except Exception as e:
            logger.error(f"Failed to create transcript {transcript_id}: {e}")
            raise UnifiedGraphManagerError(f"Transcript creation failed: {str(e)}")

    async def get_patterns_by_context(self, context: Dict[str, Any]) -> List:
        """Get patterns relevant to the current context."""
        # Placeholder - return empty list for now
        logger.info(f"🔍 Searching patterns for context: {context.get('customer_id', 'unknown')}")
        return []

    async def store_prediction(self, prediction) -> str:
        """Store prediction in knowledge graph."""
        try:
            query = """
            CREATE (p:Prediction {
                prediction_id: $prediction_id,
                prediction_type: $prediction_type,
                target_entity: $target_entity,
                target_entity_id: $target_entity_id,
                predicted_event: $predicted_event,
                probability: $probability,
                confidence: $confidence,
                created_at: $created_at,
                expires_at: $expires_at
            })
            """

            parameters = {
                'prediction_id': prediction.prediction_id,
                'prediction_type': prediction.prediction_type,
                'target_entity': prediction.target_entity,
                'target_entity_id': prediction.target_entity_id,
                'predicted_event': prediction.predicted_event,
                'probability': prediction.probability,
                'confidence': prediction.confidence,
                'created_at': prediction.created_at if hasattr(prediction.created_at, 'isoformat') else datetime.utcnow(),
                'expires_at': prediction.expires_at if hasattr(prediction.expires_at, 'isoformat') else datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔮 Stored prediction: {prediction.prediction_id}")
            return prediction.prediction_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Prediction storage failed: {str(e)}")

    async def store_pattern(self, pattern) -> str:
        """Store pattern in knowledge graph."""
        try:
            # Store as Hypothesis (new approach)
            query = """
            CREATE (h:Hypothesis {
                hypothesis_id: $pattern_id,
                pattern_type: $pattern_type,
                title: $title,
                description: $description,
                confidence: $confidence,
                evidence_count: $occurrences,
                success_rate: $success_rate,
                last_observed: $last_observed,
                source_pipeline: $source_pipeline,
                status: 'unvalidated',
                created_at: $created_at
            })
            """

            parameters = {
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'title': pattern.title,
                'description': pattern.description,
                'confidence': pattern.confidence,
                'occurrences': pattern.occurrences,
                'success_rate': pattern.success_rate,
                'last_observed': pattern.last_observed.isoformat() if hasattr(pattern.last_observed, 'isoformat') else str(pattern.last_observed),
                'source_pipeline': pattern.source_pipeline,
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"📊 Stored pattern as hypothesis: {pattern.pattern_id}")
            return pattern.pattern_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Pattern storage failed: {str(e)}")

    async def create_or_update_customer(self, customer_id: str, **kwargs) -> str:
        """Create or update customer in knowledge graph."""
        try:
            query = """
            MERGE (c:Customer {customer_id: $customer_id})
            ON CREATE SET
                c.created_at = $created_at,
                c.total_interactions = $total_interactions,
                c.risk_score = $risk_score,
                c.satisfaction_score = $satisfaction_score,
                c.last_contact_date = $last_contact_date
            ON MATCH SET
                c.total_interactions = c.total_interactions + 1,
                c.last_contact_date = $last_contact_date,
                c.risk_score = $risk_score
            """

            parameters = {
                'customer_id': customer_id,
                'created_at': datetime.utcnow(),
                'total_interactions': kwargs.get('total_interactions', 1),
                'last_contact_date': kwargs.get('last_contact_date', datetime.utcnow()),
                'risk_score': kwargs.get('risk_score', 0.5),
                'satisfaction_score': kwargs.get('satisfaction_score', 0.7)
            }

            await self._execute_async(query, parameters)
            logger.info(f"📞 Created/updated customer: {customer_id}")
            return customer_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Customer creation failed: {str(e)}")

    async def create_call_node(self, call_id: str, **kwargs) -> str:
        """Create call node in knowledge graph."""
        try:
            query = """
            CREATE (c:Call {
                call_id: $call_id,
                transcript_id: $transcript_id,
                customer_id: $customer_id,
                advisor_id: $advisor_id,
                topic: $topic,
                urgency_level: $urgency_level,
                sentiment: $sentiment,
                resolved: $resolved,
                call_date: $call_date,
                created_at: $created_at
            })
            """

            parameters = {
                'call_id': call_id,
                'transcript_id': kwargs.get('transcript_id'),
                'customer_id': kwargs.get('customer_id'),
                'advisor_id': kwargs.get('advisor_id', 'UNKNOWN'),
                'topic': kwargs.get('topic', 'general inquiry'),
                'urgency_level': kwargs.get('urgency_level', 'medium'),
                'sentiment': kwargs.get('sentiment', 'neutral'),
                'resolved': kwargs.get('resolved', False),
                'call_date': kwargs.get('call_date', datetime.utcnow()),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"📞 Created call node: {call_id}")
            return call_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Call creation failed: {str(e)}")

    async def link_call_to_pattern(self, call_id: str, pattern_id: str, **kwargs) -> bool:
        """Link call to pattern in knowledge graph."""
        try:
            query = """
            MATCH (c:Call {call_id: $call_id}), (h:Hypothesis {hypothesis_id: $pattern_id})
            CREATE (c)-[:TRIGGERED_HYPOTHESIS {strength: $strength, created_at: $created_at}]->(h)
            """

            parameters = {
                'call_id': call_id,
                'pattern_id': pattern_id,
                'strength': kwargs.get('strength', 0.8),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔗 Linked call {call_id} to hypothesis {pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link call to pattern: {e}")
            return False

    async def store_wisdom(self, wisdom) -> str:
        """Store wisdom in knowledge graph."""
        try:
            query = """
            CREATE (w:Wisdom {
                wisdom_id: $wisdom_id,
                wisdom_type: $wisdom_type,
                title: $title,
                content: $content,
                learning_domain: $learning_domain,
                applicability: $applicability,
                validated: $validated,
                effectiveness_score: $effectiveness_score,
                application_count: $application_count,
                created_at: $created_at
            })
            """

            parameters = {
                'wisdom_id': wisdom.wisdom_id,
                'wisdom_type': wisdom.wisdom_type,
                'title': wisdom.title,
                'content': wisdom.content,
                'learning_domain': wisdom.learning_domain,
                'applicability': wisdom.applicability,
                'validated': wisdom.validated,
                'effectiveness_score': wisdom.effectiveness_score,
                'application_count': wisdom.application_count,
                'created_at': wisdom.created_at.isoformat() if hasattr(wisdom.created_at, 'isoformat') else str(wisdom.created_at)
            }

            await self._execute_async(query, parameters)
            logger.info(f"🧠 Stored wisdom: {wisdom.wisdom_id}")
            return wisdom.wisdom_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Wisdom storage failed: {str(e)}")

    async def store_meta_learning(self, meta_learning) -> str:
        """Store meta-learning in knowledge graph."""
        try:
            query = """
            CREATE (m:MetaLearning {
                meta_learning_id: $meta_learning_id,
                learning_type: $learning_type,
                insight_source: $insight_source,
                meta_insight: $meta_insight,
                improvement_area: $improvement_area,
                system_component: $system_component,
                impact_assessment: $impact_assessment,
                validation_status: $validation_status,
                validation_count: $validation_count,
                created_at: $created_at
            })
            """

            parameters = {
                'meta_learning_id': meta_learning.meta_learning_id,
                'learning_type': meta_learning.learning_type,
                'insight_source': meta_learning.insight_source,
                'meta_insight': meta_learning.meta_insight,
                'improvement_area': meta_learning.improvement_area,
                'system_component': meta_learning.system_component,
                'impact_assessment': meta_learning.impact_assessment,
                'validation_status': meta_learning.validation_status,
                'validation_count': meta_learning.validation_count,
                'created_at': meta_learning.created_at.isoformat() if hasattr(meta_learning.created_at, 'isoformat') else str(meta_learning.created_at)
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔄 Stored meta-learning: {meta_learning.meta_learning_id}")
            return meta_learning.meta_learning_id

        except Exception as e:
            raise UnifiedGraphManagerError(f"Meta-learning storage failed: {str(e)}")

    async def link_prediction_to_customer(self, prediction_id: str, customer_id: str, **kwargs) -> bool:
        """Link prediction to customer in knowledge graph."""
        try:
            query = """
            MATCH (p:Prediction {prediction_id: $prediction_id}), (c:Customer {customer_id: $customer_id})
            CREATE (p)-[:TARGETS_CUSTOMER {scope: $scope, created_at: $created_at}]->(c)
            """

            parameters = {
                'prediction_id': prediction_id,
                'customer_id': customer_id,
                'scope': kwargs.get('scope', 'individual'),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔗 Linked prediction {prediction_id} to customer {customer_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link prediction to customer: {e}")
            return False

    async def link_wisdom_to_advisor(self, wisdom_id: str, advisor_id: str, **kwargs) -> bool:
        """Link wisdom to advisor in knowledge graph."""
        try:
            query = """
            MATCH (w:Wisdom {wisdom_id: $wisdom_id}), (a:Advisor {advisor_id: $advisor_id})
            CREATE (w)-[:APPLIES_TO_ADVISOR {relevance_score: $relevance_score, created_at: $created_at}]->(a)
            """

            parameters = {
                'wisdom_id': wisdom_id,
                'advisor_id': advisor_id,
                'relevance_score': kwargs.get('relevance_score', 0.8),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔗 Linked wisdom {wisdom_id} to advisor {advisor_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link wisdom to advisor: {e}")
            return False

    async def link_call_to_meta_learning(self, call_id: str, meta_learning_id: str, **kwargs) -> bool:
        """Link call to meta-learning in knowledge graph."""
        try:
            query = """
            MATCH (c:Call {call_id: $call_id}), (m:MetaLearning {meta_learning_id: $meta_learning_id})
            CREATE (c)-[:TRIGGERED_LEARNING {trigger_reason: $trigger_reason, created_at: $created_at}]->(m)
            """

            parameters = {
                'call_id': call_id,
                'meta_learning_id': meta_learning_id,
                'trigger_reason': kwargs.get('trigger_reason', 'knowledge_extraction'),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔗 Linked call {call_id} to meta-learning {meta_learning_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link call to meta-learning: {e}")
            return False

    async def link_customer_to_pattern(self, customer_id: str, pattern_id: str, **kwargs) -> bool:
        """Link customer to pattern in knowledge graph."""
        try:
            query = """
            MATCH (c:Customer {customer_id: $customer_id}), (h:Hypothesis {hypothesis_id: $pattern_id})
            CREATE (c)-[:TRIGGERED_HYPOTHESIS {trigger_strength: $trigger_strength, created_at: $created_at}]->(h)
            """

            parameters = {
                'customer_id': customer_id,
                'pattern_id': pattern_id,
                'trigger_strength': kwargs.get('trigger_strength', 0.8),
                'created_at': datetime.utcnow()
            }

            await self._execute_async(query, parameters)
            logger.info(f"🔗 Linked customer {customer_id} to hypothesis {pattern_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to link customer to pattern: {e}")
            return False

    async def _create_advisor_async(self, advisor_data: Dict[str, Any]) -> str:
        """Helper method to create advisor asynchronously."""
        try:
            query = """
            MERGE (a:Advisor {advisor_id: $advisor_id})
            ON CREATE SET
                a.created_at = $created_at,
                a.total_calls = 1,
                a.performance_score = $performance_score,
                a.skill_level = $skill_level
            ON MATCH SET
                a.total_calls = a.total_calls + 1,
                a.last_active = $created_at
            """

            parameters = {
                'advisor_id': advisor_data['advisor_id'],
                'created_at': datetime.utcnow(),
                'performance_score': advisor_data.get('performance_score', 0.8),
                'skill_level': advisor_data.get('skill_level', 'intermediate')
            }

            await self._execute_async(query, parameters)
            logger.info(f"👨‍💼 Created advisor: {advisor_data['advisor_id']}")
            return advisor_data['advisor_id']

        except Exception as e:
            logger.error(f"Failed to create advisor: {e}")
            raise UnifiedGraphManagerError(f"Advisor creation failed: {str(e)}")

    async def shutdown(self):
        """Clean shutdown of the graph manager."""
        if self._write_queue:
            await self._write_queue.put(None)  # Shutdown signal

        if self._write_processor_task:
            await self._write_processor_task


# Global manager instance
_global_manager = None

def get_unified_graph_manager() -> UnifiedGraphManager:
    """Get or create the global unified graph manager."""
    global _global_manager
    if _global_manager is None:
        _global_manager = UnifiedGraphManager()
    return _global_manager

def close_unified_graph_manager():
    """Close the global unified graph manager."""
    global _global_manager
    if _global_manager is not None:
        # Note: This is sync, but shutdown is async - need to handle properly in production
        _global_manager = None
        logger.info("✅ UnifiedGraphManager shutdown complete")

