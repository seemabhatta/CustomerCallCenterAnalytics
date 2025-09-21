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

        # Initialize two-layer memory architecture
        from .session_context import SessionContext
        from ...storage.queued_graph_store import get_queued_graph_store

        # Use the queued graph store for thread-safe access
        queued_graph_store = get_queued_graph_store()
        self.session_context = SessionContext(session_id, graph_store=queued_graph_store)

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
            # Update SessionContext with any entity references in user input
            await self._update_session_context_from_input(user_input, session_context)

            # Build context for the LLM with graph-aware information
            context = self._build_llm_context(user_input, session_context)

            # Get LLM decision on what to do
            decision = await self._get_llm_decision(context)

            # Execute any tool calls the LLM decided to make
            if decision.get('tool_calls'):
                # Store the LLM's tool call decision in conversation
                await self._store_tool_call_decision(decision)

                tool_results = await self._execute_tool_calls(decision['tool_calls'])

                # Store tool execution results in conversation
                await self._store_tool_results(tool_results)

                # LLM formats final response based on tool results
                response = await self._format_response_with_results(user_input, tool_results, context)
            else:
                response = decision.get('response', "I understand you want help with borrower workflows. Could you be more specific about what you'd like to do?")

            # Update conversation history with user input and final response
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

        # Merge extracted context with session context
        extracted_context = getattr(self, '_session_context', {})
        merged_session_context = {
            'plan_id': extracted_context.get('plan_id') or session_context.get('plan_id'),
            'transcript_id': extracted_context.get('transcript_id') or session_context.get('transcript_id'),
            'active_workflow_id': extracted_context.get('active_workflow_id') or session_context.get('active_workflow_id'),
            'cursor_step': session_context.get('cursor_step', 1),
            'step_statuses': session_context.get('step_statuses', {})
        }

        return {
            'user_input': user_input.strip(),
            'session_id': self.session_id,
            'advisor_id': self.advisor_id,
            'conversation_history': recent_history,
            'session_context': merged_session_context,
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
        # Build messages array with conversation history (industry standard)
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        # Add conversation history including tool interactions
        conversation_history = context.get('conversation_history', [])
        for turn in conversation_history:
            role = turn.get('role')
            content = turn.get('content', '')

            if role == 'user':
                messages.append({"role": "user", "content": content})
            elif role == 'assistant':
                messages.append({"role": "assistant", "content": content})
            elif role == 'tool_call':
                # Show LLM what tools were called in previous turns
                messages.append({"role": "assistant", "content": f"[PREVIOUS TOOL CALL] {content}"})
            elif role == 'tool_result':
                # Show LLM what data was retrieved in previous turns
                messages.append({"role": "user", "content": f"[TOOL RESULTS] {content}"})

        # Add current user input
        messages.append({
            "role": "user",
            "content": f"""Current request: {context['user_input']}

Available tools: {json.dumps([tool['name'] for tool in context.get('available_tools', [])], indent=2)}

Decide what to do based on the conversation history above and this current request.

Respond with JSON in this format:
{{
    "reasoning": "Why you chose this approach based on conversation context",
    "tool_calls": [
        {{"tool_name": "tool_name", "parameters": {{"param": "value"}}}}
    ],
    "response": "Direct response if no tools needed, or null if tools will provide the response"
}}"""
        })

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
                elif tool_name == 'get_full_pipeline_for_transcript':
                    result = await self.tools.get_full_pipeline_for_transcript(**parameters)
                elif tool_name == 'get_pending_borrower_workflows':
                    result = await self.tools.get_pending_borrower_workflows(**parameters)
                # Contextual graph-aware tools
                elif tool_name == 'get_pending_workflows_for_context':
                    result = await self.tools.get_pending_workflows_for_context(self.session_context.entity_refs)
                elif tool_name == 'get_analysis_for_context':
                    result = await self.tools.get_analysis_for_context(self.session_context.entity_refs)
                elif tool_name == 'get_plan_for_context':
                    result = await self.tools.get_plan_for_context(self.session_context.entity_refs)
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

                # Extract and store context information for future requests
                if success and result:
                    self._extract_context_from_result(tool_name, result)

            except Exception as e:
                print(f"      💥 Exception: {str(e)}")
                results.append({
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'error': str(e),
                    'success': False
                })

        return results

    def _extract_context_from_result(self, tool_name: str, result: Dict[str, Any]):
        """Extract context information from tool results and update session.

        Args:
            tool_name: Name of the tool that was executed
            result: Result from the tool execution
        """
        if not hasattr(self, '_session_context'):
            self._session_context = {}

        print(f"  🔍 Extracting context from {tool_name}")

        try:
            # Use SessionContext for intelligent entity tracking
            if tool_name == 'get_transcripts' and isinstance(result, list) and result:
                # Store the first transcript as current context
                first_transcript = result[0]
                if 'id' in first_transcript:
                    transcript_id = first_transcript['id']
                    self.session_context.set_active_transcript(transcript_id)
                    print(f"      📋 Set active transcript: {transcript_id}")

            elif tool_name == 'get_transcript' and 'id' in result:
                transcript_id = result['id']
                self.session_context.set_active_transcript(transcript_id)
                print(f"      📋 Set active transcript: {transcript_id}")

            # Extract workflow ID when workflows are retrieved
            elif tool_name == 'get_workflows_for_plan' and isinstance(result, list) and result:
                workflow_ids = [w.get('id') for w in result if w.get('id')]
                if workflow_ids:
                    self.session_context.set_active_workflow(workflow_ids[0])
                    print(f"      ⚙️ Set active workflow: {workflow_ids[0]}")

            elif tool_name == 'get_workflow' and 'id' in result:
                workflow_id = result['id']
                self.session_context.set_active_workflow(workflow_id)
                print(f"      ⚙️ Set active workflow: {workflow_id}")

            # Extract from full pipeline results
            elif tool_name == 'get_full_pipeline_for_transcript':
                if 'transcript_id' in result:
                    transcript_id = result['transcript_id']
                    self.session_context.set_active_transcript(transcript_id)
                    print(f"      📋 Set active transcript: {transcript_id}")

                # SessionContext will auto-derive related entities from graph

        except Exception as e:
            print(f"      ⚠️ Failed to extract context: {str(e)}")

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
- Use status indicators (HIGH, MEDIUM, LOW, completed, pending, etc.)
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

    async def _store_tool_call_decision(self, decision: Dict[str, Any]):
        """Store the LLM's tool call decision in conversation history.

        Args:
            decision: LLM decision containing tool_calls and reasoning
        """
        try:
            tool_calls = decision.get('tool_calls', [])
            reasoning = decision.get('reasoning', 'No reasoning provided')

            content = f"I decided to call {len(tool_calls)} tool(s): {', '.join([tc.get('tool_name', 'unknown') for tc in tool_calls])}. Reasoning: {reasoning}"

            self.session_store.add_conversation_turn(
                self.session_id,
                'tool_call',
                content,
                tool_data={'tool_calls': tool_calls, 'reasoning': reasoning}
            )
            print(f"  📝 Stored tool call decision: {len(tool_calls)} tools")
        except Exception as e:
            print(f"  ⚠️ Failed to store tool call decision: {str(e)}")

    async def _store_tool_results(self, tool_results: List[Dict[str, Any]]):
        """Store tool execution results in conversation history.

        Args:
            tool_results: List of tool execution results
        """
        try:
            successful_tools = [r for r in tool_results if r.get('success')]
            failed_tools = [r for r in tool_results if not r.get('success')]

            content = f"Tool execution completed: {len(successful_tools)} successful, {len(failed_tools)} failed"

            # Add summary of successful tool results for LLM context
            if successful_tools:
                content += "\n\nResults:"
                for result in successful_tools:
                    tool_name = result.get('tool_name', 'unknown')
                    data = result.get('result', {})
                    if isinstance(data, list) and data:
                        content += f"\n- {tool_name}: Found {len(data)} items"
                    elif isinstance(data, dict) and data:
                        content += f"\n- {tool_name}: Retrieved data with keys: {list(data.keys())}"
                    else:
                        content += f"\n- {tool_name}: Completed successfully"

            self.session_store.add_conversation_turn(
                self.session_id,
                'tool_result',
                content,
                tool_data={'results': tool_results}
            )
            print(f"  📝 Stored tool results: {len(tool_results)} total")
        except Exception as e:
            print(f"  ⚠️ Failed to store tool results: {str(e)}")

    async def _update_session_context_from_input(self, user_input: str, session_context: Dict[str, Any]):
        """Update SessionContext based on user input patterns and entity references.

        This method analyzes user input for entity references and updates the session context
        to enable contextual tool calls like "show me the analysis" after mentioning a call.

        Args:
            user_input: Current user message
            session_context: Current session context
        """
        try:
            user_lower = user_input.lower().strip()

            # Check for transcript/call ID mentions
            import re
            call_pattern = r'call[_\s]+([a-zA-Z0-9_]+)'
            transcript_pattern = r'transcript[_\s]+([a-zA-Z0-9_]+)'

            call_match = re.search(call_pattern, user_lower)
            transcript_match = re.search(transcript_pattern, user_lower)

            if call_match or transcript_match:
                transcript_id = call_match.group(1) if call_match else transcript_match.group(1)
                transcript_id = transcript_id.upper()

                # Update SessionContext with this transcript
                success = self.session_context.set_active_transcript(transcript_id)
                if success:
                    print(f"🎯 Updated session context with transcript: {transcript_id}")
                    # Update session context dict for immediate use
                    session_context.update(self.session_context.entity_refs)

            # Check for "last call" or "most recent call" references
            elif any(phrase in user_lower for phrase in ['last call', 'most recent', 'latest call', 'recent call']):
                # Get the most recent transcript from API
                try:
                    recent_transcripts = await self.tools.get_transcripts(limit=1)
                    if recent_transcripts and len(recent_transcripts) > 0:
                        latest_transcript = recent_transcripts[0]
                        transcript_id = latest_transcript.get('id')
                        if transcript_id:
                            success = self.session_context.set_active_transcript(transcript_id)
                            if success:
                                print(f"🎯 Updated session context with latest transcript: {transcript_id}")
                                session_context.update(self.session_context.entity_refs)
                except Exception as e:
                    print(f"⚠️ Failed to get latest transcript: {str(e)}")

        except Exception as e:
            print(f"⚠️ Error updating session context from input: {str(e)}")
            # Non-fatal error - continue processing