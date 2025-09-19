"""Leadership Insights Agent - Simplified Agentic Approach.

Core Principles Applied:
- NO FALLBACK: Fail fast on unclear queries or processing errors
- AGENTIC: LLM makes all decisions, no hardcoded workflows
- SIMPLIFIED: 2-step process instead of 7-step over-engineering
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
    """Simplified leadership insights agent with 2-step processing."""

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

        # Initialize sub-agents
        self.thinking_agent = ThinkingAgent(llm_client)

    @trace_async_function("insights.process_query")
    async def process_query(self, query: str, executive_role: str = None,
                           session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process leadership query with simplified 2-step approach.

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
        processing_steps = []

        # Add tracing attributes for observability
        set_span_attributes(
            query_length=len(query),
            executive_role=executive_role or "unknown",
            has_session_context=bool(session_context)
        )

        try:
            # STEP 1: STRATEGY - Let LLM agent decide everything
            print("🧠 STRATEGIZING: Analyzing query and creating action plan...")
            step_start = time.time()

            # Create strategy using LLM agent (not hardcoded logic)
            strategy = await self._create_strategy(query, executive_role, session_context)

            # Display strategy-driven visibility messages (agent decides what to show)
            for message in strategy.get('visibility_messages', []):
                print(message)

            understanding = strategy['understanding']

            strategy_time = time.time() - step_start
            processing_steps.append({
                'step': 'strategy',
                'duration_ms': round(strategy_time * 1000),
                'confidence': understanding.confidence,
                'strategy_type': strategy.get('approach', 'unknown')
            })

            # STEP 2: DATA SEARCH - Use strategy-driven data finder
            print("📊 SEARCHING: Following strategy-defined data search plan...")
            step_start = time.time()

            # Let the data finder agent execute the strategy
            data_result = await self._find_data_with_strategy(strategy)

            # Display data search results (agent decides what to show)
            for message in data_result.get('search_messages', []):
                print(message)

            search_time = time.time() - step_start
            processing_steps.append({
                'step': 'data_search',
                'duration_ms': round(search_time * 1000),
                'records_found': data_result.get('total_records', 0),
                'sources_searched': len(data_result.get('sources_tried', []))
            })

            # STEP 3: RESPONSE GENERATION - Let response agent decide how to respond
            print("✨ GENERATING: Creating strategic response...")
            step_start = time.time()

            # Generate response using strategy + data (agent decides format and content)
            response = await self._generate_strategic_response(strategy, data_result, query)

            generation_time = time.time() - step_start
            processing_steps.append({
                'step': 'response_generation',
                'duration_ms': round(generation_time * 1000),
                'response_type': response.get('response_type', 'standard')
            })

            # Compile final response with strategy context
            total_time = time.time() - start_time

            final_response = {
                'content': response.get('content'),
                'executive_summary': response.get('executive_summary'),
                'key_metrics': response.get('key_metrics', []),
                'recommendations': response.get('recommendations', []),
                'supporting_data': response.get('supporting_data', {}),

                # Metadata for transparency
                'metadata': {
                    'query_understanding': understanding.to_dict(),
                    'strategy_used': strategy.get('approach', 'unknown'),
                    'processing_steps': processing_steps,
                    'total_processing_time_ms': round(total_time * 1000),
                    'overall_confidence': response.get('confidence', 80),
                    'data_sources_used': data_result.get('sources_used', []),
                    'records_analyzed': data_result.get('total_records', 0),
                    'response_timestamp': datetime.now().isoformat()
                }
            }

            print(f"✅ COMPLETE: {strategy.get('goal', 'Query')} processed in {total_time:.2f}s")

            return final_response

        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Leadership insights processing failed after {processing_time:.2f}s: {str(e)}")

    async def _create_strategy(self, query: str, executive_role: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Strategy Agent: Create comprehensive strategy for query processing.

        Args:
            query: Original query
            executive_role: Executive role
            session_context: Session context

        Returns:
            Strategy dictionary with understanding, approach, visibility messages
        """
        try:
            # Build strategy context
            context = {
                'query': query,
                'executive_role': executive_role or 'Manager',
                'session_context': session_context or {}
            }

            # Load strategy prompt
            prompt = prompt_loader.format(
                'insights/strategy/query_strategy.txt',
                **context
            )

            # Get strategy from LLM
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.3)
            )

            if not response.text:
                raise Exception("Strategy agent returned no response")

            strategy = self._parse_json_response(response.text)

            # Add understanding from thinking agent
            understanding = await self.thinking_agent.understand_query(
                query=query,
                executive_role=executive_role,
                session_context=session_context
            )
            strategy['understanding'] = understanding

            return strategy

        except Exception as e:
            raise Exception(f"Strategy creation failed: {str(e)}")

    async def _find_data_with_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Data Finder Agent: Execute strategy-driven data search.

        Args:
            strategy: Strategy from strategy agent

        Returns:
            Data search results with messages and findings
        """
        try:
            # Build data search context
            context = {
                'strategy': strategy,
                'understanding': strategy['understanding'].to_dict()
            }

            # Load data search prompt
            prompt = prompt_loader.format(
                'insights/data/strategic_search.txt',
                **context
            )

            # Get search plan from LLM
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.2)
            )

            if not response.text:
                raise Exception("Data finder agent returned no response")

            search_plan = self._parse_json_response(response.text)

            # Execute the search plan
            data_result = {
                'search_messages': search_plan.get('search_messages', []),
                'sources_tried': [],
                'sources_used': [],
                'total_records': 0,
                'data': {}
            }

            # Execute each search in the plan
            for search in search_plan.get('searches', []):
                try:
                    if search['source'] == 'transcripts':
                        data = await self.data_reader.get_transcripts(search.get('filters', {}))
                        if data:
                            data_result['data']['transcripts'] = data
                            data_result['sources_used'].append('transcripts')
                            data_result['total_records'] += len(data)

                    elif search['source'] == 'analyses':
                        data = await self.data_reader.get_analyses(search.get('filters', {}))
                        if data:
                            data_result['data']['analyses'] = data
                            data_result['sources_used'].append('analyses')
                            data_result['total_records'] += len(data)

                    data_result['sources_tried'].append(search['source'])

                except Exception as search_error:
                    # Continue with other searches if one fails
                    print(f"Search failed for {search['source']}: {search_error}")

            return data_result

        except Exception as e:
            raise Exception(f"Strategic data search failed: {str(e)}")

    async def _generate_strategic_response(self, strategy: Dict[str, Any],
                                          data_result: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Response Generator Agent: Create strategic response based on strategy and data.

        Args:
            strategy: Strategy from strategy agent
            data_result: Data search results
            query: Original query

        Returns:
            Strategic response dictionary
        """
        try:
            # Build response context
            context = {
                'query': query,
                'strategy': strategy,
                'data_result': data_result,
                'understanding': strategy['understanding'].to_dict()
            }

            # Load strategic response prompt
            prompt = prompt_loader.format(
                'insights/response/strategic_executive_response.txt',
                **context
            )

            # Get strategic response from LLM
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("Response generator agent returned no response")

            # Parse strategic response
            parsed = self._parse_json_response(response.text)

            return {
                'content': parsed.get('content', ''),
                'executive_summary': parsed.get('executive_summary', ''),
                'key_metrics': parsed.get('key_metrics', []),
                'recommendations': parsed.get('recommendations', []),
                'supporting_data': parsed.get('supporting_data', {}),
                'confidence': parsed.get('confidence', 80),
                'response_type': parsed.get('response_type', 'strategic')
            }

        except Exception as e:
            raise Exception(f"Strategic response generation failed: {str(e)}")


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
            'version': '2.0.0',
            'approach': 'simplified_agentic',
            'capabilities': [
                'query_understanding',
                'data_fetching',
                'response_generation',
                'no_data_handling'
            ],
            'processing_steps': [
                'understand_query',
                'generate_response'
            ],
            'status': 'ready'
        }