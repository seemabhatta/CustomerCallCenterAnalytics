#!/usr/bin/env python3
"""
Simple test for LLM-based intent analysis without database dependencies.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.llm.llm_client_v2 import LLMClientV2, RequestOptions

async def test_llm_intent_analysis():
    """Test LLM intent detection directly."""

    print("🧠 Testing LLM Intent Analysis")
    print("=" * 40)

    # Initialize LLM client
    llm = LLMClientV2()

    test_cases = [
        ("approved", True),
        ("yes", True),
        ("go ahead", True),
        ("do it", True),
        ("no", False),
        ("what does step 1 do?", False),
        ("show me other workflows", False),
        ("maybe later", False)
    ]

    workflow_name = "Monitor Payment Status"

    results = []

    for user_input, expected in test_cases:
        print(f"\n🧪 Testing: '{user_input}' (expected: {'CONFIRM' if expected else 'OTHER'})")

        messages = [
            {
                "role": "system",
                "content": f"""You are analyzing if a user is confirming to proceed with a workflow.

Context: Agent proposed executing the "{workflow_name}" workflow and is awaiting confirmation.

Respond with ONLY "true" or "false":
- true: User is confirming/agreeing to proceed (yes, approved, ok, go ahead, etc.)
- false: User is declining, asking questions, or saying something unrelated"""
            },
            {
                "role": "user",
                "content": f'User said: "{user_input}"'
            }
        ]

        try:
            response = await llm.arun(messages=messages, options=RequestOptions(temperature=0.1))
            is_confirmation = response.text.strip().lower() == "true"

            status = "✅" if (is_confirmation == expected) else "❌"
            print(f"   LLM Response: {response.text.strip()}")
            print(f"   Result: {'CONFIRM' if is_confirmation else 'OTHER'} {status}")

            results.append(is_confirmation == expected)

        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)

    # Summary
    correct = sum(results)
    total = len(results)
    print(f"\n📊 Results: {correct}/{total} correct ({correct/total*100:.1f}%)")

    if correct == total:
        print("🎉 All tests passed! LLM intent analysis working perfectly.")
        return True
    else:
        print("⚠️ Some tests failed. LLM intent analysis needs adjustment.")
        return False

async def main():
    """Run the LLM intent tests."""
    success = await test_llm_intent_analysis()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)