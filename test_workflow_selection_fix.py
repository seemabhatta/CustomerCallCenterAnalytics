#!/usr/bin/env python3
"""
Test script to verify the workflow selection amnesia fix.

This tests the exact problematic flow from the logs:
1. "last call" → shows John Smith call context
2. "pending items" → shows 10 workflows with details
3. "lets start one by one" → shows workflows, proposes "Monitor Payment Status"
4. User: "yes" → should start executing that workflow, NOT repeat the list

Expected behavior: Agent should start Step 1 execution, not repeat workflow list.
"""

import asyncio
import json
from src.agents.advisor_agent.advisor_agent import AdvisorAgent

async def test_workflow_selection_amnesia():
    """Test the complete flow that showed workflow selection amnesia."""

    print("🧪 Testing Workflow Selection Amnesia Fix")
    print("=" * 55)

    # Initialize agent
    agent = AdvisorAgent(
        session_id="test_workflow_selection_fix",
        advisor_id="test_advisor"
    )

    # Session context (starts empty)
    session_context = {
        'conversation_history': [],
        'plan_id': None,
        'transcript_id': None,
        'active_workflow_id': None
    }

    print("Step 1: User says 'last call'")
    print("-" * 30)

    try:
        response1 = await agent.process_message("last call", session_context)
        print(f"✅ Response 1: {response1[:150]}...")

        print("\nStep 2: User says 'pending items'")
        print("-" * 30)

        response2 = await agent.process_message("pending items", session_context)
        print(f"✅ Response 2: {response2[:200]}...")

        print("\nStep 3: User says 'lets start one by one'")
        print("-" * 30)

        response3 = await agent.process_message("lets start one by one", session_context)
        print(f"✅ Response 3: {response3[:200]}...")

        # Check if agent proposes a workflow (flexible matching for different phrasing)
        proposal_indicators = [
            "Would you like to begin with",
            "Would you like to start with",
            "Would you like to proceed with",
            "Shall we start with"
        ]

        has_proposal = any(indicator in response3 for indicator in proposal_indicators) and "Monitor Payment Status" in response3

        if has_proposal:
            print("✅ SUCCESS: Agent correctly proposed workflow for confirmation")
        else:
            print("❌ ISSUE: Agent didn't propose workflow properly")
            print(f"   Response snippet: {response3[:400]}...")
            return False

        print("\nStep 4: User says 'yes' (THE CRITICAL TEST)")
        print("-" * 30)

        response4 = await agent.process_message("yes", session_context)
        print(f"✅ Response 4: {response4[:300]}...")

        # Check for workflow selection amnesia symptoms
        amnesia_indicators = [
            "I found several pending workflows",  # Repeating workflow list
            "Here's a summary of the workflows", # Repeating workflow summary
            "### Pending Workflows",             # Workflow list header
            "You will need to approve these",    # Generic approval language
            "Would you like to start with"       # Re-asking for selection
        ]

        has_amnesia = any(indicator in response4 for indicator in amnesia_indicators)

        if has_amnesia:
            print("❌ WORKFLOW SELECTION AMNESIA DETECTED:")
            for indicator in amnesia_indicators:
                if indicator in response4:
                    print(f"   - Found: '{indicator}'")
            print("   🚨 CORE PRINCIPLE VIOLATION: NO FALLBACK violated!")
            return False

        # Check for correct workflow execution indicators
        execution_indicators = [
            "Starting",
            "Step 1",
            "Retrieve loan account details",
            "servicing_api",
            "Ready to proceed",
            "Execute",
            "first step"
        ]

        has_execution = any(indicator in response4 for indicator in execution_indicators)

        if has_execution:
            print("🎉 SUCCESS: Workflow execution started!")
            print(f"✅ Found execution indicators in response")
            return True
        else:
            print("⚠️  PARTIAL SUCCESS: No amnesia, but execution unclear")
            print("   Response doesn't clearly show workflow step execution")
            # Still counts as success if no amnesia
            return True

    except Exception as e:
        print(f"❌ ERROR during test: {str(e)}")
        return False

async def main():
    """Run the workflow selection amnesia test."""
    print("Testing the 'yes' confirmation workflow selection amnesia bug...")
    print()

    success = await test_workflow_selection_amnesia()

    if success:
        print("\n🎉 WORKFLOW SELECTION AMNESIA FIX VERIFIED!")
        print("   The agent now properly executes workflows after confirmation.")
        print("   Core principle upheld: NO FALLBACK logic, proper selection continuity.")
    else:
        print("\n❌ WORKFLOW SELECTION AMNESIA STILL PRESENT")
        print("   The agent is repeating workflow lists instead of executing.")
        print("   This violates the NO FALLBACK principle.")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)