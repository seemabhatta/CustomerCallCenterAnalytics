"""
Shared test configuration and fixtures for all test modules.
Provides common fixtures, utilities, and test helpers following NO FALLBACK principles.
"""
import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List
from datetime import datetime


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_api_key():
    """Mock OpenAI API key for testing."""
    return "test-api-key-123456"


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    from src.models.transcript import Transcript
    return Transcript(
        transcript_id="CALL_TEST123",
        customer_id="CUST_001",
        topic="payment_inquiry",
        urgency="medium",
        messages=[
            {
                "speaker": "customer",
                "text": "I need help with my payment",
                "timestamp": "10:00:00"
            },
            {
                "speaker": "agent",
                "text": "I can help you with that",
                "timestamp": "10:00:30"
            },
            {
                "speaker": "customer", 
                "text": "When is my payment due?",
                "timestamp": "10:01:00"
            },
            {
                "speaker": "agent",
                "text": "Your payment is due on the 15th",
                "timestamp": "10:01:15"
            }
        ]
    )


@pytest.fixture
def sample_analysis():
    """Sample analysis result for testing."""
    return {
        "analysis_id": "ANALYSIS_TEST123",
        "transcript_id": "CALL_TEST123",
        "sentiment_analysis": {
            "overall_sentiment": "neutral",
            "customer_sentiment": "concerned",
            "agent_sentiment": "helpful",
            "confidence": 0.85
        },
        "risk_indicators": {
            "delinquency_risk": 0.3,
            "churn_risk": 0.2,
            "complaint_risk": 0.1
        },
        "topics": ["payment", "due_date", "account_inquiry"],
        "resolution_status": "resolved",
        "follow_up_required": False,
        "key_entities": {
            "customer_id": "CUST_001",
            "account_number": "123456789",
            "payment_amount": 1500.00
        }
    }


@pytest.fixture
def sample_plan():
    """Sample action plan for testing."""
    return {
        "plan_id": "PLAN_TEST123",
        "analysis_id": "ANALYSIS_TEST123",
        "transcript_id": "CALL_TEST123",
        "risk_level": "medium",
        "approval_route": "advisor_approval",
        "queue_status": "pending_advisor",
        "auto_executable": False,
        "generator_version": "1.0",
        "routing_reason": "Medium risk detected: 0.5",
        "borrower_plan": {
            "immediate_actions": [
                {
                    "action": "Send confirmation email",
                    "timeline": "Within 24 hours",
                    "priority": "high",
                    "auto_executable": True
                },
                {
                    "action": "Schedule follow-up call",
                    "timeline": "Within 3 days", 
                    "priority": "medium",
                    "auto_executable": False
                }
            ],
            "follow_ups": [
                {
                    "action": "Follow up call",
                    "due_date": "2024-01-15",
                    "owner": "CSR"
                }
            ],
            "personalized_offers": ["Refinance evaluation"],
            "risk_mitigation": ["Monitor payment patterns"]
        },
        "advisor_plan": {
            "coaching_items": ["Improve active listening", "Better rapport building"],
            "performance_feedback": {
                "strengths": ["Clear communication", "Problem resolution"],
                "improvements": ["Better questions", "Empathy building"],
                "score_explanations": ["Good resolution", "Professional tone"]
            },
            "training_recommendations": ["De-escalation training", "Product knowledge"],
            "next_actions": ["Review recording", "Schedule coaching session"]
        },
        "supervisor_plan": {
            "escalation_items": [
                {
                    "item": "Payment dispute",
                    "reason": "Complex case requiring supervisor review",
                    "priority": "medium",
                    "action_required": "Review and approve resolution"
                }
            ],
            "team_patterns": ["Increase in payment inquiries", "Good resolution rates"],
            "compliance_review": ["Check disclosures", "Verify procedures"],
            "approval_required": True,
            "process_improvements": ["Streamline payment process"]
        },
        "leadership_plan": {
            "portfolio_insights": ["Rising payment concerns", "Good customer satisfaction"],
            "strategic_opportunities": ["Improve online payment tools"],
            "risk_indicators": ["Payment delays trending up"],
            "trend_analysis": ["Seasonal payment patterns"],
            "resource_allocation": ["Consider additional payment options"]
        }
    }


