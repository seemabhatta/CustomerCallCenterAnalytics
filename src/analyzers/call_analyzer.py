"""Post-call intelligence analyzer for mortgage servicing."""
import os
import uuid
import json
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv

from src.models.transcript import Transcript

load_dotenv()


class CallAnalyzer:
    """Mortgage servicing call analyzer using OpenAI Responses API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def analyze(self, transcript: Transcript) -> Dict[str, Any]:
        """Analyze a transcript for mortgage servicing insights.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            Analysis results with mortgage-specific insights
        """
        # Build transcript text for analysis
        transcript_text = self._build_transcript_text(transcript)
        
        # Define the structured output schema aligned with mortgage servicing vision
        # Note: For the Responses API, structured outputs are configured via
        # `text={"format": {"type": "json_schema", ...}}`.
        schema_properties = {
            # Core Analysis
            "call_summary": {"type": "string"},
            "primary_intent": {"type": "string"},  # refinance, hardship, payment, escrow, PMI
            "urgency_level": {"type": "string"},   # high, medium, low

            # Borrower Insights
            "borrower_sentiment": {
                "type": "object",
                "properties": {
                    "overall": {"type": "string"},
                    "start": {"type": "string"},
                    "end": {"type": "string"},
                    "trend": {"type": "string"}  # improving, declining, stable
                },
                "required": ["overall", "start", "end", "trend"],
                "additionalProperties": False
            },
            "borrower_risks": {
                "type": "object",
                "properties": {
                    "delinquency_risk": {"type": "number", "minimum": 0, "maximum": 1},
                    "churn_risk": {"type": "number", "minimum": 0, "maximum": 1},
                    "complaint_risk": {"type": "number", "minimum": 0, "maximum": 1},
                    "refinance_likelihood": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["delinquency_risk", "churn_risk", "complaint_risk", "refinance_likelihood"],
                "additionalProperties": False
            },

            # Advisor Performance
            "advisor_metrics": {
                "type": "object",
                "properties": {
                    "empathy_score": {"type": "number", "minimum": 0, "maximum": 10},
                    "compliance_adherence": {"type": "number", "minimum": 0, "maximum": 10},
                    "solution_effectiveness": {"type": "number", "minimum": 0, "maximum": 10},
                    "coaching_opportunities": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["empathy_score", "compliance_adherence", "solution_effectiveness", "coaching_opportunities"],
                "additionalProperties": False
            },

            # Compliance & Risk
            "compliance_flags": {"type": "array", "items": {"type": "string"}},
            "required_disclosures": {"type": "array", "items": {"type": "string"}},

            # Resolution
            "issue_resolved": {"type": "boolean"},
            "first_call_resolution": {"type": "boolean"},
            "escalation_needed": {"type": "boolean"},

            # Key Topics & Metadata
            "topics_discussed": {"type": "array", "items": {"type": "string"}},
            "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},

            # Mortgage-Specific Insights
            "product_opportunities": {"type": "array", "items": {"type": "string"}},
            "payment_concerns": {"type": "array", "items": {"type": "string"}},
            "property_related_issues": {"type": "array", "items": {"type": "string"}},
        }

        schema = {
            "type": "object",
            "properties": schema_properties,
            "required": [
                "call_summary", "primary_intent", "urgency_level", "borrower_sentiment",
                "borrower_risks", "advisor_metrics", "compliance_flags", "required_disclosures",
                "issue_resolved", "first_call_resolution", "escalation_needed",
                "topics_discussed", "confidence_score", "product_opportunities",
                "payment_concerns", "property_related_issues"
            ],
            "additionalProperties": False,
        }

        text_format = {
            "type": "json_schema",
            "name": "MortgageCallAnalysis",
            "strict": True,
            "schema": schema,
        }
        
        # Create analysis prompt
        prompt = f"""
        Analyze this mortgage servicing call transcript and provide comprehensive insights.
        
        Focus on:
        - Borrower's primary intent and emotional journey
        - Risk indicators (delinquency, churn, complaints)
        - Advisor's performance and coaching opportunities
        - Compliance requirements and potential issues
        - Mortgage-specific topics (PMI, escrow, refinancing, hardship)
        - Resolution effectiveness and next steps needed
        
        Transcript:
        {transcript_text}
        
        Customer ID: {getattr(transcript, 'customer_id', 'N/A')}
        Advisor ID: {getattr(transcript, 'advisor_id', 'N/A')}
        Call Duration: {getattr(transcript, 'duration', 'N/A')} seconds
        """
        
        try:
            # Use OpenAI Responses API for structured analysis
            response = self.client.responses.create(
                model="gpt-4.1",
                input=prompt,
                text={"format": text_format},
                temperature=0.3  # Lower temperature for consistent analysis
            )

            # Robust extraction of structured output across SDK variants
            analysis: Optional[Dict[str, Any]] = None

            # Preferred: output_parsed when available
            if hasattr(response, "output_parsed"):
                analysis = getattr(response, "output_parsed")  # type: ignore

            # Try nested response.output -> content[0].parsed/text
            if analysis is None and hasattr(response, "output"):
                try:
                    out = getattr(response, "output")
                    if isinstance(out, list) and out:
                        content = getattr(out[0], "content", None)
                        if isinstance(content, list) and content:
                            item = content[0]
                            # Some SDKs expose a parsed field for structured outputs
                            if hasattr(item, "parsed") and getattr(item, "parsed"):
                                analysis = getattr(item, "parsed")
                            elif hasattr(item, "text") and getattr(item, "text"):
                                # If text contains JSON, parse it
                                text_val = getattr(item, "text")
                                try:
                                    maybe_json = json.loads(text_val)
                                    if isinstance(maybe_json, dict):
                                        analysis = maybe_json
                                except Exception:
                                    pass
                except Exception:
                    pass

            if analysis is None:
                raise AttributeError("Could not extract structured analysis from response")

            # Add metadata
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
