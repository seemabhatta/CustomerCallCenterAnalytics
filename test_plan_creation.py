#!/usr/bin/env python3
"""
Minimal test to debug plan creation issue.
"""

import asyncio
import sys
sys.path.append('.')

from src.services.plan_service import PlanService


async def test_plan_creation():
    """Test plan creation to isolate the bug."""
    print("=" * 50)
    print("TESTING PLAN CREATION")
    print("=" * 50)

    try:
        # Initialize plan service
        plan_service = PlanService(api_key="test")

        # Test with known analysis ID
        request_data = {
            "analysis_id": "ANALYSIS_CALL_CA1A2E",
            "store": True
        }

        print(f"Creating plan for analysis: {request_data['analysis_id']}")
        result = await plan_service.create(request_data)

        print("✅ Plan creation successful!")
        print(f"Plan ID: {result.get('plan_id')}")
        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🧪 Testing Plan Creation...\n")
    success = asyncio.run(test_plan_creation())

    if success:
        print("\n✅ TEST PASSED")
    else:
        print("\n❌ TEST FAILED")