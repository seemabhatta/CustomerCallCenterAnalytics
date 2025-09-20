#!/usr/bin/env python3
"""
Quick test to verify actor confusion and goal fixes.
"""

import asyncio
import sys
sys.path.append('.')

from src.agents.advisor_agent.advisor_agent import AdvisorAgent


async def test_actor_fixes():
    """Test that agent properly distinguishes between advisor and customer."""
    print("=" * 80)
    print("TESTING ACTOR CONFUSION AND GOAL FRAMEWORK FIXES")
    print("=" * 80)

    session_id = "TEST-ACTOR-001"
    advisor_id = "ADV001"

    try:
        agent = AdvisorAgent(session_id=session_id, advisor_id=advisor_id)
        session_context = {
            'conversation_history': [],
            'transcript_id': 'CALL_759BAD5F'  # Known call
        }

        # Test 1: Check if agent addresses advisor correctly
        print("\n" + "=" * 40)
        print("TEST 1: Actor Identification")
        print("=" * 40)
        print("User (Advisor): hi")

        response = await agent.process_message("hi", session_context)
        print(f"\nAgent Response:\n{response}")

        # Check for correct language patterns
        print("\n" + "=" * 40)
        print("ANALYSIS")
        print("=" * 40)

        good_patterns = [
            "the customer",
            "customer's",
            "John Smith",
            "Mark Thompson",
            "I can help you"
        ]

        bad_patterns = [
            "your mortgage",
            "your payment",
            "you called about",
            "your recent calls"
        ]

        has_good = any(pattern.lower() in response.lower() for pattern in good_patterns)
        has_bad = any(pattern.lower() in response.lower() for pattern in bad_patterns)

        if has_good and not has_bad:
            print("✅ SUCCESS: Agent properly distinguishes advisor from customer")
            print("✅ Uses correct pronouns and references")
        elif has_bad:
            print("❌ FAILURE: Agent still confusing advisor with customer")
            print(f"   Found problematic patterns: {[p for p in bad_patterns if p.lower() in response.lower()]}")
        else:
            print("⚠️  UNCERTAIN: Response doesn't clearly show actor awareness")

        # Test goal-oriented behavior
        print("\n" + "=" * 40)
        print("TEST 2: Goal-Oriented Behavior")
        print("=" * 40)

        goal_indicators = [
            "resolve",
            "complete",
            "help",
            "workflow",
            "next steps"
        ]

        has_goals = any(indicator.lower() in response.lower() for indicator in goal_indicators)

        if has_goals:
            print("✅ SUCCESS: Agent shows goal-oriented language")
        else:
            print("⚠️  UNCERTAIN: Limited goal-oriented language detected")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("\n🚀 Starting Actor & Goal Fixes Test...\n")
    success = asyncio.run(test_actor_fixes())

    print("\n" + "=" * 80)
    if success:
        print("✅ TEST COMPLETED")
    else:
        print("❌ TEST FAILED")
    print("=" * 80)