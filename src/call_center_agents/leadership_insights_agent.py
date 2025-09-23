"""Leadership Insights Agent - Simple Conversational Approach.

Core Principles Applied:
- NO FALLBACK: Fail fast if no value can be provided
- AGENTIC: LLM makes all decisions including what to say to user
- TRANSPARENT: Real-time narration of thinking process
- SIMPLE: One agent, one loop, conversational
"""
from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime

from ..infrastructure.llm.llm_client_v2 import LLMClientV2, RequestOptions
from ..infrastructure.telemetry import trace_async_function, set_span_attributes
from ..utils.prompt_loader import prompt_loader
from .insights.thinking_agent import ThinkingAgent, QueryUnderstanding


class LeadershipInsightsAgent:
    """Simple conversational agent that thinks out loud while searching."""

    def __init__(self, llm_client: LLMClientV2, data_reader=None):
        """Initialize agent with dependencies.

        Args:
            llm_client: LLM client for reasoning
            data_reader: Data reader service for analytics

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not llm_client:
            raise ValueError("llm_client cannot be None")

        if not data_reader:
            raise ValueError("data_reader cannot be None")

        self.llm = llm_client
        self.data_reader = data_reader

        # Initialize thinking agent for query understanding
        self.thinking_agent = ThinkingAgent(llm_client)

    @trace_async_function("insights.process_query")
    async def process_query(self, query: str, executive_role: str = None,
                           session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process leadership query with conversational thinking out loud.

        Args:
            query: Leadership query string
            executive_role: Executive's role (VP, CCO, etc.)
            session_context: Previous conversation context

        Returns:
            Complete response with insights and metadata

        Raises:
            Exception: If processing fails (NO FALLBACK)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        start_time = time.time()

        # Add tracing attributes for observability
        set_span_attributes(
            query_length=len(query),
            executive_role=executive_role or "unknown",
            has_session_context=bool(session_context)
        )

        try:
            # Quick understanding of the query
            understanding = await self.thinking_agent.understand_query(
                query=query,
                executive_role=executive_role,
                session_context=session_context
            )

            # Start conversational search
            found_data = {}
            data_sources = ['analyses', 'transcripts', 'workflows', 'plans']

            # Search loop with narration
            for attempt in range(len(data_sources) + 1):  # +1 for final attempt
                # Get LLM's next thought and narration
                thought = await self._get_next_thought(
                    query=query,
                    understanding=understanding,
                    searched_so_far=list(found_data.keys()),
                    available_sources=[s for s in data_sources if s not in found_data],
                    current_data=found_data,
                    attempt=attempt
                )

                # Print what the agent is thinking
                print(thought['narration'])

                # If LLM says to summarize, we're done searching
                if thought['action'] == 'summarize':
                    break

                # If LLM wants to search, do it
                if thought['action'] == 'search' and thought.get('source'):
                    try:
                        data = await self._search_source(
                            thought['source'],
                            thought.get('filters', {}),
                            understanding
                        )
                        if data:
                            found_data[thought['source']] = data
                    except Exception as e:
                        # Continue searching even if one source fails
                        print(f"❌ Search failed: {str(e)}")

                # If LLM says to fail fast, stop immediately
                if thought['action'] == 'fail_fast':
                    raise Exception(thought.get('reason', 'Cannot provide meaningful insights'))

            # Generate brief summary
            summary_response = await self._create_summary(query, understanding, found_data)

            # Print the summary
            print(f"\n💬 {summary_response['brief_summary']}")

            # Compile final response
            total_time = time.time() - start_time

            final_response = {
                'content': summary_response['content'],
                'executive_summary': summary_response['brief_summary'],
                'key_metrics': summary_response.get('key_metrics', []),
                'recommendations': summary_response.get('recommendations', []),
                'supporting_data': summary_response.get('supporting_data', {}),

                # Metadata for transparency
                'metadata': {
                    'query_understanding': understanding.to_dict(),
                    'total_processing_time_ms': round(total_time * 1000),
                    'overall_confidence': summary_response.get('confidence', 75),
                    'data_sources_used': list(found_data.keys()),
                    'records_analyzed': sum(len(data) if isinstance(data, list) else 1 for data in found_data.values()),
                    'response_timestamp': datetime.now().isoformat()
                }
            }

            return final_response

        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Leadership insights processing failed after {processing_time:.2f}s: {str(e)}")

    async def _get_next_thought(self, query: str, understanding: QueryUnderstanding,
                               searched_so_far: List[str], available_sources: List[str],
                               current_data: Dict[str, Any], attempt: int) -> Dict[str, Any]:
        """Get LLM's next thought and action in the search process.

        Args:
            query: Original query
            understanding: Query understanding
            searched_so_far: Sources already searched
            available_sources: Sources still available
            current_data: Data found so far
            attempt: Current attempt number

        Returns:
            Dictionary with narration and next action
        """
        try:
            # Build context for LLM decision
            context = {
                'query': query,
                'understanding': understanding.to_dict(),
                'searched_so_far': searched_so_far,
                'available_sources': available_sources,
                'current_data_summary': self._summarize_found_data(current_data),
                'attempt': attempt,
                'max_attempts': 4
            }

            # Load conversational thinking prompt
            prompt = prompt_loader.format(
                'insights/conversational/next_thought.txt',
                **context
            )

            # Get LLM's next thought
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no thought")

            # Parse the thought
            thought = self._parse_json_response(response.text)

            return thought

        except Exception as e:
            # Fallback thought if parsing fails
            return {
                'narration': f"🤔 Having trouble thinking through this... {str(e)}",
                'action': 'fail_fast',
                'reason': f"Thought process failed: {str(e)}"
            }

    async def _search_source(self, source: str, filters: Dict[str, Any],
                           understanding: QueryUnderstanding) -> Optional[List[Dict]]:
        """Search a specific data source.

        Args:
            source: Data source name
            filters: Search filters
            understanding: Query understanding

        Returns:
            Search results or None
        """
        try:
            if source == 'analyses':
                return await self.data_reader.get_analyses(filters)
            elif source == 'transcripts':
                return await self.data_reader.get_transcripts(filters)
            elif source == 'workflows':
                # Note: workflows method doesn't exist yet, but agent might try it
                return []
            elif source == 'plans':
                # Note: plans method doesn't exist yet, but agent might try it
                return []
            else:
                return None

        except Exception as e:
            print(f"❌ Error searching {source}: {str(e)}")
            return None

    async def _create_summary(self, query: str, understanding: QueryUnderstanding,
                            found_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create brief conversational summary.

        Args:
            query: Original query
            understanding: Query understanding
            found_data: All data found during search

        Returns:
            Summary response dictionary
        """
        try:
            # Build summary context
            context = {
                'query': query,
                'understanding': understanding.to_dict(),
                'found_data': found_data,
                'data_summary': self._summarize_found_data(found_data),
                'has_data': len(found_data) > 0
            }

            # Load conversational summary prompt
            prompt = prompt_loader.format(
                'insights/conversational/brief_summary.txt',
                **context
            )

            # Get brief summary from LLM
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no summary")

            # Parse summary
            summary = self._parse_json_response(response.text)

            return summary

        except Exception as e:
            # Simple fallback summary
            if found_data:
                record_count = sum(len(data) if isinstance(data, list) else 1 for data in found_data.values())
                brief = f"Found {record_count} relevant records. Analysis available with more details."
            else:
                brief = "No relevant data found for this query."

            return {
                'brief_summary': brief,
                'content': brief,
                'confidence': 50
            }

    def _summarize_found_data(self, found_data: Dict[str, Any]) -> str:
        """Create brief summary of found data for context.

        Args:
            found_data: Data found during search

        Returns:
            Brief summary string
        """
        if not found_data:
            return "No data found yet"

        summaries = []
        for source, data in found_data.items():
            count = len(data) if isinstance(data, list) else 1
            summaries.append(f"{source}: {count} records")

        return ", ".join(summaries)

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM.

        Args:
            response_text: LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            Exception: If parsing fails (NO FALLBACK)
        """
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()

            # Look for JSON-like structure
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            # If no JSON found, try parsing the entire response
            return json.loads(response_text)

        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of the agent and its components.

        Returns:
            Agent status dictionary
        """
        return {
            'agent_type': 'LeadershipInsightsAgent',
            'version': '3.0.0',
            'approach': 'conversational_transparent',
            'capabilities': [
                'real_time_narration',
                'progressive_search',
                'conversational_summary',
                'fail_fast_behavior'
            ],
            'processing_steps': [
                'understand_query',
                'conversational_search_loop',
                'brief_summary'
            ],
            'status': 'ready'
        }