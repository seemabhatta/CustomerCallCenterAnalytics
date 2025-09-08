#!/usr/bin/env python3
"""
Customer Call Center Analytics - FastAPI
Example showing how the same business logic can be exposed as REST API.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the SAME pure business logic classes used by CLI
from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore


# Pydantic models for API requests/responses
class GenerateRequest(BaseModel):
    """Request model for generating transcripts."""
    scenario: Optional[str] = Field(None, description="Conversation scenario")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    sentiment: Optional[str] = Field(None, description="Customer sentiment")
    urgency: Optional[str] = Field(None, description="Urgency level")
    
    # Allow any additional dynamic parameters
    class Config:
        extra = "allow"
        schema_extra = {
            "example": {
                "scenario": "PMI Removal",
                "customer_id": "CUST_123",
                "sentiment": "hopeful"
            }
        }


class TranscriptResponse(BaseModel):
    """Response model for transcript data."""
    id: str
    timestamp: str
    messages: List[Dict[str, Any]]
    # Dynamic attributes are included as dict


class BatchGenerateRequest(BaseModel):
    """Request model for generating multiple transcripts."""
    count: int = Field(ge=1, le=10, description="Number of transcripts to generate")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for generation")


class SearchResponse(BaseModel):
    """Response model for search results."""
    count: int
    transcripts: List[TranscriptResponse]


class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_transcripts: int
    total_messages: int
    unique_customers: int
    avg_messages_per_transcript: float
    top_topics: Dict[str, int]
    sentiments: Dict[str, int]


# Initialize FastAPI app
app = FastAPI(
    title="Customer Call Center Analytics API",
    description="REST API for generating and managing call center transcripts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Initialize business logic (same classes used by CLI!)
def init_system():
    """Initialize the business logic components."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="OPENAI_API_KEY not configured"
        )
    
    generator = TranscriptGenerator(api_key=api_key)
    
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    store = TranscriptStore("data/call_center.db")
    return generator, store


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Customer Call Center Analytics API",
        "version": "1.0.0",
        "description": "Generate and manage call center transcripts",
        "endpoints": {
            "docs": "/docs",
            "generate": "/generate",
            "transcripts": "/transcripts",
            "search": "/transcripts/search",
            "stats": "/stats"
        }
    }


@app.post("/generate", response_model=TranscriptResponse)
async def generate_transcript(request: GenerateRequest):
    """Generate a new transcript."""
    try:
        generator, store = init_system()
        
        # Convert request to dict for dynamic parameter passing
        params = request.dict(exclude_none=True, exclude_unset=True)
        
        # Use the same business logic as CLI!
        transcript = generator.generate(**params)
        
        return TranscriptResponse(
            id=transcript.id,
            timestamp=getattr(transcript, 'timestamp', ''),
            messages=[msg.to_dict() for msg in transcript.messages]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@app.post("/generate/batch", response_model=List[TranscriptResponse])
async def generate_batch(request: BatchGenerateRequest):
    """Generate multiple transcripts."""
    try:
        generator, store = init_system()
        
        # Use the same business logic as CLI!
        transcripts = generator.generate_batch(request.count, **request.params)
        
        return [
            TranscriptResponse(
                id=t.id,
                timestamp=getattr(t, 'timestamp', ''),
                messages=[msg.to_dict() for msg in t.messages]
            )
            for t in transcripts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")


@app.get("/transcripts", response_model=List[TranscriptResponse])
async def list_transcripts(limit: int = Query(100, ge=1, le=1000)):
    """List all transcripts."""
    try:
        _, store = init_system()
        
        # Use the same business logic as CLI!
        transcripts = store.get_all()[:limit]
        
        return [
            TranscriptResponse(
                id=t.id,
                timestamp=getattr(t, 'timestamp', ''),
                messages=[msg.to_dict() for msg in t.messages]
            )
            for t in transcripts
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list transcripts: {str(e)}")


@app.get("/transcripts/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(transcript_id: str):
    """Get a specific transcript by ID."""
    try:
        _, store = init_system()
        
        # Use the same business logic as CLI!
        transcript = store.get_by_id(transcript_id)
        
        if not transcript:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return TranscriptResponse(
            id=transcript.id,
            timestamp=getattr(transcript, 'timestamp', ''),
            messages=[msg.to_dict() for msg in transcript.messages]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")


@app.delete("/transcripts/{transcript_id}")
async def delete_transcript(transcript_id: str):
    """Delete a transcript."""
    try:
        _, store = init_system()
        
        # Use the same business logic as CLI!
        result = store.delete(transcript_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Transcript not found")
        
        return {"message": f"Deleted transcript {transcript_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete transcript: {str(e)}")


@app.get("/transcripts/search", response_model=SearchResponse)
async def search_transcripts(
    customer: Optional[str] = Query(None, description="Search by customer ID"),
    topic: Optional[str] = Query(None, description="Search by topic"),
    text: Optional[str] = Query(None, description="Search by text content")
):
    """Search transcripts."""
    if not any([customer, topic, text]):
        raise HTTPException(
            status_code=400, 
            detail="Please provide at least one search parameter: customer, topic, or text"
        )
    
    try:
        _, store = init_system()
        
        # Use the same business logic as CLI!
        if customer:
            results = store.search_by_customer(customer)
        elif topic:
            results = store.search_by_topic(topic)
        elif text:
            results = store.search_by_text(text)
        else:
            results = []
        
        return SearchResponse(
            count=len(results),
            transcripts=[
                TranscriptResponse(
                    id=t.id,
                    timestamp=getattr(t, 'timestamp', ''),
                    messages=[msg.to_dict() for msg in t.messages]
                )
                for t in results
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get database statistics."""
    try:
        _, store = init_system()
        
        # Use the same business logic as CLI!
        transcripts = store.get_all()
        
        if not transcripts:
            return StatsResponse(
                total_transcripts=0,
                total_messages=0,
                unique_customers=0,
                avg_messages_per_transcript=0.0,
                top_topics={},
                sentiments={}
            )
        
        total = len(transcripts)
        total_messages = sum(len(t.messages) for t in transcripts)
        
        # Collect statistics
        customers = set()
        topics = {}
        sentiments = {}
        
        for transcript in transcripts:
            # Customer IDs
            if hasattr(transcript, 'customer_id'):
                customers.add(transcript.customer_id)
            
            # Topics/scenarios
            topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown'))
            topics[topic] = topics.get(topic, 0) + 1
            
            # Sentiments
            sentiment = getattr(transcript, 'sentiment', 'Unknown')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
        
        return StatsResponse(
            total_transcripts=total,
            total_messages=total_messages,
            unique_customers=len(customers),
            avg_messages_per_transcript=total_messages/total,
            top_topics=dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]),
            sentiments=sentiments
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")


@app.post("/transcripts/{transcript_id}/store")
async def store_transcript(transcript_id: str):
    """Store a transcript in the database (for generated transcripts not yet stored)."""
    # This would be used if transcripts are generated but not immediately stored
    raise HTTPException(status_code=501, detail="Not implemented - transcripts are stored automatically")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        _, store = init_system()
        store.get_all()  # Simple database query
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        )


# Example usage and documentation
if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Customer Call Center Analytics API")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative docs: http://localhost:8000/redoc")
    print("")
    print("Example API calls:")
    print("curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{\"scenario\":\"PMI Removal\"}'")
    print("curl http://localhost:8000/transcripts")
    print("curl http://localhost:8000/stats")
    print("")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)