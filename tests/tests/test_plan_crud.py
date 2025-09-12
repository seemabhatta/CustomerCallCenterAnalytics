"""
Test cases for plan CRUD operations following TDD principles.
Tests missing plan operations: view, update, delete, delete-all.
Ensures NO FALLBACK behavior - commands must work or fail fast.
"""

import pytest
import subprocess
import json
import os
import re
from pathlib import Path
from unittest.mock import Mock, patch
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


class TestPlanViewCLIIntegration:
    """Integration tests for 'plan view' CLI command."""
    
    def test_plan_view_command_exists(self):
        """
        TDD TEST: plan view command should exist and show help.
        """
        result = run_cli_subprocess(['plan', 'view', '--help'])
        assert result.returncode == 0, f"plan view help failed: {result.stderr}"
        assert 'view' in result.stdout.lower(), "Should show view command help"
        assert 'plan' in result.stdout.lower(), "Should reference plans"
    
    @patch('requests.Session.request')
    def test_plan_view_successful_retrieval(self, mock_request):
        """
        TDD TEST: plan view should display single plan details.
        Tests complete CLI flow with detailed plan information.
        """
        # Arrange - Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plan_id": "PLAN_VIEW_TEST",
            "analysis_id": "ANALYSIS_VIEW_123",
            "status": "pending",
            "created_at": "2024-01-15T10:30:00Z",
            "borrower_plan": {
                "immediate_actions": [
                    {"action": "Review credit report", "priority": "high"},
                    {"action": "Contact lender", "priority": "medium"}
                ],
                "timeframe": "24 hours"
            },
            "advisor_plan": {
                "recommendations": ["Debt consolidation", "Budget review"]
            }
        }
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'view', 'PLAN_VIEW_TEST'])
        
        # Assert
        assert result.returncode == 0, f"plan view failed: {result.stderr}"
        assert "PLAN_VIEW_TEST" in result.stdout, "Should show plan ID"
        assert "ANALYSIS_VIEW_123" in result.stdout, "Should show analysis ID"
        assert "pending" in result.stdout, "Should show plan status"
        
        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'
        assert '/api/v1/plans/PLAN_VIEW_TEST' in call_args[1]['url']
    
    @patch('requests.Session.request')
    def test_plan_view_not_found_fails_fast(self, mock_request):
        """
        TDD TEST: plan view should fail fast for non-existent plan.
        Tests NO FALLBACK principle - should exit with error, not show placeholder.
        """
        # Arrange - Mock 404 error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Plan not found"
        mock_response.json.return_value = {"detail": "Plan PLAN_NONEXISTENT not found"}
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'view', 'PLAN_NONEXISTENT'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "not found" in result.stderr.lower(), "Should show error message"
        assert "View plan failed" in result.stderr, "Should show command-specific error"
        assert "PLAN_NONEXISTENT" not in result.stdout, "Should NOT show placeholder data"


class TestPlanUpdateCLIIntegration:
    """Integration tests for 'plan update' CLI command."""
    
    def test_plan_update_command_exists(self):
        """
        TDD TEST: plan update command should exist and show help.
        """
        result = run_cli_subprocess(['plan', 'update', '--help'])
        assert result.returncode == 0, f"plan update help failed: {result.stderr}"
        assert 'update' in result.stdout.lower(), "Should show update command help"
        assert 'plan' in result.stdout.lower(), "Should reference plans"
    
    @patch('requests.Session.request')
    def test_plan_update_status_successful(self, mock_request):
        """
        TDD TEST: plan update should modify plan status successfully.
        Tests status update functionality.
        """
        # Arrange - Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "plan_id": "PLAN_UPDATE_TEST",
            "analysis_id": "ANALYSIS_UPDATE_123",
            "status": "approved",  # Updated status
            "updated_at": "2024-01-15T11:00:00Z"
        }
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'update', 'PLAN_UPDATE_TEST', '--status', 'approved'])
        
        # Assert
        assert result.returncode == 0, f"plan update failed: {result.stderr}"
        assert "PLAN_UPDATE_TEST" in result.stdout, "Should show updated plan ID"
        assert "approved" in result.stdout, "Should show updated status"
        
        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'PUT'
        assert '/api/v1/plans/PLAN_UPDATE_TEST' in call_args[1]['url']
        assert call_args[1]['json']['status'] == 'approved'
    
    @patch('requests.Session.request')
    def test_plan_update_not_found_fails_fast(self, mock_request):
        """
        TDD TEST: plan update should fail fast for non-existent plan.
        Tests NO FALLBACK principle - should not create new plan.
        """
        # Arrange - Mock 404 error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Plan not found"
        mock_response.json.return_value = {"detail": "Plan PLAN_UPDATE_FAIL not found"}
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'update', 'PLAN_UPDATE_FAIL', '--status', 'approved'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "not found" in result.stderr.lower(), "Should show error message"
        assert "Update plan failed" in result.stderr, "Should show command-specific error"


