"""Test cases to validate the risk_level constraint bug fix.

This test module verifies that the database constraint error 
"CHECK constraint failed: risk_level IN ('LOW', 'MEDIUM', 'HIGH')"
has been fixed in the parallel workflow processing.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import AsyncMock, patch
from src.storage.workflow_store import WorkflowStore
from src.services.workflow_service import WorkflowService
from src.agents.risk_assessment_agent import RiskAssessmentAgent


class TestRiskLevelConstraintFix:
    """Test suite for validating the risk_level constraint fixes."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def workflow_store(self, temp_db):
        """Create a workflow store instance."""
        return WorkflowStore(temp_db)
    
    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            'plan_id': 'test-plan-123',
            'analysis_id': 'test-analysis-456',
            'transcript_id': 'test-transcript-789',
            'workflow_data': {
                'title': 'Test Action Item',
                'description': 'Test action item description',
                'priority': 'MEDIUM'
            },
            'workflow_type': 'BORROWER',
            'context_data': {
                'test_context': 'test_value'
            },
            'risk_assessment': {
                'risk_level': 'LOW',
                'reasoning': 'This is a low risk action item',
                'factors': ['standard procedure', 'routine task'],
                'score': 0.2
            },
            'approval_routing': {
                'requires_human_approval': False,
                'initial_status': 'AUTO_APPROVED',
                'routing_reasoning': 'Low risk item can be auto-approved',
                'suggested_approver_level': 'advisor'
            }
        }

    def test_workflow_store_create_bulk_valid_risk_levels(self, workflow_store, sample_workflow_data):
        """Test that create_bulk properly extracts and validates risk levels."""
        
        # Test data with different valid risk levels
        test_workflows = []
        for risk_level in ['LOW', 'MEDIUM', 'HIGH']:
            workflow = sample_workflow_data.copy()
            workflow['risk_assessment'] = {
                'risk_level': risk_level,
                'reasoning': f'This is a {risk_level.lower()} risk action item',
                'factors': [f'{risk_level.lower()} risk factors'],
                'score': {'LOW': 0.2, 'MEDIUM': 0.5, 'HIGH': 0.8}[risk_level]
            }
            workflow['plan_id'] = f'plan-{risk_level.lower()}'
            test_workflows.append(workflow)
        
        # This should not raise a constraint error
        workflow_ids = workflow_store.create_bulk(test_workflows)
        
        assert len(workflow_ids) == 3
        
        # Verify that all workflows were created with correct risk levels
        for i, workflow_id in enumerate(workflow_ids):
            workflow = workflow_store.get_by_id(workflow_id)
            expected_risk = ['LOW', 'MEDIUM', 'HIGH'][i]
            assert workflow['risk_level'] == expected_risk
            assert workflow['workflow_type'] == 'BORROWER'

    def test_workflow_store_create_bulk_invalid_risk_level_fallback(self, workflow_store, sample_workflow_data):
        """Test that create_bulk handles invalid risk levels by falling back to MEDIUM."""
        
        # Test with invalid risk level
        invalid_workflow = sample_workflow_data.copy()
        invalid_workflow['risk_assessment'] = {
            'risk_level': 'INVALID_LEVEL',  # This should be handled
            'reasoning': 'This has an invalid risk level',
            'factors': ['invalid factor'],
            'score': 0.5
        }
        
        # This should not raise a constraint error - should fallback to MEDIUM
        workflow_ids = workflow_store.create_bulk([invalid_workflow])
        
        assert len(workflow_ids) == 1
        
        # Verify that the workflow was created with fallback risk level
        workflow = workflow_store.get_by_id(workflow_ids[0])
        assert workflow['risk_level'] == 'MEDIUM'  # Should fallback to MEDIUM
        assert workflow['workflow_type'] == 'BORROWER'

    def test_workflow_store_create_bulk_missing_risk_assessment_fallback(self, workflow_store, sample_workflow_data):
        """Test that create_bulk handles missing risk assessment by using defaults."""
        
        # Test with missing risk_assessment
        minimal_workflow = {
            'plan_id': 'test-plan-minimal',
            'analysis_id': 'test-analysis-minimal',
            'transcript_id': 'test-transcript-minimal',
            'workflow_data': {'title': 'Minimal Action Item'},
            'workflow_type': 'ADVISOR',
            'context_data': {}
            # No risk_assessment or approval_routing
        }
        
        # This should not raise a constraint error - should use defaults
        workflow_ids = workflow_store.create_bulk([minimal_workflow])
        
        assert len(workflow_ids) == 1
        
        # Verify that the workflow was created with default values
        workflow = workflow_store.get_by_id(workflow_ids[0])
        assert workflow['risk_level'] == 'MEDIUM'  # Default fallback
        assert workflow['status'] == 'PENDING_ASSESSMENT'  # Default status
        assert workflow['requires_human_approval'] is True  # Default approval requirement
        assert workflow['workflow_type'] == 'ADVISOR'

    def test_workflow_store_all_select_queries_include_workflow_type(self, workflow_store, sample_workflow_data):
        """Test that all SELECT queries properly include workflow_type field."""
        
        # Create a workflow
        workflow_ids = workflow_store.create_bulk([sample_workflow_data])
        workflow_id = workflow_ids[0]
        plan_id = sample_workflow_data['plan_id']
        
        # Test all get methods that should return workflow_type
        workflow = workflow_store.get_by_id(workflow_id)
        assert 'workflow_type' in workflow
        assert workflow['workflow_type'] == 'BORROWER'
        
        workflows_by_plan = workflow_store.get_by_plan_id(plan_id)
        assert len(workflows_by_plan) > 0
        assert 'workflow_type' in workflows_by_plan[0]
        assert workflows_by_plan[0]['workflow_type'] == 'BORROWER'
        
        workflows_by_status = workflow_store.get_by_status('AUTO_APPROVED')
        if workflows_by_status:
            assert 'workflow_type' in workflows_by_status[0]
        
        workflows_by_risk = workflow_store.get_by_risk_level('LOW')
        if workflows_by_risk:
            assert 'workflow_type' in workflows_by_risk[0]
        
        all_workflows = workflow_store.get_all(limit=1)
        assert len(all_workflows) > 0
        assert 'workflow_type' in all_workflows[0]
        assert all_workflows[0]['workflow_type'] == 'BORROWER'

    def test_risk_assessment_agent_constructor_fix(self):
        """Test that RiskAssessmentAgent constructor properly initializes all required attributes."""
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            agent = RiskAssessmentAgent()
            
            # Should have both new structured output wrapper and legacy attributes
            assert hasattr(agent, 'llm')  # New structured outputs wrapper
            assert hasattr(agent, 'client')  # Legacy attribute for backward compatibility
            assert hasattr(agent, 'model')  # Legacy attribute for backward compatibility
            assert hasattr(agent, 'agent_id')
            assert hasattr(agent, 'agent_version')
            
            # Verify the client and model are properly initialized
            assert agent.client is not None
            assert agent.model in ['gpt-4o', 'gpt-4o-mini']  # Valid default models
            assert agent.agent_version == "v2.0"

    @patch('src.agents.risk_assessment_agent.RiskAssessmentAgent.assess_action_item_risk')
    @patch('src.agents.risk_assessment_agent.RiskAssessmentAgent.determine_action_item_approval_routing')
    @patch('src.agents.risk_assessment_agent.RiskAssessmentAgent.extract_individual_action_items')
    @patch('src.storage.action_plan_store.ActionPlanStore.get_by_id')
    @pytest.mark.asyncio
    async def test_workflow_service_parallel_processing_no_constraint_error(
        self,
        mock_get_plan,
        mock_extract_items,
        mock_routing,
        mock_risk_assessment,
        temp_db
    ):
        """Test that parallel workflow processing doesn't cause constraint errors."""
        
        # Mock the action plan
        mock_plan_data = {
            'transcript_id': 'test-transcript',
            'analysis_id': 'test-analysis',
            'borrower': {'actions': ['Test borrower action']},
            'advisor': {'actions': ['Test advisor action']},
            'supervisor': {'actions': ['Test supervisor action']},
            'leadership': {'actions': ['Test leadership action']}
        }
        mock_get_plan.return_value = mock_plan_data
        
        # Mock individual action items extraction
        mock_extract_items.return_value = [
            {
                'title': 'Test Action Item',
                'description': 'Test description',
                'priority': 'MEDIUM'
            }
        ]
        
        # Mock risk assessment with valid risk level
        mock_risk_assessment.return_value = {
            'risk_level': 'LOW',  # Valid risk level
            'reasoning': 'Low risk action',
            'factors': ['routine task'],
            'score': 0.2
        }
        
        # Mock approval routing
        mock_routing.return_value = {
            'requires_human_approval': False,
            'initial_status': 'AUTO_APPROVED',
            'routing_reasoning': 'Auto-approved low risk item',
            'suggested_approver_level': 'advisor'
        }
        
        # Create workflow service
        workflow_service = WorkflowService(temp_db)
        
        # This should not raise any database constraint errors
        try:
            workflows = await workflow_service.extract_all_workflows_from_plan('test-plan-123')
            
            # Verify workflows were created successfully
            assert isinstance(workflows, list)
            # Should have workflows for each type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            # Each with the mocked action item
            
            # Verify all workflows have valid risk levels
            for workflow in workflows:
                assert workflow['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
                assert 'workflow_type' in workflow
                assert workflow['workflow_type'] in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
                
        except Exception as e:
            # Should not get constraint errors
            assert "CHECK constraint failed: risk_level" not in str(e)
            # Re-raise if it's a different error for debugging
            raise

    def test_no_pending_risk_level_in_database_constraints(self, workflow_store):
        """Test that database constraints don't allow PENDING risk level."""
        
        # Try to directly insert a workflow with PENDING risk level (should fail)
        invalid_workflow = {
            'plan_id': 'test-plan-invalid',
            'analysis_id': 'test-analysis-invalid',
            'transcript_id': 'test-transcript-invalid',
            'workflow_data': {'title': 'Invalid Action Item'},
            'workflow_type': 'BORROWER',
            'context_data': {},
            'risk_assessment': {
                'risk_level': 'PENDING',  # This is invalid
                'reasoning': 'Pending assessment'
            }
        }
        
        # The create_bulk method should handle this by falling back to MEDIUM
        # instead of allowing the invalid PENDING value to reach the database
        workflow_ids = workflow_store.create_bulk([invalid_workflow])
        
        # Verify it was created with valid fallback value
        workflow = workflow_store.get_by_id(workflow_ids[0])
        assert workflow['risk_level'] == 'MEDIUM'  # Should be fallback, not PENDING

if __name__ == "__main__":
    pytest.main([__file__])