"""Workflow step generation agent for breaking down actions into executable steps."""
import json
from typing import Dict, Any, List
from datetime import datetime
from src.llm.openai_wrapper import OpenAIWrapper
from src.utils.prompt_loader import prompt_loader


class WorkflowStepAgent:
    """Agent for generating detailed execution steps from high-level actions.

    This agent converts strategic actions into tactical, executable steps
    with specific tool mappings for mortgage servicing workflows.
    """

    def __init__(self):
        """Initialize the workflow step agent."""
        self.llm = OpenAIWrapper()
        self.agent_id = "workflow_step_agent"
        self.agent_version = "v1.0"

    async def generate_steps_for_action(self, action_item: Dict[str, Any],
                                       workflow_type: str,
                                       context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed execution steps for an action item using LLM.

        This is the critical transformation layer that converts strategic actions
        into tactical, executable steps with tool mappings.

        Args:
            action_item: The action from the plan to break down
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            context: Full context for step generation

        Returns:
            List of detailed execution steps

        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM step generation failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")

        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")

        # Use external prompt file for step generation
        try:
            full_prompt = prompt_loader.format(
                'agents/workflow_steps.txt',
                workflow_type=workflow_type,
                action=action_item.get('action', ''),
                description=action_item.get('description', ''),
                priority=action_item.get('priority', ''),
                timeline=action_item.get('timeline', ''),
                transcript_id=context.get('transcript_id', 'Unknown'),
                customer_id=context.get('customer_id', 'Unknown'),
                plan_id=context.get('plan_id', 'Unknown')
            )
            print(f"[STEP_GEN] Calling LLM for {workflow_type} step generation")

            response_text = await self.llm.generate_text_async(
                prompt=full_prompt,
                temperature=0.3
            )

            print(f"[STEP_GEN] Got response for {workflow_type}, length: {len(response_text) if response_text else 0}")

            if not response_text or response_text.strip() == "":
                raise ValueError("LLM returned empty response")

            # Strip markdown code blocks if present
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]   # Remove ```
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            cleaned_text = cleaned_text.strip()

            # Parse JSON response
            try:
                response_data = json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                print(f"[STEP_GEN] Invalid JSON response for {workflow_type}: {cleaned_text[:200]}...")
                raise ValueError(f"LLM response is not valid JSON: {str(e)}")

            # Extract steps array
            if isinstance(response_data, dict) and 'steps' in response_data:
                steps = response_data['steps']
            else:
                raise ValueError("LLM response missing 'steps' array")

            if not isinstance(steps, list) or len(steps) == 0:
                raise ValueError("LLM generated invalid or empty steps array")

            # Add agent metadata to each step
            for step in steps:
                if isinstance(step, dict):
                    step['generation_metadata'] = {
                        'agent_id': self.agent_id,
                        'agent_version': self.agent_version,
                        'generated_at': datetime.utcnow().isoformat(),
                        'workflow_type': workflow_type
                    }

            print(f"[STEP_GEN] Successfully parsed {len(steps)} steps for {workflow_type}")
            return steps

        except Exception as e:
            raise Exception(f"Failed to generate steps for {workflow_type} action: {str(e)}")