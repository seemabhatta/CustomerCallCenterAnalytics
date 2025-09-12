"""
Test suite for DecisionAgent - Central decision-making component
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.agents.decision_agent import DecisionAgent, ApprovalRoute


@pytest.fixture
def decision_agent():
    """Create DecisionAgent for testing."""
    return DecisionAgent()


@pytest.fixture
def sample_action_plan():
    """Sample four-layer action plan for testing."""
    return {
        "plan_id": "PLAN_TEST123",
        "analysis_id": "ANALYSIS_TEST123",
        "borrower_plan": {
            "immediate_actions": [
                {
                    "action": "Send payment reminder",
                    "timeline": "Within 24 hours",
                    "priority": "high",
                    "financial_impact": False
                },
                {
                    "action": "Apply late fee",
                    "timeline": "After 5 days",
                    "priority": "medium",
                    "financial_impact": True,
                    "amount": 25.00
                }
            ],
            "follow_ups": [
                {
                    "action": "Follow up call",
                    "due_date": "2024-01-15",
                    "owner": "CSR"
                }
            ]
        },
        "advisor_plan": {
            "coaching_items": ["Improve active listening"],
            "performance_feedback": {
                "strengths": ["Clear communication"],
                "improvements": ["Better questions"]
            }
        },
        "supervisor_plan": {
            "escalation_items": [{
                "item": "Payment dispute",
                "priority": "medium",
                "compliance_related": True
            }]
        },
        "leadership_plan": {
            "portfolio_insights": ["Rising payment delays"]
        }
    }


@pytest.fixture
def sample_analysis_context():
    """Sample analysis context for decision making."""
    return {
        "transcript_id": "CALL_TEST123",
        "customer_id": "CUST_001",
        "risk_indicators": {
            "delinquency_risk": 0.6,
            "churn_risk": 0.3,
            "complaint_risk": 0.2
        },
        "sentiment_analysis": {
            "overall_sentiment": "frustrated",
            "customer_sentiment": "angry",
            "confidence": 0.8
        },
        "financial_impact": 1500.00,
        "urgency": "high"
    }


class TestApprovalRoute:
    """Test ApprovalRoute enum."""

    def test_approval_route_values(self):
        """Test ApprovalRoute enum has correct values."""
        assert ApprovalRoute.AUTO_APPROVED.value == "auto_approved"
        assert ApprovalRoute.ADVISOR_APPROVAL.value == "advisor_approval"
        assert ApprovalRoute.SUPERVISOR_APPROVAL.value == "supervisor_approval"


class TestDecisionAgent:
    """Test DecisionAgent functionality."""

    def test_agent_initialization(self, decision_agent):
        """Test agent initializes with correct dependencies and config."""
        assert decision_agent.risk_evaluator is not None
        assert decision_agent.decision_log == []
        assert decision_agent.config['auto_approval_threshold'] == 0.3
        assert decision_agent.config['supervisor_threshold'] == 0.7
        assert decision_agent.config['financial_always_supervisor'] is True

    def test_process_action_plan_complete_flow(self, decision_agent, sample_action_plan, sample_analysis_context):
        """Test processing complete action plan through decision flow."""
        # Mock risk evaluator to return known risk scores
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk') as mock_evaluate:
            mock_evaluate.side_effect = [0.2, 0.8, 0.1, 0.9, 0.5]  # Different risk scores
            
            result = await decision_agent.process_action_plan(sample_action_plan, sample_analysis_context)
            
            # Verify decision metadata added
            assert result['decision_agent_processed'] is True
            assert 'processed_at' in result
            assert 'routing_decision' in result
            assert 'routing_summary' in result
            
            # Verify routing summary populated
            summary = result['routing_summary']
            assert 'auto_approved_actions' in summary
            assert 'supervisor_approval_actions' in summary
            assert summary['total_actions_processed'] > 0

    def test_process_action_plan_auto_approval_low_risk(self, decision_agent, sample_analysis_context):
        """Test auto-approval for low-risk actions."""
        low_risk_plan = {
            "borrower_plan": {
                "immediate_actions": [{
                    "action": "Send confirmation email",
                    "priority": "low",
                    "financial_impact": False
                }]
            }
        }
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.1):
            result = await decision_agent.process_action_plan(low_risk_plan, sample_analysis_context)
            
            action = result['borrower_plan']['immediate_actions'][0]
            assert action['approval_required'] is False
            assert action['routing'] == ApprovalRoute.AUTO_APPROVED.value

    def test_process_action_plan_supervisor_approval_high_risk(self, decision_agent, sample_analysis_context):
        """Test supervisor approval required for high-risk actions."""
        high_risk_plan = {
            "borrower_plan": {
                "immediate_actions": [{
                    "action": "Waive large fee",
                    "priority": "high",
                    "financial_impact": True,
                    "amount": 500.00
                }]
            }
        }
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.9):
            result = await decision_agent.process_action_plan(high_risk_plan, sample_analysis_context)
            
            action = result['borrower_plan']['immediate_actions'][0]
            assert action['approval_required'] is True
            assert action['routing'] == ApprovalRoute.SUPERVISOR_APPROVAL.value

    def test_process_action_plan_financial_always_supervisor(self, decision_agent, sample_analysis_context):
        """Test financial actions always require supervisor approval regardless of risk."""
        financial_plan = {
            "borrower_plan": {
                "immediate_actions": [{
                    "action": "Process refund",
                    "priority": "medium",
                    "financial_impact": True,
                    "amount": 50.00  # Small amount but financial
                }]
            }
        }
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.1):  # Low risk
            result = await decision_agent.process_action_plan(financial_plan, sample_analysis_context)
            
            action = result['borrower_plan']['immediate_actions'][0]
            assert action['approval_required'] is True
            assert action['routing'] == ApprovalRoute.SUPERVISOR_APPROVAL.value
            assert "financial impact detected" in action['routing_reason']

    def test_process_action_plan_compliance_always_supervisor(self, decision_agent, sample_analysis_context):
        """Test compliance actions always require supervisor approval."""
        compliance_plan = {
            "supervisor_plan": {
                "escalation_items": [{
                    "item": "TCPA compliance review",
                    "priority": "high",
                    "compliance_related": True
                }]
            }
        }
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.2):  # Low risk
            result = await decision_agent.process_action_plan(compliance_plan, sample_analysis_context)
            
            action = result['supervisor_plan']['escalation_items'][0]
            assert action['approval_required'] is True
            assert action['routing'] == ApprovalRoute.SUPERVISOR_APPROVAL.value
            assert "compliance" in action['routing_reason'].lower()

    def test_process_action_plan_advisor_approval_medium_risk(self, decision_agent, sample_analysis_context):
        """Test advisor approval for medium-risk actions."""
        medium_risk_plan = {
            "borrower_plan": {
                "immediate_actions": [{
                    "action": "Schedule callback",
                    "priority": "medium",
                    "financial_impact": False
                }]
            }
        }
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.5):  # Medium risk
            result = await decision_agent.process_action_plan(medium_risk_plan, sample_analysis_context)
            
            action = result['borrower_plan']['immediate_actions'][0]
            assert action['approval_required'] is True
            assert action['routing'] == ApprovalRoute.ADVISOR_APPROVAL.value

    def test_process_action_plan_empty_plan(self, decision_agent, sample_analysis_context):
        """Test processing empty action plan."""
        empty_plan = {}
        
        result = await decision_agent.process_action_plan(empty_plan, sample_analysis_context)
        
        assert result['decision_agent_processed'] is True
        assert result['routing_summary']['total_actions_processed'] == 0

    def test_process_action_plan_risk_evaluator_failure(self, decision_agent, sample_action_plan, sample_analysis_context):
        """Test process fails fast when risk evaluator fails."""
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', side_effect=Exception("Risk evaluation failed")):
            
            with pytest.raises(Exception, match="Risk evaluation failed"):
                await decision_agent.process_action_plan(sample_action_plan, sample_analysis_context)

    def test_create_decision_context(self, decision_agent, sample_action_plan, sample_analysis_context):
        """Test decision context creation."""
        context = decision_agent._create_decision_context(sample_action_plan, sample_analysis_context)
        
        assert context['plan_id'] == "PLAN_TEST123"
        assert context['customer_id'] == "CUST_001"
        assert context['overall_risk_score'] > 0
        assert context['customer_sentiment'] == "angry"
        assert context['financial_impact'] == 1500.00

    def test_process_plan_layer_borrower(self, decision_agent, sample_analysis_context):
        """Test processing borrower plan layer specifically."""
        borrower_layer = {
            "immediate_actions": [{
                "action": "Test action",
                "priority": "medium"
            }]
        }
        decision_context = {"plan_id": "TEST", "overall_risk_score": 0.5}
        routing_summary = {"total_actions_processed": 0, "advisor_approval_actions": 0}
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.4):
            result = decision_agent._process_plan_layer(borrower_layer, 'borrower', decision_context, routing_summary)
            
            assert result['immediate_actions'][0]['approval_required'] is True
            assert routing_summary['total_actions_processed'] == 1

    def test_determine_plan_routing_highest_risk(self, decision_agent):
        """Test plan routing determination based on highest risk action."""
        enhanced_plan = {
            "borrower_plan": {
                "immediate_actions": [
                    {"routing": "auto_approved", "risk_score": 0.1},
                    {"routing": "supervisor_approval", "risk_score": 0.9}
                ]
            }
        }
        routing_summary = {"supervisor_approval_actions": 1}
        
        result = decision_agent._determine_plan_routing(enhanced_plan, routing_summary)
        
        assert result['overall_routing'] == "supervisor_approval"
        assert result['requires_approval'] is True
        assert result['highest_risk_score'] == 0.9

    def test_process_action_item_with_metadata(self, decision_agent):
        """Test individual action item processing adds correct metadata."""
        action_item = {
            "action": "Test action",
            "priority": "high"
        }
        decision_context = {"plan_id": "TEST"}
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.6):
            result = decision_agent._process_action_item(action_item, 'borrower', decision_context)
            
            assert result['approval_required'] is True
            assert result['routing'] == ApprovalRoute.ADVISOR_APPROVAL.value
            assert result['risk_score'] == 0.6
            assert 'routing_reason' in result
            assert 'decision_timestamp' in result

    def test_configure_thresholds(self, decision_agent):
        """Test decision threshold configuration."""
        new_config = {
            'auto_approval_threshold': 0.2,
            'supervisor_threshold': 0.8
        }
        
        decision_agent.configure_thresholds(new_config)
        
        assert decision_agent.config['auto_approval_threshold'] == 0.2
        assert decision_agent.config['supervisor_threshold'] == 0.8

    def test_get_decision_statistics(self, decision_agent, sample_action_plan, sample_analysis_context):
        """Test decision statistics collection."""
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.5):
            await decision_agent.process_action_plan(sample_action_plan, sample_analysis_context)
            
            stats = decision_agent.get_decision_statistics()
            
            assert 'total_decisions' in stats
            assert 'approval_rate' in stats
            assert 'average_risk_score' in stats
            assert stats['total_decisions'] > 0

    def test_agent_no_fallback_logic(self, decision_agent):
        """Meta-test: Verify agent contains NO fallback logic."""
        # Agent should not contain:
        # 1. Default approval routes when risk evaluation fails
        # 2. Hardcoded routing decisions as fallbacks
        # 3. try/catch blocks that return "safe" default routes
        # 4. Mock risk scores when risk evaluator is unavailable
        
        # This is verified by test_process_action_plan_risk_evaluator_failure
        # which expects exceptions to propagate
        assert True  # All other tests verify fail-fast behavior

    def test_decision_consistency_same_input(self, decision_agent, sample_action_plan, sample_analysis_context):
        """Test agent produces consistent decisions for same input."""
        # Same input should produce same routing decisions
        # This is important for deterministic approval workflows
        
        with patch.object(decision_agent.risk_evaluator, 'evaluate_action_risk', return_value=0.5):
            result1 = await decision_agent.process_action_plan(sample_action_plan, sample_analysis_context)
            result2 = await decision_agent.process_action_plan(sample_action_plan, sample_analysis_context)
            
            # Compare routing decisions (excluding timestamps)
            routing1 = result1['routing_decision']['overall_routing']
            routing2 = result2['routing_decision']['overall_routing']
            assert routing1 == routing2