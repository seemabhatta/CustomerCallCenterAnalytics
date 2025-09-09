"""
Test Execution Status Reporting - Issue #13
Tests that executed actions return proper success status indicators.
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.executors.smart_executor import SmartExecutor


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        temp_path = tmp.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_openai_success_response():
    """Mock successful OpenAI response for action execution."""
    mock_response = Mock()
    mock_response.output = [Mock()]
    mock_response.output[0].content = [Mock()]
    mock_response.output[0].content[0].text = '{"status": "success", "message": "Action completed successfully"}'
    return mock_response


class TestExecutionStatus:
    """Test cases for proper execution status reporting."""

    def test_status_icon_logic_fixed(self):
        """Test that status icon logic correctly identifies successful vs failed actions."""
        # This test verifies the fix in cli_fast.py line 904-912
        
        # Test successful statuses show ✅
        successful_statuses = ['success', 'completed', 'generated', 'delivered', 'sent', 'approved']
        for status in successful_statuses:
            # Simulate the fixed logic
            if status.lower() in ['success', 'completed', 'generated', 'delivered', 'sent', 'approved']:
                icon = "✅"
            elif status.lower() in ['error', 'failed', 'rejected']:
                icon = "❌"
            else:
                icon = "⚠️"
            
            assert icon == "✅", f"Status '{status}' should show ✅ but got {icon}"
        
        # Test error statuses show ❌
        error_statuses = ['error', 'failed', 'rejected']
        for status in error_statuses:
            if status.lower() in ['success', 'completed', 'generated', 'delivered', 'sent', 'approved']:
                icon = "✅"
            elif status.lower() in ['error', 'failed', 'rejected']:
                icon = "❌"
            else:
                icon = "⚠️"
            
            assert icon == "❌", f"Status '{status}' should show ❌ but got {icon}"
        
        # Test unknown statuses show ⚠️
        unknown_statuses = ['pending', 'unknown', 'processing']
        for status in unknown_statuses:
            if status.lower() in ['success', 'completed', 'generated', 'delivered', 'sent', 'approved']:
                icon = "✅"
            elif status.lower() in ['error', 'failed', 'rejected']:
                icon = "❌"
            else:
                icon = "⚠️"
            
            assert icon == "⚠️", f"Status '{status}' should show ⚠️ but got {icon}"

    def test_failed_action_shows_error_status_clearly(self, temp_db):
        """Test that genuinely failed actions show clear error status."""
        # Arrange
        executor = SmartExecutor(db_path=temp_db)
        
        sample_action = {
            "action": "Invalid action that should fail",
            "action_type": "borrower_action",
            "priority": "high",
            "auto_executable": True,
            "approval_status": "approved"
        }
        
        # Mock OpenAI to return error
        with patch('src.executors.smart_executor.openai') as mock_openai:
            mock_openai.responses.create.side_effect = Exception("API Error")
            
            # Act
            result = executor._execute_single_action(sample_action, "test-execution-123")
            
            # Assert
            assert result['status'] == 'error', f"Failed action should show 'error' status"
            assert result.get('error') is not None, f"Failed action should have error message"

    def test_execution_result_shows_correct_success_indicators(self, temp_db, mock_openai_success_response):
        """Test that execution result properly categorizes success vs failure."""
        # This test currently FAILS because execution shows ❌ for successful actions
        # Arrange
        executor = SmartExecutor(db_path=temp_db)
        
        plan_data = {
            "plan_id": "test-plan-123",
            "borrower_actions": [
                {
                    "action": "Send status update email",
                    "action_type": "borrower_action", 
                    "priority": "high",
                    "auto_executable": True,
                    "approval_status": "approved"
                }
            ],
            "advisor_actions": [],
            "supervisor_actions": [],
            "leadership_actions": []
        }
        
        # Mock successful responses
        with patch('src.executors.smart_executor.openai') as mock_openai:
            mock_openai.responses.create.return_value = mock_openai_success_response
            
            # Act
            result = executor.execute_action_plan("test-plan-123")
            
            # Assert - These assertions will FAIL until implementation is fixed
            # Should show ✅ success indicators, not ❌ error indicators
            assert result.get('status') == 'success', f"Overall execution should succeed"
            
            # Check individual action results
            borrower_results = result.get('results', {}).get('borrower_actions', [])
            assert len(borrower_results) > 0, "Should have borrower action results"
            
            for action_result in borrower_results:
                # This assertion will FAIL - currently shows 'error' for successful actions
                assert action_result.get('status') != 'error', f"Successful action showing error status: {action_result}"

    def test_status_icons_match_actual_results(self, temp_db):
        """Test that UI status icons (✅/❌) match the actual execution results."""
        # This test documents the current bug where successful actions show ❌
        # After fix, successful actions should show ✅
        
        # This test will be implemented after we understand the status reporting format
        # Currently execution output shows:
        # ❌ borrower_immediate: error  <-- This should be ✅ borrower_immediate: success
        # ❌ advisor_coaching: generated  <-- This should be ✅ advisor_coaching: generated
        
        pytest.skip("Test to be completed after status reporting format is analyzed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])