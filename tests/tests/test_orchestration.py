"""
Test suite for orchestration pipeline
Following TDD principles - tests written first before implementation
NO FALLBACK LOGIC - test that pipeline fails fast on errors
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from prefect.testing.utilities import prefect_test_harness

from src.orchestration.models.pipeline_models import (
    PipelineInput, PipelineResult, PipelineStage, WorkflowType
)


class TestOrchestrationPipeline:
    """Test orchestration pipeline following TDD principles"""
    
    @pytest.fixture
    def sample_transcript_id(self):
        """Sample transcript ID for testing"""
        return "TEST_TRANSCRIPT_001"
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis result"""
        return {
            "id": "ANALYSIS_TEST_001",
            "transcript_id": "TEST_TRANSCRIPT_001",
            "status": "completed"
        }
    
    @pytest.fixture
    def sample_plan(self):
        """Sample action plan result"""
        return {
            "id": "PLAN_TEST_001",
            "analysis_id": "ANALYSIS_TEST_001",
            "status": "completed"
        }
    
    @pytest.fixture
    def sample_workflows(self):
        """Sample workflows (4 types)"""
        return [
            {
                "id": f"WORKFLOW_TEST_{wf_type.value}",
                "plan_id": "PLAN_TEST_001",
                "workflow_type": wf_type.value,
                "risk_level": "MEDIUM",
                "status": "AWAITING_APPROVAL",
                "workflow_data": {"action_item": f"Test action for {wf_type.value}"}
            }
            for wf_type in WorkflowType
        ]
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_flow(self, sample_transcript_id, sample_analysis, 
                                        sample_plan, sample_workflows):
        """Test complete happy path: transcript → analysis → plan → workflows → execution"""
        with prefect_test_harness():
            # Mock all service calls
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis_service, \
                 patch('src.services.plan_service.PlanService') as mock_plan_service, \
                 patch('src.services.workflow_service.WorkflowService') as mock_workflow_service, \
                 patch('src.services.workflow_execution_engine.WorkflowExecutionEngine') as mock_execution_engine:
                
                # Setup mocks
                mock_analysis_service.return_value.create_analysis = AsyncMock(return_value=sample_analysis)
                mock_plan_service.return_value.create_plan = AsyncMock(return_value=sample_plan)
                mock_workflow_service.return_value.extract_all_workflows = AsyncMock(return_value=sample_workflows)
                mock_execution_engine.return_value.execute_workflow = AsyncMock(return_value={"status": "executed"})
                
                # Import and run pipeline
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                result = await call_center_pipeline(sample_transcript_id, auto_approve=True)
                
                # Assertions
                assert result is not None
                assert result["transcript_id"] == sample_transcript_id
                assert result["analysis_id"] == sample_analysis["id"]
                assert result["plan_id"] == sample_plan["id"]
                assert result["workflow_count"] == 4  # 4 workflow types
                assert result["executed_count"] == 4  # All executed (auto_approve=True)
                assert len(result["execution_results"]) == 4
    
    @pytest.mark.asyncio
    async def test_pipeline_failure_no_fallback(self, sample_transcript_id):
        """Test NO FALLBACK - pipeline fails fast on analysis error"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis_service:
                # Mock analysis service to fail
                mock_analysis_service.return_value.create_analysis = AsyncMock(
                    side_effect=Exception("Analysis generation failed")
                )
                
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                # Should fail fast - NO FALLBACK
                with pytest.raises(Exception) as exc_info:
                    await call_center_pipeline(sample_transcript_id)
                
                assert "Analysis generation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_parallel_workflow_processing(self, sample_transcript_id, sample_analysis,
                                              sample_plan, sample_workflows):
        """Test 1:n workflow processing in parallel"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis_service, \
                 patch('src.services.plan_service.PlanService') as mock_plan_service, \
                 patch('src.services.workflow_service.WorkflowService') as mock_workflow_service, \
                 patch('src.services.workflow_execution_engine.WorkflowExecutionEngine') as mock_execution_engine:
                
                # Setup mocks
                mock_analysis_service.return_value.create_analysis = AsyncMock(return_value=sample_analysis)
                mock_plan_service.return_value.create_plan = AsyncMock(return_value=sample_plan)
                mock_workflow_service.return_value.extract_all_workflows = AsyncMock(return_value=sample_workflows)
                
                # Mock execution to track parallel calls
                execution_calls = []
                async def mock_execute(workflow_id, executor):
                    execution_calls.append(workflow_id)
                    return {"status": "executed", "workflow_id": workflow_id}
                
                mock_execution_engine.return_value.execute_workflow = AsyncMock(side_effect=mock_execute)
                
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                result = await call_center_pipeline(sample_transcript_id, auto_approve=True)
                
                # Verify all 4 workflows were executed
                assert len(execution_calls) == 4
                assert all(f"WORKFLOW_TEST_{wf_type.value}" in execution_calls for wf_type in WorkflowType)
                assert result["executed_count"] == 4
    
    @pytest.mark.asyncio
    async def test_low_risk_auto_approval(self, sample_transcript_id, sample_analysis,
                                        sample_plan):
        """Test that LOW risk workflows are auto-approved"""
        # Create low risk workflows
        low_risk_workflows = [
            {
                "id": "WORKFLOW_LOW_RISK",
                "risk_level": "LOW",
                "status": "AWAITING_APPROVAL",
                "workflow_data": {"action_item": "Low risk action"},
                "workflow_type": "BORROWER"
            }
        ]
        
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis_service, \
                 patch('src.services.plan_service.PlanService') as mock_plan_service, \
                 patch('src.services.workflow_service.WorkflowService') as mock_workflow_service, \
                 patch('src.services.workflow_execution_engine.WorkflowExecutionEngine') as mock_execution_engine:
                
                # Setup mocks
                mock_analysis_service.return_value.create_analysis = AsyncMock(return_value=sample_analysis)
                mock_plan_service.return_value.create_plan = AsyncMock(return_value=sample_plan)
                mock_workflow_service.return_value.extract_all_workflows = AsyncMock(return_value=low_risk_workflows)
                mock_execution_engine.return_value.execute_workflow = AsyncMock(return_value={"status": "executed"})
                
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                result = await call_center_pipeline(sample_transcript_id, auto_approve=False)
                
                # Low risk should be auto-approved and executed
                assert result["executed_count"] == 1


