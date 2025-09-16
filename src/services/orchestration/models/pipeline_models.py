"""
Pipeline data models for orchestration
Provides type safety and validation for pipeline data flow
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class PipelineStage(Enum):
    """Pipeline stages"""
    TRANSCRIPT = "transcript"
    ANALYSIS = "analysis"
    PLAN = "plan"
    WORKFLOWS = "workflows"
    APPROVAL = "approval"
    EXECUTION = "execution"
    COMPLETE = "complete"


class WorkflowType(Enum):
    """Workflow types for granular processing"""
    BORROWER = "BORROWER"
    ADVISOR = "ADVISOR"
    SUPERVISOR = "SUPERVISOR"
    LEADERSHIP = "LEADERSHIP"


@dataclass
class PipelineInput:
    """Input parameters for pipeline execution"""
    transcript_id: str
    auto_approve: bool = False
    timeout_hours: int = 24


@dataclass
class PipelineResult:
    """Complete pipeline execution result"""
    transcript_id: str
    analysis_id: str
    plan_id: str
    workflow_count: int
    executed_count: int
    execution_results: List[Dict[str, Any]]
    stage: PipelineStage
    success: bool
    errors: Optional[List[str]] = None


@dataclass
class StageResult:
    """Result from individual pipeline stage"""
    stage: PipelineStage
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Human approval request data"""
    workflow_id: str
    action_item: str
    risk_level: str
    workflow_type: str
    requires_approval: bool
    timeout_hours: int = 24


@dataclass
class ApprovalResponse:
    """Human approval response data"""
    workflow_id: str
    approved: bool
    approver: str
    reason: str
    timestamp: str