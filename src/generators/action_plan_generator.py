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
    - Implements approval routing based on risk assessment
    """
    
    def __init__(self, api_key: Optional[str] = None, db_path: Optional[str] = None):
        """Initialize the action plan generator.
        
        Args:
            api_key: OpenAI API key (optional, uses environment variable if not provided)
            db_path: Database path for DecisionAgent integration (optional)
        """
        self.client = openai.OpenAI(api_key=api_key or os.getenv('OPENAI_API_KEY'))
        
        # Initialize Decision Agent components if database path provided
        if db_path:
            from src.agents.decision_agent import DecisionAgent
            from src.storage.approval_store import ApprovalStore
            self.decision_agent = DecisionAgent()
            self.approval_store = ApprovalStore(db_path)
        else:
            self.decision_agent = None
            self.approval_store = None
    
    def generate(self, analysis: Dict[str, Any], transcript: Transcript) -> Dict[str, Any]:
        """Generate four-layer action plans from analysis and transcript.
        
        Args:
            analysis: Analysis results from call_analyzer
            transcript: Original transcript object
            
        Returns:
            Dictionary containing four layer action plans with approval routing
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
            
            # Add approval routing based on risk assessment
            action_plans = self._add_approval_routing(action_plans, analysis)
            
            # PHASE 1: DecisionAgent integration - per-action risk evaluation and approval routing
            if self.decision_agent is not None:
                action_plans = self._integrate_decision_agent(action_plans, analysis, transcript)
            else:
                # Fail gracefully if DecisionAgent not configured
                raise AttributeError("DecisionAgent not configured. Initialize ActionPlanGenerator with db_path parameter.")
            
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
        
        # Extract promises and commitments from transcript
        context['promises_made'] = self._extract_promises(transcript)
        context['timeline_commitments'] = self._extract_timelines(transcript)
        context['customer_concerns'] = self._extract_concerns(transcript)
        context['next_steps_mentioned'] = self._extract_next_steps(transcript)
        
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
    
    def _extract_promises(self, transcript: Transcript) -> List[str]:
        """Extract promises and commitments made during the call.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            List of promises/commitments found
        """
        promises = []
        promise_indicators = [
            "we'll", "i'll", "we will", "i will", "we can", "i can",
            "we'll send", "we'll call", "we'll email", "we'll follow up"
        ]
        
        for message in transcript.messages:
            # Look for advisor messages with promise indicators
            if hasattr(message, 'speaker') and 'CSR' in message.speaker.upper():
                text = message.text.lower()
                for indicator in promise_indicators:
                    if indicator in text:
                        # Extract the sentence containing the promise
                        sentences = message.text.split('.')
                        for sentence in sentences:
                            if indicator in sentence.lower():
                                promises.append(sentence.strip())
                                break
        
        return list(set(promises))  # Remove duplicates
    
    def _extract_timelines(self, transcript: Transcript) -> List[str]:
        """Extract timeline commitments from the conversation.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            List of timeline commitments
        """
        timelines = []
        timeline_patterns = [
            "within", "in", "by", "days", "weeks", "hours", "minutes",
            "today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday"
        ]
        
        for message in transcript.messages:
            if hasattr(message, 'speaker') and 'CSR' in message.speaker.upper():
                text = message.text.lower()
                for pattern in timeline_patterns:
                    if pattern in text:
                        # Extract sentences with timeline information
                        sentences = message.text.split('.')
                        for sentence in sentences:
                            if any(p in sentence.lower() for p in timeline_patterns):
                                timelines.append(sentence.strip())
                                break
        
        return list(set(timelines))
    
    def _extract_concerns(self, transcript: Transcript) -> List[str]:
        """Extract customer concerns and pain points.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            List of customer concerns
        """
        concerns = []
        concern_indicators = [
            "worried", "concerned", "confused", "frustrated", "problem", "issue",
            "difficult", "hard", "expensive", "cost", "afraid", "nervous"
        ]
        
        for message in transcript.messages:
            # Look for customer messages with concern indicators
            if hasattr(message, 'speaker') and 'CUST' in message.speaker.upper():
                text = message.text.lower()
                for indicator in concern_indicators:
                    if indicator in text:
                        concerns.append(message.text.strip())
                        break
        
        return concerns
    
    def _extract_next_steps(self, transcript: Transcript) -> List[str]:
        """Extract next steps discussed in the conversation.
        
        Args:
            transcript: Transcript to analyze
            
        Returns:
            List of next steps mentioned
        """
        next_steps = []
        step_indicators = [
            "next step", "need to", "have to", "should", "must", "required",
            "process", "submit", "send", "provide", "contact", "call back"
        ]
        
        for message in transcript.messages:
            text = message.text.lower()
            for indicator in step_indicators:
                if indicator in text:
                    next_steps.append(message.text.strip())
                    break
        
        return next_steps
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for action plan generation.
        
        Args:
            context: Extracted context information
            
        Returns:
            Formatted prompt for OpenAI
        """
        return f"""
        Generate comprehensive four-layer action plans for this mortgage servicing call.
        
        Call Analysis Context:
        Primary Intent: {context['primary_intent']}
        Urgency Level: {context['urgency_level']}
        Customer ID: {context['customer_id']}
        Confidence Score: {context['confidence_score']}
        
        Borrower Risk Profile:
        {json.dumps(context['borrower_risks'], indent=2)}
        
        Advisor Performance:
        {json.dumps(context['advisor_metrics'], indent=2)}
        
        Promises Made:
        {chr(10).join(f'- {promise}' for promise in context['promises_made'])}
        
        Timeline Commitments:
        {chr(10).join(f'- {timeline}' for timeline in context['timeline_commitments'])}
        
        Customer Concerns:
        {chr(10).join(f'- {concern}' for concern in context['customer_concerns'])}
        
        Topics Discussed:
        {chr(10).join(f'- {topic}' for topic in context['topics_discussed'])}
        
        Resolution Status:
        - Issue Resolved: {context['resolution_status']['resolved']}
        - First Call Resolution: {context['resolution_status']['first_call_resolution']}
        - Escalation Needed: {context['resolution_status']['escalation_needed']}
        
        Compliance Flags: {', '.join(context['compliance_flags']) if context['compliance_flags'] else 'None'}
        
        Generate four comprehensive action plans:
        
        1. BORROWER PLAN: Immediate actions, follow-ups, personalized offers, and risk mitigation
        2. ADVISOR PLAN: Coaching items, performance feedback, and development opportunities  
        3. SUPERVISOR PLAN: Escalation items, team patterns, and approval requirements
        4. LEADERSHIP PLAN: Portfolio insights, strategic opportunities, and risk indicators
        
        Focus on:
        - Specific, actionable items with clear timelines
        - Risk-based prioritization
        - Personalized recommendations based on conversation context
        - Compliance requirements and disclosure needs
        - Continuous improvement opportunities
        """
    
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
    
    def _add_approval_routing(self, action_plans: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Add approval routing based on risk assessment.
        
        Args:
            action_plans: Generated action plans
            analysis: Analysis data for risk assessment
            
        Returns:
            Action plans with approval routing information
        """
        confidence = analysis.get('confidence_score', 0)
        risks = analysis.get('borrower_risks', {})
        compliance_flags = analysis.get('compliance_flags', [])
        
        # Calculate maximum risk level
        max_risk = max(risks.values()) if risks else 0
        
        # Determine approval routing based on Architecture diagram decision flow
        if compliance_flags or confidence < 0.7 or max_risk > 0.7:
            # High risk → Queue → Manual Approve (Supervisor)
            action_plans['approval_route'] = 'supervisor_approval'
            action_plans['queue_status'] = 'pending_supervisor'
            action_plans['auto_executable'] = False
            action_plans['risk_level'] = 'high'
        elif confidence < 0.9 or max_risk > 0.3:
            # Medium risk → Queue → Advisor Approve
            action_plans['approval_route'] = 'advisor_approval'
            action_plans['queue_status'] = 'pending_advisor'
            action_plans['auto_executable'] = False
            action_plans['risk_level'] = 'medium'
        else:
            # Low risk → Auto Approve
            action_plans['approval_route'] = 'auto_approved'
            action_plans['queue_status'] = 'approved'
            action_plans['auto_executable'] = True
            action_plans['risk_level'] = 'low'
        
        # Add routing metadata
        action_plans['routing_reason'] = self._get_routing_reason(confidence, max_risk, compliance_flags)
        action_plans['created_at'] = str(uuid.uuid4())  # Placeholder for timestamp
        
        return action_plans
    
    def _evaluate_individual_actions(self, action_plans: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 1: Evaluate each action item individually for risk and approval requirements.
        This implements the first step towards the Decision Agent pattern.
        """
        
        # Feature flag to enable/disable per-action evaluation
        ENABLE_PER_ACTION_EVALUATION = True
        
        if not ENABLE_PER_ACTION_EVALUATION:
            return action_plans
        
        # Import the risk evaluator
        from src.analyzers.action_risk_evaluator import ActionRiskEvaluator
        evaluator = ActionRiskEvaluator()
        
        # Create plan context for evaluation
        plan_context = {
            'risk_level': action_plans.get('risk_level', 'medium'),
            'complaint_risk': analysis.get('borrower_risks', {}).get('complaint_risk', 0),
            'churn_risk': analysis.get('borrower_risks', {}).get('churn_risk', 0),
            'delinquency_risk': analysis.get('borrower_risks', {}).get('delinquency_risk', 0),
            'urgency_level': analysis.get('urgency_level', 'medium'),
            'compliance_flags': analysis.get('compliance_flags', []),
            'confidence_score': analysis.get('confidence_score', 0.5)
        }
        
        # Evaluate actions in each layer
        action_counter = 1
        approval_summary = {
            'total_actions': 0,
            'needs_approval': 0,
            'auto_approved': 0,
            'high_risk_actions': 0,
            'by_layer': {}
        }
        
        for layer_name in ['borrower_plan', 'advisor_plan', 'supervisor_plan', 'leadership_plan']:
            if layer_name not in action_plans:
                continue
            
            layer_data = action_plans[layer_name]
            layer_summary = {'total': 0, 'needs_approval': 0, 'auto_approved': 0}
            
            # Set current layer in context
            plan_context['current_layer'] = layer_name
            
            # Process immediate actions
            if 'immediate_actions' in layer_data and isinstance(layer_data['immediate_actions'], list):
                for i, action in enumerate(layer_data['immediate_actions']):
                    if isinstance(action, dict):
                        # Generate action ID
                        action_id = f"ACT_{action_counter:03d}_{layer_name[:4].upper()}_IMM_{i+1:03d}"
                        action['action_id'] = action_id
                        
                        # Evaluate action
                        evaluated_action = evaluator.evaluate_action(action, plan_context)
                        layer_data['immediate_actions'][i] = evaluated_action
                        
                        # Update counters
                        action_counter += 1
                        layer_summary['total'] += 1
                        approval_summary['total_actions'] += 1
                        
                        if evaluated_action.get('needs_approval', False):
                            layer_summary['needs_approval'] += 1
                            approval_summary['needs_approval'] += 1
                        else:
                            layer_summary['auto_approved'] += 1
                            approval_summary['auto_approved'] += 1
                        
                        if evaluated_action.get('risk_level') == 'high':
                            approval_summary['high_risk_actions'] += 1
            
            # Process follow-up actions
            if 'follow_ups' in layer_data and isinstance(layer_data['follow_ups'], list):
                for i, action in enumerate(layer_data['follow_ups']):
                    if isinstance(action, dict):
                        # Generate action ID
                        action_id = f"ACT_{action_counter:03d}_{layer_name[:4].upper()}_FUP_{i+1:03d}"
                        action['action_id'] = action_id
                        
                        # Evaluate action
                        evaluated_action = evaluator.evaluate_action(action, plan_context)
                        layer_data['follow_ups'][i] = evaluated_action
                        
                        # Update counters
                        action_counter += 1
                        layer_summary['total'] += 1
                        approval_summary['total_actions'] += 1
                        
                        if evaluated_action.get('needs_approval', False):
                            layer_summary['needs_approval'] += 1
                            approval_summary['needs_approval'] += 1
                        else:
                            layer_summary['auto_approved'] += 1
                            approval_summary['auto_approved'] += 1
                        
                        if evaluated_action.get('risk_level') == 'high':
                            approval_summary['high_risk_actions'] += 1
            
            approval_summary['by_layer'][layer_name] = layer_summary
        
        # Calculate approval percentage
        if approval_summary['total_actions'] > 0:
            approval_summary['approval_percentage'] = (
                approval_summary['needs_approval'] / approval_summary['total_actions']
            ) * 100
        else:
            approval_summary['approval_percentage'] = 0
        
        # Add summary to action plans
        action_plans['action_evaluation_summary'] = approval_summary
        action_plans['per_action_evaluation_enabled'] = True
        action_plans['evaluation_timestamp'] = datetime.now().isoformat()
        
        # Add evaluator summary
        evaluator_summary = evaluator.get_evaluation_summary()
        action_plans['evaluator_summary'] = evaluator_summary
        
        return action_plans
    
    def _get_routing_reason(self, confidence: float, max_risk: float, compliance_flags: List[str]) -> str:
        """Get human-readable reason for approval routing.
        
        Args:
            confidence: Analysis confidence score
            max_risk: Maximum risk level
            compliance_flags: List of compliance issues
            
        Returns:
            Explanation of routing decision
        """
        reasons = []
        
        if compliance_flags:
            reasons.append(f"Compliance flags: {', '.join(compliance_flags)}")
        if confidence < 0.7:
            reasons.append(f"Low confidence score: {confidence}")
        if max_risk > 0.7:
            reasons.append(f"High risk detected: {max_risk}")
        elif max_risk > 0.3:
            reasons.append(f"Medium risk detected: {max_risk}")
        
        if not reasons:
            return "Low risk - auto-approved"
        
        return "; ".join(reasons)
    
    def _integrate_decision_agent(self, action_plans: Dict[str, Any], analysis: Dict[str, Any], transcript: Transcript) -> Dict[str, Any]:
        """
        Integrate DecisionAgent for comprehensive risk evaluation and approval routing.
        
        Args:
            action_plans: Generated action plans from OpenAI
            analysis: Analysis results for context
            transcript: Original transcript for context
            
        Returns:
            Enhanced action plans with per-action risk evaluation and approval routing
        """
        # Create analysis context for DecisionAgent
        analysis_context = {
            'complaint_risk': analysis.get('borrower_risks', {}).get('complaint_risk', 0),
            'urgency_level': analysis.get('urgency_level', 'medium'),
            'compliance_flags': analysis.get('compliance_flags', []),
            'borrower_risks': analysis.get('borrower_risks', {}),
            'confidence_score': analysis.get('confidence_score', 0.5),
            'transcript_id': transcript.id
        }
        
        # Process action plan through DecisionAgent
        enhanced_plan = self.decision_agent.process_action_plan(action_plans, analysis_context)
        
        # Store approval records for actions needing approval
        if self.approval_store is not None:
            self._store_approval_records(enhanced_plan)
        
        return enhanced_plan
    
    def _store_approval_records(self, action_plans: Dict[str, Any]) -> None:
        """
        Store approval records for actions that need approval.
        
        Args:
            action_plans: Enhanced action plans with approval data
        """
        # Extract all actions from all layers
        all_actions = []
        
        # Collect actions from each layer
        for layer_name in ['borrower_plan', 'advisor_plan', 'supervisor_plan']:
            if layer_name not in action_plans:
                continue
                
            layer_data = action_plans[layer_name]
            
            # Collect immediate actions
            for action in layer_data.get('immediate_actions', []):
                if isinstance(action, dict) and action.get('needs_approval'):
                    all_actions.append((action, layer_name, 'immediate_actions'))
            
            # Collect follow-ups (borrower layer)
            if layer_name == 'borrower_plan':
                for action in layer_data.get('follow_ups', []):
                    if isinstance(action, dict) and action.get('needs_approval'):
                        all_actions.append((action, layer_name, 'follow_ups'))
            
            # Collect coaching items (advisor layer)
            if layer_name == 'advisor_plan':
                for action in layer_data.get('coaching_items', []):
                    if isinstance(action, dict) and action.get('needs_approval'):
                        all_actions.append((action, layer_name, 'coaching_items'))
                        
            # Collect escalation items (supervisor layer)
            if layer_name == 'supervisor_plan':
                for action in layer_data.get('escalation_items', []):
                    if isinstance(action, dict) and action.get('needs_approval'):
                        all_actions.append((action, layer_name, 'escalation_items'))
        
        # Handle leadership plan separately (single action)
        if 'leadership_plan' in action_plans and action_plans['leadership_plan'].get('needs_approval'):
            leadership_action = {
                'action': 'Leadership portfolio insights',
                'description': action_plans['leadership_plan'].get('portfolio_insights', ''),
                'needs_approval': action_plans['leadership_plan']['needs_approval'],
                'approval_status': action_plans['leadership_plan']['approval_status'],
                'risk_level': action_plans['leadership_plan']['risk_level'],
                'action_id': action_plans['leadership_plan'].get('action_id', 'ACT_LEAD_001')
            }
            all_actions.append((leadership_action, 'leadership_plan', 'portfolio_insights'))
        
        # Store approval records
        for action, layer, action_type in all_actions:
            approval_record = {
                'id': f"APPR_{action.get('action_id', 'UNKNOWN')[4:]}",  # Remove ACT_ prefix
                'plan_id': action_plans['plan_id'],
                'action_id': action.get('action_id', f"ACT_MISSING_{len(all_actions)}"),
                'transcript_id': action_plans['transcript_id'],
                'analysis_id': action_plans['analysis_id'],
                'action_text': action['action'],
                'action_description': action.get('description', ''),
                'action_layer': layer,
                'action_type': action.get('action_type', 'general_action'),
                'risk_score': action.get('risk_score', 0.5),
                'risk_level': action['risk_level'],
                'financial_impact': action.get('financial_impact', False),
                'compliance_impact': action.get('compliance_impact', False),
                'customer_facing': action.get('customer_facing', False),
                'needs_approval': action['needs_approval'],
                'approval_status': action['approval_status'],
                'approval_route': action.get('routing_decision', 'pending'),
                'approval_reason': action.get('approval_reason', ''),
                'decision_agent_version': 'v1.0'
            }
            
            # Store in approval database
            self.approval_store.store_action_approval(approval_record)