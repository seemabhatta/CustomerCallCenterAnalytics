"""Post-call intelligence analyzer for mortgage servicing."""
import uuid
from typing import Dict, Any, Optional
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
    
    def analyze(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze a transcript for mortgage servicing insights.

        Args:
            transcript: Transcript to analyze

        Returns:
            Analysis results with mortgage-specific insights
        """
        try:
            # Build transcript text for analysis
            transcript_text = self._build_transcript_text(transcript)

            # Create analysis prompt using external template
            prompt = prompt_loader.format(
                'agents/call_analysis.txt',
                transcript_text=transcript_text,
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
