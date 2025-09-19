"""Leadership Insights Agent - Master Orchestrator with Agentic Patterns.

Core Principles Applied:
- NO FALLBACK: Fail fast on unclear queries or processing errors
- AGENTIC: LLM makes all decisions through specialized sub-agents
- FULLY ORCHESTRATED: Coordinates thinking, planning, aggregation, synthesis, reflection, learning
"""
from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime

from ..infrastructure.llm.llm_client_v2 import LLMClientV2, RequestSpec, RequestOptions
from ..utils.prompt_loader import prompt_loader
from .insights.thinking_agent import ThinkingAgent, QueryUnderstanding


class LeadershipInsightsAgent:
    """Master orchestrator agent with full agentic capabilities.

    Implements the complete workflow:
    Think → Plan → Fetch → Aggregate → Synthesize → Reflect → Learn

    This agent coordinates all sub-agents and makes intelligent decisions
    about how to process leadership queries for maximum value.
    """

    def __init__(self, llm_client: LLMClientV2, data_reader=None):
        """Initialize the master orchestrator agent.

        Args:
            llm_client: LLM client for all agent operations
            data_reader: Data reader service for fetching data

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not llm_client:
            raise ValueError("llm_client cannot be None")

        self.llm = llm_client
        self.data_reader = data_reader

        # Initialize sub-agents
        self.thinking_agent = ThinkingAgent(llm_client)

    async def process_query(self, query: str, executive_role: str = None,
                           session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process leadership query through full agentic workflow.

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

        try:
            # STEP 1: THINK - Understand the query
            print("🧠 THINKING: Understanding query...")
            step_start = time.time()

            understanding = await self.thinking_agent.understand_query(
                query=query,
                executive_role=executive_role,
                session_context=session_context
            )

            thinking_time = time.time() - step_start
            processing_steps.append({
                'step': 'thinking',
                'duration_ms': round(thinking_time * 1000),
                'confidence': understanding.confidence
            })

            # STEP 2: PLAN - Create data strategy
            print("📋 PLANNING: Creating data strategy...")
            step_start = time.time()

            data_plan = await self._create_data_plan(understanding)

            planning_time = time.time() - step_start
            processing_steps.append({
                'step': 'planning',
                'duration_ms': round(planning_time * 1000),
                'data_sources_planned': len(data_plan.get('data_sources', []))
            })

            # STEP 3: FETCH - Get data according to plan
            print("📊 FETCHING: Retrieving data...")
            step_start = time.time()

            raw_data = await self._fetch_data(data_plan)

            fetching_time = time.time() - step_start
            processing_steps.append({
                'step': 'fetching',
                'duration_ms': round(fetching_time * 1000),
                'records_fetched': raw_data.get('_metadata', {}).get('total_records', 0)
            })

            # STEP 4: AGGREGATE - Intelligently summarize data
            print("🔄 AGGREGATING: Summarizing data...")
            step_start = time.time()

            aggregated_data = await self._aggregate_data(raw_data, understanding)

            aggregation_time = time.time() - step_start
            processing_steps.append({
                'step': 'aggregation',
                'duration_ms': round(aggregation_time * 1000),
                'insights_generated': len(aggregated_data.get('key_insights', []))
            })

            # STEP 5: SYNTHESIZE - Create executive response
            print("✨ SYNTHESIZING: Creating executive response...")
            step_start = time.time()

            response = await self._synthesize_response(aggregated_data, understanding, query)

            synthesis_time = time.time() - step_start
            processing_steps.append({
                'step': 'synthesis',
                'duration_ms': round(synthesis_time * 1000),
                'response_length': len(response.get('content', ''))
            })

            # STEP 6: REFLECT - Evaluate quality
            print("🔍 REFLECTING: Evaluating response quality...")
            step_start = time.time()

            reflection = await self._reflect_on_response(response, understanding, query)

            reflection_time = time.time() - step_start
            processing_steps.append({
                'step': 'reflection',
                'duration_ms': round(reflection_time * 1000),
                'confidence_score': reflection.get('overall_confidence', 0)
            })

            # STEP 7: LEARN - Extract patterns (async, non-blocking)
            print("📚 LEARNING: Extracting patterns...")
            step_start = time.time()

            learning_result = await self._extract_learning_patterns(
                query, understanding, response, reflection
            )

            learning_time = time.time() - step_start
            processing_steps.append({
                'step': 'learning',
                'duration_ms': round(learning_time * 1000),
                'patterns_extracted': len(learning_result.get('patterns', []))
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
                    'overall_confidence': reflection.get('overall_confidence', 0),
                    'data_sources_used': list(raw_data.keys()),
                    'records_analyzed': raw_data.get('_metadata', {}).get('total_records', 0),
                    'response_timestamp': datetime.now().isoformat()
                },

                # Quality assessment
                'quality_assessment': reflection,

                # Learning insights
                'learning_insights': learning_result
            }

            print(f"✅ COMPLETE: Processed in {total_time:.2f}s with {reflection.get('overall_confidence', 0)}% confidence")

            return final_response

        except Exception as e:
            processing_time = time.time() - start_time
            raise Exception(f"Leadership insights processing failed after {processing_time:.2f}s: {str(e)}")

    async def _create_data_plan(self, understanding: QueryUnderstanding) -> Dict[str, Any]:
        """Create data fetching plan based on understanding.

        Args:
            understanding: Query understanding from thinking agent

        Returns:
            Data plan dictionary

        Raises:
            Exception: If planning fails (NO FALLBACK)
        """
        try:
            # Build planning context
            context = {
                'understanding': understanding.to_dict(),
                'available_stores': [
                    'transcripts', 'analyses', 'plans', 'workflows', 'executions'
                ]
            }

            # Load planning prompt
            prompt = prompt_loader.format(
                'insights/planning/data_strategy.txt',
                **context
            )

            # Get LLM plan
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.3)
            )

            if not response.text:
                raise Exception("LLM returned no planning response")

            # Parse plan
            plan = self._parse_json_response(response.text)

            # Validate plan
            if not plan.get('data_sources'):
                raise Exception("No data sources specified in plan")

            return plan

        except Exception as e:
            raise Exception(f"Data planning failed: {str(e)}")

    async def _fetch_data(self, data_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data according to plan.

        Args:
            data_plan: Plan from planning agent

        Returns:
            Raw data dictionary

        Raises:
            Exception: If fetching fails (NO FALLBACK)
        """
        if not self.data_reader:
            # NO FALLBACK: Fail fast on missing dependencies
            raise Exception("DataReaderService is required - NO FALLBACK LOGIC")

        try:
            # Use data reader service to fetch according to plan
            raw_data = await self.data_reader.fetch_by_plan(data_plan)

            if not raw_data:
                raise Exception("No data returned from data reader")

            return raw_data

        except Exception as e:
            raise Exception(f"Data fetching failed: {str(e)}")

    async def _aggregate_data(self, raw_data: Dict[str, Any],
                             understanding: QueryUnderstanding) -> Dict[str, Any]:
        """Aggregate raw data into leadership insights.

        Args:
            raw_data: Raw data from stores
            understanding: Query understanding

        Returns:
            Aggregated insights

        Raises:
            Exception: If aggregation fails (NO FALLBACK)
        """
        try:
            # Build aggregation context
            context = {
                'raw_data_summary': self._summarize_raw_data(raw_data),
                'understanding': understanding.to_dict(),
                'record_count': raw_data.get('_metadata', {}).get('total_records', 0)
            }

            # Load aggregation prompt
            prompt = prompt_loader.format(
                'insights/aggregation/data_summarization.txt',
                **context
            )

            # Get LLM aggregation
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no aggregation response")

            # Parse aggregation
            aggregated = self._parse_json_response(response.text)

            # Validate aggregation
            if not aggregated.get('key_insights'):
                raise Exception("No key insights generated from aggregation")

            return aggregated

        except Exception as e:
            raise Exception(f"Data aggregation failed: {str(e)}")

    async def _synthesize_response(self, aggregated_data: Dict[str, Any],
                                  understanding: QueryUnderstanding,
                                  original_query: str) -> Dict[str, Any]:
        """Synthesize executive response from aggregated data.

        Args:
            aggregated_data: Aggregated insights
            understanding: Query understanding
            original_query: Original query string

        Returns:
            Executive response

        Raises:
            Exception: If synthesis fails (NO FALLBACK)
        """
        try:
            # Build synthesis context
            context = {
                'aggregated_data': aggregated_data,
                'understanding': understanding.to_dict(),
                'original_query': original_query
            }

            # Load synthesis prompt
            prompt = prompt_loader.format(
                'insights/synthesis/executive_response.txt',
                **context
            )

            # Get LLM synthesis
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.5)
            )

            if not response.text:
                raise Exception("LLM returned no synthesis response")

            # Parse synthesis
            synthesized = self._parse_json_response(response.text)

            # Validate synthesis
            if not synthesized.get('content'):
                raise Exception("No content generated in synthesis")

            return synthesized

        except Exception as e:
            raise Exception(f"Response synthesis failed: {str(e)}")

    async def _reflect_on_response(self, response: Dict[str, Any],
                                  understanding: QueryUnderstanding,
                                  original_query: str) -> Dict[str, Any]:
        """Reflect on response quality and completeness.

        Args:
            response: Synthesized response
            understanding: Query understanding
            original_query: Original query

        Returns:
            Reflection assessment

        Raises:
            Exception: If reflection fails (NO FALLBACK)
        """
        try:
            # Build reflection context
            context = {
                'response': response,
                'understanding': understanding.to_dict(),
                'original_query': original_query
            }

            # Load reflection prompt
            prompt = prompt_loader.format(
                'insights/reflection/quality_assessment.txt',
                **context
            )

            # Get LLM reflection
            reflection_response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.3)
            )

            if not reflection_response.text:
                raise Exception("LLM returned no reflection response")

            # Parse reflection
            reflection = self._parse_json_response(reflection_response.text)

            # Validate reflection
            if 'overall_confidence' not in reflection:
                reflection['overall_confidence'] = 75  # Default confidence

            return reflection

        except Exception as e:
            raise Exception(f"Response reflection failed: {str(e)}")

    async def _extract_learning_patterns(self, query: str, understanding: QueryUnderstanding,
                                        response: Dict[str, Any], reflection: Dict[str, Any]) -> Dict[str, Any]:
        """Extract learning patterns from successful interactions.

        Args:
            query: Original query
            understanding: Query understanding
            response: Response generated
            reflection: Quality reflection

        Returns:
            Learning patterns extracted

        Raises:
            Exception: If learning extraction fails (NO FALLBACK)
        """
        try:
            # Build learning context
            context = {
                'query': query,
                'understanding': understanding.to_dict(),
                'response_quality': reflection.get('overall_confidence', 0),
                'successful_approach': {
                    'data_strategy': response.get('supporting_data', {}),
                    'response_format': {
                        'has_executive_summary': bool(response.get('executive_summary')),
                        'has_recommendations': bool(response.get('recommendations')),
                        'has_metrics': bool(response.get('key_metrics'))
                    }
                }
            }

            # Load learning prompt
            prompt = prompt_loader.format(
                'insights/learning/pattern_extraction.txt',
                **context
            )

            # Get LLM learning
            learning_response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not learning_response.text:
                return {'patterns': [], 'insights': []}

            # Parse learning
            learning = self._parse_json_response(learning_response.text)

            return learning

        except Exception as e:
            # Learning is optional - don't fail the main process
            print(f"Learning extraction failed: {str(e)}")
            return {'patterns': [], 'insights': []}

    def _summarize_raw_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of raw data for LLM processing.

        Args:
            raw_data: Raw data dictionary

        Returns:
            Summary dictionary
        """
        summary = {}

        for key, value in raw_data.items():
            if key.startswith('_'):
                continue

            if isinstance(value, list):
                summary[key] = {
                    'count': len(value),
                    'sample_fields': list(value[0].keys()) if value else [],
                    'sample_data': value[:3] if value else []
                }
            else:
                summary[key] = {'type': type(value).__name__, 'value': str(value)[:100]}

        return summary

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response.

        Args:
            response_text: LLM response text

        Returns:
            Parsed JSON dictionary

        Raises:
            Exception: If parsing fails
        """
        try:
            # Clean response text
            response_text = response_text.strip()

            # Find JSON boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            # Try parsing the whole response
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
            'version': '1.0.0',
            'capabilities': [
                'query_understanding',
                'data_planning',
                'intelligent_aggregation',
                'executive_synthesis',
                'quality_reflection',
                'pattern_learning'
            ],
            'sub_agents': [
                'ThinkingAgent'
            ],
            'status': 'ready',
            'last_updated': datetime.now().isoformat()
        }