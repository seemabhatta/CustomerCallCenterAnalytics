"""
Test suite for CLI Agent REST client
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import json
from unittest.mock import Mock, patch
import requests
from cli_agent import AdvisorCLI


class TestAdvisorCLIInit:
    """Test AdvisorCLI REST client initialization."""

    def test_init_with_default_url(self):
        """Should initialize with default API URL."""
        client = AdvisorCLI()
        assert client.api_url == "http://localhost:8000"

    def test_init_with_custom_url(self):
        """Should initialize with custom API URL."""
        client = AdvisorCLI("https://custom-api.example.com")
        assert client.api_url == "https://custom-api.example.com"

    def test_init_strips_trailing_slash(self):
        """Should strip trailing slash from API URL."""
        client = AdvisorCLI("http://localhost:8000/")
        assert client.api_url == "http://localhost:8000"

    def test_init_sets_content_type_header(self):
        """Should set Content-Type header for JSON requests."""
        client = AdvisorCLI()
        assert client.session.headers.get('Content-Type') == 'application/json'


class TestAdvisorCLIChat:
    """Test chat functionality - REST API calls."""

    @patch('requests.Session.post')
    def test_chat_makes_correct_api_call(self, mock_post):
        """Should make POST request to correct endpoint with proper payload."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Hello! Ready to help.",
            "session_id": "SID-12345",
            "advisor_id": "ADV001"
        }
        mock_post.return_value = mock_response

        client = AdvisorCLI("http://test-api:8000")
        result = client.chat(
            advisor_id="ADV001",
            message="Hello",
            session_id="SID-12345",
            transcript_id="CALL_123"
        )

        # Verify API call
        mock_post.assert_called_once_with(
            "http://test-api:8000/api/v1/advisor/chat",
            json={
                "advisor_id": "ADV001",
                "message": "Hello",
                "session_id": "SID-12345",
                "transcript_id": "CALL_123",
                "plan_id": None
            },
            timeout=30
        )

        # Verify response
        assert result["response"] == "Hello! Ready to help."
        assert result["session_id"] == "SID-12345"

    @patch('requests.Session.post')
    def test_chat_handles_http_error_responses(self, mock_post):
        """Should fail fast with proper error for HTTP error responses."""
        # Setup mock error response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request: Missing advisor_id"
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response

        client = AdvisorCLI()

        with pytest.raises(Exception, match="API error \\(400\\): Bad Request: Missing advisor_id"):
            client.chat(advisor_id="", message="Hello")

    @patch('requests.Session.post')
    def test_chat_handles_json_error_responses(self, mock_post):
        """Should extract error details from JSON response."""
        # Setup mock JSON error response
        mock_response = Mock()
        mock_response.status_code = 422
        mock_response.json.return_value = {
            "detail": "Validation error: advisor_id is required"
        }
        mock_post.return_value = mock_response

        client = AdvisorCLI()

        with pytest.raises(Exception, match="API error \\(422\\): Validation error: advisor_id is required"):
            client.chat(advisor_id="", message="Hello")

    @patch('requests.Session.post')
    def test_chat_handles_connection_errors(self, mock_post):
        """Should fail fast with connection error details."""
        # Setup mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = AdvisorCLI("http://unavailable-server:8000")

        with pytest.raises(Exception, match="Failed to connect to API at http://unavailable-server:8000: Connection refused"):
            client.chat(advisor_id="ADV001", message="Hello")

    @patch('requests.Session.post')
    def test_chat_handles_timeout_errors(self, mock_post):
        """Should fail fast with timeout error details."""
        # Setup mock timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        client = AdvisorCLI()

        with pytest.raises(Exception, match="Failed to connect to API at http://localhost:8000: Request timed out"):
            client.chat(advisor_id="ADV001", message="Hello")

    @patch('requests.Session.post')
    def test_chat_passes_all_context_parameters(self, mock_post):
        """Should pass all context parameters to API."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Context loaded", "session_id": "SID-123"}
        mock_post.return_value = mock_response

        client = AdvisorCLI()
        client.chat(
            advisor_id="ADV001",
            message="Show workflows",
            session_id="SID-456",
            transcript_id="CALL_789",
            plan_id="PLAN_101"
        )

        # Verify all parameters were passed
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload["advisor_id"] == "ADV001"
        assert payload["message"] == "Show workflows"
        assert payload["session_id"] == "SID-456"
        assert payload["transcript_id"] == "CALL_789"
        assert payload["plan_id"] == "PLAN_101"

    @patch('requests.Session.post')
    def test_chat_uses_30_second_timeout(self, mock_post):
        """Should use 30 second timeout for API calls."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "OK", "session_id": "SID-123"}
        mock_post.return_value = mock_response

        client = AdvisorCLI()
        client.chat(advisor_id="ADV001", message="Hello")

        # Verify timeout was set
        call_args = mock_post.call_args
        assert call_args[1]['timeout'] == 30


class TestAdvisorCLIErrorHandling:
    """Test error handling and fail-fast behavior."""

    @patch('requests.Session.post')
    def test_chat_no_fallback_on_server_error(self, mock_post):
        """Should fail fast on server errors without fallback logic."""
        # Setup mock server error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.json.side_effect = ValueError("No JSON")
        mock_post.return_value = mock_response

        client = AdvisorCLI()

        # Should raise exception, not return mock data or default response
        with pytest.raises(Exception, match="API error \\(500\\): Internal Server Error"):
            client.chat(advisor_id="ADV001", message="Hello")

    @patch('requests.Session.post')
    def test_chat_no_fallback_on_network_error(self, mock_post):
        """Should fail fast on network errors without fallback logic."""
        # Setup mock network error
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        client = AdvisorCLI()

        # Should raise exception, not return mock data or default response
        with pytest.raises(Exception, match="Failed to connect to API"):
            client.chat(advisor_id="ADV001", message="Hello")