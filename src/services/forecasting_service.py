"""Forecasting Service - API layer for Prophet forecasting.

Provides business logic layer for time-series forecasting.
Follows NO FALLBACK principle - fails fast on errors.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..analytics.forecasting.forecast_types import ForecastGenerator, get_forecast_type_info, list_all_forecast_types
from ..analytics.forecasting.data_aggregator import DataAggregator
from ..storage.forecast_store import ForecastStore


logger = logging.getLogger(__name__)


class ForecastingServiceError(Exception):
    """Exception raised for forecasting service errors."""
    pass


class ForecastingService:
    """Service layer for time-series forecasting using Prophet."""

    def __init__(self, db_path: str = "data/call_center.db"):
        """Initialize forecasting service.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.forecast_generator = ForecastGenerator(db_path)
        self.forecast_store = ForecastStore(db_path)
        self.data_aggregator = DataAggregator(db_path)

    async def generate_forecast(self, forecast_type: str, horizon_days: Optional[int] = None,
                               start_date: Optional[str] = None, end_date: Optional[str] = None,
                               use_cache: bool = True, ttl_hours: int = 24) -> Dict[str, Any]:
        """Generate or retrieve forecast.

        Args:
            forecast_type: Type of forecast to generate
            horizon_days: Forecast horizon in days
            start_date: Training data start date
            end_date: Training data end date
            use_cache: Whether to use cached forecasts
            ttl_hours: Cache TTL in hours

        Returns:
            Forecast results

        Raises:
            ForecastingServiceError: If forecast generation fails
        """
        try:
            # Check if cached forecast exists
            if use_cache:
                cached = self.forecast_store.get_latest_by_type(forecast_type)
                if cached:
                    logger.info(f"Using cached forecast for {forecast_type}")
                    return {
                        'forecast_id': cached['id'],
                        'forecast_type': forecast_type,
                        'cached': True,
                        'generated_at': cached['generated_at'],
                        'expires_at': cached['expires_at'],
                        **cached['forecast_data']
                    }

            # Check data readiness
            readiness = self.forecast_generator.check_data_readiness(forecast_type)
            if not readiness['ready']:
                raise ForecastingServiceError(
                    f"Insufficient data for {forecast_type}. {readiness['recommendation']}"
                )

            # Generate new forecast
            logger.info(f"Generating new forecast for {forecast_type}")
            forecast_result = self.forecast_generator.generate(
                forecast_type=forecast_type,
                horizon_days=horizon_days,
                start_date=start_date,
                end_date=end_date
            )

            # Store forecast
            metadata = forecast_result.get('metadata', {})
            forecast_id = self.forecast_store.store(
                forecast_type=forecast_type,
                forecast_data=forecast_result,
                horizon_days=horizon_days or metadata.get('default_horizon_days', 7),
                data_start=metadata.get('training_start', ''),
                data_end=metadata.get('training_end', ''),
                prediction_start=forecast_result['summary']['prediction_start'],
                prediction_end=forecast_result['summary']['prediction_end'],
                data_points=metadata.get('data_points_used', 0),
                model_params=metadata.get('prophet_config'),
                ttl_hours=ttl_hours
            )

            return {
                'forecast_id': forecast_id,
                'forecast_type': forecast_type,
                'cached': False,
                'generated_at': datetime.now().isoformat(),
                **forecast_result
            }

        except ValueError as e:
            raise ForecastingServiceError(f"Invalid forecast parameters: {str(e)}")
        except Exception as e:
            raise ForecastingServiceError(f"Forecast generation failed: {str(e)}")

    async def get_forecast_by_id(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        """Get forecast by ID.

        Args:
            forecast_id: Forecast ID

        Returns:
            Forecast data or None if not found

        Raises:
            ForecastingServiceError: If retrieval fails
        """
        try:
            forecast = self.forecast_store.get_by_id(forecast_id)
            if not forecast:
                return None

            return {
                'forecast_id': forecast['id'],
                'forecast_type': forecast['forecast_type'],
                'generated_at': forecast['generated_at'],
                'expires_at': forecast['expires_at'],
                **forecast['forecast_data']
            }

        except Exception as e:
            raise ForecastingServiceError(f"Forecast retrieval failed: {str(e)}")

    async def get_available_forecast_types(self) -> List[Dict[str, Any]]:
        """Get list of available forecast types.

        Returns:
            List of forecast type metadata

        Raises:
            ForecastingServiceError: If retrieval fails
        """
        try:
            return self.forecast_generator.get_available_types()

        except Exception as e:
            raise ForecastingServiceError(f"Failed to get forecast types: {str(e)}")

    async def check_data_readiness(self, forecast_type: Optional[str] = None) -> Dict[str, Any]:
        """Check data readiness for forecasting.

        Args:
            forecast_type: Specific forecast type to check, or None for all

        Returns:
            Data readiness status

        Raises:
            ForecastingServiceError: If check fails
        """
        try:
            if forecast_type:
                # Check specific type
                return self.forecast_generator.check_data_readiness(forecast_type)
            else:
                # Check all types
                all_types = list_all_forecast_types()
                readiness_by_type = {}

                for ft in all_types:
                    readiness = self.forecast_generator.check_data_readiness(ft)
                    readiness_by_type[ft] = readiness

                # Overall summary
                ready_count = sum(1 for r in readiness_by_type.values() if r['ready'])

                return {
                    'total_types': len(all_types),
                    'ready_types': ready_count,
                    'not_ready_types': len(all_types) - ready_count,
                    'by_type': readiness_by_type,
                    'overall_status': 'ready' if ready_count > 0 else 'not_ready'
                }

        except Exception as e:
            raise ForecastingServiceError(f"Data readiness check failed: {str(e)}")

    async def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data for forecasting.

        Returns:
            Data summary

        Raises:
            ForecastingServiceError: If summary generation fails
        """
        try:
            return self.data_aggregator.get_data_summary()

        except Exception as e:
            raise ForecastingServiceError(f"Data summary failed: {str(e)}")

    async def get_forecast_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored forecasts.

        Returns:
            Forecast statistics

        Raises:
            ForecastingServiceError: If statistics retrieval fails
        """
        try:
            return self.forecast_store.get_statistics()

        except Exception as e:
            raise ForecastingServiceError(f"Statistics retrieval failed: {str(e)}")

    async def delete_forecast(self, forecast_id: str) -> bool:
        """Delete a forecast.

        Args:
            forecast_id: Forecast ID to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ForecastingServiceError: If deletion fails
        """
        try:
            return self.forecast_store.delete(forecast_id)

        except Exception as e:
            raise ForecastingServiceError(f"Forecast deletion failed: {str(e)}")

    async def cleanup_expired_forecasts(self) -> int:
        """Clean up expired forecasts.

        Returns:
            Number of forecasts deleted

        Raises:
            ForecastingServiceError: If cleanup fails
        """
        try:
            return self.forecast_store.cleanup_expired()

        except Exception as e:
            raise ForecastingServiceError(f"Forecast cleanup failed: {str(e)}")

    async def get_forecast_type_info(self, forecast_type: str) -> Dict[str, Any]:
        """Get detailed information about a forecast type.

        Args:
            forecast_type: Forecast type name

        Returns:
            Forecast type information

        Raises:
            ForecastingServiceError: If forecast type is invalid
        """
        try:
            return get_forecast_type_info(forecast_type)

        except ValueError as e:
            raise ForecastingServiceError(str(e))
        except Exception as e:
            raise ForecastingServiceError(f"Failed to get forecast type info: {str(e)}")

    async def get_all_forecasts_by_type(self, forecast_type: str,
                                       include_expired: bool = False,
                                       limit: int = 10) -> List[Dict[str, Any]]:
        """Get all forecasts of a specific type.

        Args:
            forecast_type: Forecast type
            include_expired: Include expired forecasts
            limit: Maximum results

        Returns:
            List of forecasts

        Raises:
            ForecastingServiceError: If retrieval fails
        """
        try:
            forecasts = self.forecast_store.get_all_by_type(
                forecast_type=forecast_type,
                include_expired=include_expired,
                limit=limit
            )

            return [
                {
                    'forecast_id': f['id'],
                    'forecast_type': f['forecast_type'],
                    'generated_at': f['generated_at'],
                    'expires_at': f['expires_at'],
                    'summary': f['forecast_data'].get('summary', {})
                }
                for f in forecasts
            ]

        except Exception as e:
            raise ForecastingServiceError(f"Forecast retrieval failed: {str(e)}")
