"""
Execution Models - Request/Response models for step-by-step workflow execution.
Clean separation of API models from business logic.
NO FALLBACK LOGIC - strict validation with immediate failure.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class StepExecutionRequest(BaseModel):
    """Request model for executing a single workflow step.

    Following core principles:
    - NO FALLBACK - required fields must be provided
    - Fail fast on invalid data
    """
    executed_by: str = Field(..., min_length=1, description="Who is executing the step")
    confirmation: bool = Field(default=True, description="Confirmation that step should be executed")

    class Config:
        # Strict validation - NO FALLBACK for invalid data
        extra = "forbid"  # Reject extra fields
        validate_assignment = True  # Validate on assignment


class StepExecutionResponse(BaseModel):
    """Response model for step execution result.

    Contains all essential information about the executed step.
    """
    workflow_id: str = Field(..., description="ID of the executed workflow")
    step_number: int = Field(..., gt=0, description="Step number that was executed")
    status: str = Field(..., description="Execution status: success, failed, skipped")
    executor_type: str = Field(..., description="Type of executor used")
    execution_id: str = Field(..., description="Unique execution record ID")
    result: Dict[str, Any] = Field(..., description="Execution result data")
    executed_at: str = Field(..., description="ISO timestamp when step was executed")
    executed_by: str = Field(..., description="Who executed the step")
    duration_ms: int = Field(..., ge=0, description="Execution duration in milliseconds")

    class Config:
        extra = "forbid"
        validate_assignment = True


class StepStatusResponse(BaseModel):
    """Response model for step execution status query.

    Indicates whether a specific step has been executed and provides details.
    """
    workflow_id: str = Field(..., description="ID of the workflow")
    step_number: int = Field(..., gt=0, description="Step number being queried")
    executed: bool = Field(..., description="Whether the step has been executed")
    execution_details: Optional[StepExecutionResponse] = Field(
        default=None,
        description="Execution details if step was executed"
    )

    class Config:
        extra = "forbid"
        validate_assignment = True


class WorkflowStepsResponse(BaseModel):
    """Response model for workflow steps list.

    Returns all steps in a workflow for step-by-step execution.
    """
    workflow_id: str = Field(..., description="ID of the workflow")
    total_steps: int = Field(..., ge=0, description="Total number of steps")
    steps: list[Dict[str, Any]] = Field(..., description="List of workflow steps")

    class Config:
        extra = "forbid"
        validate_assignment = True


# Error response models for consistent error handling
class ExecutionErrorResponse(BaseModel):
    """Standard error response for execution failures.

    Following NO FALLBACK principle - clear error messages without fallback behavior.
    """
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    workflow_id: Optional[str] = Field(default=None, description="Workflow ID if applicable")
    step_number: Optional[int] = Field(default=None, description="Step number if applicable")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error context")

    class Config:
        extra = "forbid"
        validate_assignment = True