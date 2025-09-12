"""
Simple orchestrator implementation without external dependencies
Provides the same functionality as Prefect but with native Python
NO FALLBACK LOGIC - fails fast on any errors
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.orchestration.models.pipeline_models import PipelineResult, PipelineStage


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class TaskResult:
    """Result from task execution"""
    task_name: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class SimpleOrchestrator:
    """Simple orchestrator for pipeline execution"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.task_results: List[TaskResult] = []
        self.paused = False
        self.current_stage = PipelineStage.TRANSCRIPT
    
    async def execute_task(self, task_name: str, task_func: Callable, *args, **kwargs) -> TaskResult:
        """Execute a single task with error handling and logging"""
        task_result = TaskResult(
            task_name=task_name,
            status=TaskStatus.PENDING,
            start_time=datetime.now()
        )
        
        try:
            self.logger.info(f"🚀 Starting task: {task_name}")
            print(f"🔄 Executing task: {task_name}")
            task_result.status = TaskStatus.RUNNING
            
            # Execute the task
            result = await task_func(*args, **kwargs)
            print(f"✅ Task completed: {task_name}")
            
            task_result.result = result
            task_result.status = TaskStatus.COMPLETED
            task_result.end_time = datetime.now()
            
            self.logger.info(f"✅ Completed task: {task_name}")
            
        except Exception as e:
            task_result.error = str(e)
            task_result.status = TaskStatus.FAILED
            task_result.end_time = datetime.now()
            
            self.logger.error(f"💥 Task failed: {task_name} - {e}")
            
            # NO FALLBACK - fail immediately
            raise Exception(f"Task '{task_name}' failed: {e}")
        
        finally:
            self.task_results.append(task_result)
        
        return task_result
    
    async def execute_parallel_tasks(self, tasks: List[tuple]) -> List[TaskResult]:
        """Execute multiple tasks in parallel"""
        self.logger.info(f"⚡ Starting {len(tasks)} parallel tasks")
        
        # Create coroutines for all tasks
        task_coroutines = [
            self.execute_task(name, func, *args, **kwargs)
            for name, func, args, kwargs in tasks
        ]
        
        # Execute all tasks in parallel
        try:
            results = await asyncio.gather(*task_coroutines)
            self.logger.info(f"✅ Completed all {len(tasks)} parallel tasks")
            return results
        except Exception as e:
            self.logger.error(f"💥 Parallel execution failed: {e}")
            raise
    
    def pause_execution(self):
        """Pause orchestration execution"""
        self.paused = True
        self.logger.info("⏸️ Orchestration paused")
    
    def resume_execution(self):
        """Resume orchestration execution"""
        self.paused = False
        self.logger.info("▶️ Orchestration resumed")
    
    def check_if_paused(self):
        """Check if execution should be paused"""
        if self.paused:
            self.logger.info("⏸️ Execution is paused, waiting for resume...")
            # In a real implementation, this would wait for external signal
            # For now, we'll just raise an exception to stop execution
            raise Exception("Execution paused - manual resume required")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all task executions"""
        total_tasks = len(self.task_results)
        completed = sum(1 for t in self.task_results if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.task_results if t.status == TaskStatus.FAILED)
        
        return {
            "total_tasks": total_tasks,
            "completed": completed,
            "failed": failed,
            "success_rate": (completed / total_tasks) if total_tasks > 0 else 0,
            "current_stage": self.current_stage.value,
            "tasks": [
                {
                    "name": t.task_name,
                    "status": t.status.value,
                    "error": t.error,
                    "duration_ms": (
                        (t.end_time - t.start_time).total_seconds() * 1000
                        if t.start_time and t.end_time else None
                    )
                }
                for t in self.task_results
            ]
        }