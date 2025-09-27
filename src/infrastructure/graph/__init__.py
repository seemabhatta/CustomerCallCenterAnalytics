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

# Unified graph manager
from .unified_graph_manager import (
    UnifiedGraphManager,
    get_unified_graph_manager,
    close_unified_graph_manager
)

__all__ = [
    'Pattern',
    'Prediction',
    'Wisdom',
    'MetaLearning',
    'PredictiveInsight',
    'PredictiveKnowledgeExtractor',
    'get_predictive_knowledge_extractor',
    'UnifiedGraphManager',
    'get_unified_graph_manager',
    'close_unified_graph_manager'
]