class TestPlanDeleteCLIIntegration:
    """Integration tests for 'plan delete' CLI command."""
    
    def test_plan_delete_command_exists(self):
        """
        TDD TEST: plan delete command should exist and show help.
        """
        result = run_cli_subprocess(['plan', 'delete', '--help'])
        assert result.returncode == 0, f"plan delete help failed: {result.stderr}"
        assert 'delete' in result.stdout.lower(), "Should show delete command help"
        assert 'plan' in result.stdout.lower(), "Should reference plans"
    
    @patch('requests.Session.request')  
    def test_plan_delete_with_force_successful(self, mock_request):
        """
        TDD TEST: plan delete should delete plan with --force flag.
        Tests deletion without confirmation prompt.
        """
        # Arrange - Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Plan PLAN_DELETE_TEST deleted successfully",
            "plan_id": "PLAN_DELETE_TEST"
        }
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'delete', 'PLAN_DELETE_TEST', '--force'])
        
        # Assert
        assert result.returncode == 0, f"plan delete failed: {result.stderr}"
        assert "PLAN_DELETE_TEST" in result.stdout, "Should show deleted plan ID"
        assert "deleted" in result.stdout.lower(), "Should confirm deletion"
        
        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'DELETE'
        assert '/api/v1/plans/PLAN_DELETE_TEST' in call_args[1]['url']
    
    @patch('requests.Session.request')
    def test_plan_delete_not_found_fails_fast(self, mock_request):
        """
        TDD TEST: plan delete should fail fast for non-existent plan.
        Tests NO FALLBACK principle - should not silently succeed.
        """
        # Arrange - Mock 404 error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Plan not found"
        mock_response.json.return_value = {"detail": "Plan PLAN_DELETE_FAIL not found"}
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'delete', 'PLAN_DELETE_FAIL', '--force'])
        
        # Assert
        assert result.returncode == 1, "Should exit with error code"
        assert "not found" in result.stderr.lower(), "Should show error message"
        assert "Delete plan failed" in result.stderr, "Should show command-specific error"
        assert "deleted successfully" not in result.stdout, "Should NOT show success message"
    
    def test_plan_delete_requires_confirmation_or_force(self):
        """
        TDD TEST: plan delete without --force should require confirmation.
        Tests safety mechanism to prevent accidental deletion.
        """
        result = run_cli_subprocess(['plan', 'delete', 'PLAN_TEST'])
        
        # Should either prompt for confirmation or show error about missing --force
        assert result.returncode != 0, "Should not succeed without confirmation mechanism"


class TestPlanDeleteAllCLIIntegration:
    """Integration tests for 'plan delete-all' CLI command."""
    
    def test_plan_delete_all_command_exists(self):
        """
        TDD TEST: plan delete-all command should exist and show help.
        """
        result = run_cli_subprocess(['plan', 'delete-all', '--help'])
        assert result.returncode == 0, f"plan delete-all help failed: {result.stderr}"
        assert 'delete-all' in result.stdout.lower(), "Should show delete-all command help"
        assert 'plan' in result.stdout.lower(), "Should reference plans"
    
    @patch('requests.Session.request')
    def test_plan_delete_all_with_force_successful(self, mock_request):
        """
        TDD TEST: plan delete-all should delete all plans with --force flag.
        Tests bulk deletion functionality.
        """
        # Arrange - Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "All plans deleted successfully",
            "deleted_count": 5
        }
        mock_request.return_value = mock_response
        
        # Act
        result = run_cli_subprocess(['plan', 'delete-all', '--force'])
        
        # Assert
        assert result.returncode == 0, f"plan delete-all failed: {result.stderr}"
        assert "deleted" in result.stdout.lower(), "Should confirm deletion"
        assert "5" in result.stdout or "all" in result.stdout.lower(), "Should show deletion count or all"
        
        # Verify API call was made correctly
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'DELETE'
        assert '/api/v1/plans' in call_args[1]['url']
    
    def test_plan_delete_all_requires_force_flag(self):
        """
        TDD TEST: plan delete-all without --force should fail for safety.
        Tests safety mechanism to prevent accidental bulk deletion.
        """
        result = run_cli_subprocess(['plan', 'delete-all'])
        
        assert result.returncode != 0, "Should not succeed without --force flag"
        assert "force" in result.stderr.lower() or "confirmation" in result.stderr.lower(), \
            "Should mention need for --force or confirmation"


