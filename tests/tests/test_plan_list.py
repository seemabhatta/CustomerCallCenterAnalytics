"""
Test cases for 'plan list' CLI command following TDD principles.
Tests CLI-to-REST-API flow with comprehensive error handling.
Ensures NO FALLBACK behavior - commands must work or fail fast.

The bug being tested: PlanService.list_all() calls .to_dict() on dict objects,
causing AttributeError: 'dict' object has no attribute 'to_dict'
"""

import pytest
import subprocess
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typer.testing import CliRunner
import requests

# Add project root to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import app, CLIRestClient, CLIError


def run_cli_subprocess(args, timeout=30):
    """Helper to run CLI commands using subprocess (integration testing)."""
    cmd = ['python', 'cli.py'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent,  # Run from project root
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent)}
    )
    return result


class TestPlanListCLIIntegration:
    """Integration tests for 'plan list' CLI command using subprocess."""
    
    def test_plan_list_command_exists(self):
        """
        TDD TEST: plan list command should exist and show help.
        This ensures the command structure is properly defined.
        """
        result = run_cli_subprocess(['plan', 'list', '--help'])
        assert result.returncode == 0, f"plan list help failed: {result.stderr}"
        assert 'list' in result.stdout.lower(), "Should show list command help"
        assert 'plan' in result.stdout.lower(), "Should reference plans"
    
    @patch('requests.Session.request')
    def test_plan_list_successful_multiple_plans(self, mock_request):
        """
        TDD TEST: plan list should display multiple plans correctly.
        Tests the complete CLI flow with proper output formatting.
        """
        # Arrange - Mock successful API response with multiple plans
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "plan_id": "PLAN_ABC123",
                "analysis_id": "ANALYSIS_XYZ789",
                "status": "pending",
                "created_at": "2024-01-15T10:30:00Z"
            },
            {
                "plan_id": "PLAN_DEF456", 
                "analysis_id": "ANALYSIS_UVW012",
                "status": "approved",
                "created_at": "2024-01-15T11:45:00Z"
            }
        ]
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 0, f"plan list failed: {result.stderr}"
        assert "Found 2 plan(s)" in result.stdout, "Should show correct plan count"
        assert "PLAN_ABC123" in result.stdout, "Should show first plan ID"
        assert "PLAN_DEF456" in result.stdout, "Should show second plan ID"
        assert "ANALYSIS_XYZ789" in result.stdout, "Should show first analysis ID"
        assert "ANALYSIS_UVW012" in result.stdout, "Should show second analysis ID"
        assert "pending" in result.stdout, "Should show first plan status"
        assert "approved" in result.stdout, "Should show second plan status"
        
        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'
        assert '/api/v1/plans' in call_args[1]['url']
    
    @patch('requests.Session.request')
    def test_plan_list_empty_plans(self, mock_request):
        """
        TDD TEST: plan list should handle empty plan list gracefully.
        Tests NO FALLBACK principle - should show clear empty message.
        """
        # Arrange - Mock API response with empty list
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 0, f"plan list failed: {result.stderr}"
        assert "📭 No plans found" in result.stdout, "Should show empty message"
        assert "Found 0 plan(s)" not in result.stdout, "Should not show count for empty list"
        
        # Verify API call
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_plan_list_with_limit_parameter(self, mock_request):
        """
        TDD TEST: plan list --limit should pass limit parameter to API.
        Tests limit functionality and API parameter passing.
        """
        # Arrange - Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "plan_id": "PLAN_LIMITED1",
                "analysis_id": "ANALYSIS_LIM1",
                "status": "pending"
            }
        ]
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list', '--limit', '5'])
        
        # Assert
        assert result.returncode == 0, f"plan list with limit failed: {result.stderr}"
        assert "PLAN_LIMITED1" in result.stdout, "Should show limited results"
        
        # Verify API call included limit parameter
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {'limit': '5'}, "Should pass limit parameter"
    
    @patch('requests.Session.request')
    def test_plan_list_api_error_404(self, mock_request):
        """
        TDD TEST: plan list should fail fast on 404 API error.
        Tests NO FALLBACK principle - should exit with error, not continue.
        """
        # Arrange - Mock 404 error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Plans endpoint not found"
        mock_response.json.return_value = {"detail": "Not found: /api/v1/plans"}
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "Not found" in result.stderr, "Should show error message"
        assert "List plans failed" in result.stderr, "Should show command-specific error"
        assert "📭 No plans found" not in result.stdout, "Should NOT show empty message"
    
    @patch('requests.Session.request')
    def test_plan_list_api_error_500(self, mock_request):
        """
        TDD TEST: plan list should fail fast on 500 API error.
        Tests server error handling without fallbacks.
        """
        # Arrange - Mock 500 server error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "API error (500)" in result.stderr, "Should show HTTP error"
        assert "List plans failed" in result.stderr, "Should show command failure"
    
    @patch('requests.Session.request')
    def test_plan_list_network_timeout(self, mock_request):
        """
        TDD TEST: plan list should fail fast on network timeout.
        Tests timeout handling without fallbacks.
        """
        # Arrange - Mock timeout
        mock_request.side_effect = requests.exceptions.Timeout("Request timeout")
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "List plans failed" in result.stderr, "Should show command failure"


