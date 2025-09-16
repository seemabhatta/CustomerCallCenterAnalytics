from typing import Dict, Any, Optional, List, Literal, Union
import os
from pydantic import BaseModel, Field
from openai import OpenAI, AsyncOpenAI
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Removed old helper functions - no longer needed with chat completions API


class RiskAssessment(BaseModel):
    """Structured output for risk assessment results."""
    risk_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Risk level classification")
    reasoning: str = Field(description="Detailed reasoning for the risk assessment")
    factors: List[str] = Field(description="Key risk factors identified")
    score: float = Field(ge=0.0, le=1.0, description="Risk score between 0 and 1")


class ApprovalRouting(BaseModel):
    """Structured output for approval routing decisions."""
    approval_level: Literal["ADVISOR", "SUPERVISOR", "LEADERSHIP"] = Field(description="Required approval level")
    reasoning: str = Field(description="Reasoning for the approval level decision")
    urgency: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Urgency level")
    estimated_time_days: int = Field(ge=1, description="Estimated approval time in days")


class ActionItem(BaseModel):
    """Structured output for individual action items."""
    title: str = Field(description="Clear, actionable title")
    description: str = Field(description="Detailed description of the action")
    pillar: Literal["BORROWER", "ADVISOR", "SUPERVISOR", "LEADERSHIP"] = Field(description="Responsible pillar")
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Priority level")
    estimated_hours: float = Field(ge=0.1, description="Estimated effort in hours")


class ActionItemList(BaseModel):
    """Collection of action items for a workflow type."""
    workflow_type: str = Field(description="Type of workflow")
    action_items: List[ActionItem] = Field(description="List of extracted action items")
    total_items: int = Field(description="Total number of action items")


class WorkflowStep(BaseModel):
    """Structured output for individual workflow step."""
    step_number: int = Field(description="Sequential step number")
    action: str = Field(description="Clear, actionable step description")
    details: str = Field(description="Detailed instructions for executing this step")
    tool_needed: str = Field(description="System or tool required for this step")
    validation_criteria: str = Field(description="How to verify this step was completed correctly")


class WorkflowSteps(BaseModel):
    """Collection of workflow steps for an action item."""
    steps: List[WorkflowStep] = Field(description="Ordered list of executable steps")
    total_steps: int = Field(description="Total number of steps")
    estimated_duration_minutes: int = Field(description="Estimated time to complete all steps")


class WorkflowExtraction(BaseModel):
    """Structured output for workflow extraction from plan data."""
    workflow_type: str = Field(description="Type of workflow")
    workflow_steps: List[Dict[str, Any]] = Field(description="List of extracted workflow steps")
    dependencies: List[str] = Field(description="List of dependencies between steps")
    estimated_duration: str = Field(description="Estimated duration for the workflow")


class RoutingDecision(BaseModel):
    """Structured output for approval routing decisions."""
    requires_human_approval: bool = Field(description="Whether human approval is required")
    initial_status: Literal["PENDING_ASSESSMENT", "AWAITING_APPROVAL", "AUTO_APPROVED"] = Field(description="Initial status of the item")
    routing_reasoning: str = Field(description="Reasoning for the routing decision")
    approval_level: Optional[str] = Field(description="Required approval level if needed")


class ValidationResult(BaseModel):
    """Structured output for validation results."""
    is_valid: bool = Field(description="Whether the validation passed")
    validation_status: str = Field(description="Status of the validation")
    validation_reasoning: str = Field(description="Reasoning for the validation result")
    issues_found: List[str] = Field(description="List of issues found during validation")
    recommended_actions: List[str] = Field(description="Recommended actions to address issues")


class StatusDecision(BaseModel):
    """Structured output for status decisions."""
    new_status: str = Field(description="New status to be assigned")
    status_reasoning: str = Field(description="Reasoning for the status change")
    next_actions: List[str] = Field(description="Next actions required")
    requires_notification: bool = Field(description="Whether notification is required")


class ExecutionResult(BaseModel):
    """Structured output for execution results."""
    execution_status: str = Field(description="Status of the execution")
    success: bool = Field(description="Whether execution was successful")
    results_summary: str = Field(description="Summary of execution results")
    completed_steps: List[str] = Field(description="List of completed steps")
    failed_steps: List[str] = Field(description="List of failed steps")
    next_steps: List[str] = Field(description="Next steps to be taken")


class OpenAIWrapper:
    """Wrapper for OpenAI Responses API with structured outputs."""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    def _create_json_schema(self, pydantic_model: BaseModel) -> Dict[str, Any]:
        """Convert Pydantic model to JSON schema for structured outputs."""
        schema = pydantic_model.model_json_schema()
        
        # Ensure additionalProperties is false for all objects to meet OpenAI's strict requirements
        def fix_schema(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "object" and "additionalProperties" not in obj:
                    obj["additionalProperties"] = False
                for key, value in obj.items():
                    fix_schema(value)
            elif isinstance(obj, list):
                for item in obj:
                    fix_schema(item)
        
        fix_schema(schema)
        
        return {
            "type": "json_schema",
            "name": pydantic_model.__name__,
            "strict": True,
            "schema": schema
        }
    
    def generate_text(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response."""
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature
        )
        return resp.output_text
    
    def generate_structured(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema."""
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        return schema_model.model_validate(resp.output_parsed)
    
    async def generate_text_async(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response asynchronously."""
        resp = await self.async_client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature
        )
        return resp.output_text
    
    async def generate_structured_async(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema asynchronously."""
        resp = await self.async_client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        return schema_model.model_validate(resp.output_parsed)
    
    async def assess_risk(self, prompt: str) -> RiskAssessment:
        """Perform risk assessment with structured output."""
        return await self.generate_structured_async(prompt, RiskAssessment)
    
    async def determine_approval_routing(self, prompt: str) -> ApprovalRouting:
        """Determine approval routing with structured output."""
        return await self.generate_structured_async(prompt, ApprovalRouting)
    
    async def extract_action_items(self, prompt: str) -> ActionItemList:
        """Extract action items with structured output."""
        return await self.generate_structured_async(prompt, ActionItemList)