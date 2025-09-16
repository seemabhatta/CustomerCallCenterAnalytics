"""
Test suite for simple orchestration pipeline (no external dependencies)
Following TDD principles - tests written first before implementation
NO FALLBACK LOGIC - test that pipeline fails fast on errors
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch

from src.services.orchestration.simple_orchestrator import SimpleOrchestrator, TaskStatus
from src.services.orchestration.simple_pipeline import SimplePipeline, run_simple_pipeline
from src.services.orchestration.models.pipeline_models import PipelineStage, WorkflowType


class TestSimpleOrchestrator:
    """Test simple orchestrator functionality"""
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly"""
        orchestrator = SimpleOrchestrator()
        
        assert orchestrator.task_results == []
        assert orchestrator.paused == False
        assert orchestrator.current_stage == PipelineStage.TRANSCRIPT
    
    @pytest.mark.asyncio
    async def test_execute_single_task_success(self):
        """Test successful single task execution"""
        orchestrator = SimpleOrchestrator()
        
        async def dummy_task(value: int) -> int:
            return value * 2
        
        result = await orchestrator.execute_task("test-task", dummy_task, 5)
        
        assert result.task_name == "test-task"
        assert result.status == TaskStatus.COMPLETED
        assert result.result == 10
        assert result.error is None
        assert result.start_time is not None
        assert result.end_time is not None
        
        # Check task is recorded
        assert len(orchestrator.task_results) == 1
        assert orchestrator.task_results[0] == result
    
    @pytest.mark.asyncio
    async def test_execute_single_task_failure(self):
        """Test single task execution failure - NO FALLBACK"""
        orchestrator = SimpleOrchestrator()
        
        async def failing_task() -> None:
            raise ValueError("Task failed intentionally")
        
        # Should fail fast - NO FALLBACK
        with pytest.raises(Exception) as exc_info:
            await orchestrator.execute_task("failing-task", failing_task)
        
        assert "Task 'failing-task' failed" in str(exc_info.value)
        
        # Task failure should be recorded
        assert len(orchestrator.task_results) == 1
        task_result = orchestrator.task_results[0]
        assert task_result.status == TaskStatus.FAILED
        assert "Task failed intentionally" in task_result.error
    
    @pytest.mark.asyncio
    async def test_execute_parallel_tasks_success(self):
        """Test parallel task execution success"""
        orchestrator = SimpleOrchestrator()
        
        async def task1() -> str:
            return "result1"
        
        async def task2(value: int) -> int:
            return value * 3
        
        async def task3() -> str:
            return "result3"
        
        tasks = [
            ("task1", task1, (), {}),
            ("task2", task2, (4,), {}),
            ("task3", task3, (), {})
        ]
        
        results = await orchestrator.execute_parallel_tasks(tasks)
        
        assert len(results) == 3
        assert all(r.status == TaskStatus.COMPLETED for r in results)
        assert results[0].result == "result1"
        assert results[1].result == 12
        assert results[2].result == "result3"
    
    @pytest.mark.asyncio
    async def test_execute_parallel_tasks_one_failure(self):
        """Test parallel execution fails fast if one task fails"""
        orchestrator = SimpleOrchestrator()
        
        async def success_task() -> str:
            return "success"
        
        async def failing_task() -> None:
            raise RuntimeError("Parallel task failed")
        
        tasks = [
            ("success-task", success_task, (), {}),
            ("failing-task", failing_task, (), {})
        ]
        
        # Should fail fast - NO FALLBACK
        with pytest.raises(Exception) as exc_info:
            await orchestrator.execute_parallel_tasks(tasks)
        
        assert "failing-task" in str(exc_info.value)
    
    def test_pause_and_resume(self):
        """Test pause and resume functionality"""
        orchestrator = SimpleOrchestrator()
        
        # Initially not paused
        assert orchestrator.paused == False
        
        # Pause execution
        orchestrator.pause_execution()
        assert orchestrator.paused == True
        
        # Resume execution
        orchestrator.resume_execution()
        assert orchestrator.paused == False
    
    def test_execution_summary(self):
        """Test execution summary generation"""
        orchestrator = SimpleOrchestrator()
        
        # Empty summary initially
        summary = orchestrator.get_execution_summary()
        assert summary["total_tasks"] == 0
        assert summary["completed"] == 0
        assert summary["failed"] == 0
        assert summary["success_rate"] == 0


