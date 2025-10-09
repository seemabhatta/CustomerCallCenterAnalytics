#!/usr/bin/env python3
"""Quick test of forecasting functionality."""
import sys
import os
sys.path.insert(0, 'src')

from src.analytics.forecasting.data_aggregator import DataAggregator
from src.analytics.forecasting.synthetic_data_generator import generate_synthetic_data
from src.services.forecasting_service import ForecastingService

async def test_forecasting():
    """Test forecasting implementation."""
    print("=" * 60)
    print("FORECASTING IMPLEMENTATION TEST")
    print("=" * 60)

    db_path = "data/call_center.db"

    # 1. Check current data
    print("\n1. Checking current data...")
    aggregator = DataAggregator(db_path)
    data_summary = aggregator.get_data_summary()
    print(f"   Transcripts: {data_summary['transcripts']['total']}")
    print(f"   Days of data: {data_summary['transcripts']['unique_days']}")

    # 2. Check data sufficiency
    print("\n2. Checking data readiness...")
    sufficiency = aggregator.check_data_sufficiency(min_days=14)
    print(f"   Sufficient: {sufficiency['sufficient']}")
    print(f"   Days: {sufficiency['days_of_data']}")
    print(f"   Recommendation: {sufficiency['recommendation']}")

    # 3. Generate synthetic data if needed
    if not sufficiency['sufficient']:
        print("\n3. Generating synthetic data (60 days, 20 calls/day)...")
        result = generate_synthetic_data(db_path, days=60, base_daily_calls=20)
        print(f"   Generated {result['transcripts_generated']} transcripts")
        print(f"   Date range: {result['date_range']}")

        # Re-check sufficiency
        sufficiency = aggregator.check_data_sufficiency(min_days=14)
        print(f"   Now sufficient: {sufficiency['sufficient']}")

    # 4. Test forecasting service
    print("\n4. Testing forecasting service...")
    service = ForecastingService(db_path)

    # Check available types
    types = await service.get_available_forecast_types()
    print(f"   Available forecast types: {len(types)}")
    for ft in types[:3]:  # Show first 3
        print(f"     - {ft['type']}: {ft['description']}")

    # 5. Generate a forecast
    print("\n5. Generating call volume forecast...")
    try:
        forecast = await service.generate_forecast(
            forecast_type='call_volume_daily',
            horizon_days=7,
            use_cache=False
        )
        print(f"   Forecast ID: {forecast['forecast_id']}")
        print(f"   Forecast type: {forecast['forecast_type']}")
        print(f"   Cached: {forecast['cached']}")

        summary = forecast['summary']
        print(f"   Predictions: {summary['total_periods']} days")
        print(f"   Average predicted: {summary['average_predicted']:.2f} calls/day")
        print(f"   Range: {summary['min_predicted']:.2f} - {summary['max_predicted']:.2f}")

        # Show first 3 predictions
        print("\n   First 3 predictions:")
        for pred in forecast['predictions'][:3]:
            print(f"     {pred['date']}: {pred['predicted']:.2f} (±{pred['confidence_interval']:.2f})")

        print("\n✅ Forecasting test completed successfully!")

    except Exception as e:
        print(f"\n❌ Forecast generation failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_forecasting())
