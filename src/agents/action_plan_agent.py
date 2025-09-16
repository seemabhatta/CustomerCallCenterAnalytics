"""Four-layer action plan generator for mortgage servicing."""
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from src.models.transcript import Transcript
from src.utils.prompt_loader import prompt_loader
from src.llm.openai_wrapper import OpenAIWrapper
from src.agents.models.action_plan_models import FourLayerActionPlan

load_dotenv()


class ActionPlanAgent:
    """Agent for generating four-layer action plans from analysis and transcript data.

    Follows architecture principles:
    - Pure Python business logic (no UI dependencies)
    - Uses OpenAI Responses API with structured output
    - Generates structured action plans for four layers
    """
    
    def __init__(self):
        """Initialize the action plan agent."""
        self.llm = OpenAIWrapper()
    
    def generate(self, analysis: Dict[str, Any], transcript: Transcript) -> Dict[str, Any]:
        """Generate four-layer action plans from analysis and transcript.
        
        Args:
            analysis: Analysis results from call_analyzer
            transcript: Original transcript object
            
        Returns:
            Dictionary containing four layer action plans
        """
        # Extract contextual information from transcript and analysis
        context = self._extract_context(transcript, analysis)

        # Build comprehensive prompt for action plan generation
        prompt = self._build_prompt(context)

        try:
            # Use OpenAI wrapper with structured output
            action_plan_result = self.llm.generate_structured(
                prompt=prompt,
                schema_model=FourLayerActionPlan,
                temperature=0.3
            )

            # Convert to dict and add metadata
            action_plans = action_plan_result.model_dump()
            action_plans['plan_id'] = str(uuid.uuid4())
            action_plans['analysis_id'] = analysis.get('analysis_id')
            action_plans['transcript_id'] = transcript.id
            action_plans['generator_version'] = "1.0"

            return action_plans

        except Exception as e:
            raise Exception(f"Action plan generation failed: {str(e)}")
    
    def _extract_context(self, transcript: Transcript, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant context from transcript and analysis for action planning.
        
        Args:
            transcript: Transcript object
            analysis: Analysis results
            
        Returns:
            Context dictionary with extracted information
        """
        # Type validation to catch the bug early
        if not isinstance(analysis, dict):
            raise TypeError(f"Expected analysis to be Dict[str, Any], got {type(analysis)}. Value: {repr(analysis)[:200]}...")
        
        context = {}
        
        # Add COMPLETE conversation for maximum context
        context['full_conversation'] = []
        for message in transcript.messages:
            context['full_conversation'].append({
                'speaker': getattr(message, 'speaker', 'Unknown'),
                'text': getattr(message, 'text', ''),
                'timestamp': getattr(message, 'timestamp', None)
            })
        
        # Add transcript metadata
        context['call_duration'] = getattr(transcript, 'duration', 0)
        context['call_topic'] = getattr(transcript, 'topic', 'Unknown')
        context['customer_id'] = getattr(transcript, 'customer_id', 'Unknown')
        
        # Add all analysis data
        context['analysis'] = analysis
        
        # No hardcoded extraction - let LLM analyze the full conversation
        # These fields are kept for compatibility but will be empty
        context['promises_made'] = []
        context['timeline_commitments'] = []
        context['customer_concerns'] = []
        context['next_steps_mentioned'] = []
        
        # Extract structured insights from analysis
        context['primary_intent'] = analysis.get('primary_intent', '')
        context['urgency_level'] = analysis.get('urgency_level', '')
        context['borrower_risks'] = analysis.get('borrower_risks', {})
        context['advisor_metrics'] = analysis.get('advisor_metrics', {})
        context['compliance_flags'] = analysis.get('compliance_flags', [])
        context['topics_discussed'] = analysis.get('topics_discussed', [])
        context['resolution_status'] = {
            'resolved': analysis.get('issue_resolved', False),
            'first_call_resolution': analysis.get('first_call_resolution', False),
            'escalation_needed': analysis.get('escalation_needed', False)
        }
        context['confidence_score'] = analysis.get('confidence_score', 0)
        
        # Customer and call metadata
        context['customer_id'] = getattr(transcript, 'customer_id', '')
        context['advisor_id'] = getattr(transcript, 'advisor_id', '')
        context['call_sentiment'] = getattr(transcript, 'sentiment', '')
        
        return context
    
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for action plan generation.
        
        Args:
            context: Extracted context information
            
        Returns:
            Formatted prompt for OpenAI
        """
        # Format full conversation
        conversation_text = "\n".join([
            f"{msg['speaker']}: {msg['text']}"
            for msg in context['full_conversation']
        ])
        
        # Get analysis details
        analysis = context['analysis']
        
        return prompt_loader.format(
            'agents/action_plan.txt',
            conversation_text=conversation_text,
            call_duration=context['call_duration'],
            call_topic=context['call_topic'],
            customer_id=context['customer_id'],
            primary_intent=analysis.get('primary_intent', 'Unknown'),
            sentiment=analysis.get('sentiment', 'Unknown'),
            urgency_level=analysis.get('urgency_level', 'Unknown'),
            risk_score=analysis.get('risk_score', 0),
            compliance_flags=', '.join(analysis.get('compliance_flags', [])),
            borrower_risks=json.dumps(analysis.get('borrower_risks', {}), indent=2),
            advisor_performance=json.dumps(analysis.get('advisor_performance', {}), indent=2),
            promises_made=', '.join(context['promises_made']),
            customer_concerns=', '.join(context['customer_concerns']),
            timeline_commitments=', '.join(context['timeline_commitments']),
            next_steps_mentioned=', '.join(context['next_steps_mentioned'])
        )
    
    