class TestPlanCRUDRESTClient:
    """Unit tests for CLIRestClient plan CRUD methods."""
    
    def test_view_plan_method_exists(self):
        """
        TDD TEST: CLIRestClient should have view_plan method.
        """
        client = CLIRestClient()
        assert hasattr(client, 'view_plan'), "Client should have view_plan method"
        assert callable(getattr(client, 'view_plan')), "view_plan should be callable"
    
    def test_update_plan_method_exists(self):
        """
        TDD TEST: CLIRestClient should have update_plan method.
        """
        client = CLIRestClient()
        assert hasattr(client, 'update_plan'), "Client should have update_plan method"
        assert callable(getattr(client, 'update_plan')), "update_plan should be callable"
    
    def test_delete_plan_method_exists(self):
        """
        TDD TEST: CLIRestClient should have delete_plan method.
        """
        client = CLIRestClient()
        assert hasattr(client, 'delete_plan'), "Client should have delete_plan method"
        assert callable(getattr(client, 'delete_plan')), "delete_plan should be callable"
    
    def test_delete_all_plans_method_exists(self):
        """
        TDD TEST: CLIRestClient should have delete_all_plans method.
        """
        client = CLIRestClient()
        assert hasattr(client, 'delete_all_plans'), "Client should have delete_all_plans method"
        assert callable(getattr(client, 'delete_all_plans')), "delete_all_plans should be callable"
    
    @patch('requests.Session.request')
    def test_view_plan_makes_correct_api_call(self, mock_request):
        """
        TDD TEST: view_plan should make GET request to correct endpoint.
        """
        # Arrange
        client = CLIRestClient(api_url="http://test:8000")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"plan_id": "PLAN_TEST", "status": "pending"}
        mock_request.return_value = mock_response
        
        # Act
        client.view_plan("PLAN_TEST")
        
        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'GET'
        assert call_args[1]['url'] == 'http://test:8000/api/v1/plans/PLAN_TEST'
    
    @patch('requests.Session.request')
    def test_update_plan_makes_correct_api_call(self, mock_request):
        """
        TDD TEST: update_plan should make PUT request to correct endpoint.
        """
        # Arrange
        client = CLIRestClient(api_url="http://test:8000")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"plan_id": "PLAN_TEST", "status": "approved"}
        mock_request.return_value = mock_response
        
        update_data = {"status": "approved"}
        
        # Act
        client.update_plan("PLAN_TEST", update_data)
        
        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'PUT'
        assert call_args[1]['url'] == 'http://test:8000/api/v1/plans/PLAN_TEST'
        assert call_args[1]['json'] == update_data
    
    @patch('requests.Session.request')
    def test_delete_plan_makes_correct_api_call(self, mock_request):
        """
        TDD TEST: delete_plan should make DELETE request to correct endpoint.
        """
        # Arrange
        client = CLIRestClient(api_url="http://test:8000")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Plan deleted"}
        mock_request.return_value = mock_response
        
        # Act
        client.delete_plan("PLAN_TEST")
        
        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'DELETE'
        assert call_args[1]['url'] == 'http://test:8000/api/v1/plans/PLAN_TEST'
    
    @patch('requests.Session.request')
    def test_delete_all_plans_makes_correct_api_call(self, mock_request):
        """
        TDD TEST: delete_all_plans should make DELETE request to plans endpoint.
        """
        # Arrange
        client = CLIRestClient(api_url="http://test:8000")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "All plans deleted", "count": 10}
        mock_request.return_value = mock_response
        
        # Act
        client.delete_all_plans()
        
        # Assert
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[1]['method'] == 'DELETE'
        assert call_args[1]['url'] == 'http://test:8000/api/v1/plans'


class TestPlanCRUDNoFallbackPrinciple:
    """Test that plan CRUD operations follow NO FALLBACK principle."""
    
    def test_crud_commands_fail_fast_on_missing_id(self):
        """
        TDD TEST: CRUD commands should fail fast when plan ID is missing.
        """
        failing_commands = [
            ['plan', 'view'],  # Missing plan ID
            ['plan', 'update'],  # Missing plan ID
            ['plan', 'delete']  # Missing plan ID
        ]
        
        for cmd in failing_commands:
            result = run_cli_subprocess(cmd)
            assert result.returncode != 0, f"{' '.join(cmd)} should fail for missing plan ID"
            
            # Should show clear error about missing arguments
            combined_output = (result.stdout + result.stderr).lower()
            assert 'missing' in combined_output or 'required' in combined_output or 'error' in combined_output, \
                f"Should show clear error for {' '.join(cmd)}"
    
    def test_crud_operations_no_fallback_messages(self):
        """
        TDD TEST: CRUD operations should not show fallback/placeholder messages.
        """
        # Test with invalid plan IDs
        commands_to_test = [
            ['plan', 'view', 'INVALID_PLAN'],
            ['plan', 'update', 'INVALID_PLAN', '--status', 'approved'],
            ['plan', 'delete', 'INVALID_PLAN', '--force']
        ]
        
        for cmd in commands_to_test:
            result = run_cli_subprocess(cmd)
            
            # Should NOT show fallback messages
            fallback_indicators = [
                'not yet implemented',
                'coming soon', 
                'future version',
                'will be available',
                'placeholder',
                'mock data'
            ]
            
            combined_output = (result.stdout + result.stderr).lower()
            for indicator in fallback_indicators:
                assert indicator not in combined_output, \
                    f"VIOLATION: Found fallback message '{indicator}' in {' '.join(cmd)}"


if __name__ == "__main__":
    # Run tests to verify they fail (TDD approach)
    pytest.main([__file__, "-v"])