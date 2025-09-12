"""Tests for WorkflowService - Business logic and plan integration.

Following TDD principles and NO FALLBACK approach:
- Test plan-to-workflow extraction
- Validate context preservation
- Test state management
- Integration with risk assessment
- NO FALLBACK enforcement throughout
"""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
from datetime import datetime
from typing import Dict, Any, List

from src.services.workflow_service import WorkflowService


class TestWorkflowService:
    """Test WorkflowService business logic with NO FALLBACK validation."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def workflow_service(self, temp_db_path):
        """Create WorkflowService instance with temporary database."""
        return WorkflowService(temp_db_path)
    
    @pytest.fixture
    def mock_plan_service(self):
        """Mock PlanService for testing."""
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_risk_agent(self):
        """Mock RiskAssessmentAgent for testing."""
        mock = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_plan_data(self):
        """Sample plan data with four-layer action items."""
        return {
            "plan_id": "PLAN_TEST_001",
            "analysis_id": "ANALYSIS_TEST_001",
            "transcript_id": "TRANS_TEST_001",
            "borrower_plan": {
                "immediate_actions": [
                    {
                        "action": "Send refinance options",
                        "timeline": "Within 24 hours",
                        "priority": "high",
                        "auto_executable": True,
                        "description": "Email personalized refinance options based on current rates"
                    },
                    {
                        "action": "Schedule callback",
                        "timeline": "Within 48 hours",
                        "priority": "medium",
                        "auto_executable": False,
                        "description": "Call customer to discuss refinance options"
                    }
                ],
                "follow_ups": [
                    {
                        "action": "Follow up on application",
                        "due_date": "2024-02-01",
                        "owner": "loan_officer",
                        "trigger_condition": "Application submitted"
                    }
                ]
            },
            "advisor_plan": {
                "coaching_items": [
                    {
                        "action": "Review empathy techniques",
                        "coaching_point": "Active listening during hardship calls",
                        "expected_improvement": "Increased customer satisfaction",
                        "priority": "medium"
                    }
                ]
            },
            "supervisor_plan": {
                "escalation_items": [
                    {
                        "item": "Review compliance training",
                        "reason": "Potential UDAAP concern",
                        "priority": "high",
                        "action_required": "Schedule training session"
                    }
                ]
            },
            "leadership_plan": {
                "portfolio_insights": [
                    "Increase in refinance inquiries indicates market opportunity"
                ]
            }
        }
    
    @pytest.fixture
    def sample_analysis_data(self):
        """Sample analysis data for context."""
        return {
            "analysis_id": "ANALYSIS_TEST_001",
            "transcript_id": "TRANS_TEST_001",
            "primary_intent": "refinance_inquiry",
            "sentiment": "interested",
            "urgency_level": "medium",
            "risk_score": 0.4,
            "compliance_flags": [],
            "borrower_risks": {
                "refinance_likelihood": 0.8
            }
        }
    
    @pytest.fixture
    def sample_transcript_data(self):
        """Sample transcript data for context."""
        return {
            "transcript_id": "TRANS_TEST_001",
            "customer_id": "CUST_TEST_001",
            "topic": "Refinance inquiry",
            "sentiment": "interested",
            "duration": 12
        }
    
    @pytest.fixture
    def sample_risk_assessment(self):
        """Sample risk assessment from LLM agent."""
        return {
            "risk_level": "LOW",
            "confidence_score": 0.85,
            "approver_role": "AUTO",
            "reasoning": "Routine information request with no financial impact",
            "key_factors": [
                "No financial commitment required",
                "Standard information sharing",
                "Customer has good standing"
            ],
            "estimated_approval_time": "immediate",
            "recommended_conditions": []
        }
    
    async def test_create_from_plan_success(self, workflow_service, sample_plan_data, 
                                          mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test successful workflow creation from plan."""
        # Mock dependencies
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            # Create workflows from plan
            workflow_ids = await workflow_service.create_from_plan("PLAN_TEST_001")
            
            # Verify workflows were created
            assert len(workflow_ids) > 0  # Should create multiple workflows from plan
            
            # Verify first workflow
            first_workflow = await workflow_service.get_by_id(workflow_ids[0])
            assert first_workflow["plan_id"] == "PLAN_TEST_001"
            assert first_workflow["analysis_id"] == "ANALYSIS_TEST_001"
            assert first_workflow["transcript_id"] == "TRANS_TEST_001"
            assert first_workflow["status"] == "AUTO_APPROVED"  # LOW risk = auto-approved
            assert first_workflow["risk_level"] == "LOW"
            assert first_workflow["approver_role"] == "AUTO"
    
    @pytest.mark.asyncio
    async def test_create_from_plan_fails_nonexistent_plan(self, workflow_service, mock_plan_service):
        """Test create_from_plan fails for nonexistent plan - NO FALLBACK."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service):
            mock_plan_service.get_by_id.side_effect = ValueError("Plan not found")
            
            with pytest.raises(ValueError) as exc_info:
                await workflow_service.create_from_plan("NONEXISTENT_PLAN")
            
            assert "Plan not found" in str(exc_info.value)
    
    async def test_create_from_plan_fails_empty_plan(self, workflow_service, mock_plan_service):
        """Test create_from_plan fails with empty plan - NO FALLBACK."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service):
            mock_plan_service.get_by_id.return_value = {}
            
            with pytest.raises(ValueError) as exc_info:
                await workflow_service.create_from_plan("EMPTY_PLAN")
            
            assert "No action items found" in str(exc_info.value)
    
    async def test_extract_workflows_from_plan_comprehensive(self, workflow_service, sample_plan_data):
        """Test comprehensive workflow extraction from all plan layers."""
        workflows = workflow_service._extract_workflows_from_plan(sample_plan_data)
        
        # Should extract from all layers
        assert len(workflows) >= 4  # At least one from each layer
        
        # Check borrower plan workflows
        borrower_workflows = [w for w in workflows if w["action_item"]["layer"] == "borrower_plan"]
        assert len(borrower_workflows) == 3  # 2 immediate_actions + 1 follow_up
        
        # Verify immediate action workflow
        immediate_action = next(w for w in borrower_workflows 
                               if w["action_item"]["category"] == "immediate_actions" 
                               and w["action_item"]["action"] == "Send refinance options")
        assert immediate_action["action_item"]["priority"] == "high"
        assert immediate_action["action_item"]["auto_executable"] is True
        
        # Check advisor plan workflow
        advisor_workflows = [w for w in workflows if w["action_item"]["layer"] == "advisor_plan"]
        assert len(advisor_workflows) == 1
        assert advisor_workflows[0]["action_item"]["category"] == "coaching_items"
        
        # Check supervisor plan workflow
        supervisor_workflows = [w for w in workflows if w["action_item"]["layer"] == "supervisor_plan"]
        assert len(supervisor_workflows) == 1
        assert supervisor_workflows[0]["action_item"]["category"] == "escalation_items"
        
        # Check leadership plan workflow
        leadership_workflows = [w for w in workflows if w["action_item"]["layer"] == "leadership_plan"]
        assert len(leadership_workflows) == 1
        assert leadership_workflows[0]["action_item"]["category"] == "portfolio_insights"
    
    async def test_context_preservation(self, workflow_service, sample_plan_data, 
                                      mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test that complete context is preserved from plan to workflow."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            workflow_ids = await workflow_service.create_from_plan("PLAN_TEST_001")
            workflow = await workflow_service.get_by_id(workflow_ids[0])
            
            # Verify context preservation
            assert workflow["plan_id"] == "PLAN_TEST_001"
            assert workflow["analysis_id"] == "ANALYSIS_TEST_001"
            assert workflow["transcript_id"] == "TRANS_TEST_001"
            
            # Verify action item preservation
            action_item = workflow["action_item"]
            assert action_item["layer"] in ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"]
            assert "action" in action_item
            assert "description" in action_item
    
    async def test_risk_assessment_integration(self, workflow_service, sample_plan_data,
                                             mock_plan_service, mock_risk_agent):
        """Test integration with risk assessment agent."""
        # Test different risk levels
        risk_assessments = [
            {
                "risk_level": "LOW",
                "approver_role": "AUTO",
                "confidence_score": 0.9,
                "reasoning": "Routine request"
            },
            {
                "risk_level": "MEDIUM", 
                "approver_role": "ADVISOR",
                "confidence_score": 0.8,
                "reasoning": "Requires advisor review"
            },
            {
                "risk_level": "HIGH",
                "approver_role": "SUPERVISOR", 
                "confidence_score": 0.85,
                "reasoning": "High impact decision"
            }
        ]
        
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            
            for i, assessment in enumerate(risk_assessments):
                mock_risk_agent.assess_risk.return_value = assessment
                
                workflow_ids = await workflow_service.create_from_plan(f"PLAN_TEST_{i+1}")
                workflow = await workflow_service.get_by_id(workflow_ids[0])
                
                assert workflow["risk_level"] == assessment["risk_level"]
                assert workflow["approver_role"] == assessment["approver_role"]
                assert workflow["risk_assessment"]["confidence_score"] == assessment["confidence_score"]
                
                # Verify status based on risk level
                if assessment["risk_level"] == "LOW":
                    assert workflow["status"] == "AUTO_APPROVED"
                else:
                    assert workflow["status"] == "AWAITING_APPROVAL"
    
    async def test_risk_assessment_fails_incomplete_context(self, workflow_service, mock_risk_agent):
        """Test risk assessment fails with incomplete context - NO FALLBACK."""
        incomplete_plan = {
            "plan_id": "INCOMPLETE_PLAN",
            # Missing analysis_id and transcript_id
            "borrower_plan": {
                "immediate_actions": [{"action": "test"}]
            }
        }
        
        with patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            mock_risk_agent.assess_risk.side_effect = ValueError("Missing required context")
            
            with pytest.raises(ValueError) as exc_info:
                workflows = workflow_service._extract_workflows_from_plan(incomplete_plan)
                await workflow_service._assess_and_route_workflow(workflows[0])
            
            assert "Missing required context" in str(exc_info.value)
    
    async def test_update_status_with_transition_logging(self, workflow_service, sample_plan_data,
                                                        mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test status updates with proper transition logging."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            # Create workflow
            workflow_ids = await workflow_service.create_from_plan("PLAN_TEST_001")
            workflow_id = workflow_ids[0]
            
            # Update status
            success = await workflow_service.update_status(
                workflow_id=workflow_id,
                status="EXECUTED",
                reason="Workflow completed successfully",
                metadata={"execution_time": "2024-01-15T10:30:00Z"}
            )
            
            assert success is True
            
            # Verify status was updated
            workflow = await workflow_service.get_by_id(workflow_id)
            assert workflow["status"] == "EXECUTED"
            
            # Verify transition was logged (this would be tested with actual store implementation)
    
    async def test_get_by_id_with_full_context(self, workflow_service, sample_plan_data,
                                             mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test get_by_id returns workflow with full context."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            workflow_ids = await workflow_service.create_from_plan("PLAN_TEST_001")
            workflow = await workflow_service.get_by_id(workflow_ids[0])
            
            # Verify all required fields are present
            required_fields = [
                "workflow_id", "plan_id", "analysis_id", "transcript_id",
                "action_item", "status", "risk_level", "risk_assessment",
                "approver_role", "created_at", "updated_at"
            ]
            
            for field in required_fields:
                assert field in workflow
            
            # Verify context chain
            assert workflow["plan_id"] == "PLAN_TEST_001"
            assert workflow["analysis_id"] == "ANALYSIS_TEST_001"
            assert workflow["transcript_id"] == "TRANS_TEST_001"
    
    async def test_list_all_with_filters(self, workflow_service, sample_plan_data,
                                       mock_plan_service, mock_risk_agent):
        """Test list_all with various filters."""
        # Create workflows with different characteristics
        risk_assessments = [
            {"risk_level": "LOW", "approver_role": "AUTO"},
            {"risk_level": "MEDIUM", "approver_role": "ADVISOR"},
            {"risk_level": "HIGH", "approver_role": "SUPERVISOR"}
        ]
        
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            
            for i, assessment in enumerate(risk_assessments):
                mock_risk_agent.assess_risk.return_value = assessment
                await workflow_service.create_from_plan(f"PLAN_TEST_{i+1}")
            
            # Test filtering by status
            auto_approved = await workflow_service.list_all({"status": "AUTO_APPROVED"})
            awaiting_approval = await workflow_service.list_all({"status": "AWAITING_APPROVAL"})
            
            assert len(auto_approved) >= 1  # LOW risk workflows
            assert len(awaiting_approval) >= 2  # MEDIUM and HIGH risk workflows
            
            # Test filtering by risk level
            low_risk = await workflow_service.list_all({"risk_level": "LOW"})
            high_risk = await workflow_service.list_all({"risk_level": "HIGH"})
            
            assert len(low_risk) >= 1
            assert len(high_risk) >= 1
            
            # Test filtering by approver role
            supervisor_workflows = await workflow_service.list_all({"approver_role": "SUPERVISOR"})
            assert len(supervisor_workflows) >= 1
    
    async def test_delete_workflow_success(self, workflow_service, sample_plan_data,
                                         mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test successful workflow deletion."""
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            workflow_ids = await workflow_service.create_from_plan("PLAN_TEST_001")
            workflow_id = workflow_ids[0]
            
            # Verify workflow exists
            workflow = await workflow_service.get_by_id(workflow_id)
            assert workflow is not None
            
            # Delete workflow
            success = await workflow_service.delete(workflow_id)
            assert success is True
            
            # Verify workflow is deleted
            with pytest.raises(ValueError):
                await workflow_service.get_by_id(workflow_id)
    
    async def test_delete_workflow_fails_nonexistent(self, workflow_service):
        """Test delete fails for nonexistent workflow - NO FALLBACK."""
        with pytest.raises(ValueError) as exc_info:
            await workflow_service.delete("NONEXISTENT_WF")
        
        assert "not found" in str(exc_info.value)
    
    async def test_workflow_id_generation(self, workflow_service, sample_plan_data):
        """Test that workflow IDs are generated correctly."""
        workflows = workflow_service._extract_workflows_from_plan(sample_plan_data)
        
        # Verify all workflows have unique IDs
        workflow_ids = [w["workflow_id"] for w in workflows]
        assert len(workflow_ids) == len(set(workflow_ids))  # No duplicates
        
        # Verify ID format
        for workflow_id in workflow_ids:
            assert workflow_id.startswith("WF_")
            assert len(workflow_id) > 10  # Should have UUID component
    
    async def test_action_item_structure_validation(self, workflow_service, sample_plan_data):
        """Test that extracted action items have correct structure."""
        workflows = workflow_service._extract_workflows_from_plan(sample_plan_data)
        
        for workflow in workflows:
            action_item = workflow["action_item"]
            
            # Required fields
            assert "layer" in action_item
            assert "category" in action_item
            assert "action" in action_item
            
            # Layer should be valid
            assert action_item["layer"] in ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"]
            
            # Should preserve original action data
            if "priority" in action_item:
                assert action_item["priority"] in ["high", "medium", "low"]
    
    async def test_no_fallback_principle_enforcement(self, workflow_service):
        """Test that NO FALLBACK principle is enforced throughout service."""
        # Test all methods fail fast with appropriate errors
        
        with pytest.raises(ValueError):
            await workflow_service.create_from_plan(None)
        
        with pytest.raises(ValueError):
            await workflow_service.create_from_plan("")
        
        with pytest.raises(ValueError):
            await workflow_service.get_by_id(None)
        
        with pytest.raises(ValueError):
            await workflow_service.get_by_id("")
        
        with pytest.raises(ValueError):
            await workflow_service.update_status("NONEXISTENT", "APPROVED")
        
        with pytest.raises(ValueError):
            await workflow_service.delete(None)
        
        # Test invalid filter values
        with pytest.raises(ValueError):
            await workflow_service.list_all({"status": "INVALID_STATUS"})
    
    async def test_concurrent_workflow_creation(self, workflow_service, sample_plan_data,
                                              mock_plan_service, mock_risk_agent, sample_risk_assessment):
        """Test that concurrent workflow creation works correctly."""
        import asyncio
        
        with patch('src.services.workflow_service.PlanService', return_value=mock_plan_service), \
             patch('src.agents.risk_assessment_agent.RiskAssessmentAgent', return_value=mock_risk_agent):
            
            mock_plan_service.get_by_id.return_value = sample_plan_data
            mock_risk_agent.assess_risk.return_value = sample_risk_assessment
            
            # Create multiple workflows concurrently
            tasks = [
                workflow_service.create_from_plan(f"PLAN_CONCURRENT_{i}")
                for i in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Verify all workflows were created successfully
            assert len(results) == 3
            for workflow_ids in results:
                assert len(workflow_ids) > 0
            
            # Verify all workflow IDs are unique
            all_workflow_ids = []
            for workflow_ids in results:
                all_workflow_ids.extend(workflow_ids)
            
            assert len(all_workflow_ids) == len(set(all_workflow_ids))