class TestOrchestrationTasks:
    """Test individual orchestration tasks"""
    
    @pytest.mark.asyncio
    async def test_generate_analysis_task_success(self):
        """Test analysis generation task success"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_service:
                mock_service.return_value.create_analysis = AsyncMock(return_value={"id": "ANALYSIS_001"})
                
                from src.orchestration.tasks.analysis_tasks import generate_analysis_task
                
                result = await generate_analysis_task("TEST_TRANSCRIPT")
                
                assert result["id"] == "ANALYSIS_001"
                mock_service.return_value.create_analysis.assert_called_once_with("TEST_TRANSCRIPT")
    
    @pytest.mark.asyncio
    async def test_generate_analysis_task_fail_fast(self):
        """Test analysis task fails fast - NO FALLBACK"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_service:
                mock_service.return_value.create_analysis = AsyncMock(side_effect=Exception("Service error"))
                
                from src.orchestration.tasks.analysis_tasks import generate_analysis_task
                
                with pytest.raises(Exception) as exc_info:
                    await generate_analysis_task("TEST_TRANSCRIPT")
                
                assert "Analysis generation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_create_plan_task_success(self):
        """Test plan creation task success"""
        with prefect_test_harness():
            with patch('src.services.plan_service.PlanService') as mock_service:
                mock_service.return_value.create_plan = AsyncMock(return_value={"id": "PLAN_001"})
                
                from src.orchestration.tasks.plan_tasks import create_plan_task
                
                result = await create_plan_task("ANALYSIS_001")
                
                assert result["id"] == "PLAN_001"
    
    @pytest.mark.asyncio
    async def test_extract_workflows_task_success(self):
        """Test workflow extraction task success"""
        workflows = [{"id": "WF_1"}, {"id": "WF_2"}]
        
        with prefect_test_harness():
            with patch('src.services.workflow_service.WorkflowService') as mock_service:
                mock_service.return_value.extract_all_workflows = AsyncMock(return_value=workflows)
                
                from src.orchestration.tasks.workflow_tasks import extract_workflows_task
                
                result = await extract_workflows_task("PLAN_001")
                
                assert len(result) == 2
                assert result[0]["id"] == "WF_1"
    
    @pytest.mark.asyncio
    async def test_execute_workflow_task_success(self):
        """Test workflow execution task success"""
        execution_result = {"status": "executed", "execution_id": "EXEC_001"}
        
        with prefect_test_harness():
            with patch('src.services.workflow_execution_engine.WorkflowExecutionEngine') as mock_engine:
                mock_engine.return_value.execute_workflow = AsyncMock(return_value=execution_result)
                
                from src.orchestration.tasks.execution_tasks import execute_workflow_task
                
                result = await execute_workflow_task("WORKFLOW_001")
                
                assert result["status"] == "executed"
                assert result["execution_id"] == "EXEC_001"


class TestApprovalFlow:
    """Test human approval workflow"""
    
    @pytest.mark.asyncio
    async def test_approval_flow_high_risk_workflow(self):
        """Test approval flow for high risk workflow"""
        # This test will be expanded when approval flow is implemented
        pytest.skip("Approval flow implementation pending")
    
    @pytest.mark.asyncio
    async def test_approval_timeout(self):
        """Test approval timeout handling"""
        # This test will verify timeout behavior
        pytest.skip("Approval flow implementation pending")


class TestErrorHandling:
    """Test error handling and NO FALLBACK principle"""
    
    @pytest.mark.asyncio
    async def test_no_fallback_on_plan_failure(self):
        """Test pipeline fails fast on plan creation failure"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis, \
                 patch('src.services.plan_service.PlanService') as mock_plan:
                
                mock_analysis.return_value.create_analysis = AsyncMock(return_value={"id": "ANALYSIS_001"})
                mock_plan.return_value.create_plan = AsyncMock(side_effect=Exception("Plan creation failed"))
                
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                with pytest.raises(Exception) as exc_info:
                    await call_center_pipeline("TEST_TRANSCRIPT")
                
                assert "Plan creation failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_no_fallback_on_workflow_extraction_failure(self):
        """Test pipeline fails fast on workflow extraction failure"""
        with prefect_test_harness():
            with patch('src.services.analysis_service.AnalysisService') as mock_analysis, \
                 patch('src.services.plan_service.PlanService') as mock_plan, \
                 patch('src.services.workflow_service.WorkflowService') as mock_workflow:
                
                mock_analysis.return_value.create_analysis = AsyncMock(return_value={"id": "ANALYSIS_001"})
                mock_plan.return_value.create_plan = AsyncMock(return_value={"id": "PLAN_001"})
                mock_workflow.return_value.extract_all_workflows = AsyncMock(
                    side_effect=Exception("Workflow extraction failed")
                )
                
                from src.orchestration.flows.pipeline_flow import call_center_pipeline
                
                with pytest.raises(Exception) as exc_info:
                    await call_center_pipeline("TEST_TRANSCRIPT")
                
                assert "Workflow extraction failed" in str(exc_info.value)