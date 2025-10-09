"""
Core GenAI insight generation engine.

This module uses LLMs to analyze data and generate natural language insights,
recommendations, and actionable intelligence for different personas.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from src.infrastructure.llm.llm_client_v2 import LLMClientV2, RequestOptions
from .prompt_loader import PromptLoader


class InsightGenerator:
    """
    Core GenAI engine for generating insights.

    Uses LLMs to transform raw data and forecasts into actionable
    business intelligence with natural language explanations.
    """

    def __init__(
        self,
        llm_client: Optional[LLMClientV2] = None,
        prompts_dir: str = "prompts"
    ):
        """
        Initialize the insight generator.

        Args:
            llm_client: LLM client for generating insights (creates default if None)
            prompts_dir: Directory containing prompt templates
        """
        self.llm_client = llm_client or LLMClientV2()
        self.prompt_loader = PromptLoader(prompts_dir)

    async def generate(
        self,
        prompt_name: str,
        context: Dict[str, Any],
        system_instructions: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        Generate an insight using LLM.

        Args:
            prompt_name: Name of prompt template to use
            context: Context data to pass to the prompt
            system_instructions: Optional system instructions
            temperature: LLM temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Dict containing insight data plus metadata

        Raises:
            Exception if LLM generation fails (fail fast, no fallback)
        """
        start_time = time.time()

        try:
            # Load and format prompt
            prompt = self.prompt_loader.load(prompt_name, context)

            # Prepare LLM options
            options = RequestOptions(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Invoke the LLM asynchronously
            response = await self.llm_client.arun(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_instructions,
                options=options,
            )

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Try to parse as JSON if response looks like JSON
            raw_text = response.require_text()
            insight_data = self._parse_response(raw_text)

            # Add metadata
            result = {
                'insight': insight_data,
                'metadata': {
                    'prompt_name': prompt_name,
                    'generated_at': datetime.utcnow().isoformat(),
                    'generation_time_ms': generation_time_ms,
                    'temperature': temperature,
                    'max_tokens': max_tokens
                }
            }

            return result

        except Exception as e:
            # Fail fast - no fallback logic per CLAUDE.md
            raise Exception(f"Insight generation failed for '{prompt_name}': {str(e)}")

    def _parse_response(self, response: str) -> Any:
        """
        Attempt to parse LLM response as JSON, fallback to plain text.

        Args:
            response: LLM response string

        Returns:
            Parsed JSON dict or original string
        """
        response = response.strip()

        # Try to extract JSON from markdown code blocks
        if '```json' in response:
            json_match = response.split('```json')[1].split('```')[0].strip()
            try:
                return json.loads(json_match)
            except json.JSONDecodeError:
                pass

        # Try direct JSON parse
        if response.startswith('{') or response.startswith('['):
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

        # Return as plain text
        return {'text': response}

    async def generate_structured(
        self,
        prompt_name: str,
        context: Dict[str, Any],
        schema: Dict[str, Any],
        system_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate insight with structured JSON output.

        Args:
            prompt_name: Name of prompt template
            context: Context data
            schema: Expected JSON schema
            system_instructions: Optional system instructions

        Returns:
            Structured insight data conforming to schema
        """
        # Add schema instruction to prompt
        schema_instruction = f"\n\nIMPORTANT: Return your response as JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        full_system = (system_instructions or "") + schema_instruction

        result = await self.generate(
            prompt_name=prompt_name,
            context=context,
            system_instructions=full_system,
            temperature=0.3  # Lower temperature for structured output
        )

        # Validate against schema (basic validation)
        insight = result['insight']
        if isinstance(insight, dict):
            # Check if required keys from schema exist
            if 'properties' in schema:
                required = schema.get('required', [])
                for key in required:
                    if key not in insight:
                        raise ValueError(f"Missing required field '{key}' in LLM response")

        return result

    async def batch_generate(
        self,
        prompts: List[Dict[str, Any]],
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple insights.

        Args:
            prompts: List of prompt configurations, each with:
                     {prompt_name, context, system_instructions?, temperature?}
            parallel: Whether to generate in parallel (future enhancement)

        Returns:
            List of insight results
        """
        results = []

        for prompt_config in prompts:
            try:
                result = await self.generate(**prompt_config)
                results.append({
                    'success': True,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'prompt_name': prompt_config.get('prompt_name')
                })

        return results

    async def explain_data(
        self,
        data: Any,
        question: str,
        context: Optional[str] = None
    ) -> str:
        """
        Natural language explanation of data.

        Args:
            data: Data to explain (dict, list, number, etc.)
            question: Question to answer about the data
            context: Optional context about the data

        Returns:
            Natural language explanation
        """
        prompt = f"""You are a mortgage servicing data analyst.

Data:
{json.dumps(data, indent=2) if isinstance(data, (dict, list)) else data}

{f'Context: {context}' if context else ''}

Question: {question}

Provide a clear, concise explanation in natural language.
Focus on actionable insights for mortgage servicing leadership."""

        response = await self.llm_client.arun(
            messages=[{"role": "user", "content": prompt}],
            options=RequestOptions(temperature=0.5)
        )
        return response.require_text().strip()

    async def summarize_forecast(
        self,
        forecast: Dict[str, Any],
        audience: str = "leadership"
    ) -> str:
        """
        Create natural language summary of a forecast.

        Args:
            forecast: Forecast data from Prophet service
            audience: Target audience (leadership, operations, marketing)

        Returns:
            Natural language summary
        """
        context = {
            'forecast': forecast,
            'audience': audience,
            'date': datetime.utcnow().strftime('%Y-%m-%d')
        }

        result = await self.generate(
            prompt_name='forecast_summary',
            context=context,
            temperature=0.6
        )

        # Extract text from result
        insight = result['insight']
        if isinstance(insight, dict) and 'text' in insight:
            return insight['text']
        elif isinstance(insight, dict) and 'summary' in insight:
            return insight['summary']
        elif isinstance(insight, str):
            return insight
        else:
            return json.dumps(insight)