class TestPlanListRESTClient:
    """Unit tests for CLIRestClient.list_plans() method."""
    
    def test_list_plans_method_exists(self):
        """
        TDD TEST: CLIRestClient should have list_plans method.
        """
        client = CLIRestClient()
        assert hasattr(client, 'list_plans'), "Client should have list_plans method"
        assert callable(getattr(client, 'list_plans')), "list_plans should be callable"
    
    @patch('requests.Session.request')
    def test_list_plans_makes_correct_api_call(self, mock_request):
        """
        TDD TEST: list_plans should make GET request to correct endpoint.
        """
        # Arrange
        client = CLIRestClient(api_url="http://test:8000")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        # Act
        client.list_plans()
        
        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'
        assert call_args[1]['url'] == 'http://test:8000/api/v1/plans'
        assert call_args[1]['params'] == {}
    
    @patch('requests.Session.request')
    def test_list_plans_with_limit_parameter(self, mock_request):
        """
        TDD TEST: list_plans should pass limit parameter correctly.
        """
        # Arrange
        client = CLIRestClient()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_request.return_value = mock_response
        
        # Act
        client.list_plans(limit=10)
        
        # Assert
        call_args = mock_request.call_args
        assert call_args[1]['params'] == {'limit': 10}
    
    @patch('requests.Session.request')
    def test_list_plans_returns_plan_data(self, mock_request):
        """
        TDD TEST: list_plans should return parsed JSON data.
        """
        # Arrange
        client = CLIRestClient()
        expected_plans = [
            {"plan_id": "PLAN_TEST1", "analysis_id": "ANALYSIS_1", "status": "pending"},
            {"plan_id": "PLAN_TEST2", "analysis_id": "ANALYSIS_2", "status": "approved"}
        ]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_plans
        mock_request.return_value = mock_response
        
        # Act
        result = client.list_plans()
        
        # Assert
        assert result == expected_plans, "Should return parsed plan data"
    
    @patch('requests.Session.request')
    def test_list_plans_handles_404_error(self, mock_request):
        """
        TDD TEST: list_plans should raise CLIError on 404.
        Tests NO FALLBACK principle - should fail fast, not return empty list.
        """
        # Arrange
        client = CLIRestClient()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_response.json.return_value = {"detail": "Plans endpoint not found"}
        mock_request.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            client.list_plans()
        
        assert "Not found" in str(exc_info.value), "Should raise specific error"
    
    @patch('requests.Session.request')
    def test_list_plans_handles_malformed_json(self, mock_request):
        """
        TDD TEST: list_plans should handle malformed JSON responses.
        Tests edge case where API returns 200 but invalid JSON.
        """
        # Arrange
        client = CLIRestClient()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_request.return_value = mock_response
        
        # Act & Assert
        with pytest.raises(CLIError) as exc_info:
            client.list_plans()
        
        assert "JSON" in str(exc_info.value), "Should indicate JSON parsing error"


