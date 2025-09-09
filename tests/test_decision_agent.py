"""Tests for DecisionAgent - Core decision-making component for approval routing."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.agents.decision_agent import DecisionAgent, ApprovalRoute


class TestDecisionAgent:
    """Test cases for DecisionAgent functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.agent = DecisionAgent()
        
        # Sample action plan for testing
        self.test_action_plan = {
            'plan_id': 'PLAN_TEST_001',
            'transcript_id': 'CALL_TEST_001',
            'analysis_id': 'ANALYSIS_TEST_001',
            'borrower_plan': {
                'immediate_actions': [
                    {'action': 'Send confirmation email', 'description': 'Standard confirmation'},
                    {'action': 'Process payment refund', 'description': 'Refund $150 to customer'}
                ],
                'follow_ups': [
                    {'action': 'Schedule follow-up call', 'description': 'Check satisfaction'}
                ]
            },
            'advisor_plan': {
                'coaching_items': [
                    {'action': 'Review compliance procedures', 'description': 'Training on RESPA requirements'}
                ]
            },
            'supervisor_plan': {
                'escalation_items': [
                    {'action': 'Escalate payment dispute', 'description': 'Complex financial case'}
                ]
            },
            'leadership_plan': {
                'portfolio_insights': 'Customer satisfaction improving in Q3'
            }
        }
        
        # Sample analysis context
        self.analysis_context = {
            'complaint_risk': 0.6,
            'urgency_level': 'High',
            'compliance_flags': ['disclosure_required', 'RESPA'],
            'borrower_risks': {'delinquency': 0.4, 'churn': 0.3}
        }
    
    def test_agent_initialization(self):
        """Test DecisionAgent initialization."""
        agent = DecisionAgent()
        
        assert hasattr(agent, 'risk_evaluator')
        assert agent.decision_log == []
        assert 'auto_approval_threshold' in agent.config
        assert 'supervisor_threshold' in agent.config
        assert 'financial_always_supervisor' in agent.config
        assert 'compliance_always_supervisor' in agent.config
        
        # Test default configuration values
        assert agent.config['auto_approval_threshold'] == 0.3
        assert agent.config['supervisor_threshold'] == 0.7
        assert agent.config['financial_always_supervisor'] == True
        assert agent.config['compliance_always_supervisor'] == True
    
    def test_process_action_plan_complete_workflow(self):
        """Test complete action plan processing workflow."""
        result = self.agent.process_action_plan(self.test_action_plan, self.analysis_context)
        
        # Verify enhanced plan structure
        assert 'decision_agent_processed' in result
        assert result['decision_agent_processed'] == True
        assert 'processed_at' in result
        assert 'routing_decision' in result
        assert 'routing_summary' in result
        assert 'decision_agent_version' in result
        
        # Verify routing summary
        summary = result['routing_summary']
        assert 'auto_approved_actions' in summary
        assert 'advisor_approval_actions' in summary
        assert 'supervisor_approval_actions' in summary
        assert 'total_actions_processed' in summary
        
        # Verify all layers were processed
        assert 'borrower_plan' in result
        assert 'advisor_plan' in result
        assert 'supervisor_plan' in result
        assert 'leadership_plan' in result
    
    def test_borrower_layer_processing(self):
        """Test borrower layer action processing."""
        borrower_only_plan = {
            'plan_id': 'PLAN_BORROWER_001',
            'borrower_plan': {
                'immediate_actions': [
                    {'action': 'Send welcome email', 'description': 'Standard welcome message'},
                    {'action': 'Process urgent refund', 'description': 'Financial transaction requiring approval'}
                ],
                'follow_ups': [
                    {'action': 'Schedule callback', 'description': 'Customer satisfaction follow-up'}
                ]
            }
        }
        
        result = self.agent.process_action_plan(borrower_only_plan, self.analysis_context)
        
        borrower_plan = result['borrower_plan']
        
        # Check immediate actions were evaluated
        for action in borrower_plan['immediate_actions']:
            assert 'needs_approval' in action
            assert 'approval_status' in action
            assert 'risk_level' in action
            assert 'risk_score' in action
            assert 'routing_decision' in action
        
        # Check follow-ups were evaluated
        for followup in borrower_plan['follow_ups']:
            assert 'needs_approval' in followup
            assert 'approval_status' in followup
            assert 'risk_level' in followup
    
    def test_routing_decision_logic(self):
        """Test routing decision logic for different risk levels."""
        # Low risk action
        low_risk_action = {'action': 'Send standard confirmation', 'description': 'Routine communication'}
        
        # Medium risk action
        medium_risk_action = {'action': 'Update account information', 'description': 'Account modification'}
        
        # High risk action  
        high_risk_action = {'action': 'Process large refund with fee waiver', 'description': 'Complex financial transaction'}
        
        decision_context = {'plan_id': 'TEST', 'complaint_risk': 0.3}
        
        # Test routing decisions
        low_evaluated = self.agent.risk_evaluator.evaluate_action(low_risk_action, decision_context)
        low_routing = self.agent._make_routing_decision(low_evaluated, decision_context)
        
        medium_evaluated = self.agent.risk_evaluator.evaluate_action(medium_risk_action, decision_context)
        medium_routing = self.agent._make_routing_decision(medium_evaluated, decision_context)
        
        high_evaluated = self.agent.risk_evaluator.evaluate_action(high_risk_action, decision_context)
        high_routing = self.agent._make_routing_decision(high_evaluated, decision_context)
        
        # Verify routing matches risk levels
        if low_evaluated['risk_score'] < 0.3:
            assert low_routing == ApprovalRoute.AUTO_APPROVED.value
        
        if high_evaluated['risk_score'] >= 0.7:
            assert high_routing == ApprovalRoute.SUPERVISOR_APPROVAL.value
    
    def test_business_rule_overrides(self):
        """Test business rule overrides for financial and compliance actions."""
        # Financial action should always go to supervisor
        financial_action = {'action': 'Process payment adjustment', 'description': 'Financial transaction'}
        financial_evaluated = self.agent.risk_evaluator.evaluate_action(financial_action, {})
        financial_routing = self.agent._make_routing_decision(financial_evaluated, {})
        
        if financial_evaluated['financial_impact']:
            assert financial_routing == ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # Compliance action should always go to supervisor
        compliance_action = {'action': 'Send regulatory disclosure', 'description': 'Compliance requirement'}
        compliance_evaluated = self.agent.risk_evaluator.evaluate_action(compliance_action, {})
        compliance_routing = self.agent._make_routing_decision(compliance_evaluated, {})
        
        if compliance_evaluated['compliance_impact']:
            assert compliance_routing == ApprovalRoute.SUPERVISOR_APPROVAL.value
    
    def test_high_complaint_risk_override(self):
        """Test high complaint risk context override."""
        customer_facing_action = {'action': 'Call customer regarding account', 'description': 'Customer communication'}
        
        high_complaint_context = {'complaint_risk': 0.8}
        
        evaluated_action = self.agent.risk_evaluator.evaluate_action(customer_facing_action, high_complaint_context)
        routing_decision = self.agent._make_routing_decision(evaluated_action, high_complaint_context)
        
        # Customer-facing actions in high complaint risk should go to supervisor
        if evaluated_action['customer_facing'] and high_complaint_context['complaint_risk'] > 0.7:
            assert routing_decision == ApprovalRoute.SUPERVISOR_APPROVAL.value
    
    def test_plan_routing_determination(self):
        """Test overall plan routing determination."""
        # Test plan with mixed risk levels
        enhanced_plan = {
            'routing_summary': {
                'auto_approved_actions': 3,
                'advisor_approval_actions': 2, 
                'supervisor_approval_actions': 1,
                'total_actions_processed': 6
            }
        }
        
        # If any action needs supervisor approval, plan needs supervisor approval
        plan_routing = self.agent._determine_plan_routing(enhanced_plan, enhanced_plan['routing_summary'])
        assert plan_routing == ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # Test plan with only advisor approvals
        advisor_only_summary = {
            'auto_approved_actions': 2,
            'advisor_approval_actions': 3,
            'supervisor_approval_actions': 0,
            'total_actions_processed': 5
        }
        advisor_plan_routing = self.agent._determine_plan_routing({}, advisor_only_summary)
        assert advisor_plan_routing == ApprovalRoute.ADVISOR_APPROVAL.value
        
        # Test plan with only auto-approved actions
        auto_only_summary = {
            'auto_approved_actions': 4,
            'advisor_approval_actions': 0,
            'supervisor_approval_actions': 0,
            'total_actions_processed': 4
        }
        auto_plan_routing = self.agent._determine_plan_routing({}, auto_only_summary)
        assert auto_plan_routing == ApprovalRoute.AUTO_APPROVED.value
    
    def test_leadership_layer_processing(self):
        """Test leadership layer processing as single action."""
        leadership_plan = {
            'plan_id': 'PLAN_LEADERSHIP_001',
            'leadership_plan': {
                'portfolio_insights': 'Customer retention improving with new PMI removal process'
            }
        }
        
        result = self.agent.process_action_plan(leadership_plan, self.analysis_context)
        
        leadership_result = result['leadership_plan']
        
        # Leadership layer should be treated as single action
        assert 'needs_approval' in leadership_result
        assert 'approval_status' in leadership_result
        assert 'risk_level' in leadership_result
        assert 'approval_reason' in leadership_result
    
    def test_decision_logging(self):
        """Test decision logging and audit trail."""
        initial_log_count = len(self.agent.decision_log)
        
        self.agent.process_action_plan(self.test_action_plan, self.analysis_context)
        
        assert len(self.agent.decision_log) == initial_log_count + 1
        
        log_entry = self.agent.decision_log[-1]
        assert 'timestamp' in log_entry
        assert 'decision_id' in log_entry
        assert log_entry['plan_id'] == self.test_action_plan['plan_id']
        assert 'routing_decision' in log_entry
        assert 'routing_summary' in log_entry
        assert 'decision_context' in log_entry
    
    def test_decision_summary_empty(self):
        """Test decision summary with no decisions."""
        summary = self.agent.get_decision_summary()
        
        assert summary['total_decisions'] == 0
    
    def test_decision_summary_with_data(self):
        """Test decision summary generation with processed decisions."""
        # Process several action plans
        for i in range(3):
            plan = {
                'plan_id': f'PLAN_TEST_{i:03d}',
                'borrower_plan': {
                    'immediate_actions': [
                        {'action': f'Action {i}', 'description': f'Test action {i}'}
                    ]
                }
            }
            self.agent.process_action_plan(plan, self.analysis_context)
        
        summary = self.agent.get_decision_summary()
        
        assert summary['total_decisions'] == 3
        assert 'total_actions_processed' in summary
        assert 'routing_distribution' in summary
        assert 'auto_approval_rate' in summary
        assert 'avg_actions_per_plan' in summary
        assert summary['decision_agent_version'] == 'v1.0'
        
        # Verify calculations
        assert summary['auto_approval_rate'] >= 0 and summary['auto_approval_rate'] <= 100
        assert summary['avg_actions_per_plan'] >= 0
    
    def test_config_update(self):
        """Test configuration update functionality."""
        original_threshold = self.agent.config['auto_approval_threshold']
        
        new_config = {
            'auto_approval_threshold': 0.5,
            'supervisor_threshold': 0.8
        }
        
        result = self.agent.update_config(new_config)
        
        assert result['status'] == 'updated'
        assert 'old_config' in result
        assert 'new_config' in result
        assert 'updated_at' in result
        
        # Verify config was updated
        assert self.agent.config['auto_approval_threshold'] == 0.5
        assert self.agent.config['supervisor_threshold'] == 0.8
        
        # Verify old values are preserved in other settings
        assert self.agent.config['financial_always_supervisor'] == True
    
    def test_approval_route_enum(self):
        """Test ApprovalRoute enum values."""
        assert ApprovalRoute.AUTO_APPROVED.value == "auto_approved"
        assert ApprovalRoute.ADVISOR_APPROVAL.value == "advisor_approval" 
        assert ApprovalRoute.SUPERVISOR_APPROVAL.value == "supervisor_approval"
    
    def test_decision_context_creation(self):
        """Test decision context creation from action plan and analysis."""
        context = self.agent._create_decision_context(self.test_action_plan, self.analysis_context)
        
        assert context['plan_id'] == self.test_action_plan['plan_id']
        assert context['transcript_id'] == self.test_action_plan['transcript_id']
        assert context['analysis_id'] == self.test_action_plan['analysis_id']
        assert context['complaint_risk'] == self.analysis_context['complaint_risk']
        assert context['urgency_level'] == self.analysis_context['urgency_level']
        assert context['compliance_flags'] == self.analysis_context['compliance_flags']
    
    def test_empty_action_plan_processing(self):
        """Test processing of action plan with no actions."""
        empty_plan = {
            'plan_id': 'PLAN_EMPTY_001',
            'transcript_id': 'CALL_EMPTY_001',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': []},
            'advisor_plan': {'coaching_items': []},
            'supervisor_plan': {'escalation_items': []},
            'leadership_plan': {}
        }
        
        result = self.agent.process_action_plan(empty_plan, self.analysis_context)
        
        assert result['routing_summary']['total_actions_processed'] == 0
        assert result['routing_decision'] == ApprovalRoute.AUTO_APPROVED.value
        assert result['decision_agent_processed'] == True
    
    def test_single_action_processing(self):
        """Test processing of single action through the workflow."""
        action = {'action': 'Test single action', 'description': 'Testing individual processing'}
        decision_context = {'plan_id': 'TEST', 'current_layer': 'borrower'}
        routing_summary = {'total_actions_processed': 0, 'auto_approved_actions': 0, 
                          'advisor_approval_actions': 0, 'supervisor_approval_actions': 0}
        
        result = self.agent._process_single_action(action, decision_context, routing_summary)
        
        # Verify action was enhanced with decision agent fields
        assert 'needs_approval' in result
        assert 'approval_status' in result
        assert 'risk_level' in result
        assert 'risk_score' in result
        assert 'routing_decision' in result
        assert 'routed_at' in result
        
        # Verify routing summary was updated
        assert routing_summary['total_actions_processed'] == 1
    
    def test_complex_action_plan_routing(self):
        """Test complex action plan with multiple risk levels."""
        complex_plan = {
            'plan_id': 'PLAN_COMPLEX_001',
            'borrower_plan': {
                'immediate_actions': [
                    {'action': 'Send confirmation email'},  # Low risk
                    {'action': 'Process refund payment'},   # High risk - financial
                    {'action': 'Send compliance disclosure'} # High risk - compliance
                ],
                'follow_ups': [
                    {'action': 'Schedule follow-up call'}   # Medium risk
                ]
            },
            'advisor_plan': {
                'coaching_items': [
                    {'action': 'Review performance metrics'}  # Low risk
                ]
            },
            'supervisor_plan': {
                'escalation_items': [
                    {'action': 'Escalate complex case'}      # High risk
                ]
            }
        }
        
        result = self.agent.process_action_plan(complex_plan, self.analysis_context)
        
        # Should be routed to supervisor due to high-risk actions
        assert result['routing_decision'] == ApprovalRoute.SUPERVISOR_APPROVAL.value
        
        # Verify summary reflects mixed risk levels
        summary = result['routing_summary']
        assert summary['total_actions_processed'] > 0
        assert summary['supervisor_approval_actions'] > 0  # Due to financial/compliance actions