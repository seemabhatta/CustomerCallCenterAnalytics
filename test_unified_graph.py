#!/usr/bin/env python3
"""
Quick test script to verify unified knowledge graph functionality.
"""
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.infrastructure.graph.unified_graph_manager import get_unified_graph_manager
from src.infrastructure.graph.knowledge_types import Pattern, PredictiveInsight, InsightContent, CustomerContext

async def test_unified_graph():
    """Test the unified graph with sample data."""
    print("🔄 Testing Unified Knowledge Graph...")

    try:
        # Get unified graph manager
        graph = get_unified_graph_manager()
        print("✅ Unified graph manager initialized")

        # Test 1: Create customer
        print("\n📊 Test 1: Creating customer...")
        customer_id = "CUST_TEST_001"
        await graph.create_or_update_customer(
            customer_id=customer_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@email.com",
            risk_score=0.3,
            total_interactions=1
        )
        print(f"✅ Customer created: {customer_id}")

        # Test 2: Create call
        print("\n📞 Test 2: Creating call...")
        call_id = "CALL_TEST_001"
        transcript_id = "TRANS_TEST_001"
        await graph.create_call_node(
            call_id=call_id,
            transcript_id=transcript_id,
            customer_id=customer_id,
            advisor_id="ADV_TEST_001",
            topic="PMI removal inquiry",
            urgency_level="medium",
            sentiment="positive"
        )
        print(f"✅ Call created: {call_id}")

        # Test 3: Create advisor
        print("\n👨‍💼 Test 3: Creating advisor...")
        advisor_id = "ADV_TEST_001"
        await graph.create_or_update_advisor(
            advisor_id=advisor_id,
            name="Jane Smith",
            department="Mortgage Servicing",
            skill_level="senior",
            performance_score=0.85
        )
        print(f"✅ Advisor created: {advisor_id}")

        # Test 4: Create pattern
        print("\n🔍 Test 4: Creating pattern...")
        pattern = Pattern(
            pattern_id="PATTERN_TEST_001",
            pattern_type="customer_behavior",
            title="PMI Removal Request Pattern",
            description="Customers typically request PMI removal when home values increase",
            conditions={"home_value_increase": ">15%", "ltv": "<80%"},
            outcomes={"success_rate": 0.75, "customer_satisfaction": 0.9},
            confidence=0.8,
            occurrences=5,
            success_rate=0.75,
            last_observed=datetime.utcnow(),
            source_pipeline="analysis"
        )
        await graph.store_pattern(pattern)
        print(f"✅ Pattern created: {pattern.pattern_id}")

        # Test 5: Link call to pattern
        print("\n🔗 Test 5: Linking call to pattern...")
        await graph.link_call_to_pattern(call_id, pattern.pattern_id, strength=0.9)
        print(f"✅ Linked call {call_id} to pattern {pattern.pattern_id}")

        # Test 6: Link pattern to advisor
        print("\n🔗 Test 6: Linking pattern to advisor...")
        await graph.link_pattern_to_advisor(
            pattern.pattern_id,
            advisor_id,
            learning_date=datetime.utcnow().isoformat(),
            application_count=1
        )
        print(f"✅ Linked pattern {pattern.pattern_id} to advisor {advisor_id}")

        print("\n🎉 All tests passed! Unified knowledge graph is working correctly.")
        print("\n📊 Summary:")
        print(f"   • Created customer: {customer_id}")
        print(f"   • Created call: {call_id}")
        print(f"   • Created advisor: {advisor_id}")
        print(f"   • Created pattern: {pattern.pattern_id}")
        print(f"   • Established relationships: Customer→Call→Pattern→Advisor")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if 'graph' in locals():
            graph.close()
            print("🔒 Closed database connections")

if __name__ == "__main__":
    success = asyncio.run(test_unified_graph())
    sys.exit(0 if success else 1)