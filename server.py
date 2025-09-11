#!/usr/bin/env python3
"""
Customer Call Center Analytics API Server
Standardized RESTful API with /api/v1/* endpoints
Clean routing layer - NO business logic, only proxy to services
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import service abstractions - NO business logic in routes
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.plan_service import PlanService
from src.services.case_service import CaseService
from src.services.governance_service import GovernanceService
from src.services.system_service import SystemService

# Load environment variables from .env file
load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

# Initialize all services at startup (fail-fast)
transcript_service = TranscriptService(api_key=api_key)
analysis_service = AnalysisService(api_key=api_key)
plan_service = PlanService(api_key=api_key)
case_service = CaseService(api_key=api_key)
governance_service = GovernanceService(api_key=api_key)
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
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class GovernanceSubmissionRequest(BaseModel):
    action_id: str
    description: str
    financial_impact: Optional[bool] = False
    risk_score: Optional[float] = 0.5
    amount: Optional[float] = 0
    submitted_by: str
    submitted_at: Optional[str] = None

class GovernanceApprovalRequest(BaseModel):
    governance_id: str
    action: str  # "approve" or "reject"
    approved_by: str
    conditions: Optional[List[str]] = []
    notes: Optional[str] = ""
    approved_at: Optional[str] = None

class EmergencyOverrideRequest(BaseModel):
    action_id: str
    override_by: str
    emergency_type: str
    justification: str
    approval_level_bypassed: str
    executed_at: Optional[str] = None

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
            "plans": "/api/v1/plans",
            "cases": "/api/v1/cases",
            "governance": "/api/v1/governance",
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
# CASE MANAGEMENT ENDPOINTS - 5 endpoints
# ===============================================

@app.get("/api/v1/cases")
async def list_cases(
    limit: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    customer: Optional[str] = Query(None)
):
    """List all cases - proxies to case service."""
    try:
        if any([status, priority, customer]):
            search_params = {}
            if status:
                search_params["status"] = status
            if priority:
                search_params["priority"] = priority
            if customer:
                search_params["customer"] = customer
            return await case_service.search(search_params)
        else:
            return await case_service.list_all(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list cases: {str(e)}")

@app.get("/api/v1/cases/{case_id}")
async def get_case(case_id: str):
    """Get case by ID - proxies to case service."""
    try:
        result = await case_service.get_by_id(case_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case: {str(e)}")

@app.get("/api/v1/cases/{case_id}/transcripts")
async def get_case_transcripts(case_id: str):
    """Get case transcripts - proxies to case service."""
    try:
        return await case_service.get_transcripts(case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case transcripts: {str(e)}")

@app.get("/api/v1/cases/{case_id}/analyses")
async def get_case_analyses(case_id: str):
    """Get case analyses - proxies to case service."""
    try:
        return await case_service.get_analyses(case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case analyses: {str(e)}")

@app.get("/api/v1/cases/{case_id}/plans")
async def get_case_plans(case_id: str):
    """Get case action plans - proxies to case service."""
    try:
        return await case_service.get_plans(case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case plans: {str(e)}")

# ===============================================
# GOVERNANCE ENDPOINTS - 6 endpoints
# ===============================================

@app.post("/api/v1/governance/submissions")
async def submit_for_governance(request: GovernanceSubmissionRequest):
    """Submit for governance review - proxies to governance service."""
    try:
        return await governance_service.submit(request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit for governance: {str(e)}")

@app.get("/api/v1/governance/submissions/{governance_id}")
async def get_governance_status(governance_id: str):
    """Get governance submission status - proxies to governance service."""
    try:
        result = await governance_service.get_status(governance_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Governance submission {governance_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get governance status: {str(e)}")

@app.get("/api/v1/governance/queue")
async def get_governance_queue(status: Optional[str] = Query(None)):
    """Get governance approval queue - proxies to governance service."""
    try:
        return await governance_service.get_queue(status_filter=status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get governance queue: {str(e)}")

@app.post("/api/v1/governance/approvals")
async def process_governance_approval(request: GovernanceApprovalRequest):
    """Process governance approval - proxies to governance service."""
    try:
        return await governance_service.process_approval(request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")

@app.get("/api/v1/governance/audit")
async def get_governance_audit_trail(
    user_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    limit: Optional[int] = Query(50)
):
    """Get governance audit trail - proxies to governance service."""
    try:
        audit_filters = {
            "user_id": user_id,
            "event_type": event_type,
            "start_date": start_date,
            "limit": limit
        }
        return await governance_service.get_audit_trail(audit_filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit trail: {str(e)}")

@app.get("/api/v1/governance/metrics")
async def get_governance_metrics():
    """Get governance metrics - proxies to governance service."""
    try:
        return await governance_service.get_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get governance metrics: {str(e)}")

@app.post("/api/v1/governance/emergency-override")
async def emergency_override(request: EmergencyOverrideRequest):
    """Process emergency governance override - proxies to governance service."""
    try:
        return await governance_service.emergency_override(request.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process emergency override: {str(e)}")

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

@app.get("/api/cases")
async def legacy_api_cases(priority: Optional[int] = None, status: Optional[str] = None, search: Optional[str] = None):
    """Legacy endpoint - redirects to /api/v1/cases."""
    # Convert legacy parameters
    priority_str = None
    if priority == 1:
        priority_str = "high"
    elif priority == 2:
        priority_str = "medium"
    elif priority == 3:
        priority_str = "low"
    
    return await list_cases(status=status, priority=priority_str, customer=search)

# ===============================================
# MAIN ENTRY POINT
# ===============================================

if __name__ == "__main__":
    print("🚀 Starting Customer Call Center Analytics API Server")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 Server URL: http://0.0.0.0:8000")
    print("✅ All 43 standardized /api/v1/* endpoints available")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )