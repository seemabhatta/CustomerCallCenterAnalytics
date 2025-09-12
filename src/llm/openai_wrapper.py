from typing import Dict, Any, Optional, List, Literal, Union
import os
from pydantic import BaseModel, Field
from openai import OpenAI, AsyncOpenAI
import asyncio


def rx_text(resp) -> str:
    """Return best-effort concatenated text from a Responses API result."""
    if getattr(resp, "output_text", None):
        return resp.output_text
    try:
        parts = []
        for b in getattr(resp, "output", []) or []:
            for c in getattr(b, "content", []) or []:
                t = getattr(c, "text", None)
                if isinstance(t, str):
                    parts.append(t)
        return "".join(parts).strip()
    except Exception:
        return str(resp)


def rx_parsed(resp):
    """Return parsed JSON when using text.format json_schema (or None)."""
    try:
        for b in getattr(resp, "output", []) or []:
            for c in getattr(b, "content", []) or []:
                p = getattr(c, "parsed", None)
                if p is not None:
                    return p
    except Exception:
        pass
    return None


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
        self.model = "gpt-4o"
    
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
        return rx_text(resp)
    
    def generate_structured(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema."""
        resp = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={"format": self._create_json_schema(schema_model)},
            temperature=temperature
        )
        parsed_data = rx_parsed(resp)
        if parsed_data:
            return schema_model.model_validate(parsed_data)
        raise ValueError("Failed to parse structured output")
    
    async def generate_text_async(self, prompt: str, temperature: float = 0.3) -> str:
        """Generate plain text response asynchronously."""
        resp = await self.async_client.responses.create(
            model=self.model,
            input=prompt,
            temperature=temperature
        )
        return rx_text(resp)
    
    async def generate_structured_async(self, prompt: str, schema_model: BaseModel, temperature: float = 0.3) -> Any:
        """Generate structured output using Pydantic model schema asynchronously."""
        try:
            resp = await self.async_client.responses.create(
                model=self.model,
                input=prompt,
                text={"format": self._create_json_schema(schema_model)},
                temperature=temperature
            )
            parsed_data = rx_parsed(resp)
            if parsed_data:
                return schema_model.model_validate(parsed_data)
            
            # Try to get text content if parsed data is not available
            text_content = rx_text(resp)
            if text_content:
                # Try to parse as JSON manually
                import json
                try:
                    json_data = json.loads(text_content)
                    return schema_model.model_validate(json_data)
                except json.JSONDecodeError:
                    raise ValueError(f"Response is not valid JSON: {text_content}")
            
            raise ValueError("Failed to parse structured output - no content returned")
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