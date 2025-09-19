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
            # STEP 1: UNDERSTAND - Query analysis and data check
            print("🧠 UNDERSTANDING: Query analysis and data check...")
            step_start = time.time()

            understanding = await self.thinking_agent.understand_query(
                query=query,
                executive_role=executive_role,
                session_context=session_context
            )

            # Quick data availability check
            data_summary = await self.data_reader.get_data_summary()

            thinking_time = time.time() - step_start
            processing_steps.append({
                'step': 'understanding',
                'duration_ms': round(thinking_time * 1000),
                'confidence': understanding.confidence,
                'data_available': data_summary.get('total_records', 0) > 0
            })

            # Fast exit for no data - generate helpful response immediately
            if data_summary.get('total_records', 0) == 0:
                print("💭 NO DATA: Generating helpful guidance...")
                response = await self._generate_no_data_response(understanding, query)

                total_time = time.time() - start_time
                response['metadata'] = {
                    'query_understanding': understanding.to_dict(),
                    'processing_steps': processing_steps,
                    'total_processing_time_ms': round(total_time * 1000),
                    'overall_confidence': 70,  # Default confidence for guidance
                    'data_sources_used': [],
                    'records_analyzed': 0,
                    'response_timestamp': datetime.now().isoformat()
                }

                print(f"✅ COMPLETE: No-data response in {total_time:.2f}s")
                return response

            # STEP 2: GENERATE - Fetch data and create response
            print("📊 GENERATING: Fetching data and creating response...")
            step_start = time.time()

            # Fetch relevant data based on understanding
            relevant_data = await self._fetch_relevant_data(understanding)

            # Generate complete response with all context
            response = await self._generate_response(understanding, relevant_data, query)

            generation_time = time.time() - step_start
            processing_steps.append({
                'step': 'generation',
                'duration_ms': round(generation_time * 1000),
                'records_processed': relevant_data.get('_metadata', {}).get('total_records', 0)
            })

            # Compile final response
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
                    'processing_steps': processing_steps,
                    'total_processing_time_ms': round(total_time * 1000),
                    'overall_confidence': response.get('confidence', 80),
                    'data_sources_used': list(relevant_data.keys()) if relevant_data else [],
                    'records_analyzed': relevant_data.get('_metadata', {}).get('total_records', 0),
                    'response_timestamp': datetime.now().isoformat()
                }
            }

            print(f"✅ COMPLETE: Processed in {total_time:.2f}s with {response.get('confidence', 80)}% confidence")

            return final_response

        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Leadership insights processing failed after {processing_time:.2f}s: {str(e)}")

    async def _generate_no_data_response(self, understanding: QueryUnderstanding, query: str) -> Dict[str, Any]:
        """Generate helpful response when no data is available.

        Args:
            understanding: Query understanding
            query: Original query

        Returns:
            Response dictionary
        """
        try:
            # Build context for no-data response
            context = {
                'query': query,
                'understanding': understanding.to_dict(),
                'executive_role': understanding.executive_context
            }

            # Load no-data response prompt
            prompt = prompt_loader.format(
                'insights/responses/no_data_guidance.txt',
                **context
            )

            # Get LLM response
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no response")

            # Parse response
            parsed = self._parse_json_response(response.text)

            return {
                'content': parsed.get('content', 'No data available for analysis.'),
                'executive_summary': parsed.get('executive_summary', ''),
                'recommendations': parsed.get('recommendations', []),
                'key_metrics': [],
                'supporting_data': {}
            }

        except Exception as e:
            # Fallback response for no data
            return {
                'content': f"I understand you're asking about {understanding.focus_area} matters. However, there's currently no data available in the system to analyze. I recommend setting up data collection processes and returning to this analysis once data is available.",
                'executive_summary': 'No data available for analysis',
                'recommendations': [
                    'Implement data collection processes',
                    'Verify data pipeline functionality',
                    'Return to analysis once data is available'
                ],
                'key_metrics': [],
                'supporting_data': {}
            }

    async def _fetch_relevant_data(self, understanding: QueryUnderstanding) -> Dict[str, Any]:
        """Fetch data relevant to the query understanding.

        Args:
            understanding: Query understanding

        Returns:
            Relevant data dictionary
        """
        try:
            # Build filters based on understanding
            filters = {
                'focus_area': understanding.focus_area,
                'time_frame': understanding.time_frame,
                'limit': 1000  # Reasonable limit for analysis
            }

            # Add specific filters based on query type
            if understanding.core_intent == 'compliance_review':
                filters['has_compliance_issues'] = True

            if understanding.urgency == 'critical':
                filters['urgency'] = ['high', 'critical']

            # Fetch data from multiple sources
            relevant_data = {}

            # Always get transcripts as primary data source
            transcripts = await self.data_reader.get_transcripts(filters)
            if transcripts:
                relevant_data['transcripts'] = transcripts

            # Get analyses if available
            analyses = await self.data_reader.get_analyses(filters)
            if analyses:
                relevant_data['analyses'] = analyses

            # Add metadata
            total_records = sum(len(data) if isinstance(data, list) else 1 for data in relevant_data.values())
            relevant_data['_metadata'] = {
                'total_records': total_records,
                'filters_applied': filters,
                'data_sources': list(relevant_data.keys())
            }

            return relevant_data

        except Exception as e:
            raise Exception(f"Data fetching failed: {str(e)}")

    async def _generate_response(self, understanding: QueryUnderstanding,
                               data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Generate complete executive response with all context.

        Args:
            understanding: Query understanding
            data: Relevant data
            query: Original query

        Returns:
            Complete response dictionary
        """
        try:
            # Build comprehensive context
            context = {
                'query': query,
                'understanding': understanding.to_dict(),
                'data': data,
                'has_data': len(data) > 1,  # More than just metadata
                'record_count': data.get('_metadata', {}).get('total_records', 0)
            }

            # Load unified response prompt
            prompt = prompt_loader.format(
                'insights/responses/unified_executive_response.txt',
                **context
            )

            # Get comprehensive LLM response
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no response")

            # Parse comprehensive response
            parsed = self._parse_json_response(response.text)

            return {
                'content': parsed.get('content', ''),
                'executive_summary': parsed.get('executive_summary', ''),
                'key_metrics': parsed.get('key_metrics', []),
                'recommendations': parsed.get('recommendations', []),
                'supporting_data': parsed.get('supporting_data', {}),
                'confidence': parsed.get('confidence', 80)
            }

        except Exception as e:
            raise Exception(f"Response generation failed: {str(e)}")

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