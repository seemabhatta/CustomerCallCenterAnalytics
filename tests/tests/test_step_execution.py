"""
Test cases for step-by-step workflow execution.
Following TDD principles - write tests FIRST before implementation.
NO FALLBACK LOGIC - tests should verify fail-fast behavior.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from src.services.workflow_execution_engine import WorkflowExecutionEngine
from src.storage.workflow_execution_store import WorkflowExecutionStore
from src.storage.workflow_store import WorkflowStore


class TestStepExecutionStore:
    """Test database layer for step execution tracking."""

    def test_execution_store_has_step_number_field(self):
        """Test that execution store can save and query by step_number."""
        # This test will fail until we add step_number to schema
        store = WorkflowExecutionStore(":memory:")

        # Should be able to create execution with step_number
        execution_data = {
            'workflow_id': 'WF_TEST',
            'step_number': 2,
            'executor_type': 'test_executor',
            'execution_payload': {'result': 'test'},
            'execution_status': 'executed',
            'executed_at': '2025-01-19T10:00:00Z',
            'executed_by': 'test_user',
            'execution_duration_ms': 100,
            'mock_execution': True
        }

        # This should work after implementing step_number field
        execution_id = asyncio.run(store.create(execution_data))
        assert execution_id is not None

    def test_get_execution_by_workflow_and_step(self):
        """Test querying execution by workflow_id and step_number."""
        store = WorkflowExecutionStore(":memory:")

        # Create execution for step 2
        execution_data = {
            'workflow_id': 'WF_TEST',
            'step_number': 2,
            'executor_type': 'test_executor',
            'execution_payload': {'result': 'step_2_result'},
            'execution_status': 'executed',
            'executed_at': '2025-01-19T10:00:00Z',
            'executed_by': 'test_user',
            'execution_duration_ms': 100,
            'mock_execution': True
        }

        execution_id = asyncio.run(store.create(execution_data))

        # Should be able to find by workflow + step
        result = asyncio.run(store.get_by_workflow_and_step('WF_TEST', 2))
        assert result is not None
        assert result['step_number'] == 2
        assert result['workflow_id'] == 'WF_TEST'

        # Should return None for non-existent step
        result = asyncio.run(store.get_by_workflow_and_step('WF_TEST', 3))
        assert result is None


class TestWorkflowExecutionEngine:
    """Test step-by-step execution in workflow engine."""

    @pytest.fixture
    def engine(self):
        """Create engine with in-memory database."""
        return WorkflowExecutionEngine(":memory:")

    @pytest.fixture
    def sample_workflow(self):
        """Sample workflow with multiple steps."""
        return {
            'id': 'WF_TEST_123',
            'status': 'APPROVED',
            'workflow_data': {
                'steps': [
                    {
                        'step_number': 1,
                        'action': 'Test action 1',
                        'tool_needed': 'email',
                        'details': 'Send test email'
                    },
                    {
                        'step_number': 2,
                        'action': 'Test action 2',
                        'tool_needed': 'crm',
                        'details': 'Update CRM record'
                    },
                    {
                        'step_number': 3,
                        'action': 'Test action 3',
                        'tool_needed': 'servicing_api',
                        'details': 'Call servicing API'
                    }
                ]
            }
        }

    def test_execute_single_step_exists(self, engine):
        """Test that execute_single_step method exists."""
        # This test will fail until we implement the method
        assert hasattr(engine, 'execute_single_step')
        assert callable(getattr(engine, 'execute_single_step'))

    def test_execute_single_step_success(self, engine, sample_workflow):
        """Test successful execution of a single step."""
        # Mock workflow store to return our sample workflow
        with patch.object(engine.workflow_store, 'get_by_id', return_value=sample_workflow):
            # Mock email adapter to return success
            engine.adapters['email'].execute = Mock(return_value={
                'status': 'success',
                'payload': {'email_sent': True, 'recipient': 'test@example.com'}
            })

            # Execute step 1
            result = asyncio.run(engine.execute_single_step('WF_TEST_123', 1, 'test_advisor'))

            # Verify result structure
            assert result['workflow_id'] == 'WF_TEST_123'
            assert result['step_number'] == 1
            assert result['status'] == 'success'
            assert result['executor_type'] == 'email'
            assert 'execution_id' in result
            assert 'duration_ms' in result

    def test_execute_single_step_invalid_workflow(self, engine):
        """Test execution fails fast for invalid workflow."""
        # Mock workflow store to return None (workflow not found)
        with patch.object(engine.workflow_store, 'get_by_id', return_value=None):
            # Should raise ValueError immediately (NO FALLBACK)
            with pytest.raises(ValueError, match="Workflow not found"):
                asyncio.run(engine.execute_single_step('INVALID_WF', 1, 'test_advisor'))

    def test_execute_single_step_unapproved_workflow(self, engine, sample_workflow):
        """Test execution fails fast for unapproved workflow."""
        # Modify workflow to be unapproved
        sample_workflow['status'] = 'PENDING'

        with patch.object(engine.workflow_store, 'get_by_id', return_value=sample_workflow):
            # Should raise ValueError immediately (NO FALLBACK)
            with pytest.raises(ValueError, match="must be approved"):
                asyncio.run(engine.execute_single_step('WF_TEST_123', 1, 'test_advisor'))

    def test_execute_single_step_invalid_step_number(self, engine, sample_workflow):
        """Test execution fails fast for invalid step number."""
        with patch.object(engine.workflow_store, 'get_by_id', return_value=sample_workflow):
            # Should raise ValueError for step that doesn't exist (NO FALLBACK)
            with pytest.raises(ValueError, match="Step 99 not found"):
                asyncio.run(engine.execute_single_step('WF_TEST_123', 99, 'test_advisor'))

    def test_execute_single_step_missing_adapter(self, engine, sample_workflow):
        """Test execution fails fast when adapter is missing."""
        # Add step with non-existent tool
        sample_workflow['workflow_data']['steps'].append({
            'step_number': 4,
            'action': 'Test action 4',
            'tool_needed': 'nonexistent_tool',
            'details': 'This should fail'
        })

        with patch.object(engine.workflow_store, 'get_by_id', return_value=sample_workflow):
            # Should raise error immediately (NO FALLBACK)
            with pytest.raises(Exception, match="No executor.*nonexistent_tool"):
                asyncio.run(engine.execute_single_step('WF_TEST_123', 4, 'test_advisor'))

    def test_execute_steps_out_of_order(self, engine, sample_workflow):
        """Test that steps can be executed out of order."""
        with patch.object(engine.workflow_store, 'get_by_id', return_value=sample_workflow):
            # Mock CRM adapter
            engine.adapters['crm'].execute = Mock(return_value={
                'status': 'success',
                'payload': {'crm_updated': True}
            })

            # Execute step 2 first (skip step 1)
            result = asyncio.run(engine.execute_single_step('WF_TEST_123', 2, 'test_advisor'))

            assert result['step_number'] == 2
            assert result['executor_type'] == 'crm'
            assert result['status'] == 'success'


class TestStepExecutionAPI:
    """Test API endpoints for step execution."""

    def test_step_execution_models_exist(self):
        """Test that required models exist."""
        # This will fail until we create the models
        from src.models.execution_models import (
            StepExecutionRequest,
            StepExecutionResponse,
            StepStatusResponse
        )

        # Test StepExecutionRequest
        request = StepExecutionRequest(
            executed_by="test_advisor",
            confirmation=True
        )
        assert request.executed_by == "test_advisor"
        assert request.confirmation is True

        # Test StepExecutionResponse
        response = StepExecutionResponse(
            workflow_id="WF_123",
            step_number=1,
            status="success",
            executor_type="email",
            execution_id="EXEC_789",
            result={"test": "data"},
            executed_at="2025-01-19T10:00:00Z",
            executed_by="test_advisor",
            duration_ms=250
        )
        assert response.workflow_id == "WF_123"
        assert response.step_number == 1

        # Test StepStatusResponse
        status_response = StepStatusResponse(
            workflow_id="WF_123",
            step_number=2,
            executed=False,
            execution_details=None
        )
        assert status_response.workflow_id == "WF_123"
        assert status_response.executed is False


class TestStepExecutionIntegration:
    """Integration tests for complete step execution flow."""

    def test_complete_step_execution_flow(self):
        """Test complete flow: create workflow -> execute steps -> check status."""
        # This is a high-level integration test
        # Will implement after individual components are working
        pass

    def test_step_idempotency(self):
        """Test that executing the same step twice is safe."""
        # This test ensures we don't break existing behavior
        # Should either prevent duplicate execution or handle it gracefully
        pass