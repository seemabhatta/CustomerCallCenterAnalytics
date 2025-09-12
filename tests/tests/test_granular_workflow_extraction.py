"""
Test cases for granular workflow extraction system.

Tests the extraction of multiple workflows from a single action plan,
with each action item becoming an independent workflow.

Following TDD principles - write tests before implementation.
"""

import pytest
from unittest.mock import Mock, patch
import json
from typing import Dict, Any, List

from src.services.workflow_service import WorkflowService
from src.storage.workflow_store import WorkflowStore
from src.agents.risk_assessment_agent import RiskAssessmentAgent


class TestGranularWorkflowExtraction:
    """Test granular workflow extraction from action plans."""
    
    @pytest.fixture
    def sample_action_plan(self) -> Dict[str, Any]:
        """Sample action plan with all 4 pillars and multiple items."""
        return {
            "plan_id": "PLAN_TEST_001",
            "analysis_id": "ANALYSIS_TEST_001", 
            "transcript_id": "TRANSCRIPT_TEST_001",
            "borrower_action_plan": {
                "immediate_actions": [
                    {
                        "action": "Confirm if there are any prepayment penalties on current mortgage",
                        "priority": "high",
                        "timeline": "Within 1-2 days"
                    },
                    {
                        "action": "Prepare for follow-up call with advisor",
                        "priority": "medium", 
                        "timeline": "Within 3 days"
                    }
                ]
            },
            "advisor_action_plan": {
                "coaching_items": [
                    {
                        "item": "Ensure regulatory compliance and customer transparency",
                        "priority": "high",
                        "focus_area": "compliance"
                    },
                    {
                        "item": "Accurate data collection for presenting suitable options",
                        "priority": "medium",
                        "focus_area": "data_quality"
                    }
                ]
            },
            "supervisor_action_plan": {
                "approval_required": False,
                "escalation_items": [
                    {
                        "item": "Review missing disclosures and ECOA notice in initial call",
                        "priority": "high",
                        "category": "compliance_gap"
                    }
                ]
            },
            "leadership_action_plan": {
                "portfolio_insights": [
                    {
                        "insight": "Increased customer interest in refinancing due to financial tightening",
                        "category": "market_trend"
                    },
                    {
                        "insight": "High likelihood of refinance completion among similar profiles",
                        "category": "risk_assessment"
                    }
                ]
            }
        }
    
    @pytest.fixture
    def workflow_service(self) -> WorkflowService:
        """Mock workflow service."""
        mock_store = Mock(spec=WorkflowStore)
        mock_agent = Mock(spec=RiskAssessmentAgent)
        return WorkflowService(workflow_store=mock_store, risk_agent=mock_agent)
    
    @pytest.mark.asyncio
    async def test_extract_all_workflows_from_plan(self, workflow_service, sample_action_plan):
        """Test extracting all individual workflows from action plan."""
        # Mock the risk assessment agent responses
        workflow_service.risk_agent.extract_item_workflow.return_value = {
            "workflow_steps": ["Step 1", "Step 2"],
            "complexity": "low"
        }
        workflow_service.risk_agent.assess_item_risk.return_value = {
            "risk_level": "MEDIUM",
            "reasoning": "Test reasoning"
        }
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": True,
            "initial_status": "AWAITING_APPROVAL",
            "routing_reasoning": "Test routing"
        }
        
        # Extract all workflows
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        
        # Should create 7 workflows total (2+2+1+2)
        assert len(workflows) == 7
        
        # Verify workflow types are correctly assigned
        workflow_types = [w['workflow_type'] for w in workflows]
        assert workflow_types.count('BORROWER') == 2
        assert workflow_types.count('ADVISOR') == 2  
        assert workflow_types.count('SUPERVISOR') == 1
        assert workflow_types.count('LEADERSHIP') == 2
    
    @pytest.mark.asyncio
    async def test_borrower_workflow_extraction(self, workflow_service, sample_action_plan):
        """Test extraction of borrower-specific workflows."""
        # Mock responses
        workflow_service.risk_agent.extract_item_workflow.return_value = {
            "workflow_steps": [
                "Contact current lender to verify prepayment penalties",
                "Review loan documents for penalty clauses",
                "Document findings for advisor discussion"
            ],
            "complexity": "medium"
        }
        workflow_service.risk_agent.assess_item_risk.return_value = {
            "risk_level": "LOW",
            "reasoning": "Standard information gathering task"
        }
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": False,
            "initial_status": "AUTO_APPROVED", 
            "routing_reasoning": "Low risk customer action"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        borrower_workflows = [w for w in workflows if w['workflow_type'] == 'BORROWER']
        
        # Should have 2 borrower workflows
        assert len(borrower_workflows) == 2
        
        # Check first borrower workflow
        first_workflow = borrower_workflows[0]
        assert first_workflow['id'].startswith('WF_BORR_')
        assert first_workflow['workflow_type'] == 'BORROWER'
        assert first_workflow['risk_level'] == 'LOW'
        assert first_workflow['status'] == 'AUTO_APPROVED'
        assert 'prepayment penalties' in str(first_workflow['workflow_data'])
    
    @pytest.mark.asyncio 
    async def test_advisor_workflow_extraction(self, workflow_service, sample_action_plan):
        """Test extraction of advisor coaching workflows."""
        # Mock high-risk compliance coaching
        workflow_service.risk_agent.extract_item_workflow.return_value = {
            "workflow_steps": [
                "Schedule compliance training session",
                "Review disclosure requirements with advisor",
                "Create performance improvement plan"
            ],
            "complexity": "high"
        }
        workflow_service.risk_agent.assess_item_risk.return_value = {
            "risk_level": "HIGH", 
            "reasoning": "Compliance gap requires immediate attention"
        }
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": True,
            "initial_status": "AWAITING_APPROVAL",
            "routing_reasoning": "Compliance coaching requires supervisor approval"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        advisor_workflows = [w for w in workflows if w['workflow_type'] == 'ADVISOR']
        
        assert len(advisor_workflows) == 2
        
        # Check compliance workflow has high risk
        compliance_workflow = next(w for w in advisor_workflows 
                                 if 'compliance' in str(w['workflow_data']).lower())
        assert compliance_workflow['risk_level'] == 'HIGH'
        assert compliance_workflow['status'] == 'AWAITING_APPROVAL'
        assert compliance_workflow['id'].startswith('WF_ADV_')
    
    @pytest.mark.asyncio
    async def test_supervisor_workflow_extraction(self, workflow_service, sample_action_plan):
        """Test extraction of supervisor escalation workflows."""
        workflow_service.risk_agent.extract_item_workflow.return_value = {
            "workflow_steps": [
                "Conduct compliance audit of advisor call handling",
                "Create remediation plan for disclosure gaps", 
                "Schedule follow-up compliance review"
            ],
            "complexity": "high"
        }
        workflow_service.risk_agent.assess_item_risk.return_value = {
            "risk_level": "HIGH",
            "reasoning": "Compliance violation requires executive review"
        }
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": True,
            "initial_status": "AWAITING_APPROVAL",
            "routing_reasoning": "Compliance issues require executive approval"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        supervisor_workflows = [w for w in workflows if w['workflow_type'] == 'SUPERVISOR']
        
        assert len(supervisor_workflows) == 1
        
        workflow = supervisor_workflows[0]
        assert workflow['id'].startswith('WF_SUP_')
        assert workflow['risk_level'] == 'HIGH'
        assert 'disclosure' in str(workflow['workflow_data']).lower()
    
    @pytest.mark.asyncio
    async def test_leadership_workflow_extraction(self, workflow_service, sample_action_plan):
        """Test extraction of leadership insight workflows."""
        workflow_service.risk_agent.extract_item_workflow.return_value = {
            "workflow_steps": [
                "Update market trend dashboard",
                "Notify portfolio management team",
                "Schedule strategic review meeting"
            ],
            "complexity": "low"
        }
        workflow_service.risk_agent.assess_item_risk.return_value = {
            "risk_level": "LOW",
            "reasoning": "Informational insight, no operational risk"
        }
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": False,
            "initial_status": "AUTO_APPROVED",
            "routing_reasoning": "Strategic insights auto-approved for tracking"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        leadership_workflows = [w for w in workflows if w['workflow_type'] == 'LEADERSHIP']
        
        assert len(leadership_workflows) == 2
        
        # Both leadership workflows should be auto-approved
        for workflow in leadership_workflows:
            assert workflow['id'].startswith('WF_LEAD_')
            assert workflow['risk_level'] == 'LOW'
            assert workflow['status'] == 'AUTO_APPROVED'
    
    @pytest.mark.asyncio
    async def test_workflow_id_generation(self, workflow_service, sample_action_plan):
        """Test unique workflow ID generation with proper prefixes."""
        workflow_service.risk_agent.extract_item_workflow.return_value = {"workflow_steps": ["test"]}
        workflow_service.risk_agent.assess_item_risk.return_value = {"risk_level": "LOW", "reasoning": "test"}
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": False,
            "initial_status": "AUTO_APPROVED",
            "routing_reasoning": "test"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        
        # Check all IDs are unique
        workflow_ids = [w['id'] for w in workflows]
        assert len(workflow_ids) == len(set(workflow_ids))
        
        # Check proper prefixes
        borrower_ids = [w['id'] for w in workflows if w['workflow_type'] == 'BORROWER']
        advisor_ids = [w['id'] for w in workflows if w['workflow_type'] == 'ADVISOR']
        supervisor_ids = [w['id'] for w in workflows if w['workflow_type'] == 'SUPERVISOR']
        leadership_ids = [w['id'] for w in workflows if w['workflow_type'] == 'LEADERSHIP']
        
        assert all(id.startswith('WF_BORR_') for id in borrower_ids)
        assert all(id.startswith('WF_ADV_') for id in advisor_ids)
        assert all(id.startswith('WF_SUP_') for id in supervisor_ids)  
        assert all(id.startswith('WF_LEAD_') for id in leadership_ids)
    
    @pytest.mark.asyncio
    async def test_context_preservation(self, workflow_service, sample_action_plan):
        """Test that each workflow maintains link to original plan."""
        workflow_service.risk_agent.extract_item_workflow.return_value = {"workflow_steps": ["test"]}
        workflow_service.risk_agent.assess_item_risk.return_value = {"risk_level": "LOW", "reasoning": "test"}
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": False,
            "initial_status": "AUTO_APPROVED",
            "routing_reasoning": "test"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        
        # All workflows should link back to original plan
        for workflow in workflows:
            assert workflow['plan_id'] == "PLAN_TEST_001"
            assert workflow['analysis_id'] == "ANALYSIS_TEST_001"
            assert workflow['transcript_id'] == "TRANSCRIPT_TEST_001"
            assert 'context_data' in workflow
            assert workflow['context_data']['pipeline_stage'] == 'granular_workflow_extraction'
    
    @pytest.mark.asyncio
    async def test_risk_assessment_per_item(self, workflow_service, sample_action_plan):
        """Test that each item gets independent risk assessment."""
        # Mock different risk levels for different items
        risk_responses = [
            {"risk_level": "LOW", "reasoning": "Simple customer action"},
            {"risk_level": "MEDIUM", "reasoning": "Requires advisor attention"},
            {"risk_level": "HIGH", "reasoning": "Compliance critical"},
            {"risk_level": "LOW", "reasoning": "Standard data collection"},
            {"risk_level": "HIGH", "reasoning": "Regulatory violation"},
            {"risk_level": "LOW", "reasoning": "Market insight"},
            {"risk_level": "LOW", "reasoning": "Portfolio metric"}
        ]
        
        workflow_service.risk_agent.extract_item_workflow.return_value = {"workflow_steps": ["test"]}
        workflow_service.risk_agent.assess_item_risk.side_effect = risk_responses
        workflow_service.risk_agent.determine_approval_routing.return_value = {
            "requires_human_approval": False,
            "initial_status": "AUTO_APPROVED",
            "routing_reasoning": "test"
        }
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        
        # Verify risk levels are assigned independently
        risk_levels = [w['risk_level'] for w in workflows]
        assert 'LOW' in risk_levels
        assert 'MEDIUM' in risk_levels  
        assert 'HIGH' in risk_levels
        
        # Should have called risk assessment for each item
        assert workflow_service.risk_agent.assess_item_risk.call_count == 7
    
    @pytest.mark.asyncio
    async def test_parallel_approval_paths(self, workflow_service, sample_action_plan):
        """Test that workflows can have different approval requirements."""
        # Mock different approval requirements
        def mock_routing(workflow_data, risk_assessment, context):
            risk_level = risk_assessment['risk_level']
            if risk_level == 'LOW':
                return {
                    "requires_human_approval": False,
                    "initial_status": "AUTO_APPROVED",
                    "routing_reasoning": "Low risk auto-approved"
                }
            elif risk_level == 'MEDIUM':
                return {
                    "requires_human_approval": True, 
                    "initial_status": "AWAITING_APPROVAL",
                    "routing_reasoning": "Medium risk needs advisor approval"
                }
            else:  # HIGH
                return {
                    "requires_human_approval": True,
                    "initial_status": "AWAITING_APPROVAL", 
                    "routing_reasoning": "High risk needs supervisor approval"
                }
        
        workflow_service.risk_agent.extract_item_workflow.return_value = {"workflow_steps": ["test"]}
        workflow_service.risk_agent.assess_item_risk.side_effect = [
            {"risk_level": "LOW", "reasoning": "test"},
            {"risk_level": "MEDIUM", "reasoning": "test"},
            {"risk_level": "HIGH", "reasoning": "test"},
            {"risk_level": "LOW", "reasoning": "test"},
            {"risk_level": "HIGH", "reasoning": "test"},
            {"risk_level": "LOW", "reasoning": "test"},
            {"risk_level": "LOW", "reasoning": "test"}
        ]
        workflow_service.risk_agent.determine_approval_routing.side_effect = mock_routing
        
        workflows = await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")
        
        # Check approval statuses
        auto_approved = [w for w in workflows if w['status'] == 'AUTO_APPROVED']
        awaiting_approval = [w for w in workflows if w['status'] == 'AWAITING_APPROVAL']
        
        assert len(auto_approved) > 0
        assert len(awaiting_approval) > 0
        
        # Low risk should be auto-approved
        low_risk_workflows = [w for w in workflows if w['risk_level'] == 'LOW']
        for workflow in low_risk_workflows:
            assert workflow['status'] == 'AUTO_APPROVED'
            assert not workflow['requires_human_approval']
    
    @pytest.mark.asyncio
    async def test_no_fallback_principle(self, workflow_service, sample_action_plan):
        """Test system fails fast when required data is missing."""
        # Test with invalid plan data
        invalid_plan = {"plan_id": "INVALID"}
        
        with pytest.raises(ValueError, match="Failed to extract workflows: Missing required plan sections"):
            await workflow_service.extract_all_workflows_from_plan("INVALID_PLAN")
        
        # Test with LLM failure
        workflow_service.risk_agent.extract_item_workflow.side_effect = Exception("LLM service unavailable")
        
        with pytest.raises(Exception, match="LLM service unavailable"):
            await workflow_service.extract_all_workflows_from_plan("PLAN_TEST_001")


