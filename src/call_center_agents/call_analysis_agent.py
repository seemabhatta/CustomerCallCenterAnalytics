"""Post-call intelligence analyzer for mortgage servicing."""
import uuid
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from src.models.transcript import Transcript
from src.utils.prompt_loader import prompt_loader
from src.infrastructure.llm.openai_wrapper import OpenAIWrapper
from src.call_center_agents.models.call_models import CallAnalysis

load_dotenv()


class CallAnalysisAgent:
    """Mortgage servicing call analysis agent using OpenAI Responses API."""
    
    def __init__(self):
        """Initialize the analyzer."""
        self.llm = OpenAIWrapper()
    
    def analyze(self, transcript: Transcript, pattern_insights: List[str] = None) -> Dict[str, Any]:
        """Analyze a transcript for mortgage servicing insights.

        Args:
            transcript: Transcript to analyze
            pattern_insights: Optional list of relevant patterns to inform analysis

        Returns:
            Analysis results with mortgage-specific insights
        """
        try:
            # Build transcript text for analysis
            transcript_text = self._build_transcript_text(transcript)

            # Format pattern insights for LLM context
            pattern_context = "No specific patterns found for this interaction context."
            if pattern_insights:
                pattern_context = ""
                for i, pattern in enumerate(pattern_insights, 1):
                    pattern_context += f"{i}. {pattern}\n"
                pattern_context = pattern_context.strip()

            # Create analysis prompt using external template with pattern context
            prompt = prompt_loader.format(
                'agents/call_analysis.txt',
                transcript_text=transcript_text,
                pattern_context=pattern_context,
                customer_id=getattr(transcript, 'customer_id', 'N/A'),
                advisor_id=getattr(transcript, 'advisor_id', 'N/A'),
                duration=getattr(transcript, 'duration', 'N/A')
            )

            # Use OpenAI wrapper with structured output
            analysis_result = self.llm.generate_structured(
                prompt=prompt,
                schema_model=CallAnalysis,
                temperature=0.3
            )

            # Convert to dict and add metadata
            analysis = analysis_result.model_dump()
            analysis['transcript_id'] = transcript.id
            analysis['analysis_id'] = str(uuid.uuid4())
            analysis['analyzer_version'] = "1.0"

            # NO FALLBACK: Validate predictive insight generation
            # LLM should generate meaningful insights, not null/empty objects
            predictive_insight = analysis.get('predictive_insight')

            if predictive_insight is None:
                # NO FALLBACK: If LLM doesn't generate insight, fail the analysis
                raise ValueError("LLM failed to generate required predictive_insight - analysis incomplete")

            # Validate insight content is meaningful
            if not self._validate_predictive_insight(predictive_insight):
                # NO FALLBACK: If insight is invalid/empty, fail the analysis
                raise ValueError("LLM generated invalid predictive_insight - analysis incomplete")

            return analysis

        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
    
    def _build_transcript_text(self, transcript: Transcript) -> str:
        """Convert transcript to text format for analysis.
        
        Args:
            transcript: Transcript object
            
        Returns:
            Formatted transcript text
        """
        lines = []
        
        # Add metadata if available
        if hasattr(transcript, 'timestamp'):
            lines.append(f"Call Date: {transcript.timestamp}")
        if hasattr(transcript, 'topic'):
            lines.append(f"Topic: {transcript.topic}")
        
        lines.append("")  # Empty line separator
        
        # Add conversation
        for message in transcript.messages:
            timestamp = getattr(message, 'timestamp', '')
            timestamp_str = f" ({timestamp})" if timestamp else ""
            lines.append(f"{message.speaker}{timestamp_str}: {message.text}")
        
        return "\n".join(lines)

    def _validate_predictive_insight(self, insight: Dict[str, Any]) -> bool:
        """Validate that predictive insight contains meaningful content.

        Args:
            insight: PredictiveInsight dictionary from LLM

        Returns:
            True if insight is valid and meaningful
        """
        if not isinstance(insight, dict):
            return False

        # Required fields must be present and non-empty
        required_fields = ['insight_type', 'priority', 'content', 'reasoning', 'learning_value']
        for field in required_fields:
            if field not in insight or not insight[field] or str(insight[field]).strip() == '':
                return False

        # Insight type must be valid (case-insensitive)
        valid_types = ['pattern', 'prediction', 'wisdom', 'meta_learning']
        if insight['insight_type'].lower() not in valid_types:
            return False

        # Priority must be valid (case-insensitive)
        valid_priorities = ['high', 'medium', 'low']
        if insight['priority'].lower() not in valid_priorities:
            return False

        # Learning value must be valid (case-insensitive)
        valid_learning_values = ['critical', 'exceptional', 'routine']
        if insight['learning_value'].lower() not in valid_learning_values:
            return False

        # Content must be a structured object with required fields
        content = insight['content']
        if not isinstance(content, dict):
            return False

        # Validate structured content fields
        content_required_fields = ['key', 'value', 'confidence', 'impact']
        for field in content_required_fields:
            if field not in content or not content[field] or str(content[field]).strip() == '':
                return False

        # Confidence must be a valid float between 0 and 1
        try:
            confidence = float(content['confidence'])
            if not (0.0 <= confidence <= 1.0):
                return False
        except (ValueError, TypeError):
            return False

        # Validate customer context structure
        customer_context = insight.get('customer_context')
        if not isinstance(customer_context, dict):
            return False

        # Validate customer context fields
        context_required_fields = ['customer_id', 'loan_type', 'tenure', 'risk_profile']
        for field in context_required_fields:
            if field not in customer_context or not customer_context[field] or str(customer_context[field]).strip() == '':
                return False

        # Reasoning must be meaningful (at least 10 characters)
        reasoning = str(insight['reasoning']).strip()
        if len(reasoning) < 10:
            return False

        return True
