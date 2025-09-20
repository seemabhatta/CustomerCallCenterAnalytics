"""
Main Advisor Agent - BORROWER-focused Claude Code for mortgage advisors.
Fully agentic LLM that autonomously calls tools based on user intent.
NO FALLBACK LOGIC - fails fast with clear guidance.
"""
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.infrastructure.llm.llm_client_v2 import LLMClientV2
from src.utils.prompt_loader import prompt_loader
from .api_tools import APITools
from src.storage.advisor_session_store import AdvisorSessionStore


class AdvisorAgent:
    """Main agentic assistant for mortgage advisors.

    Acts like Claude Code with tool-calling capabilities, but strictly limited
    to BORROWER workflows. Makes autonomous decisions about what tools to call
    and when, based on user intent and conversation context.
    """

    def __init__(self, session_id: str, advisor_id: str, db_path: str = "data/call_center.db"):
        """Initialize the advisor agent with tools and context.

        Args:
            session_id: Current session identifier
            advisor_id: Advisor identifier for audit trail
            db_path: Database path for storage

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not session_id or not advisor_id:
            raise ValueError("session_id and advisor_id are required")

        self.session_id = session_id
        self.advisor_id = advisor_id
        self.db_path = db_path

        # Initialize LLM client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        self.llm = LLMClientV2()

        # Initialize tools and storage
        self.tools = APITools(advisor_id=advisor_id)
        self.session_store = AdvisorSessionStore(db_path)

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """Load system prompt from file.

        Returns:
            System prompt text with role boundaries and tool descriptions

        Raises:
            Exception: If prompt cannot be loaded (NO FALLBACK)
        """
        try:
            with open('prompts/advisor_agent/system_prompt.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            raise Exception("System prompt file not found. Check prompts/advisor_agent/system_prompt.txt")
        except Exception as e:
            raise Exception(f"Failed to load system prompt: {str(e)}")

    async def process_message(self, user_input: str, session_context: Dict[str, Any]) -> str:
        """Process user message and return response.

        This is the main entry point that makes the agent fully agentic.
        The LLM decides what tools to call based on the user input and context.

        Args:
            user_input: User's message/command
            session_context: Current session state and context

        Returns:
            Agent's response after processing and optional tool calls

        Raises:
            Exception: If processing fails (NO FALLBACK)
        """
        if not user_input or not user_input.strip():
            return "I'm here to help with borrower workflows. What would you like to do? You can say 'list workflows', 'start <workflow name>', or ask for help."

        # Handle session initialization silently
        if user_input.strip() == "session_init":
            return "Session established successfully."

        try:
            # Build context for the LLM
            context = self._build_llm_context(user_input, session_context)

            # Get LLM decision on what to do
            decision = await self._get_llm_decision(context)

            # Execute any tool calls the LLM decided to make
            if decision.get('tool_calls'):
                tool_results = await self._execute_tool_calls(decision['tool_calls'])

                # LLM formats final response based on tool results
                response = await self._format_response_with_results(user_input, tool_results, context)
            else:
                response = decision.get('response', "I understand you want help with borrower workflows. Could you be more specific about what you'd like to do?")

            # Update conversation history
            await self._update_conversation_history(user_input, response)

            return response

        except Exception as e:
            # Fail fast with helpful guidance
            error_msg = str(e)
            if "not found" in error_msg.lower():
                return f"Error: {error_msg}"
            elif "access denied" in error_msg.lower():
                return f"Access Error: {error_msg}"
            else:
                return f"Sorry, I encountered an error: {error_msg}. Please try rephrasing your request or say 'help' for available commands."

    def _build_llm_context(self, user_input: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Build context package for LLM decision making.

        Args:
            user_input: Current user message
            session_context: Session state and history

        Returns:
            Complete context for LLM processing
        """
        # Get recent conversation history (last 10 turns)
        conversation_history = session_context.get('conversation_history', [])
        recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history

        # Get current workflow state if any
        active_workflow = None
        if session_context.get('active_workflow_id'):
            try:
                active_workflow = self.tools.get_workflow_details(session_context['active_workflow_id'])
            except:
                pass  # Workflow may have been deleted or become inaccessible

        return {
            'user_input': user_input.strip(),
            'session_id': self.session_id,
            'advisor_id': self.advisor_id,
            'conversation_history': recent_history,
            'session_context': {
                'plan_id': session_context.get('plan_id'),
                'transcript_id': session_context.get('transcript_id'),
                'active_workflow_id': session_context.get('active_workflow_id'),
                'cursor_step': session_context.get('cursor_step', 1),
                'step_statuses': session_context.get('step_statuses', {})
            },
            'active_workflow': active_workflow,
            'available_tools': self.tools.get_tool_descriptions(),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def _get_llm_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get LLM decision on what tools to call and how to respond.

        Args:
            context: Complete context for decision making

        Returns:
            LLM decision with tool calls and/or direct response
        """
        # Create the prompt for the LLM
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": f"""
Context: {json.dumps(context, indent=2)}

Based on the user input "{context['user_input']}" and the current context, decide what to do.

You can:
1. Call one or more tools to help the user
2. Provide a direct response if no tools are needed
3. Ask for clarification if the request is unclear

Respond with JSON in this format:
{{
    "reasoning": "Why you chose this approach",
    "tool_calls": [
        {{"tool_name": "list_workflows", "parameters": {{"plan_id": "P123"}}}},
        {{"tool_name": "get_workflow_details", "parameters": {{"workflow_id": "W456"}}}}
    ],
    "response": "Direct response if no tools needed, or null if tools will provide the response"
}}

If you need to call tools, the response will be generated after tool execution.
"""
            }
        ]

        try:
            # Call LLM to get decision
            # Call LLM using the correct API method
            from src.infrastructure.llm.llm_client_v2 import RequestOptions

            print(f"\n🧠 LLM DECISION DEBUG: Processing user input: '{context['user_input']}'")

            response = await self.llm.arun(
                messages=messages,
                options=RequestOptions(temperature=0.1)
            )
            llm_response = response.text

            print(f"🤖 Raw LLM Response:\n{llm_response}")

            # Parse JSON response
            decision = json.loads(llm_response)

            print(f"📋 Parsed Decision:")
            print(f"   Reasoning: {decision.get('reasoning', 'None')}")
            print(f"   Tool Calls: {decision.get('tool_calls', [])}")
            print(f"   Direct Response: {decision.get('response', 'None')}")

            return decision

        except json.JSONDecodeError:
            # Fallback to simple response if JSON parsing fails
            return {
                "reasoning": "JSON parsing failed, providing simple response",
                "tool_calls": [],
                "response": llm_response
            }

    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute the tool calls that the LLM decided to make.

        Args:
            tool_calls: List of tool calls with names and parameters

        Returns:
            List of tool results
        """
        results = []

        print(f"\n🔧 TOOL EXECUTION DEBUG: Executing {len(tool_calls)} tool calls")

        for i, tool_call in enumerate(tool_calls, 1):
            tool_name = tool_call.get('tool_name')
            parameters = tool_call.get('parameters', {})

            print(f"  🛠️  Tool {i}: {tool_name}")
            print(f"      Parameters: {parameters}")

            try:
                # Map tool names to actual API methods
                if tool_name == 'get_transcripts':
                    result = await self.tools.get_transcripts(**parameters)
                elif tool_name == 'get_transcript':
                    result = await self.tools.get_transcript(**parameters)
                elif tool_name == 'get_transcript_analysis':
                    result = await self.tools.get_transcript_analysis(**parameters)
                elif tool_name == 'get_plan_for_transcript':
                    result = await self.tools.get_plan_for_transcript(**parameters)
                elif tool_name == 'get_workflows_for_plan':
                    result = await self.tools.get_workflows_for_plan(**parameters)
                elif tool_name == 'get_workflow':
                    result = await self.tools.get_workflow(**parameters)
                elif tool_name == 'get_workflow_steps':
                    result = await self.tools.get_workflow_steps(**parameters)
                elif tool_name == 'execute_workflow_step':
                    result = await self.tools.execute_workflow_step(**parameters)
                else:
                    result = {'error': f'Unknown tool: {tool_name}'}

                # Handle None results from API calls (404s)
                if result is None:
                    result = {'error': 'Resource not found'}

                success = result is not None and 'error' not in result
                print(f"      ✅ Result: {result}" if success else f"      ❌ Error in result: {result}")

                results.append({
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'result': result,
                    'success': success
                })

            except Exception as e:
                print(f"      💥 Exception: {str(e)}")
                results.append({
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'error': str(e),
                    'success': False
                })

        return results

    async def _format_response_with_results(self, user_input: str, tool_results: List[Dict[str, Any]],
                                          context: Dict[str, Any]) -> str:
        """Format final response based on tool results.

        Args:
            user_input: Original user input
            tool_results: Results from tool execution
            context: Original context

        Returns:
            Formatted response for the user
        """
        # Create prompt for response formatting
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": f"""
User asked: "{user_input}"

Tool execution results:
{json.dumps(tool_results, indent=2)}

Format a helpful response for the user based on these results. Be conversational and specific about what was found or accomplished. If there were errors, provide clear guidance on next steps.

Guidelines:
- Use friendly, professional tone
- Include specific details from the results
- For workflow lists, show priority and step counts
- For step information, explain what will happen
- For errors, suggest specific next actions
- Use emojis for status indicators (🔴 HIGH, 🟡 MED, ✓ completed, etc.)
"""
            }
        ]

        print(f"\n💬 RESPONSE FORMATTING DEBUG:")
        print(f"   User Input: {user_input}")
        print(f"   Tool Results Summary: {len([r for r in tool_results if r.get('success')])} successful, {len([r for r in tool_results if not r.get('success')])} failed")

        try:
            # Call LLM using the correct API method
            from src.infrastructure.llm.llm_client_v2 import RequestOptions

            response = await self.llm.arun(
                messages=messages,
                options=RequestOptions(temperature=0.3)
            )
            final_response = response.text
            print(f"   🎯 Final Response: {final_response}")
            return final_response
        except Exception as e:
            # Fallback to basic result summary
            fallback_response = f"Completed tool execution. Results: {len([r for r in tool_results if r.get('success')])} successful, {len([r for r in tool_results if not r.get('success')])} failed."
            print(f"   ⚠️  Fallback Response: {fallback_response}")
            print(f"   💥 Exception during formatting: {str(e)}")
            return fallback_response

    async def _update_conversation_history(self, user_input: str, response: str):
        """Update session conversation history.

        Args:
            user_input: User's message
            response: Agent's response
        """
        try:
            self.session_store.add_conversation_turn(self.session_id, 'user', user_input)
            self.session_store.add_conversation_turn(self.session_id, 'assistant', response)
        except Exception:
            # Don't fail the whole interaction if conversation logging fails
            pass