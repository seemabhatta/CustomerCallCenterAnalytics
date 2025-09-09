"""
Test Artifact Generation - Issue #12
Tests that plan execution generates email and callback artifacts, not just documents.
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
def sample_action_plan():
    """Sample action plan with email and callback actions."""
    return {
        "plan_id": "test-plan-artifacts",
        "borrower_plan": {
            "immediate_actions": [
                {
                    "action": "Send confirmation email about PMI removal status",
                    "timeline": "Within 24 hours",
                    "priority": "high",
                    "auto_executable": True,
                    "approval_status": "approved"
                }
            ],
            "follow_up_actions": [
                {
                    "action": "Schedule follow-up call to discuss appraisal results",
                    "due_date": "Within 2 business days",
                    "owner": "Advisor",
                    "auto_executable": True,
                    "approval_status": "approved"
                }
            ]
        },
        "advisor_plan": {
            "coaching_items": []
        },
        "supervisor_plan": {
            "escalation_items": []
        },
        "leadership_plan": {
            "strategic_opportunities": []
        },
        "transcript_id": "CALL_TEST123",
        "queue_status": "approved"
    }


class TestArtifactGeneration:
    """Test cases for email, callback, and document artifact generation."""

    def test_execution_generates_email_artifacts(self, temp_db, sample_action_plan):
        """Test that execution creates email artifacts for customer communications."""
        # This test currently FAILS because no email artifacts are generated
        # Arrange
        executor = SmartExecutor(db_path=temp_db)
        
        # Mock the action plan store to return our sample plan
        with patch.object(executor.action_plan_store, 'get_by_id') as mock_get:
            mock_get.return_value = sample_action_plan
            
            # Mock OpenAI to return email execution decisions
            with patch('src.executors.smart_executor.openai') as mock_openai:
                mock_response = Mock()
                mock_response.output = [Mock()]
                mock_response.output[0].content = [Mock()]
                # LLM should decide to use email tool for confirmation
                mock_response.output[0].content[0].text = '''[
                    {
                        "tool": "email",
                        "action": "Send confirmation email about PMI removal status",
                        "parameters": {
                            "recipient": "customer@example.com",
                            "subject": "PMI Removal Status Update",
                            "template_id": "pmi_confirmation"
                        },
                        "content": "Dear Customer, we have received your PMI removal request..."
                    }
                ]'''
                mock_openai.responses.create.return_value = mock_response
                
                # Act
                result = executor.execute_action_plan("test-plan-artifacts")
                
                # Assert - This will FAIL until email generation is implemented
                assert result.get('status') == 'success', f"Execution should succeed: {result}"
                
                # Check that email artifacts were created
                artifacts = result.get('artifacts_created', [])
                email_artifacts = [a for a in artifacts if 'email' in str(a).lower()]
                
                assert len(email_artifacts) > 0, f"No email artifacts generated. Artifacts: {artifacts}"
                assert any('pmi_confirmation' in str(a) or 'confirmation' in str(a) for a in email_artifacts), \
                    f"Expected email confirmation artifact, got: {email_artifacts}"

    def test_execution_generates_callback_artifacts(self, temp_db, sample_action_plan):
        """Test that execution creates callback scheduling artifacts."""
        # This test currently FAILS because no callback artifacts are generated
        # Arrange
        executor = SmartExecutor(db_path=temp_db)
        
        with patch.object(executor.action_plan_store, 'get_by_id') as mock_get:
            mock_get.return_value = sample_action_plan
            
            with patch('src.executors.smart_executor.openai') as mock_openai:
                mock_response = Mock()
                mock_response.output = [Mock()]
                mock_response.output[0].content = [Mock()]
                # LLM should decide to use callback tool for follow-up
                mock_response.output[0].content[0].text = '''[
                    {
                        "tool": "callback",
                        "action": "Schedule follow-up call to discuss appraisal results",
                        "parameters": {
                            "scheduled_time": "2025-09-11T14:00:00",
                            "priority": "normal",
                            "duration": "15 minutes"
                        },
                        "content": "Follow-up call scheduled to discuss PMI removal appraisal results with customer"
                    }
                ]'''
                mock_openai.responses.create.return_value = mock_response
                
                # Act
                result = executor.execute_action_plan("test-plan-artifacts")
                
                # Assert - This will FAIL until callback generation is implemented
                assert result.get('status') == 'success', f"Execution should succeed: {result}"
                
                # Check that callback artifacts were created
                artifacts = result.get('artifacts_created', [])
                callback_artifacts = [a for a in artifacts if 'callback' in str(a).lower()]
                
                assert len(callback_artifacts) > 0, f"No callback artifacts generated. Artifacts: {artifacts}"
                assert any('follow' in str(a).lower() for a in callback_artifacts), \
                    f"Expected follow-up callback artifact, got: {callback_artifacts}"

    def test_execution_generates_all_artifact_types(self, temp_db, sample_action_plan):
        """Test that execution can generate emails, callbacks, AND documents."""
        # This test verifies the complete artifact generation capability
        # Currently will FAIL because only documents are generated
        
        executor = SmartExecutor(db_path=temp_db)
        
        with patch.object(executor.action_plan_store, 'get_by_id') as mock_get:
            mock_get.return_value = sample_action_plan
            
            with patch('src.executors.smart_executor.openai') as mock_openai:
                mock_response = Mock()
                mock_response.output = [Mock()]
                mock_response.output[0].content = [Mock()]
                # LLM should decide to use multiple tools
                mock_response.output[0].content[0].text = '''[
                    {
                        "tool": "email",
                        "action": "Send status email",
                        "parameters": {"recipient": "customer@test.com", "subject": "Status Update"},
                        "content": "Your PMI removal request update..."
                    },
                    {
                        "tool": "callback", 
                        "action": "Schedule callback",
                        "parameters": {"scheduled_time": "2025-09-11T10:00:00"},
                        "content": "Follow-up call scheduled"
                    },
                    {
                        "tool": "document",
                        "action": "Generate coaching note",
                        "parameters": {"doc_type": "coaching_note"},
                        "content": "Coaching documentation for advisor"
                    }
                ]'''
                mock_openai.responses.create.return_value = mock_response
                
                # Act
                result = executor.execute_action_plan("test-plan-artifacts")
                
                # Assert
                assert result.get('status') == 'success', f"Execution should succeed"
                
                artifacts = result.get('artifacts_created', [])
                
                # Should have all three types
                email_count = len([a for a in artifacts if 'email' in str(a).lower()])
                callback_count = len([a for a in artifacts if 'callback' in str(a).lower()])  
                doc_count = len([a for a in artifacts if 'doc' in str(a).lower() or '.txt' in str(a)])
                
                assert email_count > 0, f"No email artifacts. Artifacts: {artifacts}"
                assert callback_count > 0, f"No callback artifacts. Artifacts: {artifacts}"
                assert doc_count > 0, f"No document artifacts. Artifacts: {artifacts}"

    def test_cli_view_artifacts_shows_emails_and_callbacks(self):
        """Test that CLI commands can view email and callback artifacts after generation."""
        # This will test the CLI artifact viewing after we implement generation
        pytest.skip("Will implement after artifact generation is working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])