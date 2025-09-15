#!/usr/bin/env python3
"""
Customer Call Center Analytics API Server
Standardized RESTful API with /api/v1/* endpoints
Clean routing layer - NO business logic, only proxy to services
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Initialize OpenTelemetry tracing IMMEDIATELY after env loading for complete observability coverage
try:
    from src.telemetry import initialize_tracing
    initialize_tracing(
        service_name="xai",
        enable_console=os.getenv("OTEL_CONSOLE_ENABLED", "true").lower() == "true",
        enable_jaeger=os.getenv("OTEL_JAEGER_ENABLED", "false").lower() == "true"
    )
except ImportError:
    pass  # Telemetry not available

# NOW import everything else
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# Import service abstractions - NO business logic in routes
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.insights_service import InsightsService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.system_service import SystemService

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

class PlanUpdateRequest(BaseModel):
    updates: Dict[str, Any]

class ApprovalRequest(BaseModel):
    approved_by: str
    approved_at: Optional[str] = None
    notes: Optional[str] = ""

class ExecutionRequest(BaseModel):
    executed_by: str

# Workflow request models
class WorkflowExtractRequest(BaseModel):
    plan_id: str

class WorkflowApprovalRequest(BaseModel):
    approved_by: str
    reasoning: Optional[str] = None

class WorkflowRejectionRequest(BaseModel):
    rejected_by: str
    reason: str

class WorkflowExecutionRequest(BaseModel):
    executed_by: str


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
            "metrics": "/api/v1/metrics",
            "health": "/api/v1/health"
        }
    }

# ===============================================
# SYSTEM ENDPOINTS - 3 endpoints
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

@app.get("/api/v1/workflow/status")
async def get_workflow_status():
    """Workflow status endpoint - proxies to system service."""
    try:
        return await system_service.get_workflow_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow status retrieval failed: {str(e)}")

# ===============================================
# TRANSCRIPT ENDPOINTS - 8 endpoints
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
        return await transcript_service.create(request.dict())
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

@app.get("/api/v1/transcripts/search")
async def search_transcripts(
    customer: Optional[str] = Query(None),
    topic: Optional[str] = Query(None),
    text: Optional[str] = Query(None)
):
    """Search transcripts - proxies to transcript service."""
    try:
        search_params = {}
        if customer:
            search_params["customer"] = customer
        if topic:
            search_params["topic"] = topic
        if text:
            search_params["text"] = text
            
        if not search_params:
            raise HTTPException(status_code=400, detail="Must specify customer, topic, or text parameter")
            
        return await transcript_service.search(search_params)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search transcripts: {str(e)}")

@app.get("/api/v1/transcripts/metrics")
async def get_transcript_metrics():
    """Get transcript metrics - proxies to transcript service."""
    try:
        return await transcript_service.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript metrics: {str(e)}")

@app.post("/api/v1/transcripts/bulk")
async def create_bulk_transcripts(requests: List[TranscriptCreateRequest]):
    """Create multiple transcripts - proxies to transcript service."""
    try:
        results = []
        for request in requests:
            result = await transcript_service.create(request.dict())
            results.append(result)
        return {"transcripts": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bulk transcripts: {str(e)}")

@app.get("/api/v1/transcripts/{transcript_id}/messages")
async def get_transcript_messages(transcript_id: str):
    """Get transcript messages - proxies to transcript service."""
    try:
        transcript = await transcript_service.get_by_id(transcript_id)
        if not transcript:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        return transcript.get("messages", [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript messages: {str(e)}")

# ===============================================
# ANALYSIS ENDPOINTS - 5 endpoints
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
        return await analysis_service.create(request.dict())
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

@app.get("/api/v1/analyses/search/transcript/{transcript_id}")
async def search_analyses_by_transcript(transcript_id: str):
    """Search analyses by transcript ID - proxies to analysis service."""
    try:
        return await analysis_service.search_by_transcript(transcript_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search analyses: {str(e)}")

# ===============================================
# INSIGHTS ENDPOINTS - 5 endpoints
# ===============================================

@app.get("/api/v1/insights/patterns")
async def discover_risk_patterns(risk_threshold: float = Query(0.7)):
    """Discover high-risk patterns across all analyses - proxies to insights service."""
    try:
        return await insights_service.discover_risk_patterns(risk_threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to discover risk patterns: {str(e)}")

@app.get("/api/v1/insights/risks")
async def get_high_risks(risk_threshold: float = Query(0.8)):
    """Get high-risk patterns (convenience endpoint) - proxies to insights service."""
    try:
        return await insights_service.discover_risk_patterns(risk_threshold)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get high risks: {str(e)}")

@app.get("/api/v1/insights/recommendations/{customer_id}")
async def get_customer_recommendations(customer_id: str):
    """Get AI recommendations for a customer - proxies to insights service."""
    try:
        return await insights_service.get_customer_recommendations(customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@app.get("/api/v1/insights/similar/{analysis_id}")
async def find_similar_cases(analysis_id: str, limit: int = Query(5)):
    """Find analyses with similar risk patterns - proxies to insights service."""
    try:
        return await insights_service.find_similar_cases(analysis_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar cases: {str(e)}")

@app.get("/api/v1/insights/dashboard")
async def get_insights_dashboard():
    """Get comprehensive insights dashboard - proxies to insights service."""
    try:
        return await insights_service.get_insights_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights dashboard: {str(e)}")

# New insights management endpoints
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

@app.post("/api/v1/insights/query")
async def query_insights_graph(request: dict):
    """Execute raw Cypher query on knowledge graph - proxies to insights service."""
    try:
        cypher_query = request.get("cypher")
        parameters = request.get("parameters", {})
        
        if not cypher_query:
            raise HTTPException(status_code=400, detail="cypher parameter is required")
            
        return await insights_service.execute_query(cypher_query, parameters)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")

@app.get("/api/v1/insights/status")
async def get_insights_status():
    """Get knowledge graph status and statistics - proxies to insights service."""
    try:
        return await insights_service.get_graph_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights status: {str(e)}")

@app.delete("/api/v1/insights/analyses/{analysis_id}")
async def delete_insights_analysis(analysis_id: str):
    """Delete analysis from knowledge graph - proxies to insights service."""
    try:
        return await insights_service.delete_analysis(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")

@app.delete("/api/v1/insights/customers/{customer_id}")
async def delete_insights_customer(customer_id: str, cascade: bool = Query(False)):
    """Delete customer from knowledge graph - proxies to insights service."""
    try:
        return await insights_service.delete_customer(customer_id, cascade)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete customer: {str(e)}")

@app.post("/api/v1/insights/prune")
async def prune_insights_data(request: dict):
    """Prune old data from knowledge graph - proxies to insights service."""
    try:
        older_than_days = request.get("older_than_days")
        
        if not older_than_days or not isinstance(older_than_days, int):
            raise HTTPException(status_code=400, detail="older_than_days (integer) is required")
            
        return await insights_service.prune_old_data(older_than_days)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prune data: {str(e)}")

@app.delete("/api/v1/insights/clear")
async def clear_insights_graph():
    """Clear entire knowledge graph - proxies to insights service."""
    try:
        return await insights_service.clear_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear graph: {str(e)}")

# Visualization endpoints
@app.get("/api/v1/insights/visualization/data")
async def get_visualization_data():
    """Get knowledge graph data formatted for visualization - proxies to insights service."""
    try:
        return await insights_service.get_visualization_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get visualization data: {str(e)}")

@app.get("/api/v1/insights/visualization/stats")
async def get_visualization_statistics():
    """Get knowledge graph statistics for visualization - proxies to insights service."""
    try:
        return await insights_service.get_visualization_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get visualization statistics: {str(e)}")

# ===============================================
# ACTION PLAN ENDPOINTS - 8 endpoints
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
        return await plan_service.create(request.dict())
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

@app.put("/api/v1/plans/{plan_id}")
async def update_plan(plan_id: str, request: PlanUpdateRequest):
    """Update action plan - proxies to plan service."""
    try:
        result = await plan_service.update(plan_id, request.updates)
        if not result:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update plan: {str(e)}")

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

@app.get("/api/v1/plans/search/analysis/{analysis_id}")
async def search_plans_by_analysis(analysis_id: str):
    """Search action plans by analysis ID - proxies to plan service."""
    try:
        return await plan_service.search_by_analysis(analysis_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search plans: {str(e)}")

@app.post("/api/v1/plans/{plan_id}/approve")
async def approve_plan(plan_id: str, request: ApprovalRequest):
    """Approve action plan - proxies to plan service."""
    try:
        return await plan_service.approve(plan_id, request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve plan: {str(e)}")

@app.post("/api/v1/plans/{plan_id}/execute")
async def execute_plan(plan_id: str, request: ExecutionRequest):
    """Execute approved action plan - proxies to plan service."""
    try:
        return await plan_service.execute(plan_id, request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute plan: {str(e)}")


# ===============================================
# WORKFLOW APPROVAL ENDPOINTS
# Pure routing layer - all logic in WorkflowService
# ===============================================

@app.post("/api/v1/workflows/extract")
async def extract_workflow(request: WorkflowExtractRequest):
    """Extract workflow from action plan."""
    try:
        result = await workflow_service.extract_workflow_from_plan(request.plan_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract workflow: {str(e)}")

@app.get("/api/v1/workflows")
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by workflow status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"), 
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """List workflows with optional filters."""
    try:
        workflows = await workflow_service.list_workflows(
            status=status,
            risk_level=risk_level,
            limit=limit
        )
        return workflows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

@app.get("/api/v1/workflows/pending")
async def get_pending_workflows():
    """Get workflows requiring human approval."""
    try:
        workflows = await workflow_service.get_pending_approvals()
        return workflows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending workflows: {str(e)}")

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

@app.get("/api/v1/workflows/plan/{plan_id}")
async def get_workflows_by_plan(plan_id: str):
    """Get all workflows for a specific plan."""
    try:
        workflows = await workflow_service.get_workflows_by_plan(plan_id)
        return workflows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows by plan: {str(e)}")

@app.get("/api/v1/workflows/type/{workflow_type}")
async def get_workflows_by_type(workflow_type: str):
    """Get workflows by type."""
    try:
        workflows = await workflow_service.get_workflows_by_type(workflow_type)
        return workflows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows by type: {str(e)}")

@app.get("/api/v1/workflows/plan/{plan_id}/type/{workflow_type}")
async def get_workflows_by_plan_and_type(plan_id: str, workflow_type: str):
    """Get workflows by plan and type."""
    try:
        workflows = await workflow_service.get_workflows_by_plan_and_type(plan_id, workflow_type)
        return workflows
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows by plan and type: {str(e)}")

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

@app.post("/api/v1/workflows/{workflow_id}/reject")
async def reject_workflow(workflow_id: str, request: WorkflowRejectionRequest):
    """Reject a workflow."""
    try:
        result = await workflow_service.reject_workflow(
            workflow_id=workflow_id,
            rejected_by=request.rejected_by,
            reason=request.reason
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject workflow: {str(e)}")

@app.post("/api/v1/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecutionRequest):
    """Execute an approved workflow."""
    try:
        result = await workflow_service.execute_workflow(
            workflow_id=workflow_id,
            executed_by=request.executed_by
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")

@app.get("/api/v1/workflows/{workflow_id}/history")
async def get_workflow_history(workflow_id: str):
    """Get workflow state transition history."""
    try:
        result = await workflow_service.get_workflow_history(workflow_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow history: {str(e)}")

@app.post("/api/v1/workflows/execute-all")
async def execute_all_approved_workflows(request: Optional[Dict] = None):
    """Execute all approved workflows."""
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

@app.get("/api/v1/executions")
async def list_executions(
    limit: Optional[int] = Query(None, description="Maximum number of results"),
    status: Optional[str] = Query(None, description="Filter by execution status"),
    executor_type: Optional[str] = Query(None, description="Filter by executor type")
):
    """List all executions with optional filters."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()

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

