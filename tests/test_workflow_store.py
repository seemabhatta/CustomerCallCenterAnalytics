"""Tests for WorkflowStore - Database operations and schema validation.

Following TDD principles and NO FALLBACK approach:
- Fail fast if required data is missing
- No default values for critical fields
- Strict validation of all operations
- Complete foreign key constraint enforcement
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime
from typing import Dict, Any

from src.storage.workflow_store import WorkflowStore


class TestWorkflowStore:
    """Test WorkflowStore database operations with NO FALLBACK validation."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def workflow_store(self, temp_db_path):
        """Create WorkflowStore instance with temporary database."""
        return WorkflowStore(temp_db_path)
    
    @pytest.fixture
    def sample_workflow_data(self):
        """Sample workflow data for testing."""
        return {
            "id": "WF_TEST_001",
            "plan_id": "PLAN_TEST_001", 
            "analysis_id": "ANALYSIS_TEST_001",
            "transcript_id": "TRANS_TEST_001",
            "workflow_data": {
                "workflow_steps": [
                    "Review customer refinance eligibility",
                    "Send personalized refinance options",
                    "Schedule follow-up call"
                ],
                "complexity_assessment": "medium",
                "dependencies": ["customer_credit_check", "rate_analysis"]
            },
            "status": "PENDING_ASSESSMENT",
            "risk_level": "MEDIUM",
            "context_data": {
                "pipeline_stage": "workflow_extraction",
                "extraction_timestamp": "2024-01-01T10:00:00Z",
                "plan_id": "PLAN_TEST_001",
                "analysis_id": "ANALYSIS_TEST_001",
                "transcript_id": "TRANS_TEST_001"
            },
            "risk_reasoning": "Medium complexity workflow with customer financial impact",
            "approval_reasoning": "Requires advisor approval due to financial implications",
            "requires_human_approval": True,
            "assigned_approver": "advisor_001"
        }
    
    def test_create_workflow_success(self, workflow_store, sample_workflow_data):
        """Test successful workflow creation."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        assert workflow_id == "WF_TEST_001"
        
        # Verify workflow was created correctly
        workflow = workflow_store.get_by_id(workflow_id)
        assert workflow["id"] == "WF_TEST_001"
        assert workflow["plan_id"] == "PLAN_TEST_001"
        assert workflow["status"] == "PENDING_ASSESSMENT"
        assert workflow["risk_level"] == "MEDIUM"
        assert workflow["workflow_data"]["workflow_steps"][0] == "Review customer refinance eligibility"
        assert workflow["created_at"] is not None
        assert workflow["updated_at"] is not None
    
    def test_create_workflow_fails_missing_required_fields(self, workflow_store):
        """Test workflow creation fails with missing required fields - NO FALLBACK."""
        incomplete_data = {
            "id": "WF_INCOMPLETE_001",
            "plan_id": "PLAN_001"
            # Missing required fields: analysis_id, transcript_id, workflow_data, risk_level, status, context_data
        }
        
        with pytest.raises(ValueError) as exc_info:
            workflow_store.create(incomplete_data)
        
        assert "Required field missing or null" in str(exc_info.value)
    
    def test_create_workflow_fails_invalid_status(self, workflow_store, sample_workflow_data):
        """Test workflow creation fails with invalid status - NO FALLBACK."""
        sample_workflow_data["status"] = "INVALID_STATUS"
        
        with pytest.raises(ValueError) as exc_info:
            workflow_store.create(sample_workflow_data)
        
        assert "Invalid status" in str(exc_info.value)
    
    def test_create_workflow_fails_invalid_risk_level(self, workflow_store, sample_workflow_data):
        """Test workflow creation fails with invalid risk level - NO FALLBACK."""
        sample_workflow_data["risk_level"] = "INVALID_RISK"
        
        with pytest.raises(ValueError) as exc_info:
            workflow_store.create(sample_workflow_data)
        
        assert "Invalid risk_level" in str(exc_info.value)
    
    def test_create_workflow_fails_duplicate_id(self, workflow_store, sample_workflow_data):
        """Test workflow creation fails with duplicate workflow_id - NO FALLBACK."""
        # Create first workflow
        workflow_store.create(sample_workflow_data)
        
        # Try to create another with same ID - SQLite will raise UNIQUE constraint error
        with pytest.raises(Exception):  # SQLite constraint error, not ValueError
            workflow_store.create(sample_workflow_data)
    
    def test_get_by_id_success(self, workflow_store, sample_workflow_data):
        """Test successful workflow retrieval by ID."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        workflow = workflow_store.get_by_id(workflow_id)
        
        assert workflow["id"] == workflow_id
        assert workflow["plan_id"] == "PLAN_TEST_001"
        assert workflow["status"] == "PENDING_ASSESSMENT"
        assert isinstance(workflow["workflow_data"], dict)
        assert workflow["created_at"] is not None
    
    def test_get_by_id_fails_nonexistent(self, workflow_store):
        """Test get_by_id fails for nonexistent workflow - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            workflow_store.get_by_id("NONEXISTENT_WF")
        
        assert "not found" in str(exc_info.value)
    
    def test_get_by_id_fails_empty_id(self, workflow_store):
        """Test get_by_id fails with empty ID - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            workflow_store.get_by_id("")
        
        assert "workflow_id cannot be empty" in str(exc_info.value)
    
    def test_get_all_empty_store(self, workflow_store):
        """Test get_all returns empty list for empty store."""
        workflows = workflow_store.get_all()
        assert workflows == []
    
    def test_get_all_with_workflows(self, workflow_store, sample_workflow_data):
        """Test get_all returns all workflows."""
        # Create multiple workflows
        workflow1 = sample_workflow_data.copy()
        workflow1["workflow_id"] = "WF_001"
        workflow_store.create(workflow1)
        
        workflow2 = sample_workflow_data.copy()
        workflow2["workflow_id"] = "WF_002"
        workflow2["status"] = "AWAITING_APPROVAL"
        workflow_store.create(workflow2)
        
        workflows = workflow_store.get_all()
        
        assert len(workflows) == 2
        workflow_ids = [w["workflow_id"] for w in workflows]
        assert "WF_001" in workflow_ids
        assert "WF_002" in workflow_ids
    
    def test_get_all_with_filters(self, workflow_store, sample_workflow_data):
        """Test get_all with status filtering."""
        # Create workflows with different statuses
        workflow1 = sample_workflow_data.copy()
        workflow1["workflow_id"] = "WF_001"
        workflow1["status"] = "PENDING_ASSESSMENT"
        workflow_store.create(workflow1)
        
        workflow2 = sample_workflow_data.copy()
        workflow2["workflow_id"] = "WF_002"
        workflow2["status"] = "AWAITING_APPROVAL"
        workflow_store.create(workflow2)
        
        # Filter by status
        pending_workflows = workflow_store.get_all({"status": "PENDING_ASSESSMENT"})
        assert len(pending_workflows) == 1
        assert pending_workflows[0]["workflow_id"] == "WF_001"
        
        awaiting_workflows = workflow_store.get_all({"status": "AWAITING_APPROVAL"})
        assert len(awaiting_workflows) == 1
        assert awaiting_workflows[0]["workflow_id"] == "WF_002"
    
    def test_update_workflow_success(self, workflow_store, sample_workflow_data):
        """Test successful workflow update."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        updates = {
            "status": "AWAITING_APPROVAL",
            "risk_level": "MEDIUM",
            "approver_role": "SUPERVISOR",
            "risk_assessment": {
                "risk_level": "MEDIUM",
                "confidence": 0.85,
                "reasoning": "Moderate financial impact"
            }
        }
        
        success = workflow_store.update(workflow_id, updates)
        assert success is True
        
        # Verify updates
        updated_workflow = workflow_store.get_by_id(workflow_id)
        assert updated_workflow["status"] == "AWAITING_APPROVAL"
        assert updated_workflow["risk_level"] == "MEDIUM"
        assert updated_workflow["approver_role"] == "SUPERVISOR"
        assert updated_workflow["risk_assessment"]["confidence"] == 0.85
        assert updated_workflow["updated_at"] > updated_workflow["created_at"]
    
    def test_update_workflow_fails_nonexistent(self, workflow_store):
        """Test update fails for nonexistent workflow - NO FALLBACK."""
        updates = {"status": "APPROVED"}
        
        with pytest.raises(ValueError) as exc_info:
            workflow_store.update("NONEXISTENT_WF", updates)
        
        assert "not found" in str(exc_info.value)
    
    def test_update_workflow_fails_invalid_status(self, workflow_store, sample_workflow_data):
        """Test update fails with invalid status - NO FALLBACK."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        updates = {"status": "INVALID_STATUS"}
        
        with pytest.raises(ValueError) as exc_info:
            workflow_store.update(workflow_id, updates)
        
        assert "Invalid status" in str(exc_info.value)
    
    def test_delete_workflow_success(self, workflow_store, sample_workflow_data):
        """Test successful workflow deletion."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        # Verify workflow exists
        workflow = workflow_store.get_by_id(workflow_id)
        assert workflow is not None
        
        # Delete workflow
        success = workflow_store.delete(workflow_id)
        assert success is True
        
        # Verify workflow is deleted
        with pytest.raises(ValueError):
            workflow_store.get_by_id(workflow_id)
    
    def test_delete_workflow_fails_nonexistent(self, workflow_store):
        """Test delete fails for nonexistent workflow - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            workflow_store.delete("NONEXISTENT_WF")
        
        assert "not found" in str(exc_info.value)
    
    def test_get_by_status(self, workflow_store, sample_workflow_data):
        """Test retrieving workflows by status."""
        # Create workflows with different statuses
        workflow1 = sample_workflow_data.copy()
        workflow1["workflow_id"] = "WF_001"
        workflow1["status"] = "PENDING_ASSESSMENT"
        workflow_store.create(workflow1)
        
        workflow2 = sample_workflow_data.copy()
        workflow2["workflow_id"] = "WF_002"
        workflow2["status"] = "AWAITING_APPROVAL"
        workflow_store.create(workflow2)
        
        workflow3 = sample_workflow_data.copy()
        workflow3["workflow_id"] = "WF_003"
        workflow3["status"] = "AWAITING_APPROVAL"
        workflow_store.create(workflow3)
        
        # Test status filtering
        pending = workflow_store.get_by_status("PENDING_ASSESSMENT")
        assert len(pending) == 1
        assert pending[0]["workflow_id"] == "WF_001"
        
        awaiting = workflow_store.get_by_status("AWAITING_APPROVAL")
        assert len(awaiting) == 2
        workflow_ids = [w["workflow_id"] for w in awaiting]
        assert "WF_002" in workflow_ids
        assert "WF_003" in workflow_ids
    
    def test_get_by_approver_role(self, workflow_store, sample_workflow_data):
        """Test retrieving workflows by approver role."""
        # Create workflows with different approver roles
        workflow1 = sample_workflow_data.copy()
        workflow1["workflow_id"] = "WF_001"
        workflow1["approver_role"] = "ADVISOR"
        workflow_store.create(workflow1)
        
        workflow2 = sample_workflow_data.copy()
        workflow2["workflow_id"] = "WF_002"
        workflow2["approver_role"] = "SUPERVISOR"
        workflow_store.create(workflow2)
        
        # Test role filtering
        advisor_workflows = workflow_store.get_by_approver_role("ADVISOR")
        assert len(advisor_workflows) == 1
        assert advisor_workflows[0]["workflow_id"] == "WF_001"
        
        supervisor_workflows = workflow_store.get_by_approver_role("SUPERVISOR")
        assert len(supervisor_workflows) == 1
        assert supervisor_workflows[0]["workflow_id"] == "WF_002"
    
    def test_add_transition_success(self, workflow_store, sample_workflow_data):
        """Test successful state transition logging."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        # Add transition
        workflow_store.add_transition(
            workflow_id=workflow_id,
            from_status="PENDING_ASSESSMENT",
            to_status="AWAITING_APPROVAL",
            reason="Risk assessment completed",
            metadata={"risk_level": "MEDIUM", "assessor": "system"}
        )
        
        # Verify transition was logged
        transitions = workflow_store.get_transitions(workflow_id)
        assert len(transitions) == 1
        
        transition = transitions[0]
        assert transition["workflow_id"] == workflow_id
        assert transition["from_status"] == "PENDING_ASSESSMENT"
        assert transition["to_status"] == "AWAITING_APPROVAL"
        assert transition["reason"] == "Risk assessment completed"
        assert transition["metadata"]["risk_level"] == "MEDIUM"
        assert transition["created_at"] is not None
    
    def test_add_transition_fails_nonexistent_workflow(self, workflow_store):
        """Test add_transition fails for nonexistent workflow - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            workflow_store.add_transition(
                workflow_id="NONEXISTENT_WF",
                from_status="PENDING_ASSESSMENT", 
                to_status="AWAITING_APPROVAL",
                reason="Test transition"
            )
        
        assert "not found" in str(exc_info.value)
    
    def test_get_transitions_empty(self, workflow_store, sample_workflow_data):
        """Test get_transitions returns empty list for workflow with no transitions."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        transitions = workflow_store.get_transitions(workflow_id)
        assert transitions == []
    
    def test_get_transitions_multiple(self, workflow_store, sample_workflow_data):
        """Test get_transitions with multiple transitions."""
        workflow_id = workflow_store.create(sample_workflow_data)
        
        # Add multiple transitions
        workflow_store.add_transition(
            workflow_id, "PENDING_ASSESSMENT", "AWAITING_APPROVAL", "Risk assessed"
        )
        workflow_store.add_transition(
            workflow_id, "AWAITING_APPROVAL", "APPROVED", "Approved by supervisor"
        )
        workflow_store.add_transition(
            workflow_id, "APPROVED", "EXECUTED", "Workflow executed successfully"
        )
        
        transitions = workflow_store.get_transitions(workflow_id)
        assert len(transitions) == 3
        
        # Verify chronological order
        assert transitions[0]["from_status"] == "PENDING_ASSESSMENT"
        assert transitions[1]["from_status"] == "AWAITING_APPROVAL"
        assert transitions[2]["from_status"] == "APPROVED"
    
    def test_database_schema_validation(self, workflow_store):
        """Test that database schema enforces constraints."""
        # Test workflow table exists with correct structure
        conn = sqlite3.connect(workflow_store.db_path)
        cursor = conn.cursor()
        
        # Check workflows table schema
        cursor.execute("PRAGMA table_info(workflows)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = [
            'id', 'plan_id', 'analysis_id', 'transcript_id',
            'workflow_data', 'status', 'risk_level', 'context_data',
            'risk_reasoning', 'approval_reasoning', 'requires_human_approval',
            'assigned_approver', 'approved_by', 'approved_at', 'rejected_by',
            'rejected_at', 'rejection_reason', 'executed_at', 'execution_results',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in column_names
        
        # Check workflow_state_transitions table schema
        cursor.execute("PRAGMA table_info(workflow_state_transitions)")
        transition_columns = cursor.fetchall()
        transition_column_names = [col[1] for col in transition_columns]
        
        required_transition_columns = [
            'id', 'workflow_id', 'from_status', 'to_status', 
            'transition_reason', 'transitioned_by', 'transitioned_at'
        ]
        
        for col in required_transition_columns:
            assert col in transition_column_names
        
        conn.close()
    
    def test_no_fallback_principle_throughout(self, workflow_store):
        """Test that NO FALLBACK principle is enforced throughout the store."""
        # Test all methods fail fast with appropriate errors
        
        # Empty/None values should fail
        with pytest.raises((ValueError, TypeError)):
            workflow_store.create(None)
        
        with pytest.raises(ValueError):
            workflow_store.create({})
        
        with pytest.raises(ValueError):
            workflow_store.get_by_id(None)
        
        with pytest.raises(ValueError):
            workflow_store.get_by_id("")
        
        with pytest.raises(ValueError):
            workflow_store.update("NONEXISTENT", {})
        
        with pytest.raises(ValueError):
            workflow_store.delete(None)
        
        # Invalid enum values should fail
        sample_data = {
            "workflow_id": "WF_TEST",
            "plan_id": "PLAN_TEST",
            "analysis_id": "ANALYSIS_TEST", 
            "transcript_id": "TRANS_TEST",
            "action_item": {"action": "test"},
            "status": "INVALID_STATUS"
        }
        
        with pytest.raises(ValueError):
            workflow_store.create(sample_data)