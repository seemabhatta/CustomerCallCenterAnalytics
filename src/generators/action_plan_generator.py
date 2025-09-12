"""Four-layer action plan generator for mortgage servicing."""
import os
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from dotenv import load_dotenv

from src.models.transcript import Transcript

load_dotenv()


class ActionPlanGenerator:
    """Generate four-layer action plans from analysis and transcript data.
    
    Follows architecture principles:
    - Pure Python business logic (no UI dependencies)
    - Uses OpenAI Responses API with structured output
    - Generates structured action plans for four layers
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the action plan generator.
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
        """
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
    
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
        
        # Define structured output schema for four layers
        action_plan_schema = self._get_action_plan_schema()
        
        try:
            # Use OpenAI Responses API for structured output
            response = self.client.responses.create(
                model="gpt-4.1",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "FourLayerActionPlan",
                        "strict": True,
                        "schema": action_plan_schema
                    }
                },
                temperature=0.3  # Lower temperature for consistent action planning
            )
            
            
            # NO FALLBACK: Fail fast with proper OpenAI Responses API integration
            # The response should have structured output - if not, configuration is wrong
            # NO FALLBACK: Parse JSON from OpenAI Responses API structured output
            if not hasattr(response, 'output') or not response.output or len(response.output) == 0:
                raise ValueError("OpenAI response missing output field or empty output")
            
            output_msg = response.output[0]
            if not hasattr(output_msg, 'content') or not output_msg.content or len(output_msg.content) == 0:
                raise ValueError("OpenAI output message missing content field or empty content")
            
            # Extract JSON text from response
            text_content = output_msg.content[0].text
            if not text_content:
                raise ValueError("OpenAI response content is empty")
            
            # Parse JSON string to dictionary
            try:
                action_plans = json.loads(text_content)
            except json.JSONDecodeError as e:
                raise ValueError(f"OpenAI returned invalid JSON: {text_content[:200]}... Error: {e}")
            if not action_plans:
                raise ValueError("OpenAI Responses API returned empty output_parsed.")
            
            if not isinstance(action_plans, dict):
                raise ValueError(f"OpenAI returned parsed output that is not a dictionary. Got {type(action_plans)}: {action_plans}")
            
            # Add metadata
            action_plans['plan_id'] = str(uuid.uuid4())
            action_plans['analysis_id'] = analysis.get('analysis_id')
            action_plans['transcript_id'] = transcript.id
            action_plans['generator_version'] = "1.0"
            
            # Return action plans directly - no external dependencies
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
        
        return f'''
=== COMPLETE CALL TRANSCRIPT ===
{conversation_text}

=== CALL METADATA ===
Duration: {context['call_duration']} minutes
Topic: {context['call_topic']}
Customer ID: {context['customer_id']}

=== AI ANALYSIS ===
Primary Intent: {analysis.get('primary_intent', 'Unknown')}
Sentiment: {analysis.get('sentiment', 'Unknown')}
Urgency: {analysis.get('urgency_level', 'Unknown')}
Risk Score: {analysis.get('risk_score', 0)}
Compliance Flags: {', '.join(analysis.get('compliance_flags', []))}

Borrower Risks:
{json.dumps(analysis.get('borrower_risks', {}), indent=2)}

Advisor Performance:
{json.dumps(analysis.get('advisor_performance', {}), indent=2)}

=== EXTRACTED KEY POINTS ===
Promises Made: {', '.join(context['promises_made'])}
Customer Concerns: {', '.join(context['customer_concerns'])}
Timeline Commitments: {', '.join(context['timeline_commitments'])}
Next Steps: {', '.join(context['next_steps_mentioned'])}

=== INSTRUCTION ===
Based on the COMPLETE conversation and analysis above, generate four comprehensive action plans:

1. BORROWER PLAN: What actions should be taken for the customer?
2. ADVISOR PLAN: What coaching or feedback for the advisor?
3. SUPERVISOR PLAN: What needs supervisor attention or approval?
4. LEADERSHIP PLAN: What strategic insights or patterns emerged?

Use the actual conversation details. Be specific and actionable.
'''
    
    def _get_action_plan_schema(self) -> Dict[str, Any]:
        """Define JSON schema for structured action plan output.
        
        Returns:
            JSON schema for four-layer action plans
        """
        return {
            "type": "object",
            "properties": {
                "borrower_plan": {
                    "type": "object",
                    "properties": {
                        "immediate_actions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "timeline": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "auto_executable": {"type": "boolean"},
                                    "description": {"type": "string"}
                                },
                                "required": ["action", "timeline", "priority", "auto_executable", "description"],
                                "additionalProperties": False
                            }
                        },
                        "follow_ups": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "due_date": {"type": "string"},
                                    "owner": {"type": "string"},
                                    "trigger_condition": {"type": "string"}
                                },
                                "required": ["action", "due_date", "owner", "trigger_condition"],
                                "additionalProperties": False
                            }
                        },
                        "personalized_offers": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "risk_mitigation": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["immediate_actions", "follow_ups", "personalized_offers", "risk_mitigation"],
                    "additionalProperties": False
                },
                "advisor_plan": {
                    "type": "object",
                    "properties": {
                        "coaching_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "coaching_point": {"type": "string"},
                                    "expected_improvement": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]}
                                },
                                "required": ["action", "coaching_point", "expected_improvement", "priority"],
                                "additionalProperties": False
                            }
                        },
                        "performance_feedback": {
                            "type": "object",
                            "properties": {
                                "strengths": {"type": "array", "items": {"type": "string"}},
                                "improvements": {"type": "array", "items": {"type": "string"}},
                                "score_explanations": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["strengths", "improvements", "score_explanations"],
                            "additionalProperties": False
                        },
                        "training_recommendations": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "next_actions": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["coaching_items", "performance_feedback", "training_recommendations", "next_actions"],
                    "additionalProperties": False
                },
                "supervisor_plan": {
                    "type": "object",
                    "properties": {
                        "escalation_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "item": {"type": "string"},
                                    "reason": {"type": "string"},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "action_required": {"type": "string"}
                                },
                                "required": ["item", "reason", "priority", "action_required"],
                                "additionalProperties": False
                            }
                        },
                        "team_patterns": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "compliance_review": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "approval_required": {"type": "boolean"},
                        "process_improvements": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["escalation_items", "team_patterns", "compliance_review", "approval_required", "process_improvements"],
                    "additionalProperties": False
                },
                "leadership_plan": {
                    "type": "object",
                    "properties": {
                        "portfolio_insights": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "strategic_opportunities": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "risk_indicators": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "trend_analysis": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "resource_allocation": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["portfolio_insights", "strategic_opportunities", "risk_indicators", "trend_analysis", "resource_allocation"],
                    "additionalProperties": False
                }
            },
            "required": ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"],
            "additionalProperties": False
        }
    
