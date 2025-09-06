"""
Integration Layer for Downstream Systems
Handles CRM updates, workflow triggers, and system automation based on analysis outputs.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from ..config import settings


class IntegrationOrchestrator:
    """
    Orchestrates integrations with downstream systems based on analysis outputs.
    Parses structured analysis and triggers appropriate system actions.
    """
    
    def __init__(self):
        self.supported_triggers = {
            'CRM_UPDATE',
            'EMAIL_TEMPLATE',
            'CALLBACK_SCHEDULE', 
            'WORKFLOW_START',
            'COMPLIANCE_ALERT',
            'SUPERVISOR_ESCALATION',
            'TRAINING_ASSIGNMENT'
        }
        
    def parse_analysis_output(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse the structured analysis output into actionable data structures.
        """
        parsed = {
            'metadata': {},
            'predictions': {},
            'actions': {
                'borrower_actions': [],
                'advisor_tasks': [],
                'supervisor_items': [],
                'leadership_insights': []
            },
            'automation_triggers': [],
            'coaching_data': {},
            'compliance_flags': []
        }
        
        try:
            # Extract metadata section
            metadata_match = re.search(r'## METADATA\n(.*?)(?=## |═══)', analysis_text, re.DOTALL)
            if metadata_match:
                metadata_text = metadata_match.group(1)
                for line in metadata_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parsed['metadata'][key.strip()] = value.strip()
            
            # Extract predictions
            predictions_match = re.search(r'## PREDICTIONS\n(.*?)(?=## |═══)', analysis_text, re.DOTALL)
            if predictions_match:
                predictions_text = predictions_match.group(1)
                for line in predictions_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parsed['predictions'][key.strip()] = value.strip()
            
            # Extract action queues
            self._parse_action_queue(analysis_text, '### BORROWER_ACTIONS', parsed['actions']['borrower_actions'])
            self._parse_action_queue(analysis_text, '### ADVISOR_TASKS', parsed['actions']['advisor_tasks'])
            self._parse_action_queue(analysis_text, '### SUPERVISOR_ITEMS', parsed['actions']['supervisor_items'])
            self._parse_action_queue(analysis_text, '### LEADERSHIP_INSIGHTS', parsed['actions']['leadership_insights'])
            
            # Extract automation triggers
            triggers_match = re.search(r'## AUTOMATION_TRIGGERS\n(.*?)(?=## |═══)', analysis_text, re.DOTALL)
            if triggers_match:
                triggers_text = triggers_match.group(1)
                parsed['automation_triggers'] = self._parse_automation_triggers(triggers_text)
            
            # Extract coaching data
            coaching_match = re.search(r'## COACHING_INTELLIGENCE\n(.*?)(?=## |═══)', analysis_text, re.DOTALL)
            if coaching_match:
                coaching_text = coaching_match.group(1)
                for line in coaching_text.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        parsed['coaching_data'][key.strip()] = value.strip()
                        
        except Exception as e:
            print(f"Warning: Error parsing analysis output: {e}")
            
        return parsed
    
    def _parse_action_queue(self, text: str, section_header: str, target_list: List[Dict]):
        """Parse action queue sections into structured data."""
        section_match = re.search(f'{section_header}\n(.*?)(?=### |## |═══)', text, re.DOTALL)
        if not section_match:
            return
            
        section_text = section_match.group(1)
        current_item = {}
        
        for line in section_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('- '):
                # New item
                if current_item:
                    target_list.append(current_item)
                # Extract main field (action, task, item, pattern)
                main_content = line[2:].strip()
                if ':' in main_content:
                    key, value = main_content.split(':', 1)
                    current_item = {key.strip(): value.strip()}
                else:
                    current_item = {'content': main_content}
            elif ':' in line:
                # Additional fields
                key, value = line.split(':', 1)
                current_item[key.strip()] = value.strip()
        
        if current_item:
            target_list.append(current_item)
    
    def _parse_automation_triggers(self, triggers_text: str) -> List[Dict[str, Any]]:
        """Parse automation triggers into structured format."""
        triggers = []
        current_trigger = {}
        
        for line in triggers_text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('- trigger:'):
                if current_trigger:
                    triggers.append(current_trigger)
                trigger_name = line.split(':', 1)[1].strip()
                current_trigger = {'trigger': trigger_name}
            elif ':' in line and current_trigger:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle JSON-like payloads
                if key in ['payload', 'variables'] and value.startswith('{'):
                    try:
                        current_trigger[key] = json.loads(value.replace("'", '"'))
                    except:
                        current_trigger[key] = value
                else:
                    current_trigger[key] = value
        
        if current_trigger:
            triggers.append(current_trigger)
            
        return triggers
    
    def execute_integrations(self, parsed_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute integrations based on parsed analysis.
        Returns execution results and status.
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'transcript_id': parsed_analysis.get('metadata', {}).get('transcript_id', 'unknown'),
            'executed_actions': [],
            'pending_approvals': [],
            'errors': []
        }
        
        # Process automation triggers
        for trigger in parsed_analysis.get('automation_triggers', []):
            try:
                result = self._execute_trigger(trigger)
                results['executed_actions'].append(result)
            except Exception as e:
                results['errors'].append(f"Trigger {trigger.get('trigger', 'unknown')}: {str(e)}")
        
        # Process high-priority actions
        self._process_urgent_actions(parsed_analysis, results)
        
        # Generate pending approvals
        self._generate_pending_approvals(parsed_analysis, results)
        
        return results
    
    def _execute_trigger(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific automation trigger."""
        trigger_type = trigger.get('trigger')
        
        if trigger_type == 'CRM_UPDATE':
            return self._execute_crm_update(trigger)
        elif trigger_type == 'EMAIL_TEMPLATE':
            return self._execute_email_template(trigger)
        elif trigger_type == 'CALLBACK_SCHEDULE':
            return self._execute_callback_schedule(trigger)
        elif trigger_type == 'WORKFLOW_START':
            return self._execute_workflow_start(trigger)
        else:
            return {
                'trigger': trigger_type,
                'status': 'unsupported',
                'message': f'Trigger type {trigger_type} not implemented'
            }
    
    def _execute_crm_update(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CRM update integration."""
        payload = trigger.get('payload', {})
        
        # Mock CRM integration - in production, this would call actual CRM APIs
        crm_update = {
            'trigger': 'CRM_UPDATE',
            'status': 'success',
            'action': 'Updated customer record',
            'fields_updated': list(payload.keys()) if payload else [],
            'timestamp': datetime.now().isoformat()
        }
        
        return crm_update
    
    def _execute_email_template(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email template integration."""
        template_id = trigger.get('template_id', 'unknown')
        variables = trigger.get('variables', {})
        
        # Mock email system integration
        email_result = {
            'trigger': 'EMAIL_TEMPLATE',
            'status': 'queued',
            'template_id': template_id,
            'variables': variables,
            'scheduled_time': datetime.now().isoformat()
        }
        
        return email_result
    
    def _execute_callback_schedule(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Execute callback scheduling integration."""
        callback_time = trigger.get('datetime', '')
        
        # Mock callback system integration
        callback_result = {
            'trigger': 'CALLBACK_SCHEDULE',
            'status': 'scheduled',
            'scheduled_time': callback_time,
            'callback_id': f"CB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        return callback_result
    
    def _execute_workflow_start(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow automation integration."""
        workflow_id = trigger.get('workflow_id', 'unknown')
        
        # Mock workflow system integration  
        workflow_result = {
            'trigger': 'WORKFLOW_START',
            'status': 'initiated',
            'workflow_id': workflow_id,
            'instance_id': f"WF_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        return workflow_result
    
    def _process_urgent_actions(self, parsed_analysis: Dict[str, Any], results: Dict[str, Any]):
        """Process urgent actions that need immediate attention."""
        for action_category in parsed_analysis.get('actions', {}).values():
            if isinstance(action_category, list):
                for action in action_category:
                    priority = action.get('priority', '').upper()
                    if priority == 'URGENT':
                        results['executed_actions'].append({
                            'type': 'urgent_action',
                            'content': action,
                            'status': 'flagged_for_immediate_attention',
                            'timestamp': datetime.now().isoformat()
                        })
    
    def _generate_pending_approvals(self, parsed_analysis: Dict[str, Any], results: Dict[str, Any]):
        """Generate pending approval items."""
        supervisor_items = parsed_analysis.get('actions', {}).get('supervisor_items', [])
        
        for item in supervisor_items:
            approval_type = item.get('approval_type', 'REVIEW')
            if approval_type in ['FEE_WAIVER', 'MODIFICATION', 'EXCEPTION', 'ESCALATION']:
                results['pending_approvals'].append({
                    'type': approval_type,
                    'content': item,
                    'created_at': datetime.now().isoformat(),
                    'approval_id': f"APP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                })


class ContinuousLearningSystem:
    """
    Implements continuous learning capabilities for the multi-agent system.
    Tracks performance, gathers feedback, and improves agent capabilities over time.
    """
    
    def __init__(self):
        self.feedback_store = []
        self.performance_metrics = {}
        
    def record_analysis_feedback(self, transcript_id: str, analysis_output: str, 
                                human_feedback: Dict[str, Any]) -> None:
        """Record human feedback on analysis quality."""
        feedback_record = {
            'timestamp': datetime.now().isoformat(),
            'transcript_id': transcript_id,
            'analysis_output': analysis_output,
            'human_feedback': human_feedback,
            'feedback_type': 'analysis_quality'
        }
        
        self.feedback_store.append(feedback_record)
    
    def record_integration_outcome(self, integration_result: Dict[str, Any], 
                                 outcome_success: bool, notes: str = "") -> None:
        """Record the outcome of integration executions."""
        outcome_record = {
            'timestamp': datetime.now().isoformat(),
            'integration_result': integration_result,
            'outcome_success': outcome_success,
            'notes': notes,
            'feedback_type': 'integration_outcome'
        }
        
        self.feedback_store.append(outcome_record)
    
    def analyze_agent_performance(self) -> Dict[str, Any]:
        """Analyze agent performance patterns from feedback."""
        if not self.feedback_store:
            return {'message': 'No feedback data available'}
            
        performance_analysis = {
            'total_feedback_items': len(self.feedback_store),
            'analysis_accuracy': self._calculate_analysis_accuracy(),
            'integration_success_rate': self._calculate_integration_success_rate(),
            'improvement_recommendations': self._generate_improvement_recommendations()
        }
        
        return performance_analysis
    
    def _calculate_analysis_accuracy(self) -> float:
        """Calculate analysis accuracy from feedback."""
        analysis_feedback = [f for f in self.feedback_store if f['feedback_type'] == 'analysis_quality']
        if not analysis_feedback:
            return 0.0
            
        accurate_count = sum(1 for f in analysis_feedback 
                           if f['human_feedback'].get('accuracy_score', 0) >= 4)
        
        return accurate_count / len(analysis_feedback)
    
    def _calculate_integration_success_rate(self) -> float:
        """Calculate integration success rate."""
        integration_feedback = [f for f in self.feedback_store if f['feedback_type'] == 'integration_outcome']
        if not integration_feedback:
            return 0.0
            
        success_count = sum(1 for f in integration_feedback if f['outcome_success'])
        
        return success_count / len(integration_feedback)
    
    def _generate_improvement_recommendations(self) -> List[str]:
        """Generate recommendations for system improvement."""
        recommendations = []
        
        accuracy = self._calculate_analysis_accuracy()
        success_rate = self._calculate_integration_success_rate()
        
        if accuracy < 0.8:
            recommendations.append("Consider refining agent instructions for better analysis accuracy")
            
        if success_rate < 0.9:
            recommendations.append("Review integration error patterns and improve error handling")
            
        return recommendations