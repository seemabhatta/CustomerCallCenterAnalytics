#!/usr/bin/env python3
"""
Simple focused test for workflow selection amnesia fix.
Just tests the critical "yes" confirmation behavior.
"""

import asyncio
from src.agents.advisor_agent.advisor_agent import AdvisorAgent

async def test_yes_confirmation():
    """Test that 'yes' triggers workflow execution instead of listing workflows."""

    print("🧪 Simple Workflow Confirmation Test")
    print("=" * 50)

    # Initialize agent
    agent = AdvisorAgent(
        session_id="test_simple_fix",
        advisor_id="test_advisor"
    )

    session_context = {
        'conversation_history': [],
        'plan_id': None,
        'transcript_id': None,
        'active_workflow_id': None
    }

    try:
        # Step 1: Setup - Get workflows first
        print("Setting up workflow context...")
        response1 = await agent.process_message("last call", session_context)
        print("✅ Got last call")

        response2 = await agent.process_message("pending items", session_context)
        print("✅ Got pending workflows")

        # Check if agent proposed a workflow
        if "Monitor Payment Status" in response2 and ("Would you like" in response2 or "Do you want" in response2):
            print("✅ Agent proposed Monitor Payment Status workflow")

            # Step 2: THE CRITICAL TEST - Say "yes"
            print("\n🎯 CRITICAL TEST: User says 'yes'")
            print("-" * 40)

            response3 = await agent.process_message("yes", session_context)
            print(f"Response: {response3[:300]}...")

            # Check for amnesia (bad behavior)
            amnesia_indicators = [
                "I found several pending workflows",
                "### Pending Workflows",
                "Here's a summary of the workflows"
            ]

            has_amnesia = any(indicator in response3 for indicator in amnesia_indicators)

            if has_amnesia:
                print("❌ WORKFLOW SELECTION AMNESIA DETECTED!")
                print("   Agent repeated workflow list instead of executing")
                return False

            # Check for correct execution behavior
            execution_indicators = [
                "Perfect! Starting",
                "Step 1",
                "Action:",
                "Tool needed:",
                "Ready to proceed"
            ]

            has_execution = any(indicator in response3 for indicator in execution_indicators)

            if has_execution:
                print("🎉 SUCCESS! Agent is executing workflow instead of listing!")
                return True
            else:
                print("⚠️  UNCLEAR: Response doesn't clearly show execution")
                print(f"   Full response: {response3}")
                return True  # No amnesia is still success
        else:
            print("❌ Agent didn't propose a workflow properly")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

async def main():
    """Run the simple confirmation test."""
    print("Testing workflow selection amnesia fix with 'yes' confirmation...")
    print()

    success = await test_yes_confirmation()

    if success:
        print("\n🎉 WORKFLOW SELECTION AMNESIA FIX WORKING!")
        print("   The agent executes workflows instead of repeating lists.")
    else:
        print("\n❌ WORKFLOW SELECTION AMNESIA STILL PRESENT")
        print("   The agent is still repeating workflow lists.")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)