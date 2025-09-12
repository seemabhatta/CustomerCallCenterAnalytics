"""
Shared fixtures and mocks for API v1 tests.
Follows TDD principles - defines expected behavior before implementation.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_transcript_service():
    """Mock transcript service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def mock_analysis_service():
    """Mock analysis service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def mock_plan_service():
    """Mock plan service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def mock_case_service():
    """Mock case service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def mock_governance_service():
    """Mock governance service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def mock_system_service():
    """Mock system service for testing route-only behavior."""
    return Mock()


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return {
        "id": "CALL_TEST123",
        "customer_id": "CUST_001",
        "scenario": "payment_inquiry",
        "messages": [
            {"speaker": "Customer", "text": "I need help with my payment"},
            {"speaker": "Agent", "text": "I can help you with that"}
        ],
        "urgency": "medium",
        "financial_impact": False,
        "created_at": "2025-01-15T10:00:00Z"
    }


@pytest.fixture
def sample_analysis():
    """Sample analysis data for testing."""
    return {
        "id": "ANALYSIS_456",
        "transcript_id": "CALL_TEST123", 
        "intent": "payment_inquiry",
        "sentiment": "neutral",
        "urgency": "medium",
        "confidence": 0.85,
        "risk_scores": {
            "delinquency": 0.2,
            "churn": 0.1,
            "complaint": 0.05
        }
    }


@pytest.fixture
def sample_plan():
    """Sample action plan data for testing."""
    return {
        "id": "PLAN_789",
        "transcript_id": "CALL_TEST123",
        "risk_level": "medium",
        "approval_route": "manual",
        "queue_status": "pending",
        "borrower_plan": {
            "immediate_actions": ["Follow up on payment"],
            "follow_ups": ["Check account status"]
        }
    }


@pytest.fixture
def sample_case():
    """Sample case data for testing."""
    return {
        "id": "CALL_TEST123",
        "customerId": "CUST_001",
        "scenario": "payment_inquiry",
        "priority": 50,
        "status": "Needs Review",
        "risk": "Medium",
        "exchanges": 2,
        "createdAt": "2025-01-15T10:00:00Z"
    }


@pytest.fixture
def client_with_mocks(mock_transcript_service, mock_analysis_service, 
                      mock_plan_service, mock_case_service,
                      mock_governance_service, mock_system_service):
    """Test client with all services mocked to test route-only behavior."""
    # This will be updated once we have the new server structure
    # For now, return None to indicate this needs implementation
    return None


# Common test helpers
class TestHelpers:
    """Helper methods for API tests."""
    
    @staticmethod
    def assert_route_only_calls_service(mock_service, method_name, expected_args=None):
        """Verify that route only calls service method with expected args."""
        assert mock_service.called
        if expected_args:
            mock_service.assert_called_with(*expected_args)
        
    @staticmethod
    def assert_no_business_logic(response, mock_service):
        """Verify route contains no business logic - only proxies to service."""
        # Route should call service exactly once
        assert mock_service.call_count == 1
        # Route should return service response directly
        assert response.status_code in [200, 201, 204, 400, 404, 500]
        
    @staticmethod
    def assert_fail_fast_behavior(response):
        """Verify fail-fast behavior - no fallback data on service failure."""
        assert response.status_code == 500
        # Should not contain any fallback/mock data
        assert "fallback" not in response.text.lower()
        assert "mock" not in response.text.lower()
        assert "default" not in response.text.lower()


# Error response schemas
EXPECTED_ERROR_FORMAT = {
    "type": "object",
    "properties": {
        "detail": {"type": "string"},
        "status_code": {"type": "integer"}
    },
    "required": ["detail"]
}

EXPECTED_SUCCESS_LIST_FORMAT = {
    "type": "array",
    "items": {"type": "object"}
}

EXPECTED_SUCCESS_ITEM_FORMAT = {
    "type": "object",
    "properties": {
        "id": {"type": "string"}
    },
    "required": ["id"]
}