class TestSimplePipeline:
    """Test simple pipeline implementation"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all service dependencies"""
        with patch('src.services.orchestration.simple_pipeline.AnalysisService') as mock_analysis, \
             patch('src.services.orchestration.simple_pipeline.PlanService') as mock_plan, \
             patch('src.services.orchestration.simple_pipeline.WorkflowService') as mock_workflow, \
             patch('src.services.orchestration.simple_pipeline.WorkflowExecutionEngine') as mock_execution:
            
            yield {
                'analysis': mock_analysis,
                'plan': mock_plan, 
                'workflow': mock_workflow,
                'execution': mock_execution
            }
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing"""
        return {
            "transcript_id": "TEST_TRANSCRIPT_001",
            "analysis": {
                "id": "ANALYSIS_001",
                "transcript_id": "TEST_TRANSCRIPT_001",
                "status": "completed"
            },
            "plan": {
                "id": "PLAN_001", 
                "analysis_id": "ANALYSIS_001",
                "status": "completed"
            },
            "workflows": [
                {
                    "id": f"WORKFLOW_{wf_type.value}",
                    "plan_id": "PLAN_001",
                    "workflow_type": wf_type.value,
                    "risk_level": "MEDIUM",
                    "status": "AWAITING_APPROVAL",
                    "workflow_data": {"action_item": f"Test action for {wf_type.value}"}
                }
                for wf_type in WorkflowType
            ],
            "execution_results": [
                {"status": "executed", "workflow_id": f"WORKFLOW_{wf_type.value}"}
                for wf_type in WorkflowType
            ]
        }
    
    @pytest.mark.asyncio
    async def test_complete_pipeline_success(self, mock_services, sample_data):
        """Test complete pipeline execution success"""
        # Setup mocks
        mock_services['analysis'].return_value.create_analysis = AsyncMock(
            return_value=sample_data["analysis"]
        )
        mock_services['plan'].return_value.create_plan = AsyncMock(
            return_value=sample_data["plan"]
        )
        mock_services['workflow'].return_value.extract_all_workflows = AsyncMock(
            return_value=sample_data["workflows"]
        )
        mock_services['execution'].return_value.execute_workflow = AsyncMock(
            return_value={"status": "executed", "workflow_id": "test"}
        )
        
        # Run pipeline
        pipeline = SimplePipeline("test-api-key", "test-db-path")
        result = await pipeline.run_complete_pipeline(
            sample_data["transcript_id"], 
            auto_approve=True
        )
        
        # Verify result
        assert result["transcript_id"] == sample_data["transcript_id"]
        assert result["analysis_id"] == sample_data["analysis"]["id"]
        assert result["plan_id"] == sample_data["plan"]["id"]
        assert result["workflow_count"] == 4
        assert result["executed_count"] == 4
        assert result["success"] == True
        assert result["stage"] == PipelineStage.COMPLETE.value
    
    @pytest.mark.asyncio
    async def test_pipeline_analysis_failure(self, mock_services, sample_data):
        """Test pipeline fails fast on analysis failure - NO FALLBACK"""
        # Mock analysis service to fail
        mock_services['analysis'].return_value.create_analysis = AsyncMock(
            side_effect=Exception("Analysis service unavailable")
        )
        
        # Run pipeline
        pipeline = SimplePipeline("test-api-key", "test-db-path")
        
        # Should fail fast - NO FALLBACK
        with pytest.raises(Exception) as exc_info:
            await pipeline.run_complete_pipeline(sample_data["transcript_id"])
        
        assert "Analysis service unavailable" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_pipeline_workflow_extraction_failure(self, mock_services, sample_data):
        """Test pipeline fails fast on workflow extraction failure"""
        # Setup successful analysis and plan
        mock_services['analysis'].return_value.create_analysis = AsyncMock(
            return_value=sample_data["analysis"]
        )
        mock_services['plan'].return_value.create_plan = AsyncMock(
            return_value=sample_data["plan"]
        )
        
        # Mock workflow service to fail
        mock_services['workflow'].return_value.extract_all_workflows = AsyncMock(
            side_effect=Exception("Workflow extraction failed")
        )
        
        pipeline = SimplePipeline("test-api-key", "test-db-path")
        
        # Should fail fast - NO FALLBACK
        with pytest.raises(Exception) as exc_info:
            await pipeline.run_complete_pipeline(sample_data["transcript_id"])
        
        assert "Workflow extraction failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_pipeline_low_risk_auto_approval(self, mock_services, sample_data):
        """Test LOW risk workflows are auto-approved"""
        # Create low risk workflows
        low_risk_workflows = [
            {
                "id": "WORKFLOW_LOW_RISK",
                "plan_id": "PLAN_001",
                "workflow_type": "BORROWER",
                "risk_level": "LOW",
                "status": "AWAITING_APPROVAL",
                "workflow_data": {"action_item": "Low risk action"}
            }
        ]
        
        # Setup mocks with low risk workflow
        mock_services['analysis'].return_value.create_analysis = AsyncMock(
            return_value=sample_data["analysis"]
        )
        mock_services['plan'].return_value.create_plan = AsyncMock(
            return_value=sample_data["plan"]
        )
        mock_services['workflow'].return_value.extract_all_workflows = AsyncMock(
            return_value=low_risk_workflows * 4  # Need 4 workflows
        )
        mock_services['execution'].return_value.execute_workflow = AsyncMock(
            return_value={"status": "executed", "workflow_id": "WORKFLOW_LOW_RISK"}
        )
        
        pipeline = SimplePipeline("test-api-key", "test-db-path")
        result = await pipeline.run_complete_pipeline(
            sample_data["transcript_id"], 
            auto_approve=False  # Don't force approve
        )
        
        # Low risk should be auto-approved and executed
        assert result["executed_count"] == 4


class TestPipelineConvenienceFunction:
    """Test convenience function for running pipeline"""
    
    @pytest.mark.asyncio
    async def test_run_simple_pipeline_missing_api_key(self):
        """Test pipeline fails fast without API key"""
        # Clear environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                await run_simple_pipeline("TEST_TRANSCRIPT")
            
            assert "OpenAI API key required" in str(exc_info.value)