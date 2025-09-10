#!/usr/bin/env python3
"""
Simple FastAPI server for Replit environment
Streamlined version of the Customer Call Center Analytics API
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Real analysis and action plan components
from src.analyzers.call_analyzer import CallAnalyzer
from src.storage.analysis_store import AnalysisStore  
from src.generators.action_plan_generator import ActionPlanGenerator
from src.storage.action_plan_store import ActionPlanStore
import uuid
from datetime import datetime

# Load environment variables from Replit secrets
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

# Initialize real analysis and action plan services
print("🔧 Initializing analysis and action plan services...")
analyzer = None
analysis_store = None
action_plan_generator = None
action_plan_store = None

try:
    # Create data directory if needed
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    analyzer = CallAnalyzer(api_key=api_key)
    analysis_store = AnalysisStore("data/call_center.db")
    action_plan_generator = ActionPlanGenerator(db_path="data/call_center.db")
    action_plan_store = ActionPlanStore("data/call_center.db")
    print("✅ Analysis and action plan services initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize analysis services: {e}")
    raise e

app = FastAPI(
    title="Customer Call Center Analytics API",
    description="AI-powered system for generating and analyzing call center transcripts",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint with basic info."""
    return {
        "service": "Customer Call Center Analytics",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "api_key_configured": bool(api_key)
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "api_ready": bool(api_key)}

@app.get("/stats")
async def get_stats():
    """Get basic statistics."""
    try:
        from src.storage.transcript_store import TranscriptStore
        
        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        transcripts = store.get_all()
        
        return {
            "total_transcripts": len(transcripts),
            "database_path": "data/call_center.db",
            "service_status": "operational"
        }
    except Exception as e:
        return {"error": str(e), "total_transcripts": 0}

