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
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return resp.choices[0].message.content
    
    def generate_structured(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema."""
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_schema", "json_schema": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        content = resp.choices[0].message.content
        import json
        json_data = json.loads(content)
        return schema_model.model_validate(json_data)
    
    async def generate_text_async(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response asynchronously."""
        resp = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature
        )
        return resp.choices[0].message.content
    
    async def generate_structured_async(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema asynchronously."""
        try:
            resp = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_schema", "json_schema": self._create_json_schema(schema_model)},
                temperature=temperature
            )
            content = resp.choices[0].message.content
            import json
            json_data = json.loads(content)
            return schema_model.model_validate(json_data)
        except Exception as e:
            raise ValueError(f"Structured output generation failed: {e}")
    
    async def assess_risk(self, prompt: str) -> RiskAssessment:
        """Perform risk assessment with structured output."""
        return await self.generate_structured_async(prompt, RiskAssessment)
    
    async def determine_approval_routing(self, prompt: str) -> ApprovalRouting:
        """Determine approval routing with structured output."""
        return await self.generate_structured_async(prompt, ApprovalRouting)
    
    async def extract_action_items(self, prompt: str) -> ActionItemList:
        """Extract action items with structured output."""
        return await self.generate_structured_async(prompt, ActionItemList)