# References

- [OpenAI Build Hours – Agentic Tool Calling](https://github.com/openai/build-hours/tree/main/12-agentic-tool-calling)  
- [n8n – Open Source Workflow Orchestration](https://github.com/n8n-io/n8n)  
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/docs/getting-started/intro)  
- [OpenAI Agents Track](https://developers.openai.com/tracks/building-agents/?utm_source=chatgpt.com)  

- Sample Code - Agent SDK

	from agents import Agent, Runner
	agent = Agent(name="Assistant", instructions="You are a helpful assistant")
	result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
	print(result.final_output)

	# Code within the code,
	# Functions calling themselves,
	# Infinite loop's dance.
	
- Github: https://github.com/openai/openai-agents-python

- Sample Code - Reposponse API

from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    """returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="o3-mini",
    tools=[get_weather],
)


- Handoff - https://openai.github.io/openai-agents-python/handoffs/
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")


triage_agent = Agent(name="Triage agent", handoffs=[billing_agent, handoff(refund_agent)])

- Guadrails 
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent( 
    name="Guardrail check",
    instructions="Check if the user is asking you to do their math homework.",
    output_type=MathHomeworkOutput,
)


@input_guardrail - https://openai.github.io/openai-agents-python/guardrails/
async def math_guardrail( 
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output, 
        tripwire_triggered=result.final_output.is_math_homework,
    )


agent = Agent(  
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[math_guardrail],
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except InputGuardrailTripwireTriggered:
        print("Math homework guardrail tripped")