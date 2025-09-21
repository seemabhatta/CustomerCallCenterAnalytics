"""
Queued GraphStore Wrapper

Wraps the existing GraphStore to use the KuzuDB write queue for all write operations.
This ensures thread-safe access to the single-writer KuzuDB database.
"""

from typing import Dict, Any, Optional
from concurrent.futures import Future
import logging

from .graph_store import GraphStore
from .kuzu_queue import get_kuzu_queue

logger = logging.getLogger(__name__)

class QueuedGraphStore:
    """
    Thread-safe wrapper around GraphStore that queues all write operations.

    Read operations are executed directly for performance.
    Write operations are queued to ensure single-writer access to KuzuDB.
    """

    _instance = None
    _lock = None

    def __new__(cls, db_path: str = "data/analytics_graph.db"):
        """Singleton pattern to ensure single GraphStore instance."""
        if cls._instance is None:
            import threading
            if cls._lock is None:
                cls._lock = threading.Lock()

            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "data/analytics_graph.db"):
        """Initialize the queued graph store (only once due to singleton)."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._graph_store = GraphStore(db_path)
        self._queue = get_kuzu_queue()
        self._queue.start(self._graph_store)
        self._initialized = True

        logger.info("✅ QueuedGraphStore initialized with write queue")

    # Write operations - these go through the queue

    def add_customer(self, customer_id: str, profile_type: str = "standard", risk_level: str = "low") -> Future:
        """Queue customer addition operation."""
        return self._queue.enqueue_operation("add_customer", customer_id, profile_type, risk_level)

    def add_transcript(self, transcript_id: str, topic: str, message_count: int) -> Future:
        """Queue transcript addition operation."""
        return self._queue.enqueue_operation("add_transcript", transcript_id, topic, message_count)

    def add_analysis_with_relationships(self, analysis_data: Dict[str, Any]) -> Future:
        """Queue analysis addition operation."""
        return self._queue.enqueue_operation("add_analysis_with_relationships", analysis_data)

    def add_plan_with_relationships(self, plan_data: Dict[str, Any]) -> Future:
        """Queue plan addition operation."""
        return self._queue.enqueue_operation("add_plan_with_relationships", plan_data)

    def add_workflow_with_steps(self, workflow_data: Dict[str, Any]) -> Future:
        """Queue workflow addition operation."""
        return self._queue.enqueue_operation("add_workflow_with_steps", workflow_data)

    def add_execution_with_relationships(self, execution_data: Dict[str, Any]) -> Future:
        """Queue execution addition operation."""
        return self._queue.enqueue_operation("add_execution_with_relationships", execution_data)

    # Read operations - these execute directly for performance

    def execute_query(self, cypher_query: str, parameters: Optional[Dict] = None):
        """Execute read queries directly (not queued)."""
        return self._graph_store.execute_query(cypher_query, parameters)

    def get_transcript_analysis_chain(self, transcript_id: str):
        """Get transcript analysis chain directly."""
        return self._graph_store.get_transcript_analysis_chain(transcript_id)

    def get_workflows_for_plan(self, plan_id: str):
        """Get workflows for plan directly."""
        return self._graph_store.get_workflows_for_plan(plan_id)

    def find_similar_transcripts(self, analysis_data: Dict[str, Any], limit: int = 5):
        """Find similar transcripts directly."""
        return self._graph_store.find_similar_transcripts(analysis_data, limit)

    # Utility methods

    def wait_for_operations(self, timeout: Optional[float] = 30) -> bool:
        """
        Wait for all queued operations to complete.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if all operations completed, False if timeout occurred
        """
        return self._queue.wait_for_empty(timeout)

    def get_queue_size(self) -> int:
        """Get the number of pending write operations."""
        return self._queue.get_queue_size()

    def stop_queue(self):
        """Stop the write queue (useful for testing/shutdown)."""
        self._queue.stop()

# Convenience functions for backward compatibility

def get_queued_graph_store() -> QueuedGraphStore:
    """Get the global queued graph store instance."""
    return QueuedGraphStore()

# Async-style helper functions that return results instead of futures

def add_customer_sync(customer_id: str, profile_type: str = "standard", risk_level: str = "low") -> bool:
    """Add customer and wait for result."""
    future = get_queued_graph_store().add_customer(customer_id, profile_type, risk_level)
    return future.result(timeout=10)

def add_transcript_sync(transcript_id: str, topic: str, message_count: int) -> bool:
    """Add transcript and wait for result."""
    future = get_queued_graph_store().add_transcript(transcript_id, topic, message_count)
    return future.result(timeout=10)

def add_analysis_sync(analysis_data: Dict[str, Any]) -> bool:
    """Add analysis and wait for result."""
    future = get_queued_graph_store().add_analysis_with_relationships(analysis_data)
    return future.result(timeout=10)

def add_plan_sync(plan_data: Dict[str, Any]) -> bool:
    """Add plan and wait for result."""
    future = get_queued_graph_store().add_plan_with_relationships(plan_data)
    return future.result(timeout=10)

def add_workflow_sync(workflow_data: Dict[str, Any]) -> bool:
    """Add workflow and wait for result."""
    future = get_queued_graph_store().add_workflow_with_steps(workflow_data)
    return future.result(timeout=10)

def add_execution_sync(execution_data: Dict[str, Any]) -> bool:
    """Add execution and wait for result."""
    future = get_queued_graph_store().add_execution_with_relationships(execution_data)
    return future.result(timeout=10)