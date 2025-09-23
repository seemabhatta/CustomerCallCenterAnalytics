"""Tests for RiskAssessmentAgent - LLM-based risk evaluation and routing.

Following TDD principles and NO FALLBACK approach:
- Test LLM integration and response parsing
- Validate risk level determination
- Test approver role routing logic
- Context completeness validation
- NO FALLBACK enforcement throughout
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from typing import Dict, Any

from src.call_center_agents.risk_assessment_agent import RiskAssessmentAgent


class TestRiskAssessmentAgent:
    """Test RiskAssessmentAgent LLM-based risk evaluation with NO FALLBACK validation."""
    
    @pytest.fixture
    def risk_agent(self):
        """Create RiskAssessmentAgent instance with test API key."""
        return RiskAssessmentAgent(api_key="test_api_key")
    
    @pytest.fixture
    def sample_workflow_context(self):
        """Sample workflow context for risk assessment."""
        return {
            "transcript": {
                "customer_id": "CUST_TEST_001",
                "topic": "Payment assistance request",
                "sentiment": "concerned",
                "duration_minutes": 15,
                "summary": "Customer lost job, needs payment plan"
            },
            "analysis": {
                "primary_intent": "payment_assistance",
                "urgency_level": "high",
                "risk_score": 0.7,
                "compliance_flags": ["PAYMENT_PLAN", "HARDSHIP_PROGRAM"],
                "borrower_risks": {
                    "delinquency_risk": 0.8,
                    "default_probability": 0.3
                },
                "advisor_performance": {
                    "empathy_score": 0.9,
                    "compliance_score": 0.8
                }
            },
            "insights": {
                "similar_case_outcomes": "85% success rate for similar hardship cases",
                "typical_approval_time": "2.5 hours",
                "escalation_rate": "12%"
            },
            "action": {
                "type": "payment_plan",
                "description": "Offer 3-month payment deferral",
                "estimated_financial_impact": 15000,
                "auto_executable": False,
                "priority": "high",
                "compliance_requirements": ["HARDSHIP_VALIDATION", "INCOME_VERIFICATION"]
            }
        }
    
    @pytest.fixture
    def sample_llm_response(self):
        """Sample LLM response for risk assessment."""
        return {
            "risk_level": "MEDIUM",
            "confidence_score": 0.85,
            "approver_role": "SUPERVISOR",
            "reasoning": "High financial impact ($15K) and compliance requirements necessitate supervisor approval",
            "key_factors": [
                "Financial impact exceeds advisor threshold",
                "Hardship program requires specialized approval",
                "Customer shows genuine need with documentation"
            ],
            "estimated_approval_time": "2-4 hours",
            "escalation_triggers": [
                "If customer provides insufficient documentation",
                "If payment history shows concerning patterns"
            ],
            "recommended_conditions": [
                "Verify income documentation",
                "Review last 12 months payment history",
                "Confirm hardship eligibility"
            ]
        }
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = Mock()
        mock_response = Mock()
        mock_output = Mock()
        mock_content = Mock()
        
        # Chain the mock response structure
        mock_client.responses.create.return_value = mock_response
        mock_response.output = [mock_output]
        mock_output.content = [mock_content]
        
        return mock_client, mock_content
    
    async def test_assess_risk_success_medium_risk(self, risk_agent, sample_workflow_context, 
                                                  sample_llm_response, mock_openai_client):
        """Test successful risk assessment for medium risk scenario."""
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(sample_llm_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            assessment = await risk_agent.assess_risk(sample_workflow_context)
        
        # Verify assessment structure
        assert assessment["risk_level"] == "MEDIUM"
        assert assessment["confidence_score"] == 0.85
        assert assessment["approver_role"] == "SUPERVISOR"
        assert "reasoning" in assessment
        assert "key_factors" in assessment
        assert isinstance(assessment["key_factors"], list)
        
        # Verify OpenAI was called correctly
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args
        assert call_args[1]["model"] == "gpt-4.1"
        assert "temperature" in call_args[1]
        assert call_args[1]["temperature"] <= 0.5  # Should be low for consistent assessment
    
    async def test_assess_risk_success_low_risk(self, risk_agent, mock_openai_client):
        """Test successful risk assessment for low risk scenario."""
        low_risk_context = {
            "transcript": {
                "customer_id": "CUST_LOW_001",
                "topic": "Rate inquiry",
                "sentiment": "curious",
                "duration_minutes": 5
            },
            "analysis": {
                "primary_intent": "information_request",
                "urgency_level": "low",
                "risk_score": 0.2,
                "compliance_flags": [],
                "borrower_risks": {}
            },
            "action": {
                "type": "send_information",
                "description": "Email current rates",
                "estimated_financial_impact": 0,
                "auto_executable": True,
                "compliance_requirements": []
            }
        }
        
        low_risk_response = {
            "risk_level": "LOW",
            "confidence_score": 0.95,
            "approver_role": "AUTO",
            "reasoning": "Routine information request with no financial impact",
            "key_factors": ["No financial commitment", "Standard information sharing"],
            "estimated_approval_time": "immediate",
            "recommended_conditions": []
        }
        
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(low_risk_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            assessment = await risk_agent.assess_risk(low_risk_context)
        
        assert assessment["risk_level"] == "LOW"
        assert assessment["approver_role"] == "AUTO"
        assert assessment["confidence_score"] == 0.95
    
    async def test_assess_risk_success_high_risk(self, risk_agent, mock_openai_client):
        """Test successful risk assessment for high risk scenario."""
        high_risk_context = {
            "transcript": {
                "customer_id": "CUST_HIGH_001",
                "topic": "Foreclosure assistance",
                "sentiment": "desperate",
                "duration_minutes": 30
            },
            "analysis": {
                "primary_intent": "foreclosure_prevention",
                "urgency_level": "critical",
                "risk_score": 0.9,
                "compliance_flags": ["LEGAL_REVIEW", "EXECUTIVE_APPROVAL"],
                "borrower_risks": {
                    "foreclosure_risk": 0.95
                }
            },
            "action": {
                "type": "foreclosure_hold",
                "description": "Place 60-day foreclosure hold",
                "estimated_financial_impact": 250000,
                "auto_executable": False,
                "compliance_requirements": ["LEGAL_REVIEW", "EXECUTIVE_APPROVAL"]
            }
        }
        
        high_risk_response = {
            "risk_level": "HIGH",
            "confidence_score": 0.92,
            "approver_role": "COMPLIANCE",
            "reasoning": "Major financial exposure with legal implications requires compliance approval",
            "key_factors": [
                "Significant financial impact ($250K)",
                "Legal and regulatory requirements",
                "Foreclosure prevention complexity"
            ],
            "estimated_approval_time": "4-8 hours",
            "recommended_conditions": [
                "Legal team review required",
                "Executive approval needed",
                "Compliance documentation"
            ]
        }
        
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(high_risk_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            assessment = await risk_agent.assess_risk(high_risk_context)
        
        assert assessment["risk_level"] == "HIGH"
        assert assessment["approver_role"] == "COMPLIANCE"
        assert assessment["confidence_score"] == 0.92
    
    async def test_assess_risk_fails_missing_context(self, risk_agent):
        """Test assess_risk fails with missing required context - NO FALLBACK."""
        incomplete_context = {
            "action": {"type": "unknown"}
            # Missing transcript, analysis, etc.
        }
        
        with pytest.raises(ValueError) as exc_info:
            await risk_agent.assess_risk(incomplete_context)
        
        assert "Missing required context" in str(exc_info.value)
    
    async def test_assess_risk_fails_empty_context(self, risk_agent):
        """Test assess_risk fails with empty context - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            await risk_agent.assess_risk({})
        
        assert "Missing required context" in str(exc_info.value)
    
    async def test_assess_risk_fails_none_context(self, risk_agent):
        """Test assess_risk fails with None context - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            await risk_agent.assess_risk(None)
        
        assert "Context cannot be None" in str(exc_info.value)
    
    async def test_assess_risk_fails_invalid_llm_response(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test assess_risk fails with invalid LLM response - NO FALLBACK."""
        mock_client, mock_content = mock_openai_client
        mock_content.text = "invalid json response"
        
        with patch('openai.OpenAI', return_value=mock_client):
            with pytest.raises(ValueError) as exc_info:
                await risk_agent.assess_risk(sample_workflow_context)
            
            assert "Invalid JSON response from LLM" in str(exc_info.value)
    
    async def test_assess_risk_fails_incomplete_llm_response(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test assess_risk fails with incomplete LLM response - NO FALLBACK."""
        incomplete_response = {
            "risk_level": "MEDIUM"
            # Missing required fields: confidence_score, approver_role, reasoning
        }
        
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(incomplete_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            with pytest.raises(ValueError) as exc_info:
                await risk_agent.assess_risk(sample_workflow_context)
            
            assert "Missing required field" in str(exc_info.value)
    
    async def test_assess_risk_fails_invalid_risk_level(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test assess_risk fails with invalid risk level - NO FALLBACK."""
        invalid_response = {
            "risk_level": "INVALID_LEVEL",
            "confidence_score": 0.8,
            "approver_role": "SUPERVISOR",
            "reasoning": "Test reasoning"
        }
        
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(invalid_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            with pytest.raises(ValueError) as exc_info:
                await risk_agent.assess_risk(sample_workflow_context)
            
            assert "Invalid risk_level" in str(exc_info.value)
    
    async def test_assess_risk_fails_invalid_approver_role(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test assess_risk fails with invalid approver role - NO FALLBACK."""
        invalid_response = {
            "risk_level": "MEDIUM",
            "confidence_score": 0.8,
            "approver_role": "INVALID_ROLE",
            "reasoning": "Test reasoning"
        }
        
        mock_client, mock_content = mock_openai_client
        mock_content.text = json.dumps(invalid_response)
        
        with patch('openai.OpenAI', return_value=mock_client):
            with pytest.raises(ValueError) as exc_info:
                await risk_agent.assess_risk(sample_workflow_context)
            
            assert "Invalid approver_role" in str(exc_info.value)
    
    async def test_assess_risk_fails_openai_error(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test assess_risk fails with OpenAI API error - NO FALLBACK."""
        mock_client, _ = mock_openai_client
        mock_client.responses.create.side_effect = Exception("OpenAI API error")
        
        with patch('openai.OpenAI', return_value=mock_client):
            with pytest.raises(Exception) as exc_info:
                await risk_agent.assess_risk(sample_workflow_context)
            
            assert "Risk assessment failed" in str(exc_info.value)
    
    async def test_explain_assessment_success(self, risk_agent, sample_llm_response):
        """Test assessment explanation generation."""
        workflow_id = "WF_TEST_001"
        
        explanation = await risk_agent.explain_assessment(workflow_id, sample_llm_response)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 50  # Should be substantial explanation
        assert "MEDIUM" in explanation
        assert "SUPERVISOR" in explanation
        assert "$15K" in explanation or "15000" in explanation
    
    async def test_get_approver_role_success(self, risk_agent):
        """Test approver role determination based on risk level and context."""
        # Test different scenarios
        test_cases = [
            {
                "risk_level": "LOW",
                "context": {"financial_impact": 0},
                "expected_role": "AUTO"
            },
            {
                "risk_level": "MEDIUM", 
                "context": {"financial_impact": 5000},
                "expected_role": "ADVISOR"
            },
            {
                "risk_level": "HIGH",
                "context": {"financial_impact": 50000, "compliance_flags": ["LEGAL_REVIEW"]},
                "expected_role": "SUPERVISOR"
            },
            {
                "risk_level": "HIGH",
                "context": {"financial_impact": 100000, "compliance_flags": ["EXECUTIVE_APPROVAL"]},
                "expected_role": "COMPLIANCE"
            }
        ]
        
        for case in test_cases:
            role = await risk_agent.get_approver_role(case["risk_level"], case["context"])
            assert role == case["expected_role"]
    
    async def test_get_approver_role_fails_invalid_risk_level(self, risk_agent):
        """Test get_approver_role fails with invalid risk level - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            await risk_agent.get_approver_role("INVALID_LEVEL", {})
        
        assert "Invalid risk_level" in str(exc_info.value)
    
    async def test_validate_approval_authority_success(self, risk_agent):
        """Test approval authority validation."""
        # Test valid authority scenarios
        test_cases = [
            {
                "approver_role": "AUTO",
                "action_context": {"risk_level": "LOW"},
                "expected": True
            },
            {
                "approver_role": "ADVISOR", 
                "action_context": {"risk_level": "MEDIUM", "financial_impact": 5000},
                "expected": True
            },
            {
                "approver_role": "SUPERVISOR",
                "action_context": {"risk_level": "HIGH", "financial_impact": 25000},
                "expected": True
            },
            {
                "approver_role": "COMPLIANCE",
                "action_context": {"risk_level": "HIGH", "compliance_flags": ["LEGAL_REVIEW"]},
                "expected": True
            }
        ]
        
        for case in test_cases:
            valid = await risk_agent.validate_approval_authority(
                case["approver_role"], 
                case["action_context"]
            )
            assert valid == case["expected"]
    
    async def test_validate_approval_authority_insufficient(self, risk_agent):
        """Test approval authority validation with insufficient authority."""
        # Advisor trying to approve high-risk item
        with pytest.raises(ValueError) as exc_info:
            await risk_agent.validate_approval_authority(
                "ADVISOR", 
                {"risk_level": "HIGH", "financial_impact": 100000}
            )
        
        assert "Insufficient authority" in str(exc_info.value)
    
    def test_context_validation_comprehensive(self, risk_agent):
        """Test comprehensive context validation logic."""
        # Test required context fields
        required_fields = {
            "transcript": ["customer_id", "topic", "sentiment"],
            "analysis": ["primary_intent", "risk_score"],
            "action": ["type", "description"]
        }
        
        # Valid context
        valid_context = {
            "transcript": {
                "customer_id": "CUST_001",
                "topic": "Test topic",
                "sentiment": "neutral"
            },
            "analysis": {
                "primary_intent": "test_intent",
                "risk_score": 0.5
            },
            "action": {
                "type": "test_action",
                "description": "Test description"
            }
        }
        
        # This should not raise an error
        risk_agent._validate_context(valid_context)
        
        # Test missing top-level sections
        for section in ["transcript", "analysis", "action"]:
            incomplete_context = valid_context.copy()
            del incomplete_context[section]
            
            with pytest.raises(ValueError) as exc_info:
                risk_agent._validate_context(incomplete_context)
            assert f"Missing required section: {section}" in str(exc_info.value)
    
    def test_assessment_response_validation(self, risk_agent):
        """Test LLM response validation logic."""
        # Valid response
        valid_response = {
            "risk_level": "MEDIUM",
            "confidence_score": 0.8,
            "approver_role": "SUPERVISOR",
            "reasoning": "Test reasoning",
            "key_factors": ["factor1", "factor2"]
        }
        
        # This should not raise an error
        risk_agent._validate_assessment_response(valid_response)
        
        # Test missing required fields
        required_fields = ["risk_level", "confidence_score", "approver_role", "reasoning"]
        
        for field in required_fields:
            incomplete_response = valid_response.copy()
            del incomplete_response[field]
            
            with pytest.raises(ValueError) as exc_info:
                risk_agent._validate_assessment_response(incomplete_response)
            assert f"Missing required field: {field}" in str(exc_info.value)
        
        # Test invalid enum values
        invalid_responses = [
            {**valid_response, "risk_level": "INVALID"},
            {**valid_response, "approver_role": "INVALID_ROLE"},
            {**valid_response, "confidence_score": 1.5},  # > 1.0
            {**valid_response, "confidence_score": -0.1}  # < 0.0
        ]
        
        for invalid_response in invalid_responses:
            with pytest.raises(ValueError):
                risk_agent._validate_assessment_response(invalid_response)
    
    def test_prompt_building(self, risk_agent, sample_workflow_context):
        """Test that prompt is built correctly with full context."""
        prompt = risk_agent._build_assessment_prompt(sample_workflow_context)
        
        # Verify prompt includes all context sections
        assert "TRANSCRIPT CONTEXT" in prompt
        assert "ANALYSIS RESULTS" in prompt  
        assert "ACTION ITEM DETAILS" in prompt
        
        # Verify specific context values are included
        assert "CUST_TEST_001" in prompt
        assert "payment_assistance" in prompt
        assert "15000" in prompt or "$15K" in prompt
        
        # Verify assessment criteria are included
        assert "Financial Impact" in prompt
        assert "Compliance Requirements" in prompt
        assert "Risk Levels" in prompt
        
        # Verify output format instructions
        assert "JSON" in prompt
        assert "risk_level" in prompt
        assert "approver_role" in prompt
    
    async def test_no_fallback_principle_throughout(self, risk_agent):
        """Test NO FALLBACK principle enforcement throughout agent."""
        # All methods should fail fast with clear errors
        
        # None inputs
        with pytest.raises(ValueError):
            await risk_agent.assess_risk(None)
        
        with pytest.raises(ValueError):
            await risk_agent.explain_assessment("WF_001", None)
        
        with pytest.raises(ValueError):
            await risk_agent.get_approver_role(None, {})
        
        with pytest.raises(ValueError):
            await risk_agent.validate_approval_authority(None, {})
        
        # Empty inputs
        with pytest.raises(ValueError):
            await risk_agent.assess_risk({})
        
        with pytest.raises(ValueError):
            await risk_agent.get_approver_role("", {})
        
        # Invalid enum values
        with pytest.raises(ValueError):
            await risk_agent.get_approver_role("INVALID", {})
        
        with pytest.raises(ValueError):
            await risk_agent.validate_approval_authority("INVALID_ROLE", {})
    
    async def test_confidence_score_handling(self, risk_agent, sample_workflow_context, mock_openai_client):
        """Test confidence score validation and handling."""
        # Test different confidence scores
        confidence_scenarios = [
            {"confidence_score": 0.95, "should_pass": True},
            {"confidence_score": 0.5, "should_pass": True},
            {"confidence_score": 0.1, "should_pass": True},
            {"confidence_score": 1.0, "should_pass": True},
            {"confidence_score": 0.0, "should_pass": True},
            {"confidence_score": 1.1, "should_pass": False},
            {"confidence_score": -0.1, "should_pass": False}
        ]
        
        base_response = {
            "risk_level": "MEDIUM",
            "approver_role": "SUPERVISOR", 
            "reasoning": "Test reasoning"
        }
        
        mock_client, mock_content = mock_openai_client
        
        for scenario in confidence_scenarios:
            response = {**base_response, "confidence_score": scenario["confidence_score"]}
            mock_content.text = json.dumps(response)
            
            with patch('openai.OpenAI', return_value=mock_client):
                if scenario["should_pass"]:
                    assessment = await risk_agent.assess_risk(sample_workflow_context)
                    assert assessment["confidence_score"] == scenario["confidence_score"]
                else:
                    with pytest.raises(ValueError):
                        await risk_agent.assess_risk(sample_workflow_context)