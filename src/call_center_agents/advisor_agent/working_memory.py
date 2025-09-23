"""
Working Memory - Aggregates all context sources for agentic LLM decision making.

Core Principles:
- NO FILTERING: Pass all available context to LLM
- LET LLM DECIDE: What matters, what to ignore, what patterns to recognize
- RICH CONTEXT: Include everything - conversation history, metadata, entity refs
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from .session_context import SessionContext
from ...storage.advisor_session_store import AdvisorSessionStore


class WorkingMemory:
    """Aggregates all available context for LLM decision making.

    This class implements the "let LLM think" principle by providing
    comprehensive context without any filtering or decision-making logic.
    """

    def __init__(self, session_context: SessionContext, session_store: AdvisorSessionStore,
                 session_id: str, advisor_id: str):
        """Initialize working memory with all context sources.

        Args:
            session_context: Graph-aware entity context
            session_store: Conversation history storage
            session_id: Current session identifier
            advisor_id: Advisor identifier
        """
        self.session_context = session_context
        self.session_store = session_store
        self.session_id = session_id
        self.advisor_id = advisor_id

    def build_complete_context(self, user_input: str, available_tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive context for LLM decision making.

        Args:
            user_input: Current user message
            available_tools: List of available tool descriptions

        Returns:
            Complete context dict with all available information
        """
        # Get conversation history from storage
        conversation_history = self._get_recent_conversation()

        # Get entity context from graph-aware session
        entity_context = self.session_context.get_current_context()

        # Get metadata context from recent tool calls
        metadata_context = self.session_context.get_metadata_context()

        # Get conversation flow summary
        flow_summary = self.session_context.get_conversation_summary()

        # Aggregate everything - LLM decides what matters
        complete_context = {
            # Current request
            'user_input': user_input.strip(),
            'timestamp': datetime.utcnow().isoformat(),

            # Session identifiers
            'session_id': self.session_id,
            'advisor_id': self.advisor_id,

            # Conversation history (structured)
            'conversation_history': conversation_history,
            'conversation_flow_summary': flow_summary,

            # Entity context (graph-aware)
            'entity_context': entity_context,
            'active_entities': self.session_context.entity_refs,

            # Tool call metadata and history
            'metadata_context': metadata_context,
            'recent_completeness_issues': self._identify_completeness_issues(),

            # Available capabilities
            'available_tools': available_tools,
            'tool_descriptions': [tool.get('name', 'unknown') for tool in available_tools],

            # Context enrichment hints (for LLM pattern recognition)
            'context_enrichment': {
                'has_active_transcript': bool(entity_context.get('has_active_transcript')),
                'has_active_workflow': bool(entity_context.get('has_active_workflow')),
                'recent_tool_call_count': len(metadata_context.get('recent_tool_calls', [])),
                'conversation_depth': len(conversation_history),
                'entity_mention_recency': entity_context.get('entity_mention_time')
            }
        }

        return complete_context

    def _get_recent_conversation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history from storage."""
        try:
            session_data = self.session_store.get_session(self.session_id)
            if not session_data:
                return []

            conversation_history = session_data.get('conversation_history', [])
            # Return last N turns
            return conversation_history[-limit:] if len(conversation_history) > limit else conversation_history

        except Exception as e:
            # Non-fatal - return empty history
            print(f"⚠️ Failed to get conversation history: {str(e)}")
            return []

    def _identify_completeness_issues(self) -> List[Dict[str, Any]]:
        """Identify recent tool calls that returned partial results."""
        issues = []
        recent_calls = self.session_context.tool_call_history[-5:]  # Last 5 calls

        for call in recent_calls:
            metadata = call.get('metadata', {})
            if metadata.get('completeness') == 'partial':
                issues.append({
                    'tool_name': call['tool_name'],
                    'requested': metadata.get('requested'),
                    'returned': metadata.get('returned'),
                    'total_available': metadata.get('total_available'),
                    'timestamp': call['timestamp']
                })

        return issues

    def update_tool_call_tracking(self, tool_name: str, parameters: Dict[str, Any],
                                 result: Dict[str, Any]) -> None:
        """Update tool call tracking in session context.

        Args:
            tool_name: Name of the tool that was called
            parameters: Parameters passed to the tool
            result: Result returned by the tool
        """
        # Extract metadata if present in result
        metadata = None
        if isinstance(result, dict) and 'metadata' in result:
            metadata = result['metadata']

        # Track in session context
        self.session_context.track_tool_call(tool_name, parameters, result, metadata)

        # Store in conversation history
        try:
            # Add tool call to conversation history
            self.session_store.add_conversation_turn(
                session_id=self.session_id,
                role='tool_call',
                content=f"Called {tool_name} with {parameters}",
                metadata={'tool_name': tool_name, 'parameters': parameters}
            )

            # Add tool result to conversation history
            result_summary = self.session_context._summarize_result(result)
            self.session_store.add_conversation_turn(
                session_id=self.session_id,
                role='tool_result',
                content=f"Tool result: {result_summary}",
                metadata={'tool_name': tool_name, 'metadata': metadata}
            )

        except Exception as e:
            # Non-fatal - continue without storing
            print(f"⚠️ Failed to store tool call in history: {str(e)}")

    def get_context_summary_for_logging(self) -> Dict[str, Any]:
        """Get a summary of current context for logging/debugging."""
        entity_context = self.session_context.get_current_context()
        metadata_context = self.session_context.get_metadata_context()

        return {
            'session_id': self.session_id,
            'active_transcript': entity_context.get('entity_refs', {}).get('transcript_id'),
            'active_workflow': entity_context.get('entity_refs', {}).get('active_workflow_id'),
            'recent_tool_calls': len(metadata_context.get('recent_tool_calls', [])),
            'completeness_issues': len(self._identify_completeness_issues()),
            'conversation_turns': entity_context.get('conversation_flow_length', 0)
        }