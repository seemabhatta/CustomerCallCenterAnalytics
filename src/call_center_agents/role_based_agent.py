"""
Generic Role-Based Agent Factory.
Creates agents with role-specific prompts while maintaining the same tool set.
Follows core principles: agentic, no fallback logic, prompt separation.
"""
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from agents import Agent
from .advisor_agent_v2 import (
    # Import all the tools from advisor_agent_v2
    get_transcripts,
    get_transcript,
    get_transcript_analysis,
    get_plan_for_transcript,
    get_plan,
    get_workflows_for_plan,
    get_workflow,
    get_workflow_steps,
    execute_workflow_step,
    get_full_pipeline_for_transcript,
    get_pending_borrower_workflows
)

# Load environment variables from .env file
load_dotenv()


def load_prompt_from_file(role: str) -> str:
    """Load role-specific prompt from prompts folder.

    Args:
        role: Role identifier (advisor, leadership)

    Returns:
        Prompt text content

    Raises:
        FileNotFoundError: If prompt file doesn't exist
    """
    prompt_file = f"prompts/{role}_agent/system_prompt.txt"

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with open(prompt_file, 'r', encoding='utf-8') as f:
        return f.read().strip()


def create_role_based_agent(role: str) -> Agent:
    """Create an agent with role-specific prompts and shared tools.

    Args:
        role: Role identifier (advisor, leadership)

    Returns:
        Configured Agent instance
    """
    # Load role-specific prompt
    instructions = load_prompt_from_file(role)

    # Agent name mapping
    agent_names = {
        "advisor": "Mortgage Advisor Assistant",
        "leadership": "Leadership Analytics Assistant"
    }

    agent_name = agent_names.get(role, f"{role.title()} Assistant")

    # Create agent with role-specific configuration
    agent = Agent(
        name=agent_name,
        model="gpt-4o-mini",  # Use cheaper model with higher token limits
        instructions=instructions,
        tools=[
            # All agents get the same tool set - the prompt determines behavior
            get_transcripts,
            get_transcript,
            get_transcript_analysis,
            get_plan_for_transcript,
            get_plan,
            get_workflows_for_plan,
            get_workflow,
            get_workflow_steps,
            execute_workflow_step,
            get_full_pipeline_for_transcript,
            get_pending_borrower_workflows
        ]
    )

    return agent


# Create pre-configured agents for common roles
advisor_agent = create_role_based_agent("advisor")
leadership_agent = create_role_based_agent("leadership")