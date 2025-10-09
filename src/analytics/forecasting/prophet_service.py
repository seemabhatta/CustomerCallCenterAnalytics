"""Prophet forecasting service wrapper.

Core forecasting engine using Facebook Prophet for time-series predictions.
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics


logger = logging.getLogger(__name__)


class ProphetService:
    """Wrapper for Facebook Prophet forecasting."""

    def __init__(self, **prophet_kwargs):
        """Initialize Prophet service.

        Args:
            **prophet_kwargs: Additional Prophet model parameters
        """
        self.prophet_kwargs = prophet_kwargs
        self.model = None
        self.forecast_result = None

    def train(self, df: pd.DataFrame, **fit_kwargs) -> 'ProphetService':
        """Train Prophet model on historical data.

        Args:
            df: DataFrame with 'ds' (datetime) and 'y' (value) columns
            **fit_kwargs: Additional fit parameters

        Returns:
            self for method chaining

        Raises:
            ValueError: If data is invalid (NO FALLBACK)
        """
        if df is None or df.empty:
            raise ValueError("Cannot train on empty data")

        if 'ds' not in df.columns or 'y' not in df.columns:
            raise ValueError("DataFrame must have 'ds' and 'y' columns")

        if len(df) < 2:
            raise ValueError("Need at least 2 data points to train")

        try:
            # Initialize Prophet with configured parameters
            self.model = Prophet(**self.prophet_kwargs)

            # Train model
            logger.info(f"Training Prophet model on {len(df)} data points")
            self.model.fit(df, **fit_kwargs)

            return self

        except Exception as e:
            raise Exception(f"Prophet training failed: {str(e)}")

    def predict(self, periods: int, freq: str = 'D') -> pd.DataFrame:
        """Generate forecasts.

        Args:
            periods: Number of periods to forecast
            freq: Frequency ('D'=daily, 'H'=hourly, 'W'=weekly)

        Returns:
            DataFrame with forecast results

        Raises:
            ValueError: If model not trained (NO FALLBACK)
        """
        if self.model is None:
            raise ValueError("Model must be trained before prediction")

        if periods <= 0:
            raise ValueError("periods must be positive")

        try:
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=periods, freq=freq)

            # Generate predictions
            logger.info(f"Generating {periods} period forecast")
            forecast = self.model.predict(future)

            self.forecast_result = forecast

            return forecast

        except Exception as e:
            raise Exception(f"Prophet prediction failed: {str(e)}")

    def get_forecast_summary(self, forecast: pd.DataFrame,
                            periods: int) -> Dict[str, Any]:
        """Extract forecast summary from Prophet results.

        Args:
            forecast: Prophet forecast DataFrame
            periods: Number of future periods

        Returns:
            Forecast summary with predictions and confidence intervals
        """
        if forecast is None or forecast.empty:
            raise ValueError("Forecast is empty")

        try:
            # Get only future predictions (last N periods)
            future_forecast = forecast.tail(periods)

            predictions = []
            for _, row in future_forecast.iterrows():
                predictions.append({
                    'date': row['ds'].isoformat(),
                    'predicted': float(row['yhat']),
                    'lower_bound': float(row['yhat_lower']),
                    'upper_bound': float(row['yhat_upper']),
                    'confidence_interval': float(row['yhat_upper'] - row['yhat_lower'])
                })

            # Calculate summary statistics
            avg_predicted = future_forecast['yhat'].mean()
            min_predicted = future_forecast['yhat'].min()
            max_predicted = future_forecast['yhat'].max()

            return {
                'predictions': predictions,
                'summary': {
                    'average_predicted': float(avg_predicted),
                    'min_predicted': float(min_predicted),
                    'max_predicted': float(max_predicted),
                    'total_periods': periods,
                    'prediction_start': predictions[0]['date'],
                    'prediction_end': predictions[-1]['date']
                },
                'metadata': {
                    'model_type': 'Prophet',
                    'seasonality_mode': self.prophet_kwargs.get('seasonality_mode', 'additive'),
                    'growth': self.prophet_kwargs.get('growth', 'linear')
                }
            }

        except Exception as e:
            raise Exception(f"Failed to extract forecast summary: {str(e)}")

    def cross_validate_model(self, df: pd.DataFrame, initial: str = '30 days',
                            period: str = '7 days', horizon: str = '14 days') -> Dict[str, Any]:
        """Perform cross-validation to assess model accuracy.

        Args:
            df: Historical data DataFrame
            initial: Initial training period
            period: Period between cutoff dates
            horizon: Forecast horizon

        Returns:
            Cross-validation metrics
        """
        if self.model is None:
            raise ValueError("Model must be trained before cross-validation")

        try:
            logger.info("Performing cross-validation...")
            df_cv = cross_validation(self.model, initial=initial, period=period, horizon=horizon)

            # Calculate performance metrics
            df_p = performance_metrics(df_cv)

            return {
                'mae': float(df_p['mae'].mean()),
                'mape': float(df_p['mape'].mean()),
                'rmse': float(df_p['rmse'].mean()),
                'coverage': float(df_p['coverage'].mean()) if 'coverage' in df_p else None,
                'metrics_by_horizon': df_p.to_dict('records')
            }

        except Exception as e:
            logger.warning(f"Cross-validation failed: {str(e)}")
            # Return None instead of failing - cross-validation is optional
            return None

    def get_component_analysis(self) -> Optional[Dict[str, Any]]:
        """Get trend and seasonality components.

        Returns:
            Component analysis or None if not available
        """
        if self.forecast_result is None:
            return None

        try:
            components = {}

            # Extract trend
            if 'trend' in self.forecast_result:
                components['trend'] = {
                    'average': float(self.forecast_result['trend'].mean()),
                    'direction': 'increasing' if self.forecast_result['trend'].iloc[-1] > self.forecast_result['trend'].iloc[0] else 'decreasing'
                }

            # Extract weekly seasonality if available
            if 'weekly' in self.forecast_result:
                components['weekly_seasonality'] = {
                    'peak_day': int(self.forecast_result['weekly'].idxmax() % 7),
                    'low_day': int(self.forecast_result['weekly'].idxmin() % 7)
                }

            # Extract yearly seasonality if available
            if 'yearly' in self.forecast_result:
                components['yearly_seasonality'] = {
                    'amplitude': float(self.forecast_result['yearly'].max() - self.forecast_result['yearly'].min())
                }

            return components if components else None

        except Exception as e:
            logger.warning(f"Component analysis failed: {str(e)}")
            return None

    @staticmethod
    def create_daily_model(**kwargs) -> 'ProphetService':
        """Create Prophet model for daily forecasting.

        Returns:
            ProphetService configured for daily forecasts
        """
        default_params = {
            'daily_seasonality': True,
            'weekly_seasonality': True,
            'yearly_seasonality': False,
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.05
        }
        default_params.update(kwargs)
        return ProphetService(**default_params)

    @staticmethod
    def create_weekly_model(**kwargs) -> 'ProphetService':
        """Create Prophet model for weekly forecasting.

        Returns:
            ProphetService configured for weekly forecasts
        """
        default_params = {
            'daily_seasonality': False,
            'weekly_seasonality': True,
            'yearly_seasonality': True,
            'seasonality_mode': 'multiplicative',
            'changepoint_prior_scale': 0.1
        }
        default_params.update(kwargs)
        return ProphetService(**default_params)

    @staticmethod
    def create_hourly_model(**kwargs) -> 'ProphetService':
        """Create Prophet model for hourly forecasting.

        Returns:
            ProphetService configured for hourly forecasts
        """
        default_params = {
            'daily_seasonality': True,
            'weekly_seasonality': True,
            'yearly_seasonality': False,
            'seasonality_mode': 'additive',
            'changepoint_prior_scale': 0.01
        }
        default_params.update(kwargs)
        return ProphetService(**default_params)


def generate_forecast(df: pd.DataFrame, periods: int, freq: str = 'D',
                     model_type: str = 'daily', **prophet_kwargs) -> Dict[str, Any]:
    """Convenience function to generate forecast in one call.

    Args:
        df: Historical data with 'ds' and 'y' columns
        periods: Number of periods to forecast
        freq: Frequency ('D', 'H', 'W')
        model_type: 'daily', 'weekly', or 'hourly'
        **prophet_kwargs: Additional Prophet parameters

    Returns:
        Forecast summary dictionary
    """
    # Create appropriate model
    if model_type == 'daily':
        service = ProphetService.create_daily_model(**prophet_kwargs)
    elif model_type == 'weekly':
        service = ProphetService.create_weekly_model(**prophet_kwargs)
    elif model_type == 'hourly':
        service = ProphetService.create_hourly_model(**prophet_kwargs)
    else:
        service = ProphetService(**prophet_kwargs)

    # Train and predict
    service.train(df)
    forecast = service.predict(periods, freq)

    # Get summary
    summary = service.get_forecast_summary(forecast, periods)

    # Add components if available
    components = service.get_component_analysis()
    if components:
        summary['components'] = components

    return summary
