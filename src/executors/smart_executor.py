"""
Smart Executor - LLM-powered intelligent execution of action plans
Uses OpenAI Responses API to make smart decisions about HOW to execute actions.
"""
import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.tools.mock_tools import MockTools
from src.storage.action_plan_store import ActionPlanStore
from src.storage.analysis_store import AnalysisStore
from src.storage.transcript_store import TranscriptStore
from src.storage.approval_store import ApprovalStore


class SmartExecutor:
    """Intelligent executor that uses LLM to make execution decisions"""
    
    def _rx_parsed(self, resp):
        """Return parsed JSON when using text.format json_schema."""
        try:
            for b in getattr(resp, "output", []) or []:
                for c in getattr(b, "content", []) or []:
                    # First try the .parsed field (if it exists)
                    p = getattr(c, "parsed", None)
                    if p is not None:
                        return p
                    
                    # If no .parsed field, try to parse JSON from .text field
                    text = getattr(c, "text", None)
                    if text:
                        try:
                            import json
                            return json.loads(text)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            pass
        
        # Return empty dict instead of None to prevent subscriptable errors
        return {}
    
    def __init__(self, api_key: Optional[str] = None, db_path: str = "data/call_center.db"):
        """Initialize smart executor with tools and LLM"""
        self.tools = MockTools()
        self.action_plan_store = ActionPlanStore(db_path)
        self.analysis_store = AnalysisStore(db_path) 
        self.transcript_store = TranscriptStore(db_path)
        
        # Initialize ApprovalStore for approval-aware execution
        try:
            self.approval_store = ApprovalStore(db_path)
        except Exception:
            # Graceful degradation if ApprovalStore unavailable
            self.approval_store = None
        
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
            
            # Execute borrower-facing actions with actor assignment
            if 'borrower_plan' in action_plan:
                borrower_results = self._execute_borrower_actions_with_actors(
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
            
            # Store execution results for feedback loop
            all_action_results = (
                execution_results['results']['borrower_actions'] +
                execution_results['results']['advisor_actions'] +
                execution_results['results']['supervisor_actions'] +
                execution_results['results']['leadership_actions']
            )
            self._store_execution_results(execution_results['execution_id'], all_action_results)
            
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
    
    def _check_action_approval_status(self, action: Dict[str, Any]) -> str:
        """Check action approval status, consulting ApprovalStore if available."""
        
        # Try to get action_id for ApprovalStore lookup
        action_id = action.get('action_id')
        
        if self.approval_store and action_id:
            try:
                # Query ApprovalStore for current approval status
                approval_record = self.approval_store.get_approval_by_action_id(action_id)
                if approval_record:
                    approval_status = approval_record.get('approval_status')
                    if approval_status:
                        return approval_status
            except Exception:
                # Graceful degradation on ApprovalStore errors
                pass
        
        # Fallback to action plan's approval status
        return action.get('approval_status', 'unknown')
    
    def _execute_borrower_actions(self, borrower_plan: Dict[str, Any], 
                                 context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute borrower-facing actions with LLM intelligence"""
        
        results = []
        
        # Execute immediate actions
        for action in borrower_plan.get('immediate_actions', []):
            try:
                # Check individual action approval status using ApprovalStore-aware method
                current_approval_status = self._check_action_approval_status(action)
                if action.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': action,
                        'action_source': 'borrower_immediate',
                        'approval_status': current_approval_status,
                        'risk_level': action.get('risk_level', 'unknown')
                    })
                    continue
                
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
                # Check individual action approval status using ApprovalStore-aware method
                current_approval_status = self._check_action_approval_status(followup)
                if followup.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': followup,
                        'action_source': 'borrower_followup',
                        'approval_status': current_approval_status,
                        'risk_level': followup.get('risk_level', 'unknown')
                    })
                    continue
                
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
                # Check individual action approval status using ApprovalStore-aware method
                current_approval_status = self._check_action_approval_status(coaching_item)
                if coaching_item.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': coaching_item,
                        'action_source': 'advisor_coaching',
                        'approval_status': current_approval_status,
                        'risk_level': coaching_item.get('risk_level', 'unknown')
                    })
                    continue
                
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
                # Check individual action approval status using ApprovalStore-aware method
                current_approval_status = self._check_action_approval_status(escalation)
                if escalation.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': escalation,
                        'action_source': 'supervisor_escalation',
                        'approval_status': current_approval_status,
                        'risk_level': escalation.get('risk_level', 'unknown')
                    })
                    continue
                
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
                # For leadership actions, treat the entire plan as an action for approval checking
                leadership_action = {
                    'action_id': leadership_plan.get('action_id'),  # May be None
                    'needs_approval': leadership_plan.get('needs_approval', False),
                    'approval_status': leadership_plan.get('approval_status', 'auto_approved'),
                    'risk_level': leadership_plan.get('risk_level', 'low')
                }
                
                # Check individual action approval status using ApprovalStore-aware method
                current_approval_status = self._check_action_approval_status(leadership_action)
                if leadership_action.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'action': 'portfolio_insights_generation',
                        'action_source': 'leadership_insights',
                        'approval_status': current_approval_status,
                        'risk_level': leadership_action.get('risk_level', 'unknown')
                    })
                    return results
                
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
                model="gpt-4o",
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
                                "parameters": {"type": "object", "additionalProperties": False},
                                "reasoning": {"type": "string"}
                            },
                            "required": ["tool", "content", "tone", "timing", "reasoning"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            return self._rx_parsed(response)
            
        except Exception as e:
            # NO FALLBACK per requirements - fail fast
            raise RuntimeError(f"LLM execution decision failed: {str(e)}. NO FALLBACK per requirements.")
    
    
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
        summary = self.tools.get_execution_summary()
        
        # Add approval-aware metrics if available
        recent_actions = self.tools.get_recent_actions(50)  # Get larger sample
        
        skipped_count = sum(1 for action in recent_actions if action.get('status') == 'skipped')
        pending_approval_count = sum(1 for action in recent_actions 
                                   if action.get('status') == 'skipped' and 
                                   'approval' in action.get('reason', '').lower())
        
        summary.update({
            'actions_skipped_for_approval': skipped_count,
            'actions_awaiting_approval': pending_approval_count,
            'approval_skip_rate': round((skipped_count / len(recent_actions)) * 100, 1) if recent_actions else 0
        })
        
        return summary
    
    def _assign_action_to_actor(self, action: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to intelligently assign action to appropriate actor.
        
        Args:
            action: Action to be executed
            context: Execution context
            
        Returns:
            Dict with actor assignment decision
        """
        prompt = f"""
        You are an intelligent action assignment agent. Analyze this action and determine the most appropriate actor to execute it.
        
        Action Details:
        {json.dumps(action, indent=2)}
        
        Context:
        - Customer ID: {context.get('customer_id', 'UNKNOWN')}
        - Risk Level: {context.get('risk_level', 'medium')}
        - Plan Type: {action.get('action_source', 'unknown')}
        - Financial Impact: {action.get('financial_impact', False)}
        - Customer Facing: {action.get('customer_facing', False)}
        
        Available Actors:
        - advisor: Customer service representatives, handles routine communications
        - supervisor: Management oversight, handles escalations and high-risk actions
        - leadership: Strategic decisions, portfolio-level insights
        - customer: Customer-initiated actions (surveys, responses, etc.)
        - system: Automated system actions (CRM updates, notifications)
        
        Consider:
        1. Actor expertise and authority level
        2. Action complexity and risk
        3. Customer interaction requirements
        4. Compliance and approval needs
        5. Efficiency and workflow optimization
        
        Provide reasoning for your choice and confidence level.
        """
        
        try:
            response = self.client.responses.create(
                model="gpt-4o",
                input=prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ActorAssignment",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "assigned_actor": {
                                    "type": "string",
                                    "enum": ["advisor", "supervisor", "leadership", "customer", "system"]
                                },
                                "reasoning": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                                "alternative_actors": {
                                    "type": "array", 
                                    "items": {"type": "string"}
                                },
                                "execution_priority": {
                                    "type": "string",
                                    "enum": ["immediate", "scheduled", "deferred"]
                                }
                            },
                            "required": ["assigned_actor", "reasoning", "confidence", "alternative_actors", "execution_priority"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            return self._rx_parsed(response)
            
        except Exception as e:
            # NO FALLBACK per requirements - fail fast
            raise RuntimeError(f"Actor assignment failed: {str(e)}. NO FALLBACK per requirements.")
    
    def _simulate_actor_execution(self, actor: str, action: Dict[str, Any], 
                                 execution_decision: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate execution by assigned actor for demo purposes.
        
        Args:
            actor: Assigned actor ('advisor', 'supervisor', etc.)
            action: Action being executed
            execution_decision: LLM decision on how to execute
            context: Execution context
            
        Returns:
            Dict with execution results including actor information
        """
        try:
            # Execute the action using existing tools
            result = self._execute_single_action(execution_decision, context)
            
            # Enhance result with actor information
            actor_enhanced_result = {
                **result,
                'executed_by_actor': actor,
                'action_id': action.get('action_id', 'UNKNOWN'),
                'actor_execution_timestamp': datetime.now().isoformat(),
                'simulation_mode': True  # Mark as demo simulation
            }
            
            # Add actor-specific execution details
            if actor == 'advisor':
                actor_enhanced_result['execution_notes'] = 'Executed by customer service advisor'
                actor_enhanced_result['customer_interaction'] = action.get('customer_facing', False)
            elif actor == 'supervisor':
                actor_enhanced_result['execution_notes'] = 'Executed with supervisory oversight'
                actor_enhanced_result['escalation_handled'] = True
            elif actor == 'leadership':
                actor_enhanced_result['execution_notes'] = 'Strategic leadership execution'
                actor_enhanced_result['strategic_impact'] = True
            elif actor == 'customer':
                actor_enhanced_result['execution_notes'] = 'Customer-initiated action simulation'
                actor_enhanced_result['customer_response'] = True
            elif actor == 'system':
                actor_enhanced_result['execution_notes'] = 'Automated system execution'
                actor_enhanced_result['automated'] = True
            
            return actor_enhanced_result
            
        except Exception as e:
            # Return error result with actor information
            return {
                'status': 'error',
                'error': str(e),
                'executed_by_actor': actor,
                'action_id': action.get('action_id', 'UNKNOWN'),
                'actor_execution_timestamp': datetime.now().isoformat(),
                'simulation_mode': True
            }
    
    def _store_execution_results(self, execution_id: str, action_results: List[Dict[str, Any]]) -> None:
        """Store execution results in ApprovalStore for feedback loop.
        
        Args:
            execution_id: Unique execution identifier
            action_results: List of action execution results
        """
        if not self.approval_store:
            # Skip if ApprovalStore not available
            return
            
        for result in action_results:
            action_id = result.get('action_id') or result.get('original_action', {}).get('action_id')
            if not action_id:
                continue
                
            try:
                # Prepare execution data for storage
                execution_data = {
                    'execution_id': execution_id,
                    'execution_status': 'success' if result.get('status') == 'success' else 'failed',
                    'execution_result': {
                        'tool_used': result.get('tool_used'),
                        'artifacts_created': result.get('artifact_path') or result.get('file_path'),
                        'execution_details': result.get('execution_notes'),
                        'customer_interaction': result.get('customer_interaction'),
                        'automated': result.get('automated', False)
                    },
                    'assigned_actor': result.get('executed_by_actor', 'unknown'),
                    'actor_assignment_reason': f"LLM assigned based on action type and context",
                    'execution_artifacts': [result.get('artifact_path'), result.get('file_path')] if result.get('artifact_path') or result.get('file_path') else [],
                    'execution_errors': [result.get('error')] if result.get('error') else []
                }
                
                # Store in ApprovalStore
                success = self.approval_store.update_execution_result(action_id, execution_data)
                
                if not success:
                    # Log but don't fail - graceful degradation
                    self.tools._log_action('execution_storage_failed', {
                        'action_id': action_id,
                        'execution_id': execution_id,
                        'reason': 'ApprovalStore update failed'
                    })
                    
            except Exception as e:
                # Log error but don't fail execution
                self.tools._log_action('execution_storage_error', {
                    'action_id': action_id,
                    'execution_id': execution_id,
                    'error': str(e)
                })
    
    def _execute_borrower_actions_with_actors(self, borrower_plan: Dict[str, Any], 
                                            context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute borrower-facing actions with actor assignment."""
        results = []
        
        # Execute immediate actions with actor assignment
        for action in borrower_plan.get('immediate_actions', []):
            try:
                # Check approval status
                current_approval_status = self._check_action_approval_status(action)
                if action.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': action,
                        'action_source': 'borrower_immediate',
                        'approval_status': current_approval_status,
                        'risk_level': action.get('risk_level', 'unknown')
                    })
                    continue
                
                # Assign actor using LLM
                actor_assignment = self._assign_action_to_actor(action, context)
                assigned_actor = actor_assignment['assigned_actor']
                
                # Get execution decision
                execution_decision = self._llm_decide_execution(action, context, 'borrower')
                
                # Simulate actor execution
                result = self._simulate_actor_execution(assigned_actor, action, execution_decision, context)
                result['action_source'] = 'borrower_immediate'
                result['original_action'] = action
                result['actor_assignment'] = actor_assignment
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'error': str(e),
                    'action': action,
                    'action_source': 'borrower_immediate'
                })
        
        # Execute follow-ups with actor assignment
        for followup in borrower_plan.get('follow_ups', []):
            try:
                current_approval_status = self._check_action_approval_status(followup)
                if followup.get('needs_approval') and current_approval_status != 'approved':
                    results.append({
                        'status': 'skipped',
                        'reason': 'Awaiting approval',
                        'original_action': followup,
                        'action_source': 'borrower_followup',
                        'approval_status': current_approval_status,
                        'risk_level': followup.get('risk_level', 'unknown')
                    })
                    continue
                
                # Assign actor using LLM
                actor_assignment = self._assign_action_to_actor(followup, context)
                assigned_actor = actor_assignment['assigned_actor']
                
                # Get execution decision
                execution_decision = self._llm_decide_execution(followup, context, 'borrower_followup')
                
                # Simulate actor execution
                result = self._simulate_actor_execution(assigned_actor, followup, execution_decision, context)
                result['action_source'] = 'borrower_followup'
                result['original_action'] = followup
                result['actor_assignment'] = actor_assignment
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'status': 'error',
                    'error': str(e),
                    'action': followup,
                    'action_source': 'borrower_followup'
                })
        
        return results