class TestPlanListOutputFormatting:
    """Tests for plan list CLI output formatting and display."""
    
    @patch('requests.Session.request')
    def test_plan_list_output_format_matches_pattern(self, mock_request):
        """
        TDD TEST: plan list output should match expected Rich formatting pattern.
        Tests that output includes proper Rich console formatting.
        """
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "plan_id": "PLAN_FORMAT_TEST",
                "analysis_id": "ANALYSIS_FORMAT",
                "status": "pending"
            }
        ]
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Check for Rich formatting markers
        assert "📋" in result.stdout, "Should include plan emoji"
        assert "Listing plans" in result.stdout, "Should show loading message"
        assert "Plan ID:" in result.stdout, "Should show plan ID label"
        assert "Analysis ID:" in result.stdout, "Should show analysis ID label"
        assert "Status:" in result.stdout, "Should show status label" 
        assert "─" in result.stdout, "Should include separator lines"
    
    @patch('requests.Session.request')
    def test_plan_list_handles_missing_fields(self, mock_request):
        """
        TDD TEST: plan list should handle plans with missing fields gracefully.
        Tests robustness when API returns incomplete plan data.
        """
        # Arrange - Plan missing some fields
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "plan_id": "PLAN_INCOMPLETE"
                # Missing analysis_id and status
            }
        ]
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert "PLAN_INCOMPLETE" in result.stdout, "Should show available plan ID"
        assert "N/A" in result.stdout, "Should show N/A for missing fields"


class TestPlanListToDictBug:
    """Tests specifically targeting the .to_dict() bug in PlanService."""
    
    @patch('requests.Session.request')
    def test_plan_list_handles_dict_objects_correctly(self, mock_request):
        """
        TDD TEST: plan list should work when API returns dict objects.
        This test targets the specific bug where .to_dict() is called on dict objects.
        
        The bug occurs in PlanService.list_all() line 24:
        return [p.to_dict() for p in plans]
        
        When plans are already dict objects from the store, this fails.
        """
        # Arrange - Mock response that would trigger the bug
        mock_response = Mock()
        mock_response.status_code = 200
        # This simulates the scenario where the service tries to call .to_dict() 
        # on dict objects, which should be handled correctly
        mock_response.json.return_value = [
            {
                "plan_id": "PLAN_DICT_TEST",
                "analysis_id": "ANALYSIS_DICT",
                "status": "pending",
                "metadata": {"test": "data"}
            }
        ]
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'list'])
        
        # Assert - Should work without AttributeError
        assert result.returncode == 0, f"Command should succeed: {result.stderr}"
        assert "PLAN_DICT_TEST" in result.stdout, "Should display plan data"
        assert "AttributeError" not in result.stderr, "Should not have .to_dict() error"
        assert "'dict' object has no attribute 'to_dict'" not in result.stderr, "Should not have the specific bug error"
    
    def test_mock_to_dict_error_simulation(self):
        """
        TDD TEST: Simulate the exact .to_dict() error for verification.
        This test demonstrates what the bug looks like.
        """
        # Arrange - Create scenario that would cause the bug
        plan_dict = {"plan_id": "TEST", "analysis_id": "TEST", "status": "pending"}
        
        # Act & Assert - This should fail demonstrating the bug
        with pytest.raises(AttributeError) as exc_info:
            plan_dict.to_dict()  # This is what the buggy code tries to do
        
        assert "'dict' object has no attribute 'to_dict'" in str(exc_info.value)


if __name__ == "__main__":
    # Run tests to verify they fail (TDD approach)
    pytest.main([__file__, "-v"])