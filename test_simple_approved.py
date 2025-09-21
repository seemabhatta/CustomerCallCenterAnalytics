#!/usr/bin/env python3
"""
Simple test to just check if "approved" confirmation is detected.
This bypasses the complex workflow flow and just tests the core confirmation logic.
"""

import asyncio
from src.agents.advisor_agent.advisor_agent import AdvisorAgent

async def test_simple_approved():
    """Test if the agent can detect 'approved' as a confirmation."""

    print("🧪 Simple 'approved' Detection Test")
    print("=" * 40)

    # Initialize agent
    agent = AdvisorAgent(
        session_id="test_simple_approved",
        advisor_id="test_advisor"
    )

    # Manually set a pending workflow selection to test confirmation
    agent.pending_workflow_selection = {
        'workflow_id': '3e07d465-93ca-41b4-8893-05bd4f93cc2b',
        'workflow_name': 'Monitor Payment Status',
        'proposed_at': __import__('datetime').datetime.utcnow()
    }

    print("✅ Manually set pending workflow selection")
    print(f"   Workflow: {agent.pending_workflow_selection['workflow_name']}")
    print(f"   ID: {agent.pending_workflow_selection['workflow_id']}")

    try:
        # Test the confirmation detection directly
        response = await agent._handle_workflow_confirmation("approved")

        if response:
            print("🎉 SUCCESS! 'approved' was detected as confirmation")
            print(f"Response: {response[:200]}...")

            # Check if pending selection was cleared
            if agent.pending_workflow_selection is None:
                print("✅ Pending selection was cleared after confirmation")
                return True
            else:
                print("⚠️  Pending selection was not cleared")
                return False
        else:
            print("❌ FAILURE! 'approved' was NOT detected as confirmation")
            return False

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

async def main():
    """Run the simple approved test."""
    success = await test_simple_approved()

    if success:
        print("\n🎉 'APPROVED' DETECTION WORKING!")
        print("   The confirmation patterns are fixed.")
    else:
        print("\n❌ 'APPROVED' DETECTION BROKEN")
        print("   The confirmation patterns need more work.")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)