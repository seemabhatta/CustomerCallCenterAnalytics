"""
Knowledge Graph Infrastructure for Customer Call Center Analytics.

Enhanced graph management with comprehensive entity model and event-driven updates.
"""
from .graph_manager import (
    GraphManager,
    GraphManagerError,
    get_graph_manager
)

__all__ = [
    'GraphManager',
    'GraphManagerError',
    'get_graph_manager'
]