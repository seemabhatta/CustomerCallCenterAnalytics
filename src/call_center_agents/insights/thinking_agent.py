"""Thinking Agent for Leadership Insights.

Core Principles Applied:
- NO FALLBACK: Fail fast on unclear queries or missing context
- AGENTIC: LLM makes all understanding and classification decisions
- REASONING: Chain-of-thought for query understanding
"""
from typing import Dict, Any, Optional
import json

from ...infrastructure.llm.llm_client_v2 import LLMClientV2, RequestSpec, RequestOptions
from ...infrastructure.telemetry import set_span_attributes, add_span_event
from ...utils.prompt_loader import prompt_loader


class QueryUnderstanding:
    """Structured output for query understanding."""

    def __init__(self, data: Dict[str, Any]):
        self.core_intent = data.get('core_intent')
        self.focus_area = data.get('focus_area')
        self.urgency = data.get('urgency')
        self.scope = data.get('scope')
        self.time_frame = data.get('time_frame')
        self.depth_required = data.get('depth_required')
        self.executive_context = data.get('executive_context')
        self.reasoning = data.get('reasoning')
        self.confidence = data.get('confidence', 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'core_intent': self.core_intent,
            'focus_area': self.focus_area,
            'urgency': self.urgency,
            'scope': self.scope,
            'time_frame': self.time_frame,
            'depth_required': self.depth_required,
            'executive_context': self.executive_context,
            'reasoning': self.reasoning,
            'confidence': self.confidence
        }


class ThinkingAgent:
    """Agent responsible for query understanding and reasoning.

    Uses LLM to understand what leadership is really asking,
    classify the query across multiple dimensions, and reason
    about the best approach to answer.
    """

    def __init__(self, llm_client: LLMClientV2):
        """Initialize thinking agent.

        Args:
            llm_client: LLM client for reasoning

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not llm_client:
            raise ValueError("llm_client cannot be None")

        self.llm = llm_client

    async def understand_query(self, query: str, executive_role: str = None,
                              session_context: Dict[str, Any] = None) -> QueryUnderstanding:
        """Understand leadership query through reasoning.

        Args:
            query: Leadership query string
            executive_role: Role of the executive asking
            session_context: Previous conversation context

        Returns:
            QueryUnderstanding object

        Raises:
            Exception: If understanding fails (NO FALLBACK)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Build context for reasoning
            context = {
                'query': query.strip(),
                'executive_role': executive_role or 'Unknown',
                'session_context': session_context or {},
                'has_context': bool(session_context and session_context.get('focus_area'))
            }

            # Load thinking prompt
            prompt = prompt_loader.format(
                'insights/thinking/query_understanding.txt',
                **context
            )

            # Get LLM reasoning
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.3)
            )

            # Parse response
            if not response.text:
                raise Exception("LLM returned no response")

            understanding_data = self._parse_understanding_response(response.text)
            understanding = QueryUnderstanding(understanding_data)

            # Handle low confidence gracefully (chatbot behavior)
            if understanding.confidence < 50:
                # Low confidence, but continue processing
                # The downstream agents will handle it appropriately
                set_span_attributes(
                    low_confidence=True,
                    confidence_level=understanding.confidence
                )

                # Add event for low confidence
                add_span_event("thinking.low_confidence_warning",
                               confidence=understanding.confidence,
                               query=query[:100])  # First 100 chars of query

            return understanding

        except Exception as e:
            raise Exception(f"Query understanding failed: {str(e)}")

    async def classify_intent(self, query: str) -> Dict[str, Any]:
        """Classify query intent for routing decisions.

        Args:
            query: Query string

        Returns:
            Intent classification

        Raises:
            Exception: If classification fails (NO FALLBACK)
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Load classification prompt
            prompt = prompt_loader.format(
                'insights/thinking/intent_classification.txt',
                query=query.strip()
            )

            # Get LLM classification
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.2)
            )

            if not response.text:
                raise Exception("LLM returned no response")

            classification = self._parse_classification_response(response.text)

            # Validate classification
            if not classification.get('primary_intent'):
                raise Exception("No primary intent identified")

            return classification

        except Exception as e:
            raise Exception(f"Intent classification failed: {str(e)}")

    async def reason_about_approach(self, understanding: QueryUnderstanding,
                                   available_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Reason about the best approach to answer the query.

        Args:
            understanding: Query understanding
            available_data: Summary of available data

        Returns:
            Reasoning about approach

        Raises:
            Exception: If reasoning fails (NO FALLBACK)
        """
        if not understanding:
            raise ValueError("understanding cannot be None")

        try:
            # Build reasoning context
            context = {
                'understanding': understanding.to_dict(),
                'available_data': available_data or {},
                'has_data_info': bool(available_data)
            }

            # Load reasoning prompt
            prompt = prompt_loader.format(
                'insights/thinking/approach_reasoning.txt',
                **context
            )

            # Get LLM reasoning
            response = await self.llm.arun(
                messages=[{"role": "user", "content": prompt}],
                options=RequestOptions(temperature=0.4)
            )

            if not response.text:
                raise Exception("LLM returned no response")

            reasoning = self._parse_reasoning_response(response.text)

            # Validate reasoning
            if not reasoning.get('recommended_approach'):
                raise Exception("No approach recommendation provided")

            return reasoning

        except Exception as e:
            raise Exception(f"Approach reasoning failed: {str(e)}")

    def _parse_understanding_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for understanding.

        Args:
            response_text: LLM response

        Returns:
            Parsed understanding data
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

            # Fallback: parse structured text
            return self._parse_structured_text(response_text)

        except json.JSONDecodeError:
            # Fallback: parse structured text
            return self._parse_structured_text(response_text)

    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for classification.

        Args:
            response_text: LLM response

        Returns:
            Parsed classification data
        """
        try:
            # Try JSON parsing first
            response_text = response_text.strip()
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            # Fallback parsing
            return self._parse_structured_text(response_text)

        except json.JSONDecodeError:
            return self._parse_structured_text(response_text)

    def _parse_reasoning_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response for reasoning.

        Args:
            response_text: LLM response

        Returns:
            Parsed reasoning data
        """
        try:
            # Try JSON parsing first
            response_text = response_text.strip()
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)

            # Fallback parsing
            return self._parse_structured_text(response_text)

        except json.JSONDecodeError:
            return self._parse_structured_text(response_text)

    def _parse_structured_text(self, text: str) -> Dict[str, Any]:
        """Parse structured text response.

        Args:
            text: Structured text

        Returns:
            Parsed data dictionary
        """
        # Simple fallback parser for non-JSON responses
        result = {}
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()

                # Try to parse value
                if value.lower() in ['true', 'false']:
                    result[key] = value.lower() == 'true'
                elif value.isdigit():
                    result[key] = int(value)
                else:
                    result[key] = value

        # Ensure required fields have defaults
        result.setdefault('confidence', 75)
        result.setdefault('core_intent', 'general_inquiry')
        result.setdefault('focus_area', 'operational')

        return result