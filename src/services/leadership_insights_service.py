"""Leadership Insights Service - Business logic orchestration layer.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- AGENTIC: All routing and decisions made by LLM agents
- SERVICE LAYER: Contains ALL business logic, API layer just routes
"""
from typing import Dict, Any, Optional, List
import time
from datetime import datetime

from ..infrastructure.llm.llm_client_v2 import LLMClientV2, OpenAIProvider
from ..storage.session_store import SessionStore
from ..storage.insights_cache_store import InsightsCacheStore
from ..storage.insights_pattern_store import InsightsPatternStore
from ..agents.leadership_insights_agent import LeadershipInsightsAgent
from .data_reader_service import DataReaderService


class LeadershipInsightsService:
    """Service layer for Leadership Insights - contains ALL business logic.

    Orchestrates the complete insights workflow including session management,
    caching, agent processing, and pattern learning.
    """

    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        """Initialize service with dependencies.

        Args:
            api_key: OpenAI API key
            db_path: Database path for storage layers

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not api_key:
            raise ValueError("API key cannot be empty")

        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.api_key = api_key
        self.db_path = db_path

        # Initialize storage layers
        self.session_store = SessionStore(db_path)
        self.cache_store = InsightsCacheStore(db_path)
        self.pattern_store = InsightsPatternStore(db_path)

        # Initialize LLM client
        provider = OpenAIProvider(api_key=api_key)
        self.llm_client = LLMClientV2(provider=provider)

        # Initialize data reader
        self.data_reader = DataReaderService(db_path)

        # Initialize the main agent
        self.insights_agent = LeadershipInsightsAgent(
            llm_client=self.llm_client,
            data_reader=self.data_reader
        )

    async def chat(self, query: str, executive_id: str, executive_role: str = "Manager",
                   session_id: str = None) -> Dict[str, Any]:
        """Main chat interface for leadership insights.

        Args:
            query: Leadership query string
            executive_id: Unique identifier for executive
            executive_role: Executive's role (VP, CCO, etc.)
            session_id: Optional session ID to continue conversation

        Returns:
            Complete response with insights and metadata

        Raises:
            Exception: If chat processing fails (NO FALLBACK)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not executive_id:
            raise ValueError("Executive ID cannot be empty")

        start_time = time.time()

        try:
            # Step 1: Get or create session
            if session_id:
                session = self.session_store.get_session(session_id)
                if not session:
                    raise ValueError(f"Session {session_id} not found")
            else:
                # Let agent determine focus area during processing
                focus_area = None
                session = self.session_store.create_session(
                    executive_id=executive_id,
                    executive_role=executive_role,
                    focus_area=focus_area
                )

            session_id = session['session_id']

            # Step 2: Check cache for similar recent queries
            cache_result = await self._check_cache(query, executive_role)
            if cache_result:
                # Store cached result in session
                message_id = self.session_store.add_message(
                    session_id=session_id,
                    role='user',
                    content=query
                )

                self.session_store.add_message(
                    session_id=session_id,
                    role='assistant',
                    content=cache_result['response']['content'],
                    metadata={
                        'cache_hit': True,
                        'response_time_ms': round((time.time() - start_time) * 1000),
                        'confidence_score': cache_result['response']['metadata']['overall_confidence']
                    }
                )

                return {
                    **cache_result['response'],
                    'session_id': session_id,
                    'cache_hit': True
                }

            # Step 3: Get session context for the agent
            session_context = await self._build_session_context(session)

            # Step 4: Store user message
            self.session_store.add_message(
                session_id=session_id,
                role='user',
                content=query
            )

            # Step 5: Process query with insights agent
            response = await self.insights_agent.process_query(
                query=query,
                executive_role=executive_role,
                session_context=session_context
            )

            # Step 6: Store agent response
            processing_time = time.time() - start_time
            self.session_store.add_message(
                session_id=session_id,
                role='assistant',
                content=response['content'],
                metadata={
                    'query_classification': response['metadata']['query_understanding'],
                    'data_sources_used': response['metadata']['data_sources_used'],
                    'confidence_score': response['metadata']['overall_confidence'],
                    'response_time_ms': round(processing_time * 1000),
                    'cache_hit': False
                }
            )

            # Step 7: Cache response for future use
            await self._cache_response(query, response, executive_role)

            # Step 8: Store learning patterns (async, non-blocking)
            await self._store_learning_patterns(response)

            # Step 9: Update session context and focus area
            query_understanding = response['metadata']['query_understanding']
            agent_focus_area = query_understanding.get('focus_area')

            # Update session with agent-determined focus area
            if agent_focus_area:
                self.session_store.update_session_focus_area(session_id, agent_focus_area)

            self.session_store.update_session_context(
                session_id=session_id,
                context_data={
                    'last_query_type': query_understanding.get('core_intent'),
                    'focus_area': agent_focus_area,
                    'recent_topics': [query]  # Could expand to track more topics
                }
            )

            # Add session info to response
            response['session_id'] = session_id
            response['cache_hit'] = False

            return response

        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Chat processing failed after {processing_time:.2f}s: {str(e)}")

    async def get_session_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum messages to return

        Returns:
            Session history

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")

        try:
            # Get session info
            session = self.session_store.get_session(session_id)
            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Get messages
            messages = self.session_store.get_session_messages(session_id, limit)

            return {
                'session': session,
                'messages': messages,
                'message_count': len(messages)
            }

        except Exception as e:
            raise Exception(f"Session history retrieval failed: {str(e)}")

    async def get_executive_sessions(self, executive_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sessions for an executive.

        Args:
            executive_id: Executive identifier
            limit: Maximum sessions to return

        Returns:
            List of sessions

        Raises:
            Exception: If retrieval fails (NO FALLBACK)
        """
        if not executive_id:
            raise ValueError("Executive ID cannot be empty")

        try:
            sessions = self.session_store.get_executive_sessions(executive_id, limit)
            return sessions

        except Exception as e:
            raise Exception(f"Executive sessions retrieval failed: {str(e)}")

    async def delete_session(self, session_id: str) -> bool:
        """Delete a leadership session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found

        Raises:
            Exception: If deletion fails (NO FALLBACK)
        """
        if not session_id:
            raise ValueError("Session ID cannot be empty")

        try:
            # Check if session exists first
            session = self.session_store.get_session(session_id)
            if not session:
                return False

            # Delete session and all associated messages
            success = self.session_store.delete_session(session_id)
            if not success:
                raise Exception(f"Failed to delete session {session_id}")

            return True

        except Exception as e:
            raise Exception(f"Session deletion failed: {str(e)}")

    async def get_insights_dashboard(self, executive_role: str = None) -> Dict[str, Any]:
        """Get pre-computed insights dashboard.

        Args:
            executive_role: Optional role filter

        Returns:
            Dashboard data

        Raises:
            Exception: If dashboard generation fails (NO FALLBACK)
        """
        try:
            # Get data summary
            data_summary = await self.data_reader.get_data_summary()

            # Get cache statistics
            cache_stats = self.cache_store.get_cache_statistics()

            # Get pattern statistics
            pattern_stats = self.pattern_store.get_pattern_statistics()

            # Compile dashboard
            dashboard = {
                'data_overview': data_summary,
                'cache_performance': cache_stats,
                'learning_progress': pattern_stats,
                'system_status': {
                    'agent_status': self.insights_agent.get_agent_status(),
                    'last_updated': datetime.now().isoformat()
                }
            }

            return dashboard

        except Exception as e:
            raise Exception(f"Dashboard generation failed: {str(e)}")


    async def _check_cache(self, query: str, executive_role: str) -> Optional[Dict[str, Any]]:
        """Check cache for similar recent queries.

        Args:
            query: Query string
            executive_role: Executive role

        Returns:
            Cached response or None
        """
        try:
            # Check for exact or similar cached queries
            cached = self.cache_store.get_cached_aggregation(
                query=query,
                filters={'executive_role': executive_role}
            )

            if cached:
                return {
                    'response': cached['aggregated_data'],
                    'cache_metadata': {
                        'hit_count': cached['hit_count'],
                        'created_at': cached['created_at']
                    }
                }

            return None

        except Exception:
            # Cache errors shouldn't fail the main process
            return None

    async def _build_session_context(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Build session context for the agent.

        Args:
            session: Session data

        Returns:
            Session context
        """
        context = {
            'focus_area': session.get('focus_area'),
            'executive_role': session.get('executive_role'),
            'session_started': session.get('started_at'),
            'previous_context': {}
        }

        # Parse stored context data if available
        if session.get('context_data'):
            try:
                import json
                stored_context = json.loads(session['context_data'])
                context['previous_context'] = stored_context
            except (json.JSONDecodeError, TypeError):
                pass

        return context

    async def _cache_response(self, query: str, response: Dict[str, Any], executive_role: str):
        """Cache response for future use.

        Args:
            query: Original query
            response: Generated response
            executive_role: Executive role
        """
        try:
            # Cache the response
            self.cache_store.store_aggregation(
                query=query,
                aggregated_data=response,
                data_sources=response['metadata']['data_sources_used'],
                record_count=response['metadata']['records_analyzed'],
                computation_time_ms=response['metadata']['total_processing_time_ms'],
                filters={'executive_role': executive_role},
                ttl_hours=24  # Cache for 24 hours
            )

        except Exception as e:
            # Cache errors shouldn't fail the main process
            print(f"Cache storage failed: {str(e)}")

    async def _store_learning_patterns(self, response: Dict[str, Any]):
        """Store learning patterns from successful responses.

        Args:
            response: Generated response with learning insights
        """
        try:
            learning_insights = response.get('learning_insights', {})
            patterns = learning_insights.get('patterns', [])

            for pattern in patterns:
                if pattern.get('effectiveness', 0) > 70:  # Only store high-quality patterns
                    self.pattern_store.store_pattern(
                        pattern_type=pattern.get('type', 'general'),
                        query_pattern=pattern.get('query_pattern', ''),
                        successful_approach=pattern.get('approach', {}),
                        effectiveness_score=pattern.get('effectiveness', 75)
                    )

        except Exception as e:
            # Learning errors shouldn't fail the main process
            print(f"Pattern storage failed: {str(e)}")


    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Cache statistics dictionary
        """
        try:
            return self.cache_store.get_cache_statistics()
        except Exception as e:
            raise Exception(f"Failed to get cache statistics: {str(e)}")

    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get learning pattern statistics.

        Returns:
            Pattern statistics dictionary
        """
        try:
            return self.pattern_store.get_pattern_statistics()
        except Exception as e:
            raise Exception(f"Failed to get pattern statistics: {str(e)}")

    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and health.

        Returns:
            Service status dictionary
        """
        return {
            'service_name': 'LeadershipInsightsService',
            'version': '1.0.0',
            'status': 'ready',
            'components': {
                'agent': self.insights_agent.get_agent_status(),
                'session_store': 'ready',
                'cache_store': 'ready',
                'pattern_store': 'ready',
                'data_reader': 'ready'
            },
            'last_checked': datetime.now().isoformat()
        }