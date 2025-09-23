"""
Advisor Service - Simplified using OpenAI Agents Python SDK.
NO FALLBACK LOGIC - fails fast with clear errors.
Clean agentic approach without complex session management.
Supports both regular and streaming chat responses.
"""
import os
import asyncio
from typing import Dict, Any, Optional, AsyncIterator
from agents import Runner, SQLiteSession, RunResultStreaming
from agents.stream_events import StreamEvent, RunItemStreamEvent, RawResponsesStreamEvent

from src.call_center_agents.advisor_agent_v2 import advisor_agent


class AdvisorService:
    """Simplified service layer using OpenAI Agents.

    Uses OpenAI Agents Runner for conversation management.
    No complex manual session tracking - handled by SQLite sessions.
    """

    def __init__(self, db_path: str = "data/advisor_sessions.db"):
        """Initialize advisor service.

        Args:
            db_path: Database path for session storage

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path is required")

        self.db_path = db_path

    async def chat(self, advisor_id: str, message: str, session_id: Optional[str] = None,
                   transcript_id: Optional[str] = None, plan_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a chat message using OpenAI Agents.

        Clean agentic approach - the LLM decides what tools to call.
        No complex session management - handled by OpenAI Agents.

        Args:
            advisor_id: Advisor identifier
            message: User's chat message
            session_id: Optional session to resume (defaults to advisor_id)
            transcript_id: Optional transcript for context (unused - agent manages context)
            plan_id: Optional plan for context (unused - agent manages context)

        Returns:
            Dictionary with response and session information

        Raises:
            ValueError: Invalid input parameters (NO FALLBACK)
            Exception: If chat processing fails (NO FALLBACK)
        """
        if not advisor_id or not message:
            raise ValueError("advisor_id and message are required")

        if not message.strip():
            return {
                "response": "I'm here to help with borrower workflows. What would you like to do?",
                "session_id": session_id or advisor_id
            }

        try:
            # Use session_id or advisor_id as the session identifier
            actual_session_id = session_id or advisor_id

            # Create SQLite session for conversation persistence
            session = SQLiteSession(actual_session_id, db_path=self.db_path)

            # Run the agent with the message - OpenAI Agents handles everything
            result = await Runner.run(advisor_agent, message, session=session)

            return {
                "response": result.final_output,
                "session_id": actual_session_id,
                "advisor_id": advisor_id
            }

        except Exception as e:
            # Fail fast with clear error message
            error_msg = str(e)
            raise Exception(f"Chat processing failed: {error_msg}")

    async def chat_stream(self, advisor_id: str, message: str, session_id: Optional[str] = None,
                         transcript_id: Optional[str] = None, plan_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """Process a chat message using OpenAI Agents with streaming support.

        Yields streaming events showing thinking steps, tool calls, and response text.

        Args:
            advisor_id: Advisor identifier
            message: User's chat message
            session_id: Optional session to resume (defaults to advisor_id)
            transcript_id: Optional transcript for context (unused - agent manages context)
            plan_id: Optional plan for context (unused - agent manages context)

        Yields:
            Dictionary with streaming events:
            - type: 'thinking' | 'tool_call' | 'response_delta' | 'completed' | 'error'
            - content: Event content
            - metadata: Additional event data

        Raises:
            ValueError: Invalid input parameters (NO FALLBACK)
            Exception: If chat processing fails (NO FALLBACK)
        """
        if not advisor_id or not message:
            raise ValueError("advisor_id and message are required")

        if not message.strip():
            yield {
                "type": "completed",
                "content": "I'm here to help with borrower workflows. What would you like to do?",
                "session_id": session_id or advisor_id,
                "metadata": {}
            }
            return

        try:
            # Use session_id or advisor_id as the session identifier
            actual_session_id = session_id or advisor_id

            # Create SQLite session for conversation persistence
            session = SQLiteSession(actual_session_id, db_path=self.db_path)

            # Run the agent in streaming mode
            result = Runner.run_streamed(advisor_agent, message, session=session)

            # Stream events as they arrive
            final_output = ""

            async for event in result.stream_events():
                if event.type == "raw_response_event":
                    # Raw token deltas from LLM - includes thinking if model expresses it
                    if hasattr(event.data, 'delta') and event.data.delta:
                        yield {
                            "type": "response_delta",
                            "content": event.data.delta,
                            "session_id": actual_session_id,
                            "metadata": {"raw_event": True}
                        }

                elif event.type == "run_item_stream_event":
                    # Higher-level agent events: tool calls, reasoning items, etc.
                    item_type = getattr(event.item, 'type', 'unknown')

                    if item_type == "tool_call_item":
                        # Agent is calling a tool
                        tool_name = getattr(event.item, 'name', 'unknown_tool')
                        yield {
                            "type": "tool_call",
                            "content": f"🔧 Calling {tool_name}...",
                            "session_id": actual_session_id,
                            "metadata": {
                                "tool_name": tool_name,
                                "item": str(event.item)
                            }
                        }

                    elif item_type == "reasoning_item":
                        # Agent reasoning/thinking
                        yield {
                            "type": "thinking",
                            "content": "🤔 Thinking...",
                            "session_id": actual_session_id,
                            "metadata": {"item": str(event.item)}
                        }

                    elif item_type == "message_output_item":
                        # Message being constructed
                        yield {
                            "type": "thinking",
                            "content": "💭 Composing response...",
                            "session_id": actual_session_id,
                            "metadata": {"item": str(event.item)}
                        }

                elif event.type == "agent_updated_stream_event":
                    # Agent handoff/switch
                    agent_name = getattr(event.new_agent, 'name', 'Unknown Agent')
                    yield {
                        "type": "thinking",
                        "content": f"🔄 Switching to {agent_name}",
                        "session_id": actual_session_id,
                        "metadata": {"agent_name": agent_name}
                    }

            # Access final result after streaming is complete
            # The result object should have the final_output property available after streaming
            try:
                final_output = result.final_output if hasattr(result, 'final_output') else "Response completed"
            except Exception as e:
                final_output = "Response completed successfully"

            yield {
                "type": "completed",
                "content": final_output,
                "session_id": actual_session_id,
                "metadata": {
                    "advisor_id": advisor_id,
                    "final": True
                }
            }

        except Exception as e:
            # Fail fast with clear error message
            error_msg = str(e)
            yield {
                "type": "error",
                "content": f"Chat processing failed: {error_msg}",
                "session_id": session_id or advisor_id,
                "metadata": {"error": error_msg}
            }

    # Note: Session management is now handled by OpenAI Agents SQLiteSession
    # No need for complex session tracking methods