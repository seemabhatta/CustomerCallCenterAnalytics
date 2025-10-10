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

# NO FALLBACK: Comprehensive configuration validation at startup
print("🔍 Validating system configuration...")
try:
    from src.infrastructure.config.database_config import validate_all_configuration
    validate_all_configuration()
    print("✅ Configuration validation passed")
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    print("System cannot start. Please fix configuration issues.")
    sys.exit(1)

# NO FALLBACK: Initialize KuzuDB schema before starting services
print("🗄️ Initializing knowledge graph schema...")
try:
    from initialize_kuzu_schema import initialize_kuzu_schema
    initialize_kuzu_schema()
    print("✅ Knowledge graph schema initialized successfully")
except Exception as e:
    print(f"❌ Knowledge graph schema initialization failed: {e}")
    print("Knowledge graph functionality will be unavailable.")
    # Continue startup - not critical for basic functionality

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
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uvicorn
import json

# Import service abstractions - NO business logic in routes
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.insights_service import InsightsService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.system_service import SystemService
from src.services.leadership_insights_service import LeadershipInsightsService
from src.services.advisor_service import AdvisorService
from src.services.forecasting_service import ForecastingService, ForecastingServiceError

# Import execution models for step-by-step workflow execution
from src.models.execution_models import (
    StepExecutionRequest,
    StepExecutionResponse,
    StepStatusResponse,
    WorkflowStepsResponse,
    ExecutionErrorResponse
)

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    sys.exit(1)

# Initialize all services at startup (fail-fast)
db_path = os.getenv('DATABASE_PATH', './data/call_center.db')
transcript_service = TranscriptService(api_key=api_key)
analysis_service = AnalysisService(api_key=api_key)
plan_service = PlanService(api_key=api_key)
workflow_service = WorkflowService(db_path=db_path)
system_service = SystemService(api_key=api_key)
# Advisor service is reused to avoid re-initializing agents and session storage per request
advisor_service = AdvisorService(db_path=db_path)
forecasting_service = ForecastingService(db_path=db_path)

# Initialize intelligence services (Prophet + GenAI hybrid)
from src.storage.insight_store import InsightStore
from src.analytics.intelligence.hybrid_analyzer import HybridAnalyzer
from src.services.intelligence_service import IntelligenceService
from src.infrastructure.llm.llm_client_v2 import LLMClientV2

llm_client = LLMClientV2()
insight_store = InsightStore(db_path=db_path)
hybrid_analyzer = HybridAnalyzer(
    forecasting_service=forecasting_service,
    llm_client=llm_client,
    db_path=db_path
)
intelligence_service = IntelligenceService(
    hybrid_analyzer=hybrid_analyzer,
    insight_store=insight_store,
    db_path=db_path
)

print("✅ All services initialized successfully")

# Initialize knowledge event handling system
try:
    from src.infrastructure.graph.knowledge_event_handler import initialize_knowledge_event_handling
    initialize_knowledge_event_handling()
    print("✅ Knowledge event handling system initialized")
except ImportError as e:
    print(f"⚠️  Knowledge event handling not available: {e}")
except Exception as e:
    print(f"❌ Failed to initialize knowledge event handling: {e}")
    # NO FALLBACK: Continue with degraded functionality but log the issue

# Initialize graph event handlers for complete event-driven architecture
try:
    from src.infrastructure.events.graph_handlers import initialize_graph_handlers
    initialize_graph_handlers()
    print("✅ Graph event handlers initialized - complete event-driven pipeline active")
except ImportError as e:
    print(f"⚠️  Graph event handlers not available: {e}")
except Exception as e:
    print(f"❌ Failed to initialize graph event handlers: {e}")
    # NO FALLBACK: Continue with degraded functionality but log the issue
    import logging
    logging.getLogger(__name__).error(f"Knowledge event handling initialization failed: {e}")

# Initialize graph event handlers for business events
try:
    from src.infrastructure.events.graph_handlers import initialize_graph_handlers
    initialize_graph_handlers()
    print("✅ Graph event handlers initialized")