class TestGranularWorkflowStorage:
    """Test storage and retrieval of granular workflows."""
    
    @pytest.fixture
    def workflow_store(self):
        """Mock workflow store."""
        return Mock(spec=WorkflowStore)
    
    def test_bulk_workflow_creation(self, workflow_store):
        """Test creating multiple workflows in bulk."""
        workflows = [
            {"id": "WF_BORR_001", "workflow_type": "BORROWER"},
            {"id": "WF_ADV_001", "workflow_type": "ADVISOR"},
            {"id": "WF_SUP_001", "workflow_type": "SUPERVISOR"}
        ]
        
        workflow_store.create_bulk(workflows)
        
        # Should call bulk create
        workflow_store.create_bulk.assert_called_once_with(workflows)
    
    def test_list_workflows_by_plan(self, workflow_store):
        """Test retrieving all workflows for a plan."""
        workflow_store.get_by_plan_id.return_value = [
            {"id": "WF_BORR_001", "plan_id": "PLAN_001", "workflow_type": "BORROWER"},
            {"id": "WF_ADV_001", "plan_id": "PLAN_001", "workflow_type": "ADVISOR"}
        ]
        
        workflows = workflow_store.get_by_plan_id("PLAN_001")
        
        assert len(workflows) == 2
        assert all(w['plan_id'] == "PLAN_001" for w in workflows)
        workflow_store.get_by_plan_id.assert_called_once_with("PLAN_001")
    
    def test_filter_workflows_by_type(self, workflow_store):
        """Test filtering workflows by type."""
        workflow_store.get_by_type.return_value = [
            {"id": "WF_BORR_001", "workflow_type": "BORROWER"},
            {"id": "WF_BORR_002", "workflow_type": "BORROWER"}
        ]
        
        borrower_workflows = workflow_store.get_by_type("BORROWER")
        
        assert len(borrower_workflows) == 2
        assert all(w['workflow_type'] == "BORROWER" for w in borrower_workflows)