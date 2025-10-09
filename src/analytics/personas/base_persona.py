"""
Abstract base class for persona-specific transformations.

Each persona transforms the same underlying data to answer their specific questions:
- Leadership: "What's the dollar impact? What decisions do I need to make?"
- Servicing Ops: "What's breaking? Who needs help? Are we meeting SLAs?"
- Marketing: "Who should we target? What campaigns should we launch?"
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import sqlite3


class BasePersona(ABC):
    """Base class for persona-specific data transformations."""

    def __init__(self, db_path: str = "data/call_center.db"):
        """
        Initialize persona.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    @abstractmethod
    def transform_forecast(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform forecast data for persona-specific view.

        Args:
            forecast: Raw forecast from Prophet service

        Returns:
            Transformed forecast data
        """
        pass

    @abstractmethod
    def get_key_metrics(self) -> Dict[str, Any]:
        """
        Get the key metrics this persona cares about.

        Returns:
            Dict of metrics relevant to this persona
        """
        pass

    @abstractmethod
    def get_recommended_actions(self) -> list[Dict[str, Any]]:
        """
        Get recommended actions for this persona.

        Returns:
            List of actionable recommendations
        """
        pass

    def _query_db(self, query: str, params: tuple = ()) -> list[tuple]:
        """
        Execute database query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Query results
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results

    def _query_db_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """
        Execute database query expecting single result.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Single result or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result
