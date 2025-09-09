"""
Decision Agent - Phase 2 Implementation
Implements the central decision-making component from the Decision Agent architecture.
Manages the "For Each Action Item → Needs Approval? → Route" workflow.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

from src.analyzers.action_risk_evaluator import ActionRiskEvaluator


class ApprovalRoute(Enum):
    """Approval routing options"""
    AUTO_APPROVED = "auto_approved"
    ADVISOR_APPROVAL = "advisor_approval"
    SUPERVISOR_APPROVAL = "supervisor_approval"


class DecisionAgent:
    """
    Core Decision Agent that implements the architecture pattern:
    "For Each Action Item → Needs Approval? → Route"
    
    This agent processes action plans and makes routing decisions based on
    risk assessment, compliance requirements, and business rules.
    """
    
    def __init__(self):
        """Initialize the Decision Agent"""
        self.risk_evaluator = ActionRiskEvaluator()
        self.decision_log = []
        
        # Decision thresholds (configurable)
        self.config = {
            'auto_approval_threshold': 0.3,     # Risk score below this = auto approve
            'supervisor_threshold': 0.7,        # Risk score above this = supervisor approval
            'financial_always_supervisor': True, # Financial actions always need supervisor
            'compliance_always_supervisor': True # Compliance actions always need supervisor
        }
    
    def process_action_plan(self, action_plan: Dict[str, Any], analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an entire action plan through the Decision Agent workflow.
        
        Args:
            action_plan: Complete four-layer action plan
            analysis_context: Context from call analysis for decision making
            
        Returns:
            Enhanced action plan with routing decisions and approval requirements
        """
        
        # Create decision context
        decision_context = self._create_decision_context(action_plan, analysis_context)
        
        # Process each layer of the action plan
        enhanced_plan = action_plan.copy()
        routing_summary = {
            'auto_approved_actions': 0,
            'advisor_approval_actions': 0,
            'supervisor_approval_actions': 0,
            'total_actions_processed': 0
        }
        
        # Process borrower plan
        if 'borrower_plan' in action_plan:
            enhanced_plan['borrower_plan'] = self._process_plan_layer(
                action_plan['borrower_plan'], 'borrower', decision_context, routing_summary
            )
        
        # Process advisor plan
        if 'advisor_plan' in action_plan:
            enhanced_plan['advisor_plan'] = self._process_plan_layer(
                action_plan['advisor_plan'], 'advisor', decision_context, routing_summary
            )
        
        # Process supervisor plan
        if 'supervisor_plan' in action_plan:
            enhanced_plan['supervisor_plan'] = self._process_plan_layer(
                action_plan['supervisor_plan'], 'supervisor', decision_context, routing_summary
            )
        
        # Process leadership plan
        if 'leadership_plan' in action_plan:
            enhanced_plan['leadership_plan'] = self._process_plan_layer(
                action_plan['leadership_plan'], 'leadership', decision_context, routing_summary
            )
        
        # Determine overall plan routing based on highest risk action
        plan_routing = self._determine_plan_routing(enhanced_plan, routing_summary)
        
        # Add decision metadata to plan
        enhanced_plan.update({
            'decision_agent_processed': True,
            'processed_at': datetime.now().isoformat(),
            'routing_decision': plan_routing,
            'routing_summary': routing_summary,
            'decision_agent_version': 'v1.0'
        })
        
        # Log the decision for audit
        self._log_decision(enhanced_plan, decision_context, routing_summary)
        
        return enhanced_plan
    
    def _create_decision_context(self, action_plan: Dict[str, Any], analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create decision context for the agent"""
        return {
            'plan_id': action_plan.get('plan_id'),
            'transcript_id': action_plan.get('transcript_id'),
            'analysis_id': action_plan.get('analysis_id'),
            'complaint_risk': analysis_context.get('complaint_risk', 0),
            'urgency_level': analysis_context.get('urgency_level', 'Medium'),
            'compliance_flags': analysis_context.get('compliance_flags', []),
            'borrower_risks': analysis_context.get('borrower_risks', {}),
            'current_layer': None  # Will be set per layer
        }
    
    def _process_plan_layer(self, plan_layer: Dict[str, Any], layer_name: str, 
                           decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single layer of the action plan"""
        
        enhanced_layer = plan_layer.copy()
        decision_context['current_layer'] = layer_name
        
        # Process different action types based on layer structure
        if layer_name == 'borrower':
            enhanced_layer = self._process_borrower_layer(enhanced_layer, decision_context, routing_summary)
        elif layer_name == 'advisor':
            enhanced_layer = self._process_advisor_layer(enhanced_layer, decision_context, routing_summary)
        elif layer_name == 'supervisor':
            enhanced_layer = self._process_supervisor_layer(enhanced_layer, decision_context, routing_summary)
        elif layer_name == 'leadership':
            enhanced_layer = self._process_leadership_layer(enhanced_layer, decision_context, routing_summary)
        
        return enhanced_layer
    
    def _process_borrower_layer(self, borrower_layer: Dict[str, Any], 
                               decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process borrower layer actions"""
        
        # Process immediate actions
        if 'immediate_actions' in borrower_layer:
            borrower_layer['immediate_actions'] = [
                self._process_single_action(action, decision_context, routing_summary)
                for action in borrower_layer['immediate_actions']
            ]
        
        # Process follow-ups
        if 'follow_ups' in borrower_layer:
            borrower_layer['follow_ups'] = [
                self._process_single_action(followup, decision_context, routing_summary)
                for followup in borrower_layer['follow_ups']
            ]
        
        return borrower_layer
    
    def _process_advisor_layer(self, advisor_layer: Dict[str, Any], 
                              decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process advisor layer actions"""
        
        # Process coaching items
        if 'coaching_items' in advisor_layer:
            advisor_layer['coaching_items'] = [
                self._process_single_action(coaching_item, decision_context, routing_summary)
                for coaching_item in advisor_layer['coaching_items']
            ]
        
        return advisor_layer
    
    def _process_supervisor_layer(self, supervisor_layer: Dict[str, Any], 
                                 decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process supervisor layer actions"""
        
        # Process escalation items
        if 'escalation_items' in supervisor_layer:
            supervisor_layer['escalation_items'] = [
                self._process_single_action(escalation, decision_context, routing_summary)
                for escalation in supervisor_layer['escalation_items']
            ]
        
        return supervisor_layer
    
    def _process_leadership_layer(self, leadership_layer: Dict[str, Any], 
                                 decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Process leadership layer actions"""
        
        # For leadership layer, treat the entire insights generation as one action
        if leadership_layer.get('portfolio_insights'):
            leadership_action = {
                'action': 'Generate portfolio insights report',
                'description': f"Strategic insights based on call analysis: {leadership_layer.get('portfolio_insights')}"
            }
            
            processed_action = self._process_single_action(leadership_action, decision_context, routing_summary)
            
            # Apply the decision results to the layer
            leadership_layer.update({
                'needs_approval': processed_action['needs_approval'],
                'approval_status': processed_action['approval_status'],
                'risk_level': processed_action['risk_level'],
                'approval_reason': processed_action['approval_reason']
            })
        
        return leadership_layer
    
    def _process_single_action(self, action: Dict[str, Any], 
                              decision_context: Dict[str, Any], routing_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single action through the Decision Agent workflow.
        This is the core "For Each Action Item → Needs Approval? → Route" logic.
        """
        
        # Step 1: Evaluate the action for risk
        evaluated_action = self.risk_evaluator.evaluate_action(action, decision_context)
        
        # Step 2: Make routing decision based on risk and business rules
        routing_decision = self._make_routing_decision(evaluated_action, decision_context)
        
        # Step 3: Apply routing decision to action
        evaluated_action.update({
            'routing_decision': routing_decision,
            'routed_at': datetime.now().isoformat()
        })
        
        # Step 4: Update routing summary
        routing_summary['total_actions_processed'] += 1
        if routing_decision == ApprovalRoute.AUTO_APPROVED.value:
            routing_summary['auto_approved_actions'] += 1
        elif routing_decision == ApprovalRoute.ADVISOR_APPROVAL.value:
            routing_summary['advisor_approval_actions'] += 1
        elif routing_decision == ApprovalRoute.SUPERVISOR_APPROVAL.value:
            routing_summary['supervisor_approval_actions'] += 1
        
        return evaluated_action
    
    def _make_routing_decision(self, evaluated_action: Dict[str, Any], 
                              decision_context: Dict[str, Any]) -> str:
        """
        Make the core routing decision: Auto Approve vs Advisor vs Supervisor.
        This implements the "Needs Approval? → Route" logic.
        """
        
        risk_score = evaluated_action.get('risk_score', 0)
        
        # Business rule overrides (highest priority)
        if self.config['financial_always_supervisor'] and evaluated_action.get('financial_impact'):
            return ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        if self.config['compliance_always_supervisor'] and evaluated_action.get('compliance_impact'):
            return ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # High complaint risk context override
        if decision_context.get('complaint_risk', 0) > 0.7 and evaluated_action.get('customer_facing'):
            return ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # Risk score-based routing
        if risk_score >= self.config['supervisor_threshold']:
            return ApprovalRoute.SUPERVISOR_APPROVAL.value
        elif risk_score >= self.config['auto_approval_threshold']:
            return ApprovalRoute.ADVISOR_APPROVAL.value
        else:
            return ApprovalRoute.AUTO_APPROVED.value
    
    def _determine_plan_routing(self, enhanced_plan: Dict[str, Any], 
                               routing_summary: Dict[str, Any]) -> str:
        """Determine overall plan routing based on constituent actions"""
        
        # If any action needs supervisor approval, entire plan needs supervisor approval
        if routing_summary['supervisor_approval_actions'] > 0:
            return ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # If any action needs advisor approval, plan needs advisor approval
        elif routing_summary['advisor_approval_actions'] > 0:
            return ApprovalRoute.ADVISOR_APPROVAL.value
        
        # Otherwise, plan can be auto-approved
        else:
            return ApprovalRoute.AUTO_APPROVED.value
    
    def _log_decision(self, enhanced_plan: Dict[str, Any], decision_context: Dict[str, Any], 
                     routing_summary: Dict[str, Any]):
        """Log decision for audit trail"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'decision_id': f"DEC_{uuid.uuid4().hex[:8].upper()}",
            'plan_id': enhanced_plan.get('plan_id'),
            'transcript_id': decision_context.get('transcript_id'),
            'analysis_id': decision_context.get('analysis_id'),
            'routing_decision': enhanced_plan.get('routing_decision'),
            'routing_summary': routing_summary,
            'decision_context': {
                'complaint_risk': decision_context.get('complaint_risk'),
                'urgency_level': decision_context.get('urgency_level'),
                'compliance_flags_count': len(decision_context.get('compliance_flags', []))
            }
        }
        
        self.decision_log.append(log_entry)
    
    def get_decision_summary(self) -> Dict[str, Any]:
        """Get summary of all decisions made"""
        
        if not self.decision_log:
            return {'total_decisions': 0}
        
        total = len(self.decision_log)
        
        # Aggregate routing decisions
        routing_counts = {}
        for entry in self.decision_log:
            route = entry['routing_decision']
            routing_counts[route] = routing_counts.get(route, 0) + 1
        
        # Calculate approval rates
        total_actions = sum(entry['routing_summary']['total_actions_processed'] for entry in self.decision_log)
        auto_approved = sum(entry['routing_summary']['auto_approved_actions'] for entry in self.decision_log)
        
        return {
            'total_decisions': total,
            'total_actions_processed': total_actions,
            'routing_distribution': routing_counts,
            'auto_approval_rate': round((auto_approved / total_actions) * 100, 1) if total_actions > 0 else 0,
            'avg_actions_per_plan': round(total_actions / total, 1) if total > 0 else 0,
            'decision_agent_version': 'v1.0'
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update decision agent configuration"""
        
        old_config = self.config.copy()
        self.config.update(new_config)
        
        return {
            'status': 'updated',
            'old_config': old_config,
            'new_config': self.config,
            'updated_at': datetime.now().isoformat()
        }