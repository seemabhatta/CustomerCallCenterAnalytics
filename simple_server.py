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

# Load environment variables from Replit secrets
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

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