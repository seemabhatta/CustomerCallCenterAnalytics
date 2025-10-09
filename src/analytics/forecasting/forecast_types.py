"""Forecast type definitions.

Defines available forecast types with their data sources, Prophet configs,
and output formats.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import pandas as pd

from .data_aggregator import DataAggregator
from .prophet_service import ProphetService, generate_forecast


@dataclass
class ForecastDefinition:
    """Definition of a forecast type."""
    name: str
    description: str
    granularity: str  # 'hourly', 'daily', 'weekly'
    min_data_days: int
    default_horizon_days: int
    model_type: str  # 'daily', 'weekly', 'hourly'
    prophet_kwargs: Dict[str, Any]


# Define all available forecast types
FORECAST_TYPES = {
    'call_volume_daily': ForecastDefinition(
        name='call_volume_daily',
        description='Daily call volume forecast',
        granularity='daily',
        min_data_days=14,
        default_horizon_days=7,
        model_type='daily',
        prophet_kwargs={
            'daily_seasonality': False,
            'weekly_seasonality': True,
            'yearly_seasonality': False
        }
    ),
    'call_volume_hourly': ForecastDefinition(
        name='call_volume_hourly',
        description='Hourly call volume forecast',
        granularity='hourly',
        min_data_days=7,
        default_horizon_days=3,
        model_type='hourly',
        prophet_kwargs={
            'daily_seasonality': True,
            'weekly_seasonality': True,
            'yearly_seasonality': False
        }
    ),
    'sentiment_trend': ForecastDefinition(
        name='sentiment_trend',
        description='Customer sentiment score trend',
        granularity='daily',
        min_data_days=14,
        default_horizon_days=7,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05
        }
    ),
    'delinquency_risk': ForecastDefinition(
        name='delinquency_risk',
        description='Delinquency risk score forecast',
        granularity='daily',
        min_data_days=30,
        default_horizon_days=14,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.1
        }
    ),
    'churn_risk': ForecastDefinition(
        name='churn_risk',
        description='Customer churn risk forecast',
        granularity='daily',
        min_data_days=30,
        default_horizon_days=14,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.1
        }
    ),
    'escalation_rate': ForecastDefinition(
        name='escalation_rate',
        description='Call escalation rate forecast',
        granularity='daily',
        min_data_days=14,
        default_horizon_days=7,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive'
        }
    ),
    'advisor_empathy': ForecastDefinition(
        name='advisor_empathy',
        description='Advisor empathy score trend',
        granularity='daily',
        min_data_days=21,
        default_horizon_days=7,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05
        }
    ),
    'advisor_compliance': ForecastDefinition(
        name='advisor_compliance',
        description='Advisor compliance adherence forecast',
        granularity='daily',
        min_data_days=21,
        default_horizon_days=7,
        model_type='daily',
        prophet_kwargs={
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05
        }
    )
}


class ForecastGenerator:
    """Generate forecasts based on type definitions."""

    def __init__(self, db_path: str):
        """Initialize forecast generator.

        Args:
            db_path: Path to SQLite database
        """
        self.data_aggregator = DataAggregator(db_path)

    def get_available_types(self) -> List[Dict[str, Any]]:
        """Get list of available forecast types.

        Returns:
            List of forecast type metadata
        """
        return [
            {
                'type': ft.name,
                'description': ft.description,
                'granularity': ft.granularity,
                'min_data_days': ft.min_data_days,
                'default_horizon_days': ft.default_horizon_days
            }
            for ft in FORECAST_TYPES.values()
        ]

    def check_data_readiness(self, forecast_type: str) -> Dict[str, Any]:
        """Check if sufficient data exists for forecast type.

        Args:
            forecast_type: Type of forecast

        Returns:
            Data readiness status

        Raises:
            ValueError: If invalid forecast type
        """
        if forecast_type not in FORECAST_TYPES:
            raise ValueError(f"Invalid forecast type: {forecast_type}")

        definition = FORECAST_TYPES[forecast_type]

        # Check overall data sufficiency
        sufficiency = self.data_aggregator.check_data_sufficiency(
            min_days=definition.min_data_days
        )

        return {
            'forecast_type': forecast_type,
            'ready': sufficiency['sufficient'],
            'days_of_data': sufficiency['days_of_data'],
            'min_required': definition.min_data_days,
            'recommendation': sufficiency['recommendation'],
            'earliest_date': sufficiency.get('earliest_date'),
            'latest_date': sufficiency.get('latest_date')
        }

    def generate(self, forecast_type: str, horizon_days: Optional[int] = None,
                start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Generate forecast of specified type.

        Args:
            forecast_type: Type of forecast to generate
            horizon_days: Forecast horizon (default from definition)
            start_date: Training data start date
            end_date: Training data end date

        Returns:
            Forecast results

        Raises:
            ValueError: If invalid parameters or insufficient data
        """
        if forecast_type not in FORECAST_TYPES:
            raise ValueError(f"Invalid forecast type: {forecast_type}")

        definition = FORECAST_TYPES[forecast_type]

        # Use default horizon if not specified
        if horizon_days is None:
            horizon_days = definition.default_horizon_days

        # Get historical data based on forecast type
        df = self._get_data_for_type(forecast_type, definition, start_date, end_date)

        if df is None or df.empty:
            raise ValueError(f"No data available for {forecast_type}")

        if len(df) < 2:
            raise ValueError(f"Insufficient data points for {forecast_type}. Need at least 2, got {len(df)}")

        # Generate forecast
        freq_map = {'hourly': 'H', 'daily': 'D', 'weekly': 'W'}
        freq = freq_map[definition.granularity]

        forecast_result = generate_forecast(
            df=df,
            periods=horizon_days,
            freq=freq,
            model_type=definition.model_type,
            **definition.prophet_kwargs
        )

        # Add metadata
        forecast_result['metadata'].update({
            'forecast_type': forecast_type,
            'granularity': definition.granularity,
            'data_points_used': len(df),
            'training_start': df['ds'].min().isoformat(),
            'training_end': df['ds'].max().isoformat()
        })

        return forecast_result

    def _get_data_for_type(self, forecast_type: str, definition: ForecastDefinition,
                          start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
        """Get appropriate data for forecast type.

        Args:
            forecast_type: Forecast type
            definition: Forecast definition
            start_date: Start date filter
            end_date: End date filter

        Returns:
            DataFrame with ds, y columns
        """
        if forecast_type == 'call_volume_daily':
            return self.data_aggregator.get_call_volume_data(
                granularity='daily', start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'call_volume_hourly':
            return self.data_aggregator.get_call_volume_data(
                granularity='hourly', start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'sentiment_trend':
            return self.data_aggregator.get_sentiment_score_data(
                granularity=definition.granularity, start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'delinquency_risk':
            return self.data_aggregator.get_risk_score_data(
                risk_type='delinquency', granularity=definition.granularity,
                start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'churn_risk':
            return self.data_aggregator.get_risk_score_data(
                risk_type='churn', granularity=definition.granularity,
                start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'escalation_rate':
            return self.data_aggregator.get_escalation_rate_data(
                granularity=definition.granularity, start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'advisor_empathy':
            return self.data_aggregator.get_advisor_performance_data(
                metric='empathy', granularity=definition.granularity,
                start_date=start_date, end_date=end_date
            )

        elif forecast_type == 'advisor_compliance':
            return self.data_aggregator.get_advisor_performance_data(
                metric='compliance', granularity=definition.granularity,
                start_date=start_date, end_date=end_date
            )

        else:
            raise ValueError(f"No data handler for forecast type: {forecast_type}")


def get_forecast_type_info(forecast_type: str) -> Dict[str, Any]:
    """Get information about a forecast type.

    Args:
        forecast_type: Forecast type name

    Returns:
        Forecast type information

    Raises:
        ValueError: If invalid forecast type
    """
    if forecast_type not in FORECAST_TYPES:
        raise ValueError(f"Invalid forecast type: {forecast_type}")

    definition = FORECAST_TYPES[forecast_type]

    return {
        'type': definition.name,
        'description': definition.description,
        'granularity': definition.granularity,
        'min_data_days': definition.min_data_days,
        'default_horizon_days': definition.default_horizon_days,
        'model_type': definition.model_type,
        'prophet_config': definition.prophet_kwargs
    }


def list_all_forecast_types() -> List[str]:
    """Get list of all available forecast type names.

    Returns:
        List of forecast type names
    """
    return list(FORECAST_TYPES.keys())
