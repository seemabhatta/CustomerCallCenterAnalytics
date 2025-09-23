"""
SessionContext for Two-Layer Memory Architecture.

Lightweight context management that holds entity references and uses
graph traversal for resolution. Part of the primary memory (KuzuDB graph)
and secondary memory (session context) design pattern.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from ...storage.graph_store import GraphStore, GraphStoreError
from ...storage.queued_graph_store import QueuedGraphStore


class SessionContextError(Exception):
    """Exception raised for session context errors."""
    pass


class SessionContext:
    """Lightweight session context that maintains entity references to the knowledge graph.

    This class implements the "secondary memory" layer in our two-layer architecture:
    1. Primary Memory (KuzuDB): Persistent storage of all entities and relationships
    2. Secondary Memory (SessionContext): Lightweight pointers to graph entities

    Key Benefits:
    - No data duplication - only entity IDs are stored
    - Fast context resolution via graph traversal
    - Industry-standard approach similar to Claude Code/ChatGPT
    """

    def __init__(self, session_id: str, graph_store: Optional[QueuedGraphStore] = None):
        """Initialize session context with graph store connection.

        Args:
            session_id: Unique session identifier
            graph_store: QueuedGraphStore instance for entity resolution

        Raises:
            SessionContextError: If initialization fails
        """
        if not session_id:
            raise SessionContextError("session_id cannot be empty")

        self.session_id = session_id
        self.graph_store = graph_store or QueuedGraphStore()

        # Lightweight entity references (no data duplication)
        self.entity_refs = {
            'transcript_id': None,
            'analysis_id': None,
            'plan_id': None,
            'workflow_ids': [],
            'active_workflow_id': None,
            'customer_id': None
        }

        # Conversation flow tracking
        self.conversation_flow = []
        self.last_entity_mentioned = None
        self.entity_mention_time = None

        # Tool call metadata tracking
        self.tool_call_history = []  # Last 10 tool calls with metadata
        self.current_metadata = {}   # Metadata from most recent tool calls

    def set_active_transcript(self, transcript_id: str) -> bool:
        """Set the active transcript and derive related entities from graph."""
        try:
            if not transcript_id:
                raise SessionContextError("transcript_id cannot be empty")

            # Store transcript reference
            self.entity_refs['transcript_id'] = transcript_id
            self.last_entity_mentioned = 'transcript'
            self.entity_mention_time = datetime.utcnow()

            # Use graph traversal to find related entities
            pipeline_data = self.graph_store.get_pipeline_for_transcript(transcript_id)

            # Defensive programming: handle unexpected data types
            if not isinstance(pipeline_data, dict):
                pipeline_data = {}

            if pipeline_data.get('analysis'):
                self.entity_refs['analysis_id'] = pipeline_data['analysis'].get('analysis_id')

            if pipeline_data.get('plan'):
                self.entity_refs['plan_id'] = pipeline_data['plan'].get('plan_id')

            if pipeline_data.get('workflows'):
                workflow_ids = [w.get('workflow_id') for w in pipeline_data['workflows'] if w.get('workflow_id')]
                self.entity_refs['workflow_ids'] = workflow_ids
                if workflow_ids:
                    self.entity_refs['active_workflow_id'] = workflow_ids[0]  # Most recent

            # Extract customer_id from transcript if available
            transcript_data = pipeline_data.get('transcript', {})
            if transcript_data.get('customer_id'):
                self.entity_refs['customer_id'] = transcript_data['customer_id']

            # Track in conversation flow
            self.conversation_flow.append({
                'action': 'set_active_transcript',
                'transcript_id': transcript_id,
                'timestamp': datetime.utcnow().isoformat(),
                'derived_entities': {
                    'analysis_id': self.entity_refs['analysis_id'],
                    'plan_id': self.entity_refs['plan_id'],
                    'workflow_count': len(self.entity_refs['workflow_ids'])
                }
            })

            return True

        except GraphStoreError as e:
            raise SessionContextError(f"Failed to set active transcript: {str(e)}")
        except Exception as e:
            raise SessionContextError(f"Unexpected error setting transcript: {str(e)}")

    def set_active_workflow(self, workflow_id: str) -> bool:
        """Set the active workflow for step execution context."""
        try:
            if not workflow_id:
                raise SessionContextError("workflow_id cannot be empty")

            # Verify workflow exists in current context
            if workflow_id not in self.entity_refs['workflow_ids']:
                # Try to resolve via graph if not in current list
                transcript_id = self.entity_refs['transcript_id']
                if transcript_id:
                    workflows = self.graph_store.get_workflows_for_transcript(transcript_id)
                    workflow_ids = [w.get('workflow_id') for w in workflows if w.get('workflow_id')]
                    if workflow_id in workflow_ids:
                        self.entity_refs['workflow_ids'] = workflow_ids
                    else:
                        raise SessionContextError(f"Workflow {workflow_id} not found in context")
                else:
                    raise SessionContextError(f"No transcript context for workflow {workflow_id}")

            self.entity_refs['active_workflow_id'] = workflow_id
            self.last_entity_mentioned = 'workflow'
            self.entity_mention_time = datetime.utcnow()

            # Track in conversation flow
            self.conversation_flow.append({
                'action': 'set_active_workflow',
                'workflow_id': workflow_id,
                'timestamp': datetime.utcnow().isoformat()
            })

            return True

        except Exception as e:
            raise SessionContextError(f"Failed to set active workflow: {str(e)}")

    def resolve_reference(self, reference: str) -> Optional[str]:
        """Resolve contextual references like 'this call' or 'the plan' to actual entity IDs.

        Args:
            reference: Natural language reference to resolve

        Returns:
            Entity ID if resolved, None otherwise
        """
        try:
            # Use GraphStore's resolution logic with current context
            resolved_id = self.graph_store.resolve_entity_reference(reference, self.entity_refs)

            if resolved_id:
                # Track the resolution in conversation flow
                self.conversation_flow.append({
                    'action': 'resolve_reference',
                    'reference': reference,
                    'resolved_id': resolved_id,
                    'timestamp': datetime.utcnow().isoformat()
                })

            return resolved_id

        except GraphStoreError as e:
            raise SessionContextError(f"Failed to resolve reference: {str(e)}")

    def get_workflows_for_context(self, workflow_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get workflows associated with current transcript context."""
        try:
            transcript_id = self.entity_refs['transcript_id']
            if not transcript_id:
                raise SessionContextError("No active transcript in context")

            workflows = self.graph_store.get_workflows_for_transcript(transcript_id, workflow_type)

            # Track in conversation flow
            self.conversation_flow.append({
                'action': 'get_workflows_for_context',
                'transcript_id': transcript_id,
                'workflow_type': workflow_type,
                'workflow_count': len(workflows),
                'timestamp': datetime.utcnow().isoformat()
            })

            return workflows

        except GraphStoreError as e:
            raise SessionContextError(f"Failed to get workflows: {str(e)}")

    def get_pipeline_data(self) -> Dict[str, Any]:
        """Get complete pipeline data for current transcript."""
        try:
            transcript_id = self.entity_refs['transcript_id']
            if not transcript_id:
                raise SessionContextError("No active transcript in context")

            return self.graph_store.get_pipeline_for_transcript(transcript_id)

        except GraphStoreError as e:
            raise SessionContextError(f"Failed to get pipeline data: {str(e)}")

    def get_current_context(self) -> Dict[str, Any]:
        """Get current context state for debugging and LLM context building."""
        return {
            'session_id': self.session_id,
            'entity_refs': self.entity_refs.copy(),
            'last_entity_mentioned': self.last_entity_mentioned,
            'entity_mention_time': self.entity_mention_time.isoformat() if self.entity_mention_time else None,
            'conversation_flow_length': len(self.conversation_flow),
            'has_active_transcript': bool(self.entity_refs['transcript_id']),
            'has_active_workflow': bool(self.entity_refs['active_workflow_id']),
            'workflow_count': len(self.entity_refs['workflow_ids'])
        }

    def clear_context(self) -> None:
        """Clear all entity references (but keep session_id)."""
        self.entity_refs = {
            'transcript_id': None,
            'analysis_id': None,
            'plan_id': None,
            'workflow_ids': [],
            'active_workflow_id': None,
            'customer_id': None
        }
        self.conversation_flow.clear()
        self.last_entity_mentioned = None
        self.entity_mention_time = None

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of conversation flow for LLM context."""
        recent_actions = self.conversation_flow[-5:] if len(self.conversation_flow) > 5 else self.conversation_flow

        return {
            'total_actions': len(self.conversation_flow),
            'recent_actions': recent_actions,
            'current_context': self.get_current_context()
        }

    def track_tool_call(self, tool_name: str, parameters: Dict[str, Any],
                       result: Dict[str, Any], metadata: Dict[str, Any] = None) -> None:
        """Track tool call with its metadata for context building.

        Args:
            tool_name: Name of the tool called
            parameters: Parameters passed to the tool
            result: Result returned by the tool
            metadata: Metadata about the request/response (e.g., counts, completeness)
        """
        tool_call_record = {
            'tool_name': tool_name,
            'parameters': parameters,
            'result_summary': self._summarize_result(result),
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat(),
            'success': result is not None and 'error' not in result
        }

        # Keep only last 10 tool calls
        self.tool_call_history.append(tool_call_record)
        if len(self.tool_call_history) > 10:
            self.tool_call_history.pop(0)

        # Update current metadata for immediate context
        if metadata:
            self.current_metadata[tool_name] = metadata

    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a lightweight summary of tool result for context tracking."""
        if isinstance(result, dict):
            if 'transcripts' in result:
                return {
                    'type': 'transcript_list',
                    'count': len(result.get('transcripts', [])),
                    'has_metadata': 'metadata' in result
                }
            elif 'workflows' in result:
                return {
                    'type': 'workflow_list',
                    'count': len(result.get('workflows', [])),
                    'has_metadata': 'metadata' in result
                }
            elif 'id' in result:
                return {
                    'type': 'single_entity',
                    'entity_id': result.get('id'),
                    'entity_type': result.get('type', 'unknown')
                }
            else:
                return {
                    'type': 'other',
                    'keys': list(result.keys())[:5]  # First 5 keys for debugging
                }
        else:
            return {'type': 'non_dict', 'data_type': type(result).__name__}

    def get_metadata_context(self) -> Dict[str, Any]:
        """Get metadata context for LLM decision making."""
        return {
            'recent_tool_calls': self.tool_call_history[-5:],  # Last 5 calls
            'current_metadata': self.current_metadata,
            'metadata_summary': {
                'total_tool_calls': len(self.tool_call_history),
                'recent_completeness_issues': [
                    call for call in self.tool_call_history[-5:]
                    if call.get('metadata', {}).get('completeness') == 'partial'
                ]
            }
        }