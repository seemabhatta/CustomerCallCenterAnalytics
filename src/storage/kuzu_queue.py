"""
KuzuDB Write Queue Manager

Handles serialized writes to KuzuDB to prevent concurrent access issues.
KuzuDB is a single-writer database, so all writes must be queued and processed sequentially.
"""

import threading
import queue
import time
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from concurrent.futures import Future
import logging

logger = logging.getLogger(__name__)

@dataclass
class KuzuOperation:
    """Represents a queued KuzuDB operation."""
    operation_type: str
    method_name: str
    args: tuple
    kwargs: dict
    future: Future
    timestamp: float
    operation_id: str

class KuzuWriteQueue:
    """
    Thread-safe write queue for KuzuDB operations.

    Ensures all KuzuDB writes are executed sequentially to prevent
    concurrent access conflicts in the single-writer database.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern to ensure single queue instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the write queue (only once due to singleton)."""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._queue = queue.Queue()
        self._worker_thread = None
        self._stop_event = threading.Event()
        self._graph_store = None
        self._operation_counter = 0
        self._initialized = True

    def start(self, graph_store):
        """Start the queue worker thread."""
        if self._worker_thread is not None and self._worker_thread.is_alive():
            return

        self._graph_store = graph_store
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        logger.info("🚀 KuzuDB write queue started")

    def stop(self):
        """Stop the queue worker thread."""
        if self._worker_thread is None:
            return

        self._stop_event.set()
        self._worker_thread.join(timeout=5)
        logger.info("🛑 KuzuDB write queue stopped")

    def enqueue_operation(self, method_name: str, *args, **kwargs) -> Future:
        """
        Queue a KuzuDB operation for execution.

        Args:
            method_name: Name of the GraphStore method to call
            *args: Arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            Future object that will contain the operation result
        """
        if self._graph_store is None:
            raise RuntimeError("KuzuDB write queue not started")

        future = Future()
        self._operation_counter += 1
        operation_id = f"OP_{self._operation_counter:06d}"

        operation = KuzuOperation(
            operation_type="write",
            method_name=method_name,
            args=args,
            kwargs=kwargs,
            future=future,
            timestamp=time.time(),
            operation_id=operation_id
        )

        self._queue.put(operation)
        logger.debug(f"📝 Queued operation {operation_id}: {method_name}")

        return future

    def _worker(self):
        """Worker thread that processes queued operations sequentially."""
        logger.info("🔄 KuzuDB write queue worker started")

        while not self._stop_event.is_set():
            try:
                # Get operation with timeout to allow checking stop event
                operation = self._queue.get(timeout=1.0)

                try:
                    # Execute the operation
                    start_time = time.time()
                    method = getattr(self._graph_store, operation.method_name)
                    result = method(*operation.args, **operation.kwargs)

                    # Set the result
                    operation.future.set_result(result)

                    execution_time = time.time() - start_time
                    logger.debug(f"✅ Completed operation {operation.operation_id}: {operation.method_name} in {execution_time:.3f}s")

                except Exception as e:
                    # Set the exception
                    operation.future.set_exception(e)
                    logger.error(f"❌ Failed operation {operation.operation_id}: {operation.method_name} - {str(e)}")

                finally:
                    self._queue.task_done()

            except queue.Empty:
                # Timeout - check if we should stop
                continue
            except Exception as e:
                logger.error(f"❌ Worker thread error: {str(e)}")

        logger.info("🔄 KuzuDB write queue worker stopped")

    def get_queue_size(self) -> int:
        """Get the current number of queued operations."""
        return self._queue.qsize()

    def wait_for_empty(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for the queue to be empty.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if queue became empty, False if timeout occurred
        """
        start_time = time.time()

        while not self._queue.empty():
            if timeout and (time.time() - start_time) > timeout:
                return False
            time.sleep(0.1)

        return True

# Global queue instance
_kuzu_queue = KuzuWriteQueue()

def get_kuzu_queue() -> KuzuWriteQueue:
    """Get the global KuzuDB write queue instance."""
    return _kuzu_queue