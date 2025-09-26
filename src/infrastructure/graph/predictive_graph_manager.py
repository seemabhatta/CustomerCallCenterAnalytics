"""
Predictive Graph Manager - KuzuDB operations for knowledge storage and retrieval.

Manages the storage and querying of patterns, predictions, wisdom, and meta-learning
in the KuzuDB knowledge graph database.
"""
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import kuzu

from .knowledge_types import Pattern, Prediction, Wisdom, MetaLearning

logger = logging.getLogger(__name__)


class PredictiveGraphManager:
    """
    Manages predictive knowledge storage and retrieval in KuzuDB.

    Stores patterns, predictions, wisdom, and meta-learning for the system
    to learn from and make better decisions over time.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            from ..config.database_config import get_knowledge_graph_database_path
            db_path = get_knowledge_graph_database_path()
        self.db_path = db_path
        self.db = kuzu.Database(db_path)

        # NO FALLBACK: Connection pooling for KuzuDB operations
        # Create multiple connections for better concurrency
        self._connection_pool = []
        self._pool_size = 4
        for i in range(self._pool_size):
            conn = kuzu.Connection(self.db)
            self._connection_pool.append(conn)

        # Primary connection for schema initialization
        self.conn = self._connection_pool[0]

        # Track available connections for pooling
        self._available_connections = asyncio.Queue(maxsize=self._pool_size)
        for conn in self._connection_pool:
            self._available_connections.put_nowait(conn)

        # NO FALLBACK: Thread pool for async database operations
        self._executor = ThreadPoolExecutor(max_workers=self._pool_size, thread_name_prefix="kuzu_db")

        self._init_knowledge_schema()

    def _init_knowledge_schema(self) -> None:
        """Initialize the knowledge schema in KuzuDB."""
        try:
            # Pattern node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Pattern(
                    pattern_id STRING,
                    pattern_type STRING,
                    title STRING,
                    description STRING,
                    conditions STRING,
                    outcomes STRING,
                    confidence DOUBLE,
                    occurrences INT64,
                    success_rate DOUBLE,
                    last_observed STRING,
                    source_pipeline STRING,
                    PRIMARY KEY (pattern_id)
                )
            """)

            # Prediction node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Prediction(
                    prediction_id STRING,
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
                    validation_date STRING,
                    PRIMARY KEY (prediction_id)
                )
            """)

            # Wisdom node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS Wisdom(
                    wisdom_id STRING,
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
                    application_success_rate DOUBLE,
                    PRIMARY KEY (wisdom_id)
                )
            """)

            # MetaLearning node table
            self.conn.execute("""
                CREATE NODE TABLE IF NOT EXISTS MetaLearning(
                    meta_id STRING,
                    meta_type STRING,
                    learning_insight STRING,
                    improvement_opportunity STRING,
                    optimization_suggestion STRING,
                    accuracy_metrics STRING,
                    learning_velocity DOUBLE,
                    knowledge_gaps STRING,
                    observed_at STRING,
                    system_version STRING,
                    PRIMARY KEY (meta_id)
                )
            """)

            # Relationship tables for knowledge connections
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
                    derivation_confidence DOUBLE,
                    statistical_significance DOUBLE
                )
            """)

            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS IMPROVES(
                    FROM MetaLearning TO Wisdom,
                    improvement_type STRING,
                    expected_impact DOUBLE
                )
            """)

            logger.info("✅ Knowledge schema initialized in KuzuDB")

        except Exception as e:
            logger.error(f"Failed to initialize knowledge schema: {e}")
            raise RuntimeError(f"Knowledge schema initialization failed: {str(e)}")

    async def _get_connection(self):
        """Get an available connection from the pool."""
        try:
            # Wait for available connection with timeout
            return await asyncio.wait_for(self._available_connections.get(), timeout=30.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Database connection pool exhausted - no connections available")

    async def _return_connection(self, conn):
        """Return a connection to the pool."""
        try:
            self._available_connections.put_nowait(conn)
        except asyncio.QueueFull:
            logger.warning("Connection pool full, discarding connection")

    async def _execute_async(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        """Execute KuzuDB query asynchronously with connection pooling.

        Args:
            query: KuzuDB query string
            parameters: Query parameters

        Returns:
            Query result

        Raises:
            RuntimeError: If query execution fails (NO FALLBACK)
        """
        conn = await self._get_connection()
        loop = asyncio.get_event_loop()

        def _execute():
            try:
                if parameters:
                    return conn.execute(query, parameters=parameters)
                else:
                    return conn.execute(query)
            except Exception as e:
                # NO FALLBACK: Database errors must be propagated
                raise RuntimeError(f"KuzuDB query failed: {str(e)}")

        try:
            result = await loop.run_in_executor(self._executor, _execute)
            return result
        finally:
            # Always return connection to pool
            await self._return_connection(conn)

    async def store_pattern(self, pattern: Pattern) -> bool:
        """Store a pattern in the knowledge graph."""
        try:
            import json
            # NO FALLBACK: Use async executor to prevent event loop blocking
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
            """, parameters={
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
            raise RuntimeError(f"Pattern storage failed: {str(e)}")

    async def store_prediction(self, prediction: Prediction) -> bool:
        """Store a prediction in the knowledge graph."""
        try:
            import json
            # NO FALLBACK: Use async execution like other methods to prevent event loop blocking
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
            """, parameters={
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
            raise RuntimeError(f"Prediction storage failed: {str(e)}")

    async def store_wisdom(self, wisdom: Wisdom) -> bool:
        """Store wisdom in the knowledge graph."""
        try:
            import json
            # NO FALLBACK: Use async execution to prevent event loop blocking
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
            """, parameters={
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
            raise RuntimeError(f"Wisdom storage failed: {str(e)}")

    async def store_meta_learning(self, meta_learning: MetaLearning) -> bool:
        """Store meta-learning in the knowledge graph."""
        try:
            import json
            # NO FALLBACK: Use async execution to prevent event loop blocking
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
            """, parameters={
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
            raise RuntimeError(f"Meta-learning storage failed: {str(e)}")

    async def get_patterns_by_context(self, context: Dict[str, Any]) -> List[Pattern]:
        """Get patterns relevant to the given context."""
        try:
            import json
            from datetime import datetime

            # Build context-aware query
            customer_id = context.get('customer_id', '')
            topic = context.get('topic', '')
            urgency = context.get('urgency', '')

            # Query patterns with context matching (proper KuzuDB syntax)
            query = """
                MATCH (p:Pattern)
                WHERE p.source_pipeline = 'analysis'
                   OR p.title CONTAINS $topic
                   OR p.description CONTAINS $topic
                   OR p.pattern_type = 'risk_escalation'
                RETURN p
                ORDER BY p.confidence DESC, p.success_rate DESC
                LIMIT 5
            """

            # NO FALLBACK: Use async executor to prevent event loop blocking
            result = await self._execute_async(query, parameters={'topic': topic})
            patterns = []

            while result.has_next():
                row = result.get_next()
                pattern_data = row[0]

                # Convert KuzuDB result back to Pattern object
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

            logger.info(f"🔍 Retrieved {len(patterns)} patterns for context: {context}")
            return patterns

        except Exception as e:
            logger.error(f"Failed to get patterns by context: {e}")
            # NO FALLBACK: Fail fast on query errors
            raise RuntimeError(f"Pattern retrieval failed: {str(e)}")

    async def get_predictions_for_entity(self, entity_type: str, entity_id: str) -> List[Prediction]:
        """Get active predictions for a specific entity."""
        try:
            import json
            from datetime import datetime

            # Query active predictions for entity
            # NO FALLBACK: Use async executor to prevent event loop blocking
            result = await self._execute_async("""
                MATCH (p:Prediction)
                WHERE p.target_entity = $entity_type
                  AND p.target_entity_id = $entity_id
                  AND (p.expires_at IS NULL OR p.expires_at > $current_time)
                  AND p.validated IS NULL
                RETURN p
                ORDER BY p.probability DESC, p.confidence DESC
            """, parameters={
                'entity_type': entity_type,
                'entity_id': entity_id,
                'current_time': datetime.utcnow().isoformat()
            })

            predictions = []
            while result.has_next():
                row = result.get_next()
                prediction_data = row[0]

                # Convert KuzuDB result back to Prediction object
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
            # NO FALLBACK: Fail fast on query errors
            raise RuntimeError(f"Prediction retrieval failed: {str(e)}")

    async def validate_prediction(self, prediction_id: str, outcome: bool) -> bool:
        """Validate a prediction with actual outcome."""
        try:
            # NO FALLBACK: Use async executor to prevent event loop blocking
            await self._execute_async("""
                MATCH (p:Prediction {prediction_id: $prediction_id})
                SET p.validated = $outcome, p.validation_date = $validation_date
            """, parameters={
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
            # Increment occurrences and update last_observed
            self.conn.execute("""
                MATCH (p:Pattern {pattern_id: $pattern_id})
                SET p.occurrences = p.occurrences + 1, p.last_observed = $last_observed
            """, parameters={
                'pattern_id': pattern_id,
                'last_observed': datetime.utcnow().isoformat()
            })
            logger.info(f"📊 Updated pattern {pattern_id} with new evidence")
            return True

        except Exception as e:
            logger.error(f"Failed to update pattern {pattern_id}: {e}")
            return False

    def close(self) -> None:
        """Close all database connections and cleanup resources."""
        # Close all connections in the pool
        if hasattr(self, '_connection_pool'):
            for conn in self._connection_pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")

        # NO FALLBACK: Properly cleanup thread pool to prevent resource leaks
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)

        logger.info("📝 Closed all KuzuDB connections and cleaned up resources")