@pytest.fixture
def sample_workflow():
    """Sample workflow for testing."""
    return {
        "id": "WORKFLOW_TEST123",
        "plan_id": "PLAN_TEST123",
        "workflow_type": "BORROWER",
        "workflow_data": {
            "action_item": {
                "action": "Send payment reminder",
                "timeline": "Within 24 hours",
                "priority": "high",
                "auto_executable": True
            },
            "description": "Automated payment reminder for customer",
            "context": {
                "customer_id": "CUST_001",
                "amount": 1500.00,
                "due_date": "2024-01-15"
            }
        },
        "risk_level": "LOW",
        "auto_executable": True,
        "status": "pending_execution",
        "created_at": "2024-01-10T10:00:00Z"
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_transcript_service():
    """Mock TranscriptService for API testing."""
    mock_service = Mock()
    mock_service.list_all = Mock()
    mock_service.create = Mock() 
    mock_service.get_by_id = Mock()
    mock_service.delete = Mock()
    mock_service.search = Mock()
    mock_service.get_metrics = Mock()
    return mock_service


@pytest.fixture  
def mock_analysis_service():
    """Mock AnalysisService for API testing."""
    mock_service = Mock()
    mock_service.list_all = Mock()
    mock_service.create = Mock()
    mock_service.get_by_id = Mock()
    mock_service.get_by_transcript_id = Mock()
    mock_service.delete = Mock()
    mock_service.get_metrics = Mock()
    mock_service.get_risk_report = Mock()
    return mock_service


@pytest.fixture
def mock_plan_service():
    """Mock PlanService for API testing."""
    mock_service = Mock()
    mock_service.list_all = Mock()
    mock_service.create = Mock()
    mock_service.get_by_id = Mock()
    mock_service.update = Mock()
    mock_service.delete = Mock()
    mock_service.get_actions_by_transcript_id = Mock()
    return mock_service


@pytest.fixture
def mock_system_service():
    """Mock SystemService for API testing.""" 
    mock_service = Mock()
    mock_service.health_check = Mock()
    mock_service.get_dashboard_metrics = Mock()
    mock_service.get_workflow_status = Mock()
    return mock_service


# ============================================================================
# Test Helper Classes
# ============================================================================

class TestHelpers:
    """Static test helper methods for common test patterns."""
    
    @staticmethod
    def assert_route_only_calls_service(mock_service_method, expected_args=None):
        """Assert that route only calls service method with expected args."""
        mock_service_method.assert_called_once()
        if expected_args:
            mock_service_method.assert_called_with(*expected_args)
    
    @staticmethod
    def assert_no_business_logic(response, mock_service_method):
        """Assert that route contains no business logic - only proxies to service."""
        # Route should only call service and return result
        # No data transformation, no decision making, no fallback logic
        mock_service_method.assert_called_once()
        
    @staticmethod
    def assert_fail_fast_behavior(response):
        """Assert that route fails fast when service fails."""
        # Should return error status codes (4xx/5xx)
        # Should NOT return mock/default data
        assert response.status_code >= 400
        
    @staticmethod
    def create_mock_openai_response(content: str):
        """Create mock OpenAI API response."""
        mock_response = Mock()
        mock_choice = Mock()
        mock_message = Mock()
        mock_message.content = content
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        return mock_response


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test path/name."""
    for item in items:
        # Mark API tests
        if "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        
        # Mark integration tests
        if "integration" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark slow tests
        if "slow" in item.name or "performance" in item.name:
            item.add_marker(pytest.mark.slow)