#!/usr/bin/env python3
"""
Test the specific "approved" confirmation scenario from the logs.

This reproduces the exact flow:
1. "last call" → get call details
2. "pending items" → show workflow list
3. "lets see the first one" → show detailed workflow steps
4. "approved" → should execute Step 1, NOT repeat workflow list
"""

import asyncio
from src.agents.advisor_agent.advisor_agent import AdvisorAgent

async def test_approved_confirmation():
    """Test the exact scenario that failed in the logs."""

    print("🧪 Testing 'approved' Confirmation Fix")
    print("=" * 50)

    # Initialize agent
    agent = AdvisorAgent(
        session_id="test_approved_confirmation",
        advisor_id="test_advisor"
    )

    session_context = {
        'conversation_history': [],
        'plan_id': None,
        'transcript_id': None,
        'active_workflow_id': None
    }

    try:
        # Step 1: "last call"
        print("Step 1: User says 'last call'")
        print("-" * 30)
        response1 = await agent.process_message("last call", session_context)
        print(f"✅ Got call details")

        # Step 2: "pending items"
        print("\nStep 2: User says 'pending items'")
        print("-" * 30)
        response2 = await agent.process_message("pending items", session_context)
        print(f"✅ Got workflow list")

        # Step 3: "lets see the first one"
        print("\nStep 3: User says 'lets see the first one'")
        print("-" * 30)
        response3 = await agent.process_message("lets see the first one", session_context)
        print(f"✅ Got detailed workflow steps")

        # Check if agent asked for confirmation
        if ("would you like to proceed with" in response3.lower() or
            "please confirm" in response3.lower() or
            "ready to proceed" in response3.lower()):
            print("✅ Agent proposed workflow execution")

            # Step 4: THE CRITICAL TEST - "approved"
            print("\nStep 4: User says 'approved' (THE CRITICAL TEST)")
            print("-" * 50)

            response4 = await agent.process_message("approved", session_context)
            print(f"Response: {response4[:300]}...")

            # Check for workflow selection amnesia
            amnesia_indicators = [
                "I found several pending workflows",
                "### Pending Workflows",
                "Here's a summary of the workflows",
                "all related to the recent call"
            ]

            has_amnesia = any(indicator in response4 for indicator in amnesia_indicators)

            if has_amnesia:
                print("❌ WORKFLOW SELECTION AMNESIA DETECTED!")
                print("   Agent repeated workflow list instead of executing")
                for indicator in amnesia_indicators:
                    if indicator in response4:
                        print(f"   - Found: '{indicator}'")
                return False

            # Check for workflow execution
            execution_indicators = [
                "Perfect! Starting",
                "Step 1",
                "Action:",
                "Tool needed:",
                "Ready to proceed",
                "Retrieve loan account details"
            ]

            has_execution = any(indicator in response4 for indicator in execution_indicators)

            if has_execution:
                print("🎉 SUCCESS! Agent executed workflow instead of repeating list!")
                print("✅ 'approved' confirmation worked correctly")
                return True
            else:
                print("⚠️  UNKNOWN: Response doesn't clearly show execution or amnesia")
                print(f"   Full response: {response4}")
                return False
        else:
            print("❌ Agent didn't ask for confirmation in Step 3")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

async def main():
    """Run the approved confirmation test."""
    print("Testing the exact 'approved' confirmation scenario from logs...")
    print()

    success = await test_approved_confirmation()

    if success:
        print("\n🎉 'APPROVED' CONFIRMATION FIX WORKING!")
        print("   The agent now recognizes 'approved' as confirmation.")
        print("   No more workflow selection amnesia!")
    else:
        print("\n❌ 'APPROVED' CONFIRMATION STILL BROKEN")
        print("   The agent is still repeating workflow lists.")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)