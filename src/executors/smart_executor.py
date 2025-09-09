"""
Smart Executor - LLM-powered intelligent execution of action plans
Uses OpenAI Responses API to make smart decisions about HOW to execute actions.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import openai

from src.tools.mock_tools import MockTools
from src.storage.action_plan_store import ActionPlanStore
from src.storage.analysis_store import AnalysisStore
from src.storage.transcript_store import TranscriptStore


class SmartExecutor:
    """Intelligent executor that uses LLM to make execution decisions"""
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "data/call_center.db"):
        """Initialize smart executor with tools and LLM"""
        self.tools = MockTools()
        self.action_plan_store = ActionPlanStore(db_path)
        self.analysis_store = AnalysisStore(db_path) 
        self.transcript_store = TranscriptStore(db_path)
        
        # Initialize OpenAI client
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            import os
            self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def execute_action_plan(self, plan_id: str, mode: str = 'auto') -> Dict[str, Any]:
        """Execute an action plan with intelligent decisions"""
        
        try:
            # Get action plan
            action_plan = self.action_plan_store.get_by_id(plan_id)
            if not action_plan:
                return {
                    'status': 'error',
                    'message': f'Action plan {plan_id} not found'
                }
            
            # Check approval status
            if not self._is_approved_for_execution(action_plan, mode):
                return {
                    'status': 'pending_approval',
                    'message': f'Action plan requires approval. Current status: {action_plan["queue_status"]}',
                    'risk_level': action_plan['risk_level']
                }
            
            # Get context for intelligent execution
            context = self._get_execution_context(action_plan)
            
            # Execute actions from each plan layer
            execution_results = {
                'execution_id': f'EXEC_{uuid.uuid4().hex[:10].upper()}',
                'plan_id': plan_id,
                'executed_at': datetime.now().isoformat(),
                'status': 'success',
                'results': {
                    'borrower_actions': [],
                    'advisor_actions': [], 
                    'supervisor_actions': [],
                    'leadership_actions': []
                },
                'artifacts_created': [],
                'errors': []
            }
            
            # Execute borrower-facing actions
            if 'borrower_plan' in action_plan:
                borrower_results = self._execute_borrower_actions(
                    action_plan['borrower_plan'], context
                )
                execution_results['results']['borrower_actions'] = borrower_results
                
            # Execute advisor-facing actions  
            if 'advisor_plan' in action_plan:
                advisor_results = self._execute_advisor_actions(
                    action_plan['advisor_plan'], context
                )
                execution_results['results']['advisor_actions'] = advisor_results
                
            # Execute supervisor-facing actions
            if 'supervisor_plan' in action_plan:
                supervisor_results = self._execute_supervisor_actions(
                    action_plan['supervisor_plan'], context
                )
                execution_results['results']['supervisor_actions'] = supervisor_results
            
            # Execute leadership-facing actions
            if 'leadership_plan' in action_plan:
                leadership_results = self._execute_leadership_actions(
                    action_plan['leadership_plan'], context  
                )
                execution_results['results']['leadership_actions'] = leadership_results
            
            # Collect all artifacts
            all_results = (
                execution_results['results']['borrower_actions'] +
                execution_results['results']['advisor_actions'] +
                execution_results['results']['supervisor_actions'] +
                execution_results['results']['leadership_actions']
            )
            
            execution_results['artifacts_created'] = [
                r.get('artifact_path') or r.get('file_path') 
                for r in all_results if r.get('artifact_path') or r.get('file_path')
            ]
            
            # Update action plan status
            self._update_plan_execution_status(plan_id, execution_results['execution_id'])
            
            return execution_results
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Execution failed: {str(e)}',
                'plan_id': plan_id
            }
    
    def _is_approved_for_execution(self, action_plan: Dict[str, Any], mode: str) -> bool:
        """Check if action plan is approved for execution"""
        
        # Auto mode respects approval workflow
        if mode == 'auto':
            return action_plan.get('queue_status') == 'approved'
        
        # Manual mode can override for testing (with user confirmation)
        if mode == 'manual':
            return True
            
        # Default to strict approval
        return action_plan.get('queue_status') == 'approved'
    
    def _get_execution_context(self, action_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Get rich context for intelligent execution"""
        
        context = {
            'plan_id': action_plan['plan_id'],
            'risk_level': action_plan.get('risk_level', 'unknown'),
            'approval_route': action_plan.get('approval_route', 'unknown')
        }
        
        # Get analysis context
        if 'analysis_id' in action_plan:
            analysis = self.analysis_store.get_by_id(action_plan['analysis_id'])
            if analysis:
                context.update({
                    'customer_sentiment': analysis.get('borrower_sentiment', {}),
                    'urgency_level': analysis.get('urgency_level', 'medium'),
                    'primary_intent': analysis.get('primary_intent', 'unknown'),
                    'risk_scores': analysis.get('borrower_risks', {}),
                    'compliance_flags': analysis.get('compliance_flags', [])
                })
        
        # Get transcript context  
        if 'transcript_id' in action_plan:
            transcript = self.transcript_store.get_by_id(action_plan['transcript_id'])
            if transcript:
                context.update({
                    'customer_id': getattr(transcript, 'customer_id', 'UNKNOWN'),
                    'advisor_id': getattr(transcript, 'advisor_id', 'UNKNOWN'),
                    'transcript_sentiment': getattr(transcript, 'sentiment', 'neutral'),
                    'call_scenario': getattr(transcript, 'scenario', 'general')
                })
        
        return context
    
    def _execute_borrower_actions(self, borrower_plan: Dict[str, Any], 
                                 context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute borrower-facing actions with LLM intelligence"""
        
        results = []
        
        # Execute immediate actions
        for action in borrower_plan.get('immediate_actions', []):
            try:
                # Use LLM to decide HOW to execute this action
                execution_decision = self._llm_decide_execution(action, context, 'borrower')
                
                # Execute based on LLM decision
                result = self._execute_single_action(execution_decision, context)
                result['action_source'] = 'borrower_immediate'
                result['original_action'] = action
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'action': action,
                    'error': str(e),
                    'action_source': 'borrower_immediate'
                })
        
        # Schedule follow-up actions
        for followup in borrower_plan.get('follow_ups', []):
            try:
                # Use LLM to decide on follow-up scheduling
                execution_decision = self._llm_decide_execution(followup, context, 'borrower_followup')
                
                result = self._execute_single_action(execution_decision, context)
                result['action_source'] = 'borrower_followup'
                result['original_action'] = followup
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error', 
                    'action': followup,
                    'error': str(e),
                    'action_source': 'borrower_followup'
                })
        
        return results
    
    def _execute_advisor_actions(self, advisor_plan: Dict[str, Any],
                                context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute advisor-facing actions"""
        
        results = []
        
        # Create coaching notes
        for coaching_item in advisor_plan.get('coaching_items', []):
            try:
                # Generate coaching document
                result = self.tools.generate_document(
                    'coaching_note',
                    context.get('advisor_id', 'UNKNOWN_ADVISOR'),
                    {
                        'coaching_item': coaching_item,
                        'customer_context': context.get('primary_intent', ''),
                        'performance_areas': advisor_plan.get('performance_feedback', {}),
                        'call_id': context.get('plan_id', '')
                    }
                )
                result['action_source'] = 'advisor_coaching'
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'action': coaching_item,
                    'error': str(e),
                    'action_source': 'advisor_coaching'
                })
        
        return results
    
    def _execute_supervisor_actions(self, supervisor_plan: Dict[str, Any],
                                   context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute supervisor-facing actions"""
        
        results = []
        
        # Handle escalation items
        for escalation in supervisor_plan.get('escalation_items', []):
            try:
                # Create escalation notification
                result = self.tools.send_notification(
                    recipient='supervisor@demo.com',
                    message=f"Escalation required: {escalation.get('item', 'Unknown')} - {escalation.get('reason', 'No reason provided')}",
                    channel='email',
                    urgency=escalation.get('priority', 'medium')
                )
                result['action_source'] = 'supervisor_escalation'
                result['escalation_details'] = escalation
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'action': escalation,
                    'error': str(e),
                    'action_source': 'supervisor_escalation'
                })
        
        return results
    
    def _execute_leadership_actions(self, leadership_plan: Dict[str, Any],
                                   context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute leadership-facing actions"""
        
        results = []
        
        # Generate portfolio insights reports
        if leadership_plan.get('portfolio_insights'):
            try:
                result = self.tools.generate_document(
                    'portfolio_insights',
                    'LEADERSHIP_TEAM',
                    {
                        'insights': leadership_plan['portfolio_insights'],
                        'strategic_opportunities': leadership_plan.get('strategic_opportunities', []),
                        'risk_indicators': leadership_plan.get('risk_indicators', []),
                        'generated_from_call': context.get('plan_id', '')
                    }
                )
                result['action_source'] = 'leadership_insights'
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'error': str(e),
                    'action_source': 'leadership_insights'
                })
        
        return results
    
    def _llm_decide_execution(self, action: Dict[str, Any], context: Dict[str, Any],
                             action_type: str) -> Dict[str, Any]:
        """Use LLM to make intelligent execution decisions"""
        
        prompt = f"""
        You are an intelligent execution agent. Decide HOW to execute this action:
        
        Action to execute: {json.dumps(action, indent=2)}
        
        Context:
        - Customer sentiment: {context.get('customer_sentiment', {}).get('overall', 'neutral')}
        - Urgency level: {context.get('urgency_level', 'medium')}
        - Risk level: {context.get('risk_level', 'medium')}
        - Customer ID: {context.get('customer_id', 'UNKNOWN')}
        - Primary issue: {context.get('primary_intent', 'general_inquiry')}
        
        Action type: {action_type}
        
        Decide:
        1. What tool to use (email/callback/document/notification/crm_update)
        2. What content/message to create (be specific and personalized)
        3. When to execute (now/scheduled)
        4. What tone to use (friendly/formal/urgent/empathetic)
        5. Any specific parameters needed
        
        For emails: provide recipient, subject, and body
        For callbacks: provide date/time and notes  
        For documents: specify document type and key data
        For CRM updates: specify what fields to update
        
        Consider the customer's emotional state and the context of their call.
        Be helpful and personalized in your response.
        """
        
        try:
            response = self.client.responses.create(
                model="gpt-4",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ExecutionDecision",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "tool": {
                                    "type": "string",
                                    "enum": ["email", "callback", "document", "notification", "crm_update"]
                                },
                                "content": {"type": "string"},
                                "tone": {
                                    "type": "string", 
                                    "enum": ["friendly", "formal", "urgent", "empathetic"]
                                },
                                "timing": {
                                    "type": "string",
                                    "enum": ["immediate", "scheduled", "delayed"]
                                },
                                "parameters": {"type": "object"},
                                "reasoning": {"type": "string"}
                            },
                            "required": ["tool", "content", "tone", "timing", "parameters"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            return response.output_parsed
            
        except Exception as e:
            # Fallback to simple execution if LLM fails
            return self._fallback_execution_decision(action, context)
    
    def _fallback_execution_decision(self, action: Dict[str, Any], 
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback execution decision when LLM is unavailable"""
        
        action_text = action.get('action', '').lower()
        
        # Simple rule-based decisions
        if 'email' in action_text or 'send' in action_text:
            return {
                'tool': 'email',
                'content': f"Following up on your recent call regarding {context.get('primary_intent', 'your inquiry')}.",
                'tone': 'friendly',
                'timing': 'immediate',
                'parameters': {
                    'subject': 'Follow-up from Customer Service',
                    'recipient': f"{context.get('customer_id', 'customer')}@demo.com"
                },
                'reasoning': 'Fallback rule-based decision'
            }
        elif 'call' in action_text or 'callback' in action_text:
            return {
                'tool': 'callback',
                'content': f"Schedule follow-up call regarding {context.get('primary_intent', 'recent inquiry')}",
                'tone': 'friendly',
                'timing': 'scheduled',
                'parameters': {
                    'scheduled_time': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d 14:00'),
                    'notes': action.get('description', 'Follow-up call scheduled')
                },
                'reasoning': 'Fallback rule-based decision'
            }
        else:
            return {
                'tool': 'document',
                'content': f"Generate documentation for: {action.get('action', 'Customer action')}",
                'tone': 'formal',
                'timing': 'immediate',
                'parameters': {
                    'doc_type': 'action_summary'
                },
                'reasoning': 'Fallback rule-based decision'
            }
    
    def _execute_single_action(self, execution_decision: Dict[str, Any],
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single action based on LLM decision"""
        
        tool = execution_decision['tool']
        params = execution_decision['parameters']
        
        if tool == 'email':
            return self.tools.send_email(
                recipient=params.get('recipient', f"{context.get('customer_id', 'customer')}@demo.com"),
                subject=params.get('subject', 'Customer Service Follow-up'),
                body=execution_decision['content'],
                template_id=params.get('template_id')
            )
        
        elif tool == 'callback':
            return self.tools.schedule_callback(
                customer_id=context.get('customer_id', 'UNKNOWN'),
                scheduled_time=params.get('scheduled_time', 'TBD'),
                notes=execution_decision['content'],
                priority=params.get('priority', 'normal')
            )
        
        elif tool == 'document':
            return self.tools.generate_document(
                doc_type=params.get('doc_type', 'general'),
                customer_id=context.get('customer_id', 'UNKNOWN'),
                data={
                    'content': execution_decision['content'],
                    'context': context,
                    'generated_reason': params.get('reason', 'Action plan execution')
                }
            )
        
        elif tool == 'notification':
            return self.tools.send_notification(
                recipient=params.get('recipient', 'staff@demo.com'),
                message=execution_decision['content'],
                channel=params.get('channel', 'app'),
                urgency=params.get('urgency', 'normal')
            )
        
        elif tool == 'crm_update':
            return self.tools.update_crm(
                customer_id=context.get('customer_id', 'UNKNOWN'),
                updates=params.get('updates', {'notes': execution_decision['content']}),
                interaction_type=params.get('interaction_type', 'action_plan_execution')
            )
        
        else:
            raise ValueError(f"Unknown tool: {tool}")
    
    def _update_plan_execution_status(self, plan_id: str, execution_id: str):
        """Update action plan with execution information"""
        
        # Note: This would update the action plan status in a real system
        # For now, we'll log it to the execution history
        self.tools._log_action('plan_executed', {
            'plan_id': plan_id,
            'execution_id': execution_id,
            'executed_at': datetime.now().isoformat()
        })
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        return self.tools.get_recent_actions(limit)
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution statistics summary"""
        return self.tools.get_execution_summary()