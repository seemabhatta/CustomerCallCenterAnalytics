"""Tests for independent action plan generation - NO Decision Agent dependencies."""
import pytest
from unittest.mock import Mock, patch
import json
from src.generators.action_plan_generator import ActionPlanGenerator
from src.models.transcript import Transcript, Message


class TestActionPlanIndependent:
    """Test action plan generation works completely independently."""
    
    def test_generator_initializes_without_db_path(self):
        """ActionPlanGenerator should initialize with only API key."""
        generator = ActionPlanGenerator(api_key="test_key")
        
        # Should have OpenAI client
        assert generator.client is not None
        
        # Should NOT have Decision Agent components
        assert not hasattr(generator, 'decision_agent')
        assert not hasattr(generator, 'approval_store')
    
    def test_plan_generates_without_decision_agent(self):
        """Plan generation should work without Decision Agent."""
        # Mock transcript
        messages = [
            Message(speaker="CUSTOMER", text="I need help with my mortgage payment"),
            Message(speaker="CSR", text="I'll help you with that. Let me check your account")
        ]
        transcript = Transcript(
            transcript_id="TEST_001",
            customer_id="CUST_001", 
            messages=messages,
            topic="Payment assistance"
        )
        
        # Mock analysis
        analysis = {
            "analysis_id": "ANALYSIS_001",
            "primary_intent": "payment_assistance",
            "sentiment": "concerned",
            "urgency_level": "high",
            "risk_score": 0.7,
            "borrower_risks": {"delinquency_risk": 0.6},
            "compliance_flags": ["PAYMENT_PLAN"],
            "advisor_performance": {"empathy_score": 0.8}
        }
        
        # Mock OpenAI response
        mock_response = Mock()
        mock_output = Mock()
        mock_content = Mock()
        mock_content.text = json.dumps({
            "borrower_plan": {
                "immediate_actions": [{"action": "Send payment options", "priority": "high"}]
            },
            "advisor_plan": {
                "coaching_items": [{"item": "Review empathy techniques", "priority": "medium"}]
            },
            "supervisor_plan": {
                "approvals_needed": [{"item": "Payment plan approval", "risk_level": "medium"}]
            },
            "leadership_plan": {
                "insights": [{"insight": "Increase in payment assistance requests", "trend": "up"}]
            }
        })
        mock_output.content = [mock_content]
        mock_response.output = [mock_output]
        
        with patch('openai.OpenAI') as mock_client:
            mock_client.return_value.responses.create.return_value = mock_response
            
            generator = ActionPlanGenerator(api_key="test_key")
            result = generator.generate(analysis, transcript)
        
        # Should generate all four plan layers
        assert "borrower_plan" in result
        assert "advisor_plan" in result 
        assert "supervisor_plan" in result
        assert "leadership_plan" in result
        
        # Should not contain Decision Agent artifacts
        result_str = json.dumps(result).lower()
        assert "decision_agent" not in result_str
        assert "approval_store" not in result_str
    
    def test_full_transcript_in_context(self):
        """Verify full conversation is included in context extraction."""
        messages = [
            Message(speaker="CUSTOMER", text="I'm worried about my payment"),
            Message(speaker="CSR", text="I understand your concern. Let me help"),
            Message(speaker="CUSTOMER", text="I lost my job last month"),
            Message(speaker="CSR", text="We have hardship programs available")
        ]
        transcript = Transcript(
            transcript_id="TEST_002",
            customer_id="CUST_002",
            messages=messages,
            topic="Hardship assistance",
            duration=15
        )
        
        analysis = {
            "primary_intent": "hardship_assistance",
            "sentiment": "worried",
            "borrower_risks": {"unemployment": 0.9}
        }
        
        generator = ActionPlanGenerator(api_key="test_key")
        context = generator._extract_context(transcript, analysis)
        
        # Should include full conversation
        assert "full_conversation" in context
        assert len(context["full_conversation"]) == 4
        
        # Should preserve all message details
        assert context["full_conversation"][0]["speaker"] == "CUSTOMER"
        assert "worried" in context["full_conversation"][0]["text"]
        assert context["full_conversation"][2]["text"] == "I lost my job last month"
        
        # Should include transcript metadata
        assert context["call_duration"] == 15
        assert context["call_topic"] == "Hardship assistance"
        assert context["customer_id"] == "CUST_002"
        
        # Should include analysis data
        assert context["analysis"]["primary_intent"] == "hardship_assistance"
        assert context["analysis"]["sentiment"] == "worried"
    
    def test_context_extraction_with_empty_transcript_fails(self):
        """Should fail fast if transcript has no messages - NO FALLBACK."""
        transcript = Transcript(
            transcript_id="EMPTY_001",
            customer_id="CUST_003", 
            messages=[],  # Empty messages
            topic="Unknown"
        )
        
        analysis = {"primary_intent": "unknown"}
        
        generator = ActionPlanGenerator(api_key="test_key")
        context = generator._extract_context(transcript, analysis)
        
        # Should have empty conversation but not fail
        assert context["full_conversation"] == []
        
        # Extracted elements should be empty
        assert context["promises_made"] == []
        assert context["customer_concerns"] == []
    
    def test_no_hardcoded_extraction_methods(self):
        """Test that hardcoded extraction methods are removed - following agentic approach."""
        generator = ActionPlanGenerator(api_key="test_key")
        
        # Should NOT have hardcoded extraction methods
        assert not hasattr(generator, '_extract_promises')
        assert not hasattr(generator, '_extract_concerns')
        assert not hasattr(generator, '_extract_timelines')
        assert not hasattr(generator, '_extract_next_steps')
        
        # Should have only essential methods for agentic approach
        assert hasattr(generator, 'generate')
        assert hasattr(generator, '_extract_context')
        assert hasattr(generator, '_build_prompt')
        assert hasattr(generator, '_get_action_plan_schema')
    
    def test_context_includes_full_conversation_for_llm_analysis(self):
        """Test that full conversation is provided to LLM instead of hardcoded extraction."""
        messages = [
            Message(speaker="CUSTOMER", text="I'm really worried about losing my home"),
            Message(speaker="CUSTOMER", text="This is so confusing and frustrating"),
            Message(speaker="CSR", text="I understand your concerns"),
            Message(speaker="CUSTOMER", text="The costs are getting too expensive")
        ]
        transcript = Transcript(
            transcript_id="CONCERNS_001", 
            customer_id="CUST_005",
            messages=messages,
            topic="Financial difficulty"
        )
        
        generator = ActionPlanGenerator(api_key="test_key")
        context = generator._extract_context(transcript, {"primary_intent": "financial_difficulty"})
        
        # Should include full conversation for LLM to analyze
        assert len(context["full_conversation"]) == 4
        conversation_text = " ".join([msg["text"] for msg in context["full_conversation"]])
        
        # LLM will see all customer concerns in the full conversation
        assert "worried about losing my home" in conversation_text
        assert "confusing and frustrating" in conversation_text
        assert "costs are getting too expensive" in conversation_text
        
        # No hardcoded extraction - let LLM analyze
        assert context["customer_concerns"] == []  # Empty - LLM handles this
    
    def test_agentic_approach_no_hardcoded_patterns(self):
        """Test that timeline commitments are captured in full conversation for LLM analysis."""
        messages = [
            Message(speaker="CSR", text="I'll get back to you within 2 business days"),
            Message(speaker="CSR", text="The review will be completed by Friday"),
            Message(speaker="CUSTOMER", text="Can you call me tomorrow?"),
            Message(speaker="CSR", text="Yes, I'll call you tomorrow morning")
        ]
        transcript = Transcript(
            transcript_id="TIMELINE_001",
            customer_id="CUST_006", 
            messages=messages,
            topic="Account review"
        )
        
        generator = ActionPlanGenerator(api_key="test_key")
        context = generator._extract_context(transcript, {"primary_intent": "account_review"})
        
        # Full conversation captured for LLM analysis instead of hardcoded patterns
        conversation_text = " ".join([msg["text"] for msg in context["full_conversation"]])
        
        # LLM will see all timeline commitments in context
        assert "2 business days" in conversation_text
        assert "completed by Friday" in conversation_text
        assert "call you tomorrow" in conversation_text
        
        # No hardcoded extraction - agentic approach
        assert context["timeline_commitments"] == []  # Empty - LLM handles this
    
    def test_comprehensive_prompt_includes_full_context(self):
        """Test that prompt includes full conversation and analysis."""
        messages = [
            Message(speaker="CUSTOMER", text="I need a payment plan"),
            Message(speaker="CSR", text="I can help set that up")
        ]
        transcript = Transcript(
            transcript_id="PROMPT_001",
            customer_id="CUST_007",
            messages=messages,
            topic="Payment plan",
            duration=10
        )
        
        analysis = {
            "primary_intent": "payment_plan",
            "sentiment": "cooperative", 
            "risk_score": 0.4,
            "borrower_risks": {"payment_difficulty": 0.5},
            "compliance_flags": ["PAYMENT_ARRANGEMENT"]
        }
        
        generator = ActionPlanGenerator(api_key="test_key")
        context = generator._extract_context(transcript, analysis)
        prompt = generator._build_prompt(context)
        
        # Should include full transcript
        assert "CUSTOMER: I need a payment plan" in prompt
        assert "CSR: I can help set that up" in prompt
        
        # Should include analysis details
        assert "payment_plan" in prompt
        assert "cooperative" in prompt
        assert "0.4" in prompt  # risk score
        
        # Should include metadata
        assert "Duration: 10" in prompt
        assert "Payment plan" in prompt  # topic
        assert "CUST_007" in prompt  # customer_id
        
        # Should have instruction for four layers
        assert "BORROWER PLAN" in prompt
        assert "ADVISOR PLAN" in prompt  
        assert "SUPERVISOR PLAN" in prompt
        assert "LEADERSHIP PLAN" in prompt
    
    def test_no_decision_agent_methods_or_attributes(self):
        """Ensure ActionPlanGenerator has no Decision Agent code."""
        generator = ActionPlanGenerator(api_key="test_key")
        
        # Should not have Decision Agent methods
        assert not hasattr(generator, '_integrate_decision_agent')
        assert not hasattr(generator, 'apply_decision_agent')
        
        # Should not have Decision Agent attributes
        assert not hasattr(generator, 'decision_agent')
        assert not hasattr(generator, 'approval_store')
        
        # Check that generate method doesn't reference Decision Agent
        import inspect
        source = inspect.getsource(generator.generate)
        assert 'decision_agent' not in source.lower()
        assert 'approval' not in source.lower()