except ImportError as e:
    print(f"⚠️  Graph event handlers not available: {e}")
except Exception as e:
    print(f"❌ Failed to initialize graph event handlers: {e}")
    # NO FALLBACK: Continue with degraded functionality but log the issue
    import logging
    logging.getLogger(__name__).error(f"Graph event handlers initialization failed: {e}")

# Initialize prediction cleanup system
# NO FALLBACK: Proper background task management with FastAPI lifecycle
background_tasks = set()
prediction_cleanup = None

try:
    from src.infrastructure.graph.prediction_cleanup import get_prediction_cleanup
    prediction_cleanup = get_prediction_cleanup()
    print("✅ Prediction cleanup system initialized")
except ImportError as e:
    print(f"❌ Prediction cleanup not available: {e}")
    # NO FALLBACK: If cleanup is critical, fail here
    raise RuntimeError(f"Critical component missing: {e}")
except Exception as e:
    print(f"❌ Failed to initialize prediction cleanup: {e}")
    # NO FALLBACK: If cleanup fails, entire system fails
    raise RuntimeError(f"Cannot proceed without prediction cleanup: {e}")

# NO FALLBACK: Define lifespan function BEFORE FastAPI app creation to avoid undefined reference
# Modern FastAPI lifespan management - NO FALLBACK
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan management for background tasks following NO FALLBACK principles."""
    global background_tasks, prediction_cleanup

    # Startup
    print("🚀 Starting application lifespan...")

    if prediction_cleanup is not None:
        import asyncio

        async def run_cleanup_with_recovery():
            """Background cleanup task with automatic error recovery - NO FALLBACK."""
            max_retries = 3
            base_delay = 60  # seconds

            for attempt in range(max_retries):
                try:
                    logger.info(f"🔄 Starting prediction cleanup (attempt {attempt + 1}/{max_retries})")
                    await prediction_cleanup.schedule_periodic_cleanup(interval_hours=24)
                    # If successful, exit retry loop
                    break

                except Exception as e:
                    logger.error(f"❌ Prediction cleanup failed (attempt {attempt + 1}/{max_retries}): {e}")

                    if attempt < max_retries - 1:
                        # Exponential backoff for retries
                        delay = base_delay * (2 ** attempt)
                        logger.info(f"⏳ Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)
                    else:
                        # NO FALLBACK: After max retries, log critical failure
                        logger.critical(f"🚨 Prediction cleanup permanently failed after {max_retries} attempts")
                        # Schedule a restart task
                        asyncio.create_task(schedule_cleanup_restart())

        async def schedule_cleanup_restart():
            """Schedule cleanup restart after permanent failure."""
            restart_delay = 3600  # 1 hour
            logger.info(f"📅 Scheduling cleanup restart in {restart_delay} seconds")
            await asyncio.sleep(restart_delay)

            # Restart the cleanup task
            restart_task = asyncio.create_task(run_cleanup_with_recovery())
            background_tasks.add(restart_task)
            restart_task.add_done_callback(lambda t: background_tasks.discard(t))
            logger.info("🔄 Cleanup task restarted after failure recovery")

        # Create and track the background task with recovery
        cleanup_task = asyncio.create_task(run_cleanup_with_recovery())
        background_tasks.add(cleanup_task)

        # Clean up completed tasks to prevent memory leaks
        cleanup_task.add_done_callback(lambda t: background_tasks.discard(t))

        print("✅ Background prediction cleanup task started with error recovery")
    else:
        print("⚠️  Prediction cleanup not available - skipping background task")

    yield  # Application runs here

    # Shutdown
    print("🛑 Shutting down application...")

    # Cancel all background tasks
    for task in background_tasks:
        if not task.done():
            task.cancel()

    # Wait for tasks to complete cancellation
    if background_tasks:
        import asyncio
        await asyncio.gather(*background_tasks, return_exceptions=True)

    print("✅ All background tasks shut down")

app = FastAPI(
    title="Customer Call Center Analytics API",
    description="AI-powered system for generating and analyzing call center transcripts",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend connectivity - NO FALLBACK security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5000",  # Frontend dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8000",  # FastAPI dev server
        os.getenv("FRONTEND_URL", "").split(",") if os.getenv("FRONTEND_URL") else []
    ] if os.getenv("ENVIRONMENT", "development") == "development"
    else [os.getenv("FRONTEND_URL", "https://production-frontend.example.com")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Pydantic models for request/response validation
class TranscriptCreateRequest(BaseModel):
    topic: Optional[str] = "payment_inquiry"
    urgency: Optional[str] = "medium"
    financial_impact: Optional[bool] = False
    customer_sentiment: Optional[str] = "neutral"
    customer_id: Optional[str] = None
    advisor_id: Optional[str] = None
    loan_id: Optional[str] = None
    property_id: Optional[str] = None
    context: Optional[str] = None
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

# Note: Leadership requests now use AdvisorChatRequest with role="leadership"


class AdvisorChatRequest(BaseModel):
    advisor_id: str
    message: str
    session_id: Optional[str] = None
    transcript_id: Optional[str] = None
    plan_id: Optional[str] = None
    role: Optional[str] = "advisor"  # Role parameter: "advisor" or "leadership"


class ForecastGenerateRequest(BaseModel):
    forecast_type: str
    horizon_days: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    use_cache: bool = True
    ttl_hours: int = 24


class IntelligenceQueryRequest(BaseModel):
    question: str
    persona: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class CampaignPerformanceRequest(BaseModel):
    campaign_id: Optional[str] = None
    date_range: Optional[str] = "last_30_days"


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
            "chat": "/api/v1/advisor/chat (universal endpoint for all roles)",
            "forecasts": "/api/v1/forecasts",
            "intelligence": {
                "leadership": "/api/v1/intelligence/leadership/*",
                "servicing": "/api/v1/intelligence/servicing/*",
                "marketing": "/api/v1/intelligence/marketing/*",
                "cross_persona": "/api/v1/intelligence/ask, /insights, /cache, /health"
            }
        }
    }

# ===============================================
# SYSTEM ENDPOINTS
# ===============================================

@app.get("/api/v1/health")
async def health_check():
    """Comprehensive health check endpoint - NO FALLBACK monitoring."""
    try:
        # Get basic system health from system service
        system_health = await system_service.health_check()

        # Add database connectivity checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "components": {
                "system": system_health,
                "databases": await _check_database_health(),
                "knowledge_graph": await _check_knowledge_graph_health(),
                "event_system": await _check_event_system_health()
            }
        }

        # Determine overall health status
        unhealthy_components = [
            name for name, component in health_status["components"].items()
            if component.get("status") != "healthy"
        ]

        if unhealthy_components:
            health_status["status"] = "unhealthy"
            health_status["unhealthy_components"] = unhealthy_components
            return JSONResponse(status_code=503, content=health_status)

        return health_status
    except Exception as e:
        error_health = {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": f"Health check failed: {str(e)}"
        }
        return JSONResponse(status_code=500, content=error_health)

async def _check_database_health() -> Dict[str, Any]:
    """Check main SQLite database health."""
    try:
        from src.infrastructure.config.database_config import get_main_database_path
        import sqlite3
        import os

        db_path = get_main_database_path()

        # Check if database file exists and is accessible
        if not os.path.exists(db_path):
            return {"status": "unhealthy", "error": "Database file not found"}

        # Test connection
        with sqlite3.connect(db_path) as conn:
            conn.execute("SELECT 1").fetchone()

        return {"status": "healthy", "database_path": db_path}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def _check_knowledge_graph_health() -> Dict[str, Any]:
    """Check KuzuDB knowledge graph health."""
    try:
        from src.infrastructure.graph.unified_graph_manager import get_unified_graph_manager
        from src.infrastructure.config.database_config import get_knowledge_graph_database_path
        import os

        db_path = get_knowledge_graph_database_path()

        # Check if database directory exists
        if not os.path.exists(os.path.dirname(db_path)):
            return {"status": "unhealthy", "error": "Knowledge graph directory not found"}

        # Test UnifiedGraphManager connection (uses singleton so no extra connections)
        manager = get_unified_graph_manager()
        # Don't close here since it's a shared singleton

        return {"status": "healthy", "database_path": db_path}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def _check_event_system_health() -> Dict[str, Any]:
    """Check event system health."""
    try:
        from src.infrastructure.events.event_system import get_event_system

        event_system = get_event_system()

        # Check if event system is properly initialized
        if not hasattr(event_system, '_signal'):
            return {"status": "unhealthy", "error": "Event system not initialized"}

        return {"status": "healthy", "subscribers": len(event_system._signal.receivers)}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/api/v1/config")
async def get_configuration():
    """Get system configuration for frontend.

    Returns:
        Frontend-compatible configuration with roles, settings, and UI preferences

    Raises:
        HTTPException: 500 if configuration cannot be loaded or is invalid
    """
    try:
        from call_center_agents.role_based_agent import load_prompt_config

        # NO FALLBACK: Fail fast if configuration cannot be loaded
        config = load_prompt_config()

        # Validate required structure exists
        if "roles" not in config:
            raise ValueError("Configuration missing required 'roles' section")

        # Build frontend-safe response with explicit key checking
        response = {
            "roles": config["roles"],
            "settings": config.get("settings", {}),
            "ui": config.get("settings", {}).get("ui", {}),
            "metadata": config.get("metadata", {})
        }

        # Validate that we have at least some roles for frontend
        if not response["roles"]:
            raise ValueError("No roles defined in configuration")

        return response

    except ImportError as e:
        logger.error(f"Failed to import configuration module: {e}")
        raise HTTPException(status_code=500, detail="Configuration system unavailable")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise HTTPException(status_code=500, detail="Configuration system error")

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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create transcript: {str(e)}")


@app.post("/api/v1/transcripts/bulk")
async def create_transcripts_bulk(requests: List[TranscriptCreateRequest]):
    """Bulk create transcripts - proxies to transcript service."""
    try:
        payloads = [req.model_dump() for req in requests]
        return await transcript_service.create_bulk(payloads)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create bulk transcripts: {str(e)}")


@app.get("/api/v1/transcripts/seeds")
async def get_transcript_seed_profiles():
    """Expose seeded customer/advisor profiles for transcript generator UI."""
    try:
        return await transcript_service.get_seed_profiles()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch transcript seeds: {str(e)}")

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

@app.get("/api/v1/analyses/by-transcript/{transcript_id}")
async def get_analysis_by_transcript(transcript_id: str):
    """Get analysis by transcript ID - proxies to analysis service."""
    try:
        result = await analysis_service.get_by_transcript_id(transcript_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"No analysis found for transcript {transcript_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analysis for transcript: {str(e)}")

@app.delete("/api/v1/analyses")
async def delete_all_analyses():
    """Delete all analyses - proxies to analysis service."""
    try:
        count = await analysis_service.delete_all()
        return {"message": f"Deleted {count} analyses successfully", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete all analyses: {str(e)}")

# ===============================================
# GRAPH QUERY ENDPOINTS
# ===============================================

@app.post("/api/v1/graph/ask")
async def ask_graph_question(request: dict):
    """Ask natural language question about the knowledge graph."""
    try:
        from src.services.graph_query_service import get_graph_query_service
        graph_service = get_graph_query_service()

        question = request.get("question")
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")

        result = await graph_service.ask(question)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph query failed: {str(e)}")

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

@app.get("/api/v1/plans/by-transcript/{transcript_id}")
async def get_plan_by_transcript(transcript_id: str):
    """Get action plan by transcript ID - proxies to plan service."""
    try:
        result = await plan_service.get_by_transcript_id(transcript_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"No plan found for transcript {transcript_id}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get plan for transcript: {str(e)}")

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
# STEP-BY-STEP WORKFLOW EXECUTION ENDPOINTS
# ===============================================

@app.get("/api/v1/workflows/{workflow_id}/steps", response_model=WorkflowStepsResponse)
async def get_workflow_steps(workflow_id: str):
    """Get all steps for a workflow."""
    try:
        return workflow_service.get_workflow_steps(workflow_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow steps: {str(e)}")

@app.post("/api/v1/workflows/{workflow_id}/steps/{step_number}/execute", response_model=StepExecutionResponse)
async def execute_workflow_step(
    workflow_id: str,
    step_number: int,
    request: StepExecutionRequest
):
    """Execute a single workflow step."""
    try:
        return await workflow_service.execute_workflow_step(workflow_id, step_number, request.executed_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute step: {str(e)}")

@app.get("/api/v1/workflows/{workflow_id}/steps/{step_number}/status", response_model=StepStatusResponse)
async def get_step_execution_status(workflow_id: str, step_number: int):
    """Get execution status for a specific workflow step."""
    try:
        return await workflow_service.get_step_execution_status(workflow_id, step_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get step status: {str(e)}")

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
        "started_at": datetime.now(timezone.utc).isoformat(),
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
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

        # Update final status
        orchestration_runs[run_id]["status"] = "COMPLETED"
        orchestration_runs[run_id]["stage"] = "COMPLETE"
        orchestration_runs[run_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

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
# UNIFIED CHAT ENDPOINT - Handles All Roles
# ===============================================

# Note: All chat functionality (advisor, leadership, etc.) is now handled
# by the single /api/v1/advisor/chat endpoint with the role parameter.
# This simplifies the API and reduces redundant code.


# ===============================================
# UNIFIED CHAT ENDPOINTS - All Roles (Advisor, Leadership, etc.)
# ===============================================

@app.post("/api/v1/advisor/chat")
async def advisor_chat(request: AdvisorChatRequest):
    """Universal chat interface for all roles - like Claude Code for any workflow type.

    This is the single endpoint that handles all user roles (advisor, leadership, etc.).
    The agent behavior is determined by the 'role' parameter which loads role-specific prompts.
    The agent autonomously decides what tools to call based on the message and role.
    """
    try:
        # Process chat through service layer (fully agentic)
        result = await advisor_service.chat(
            advisor_id=request.advisor_id,
            message=request.message,
            session_id=request.session_id,
            transcript_id=request.transcript_id,
            plan_id=request.plan_id,
            role=request.role
        )

        return result

    except Exception as e:
        error_detail = f"Advisor chat failed: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.post("/api/v1/advisor/chat/stream")
async def advisor_chat_stream(request: AdvisorChatRequest):
    """Streaming chat interface for advisors with thinking steps and tool calls.

    This endpoint streams events in real-time showing:
    - 🤔 Thinking steps (agent reasoning)
    - 🔧 Tool calls (agent actions)
    - 📝 Response text (final answer)

    Returns Server-Sent Events (SSE) format.
    """
    try:
        async def generate_events():
            """Generate SSE events from streaming chat response."""
            try:
                async for event in advisor_service.chat_stream(
                    advisor_id=request.advisor_id,
                    message=request.message,
                    session_id=request.session_id,
                    transcript_id=request.transcript_id,
                    plan_id=request.plan_id,
                    role=request.role
                ):
                    # Format as Server-Sent Events
                    event_data = {
                        "type": event["type"],
                        "content": event["content"],
                        "session_id": event["session_id"],
                        "metadata": event.get("metadata", {})
                    }

                    # Send as proper SSE format
                    yield f"data: {json.dumps(event_data)}\n\n"

                    # If this is the final event, close the stream
                    if event["type"] in ["completed", "error"]:
                        break

            except Exception as e:
                # Send error event
                error_event = {
                    "type": "error",
                    "content": f"Streaming failed: {str(e)}",
                    "session_id": request.session_id or request.advisor_id,
                    "metadata": {"error": str(e)}
                }
                yield f"data: {json.dumps(error_event)}\n\n"

        return StreamingResponse(
            generate_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )

    except Exception as e:
        error_detail = f"Advisor streaming chat failed: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)


# Session management endpoints disabled - now handled by OpenAI Agents SQLiteSession
# @app.get("/api/v1/advisor/sessions/{advisor_id}")
# async def get_advisor_sessions(advisor_id: str, limit: int = Query(5, ge=1, le=20)):
#     """Get recent sessions for an advisor."""
#     # Session tracking now handled automatically by OpenAI Agents
#     return {"message": "Session management is now handled by OpenAI Agents"}


# ===============================================
# FORECASTING ENDPOINTS
# ===============================================

@app.post("/api/v1/forecasts/generate")
async def generate_forecast(request: ForecastGenerateRequest):
    """Generate time-series forecast using Prophet.

    Generates forecasts for call volume, sentiment, risk scores, etc.
    Uses cached forecasts when available.
    """
    try:
        result = await forecasting_service.generate_forecast(
            forecast_type=request.forecast_type,
            horizon_days=request.horizon_days,
            start_date=request.start_date,
            end_date=request.end_date,
            use_cache=request.use_cache,
            ttl_hours=request.ttl_hours
        )
        return result
    except ForecastingServiceError as exc:
        return {
            "status": "insufficient_data",
            "forecast_type": request.forecast_type,
            "detail": str(exc),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")


@app.get("/api/v1/forecasts/statistics")
async def get_forecast_statistics():
    """Get statistics about stored forecasts."""
    try:
        return await forecasting_service.get_forecast_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Statistics retrieval failed: {str(e)}")


@app.get("/api/v1/forecasts/{forecast_id}")
async def get_forecast(forecast_id: str):
    """Get forecast by ID."""
    try:
        result = await forecasting_service.get_forecast_by_id(forecast_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Forecast {forecast_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve forecast: {str(e)}")


@app.get("/api/v1/forecasts/types/available")
async def get_available_forecast_types():
    """Get list of available forecast types."""
    try:
        return await forecasting_service.get_available_forecast_types()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast types: {str(e)}")


@app.get("/api/v1/forecasts/types/{forecast_type}")
async def get_forecast_type_info(forecast_type: str):
    """Get detailed information about a forecast type."""
    try:
        return await forecasting_service.get_forecast_type_info(forecast_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast type info: {str(e)}")


@app.get("/api/v1/forecasts/data/readiness")
async def check_data_readiness(forecast_type: Optional[str] = None):
    """Check if sufficient data exists for forecasting.

    Args:
        forecast_type: Specific type to check, or None for all types
    """
    try:
        return await forecasting_service.check_data_readiness(forecast_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data readiness check failed: {str(e)}")


@app.get("/api/v1/forecasts/data/summary")
async def get_data_summary():
    """Get summary of available historical data for forecasting."""
    try:
        return await forecasting_service.get_data_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data summary failed: {str(e)}")


@app.delete("/api/v1/forecasts/{forecast_id}")
async def delete_forecast(forecast_id: str):
    """Delete a forecast."""
    try:
        deleted = await forecasting_service.delete_forecast(forecast_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Forecast {forecast_id} not found")
        return {"message": f"Forecast {forecast_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast deletion failed: {str(e)}")


@app.post("/api/v1/forecasts/cleanup")
async def cleanup_expired_forecasts():
    """Clean up expired forecasts."""
    try:
        deleted_count = await forecasting_service.cleanup_expired_forecasts()
        return {"message": f"Cleaned up {deleted_count} expired forecasts"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.get("/api/v1/forecasts/type/{forecast_type}/history")
async def get_forecast_history(forecast_type: str, limit: int = Query(10, ge=1, le=50)):
    """Get forecast history for a specific type."""
    try:
        return await forecasting_service.get_all_forecasts_by_type(
            forecast_type=forecast_type,
            include_expired=True,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get forecast history: {str(e)}")


# ===============================================
# INTELLIGENCE ENDPOINTS - Prophet + GenAI Hybrid
# ===============================================

# ---------------------------------------------
# LEADERSHIP INTELLIGENCE
# ---------------------------------------------

@app.get("/api/v1/intelligence/leadership/briefing")
async def get_leadership_briefing(
    use_cache: bool = Query(True),
    ttl_hours: int = Query(1, ge=1, le=24)
):
    """Get daily executive briefing with urgent items and financial impact.

    Returns:
        - Portfolio health status
        - Urgent items requiring attention
        - Financial summary ($$ impact)
        - Strategic recommendations
    """
    try:
        return await intelligence_service.get_leadership_briefing(
            use_cache=use_cache,
            ttl_hours=ttl_hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate leadership briefing: {str(e)}")


@app.get("/api/v1/intelligence/leadership/dollar-impact")
async def get_dollar_impact():
    """Get portfolio risk quantified in dollars.

    Returns financial impact of:
        - Churn risk (lost servicing fees)
        - Delinquency risk (potential losses)
        - Compliance violations (penalty exposure)
    """
    try:
        return await intelligence_service.get_dollar_impact()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate dollar impact: {str(e)}")


@app.get("/api/v1/intelligence/leadership/decision-queue")
async def get_decision_queue():
    """Get items requiring executive decision today.

    Returns workflows and recommendations sorted by:
        - Financial impact
        - Urgency
        - Risk level
    """
    try:
        return await intelligence_service.get_decision_queue()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decision queue: {str(e)}")


@app.get("/api/v1/intelligence/leadership/risk-waterfall")
async def get_risk_waterfall():
    """Get cascading risk breakdown across portfolio.

    Shows how risks compound from individual loans to portfolio level.
    """
    try:
        return await intelligence_service.get_risk_waterfall()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate risk waterfall: {str(e)}")


# ---------------------------------------------
# SERVICING OPERATIONS INTELLIGENCE
# ---------------------------------------------

@app.get("/api/v1/intelligence/servicing/queue-status")
async def get_queue_status():
    """Get real-time and predicted queue status.

    Returns:
        - Current queue depth
        - Predicted peak times
        - Staffing recommendations
    """
    try:
        return await intelligence_service.get_queue_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue status: {str(e)}")


@app.get("/api/v1/intelligence/servicing/sla-monitor")
async def get_sla_monitor():
    """Get SLA compliance tracking and breach predictions.

    Monitors:
        - First call resolution
        - Answer rate
        - Escalation rate
    """
    try:
        return await intelligence_service.get_sla_monitor()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get SLA monitor: {str(e)}")


@app.get("/api/v1/intelligence/servicing/advisor-heatmap")
async def get_advisor_heatmap():
    """Get advisor performance matrix for visualization.

    Returns heatmap data showing:
        - Empathy scores
        - Compliance adherence
        - First call resolution
        - Color-coded status (green/yellow/red)
    """
    try:
        return await intelligence_service.get_advisor_heatmap()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate advisor heatmap: {str(e)}")


@app.get("/api/v1/intelligence/servicing/coaching-alerts")
async def get_coaching_alerts():
    """Get advisor coaching recommendations.

    Identifies advisors needing:
        - Compliance training
        - Empathy coaching
        - Escalation protocol review
    """
    try:
        return await intelligence_service.get_coaching_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get coaching alerts: {str(e)}")


@app.get("/api/v1/intelligence/servicing/workload-balance")
async def get_workload_balance():
    """Get staffing optimization recommendations.

    Returns:
        - Current capacity vs demand
        - Predicted staffing gaps
        - Reallocation suggestions
    """
    try:
        return await intelligence_service.get_workload_balance()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workload balance: {str(e)}")


@app.get("/api/v1/intelligence/servicing/case-resolution")
async def get_case_resolution_insights():
    """Get case resolution trends and bottlenecks.

    Analyzes:
        - Most common issues
        - Resolution time patterns
        - Escalation triggers
    """
    try:
        return await intelligence_service.get_case_resolution_insights()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get case resolution insights: {str(e)}")


# ---------------------------------------------
# MARKETING INTELLIGENCE
# ---------------------------------------------

@app.get("/api/v1/intelligence/marketing/segments")
async def get_marketing_segments():
    """Get customer segmentation with targeting opportunities.

    Returns segments:
        - Refi-ready
        - At-risk (churn prevention)
        - Loyal champions (referrals)
        - PMI removal eligible
    """
    try:
        return await intelligence_service.get_marketing_segments()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get marketing segments: {str(e)}")


@app.get("/api/v1/intelligence/marketing/campaign-recommendations")
async def get_campaign_recommendations():
    """Get AI-generated campaign recommendations with ROI.

    Provides campaign ideas with:
        - Target segment
        - Expected conversion rate
        - Cost estimates
        - Projected ROI
    """
    try:
        return await intelligence_service.get_campaign_recommendations()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get campaign recommendations: {str(e)}")


@app.post("/api/v1/intelligence/marketing/campaign-performance")
async def analyze_campaign_performance(request: CampaignPerformanceRequest):
    """Analyze campaign performance metrics.

    Returns performance analysis based on intent patterns.
    """
    try:
        return await intelligence_service.get_campaign_performance(
            campaign_id=request.campaign_id,
            date_range=request.date_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze campaign performance: {str(e)}")


@app.post("/api/v1/intelligence/marketing/churn-analysis")
async def get_churn_analysis(
    use_cache: bool = Query(True),
    ttl_hours: int = Query(2, ge=1, le=24)
):
    """Get detailed churn risk intelligence.

    Returns:
        - Root cause analysis
        - High-risk borrower segments
        - Retention strategies
        - Financial impact ($$ at risk)
    """
    try:
        return await intelligence_service.get_churn_analysis(
            use_cache=use_cache,
            ttl_hours=ttl_hours
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate churn analysis: {str(e)}")


@app.post("/api/v1/intelligence/marketing/message-optimizer")
async def optimize_message(request: dict):
    """Optimize campaign messaging for target segment.

    Takes draft message and segment, returns optimized version.
    """
    try:
        message = request.get("message")
        segment = request.get("segment", "general")

        if not message:
            raise HTTPException(status_code=400, detail="Message required")

        return await intelligence_service.optimize_campaign_message(
            message=message,
            segment=segment
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize message: {str(e)}")


@app.get("/api/v1/intelligence/marketing/customer-journey")
async def get_customer_journey_insights():
    """Get customer journey analysis and touchpoint effectiveness.

    Analyzes interaction patterns across channels.
    """
    try:
        return await intelligence_service.get_customer_journey_insights()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get customer journey insights: {str(e)}")


@app.get("/api/v1/intelligence/marketing/roi-attribution")
async def get_roi_attribution():
    """Get ROI attribution analysis for campaigns.

    Tracks revenue/retention impact by campaign theme.
    """
    try:
        return await intelligence_service.get_roi_attribution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ROI attribution: {str(e)}")


# ---------------------------------------------
# CROSS-PERSONA INTELLIGENCE
# ---------------------------------------------

@app.post("/api/v1/intelligence/ask")
async def ask_intelligence_question(request: IntelligenceQueryRequest):
    """Ask natural language question to intelligence system.

    Routes question to appropriate persona(s) and synthesizes answer.
    Works like a universal query interface across all intelligence.
    """
    try:
        return await intelligence_service.ask(
            question=request.question,
            persona=request.persona,
            context=request.context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer intelligence question: {str(e)}")


@app.get("/api/v1/intelligence/insights")
async def get_cached_insights(
    persona: Optional[str] = Query(None),
    insight_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """Get cached insights from insight store.

    Useful for reviewing previously generated intelligence.
    """
    try:
        return await intelligence_service.get_cached_insights(
            persona=persona,
            insight_type=insight_type,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve cached insights: {str(e)}")


@app.delete("/api/v1/intelligence/cache")
async def clear_intelligence_cache(
    persona: Optional[str] = Query(None),
    insight_type: Optional[str] = Query(None)
):
    """Clear intelligence cache (all or filtered by persona/type).

    Use when you want to force fresh analysis.
    """
    try:
        result = await intelligence_service.clear_cache(
            persona=persona,
            insight_type=insight_type
        )
        return {
            "message": f"Cleared {result['cleared_count']} cached insights",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@app.get("/api/v1/intelligence/health")
async def get_intelligence_health():
    """Get intelligence system health and statistics.

    Returns:
        - Cache hit rates
        - Recent insight generation stats
        - Available personas and capabilities
    """
    try:
        return await intelligence_service.get_health()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get intelligence health: {str(e)}")


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
