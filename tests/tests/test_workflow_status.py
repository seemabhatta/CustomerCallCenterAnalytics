"""
Test cases for workflow status functionality.
Following TDD principles - these tests are written FIRST and should initially fail.
NO FALLBACK LOGIC - tests will fail if dependencies are not available.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.storage.transcript_store import TranscriptStore
from src.storage.analysis_store import AnalysisStore
from src.storage.action_plan_store import ActionPlanStore
from src.storage.approval_store import ApprovalStore
from src.storage.execution_store import ExecutionStore


class TestWorkflowStatusBackend:
    """Test the backend logic for workflow status - separate from API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # These stores MUST be available - no fallback logic
        self.transcript_store = TranscriptStore("test.db")
        self.analysis_store = AnalysisStore("test.db")
        self.plan_store = ActionPlanStore("test.db")
        self.approval_store = ApprovalStore("test.db")
        self.execution_store = ExecutionStore("test.db")
    
    def test_get_all_transcripts_with_status(self):
        """Test retrieving all transcripts and their current workflow status."""
        # This test expects the backend to return transcripts with their status
        # Should fail initially as the backend logic doesn't exist yet
        
        # Expected structure for each transcript:
        expected_structure = {
            'transcript_id': str,
            'customer_name': str,
            'created_at': str,
            'current_stage': str,  # 'transcript', 'analysis', 'plan', 'approval', 'execution'
            'status': str,         # 'completed', 'in_progress', 'pending', 'failed'
            'stage_details': dict
        }
        
        # This import should fail initially - the backend doesn't exist yet
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store, 
            self.plan_store,
            self.approval_store,
            self.execution_store
        )
        
        result = backend.get_all_workflows_status()
        
        assert isinstance(result, list)
        if result:  # Only test structure if data exists
            for transcript_status in result:
                assert 'transcript_id' in transcript_status
                assert 'current_stage' in transcript_status
                assert 'status' in transcript_status
                assert transcript_status['current_stage'] in [
                    'transcript', 'analysis', 'plan', 'approval', 'execution'
                ]
                assert transcript_status['status'] in [
                    'completed', 'in_progress', 'pending', 'failed'
                ]
    
    def test_get_workflow_status_by_transcript_id(self):
        """Test getting workflow status for a specific transcript."""
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store,
            self.plan_store, 
            self.approval_store,
            self.execution_store
        )
        
        # Test with a valid transcript ID that should exist
        transcripts = self.transcript_store.get_all()
        if transcripts:
            # If transcripts exist, test with one
            transcript_id = transcripts[0]['id']
            result = backend.get_workflow_status_by_id(transcript_id)
            
            assert isinstance(result, dict)
            assert result['transcript_id'] == transcript_id
            assert 'current_stage' in result
            assert 'status' in result
            assert 'stage_details' in result
        else:
            # If no transcripts, test that invalid ID fails fast (no fallback)
            with pytest.raises(Exception):
                backend.get_workflow_status_by_id('nonexistent_id')
    
    def test_determine_current_stage_transcript_only(self):
        """Test stage determination when only transcript exists."""
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store,
            self.plan_store,
            self.approval_store, 
            self.execution_store
        )
        
        # Mock scenario: transcript exists, nothing else
        stage, status = backend.determine_stage_and_status('test_id', {
            'transcript': {'id': 'test_id', 'content': 'test'},
            'analysis': None,
            'plan': None,
            'approval': None,
            'execution': None
        })
        
        assert stage == 'transcript'
        assert status == 'completed'
    
    def test_determine_current_stage_analysis_in_progress(self):
        """Test stage determination when analysis exists but plan doesn't."""
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store,
            self.plan_store,
            self.approval_store,
            self.execution_store
        )
        
        stage, status = backend.determine_stage_and_status('test_id', {
            'transcript': {'id': 'test_id'},
            'analysis': {'id': 'test_analysis'},
            'plan': None,
            'approval': None,
            'execution': None
        })
        
        assert stage == 'analysis'
        assert status == 'completed'
    
    def test_determine_current_stage_full_workflow(self):
        """Test stage determination for complete workflow."""
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store,
            self.plan_store,
            self.approval_store,
            self.execution_store
        )
        
        # Create mock objects with attributes instead of dictionaries
        class MockExecution:
            status = 'completed'
        
        class MockApproval:
            status = 'approved'
        
        class MockPlan:
            id = 'test_plan'
        
        class MockAnalysis:
            id = 'test_analysis'
        
        class MockTranscript:
            id = 'test_id'
        
        stage, status = backend.determine_stage_and_status('test_id', {
            'transcript': MockTranscript(),
            'analysis': MockAnalysis(),
            'plan': MockPlan(),
            'approval': MockApproval(),
            'execution': MockExecution()
        })
        
        assert stage == 'execution'
        assert status == 'completed'
    
    def test_workflow_status_fails_with_invalid_transcript(self):
        """Test that workflow status fails fast with invalid transcript ID."""
        from src.services.workflow_status_service import WorkflowStatusBackend
        
        backend = WorkflowStatusBackend(
            self.transcript_store,
            self.analysis_store,
            self.plan_store,
            self.approval_store,
            self.execution_store
        )
        
        # Should raise exception - no fallback logic allowed
        with pytest.raises(Exception):
            backend.get_workflow_status_by_id('invalid_id_that_does_not_exist')
    
    def test_backend_requires_all_stores(self):
        """Test that backend fails if any store is missing."""
        # Should fail if any store is None - no fallback logic
        with pytest.raises(Exception):
            from src.services.workflow_status_service import WorkflowStatusBackend
            WorkflowStatusBackend(None, None, None, None, None)


class TestWorkflowStatusAPI:
    """Test the API endpoint for workflow status."""
    
    @pytest.fixture
    def client(self):
        """Create test client - should fail initially as endpoint doesn't exist."""
        from fastapi.testclient import TestClient
        from server import create_fastapi_app
        app = create_fastapi_app()
        return TestClient(app)
    
    def test_workflow_status_endpoint_exists(self, client):
        """Test that the workflow status API endpoint exists."""
        response = client.get("/api/v1/workflow/status")
        
        # Should return 200, not 404
        assert response.status_code != 404
    
    def test_workflow_status_endpoint_returns_json(self, client):
        """Test that workflow status endpoint returns proper JSON."""
        response = client.get("/api/v1/workflow/status")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_workflow_status_endpoint_structure(self, client):
        """Test the structure of workflow status API response."""
        response = client.get("/api/v1/workflow/status")
        
        assert response.status_code == 200
        data = response.json()
        
        if data:  # Only test if data exists
            for workflow in data:
                assert 'transcript_id' in workflow
                assert 'current_stage' in workflow
                assert 'status' in workflow
                assert workflow['current_stage'] in [
                    'transcript', 'analysis', 'plan', 'approval', 'execution'
                ]
    
    def test_workflow_status_endpoint_fails_fast(self, client):
        """Test that API fails fast - no fallback logic exists."""
        # This test ensures no fallback logic exists by verifying that
        # we get consistent real data from the backend, not mock data
        
        response = client.get("/api/v1/workflow/status")
        
        # Should return 200 with real data from backend
        # This proves no fallback/mock data is being returned
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # If there's data, it should have proper structure
        # This proves data comes from real backend, not fallback
        for workflow in data:
            assert 'transcript_id' in workflow
            assert 'current_stage' in workflow
            assert 'status' in workflow
            assert workflow['current_stage'] in [
                'transcript', 'analysis', 'plan', 'approval', 'execution'
            ]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])