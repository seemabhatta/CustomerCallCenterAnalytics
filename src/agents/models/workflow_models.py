from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


class WorkflowStep(BaseModel):
    step_number: int = Field(description="Sequential step number")
    action: str = Field(description="Clear, actionable step description")
    details: str = Field(description="Detailed instructions for executing this step")
    tool_needed: str = Field(description="System or tool required for this step")
    validation_criteria: str = Field(description="How to verify this step was completed correctly")


class WorkflowSteps(BaseModel):
    steps: List[WorkflowStep] = Field(description="Ordered list of executable steps")
    total_steps: int = Field(description="Total number of steps")
    estimated_duration_minutes: int = Field(description="Estimated time to complete all steps")


class WorkflowExtraction(BaseModel):
    workflow_type: str = Field(description="Type of workflow")
    workflow_steps: List[Dict[str, Any]] = Field(description="List of extracted workflow steps")
    dependencies: List[str] = Field(description="List of dependencies between steps")
    estimated_duration: str = Field(description="Estimated duration for the workflow")


class RoutingDecision(BaseModel):
    requires_human_approval: bool = Field(description="Whether human approval is required")
    initial_status: Literal["PENDING_ASSESSMENT", "AWAITING_APPROVAL", "AUTO_APPROVED"] = Field(description="Initial status of the item")
    routing_reasoning: str = Field(description="Reasoning for the routing decision")
    approval_level: Optional[str] = Field(description="Required approval level if needed")


class ValidationResult(BaseModel):
    is_valid: bool = Field(description="Whether the validation passed")
    validation_status: str = Field(description="Status of the validation")
    validation_reasoning: str = Field(description="Reasoning for the validation result")
    issues_found: List[str] = Field(description="List of issues found during validation")
    recommended_actions: List[str] = Field(description="Recommended actions to address issues")


class StatusDecision(BaseModel):
    new_status: str = Field(description="New status to be assigned")
    status_reasoning: str = Field(description="Reasoning for the status change")
    next_actions: List[str] = Field(description="Next actions required")
    requires_notification: bool = Field(description="Whether notification is required")


class ExecutionResult(BaseModel):
    execution_status: str = Field(description="Status of the execution")
    success: bool = Field(description="Whether execution was successful")
    results_summary: str = Field(description="Summary of execution results")
    completed_steps: List[str] = Field(description="List of completed steps")
    failed_steps: List[str] = Field(description="List of failed steps")
    next_steps: List[str] = Field(description="Next steps to be taken")