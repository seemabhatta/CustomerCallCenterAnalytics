#!/usr/bin/env python3
"""
Test script to verify the context-aware workflow step retrieval fix.

This tests the exact flow that was broken:
1. User mentions "last call" (sets transcript context to CALL_85029437)
2. User asks "pending items" (should show workflow steps, not empty)
"""

import asyncio
import sys
from src.agents.advisor_agent.api_tools import APITools

async def test_context_workflow_fix():
    """Test the context-aware workflow retrieval that was reported as broken."""

    print("🧪 Testing Context-Aware Workflow Step Retrieval Fix")
    print("=" * 60)

    # Initialize API tools
    api_tools = APITools("http://localhost:8000", "test_advisor")

    # Simulate session context with transcript from "last call"
    session_context = {
        'transcript_id': 'CALL_85029437',  # John Smith payment issue call
        'session_id': 'test_session'
    }

    print(f"📋 Session Context: {session_context}")
    print()

    try:
        # Test the problematic flow: get pending workflows for context
        print("🔍 Testing get_pending_workflows_for_context...")
        pending_workflows = await api_tools.get_pending_workflows_for_context(session_context)

        if not pending_workflows:
            print("❌ STILL BROKEN: No pending workflows returned")
            return False

        print(f"✅ SUCCESS: Found {len(pending_workflows)} pending workflow(s)")

        # Validate the key workflow is present
        monitor_payment_workflow = None
        for workflow in pending_workflows:
            action_item = workflow.get('workflow_data', {}).get('action_item', '')
            if 'Monitor payment status' in action_item:
                monitor_payment_workflow = workflow
                break

        if not monitor_payment_workflow:
            print("❌ ISSUE: Monitor payment status workflow not found")
            return False

        print("✅ FOUND: Monitor payment status workflow")

        # Validate it has the expected 7 steps
        steps = monitor_payment_workflow.get('workflow_steps', [])
        if len(steps) != 7:
            print(f"❌ ISSUE: Expected 7 steps, got {len(steps)}")
            return False

        print("✅ VERIFIED: 7 workflow steps present")

        # Show the steps
        print("\n📝 Workflow Steps:")
        for i, step in enumerate(steps, 1):
            action = step.get('action', 'Unknown')
            tool = step.get('tool_needed', 'Unknown')
            print(f"   {i}. {action} (tool: {tool})")

        print("\n🎉 SUCCESS: Context-aware workflow retrieval is working!")
        print("   When user says 'last call' then 'pending items',")
        print("   the system will now show these workflow steps.")

        return True

    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

async def main():
    """Run the test."""
    success = await test_context_workflow_fix()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())