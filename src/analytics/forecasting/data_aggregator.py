"""Data aggregation for Prophet forecasting.

Pulls historical data from SQLite stores and prepares time-series data
in Prophet's required format (ds, y columns).
"""
import sqlite3
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta


class DataAggregator:
    """Aggregates historical data for Prophet time-series forecasting."""

    def __init__(self, db_path: str):
        """Initialize data aggregator.

        Args:
            db_path: Path to SQLite database
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.db_path = db_path

    def get_call_volume_data(self, granularity: str = 'daily',
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> pd.DataFrame:
        """Get call volume time series.

        Args:
            granularity: 'hourly', 'daily', 'weekly'
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with columns 'ds' (datetime) and 'y' (call count)
        """
        conn = sqlite3.connect(self.db_path)

        try:
            # Build query based on granularity
            if granularity == 'hourly':
                query = '''
                    SELECT
                        strftime('%Y-%m-%d %H:00:00', timestamp) as ds,
                        COUNT(*) as y
                    FROM transcripts
                    WHERE 1=1
                '''
            elif granularity == 'daily':
                query = '''
                    SELECT
                        DATE(timestamp) as ds,
                        COUNT(*) as y
                    FROM transcripts
                    WHERE 1=1
                '''
            elif granularity == 'weekly':
                query = '''
                    SELECT
                        DATE(timestamp, 'weekday 0', '-6 days') as ds,
                        COUNT(*) as y
                    FROM transcripts
                    WHERE 1=1
                '''
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            # Add date filters
            params = []
            if start_date:
                query += ' AND DATE(timestamp) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(timestamp) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params if params else None)

            # Convert ds to datetime
            df['ds'] = pd.to_datetime(df['ds'])

            return df

        finally:
            conn.close()

    def get_intent_volume_data(self, intent: str, granularity: str = 'daily',
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> pd.DataFrame:
        """Get volume for specific intent type.

        Args:
            intent: Primary intent to filter
            granularity: 'daily', 'weekly'
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with ds, y columns
        """
        conn = sqlite3.connect(self.db_path)

        try:
            if granularity == 'daily':
                date_expr = 'DATE(created_at)'
            elif granularity == 'weekly':
                date_expr = "DATE(created_at, 'weekday 0', '-6 days')"
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            query = f'''
                SELECT
                    {date_expr} as ds,
                    COUNT(*) as y
                FROM analysis
                WHERE primary_intent LIKE ?
            '''

            params = [f'%{intent}%']

            if start_date:
                query += ' AND DATE(created_at) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(created_at) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params)
            df['ds'] = pd.to_datetime(df['ds'])

            return df

        finally:
            conn.close()

    def get_sentiment_score_data(self, granularity: str = 'daily',
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> pd.DataFrame:
        """Get average sentiment score over time.

        Args:
            granularity: 'daily', 'weekly'
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with ds, y (average sentiment score)
        """
        conn = sqlite3.connect(self.db_path)

        try:
            # Map sentiment to numeric score
            sentiment_map = {
                'Positive': 1.0,
                'Neutral': 0.5,
                'Negative': 0.0,
                'Frustrated': 0.2,
                'Angry': 0.0,
                'Satisfied': 0.9
            }

            if granularity == 'daily':
                date_expr = 'DATE(created_at)'
            elif granularity == 'weekly':
                date_expr = "DATE(created_at, 'weekday 0', '-6 days')"
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            query = f'''
                SELECT
                    {date_expr} as ds,
                    borrower_sentiment,
                    COUNT(*) as count
                FROM analysis
                WHERE borrower_sentiment IS NOT NULL AND borrower_sentiment != ''
            '''

            params = []
            if start_date:
                query += ' AND DATE(created_at) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(created_at) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds, borrower_sentiment ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params if params else None)

            # Calculate weighted average
            df['score'] = df['borrower_sentiment'].map(
                lambda s: sentiment_map.get(s, 0.5)
            )
            df['weighted'] = df['score'] * df['count']

            result = df.groupby('ds').agg({
                'weighted': 'sum',
                'count': 'sum'
            }).reset_index()

            result['y'] = result['weighted'] / result['count']
            result = result[['ds', 'y']]
            result['ds'] = pd.to_datetime(result['ds'])

            return result

        finally:
            conn.close()

    def get_risk_score_data(self, risk_type: str, granularity: str = 'daily',
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """Get average risk score over time.

        Args:
            risk_type: 'delinquency', 'churn', 'complaint'
            granularity: 'daily', 'weekly'
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with ds, y (average risk score)
        """
        conn = sqlite3.connect(self.db_path)

        try:
            risk_column_map = {
                'delinquency': 'delinquency_risk',
                'churn': 'churn_risk',
                'complaint': 'complaint_risk'
            }

            if risk_type not in risk_column_map:
                raise ValueError(f"Invalid risk_type: {risk_type}")

            risk_column = risk_column_map[risk_type]

            if granularity == 'daily':
                date_expr = 'DATE(created_at)'
            elif granularity == 'weekly':
                date_expr = "DATE(created_at, 'weekday 0', '-6 days')"
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            query = f'''
                SELECT
                    {date_expr} as ds,
                    AVG({risk_column}) as y
                FROM analysis
                WHERE {risk_column} IS NOT NULL
            '''

            params = []
            if start_date:
                query += ' AND DATE(created_at) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(created_at) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params if params else None)
            df['ds'] = pd.to_datetime(df['ds'])

            return df

        finally:
            conn.close()

    def get_advisor_performance_data(self, metric: str = 'empathy',
                                    granularity: str = 'daily',
                                    start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> pd.DataFrame:
        """Get average advisor performance metric over time.

        Args:
            metric: 'empathy', 'compliance', 'solution_effectiveness'
            granularity: 'daily', 'weekly'
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with ds, y (average metric score)
        """
        conn = sqlite3.connect(self.db_path)

        try:
            metric_column_map = {
                'empathy': 'empathy_score',
                'compliance': 'compliance_adherence',
                'solution_effectiveness': 'solution_effectiveness'
            }

            if metric not in metric_column_map:
                raise ValueError(f"Invalid metric: {metric}")

            metric_column = metric_column_map[metric]

            if granularity == 'daily':
                date_expr = 'DATE(created_at)'
            elif granularity == 'weekly':
                date_expr = "DATE(created_at, 'weekday 0', '-6 days')"
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            query = f'''
                SELECT
                    {date_expr} as ds,
                    AVG({metric_column}) as y
                FROM analysis
                WHERE {metric_column} IS NOT NULL
            '''

            params = []
            if start_date:
                query += ' AND DATE(created_at) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(created_at) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params if params else None)
            df['ds'] = pd.to_datetime(df['ds'])

            return df

        finally:
            conn.close()

    def get_escalation_rate_data(self, granularity: str = 'daily',
                                 start_date: Optional[str] = None,
                                 end_date: Optional[str] = None) -> pd.DataFrame:
        """Get escalation rate over time.

        Args:
            granularity: 'daily', 'weekly'
            start_date: Start date
            end_date: End date

        Returns:
            DataFrame with ds, y (escalation rate 0-1)
        """
        conn = sqlite3.connect(self.db_path)

        try:
            if granularity == 'daily':
                date_expr = 'DATE(created_at)'
            elif granularity == 'weekly':
                date_expr = "DATE(created_at, 'weekday 0', '-6 days')"
            else:
                raise ValueError(f"Invalid granularity: {granularity}")

            query = f'''
                SELECT
                    {date_expr} as ds,
                    AVG(CASE WHEN escalation_needed = 1 THEN 1.0 ELSE 0.0 END) as y
                FROM analysis
                WHERE 1=1
            '''

            params = []
            if start_date:
                query += ' AND DATE(created_at) >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND DATE(created_at) <= ?'
                params.append(end_date)

            query += ' GROUP BY ds ORDER BY ds'

            df = pd.read_sql_query(query, conn, params=params if params else None)
            df['ds'] = pd.to_datetime(df['ds'])

            return df

        finally:
            conn.close()

    def check_data_sufficiency(self, min_days: int = 14) -> Dict[str, Any]:
        """Check if there's sufficient data for forecasting.

        Args:
            min_days: Minimum days of data required

        Returns:
            Dict with sufficiency status and details
        """
        conn = sqlite3.connect(self.db_path)

        try:
            # Check transcript data
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    MIN(DATE(timestamp)) as earliest,
                    MAX(DATE(timestamp)) as latest,
                    COUNT(*) as total,
                    COUNT(DISTINCT DATE(timestamp)) as days_of_data
                FROM transcripts
            ''')
            row = cursor.fetchone()

            if not row or row[3] is None:
                return {
                    'sufficient': False,
                    'reason': 'No transcript data found',
                    'days_of_data': 0,
                    'min_required': min_days
                }

            days_of_data = row[3]
            total_transcripts = row[2]

            # Check analysis data
            cursor.execute('SELECT COUNT(*) FROM analysis')
            analysis_count = cursor.fetchone()[0]

            sufficient = days_of_data >= min_days and total_transcripts >= 10

            return {
                'sufficient': sufficient,
                'days_of_data': days_of_data,
                'min_required': min_days,
                'total_transcripts': total_transcripts,
                'total_analyses': analysis_count,
                'earliest_date': row[0],
                'latest_date': row[1],
                'recommendation': self._get_recommendation(days_of_data, min_days)
            }

        finally:
            conn.close()

    def _get_recommendation(self, days_of_data: int, min_required: int) -> str:
        """Get recommendation based on data availability."""
        if days_of_data >= min_required:
            return "Sufficient data for forecasting"
        elif days_of_data >= min_required / 2:
            return f"Close to sufficient. Need {min_required - days_of_data} more days"
        else:
            return f"Insufficient data. Need {min_required - days_of_data} more days or use synthetic data for demo"

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data for forecasting.

        Returns:
            Summary statistics
        """
        conn = sqlite3.connect(self.db_path)

        try:
            cursor = conn.cursor()

            # Transcript summary
            cursor.execute('''
                SELECT
                    MIN(DATE(timestamp)) as earliest,
                    MAX(DATE(timestamp)) as latest,
                    COUNT(*) as total,
                    COUNT(DISTINCT DATE(timestamp)) as unique_days
                FROM transcripts
            ''')
            transcript_row = cursor.fetchone()

            # Analysis summary
            cursor.execute('''
                SELECT
                    COUNT(*) as total,
                    COUNT(DISTINCT primary_intent) as unique_intents,
                    AVG(delinquency_risk) as avg_delinquency,
                    AVG(churn_risk) as avg_churn
                FROM analysis
            ''')
            analysis_row = cursor.fetchone()

            # Intent distribution
            cursor.execute('''
                SELECT primary_intent, COUNT(*) as count
                FROM analysis
                WHERE primary_intent != ''
                GROUP BY primary_intent
                ORDER BY count DESC
                LIMIT 10
            ''')
            intent_dist = {row[0]: row[1] for row in cursor.fetchall()}

            return {
                'transcripts': {
                    'total': transcript_row[2] if transcript_row[2] else 0,
                    'earliest_date': transcript_row[0],
                    'latest_date': transcript_row[1],
                    'unique_days': transcript_row[3] if transcript_row[3] else 0
                },
                'analyses': {
                    'total': analysis_row[0] if analysis_row[0] else 0,
                    'unique_intents': analysis_row[1] if analysis_row[1] else 0,
                    'avg_delinquency_risk': round(analysis_row[2], 2) if analysis_row[2] else 0,
                    'avg_churn_risk': round(analysis_row[3], 2) if analysis_row[3] else 0
                },
                'top_intents': intent_dist
            }

        finally:
            conn.close()
