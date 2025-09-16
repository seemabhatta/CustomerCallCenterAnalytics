from typing import List, Literal
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    title: str = Field(description="Clear, actionable title")
    description: str = Field(description="Detailed description of the action")
    pillar: Literal["BORROWER", "ADVISOR", "SUPERVISOR", "LEADERSHIP"] = Field(description="Responsible pillar")
    priority: Literal["LOW", "MEDIUM", "HIGH"] = Field(description="Priority level")
    estimated_hours: float = Field(ge=0.1, description="Estimated effort in hours")


class ActionItemList(BaseModel):
    workflow_type: str = Field(description="Type of workflow")
    action_items: List[ActionItem] = Field(description="List of extracted action items")
    total_items: int = Field(description="Total number of action items")