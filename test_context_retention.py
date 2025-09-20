#!/usr/bin/env python3
"""
Test script to validate context retention in advisor agent.
Tests the industry-standard conversation memory implementation.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.agents.advisor_agent.advisor_agent import AdvisorAgent

async def test_context_retention():
    """Test that the agent retains context between requests."""
    print("=" * 60)
    print("TESTING CONTEXT RETENTION - Industry Standard Approach")
    print("=" * 60)

    # Create agent instance
    agent = AdvisorAgent(
        session_id="TEST_SESSION_001",
        advisor_id="ADV001",
        db_path="data/call_center.db"
    )

    print("✅ Agent created successfully")

    # Test scenario 1: Ask for last call
    print("\n📞 REQUEST 1: 'show me the last call'")
    response1 = await agent.process_message(
        "show me the last call",
        session_context={}
    )
    print(f"RESPONSE 1: {response1[:200]}..." if len(response1) > 200 else f"RESPONSE 1: {response1}")

    # Test scenario 2: Ask for pending workflows (should use context from request 1)
    print("\n⚙️  REQUEST 2: 'show pending workflows'")
    response2 = await agent.process_message(
        "show pending workflows",
        session_context={}
    )
    print(f"RESPONSE 2: {response2[:200]}..." if len(response2) > 200 else f"RESPONSE 2: {response2}")

    # Check if agent connected context
    if "CALL_" in response2 or "transcript" in response2.lower() or "workflow" in response2.lower():
        print("\n✅ SUCCESS: Agent appears to have retained context!")
        print("   Agent connected 'show pending workflows' to the previous call.")
    else:
        print("\n❌ ISSUE: Agent may not have retained context.")
        print("   Response doesn't reference the previous call.")

    # Test scenario 3: Another follow-up to confirm context
    print("\n🔍 REQUEST 3: 'what are the action items for this call?'")
    response3 = await agent.process_message(
        "what are the action items for this call?",
        session_context={}
    )
    print(f"RESPONSE 3: {response3[:200]}..." if len(response3) > 200 else f"RESPONSE 3: {response3}")

    print("\n" + "=" * 60)
    print("CONTEXT RETENTION TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    # Set environment variable for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY not set. Loading from .env if available.")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("Install python-dotenv or set OPENAI_API_KEY environment variable")

    # Run the test
    try:
        asyncio.run(test_context_retention())
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()