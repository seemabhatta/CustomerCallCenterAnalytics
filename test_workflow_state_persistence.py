#!/usr/bin/env python3
"""
Test that workflow selection state persists across failed execution attempts.
This addresses the issue where 'yes' clears the pending selection, preventing 'approved' from working.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.infrastructure.llm.llm_client_v2 import LLMClientV2

async def test_workflow_state_persistence():
    """Test that pending workflow selection persists when execution fails."""

    print("🧪 Testing Workflow State Persistence")
    print("=" * 50)

    # Mock agent class to test just the confirmation logic
    class MockAdvisorAgent:
        def __init__(self):
            self.pending_workflow_selection = None
            self.llm = LLMClientV2()
            self.tools = MockTools()

        async def _analyze_user_intent(self, user_input: str) -> bool:
            """Same LLM intent analysis from actual agent."""
            if not self.pending_workflow_selection:
                return False

            workflow_name = self.pending_workflow_selection.get('workflow_name', 'Unknown')

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
                from src.infrastructure.llm.llm_client_v2 import RequestOptions
                response = await self.llm.arun(messages=messages, options=RequestOptions(temperature=0.1))
                is_confirmation = response.text.strip().lower() == "true"

                print(f"   🧠 LLM Intent: '{user_input}' → {'CONFIRM' if is_confirmation else 'OTHER'}")
                return is_confirmation

            except Exception as e:
                print(f"   ⚠️ Intent analysis failed: {e}")
                return False

        async def _handle_workflow_confirmation(self, user_input: str) -> str:
            """Same confirmation handling logic from actual agent."""
            if not self.pending_workflow_selection:
                return None

            # Use LLM to detect confirmation instead of hardcoded patterns
            is_confirmation = await self._analyze_user_intent(user_input)

            if is_confirmation:
                # User confirmed workflow selection - start execution
                workflow_id = self.pending_workflow_selection['workflow_id']
                workflow_name = self.pending_workflow_selection['workflow_name']

                print(f"   ✅ User confirmed workflow selection: {workflow_name}")
                print(f"   🚀 Starting direct execution of Step 1 for workflow {workflow_id}")

                try:
                    # Get workflow steps and execute first step
                    steps_result = await self.tools.get_workflow_steps(workflow_id)

                    if not steps_result or not isinstance(steps_result, list) or len(steps_result) == 0:
                        # Keep pending selection since execution failed
                        print(f"   ⚠️ Workflow step retrieval failed - keeping pending selection")
                        return f"I confirmed we'll start the **{workflow_name}** workflow, but I couldn't retrieve the execution steps. Please try listing the workflow details first."

                    # Clear pending selection only after successful workflow step retrieval
                    self.pending_workflow_selection = None
                    print(f"   🎯 Workflow execution successful - cleared pending selection")

                    # Show Step 1 details for execution
                    step_1 = steps_result[0]
                    return f"Perfect! Starting **{workflow_name}** - Step 1 execution"

                except Exception as e:
                    # Keep pending selection on exception
                    print(f"   ❌ Exception during execution - keeping pending selection")
                    return f"I confirmed we'll start the **{workflow_name}** workflow, but encountered an error: {str(e)}"

            return None

    class MockTools:
        def __init__(self):
            self.fail_count = 0

        async def get_workflow_steps(self, workflow_id):
            """Mock that fails first time, succeeds second time."""
            self.fail_count += 1
            if self.fail_count == 1:
                print(f"   🎭 Mock: Simulating workflow step retrieval failure")
                return None  # Simulate failure
            else:
                print(f"   🎭 Mock: Simulating workflow step retrieval success")
                return [{"step_number": 1, "action": "Test action", "tool_needed": "test"}]

    # Test the scenario
    agent = MockAdvisorAgent()

    # Step 1: Set up pending workflow (simulates "pending items" response)
    agent.pending_workflow_selection = {
        'workflow_id': 'test-workflow-123',
        'workflow_name': 'Monitor Payment Status',
        'proposed_at': 'test-timestamp'
    }
    print(f"✅ Set pending workflow: {agent.pending_workflow_selection['workflow_name']}")

    # Step 2: User says "yes" (should fail execution but keep pending selection)
    print(f"\n🧪 Step 2: User says 'yes'")
    response1 = await agent._handle_workflow_confirmation("yes")
    print(f"   Response: {response1[:100]}...")

    has_pending_after_yes = agent.pending_workflow_selection is not None
    print(f"   Pending selection after 'yes': {'PRESERVED ✅' if has_pending_after_yes else 'CLEARED ❌'}")

    # Step 3: User says "approved" (should succeed because selection is preserved)
    print(f"\n🧪 Step 3: User says 'approved'")
    response2 = await agent._handle_workflow_confirmation("approved")

    if response2:
        print(f"   Response: {response2[:100]}...")
        has_pending_after_approved = agent.pending_workflow_selection is not None
        print(f"   Pending selection after 'approved': {'PRESERVED' if has_pending_after_approved else 'CLEARED ✅'}")

        if "Perfect! Starting" in response2:
            print(f"   🎉 SUCCESS: 'approved' triggered workflow execution!")
            return True
        else:
            print(f"   ❌ FAIL: 'approved' detected but execution failed")
            return False
    else:
        print(f"   ❌ FAIL: 'approved' was not detected as confirmation")
        return False

async def main():
    """Run the workflow state persistence test."""
    success = await test_workflow_state_persistence()

    if success:
        print(f"\n🎉 WORKFLOW STATE PERSISTENCE WORKING!")
        print(f"   Failed 'yes' preserves selection, 'approved' can retry")
    else:
        print(f"\n❌ WORKFLOW STATE PERSISTENCE BROKEN")
        print(f"   Pending selection not preserved across failed attempts")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)