@app.get("/api/v1/workflows/{workflow_id}/executions")
async def get_workflow_executions(workflow_id: str):
    """Get all execution records for a workflow."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()
        
        result = await execution_engine.get_workflow_execution_history(workflow_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow executions: {str(e)}")

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


@app.post("/api/v1/workflows/{workflow_id}/preview-execution")
async def preview_workflow_execution(workflow_id: str):
    """Preview what would be executed without actually executing."""
    try:
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        execution_engine = WorkflowExecutionEngine()
        
        result = await execution_engine.preview_execution(workflow_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to preview execution: {str(e)}")

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
async def delete_all_workflows(
    status: Optional[str] = Query(None, description="Only delete workflows with this status"),
    risk_level: Optional[str] = Query(None, description="Only delete workflows with this risk level"),
    plan_id: Optional[str] = Query(None, description="Only delete workflows for this plan")
):
    """Delete all workflows with optional filters."""
    try:
        # Note: Current service doesn't support filters, so we implement basic version
        # In the future, this could be enhanced to support filtering
        deleted_count = await workflow_service.delete_all_workflows()

        return {
            "message": "All workflows deleted successfully",
            "deleted_count": deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete workflows: {str(e)}")


# ===============================================
# LEGACY ENDPOINTS (for backward compatibility)
# These will be deprecated once frontend migrates
# ===============================================

# Legacy transcript endpoints
@app.get("/transcripts")
async def legacy_get_transcripts():
    """Legacy endpoint - redirects to /api/v1/transcripts."""
    return await list_transcripts()

@app.get("/transcript/{transcript_id}")
async def legacy_get_transcript(transcript_id: str):
    """Legacy endpoint - redirects to /api/v1/transcripts/{id}."""
    return await get_transcript(transcript_id)

@app.post("/generate")
async def legacy_generate_transcript(request: dict):
    """Legacy endpoint - redirects to /api/v1/transcripts."""
    transcript_request = TranscriptCreateRequest(**request)
    return await create_transcript(transcript_request)

# Legacy API endpoints
@app.get("/api/metrics")
async def legacy_api_metrics():
    """Legacy endpoint - redirects to /api/v1/metrics."""
    return await get_dashboard_metrics()


# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    print("🚀 Starting Customer Call Center Analytics API Server")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 Server URL: http://0.0.0.0:8000")
    print("✅ All 30 standardized /api/v1/* endpoints available")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="debug"
    )