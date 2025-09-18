#!/usr/bin/env python3
"""
Customer Call Center Analytics API Server
Streamlined RESTful API with core /api/v1/* endpoints
Clean routing layer - NO business logic, only proxy to services
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Initialize OpenTelemetry tracing IMMEDIATELY after env loading for complete observability coverage
try:
    from src.infrastructure.telemetry import initialize_tracing
    initialize_tracing(
        service_name="xai",
        enable_console=os.getenv("OTEL_CONSOLE_ENABLED", "true").lower() == "true",
        enable_jaeger=os.getenv("OTEL_JAEGER_ENABLED", "false").lower() == "true"
    )
except ImportError:
    pass  # Telemetry not available

# Configure logging
logger = logging.getLogger(__name__)

# NOW import everything else
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uvicorn

# Import service abstractions - NO business logic in routes
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.insights_service import InsightsService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.system_service import SystemService
from src.services.leadership_insights_service import LeadershipInsightsService

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

# Initialize all services at startup (fail-fast)
db_path = os.getenv('DATABASE_PATH', './data/call_center.db')
transcript_service = TranscriptService(api_key=api_key)
analysis_service = AnalysisService(api_key=api_key)
insights_service = InsightsService()
plan_service = PlanService(api_key=api_key)
workflow_service = WorkflowService(db_path=db_path)
system_service = SystemService(api_key=api_key)
leadership_insights_service = LeadershipInsightsService(api_key=api_key, db_path=db_path)

print("✅ All services initialized successfully")

app = FastAPI(
    title="Customer Call Center Analytics API",
    description="AI-powered system for generating and analyzing call center transcripts",
    version="1.0.0"
)

# Add CORS middleware for frontend connectivity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class TranscriptCreateRequest(BaseModel):
    topic: Optional[str] = "payment_inquiry"
    urgency: Optional[str] = "medium"
    financial_impact: Optional[bool] = False
    customer_sentiment: Optional[str] = "neutral"
    customer_id: Optional[str] = "CUST_001"
    store: Optional[bool] = True

class AnalysisCreateRequest(BaseModel):
    transcript_id: str
    analysis_type: Optional[str] = "comprehensive"
    urgency: Optional[str] = "medium"
    customer_tier: Optional[str] = "standard"
    store: Optional[bool] = True

class PlanCreateRequest(BaseModel):
    analysis_id: str
    plan_type: Optional[str] = "standard"
    urgency: Optional[str] = "medium"
    customer_tier: Optional[str] = "standard"
    constraints: Optional[List[str]] = []
    store: Optional[bool] = True

class WorkflowExtractRequest(BaseModel):
    plan_id: str

class WorkflowApprovalRequest(BaseModel):
    approved_by: str
    reasoning: Optional[str] = None

class WorkflowExecutionRequest(BaseModel):
    executed_by: str

class LeadershipChatRequest(BaseModel):
    query: str
    executive_id: str
    executive_role: Optional[str] = "Manager"
    session_id: Optional[str] = None

class LeadershipSessionRequest(BaseModel):
    executive_id: str
    limit: Optional[int] = 10

class LeadershipDashboardRequest(BaseModel):
    executive_role: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Customer Call Center Analytics",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "api_version": "v1",
        "endpoints": {
            "transcripts": "/api/v1/transcripts",
            "analyses": "/api/v1/analyses",
            "insights": "/api/v1/insights",
            "plans": "/api/v1/plans",
            "workflows": "/api/v1/workflows",
            "executions": "/api/v1/executions",
            "metrics": "/api/v1/metrics",
            "health": "/api/v1/health",
            "leadership": "/api/v1/leadership"
        }
    }

# ===============================================
# SYSTEM ENDPOINTS
# ===============================================

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint - proxies to system service."""
    try:
        result = await system_service.health_check()
        if result.get("status") == "unhealthy":
            return JSONResponse(status_code=503, content=result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/api/v1/metrics")
async def get_dashboard_metrics():
    """Dashboard metrics endpoint - proxies to system service."""
    try:
        return await system_service.get_dashboard_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics collection failed: {str(e)}")

# ===============================================
# TRANSCRIPT ENDPOINTS
# ===============================================

@app.get("/api/v1/transcripts")
async def list_transcripts(limit: Optional[int] = Query(None)):
    """List all transcripts - proxies to transcript service."""
    try:
        return await transcript_service.list_all(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list transcripts: {str(e)}")

@app.post("/api/v1/transcripts")
async def create_transcript(request: TranscriptCreateRequest):
    """Create new transcript - proxies to transcript service."""
    try:
        return await transcript_service.create(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transcript: {str(e)}")

@app.get("/api/v1/transcripts/{transcript_id}")
async def get_transcript(transcript_id: str):
    """Get transcript by ID - proxies to transcript service."""
    try:
        result = await transcript_service.get_by_id(transcript_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")

@app.delete("/api/v1/transcripts/{transcript_id}")
async def delete_transcript(transcript_id: str):
    """Delete transcript by ID - proxies to transcript service."""
    try:
        success = await transcript_service.delete(transcript_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        return {"message": f"Transcript {transcript_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete transcript: {str(e)}")

# ===============================================
# ANALYSIS ENDPOINTS
# ===============================================

@app.get("/api/v1/analyses")
async def list_analyses(limit: Optional[int] = Query(None)):
    """List all analyses - proxies to analysis service."""
    try:
        return await analysis_service.list_all(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list analyses: {str(e)}")

@app.post("/api/v1/analyses")
async def create_analysis(request: AnalysisCreateRequest):
    """Create new analysis - proxies to analysis service."""
    try:
        return await analysis_service.create(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")

@app.get("/api/v1/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis by ID - proxies to analysis service."""
    try:
        result = await analysis_service.get_by_id(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")

@app.delete("/api/v1/analyses/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete analysis by ID - proxies to analysis service."""
    try:
        success = await analysis_service.delete(analysis_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        return {"message": f"Analysis {analysis_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")

@app.delete("/api/v1/analyses")
async def delete_all_analyses():
    """Delete all analyses - proxies to analysis service."""
    try:
        count = await analysis_service.delete_all()
        return {"message": f"Deleted {count} analyses successfully", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete all analyses: {str(e)}")

# ===============================================
# INSIGHTS ENDPOINTS (Core subset)
# ===============================================

@app.get("/api/v1/insights/patterns")
async def discover_risk_patterns(risk_threshold: float = Query(0.7)):
    """Discover high-risk patterns across all analyses - proxies to insights service."""
    try:
        return await insights_service.discover_risk_patterns(risk_threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover risk patterns: {str(e)}")

@app.get("/api/v1/insights/dashboard")
async def get_insights_dashboard():
    """Get comprehensive insights dashboard - proxies to insights service."""
    try:
        return await insights_service.get_insights_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights dashboard: {str(e)}")

@app.post("/api/v1/insights/populate")
async def populate_insights_graph(request: dict):
    """Populate knowledge graph from analysis data - proxies to insights service."""
    try:
        analysis_id = request.get("analysis_id")
        analysis_ids = request.get("analysis_ids")
        from_date = request.get("from_date")
        populate_all = request.get("all", False)

        if analysis_id:
            return await insights_service.populate_from_analysis(analysis_id)
        elif analysis_ids:
            return await insights_service.populate_batch(analysis_ids)
        elif populate_all or from_date:
            return await insights_service.populate_all(from_date)
        else:
            raise HTTPException(status_code=400, detail="Must provide analysis_id, analysis_ids, or all=true")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to populate insights: {str(e)}")

@app.get("/api/v1/insights/status")
async def get_insights_status():
    """Get knowledge graph status and statistics - proxies to insights service."""
    try:
        return await insights_service.get_graph_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights status: {str(e)}")

# ===============================================
# PLAN ENDPOINTS
# ===============================================

@app.get("/api/v1/plans")
async def list_plans(limit: Optional[int] = Query(None)):
    """List all action plans - proxies to plan service."""
    try:
        return await plan_service.list_all(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list plans: {str(e)}")

@app.post("/api/v1/plans")
async def create_plan(request: PlanCreateRequest):
    """Create new action plan - proxies to plan service."""
    try:
        return await plan_service.create(request.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create plan: {str(e)}")

@app.get("/api/v1/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get action plan by ID - proxies to plan service."""
    try:
        result = await plan_service.get_by_id(plan_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plan: {str(e)}")

@app.delete("/api/v1/plans/{plan_id}")
async def delete_plan(plan_id: str):
    """Delete action plan by ID - proxies to plan service."""
    try:
        success = await plan_service.delete(plan_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        return {"message": f"Plan {plan_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete plan: {str(e)}")

@app.delete("/api/v1/plans")
async def delete_all_plans():
    """Delete all action plans - bulk operation."""
    try:
        result = await plan_service.delete_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete all plans: {str(e)}")

# ===============================================
# WORKFLOW ENDPOINTS
# ===============================================

@app.post("/api/v1/workflows/extract-all")
async def extract_all_workflows(request: WorkflowExtractRequest):
    """Extract all granular workflows from action plan (background processing)."""
    try:
        result = await workflow_service.extract_all_workflows_background(request.plan_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start workflow extraction: {str(e)}")

@app.get("/api/v1/workflows")
async def list_workflows(
    plan_id: Optional[str] = Query(None, description="Filter by plan ID"),
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """List workflows with optional filters."""
    try:
        workflows = await workflow_service.list_workflows(
            plan_id=plan_id,
            status=status,
            risk_level=risk_level,
            limit=limit
        )
        return workflows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@app.get("/api/v1/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow by ID."""
    try:
        workflow = await workflow_service.get_workflow(workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow_id}")
        return workflow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")

@app.post("/api/v1/workflows/{workflow_id}/approve")
async def approve_workflow(workflow_id: str, request: WorkflowApprovalRequest):
    """Approve a workflow."""
    try:
        result = await workflow_service.approve_action_item_workflow(
            workflow_id=workflow_id,
            approved_by=request.approved_by,
            reasoning=request.reasoning
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve workflow: {str(e)}")

@app.post("/api/v1/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecutionRequest):
    """Execute an approved workflow."""
    logger.info(f"Starting workflow execution: workflow_id={workflow_id}, executed_by={request.executed_by}")
    try:
        result = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            executed_by=request.executed_by
        )
        logger.info(f"Workflow execution completed successfully: workflow_id={workflow_id}")
        return result
    except ValueError as e:
        logger.error(f"Workflow execution validation error: workflow_id={workflow_id}, error={str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Workflow execution failed: workflow_id={workflow_id}, executed_by={request.executed_by}")
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@app.delete("/api/v1/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete workflow by ID."""
    try:
        deleted = await workflow_service.delete_workflow(workflow_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

        return {"message": f"Workflow {workflow_id} deleted successfully", "deleted": True}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")

@app.delete("/api/v1/workflows")
async def delete_all_workflows():
    """Delete all workflows."""
    try:
        deleted_count = await workflow_service.delete_all_workflows()
        return {
            "message": "All workflows deleted successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflows: {str(e)}")

@app.post("/api/v1/workflows/execute-all")
async def execute_all_approved_workflows(request: Optional[Dict] = None):
    """Execute all approved workflows (orchestration)."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        workflow_type = None
        executed_by = "api_user"

        if request:
            workflow_type = request.get('workflow_type')
            executed_by = request.get('executed_by', executed_by)

        result = await execution_engine.execute_all_approved_workflows(
            workflow_type=workflow_type,
            executed_by=executed_by
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute all workflows: {str(e)}")

# ===============================================
# EXECUTION ENDPOINTS
# ===============================================

@app.get("/api/v1/executions")
async def list_executions(
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    limit: Optional[int] = Query(None, description="Maximum number of results"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    executor_type: Optional[str] = Query(None, description="Filter by executor type")
):
    """List all executions with optional filters."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        # Note: workflow_id filtering not supported by list_all_executions
        result = await execution_engine.list_all_executions(
            limit=limit,
            status=status,
            executor_type=executor_type
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")

@app.get("/api/v1/executions/{execution_id}")
async def get_execution_status(execution_id: str):
    """Get detailed execution status and results."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        result = await execution_engine.get_execution_status(execution_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution status: {str(e)}")

@app.delete("/api/v1/executions/{execution_id}")
async def delete_execution(execution_id: str):
    """Delete execution record by ID."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        deleted = await execution_engine.delete_execution(execution_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

        return {"message": f"Execution {execution_id} deleted successfully", "deleted": True}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete execution: {str(e)}")

@app.delete("/api/v1/executions")
async def delete_all_executions(
    status: Optional[str] = Query(None, description="Only delete executions with this status"),
    executor_type: Optional[str] = Query(None, description="Only delete executions of this type")
):
    """Delete all executions with optional filters."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        deleted_count = await execution_engine.delete_all_executions(
            status=status,
            executor_type=executor_type
        )

        return {
            "message": f"All executions deleted successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete executions: {str(e)}")

@app.get("/api/v1/executions/statistics")
async def get_execution_statistics():
    """Get comprehensive execution statistics."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

        result = await execution_engine.get_execution_statistics()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution statistics: {str(e)}")

# ===============================================
# ORCHESTRATION ENDPOINTS
# ===============================================

# In-memory storage for orchestration runs (NO FALLBACK - fails if not found)
orchestration_runs: Dict[str, Dict] = {}

@app.post("/api/v1/orchestrate/run")
async def orchestrate_run(request: Dict):
    """Run orchestration pipeline for transcripts - NO FALLBACK.

    Pipeline stages: Transcript → Analysis → Plan → Workflows → Execution
    """
    import uuid
    import asyncio
    from src.services.orchestration.simple_pipeline import run_simple_pipeline

    # Extract parameters (fail fast if missing)
    transcript_ids = request.get("transcript_ids", [])
    auto_approve = request.get("auto_approve", False)

    if not transcript_ids:
        raise HTTPException(status_code=400, detail="transcript_ids required - NO FALLBACK")

    # Generate run ID
    run_id = f"RUN_{uuid.uuid4().hex[:8].upper()}"

    # Initialize run status
    orchestration_runs[run_id] = {
        "id": run_id,
        "transcript_ids": transcript_ids,
        "auto_approve": auto_approve,
        "status": "RUNNING",
        "stage": "INITIALIZING",
        "started_at": datetime.utcnow().isoformat(),
        "results": [],
        "errors": []
    }

    # Run pipeline asynchronously for each transcript
    async def run_pipelines():
        for transcript_id in transcript_ids:
            try:
                orchestration_runs[run_id]["stage"] = f"PROCESSING_{transcript_id}"
                # Pass the status dict so SimplePipeline can update it in real-time
                result = await run_simple_pipeline(
                    transcript_id,
                    auto_approve,
                    status_dict=orchestration_runs[run_id]
                )
                orchestration_runs[run_id]["results"].append(result)
            except Exception as e:
                # NO FALLBACK - record failure and continue
                orchestration_runs[run_id]["errors"].append({
                    "transcript_id": transcript_id,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        # Update final status
        orchestration_runs[run_id]["status"] = "COMPLETED"
        orchestration_runs[run_id]["stage"] = "COMPLETE"
        orchestration_runs[run_id]["completed_at"] = datetime.utcnow().isoformat()

        # Calculate summary
        total_results = len(orchestration_runs[run_id]["results"])
        total_errors = len(orchestration_runs[run_id]["errors"])
        orchestration_runs[run_id]["summary"] = {
            "total_transcripts": len(transcript_ids),
            "successful": total_results,
            "failed": total_errors,
            "success_rate": total_results / len(transcript_ids) if transcript_ids else 0
        }

    # Start pipeline in background
    asyncio.create_task(run_pipelines())

    return {
        "run_id": run_id,
        "status": "STARTED",
        "transcript_count": len(transcript_ids),
        "auto_approve": auto_approve
    }

@app.get("/api/v1/orchestrate/status/{run_id}")
async def get_orchestration_status(run_id: str):
    """Get orchestration run status - NO FALLBACK."""
    if run_id not in orchestration_runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found - NO FALLBACK")

    run = orchestration_runs[run_id]

    # Calculate current progress
    total_transcripts = len(run["transcript_ids"])
    processed = len(run["results"]) + len(run["errors"])
    progress_percentage = (processed / total_transcripts * 100) if total_transcripts > 0 else 0

    return {
        **run,
        "progress": {
            "total": total_transcripts,
            "processed": processed,
            "percentage": round(progress_percentage, 2)
        }
    }

@app.get("/api/v1/orchestrate/runs")
async def list_orchestration_runs(
    limit: Optional[int] = Query(None, description="Limit the number of results"),
    status: Optional[str] = Query(None, description="Filter by status (RUNNING, COMPLETED)")
):
    """List all orchestration runs."""
    runs = list(orchestration_runs.values())

    # Filter by status if provided
    if status:
        runs = [r for r in runs if r["status"] == status]

    # Sort by started_at descending (most recent first)
    runs.sort(key=lambda x: x["started_at"], reverse=True)

    # Apply limit if provided
    if limit:
        runs = runs[:limit]

    return {
        "runs": runs,
        "total": len(runs)
    }

# ===============================================
# LEADERSHIP INSIGHTS ENDPOINTS
# ===============================================

@app.post("/api/v1/leadership/chat")
async def leadership_chat(request: LeadershipChatRequest):
    """Main chat interface for leadership insights - proxies to leadership service."""
    try:
        result = await leadership_insights_service.chat(
            query=request.query,
            executive_id=request.executive_id,
            executive_role=request.executive_role,
            session_id=request.session_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leadership chat failed: {str(e)}")

@app.get("/api/v1/leadership/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: Optional[int] = Query(50, description="Maximum messages to return")
):
    """Get conversation history for a session - proxies to leadership service."""
    try:
        result = await leadership_insights_service.get_session_history(session_id, limit)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session history: {str(e)}")

@app.get("/api/v1/leadership/sessions")
async def list_executive_sessions(
    executive_id: str = Query(..., description="Executive identifier"),
    limit: Optional[int] = Query(10, description="Maximum sessions to return")
):
    """List sessions for an executive - proxies to leadership service."""
    try:
        result = await leadership_insights_service.get_executive_sessions(executive_id, limit)
        return {"sessions": result, "total": len(result)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executive sessions: {str(e)}")

@app.get("/api/v1/leadership/sessions/{session_id}")
async def get_session_details(session_id: str):
    """Get session details including metadata - proxies to leadership service."""
    try:
        result = await leadership_insights_service.get_session_history(session_id, limit=1)
        if not result or not result.get('session'):
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return result['session']
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session details: {str(e)}")

@app.delete("/api/v1/leadership/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a leadership session - proxies to leadership service."""
    try:
        success = await leadership_insights_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        return {"message": f"Session {session_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/api/v1/leadership/dashboard")
async def get_leadership_dashboard(
    executive_role: Optional[str] = Query(None, description="Filter by executive role")
):
    """Get pre-computed insights dashboard - proxies to leadership service."""
    try:
        result = await leadership_insights_service.get_insights_dashboard(executive_role)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leadership dashboard: {str(e)}")

@app.get("/api/v1/leadership/cache/stats")
async def get_cache_statistics():
    """Get cache performance metrics - proxies to leadership service."""
    try:
        cache_stats = leadership_insights_service.get_cache_statistics()
        return cache_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache statistics: {str(e)}")

@app.get("/api/v1/leadership/patterns")
async def get_pattern_statistics():
    """Get learning patterns statistics - proxies to leadership service."""
    try:
        pattern_stats = leadership_insights_service.get_pattern_statistics()
        return pattern_stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pattern statistics: {str(e)}")

@app.get("/api/v1/leadership/status")
async def get_leadership_service_status():
    """Get leadership service health and component status."""
    try:
        result = leadership_insights_service.get_service_status()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get leadership service status: {str(e)}")

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    print("🚀 Starting Customer Call Center Analytics API Server")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 Server URL: http://0.0.0.0:8000")
    print("✅ Streamlined API with core endpoints only")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug"
    )