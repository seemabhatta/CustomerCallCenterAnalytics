"""
Knowledge Graph Infrastructure for Customer Call Center Analytics.

Predictive knowledge graph with patterns, predictions, and wisdom.
"""
from .knowledge_types import (
    Pattern,
    Prediction,
    Wisdom,
    MetaLearning,
    PredictiveInsight
)

from .predictive_knowledge_extractor import (
    PredictiveKnowledgeExtractor,
    get_predictive_knowledge_extractor
)

# Legacy graph manager - optional import to avoid kuzu dependency issues
try:
    from .graph_manager import (
        GraphManager,
        GraphManagerError,
        get_graph_manager
    )
    LEGACY_GRAPH_AVAILABLE = True
except ImportError:
    LEGACY_GRAPH_AVAILABLE = False

__all__ = [
    'Pattern',
    'Prediction',
    'Wisdom',
    'MetaLearning',
    'PredictiveInsight',
    'PredictiveKnowledgeExtractor',
    'get_predictive_knowledge_extractor'
]

if LEGACY_GRAPH_AVAILABLE:
    __all__.extend(['GraphManager', 'GraphManagerError', 'get_graph_manager'])