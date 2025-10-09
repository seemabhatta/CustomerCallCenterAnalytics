"""
Hybrid analyzer that combines Prophet forecasts with GenAI contextual analysis.

This module orchestrates:
1. Prophet service generates time-series forecasts (numbers)
2. GenAI analyzes those numbers in context (insights)
3. Returns actionable intelligence for personas
"""

import json
import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.services.forecasting_service import ForecastingService
from src.infrastructure.llm.llm_client_v2 import LLMClientV2
from .insight_generator import InsightGenerator


class HybridAnalyzer:
    """
    Combines Prophet forecasts with GenAI analysis.

    The power combo:
    - Prophet: "Call volume will increase 40% next week"
    - GenAI: "Due to payment processing delays + end-of-month pattern.
             Recommend shifting 3 advisors from refi team."
    """

    def __init__(
        self,
        forecasting_service: ForecastingService,
        llm_client: Optional[LLMClientV2] = None,
        db_path: str = "data/call_center.db"
    ):
        """
        Initialize hybrid analyzer.

        Args:
            forecasting_service: Prophet forecasting service
            llm_client: LLM client for GenAI analysis
            db_path: Path to SQLite database
        """
        self.forecasting_service = forecasting_service
        self.llm_client = llm_client or LLMClientV2()
        self.insight_generator = InsightGenerator(llm_client)
        self.db_path = db_path

    async def analyze_with_forecast(
        self,
        forecast_type: str,
        prompt_name: str,
        additional_context: Optional[Dict[str, Any]] = None,
        horizon_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate forecast and analyze it with GenAI.

        Args:
            forecast_type: Type of forecast to generate
            prompt_name: Name of prompt template for analysis
            additional_context: Extra context to pass to LLM
            horizon_days: Forecast horizon

        Returns:
            Combined forecast + insights
        """
        # Step 1: Generate Prophet forecast
        forecast = await self.forecasting_service.generate_forecast(
            forecast_type=forecast_type,
            horizon_days=horizon_days
        )

        # Step 2: Get additional data from database
        raw_data = self._get_raw_data(forecast_type)

        # Step 3: Prepare context for GenAI
        context = {
            'forecast': forecast,
            'raw_data': raw_data,
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'forecast_type': forecast_type
        }

        if additional_context:
            context.update(additional_context)

        # Step 4: Generate GenAI insights
        insights = self.insight_generator.generate(
            prompt_name=prompt_name,
            context=context
        )

        # Step 5: Combine
        return {
            'forecast': forecast,
            'insights': insights['insight'],
            'metadata': {
                'forecast_metadata': forecast.get('metadata', {}),
                'insight_metadata': insights['metadata'],
                'analyzed_at': datetime.utcnow().isoformat()
            }
        }

    def _get_raw_data(self, forecast_type: str) -> Dict[str, Any]:
        """
        Fetch relevant raw data based on forecast type.

        Args:
            forecast_type: Type of forecast

        Returns:
            Relevant raw data from database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = {}

        try:
            # Common data
            # Get recent transcripts count
            cursor.execute("""
                SELECT COUNT(*),
                       MIN(timestamp),
                       MAX(timestamp)
                FROM transcripts
            """)
            result = cursor.fetchone()
            data['transcript_count'] = result[0]
            data['data_start'] = result[1]
            data['data_end'] = result[2]

            # Forecast-specific data
            if 'churn' in forecast_type:
                # High churn risk borrowers
                cursor.execute("""
                    SELECT COUNT(*), AVG(churn_risk)
                    FROM analysis
                    WHERE churn_risk > 0.7
                """)
                result = cursor.fetchone()
                data['high_churn_count'] = result[0]
                data['avg_high_churn_risk'] = result[1]

                # Top intents for churn risk
                cursor.execute("""
                    SELECT primary_intent, COUNT(*) as count
                    FROM analysis
                    WHERE churn_risk > 0.5
                    GROUP BY primary_intent
                    ORDER BY count DESC
                    LIMIT 5
                """)
                data['churn_risk_intents'] = [
                    {'intent': row[0], 'count': row[1]}
                    for row in cursor.fetchall()
                ]

            elif 'sentiment' in forecast_type:
                # Sentiment distribution
                cursor.execute("""
                    SELECT borrower_sentiment, COUNT(*) as count
                    FROM analysis
                    GROUP BY borrower_sentiment
                """)
                data['sentiment_distribution'] = dict(cursor.fetchall())

            elif 'advisor' in forecast_type or 'empathy' in forecast_type or 'compliance' in forecast_type:
                # Advisor performance stats
                cursor.execute("""
                    SELECT
                        COUNT(DISTINCT t.advisor_id) as advisor_count,
                        AVG(a.empathy_score) as avg_empathy,
                        AVG(a.compliance_adherence) as avg_compliance
                    FROM transcripts t
                    JOIN analysis a ON t.id = a.transcript_id
                    WHERE t.advisor_id IS NOT NULL
                """)
                result = cursor.fetchone()
                data['advisor_count'] = result[0]
                data['avg_empathy'] = result[1]
                data['avg_compliance'] = result[2]

                # Advisors needing coaching
                cursor.execute("""
                    SELECT
                        t.advisor_id,
                        AVG(a.empathy_score) as avg_empathy,
                        AVG(a.compliance_adherence) as avg_compliance,
                        COUNT(*) as call_count
                    FROM transcripts t
                    JOIN analysis a ON t.id = a.transcript_id
                    WHERE t.advisor_id IS NOT NULL
                    GROUP BY t.advisor_id
                    HAVING avg_empathy < 7.0 OR avg_compliance < 0.8
                    ORDER BY avg_compliance ASC
                    LIMIT 10
                """)
                data['coaching_needed'] = [
                    {
                        'advisor_id': row[0],
                        'empathy': row[1],
                        'compliance': row[2],
                        'calls': row[3]
                    }
                    for row in cursor.fetchall()
                ]

            elif 'delinquency' in forecast_type:
                # Delinquency risk stats
                cursor.execute("""
                    SELECT
                        COUNT(*) as high_risk_count,
                        AVG(delinquency_risk) as avg_risk
                    FROM analysis
                    WHERE delinquency_risk > 0.7
                """)
                result = cursor.fetchone()
                data['high_delinquency_count'] = result[0]
                data['avg_delinquency_risk'] = result[1]

            # Always include recent intents
            cursor.execute("""
                SELECT primary_intent, COUNT(*) as count
                FROM analysis
                GROUP BY primary_intent
                ORDER BY count DESC
                LIMIT 10
            """)
            data['top_intents'] = [
                {'intent': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]

        finally:
            conn.close()

        return data

    async def generate_executive_briefing(
        self,
        forecast_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive executive briefing.

        Combines multiple forecasts + raw data into executive summary.

        Args:
            forecast_types: List of forecasts to include (defaults to key metrics)

        Returns:
            Executive briefing with recommendations
        """
        if not forecast_types:
            forecast_types = [
                'call_volume_daily',
                'churn_risk',
                'delinquency_risk'
            ]

        # Generate all forecasts
        forecasts = {}
        for ft in forecast_types:
            try:
                forecast = await self.forecasting_service.generate_forecast(
                    forecast_type=ft,
                    use_cache=True
                )
                forecasts[ft] = forecast
            except Exception as e:
                # Log but continue
                print(f"Warning: Could not generate {ft} forecast: {e}")

        # Get supplementary data
        raw_data = self._get_executive_data()

        # Prepare context
        context = {
            'forecasts': forecasts,
            'data': raw_data,
            'date': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }

        # Generate briefing
        briefing = self.insight_generator.generate(
            prompt_name='executive_briefing',
            context=context
        )

        return briefing

    def _get_executive_data(self) -> Dict[str, Any]:
        """
        Get data for executive briefing.

        Returns:
            Key metrics and highlights
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = {}

        try:
            # Portfolio overview
            cursor.execute("""
                SELECT
                    COUNT(DISTINCT customer_id) as unique_customers,
                    COUNT(*) as total_calls
                FROM transcripts
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            result = cursor.fetchone()
            data['customers_last_30d'] = result[0]
            data['calls_last_30d'] = result[1]

            # Risk summary
            cursor.execute("""
                SELECT
                    AVG(delinquency_risk) as avg_delinq,
                    AVG(churn_risk) as avg_churn,
                    AVG(complaint_risk) as avg_complaint
                FROM analysis
                WHERE created_at >= datetime('now', '-7 days')
            """)
            result = cursor.fetchone()
            data['avg_delinquency_risk'] = result[0]
            data['avg_churn_risk'] = result[1]
            data['avg_complaint_risk'] = result[2]

            # High priority items
            cursor.execute("""
                SELECT COUNT(*)
                FROM analysis
                WHERE escalation_needed = 1
                AND created_at >= datetime('now', '-7 days')
            """)
            data['escalations_last_7d'] = cursor.fetchone()[0]

            # Workflow status
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM workflows
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY status
            """)
            data['workflow_status'] = dict(cursor.fetchall())

        finally:
            conn.close()

        return data

    async def analyze_churn_risk(self) -> Dict[str, Any]:
        """
        Detailed churn risk analysis.

        Returns:
            Churn prediction + retention strategies
        """
        return await self.analyze_with_forecast(
            forecast_type='churn_risk',
            prompt_name='churn_analysis'
        )

    async def analyze_operations(self) -> Dict[str, Any]:
        """
        Operations intelligence (SLA, queue, advisors).

        Returns:
            Operational insights and recommendations
        """
        # Get call volume forecast
        call_volume = await self.forecasting_service.generate_forecast(
            forecast_type='call_volume_hourly',
            horizon_days=1  # Next 24 hours
        )

        # Get advisor performance data
        raw_data = self._get_raw_data('advisor_empathy')

        context = {
            'call_volume_forecast': call_volume,
            'advisor_data': raw_data,
            'timestamp': datetime.utcnow().isoformat()
        }

        insights = self.insight_generator.generate(
            prompt_name='operations_alerts',
            context=context
        )

        return {
            'call_volume_forecast': call_volume,
            'operational_insights': insights['insight'],
            'metadata': insights['metadata']
        }
