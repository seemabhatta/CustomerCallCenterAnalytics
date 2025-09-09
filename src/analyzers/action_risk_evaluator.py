"""
Action Risk Evaluator - Phase 1 Implementation
Evaluates individual action items for risk level and approval requirements.
Implements the "For Each Action Item" evaluation pattern from the Decision Agent architecture.
"""

import uuid
from typing import Dict, Any, List
from datetime import datetime


class ActionRiskEvaluator:
    """
    Evaluate individual action items for risk and approval requirements.
    This implements the first step of the Decision Agent pattern.
    """
    
    # Risk indicators by keyword categories
    FINANCIAL_KEYWORDS = [
        'refund', 'payment', 'charge', 'fee', 'credit', 'debit',
        'transaction', 'money', 'fund', 'disbursement', 'reimburse',
        'payoff', 'balance', 'adjustment', 'waive', 'forgive'
    ]
    
    COMPLIANCE_KEYWORDS = [
        'disclosure', 'regulation', 'compliance', 'audit', 'legal',
        'regulatory', 'requirement', 'mandatory', 'cfpb', 'respa',
        'tila', 'fcra', 'fdcpa', 'documentation', 'record'
    ]
    
    HIGH_RISK_ACTIONS = [
        'escalate', 'terminate', 'cancel', 'void', 'override',
        'waive', 'forgive', 'write-off', 'modify', 'change',
        'delete', 'remove', 'suspend', 'freeze', 'expedite'
    ]
    
    CUSTOMER_FACING_ACTIONS = [
        'email', 'call', 'send', 'mail', 'notify', 'contact',
        'communicate', 'inform', 'update', 'respond', 'follow-up'
    ]
    
    def __init__(self):
        self.evaluation_log = []
    
    def evaluate_action(self, action: Dict, plan_context: Dict) -> Dict:
        """
        Evaluate a single action item for risk and approval requirements.
        
        Args:
            action: Single action item from action plan
            plan_context: Context from the overall plan (risk scores, etc.)
        
        Returns:
            Enhanced action dictionary with risk assessment fields
        """
        
        # Generate unique action ID if not present
        if 'action_id' not in action:
            action['action_id'] = self._generate_action_id(action, plan_context)
        
        # Determine action classification
        action['action_type'] = self._classify_action(action)
        action['financial_impact'] = self._has_financial_impact(action)
        action['compliance_impact'] = self._has_compliance_impact(action)
        action['customer_facing'] = self._is_customer_facing(action)
        
        # Calculate individual risk score
        risk_score = self._calculate_risk_score(action, plan_context)
        
        # Determine risk level and approval requirements
        if risk_score >= 0.7:
            action['risk_level'] = 'high'
            action['needs_approval'] = True
            action['approval_status'] = 'pending'
            action['approval_reason'] = 'High risk action requires supervisor approval'
            action['auto_executable'] = False
        elif risk_score >= 0.4:
            action['risk_level'] = 'medium'
            # Medium risk inherits plan-level approval requirements
            action['needs_approval'] = plan_context.get('risk_level') == 'high'
            action['approval_status'] = 'pending' if action['needs_approval'] else 'auto_approved'
            action['approval_reason'] = self._get_medium_risk_reason(action, plan_context)
            action['auto_executable'] = not action['needs_approval']
        else:
            action['risk_level'] = 'low'
            action['needs_approval'] = False
            action['approval_status'] = 'auto_approved'
            action['approval_reason'] = 'Low risk action auto-approved'
            action['auto_executable'] = True
        
        # Apply plan-level overrides for high-risk contexts
        if plan_context.get('risk_level') == 'high' and action['customer_facing']:
            action['needs_approval'] = True
            action['approval_status'] = 'pending'
            action['approval_reason'] = f"Part of high-risk plan (complaint risk: {plan_context.get('complaint_risk', 0):.0%})"
            action['auto_executable'] = False
        
        # Add evaluation timestamp
        action['evaluated_at'] = datetime.now().isoformat()
        action['risk_score'] = round(risk_score, 3)
        
        # Log evaluation for audit
        self._log_evaluation(action, plan_context, risk_score)
        
        return action
    
    def _generate_action_id(self, action: Dict, plan_context: Dict) -> str:
        """Generate unique action ID"""
        layer = plan_context.get('current_layer', 'UNK')
        action_type = action.get('action', '')[:10].upper().replace(' ', '_')
        unique_id = uuid.uuid4().hex[:6].upper()
        return f"ACT_{layer[:4]}_{action_type}_{unique_id}"
    
    def _classify_action(self, action: Dict) -> str:
        """Classify action into type categories"""
        action_text = action.get('action', '').lower()
        
        if any(word in action_text for word in self.CUSTOMER_FACING_ACTIONS):
            return 'customer_communication'
        elif any(word in action_text for word in self.FINANCIAL_KEYWORDS):
            return 'financial_transaction'
        elif any(word in action_text for word in self.COMPLIANCE_KEYWORDS):
            return 'compliance_action'
        elif 'train' in action_text or 'coach' in action_text:
            return 'training_action'
        elif 'escalate' in action_text or 'supervisor' in action_text:
            return 'escalation_action'
        else:
            return 'general_action'
    
    def _has_financial_impact(self, action: Dict) -> bool:
        """Check if action has financial implications"""
        action_text = action.get('action', '').lower()
        description = action.get('description', '').lower()
        
        return any(
            keyword in text 
            for text in [action_text, description]
            for keyword in self.FINANCIAL_KEYWORDS
        )
    
    def _has_compliance_impact(self, action: Dict) -> bool:
        """Check if action has compliance implications"""
        action_text = action.get('action', '').lower()
        description = action.get('description', '').lower()
        
        return any(
            keyword in text 
            for text in [action_text, description]
            for keyword in self.COMPLIANCE_KEYWORDS
        )
    
    def _is_customer_facing(self, action: Dict) -> bool:
        """Check if action directly impacts customer"""
        action_text = action.get('action', '').lower()
        description = action.get('description', '').lower()
        
        return any(
            keyword in text 
            for text in [action_text, description]
            for keyword in self.CUSTOMER_FACING_ACTIONS
        )
    
    def _calculate_risk_score(self, action: Dict, plan_context: Dict) -> float:
        """
        Calculate 0-1 risk score for individual action.
        
        Risk factors:
        - Financial impact: +0.4
        - Compliance impact: +0.3  
        - High-risk action type: +0.3
        - Customer-facing + high complaint risk: +0.2
        - High urgency context: +0.1 multiplier
        """
        score = 0.0
        
        # Base risk factors
        if action['financial_impact']:
            score += 0.4
        
        if action['compliance_impact']:
            score += 0.3
        
        # Check for high-risk action keywords
        action_text = action.get('action', '').lower()
        if any(risk_word in action_text for risk_word in self.HIGH_RISK_ACTIONS):
            score += 0.3
        
        # Customer-facing risk in high complaint contexts
        if action['customer_facing'] and plan_context.get('complaint_risk', 0) > 0.6:
            score += 0.2
        
        # Priority multipliers
        if action.get('priority') == 'urgent':
            score *= 1.2
        
        # Context multipliers
        if plan_context.get('urgency_level') == 'High':
            score *= 1.1
        
        if len(plan_context.get('compliance_flags', [])) > 0:
            score *= 1.15
        
        return min(score, 1.0)
    
    def _get_medium_risk_reason(self, action: Dict, plan_context: Dict) -> str:
        """Get explanation for medium risk approval decision"""
        if action['needs_approval']:
            return f"Medium risk action in high-risk plan context (plan risk: {plan_context.get('risk_level')})"
        else:
            return "Medium risk action auto-approved in low-risk context"
    
    def _log_evaluation(self, action: Dict, plan_context: Dict, risk_score: float):
        """Log evaluation for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_id': action['action_id'],
            'action_text': action.get('action', ''),
            'risk_score': risk_score,
            'risk_level': action['risk_level'],
            'needs_approval': action['needs_approval'],
            'financial_impact': action['financial_impact'],
            'compliance_impact': action['compliance_impact'],
            'customer_facing': action['customer_facing'],
            'plan_context': {
                'plan_risk_level': plan_context.get('risk_level'),
                'complaint_risk': plan_context.get('complaint_risk'),
                'compliance_flags_count': len(plan_context.get('compliance_flags', []))
            }
        }
        
        self.evaluation_log.append(log_entry)
    
    def get_evaluation_summary(self) -> Dict:
        """Get summary of all evaluations performed"""
        if not self.evaluation_log:
            return {'total_evaluations': 0}
        
        total = len(self.evaluation_log)
        needs_approval = sum(1 for e in self.evaluation_log if e['needs_approval'])
        auto_approved = total - needs_approval
        
        risk_levels = {}
        for entry in self.evaluation_log:
            level = entry['risk_level']
            risk_levels[level] = risk_levels.get(level, 0) + 1
        
        return {
            'total_evaluations': total,
            'needs_approval': needs_approval,
            'auto_approved': auto_approved,
            'approval_rate': (needs_approval / total) * 100 if total > 0 else 0,
            'risk_level_distribution': risk_levels,
            'avg_risk_score': sum(e['risk_score'] for e in self.evaluation_log) / total if total > 0 else 0
        }