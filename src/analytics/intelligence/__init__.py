"""
Intelligence layer for GenAI-powered insights and recommendations.

This module combines Prophet forecasts with contextual analysis using LLMs
to generate actionable business intelligence.
"""

from .insight_generator import InsightGenerator
from .prompt_loader import PromptLoader

__all__ = ['InsightGenerator', 'PromptLoader']