@app.get("/transcripts")
async def get_transcripts():
    """Get all stored transcripts."""
    try:
        from src.storage.transcript_store import TranscriptStore
        
        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        transcripts = store.get_all()
        
        # Convert to API format
        result = []
        for transcript in transcripts:
            result.append({
                "transcript_id": transcript.id,
                "customer_id": getattr(transcript, 'customer_id', 'Unknown'),
                "scenario": getattr(transcript, 'scenario', 'Unknown scenario'),
                "message_count": len(transcript.messages),
                "urgency": getattr(transcript, 'urgency', 'medium'),
                "financial_impact": getattr(transcript, 'financial_impact', False),
                "stored": True,
                "created_at": getattr(transcript, 'timestamp', None)
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcripts: {str(e)}")

@app.get("/transcript/{transcript_id}")
async def get_transcript_detail(transcript_id: str):
    """Get detailed transcript with full conversation."""
    try:
        from src.storage.transcript_store import TranscriptStore
        
        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        transcript = store.get_by_id(transcript_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
        # Return detailed transcript data
        return {
            "transcript_id": transcript.id,
            "customer_id": getattr(transcript, 'customer_id', 'Unknown'),
            "scenario": getattr(transcript, 'scenario', 'Unknown scenario'),
            "messages": [
                {
                    "role": getattr(msg, 'role', getattr(msg, 'speaker', 'unknown')),
                    "content": getattr(msg, 'content', getattr(msg, 'text', '')),
                    "timestamp": getattr(msg, 'timestamp', None)
                } for msg in transcript.messages
            ],
            "message_count": len(transcript.messages),
            "urgency": getattr(transcript, 'urgency', 'medium'),
            "financial_impact": getattr(transcript, 'financial_impact', False),
            "stored": True,
            "created_at": getattr(transcript, 'timestamp', None),
            "metadata": getattr(transcript, 'metadata', {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")

@app.post("/generate")
async def generate_transcript(request: dict):
    """Generate a new transcript."""
    try:
        from src.generators.transcript_generator import TranscriptGenerator
        from src.storage.transcript_store import TranscriptStore
        
        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        generator = TranscriptGenerator(api_key=api_key)
        store = TranscriptStore("data/call_center.db")
        
        # Generate transcript
        scenario = request.get("scenario", "payment_inquiry")
        urgency = request.get("urgency", "medium")
        financial_impact = request.get("financial_impact", False)
        customer_sentiment = request.get("customer_sentiment", "neutral")
        
        transcript = generator.generate(
            scenario=scenario,
            urgency=urgency,
            financial_impact=financial_impact,
            customer_sentiment=customer_sentiment
        )
        
        # Store if requested
        should_store = request.get("store", True)
        if should_store:
            store.store(transcript)
        
        return {
            "success": True,
            "transcript_id": transcript.id,
            "customer_id": getattr(transcript, 'customer_id', 'CUST_001'),
            "scenario": scenario,
            "message_count": len(transcript.messages),
            "urgency": urgency,
            "financial_impact": financial_impact,
            "stored": should_store,
            "created_at": getattr(transcript, 'timestamp', None)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

# ===============================================
# ANALYSIS API ENDPOINTS
# ===============================================

@app.post("/api/v1/analysis/analyze")
async def analyze_transcript_api(request: dict):
    """Analyze transcript via API."""
    try:
        if not analyzer or not analysis_store:
            raise HTTPException(status_code=503, detail="Analysis service not available")
            
        if "transcript_id" not in request:
            raise HTTPException(status_code=400, detail="transcript_id required")
            
        transcript_id = request["transcript_id"]
        
        from src.storage.transcript_store import TranscriptStore
        store = TranscriptStore("data/call_center.db")
        transcript = store.get_by_id(transcript_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
        # Generate real AI analysis
        analysis = analyzer.analyze(transcript)
        stored_analysis = analysis_store.store(analysis)
        
        return {
            "analysis_id": stored_analysis["id"],
            "intent": stored_analysis.get("intent"),
            "urgency": stored_analysis.get("urgency"), 
            "sentiment": stored_analysis.get("sentiment"),
            "confidence": stored_analysis.get("confidence")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/v1/analysis/{analysis_id}")
async def get_analysis_by_id(analysis_id: str):
    """Get analysis results by ID."""
    try:
        if not analysis_store:
            raise HTTPException(status_code=503, detail="Analysis service not available")
            
        analysis = analysis_store.get_by_id(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
        
        return {
            "analysis_id": analysis_id,
            "intent": analysis.get("intent"),
            "sentiment": analysis.get("sentiment"),
            "risk_scores": {
                "delinquency": analysis.get("borrower_risk", {}).get("delinquency_risk", 0),
                "churn": analysis.get("borrower_risk", {}).get("churn_risk", 0),
                "complaint": analysis.get("borrower_risk", {}).get("complaint_risk", 0),
                "refinance": analysis.get("borrower_risk", {}).get("refinance_risk", 0)
            },
            "advisor_metrics": analysis.get("advisor_metrics", {}),
            "call_summary": analysis.get("call_summary", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")

# ===============================================
# ACTION PLAN API ENDPOINTS  
# ===============================================

@app.post("/api/v1/plans/generate")
async def generate_action_plan_api(request: dict):
    """Generate action plan via API."""
    try:
        if not action_plan_generator or not action_plan_store:
            raise HTTPException(status_code=503, detail="Action plan service not available")
            
        if "transcript_id" not in request:
            raise HTTPException(status_code=400, detail="transcript_id required")
            
        transcript_id = request["transcript_id"]
        
        from src.storage.transcript_store import TranscriptStore
        store = TranscriptStore("data/call_center.db")
        transcript = store.get_by_id(transcript_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
        
        # Generate real action plan using AI
        plan = action_plan_generator.generate_comprehensive_plan(transcript)
        stored_plan = action_plan_store.store(plan)
        
        return {
            "plan_id": stored_plan["plan_id"],
            "risk_level": stored_plan.get("risk_level"),
            "approval_route": stored_plan.get("approval_route"),
            "total_actions": len(stored_plan.get("borrower_plan", {}).get("immediate_actions", [])) + 
                           len(stored_plan.get("borrower_plan", {}).get("follow_ups", [])),
            "queue_status": stored_plan.get("queue_status"),
            "borrower_plan": stored_plan.get("borrower_plan", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")

@app.get("/api/v1/plans/{plan_id}")
async def get_action_plan_details(plan_id: str):
    """Get action plan details."""
    try:
        if not action_plan_store:
            raise HTTPException(status_code=503, detail="Action plan service not available")
            
        plan = action_plan_store.get_by_id(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        
        return {
            "plan_id": plan_id,
            "borrower_plan": plan.get("borrower_plan", {}),
            "advisor_plan": plan.get("advisor_plan", {}),
            "supervisor_plan": plan.get("supervisor_plan", {}),
            "leadership_plan": plan.get("leadership_plan", {}),
            "risk_level": plan.get("risk_level"),
            "approval_route": plan.get("approval_route"),
            "queue_status": plan.get("queue_status")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plan: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Simple Customer Call Center Analytics Server")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🌐 Server URL: http://0.0.0.0:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )