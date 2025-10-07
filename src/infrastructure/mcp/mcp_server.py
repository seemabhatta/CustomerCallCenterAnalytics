"""
MCP Server for Customer Call Center Analytics

FastMCP-based server that exposes mortgage call center analytics tools
to ChatGPT via Model Context Protocol (MCP).

Architecture:
- Runs on port 8001 (separate from main API on 8000)
- SSE endpoint: GET /mcp for ChatGPT streaming
- HTTP endpoint: POST /mcp/messages for tool calls
- Reuses existing service layer (NO duplication)
- NO FALLBACK: Fails fast on errors

Usage:
    python src/infrastructure/mcp/mcp_server.py
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import existing services
from src.services.transcript_service import TranscriptService
from src.services.analysis_service import AnalysisService
from src.services.plan_service import PlanService
from src.services.workflow_service import WorkflowService
from src.services.system_service import SystemService

# Import MCP components
from src.infrastructure.mcp.tool_definitions import get_all_tool_definitions
from src.infrastructure.mcp.tool_handlers import MCPToolHandlers

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================================
# MCP SERVER SETUP
# ========================================

def create_mcp_app() -> FastAPI:
    """Create FastAPI app for MCP server - NO FALLBACK."""

    # Validate configuration
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not found in environment")
        sys.exit(1)

    # Initialize services (reuse from main server)
    db_path = os.getenv('DATABASE_PATH', './data/call_center.db')

    logger.info("🔧 Initializing MCP services...")
    transcript_service = TranscriptService(api_key=api_key)
    analysis_service = AnalysisService(api_key=api_key)
    plan_service = PlanService(api_key=api_key)
    workflow_service = WorkflowService(db_path=db_path)
    system_service = SystemService(api_key=api_key)
    logger.info("✅ MCP services initialized")

    # Initialize tool handlers
    tool_handlers = MCPToolHandlers(
        transcript_service=transcript_service,
        analysis_service=analysis_service,
        plan_service=plan_service,
        workflow_service=workflow_service,
        system_service=system_service
    )

    # Create FastAPI app
    app = FastAPI(
        title="MCP Server - Customer Call Center Analytics",
        description="Model Context Protocol server for ChatGPT integration",
        version="1.0.0"
    )

    # Add CORS for ChatGPT
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # ChatGPT can connect from various origins
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ========================================
    # MCP PROTOCOL ENDPOINTS
    # ========================================

    @app.get("/")
    async def root():
        """Root endpoint with MCP server info."""
        return {
            "service": "MCP Server - Customer Call Center Analytics",
            "status": "running",
            "protocol": "Model Context Protocol",
            "version": "1.0.0",
            "tools_count": len(get_all_tool_definitions()),
            "endpoints": {
                "tools": "/tools",
                "execute": "/execute"
            }
        }

    @app.get("/tools")
    async def list_tools():
        """List all available MCP tools."""
        tools = get_all_tool_definitions()
        return {
            "tools": tools,
            "count": len(tools)
        }

    @app.post("/execute")
    async def execute_tool(request: dict):
        """Execute a tool call from ChatGPT.

        Request format:
        {
            "tool": "tool_name",
            "params": {...}
        }
        """
        tool_name = request.get("tool")
        params = request.get("params", {})

        if not tool_name:
            return {
                "success": False,
                "error": "Tool name required"
            }

        try:
            logger.info(f"🔧 Executing tool: {tool_name}")
            result = await tool_handlers.handle_tool_call(tool_name, params)
            logger.info(f"✅ Tool '{tool_name}' executed successfully")
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
        except Exception as e:
            logger.error(f"❌ Tool '{tool_name}' failed: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "MCP Server",
            "tools_available": len(get_all_tool_definitions())
        }

    return app


def start_mcp_server(host: str = "0.0.0.0", port: int = 8001):
    """Start the MCP server - NO FALLBACK."""
    logger.info("🚀 Starting MCP Server for Customer Call Center Analytics")
    logger.info(f"🌐 Server URL: http://{host}:{port}")
    logger.info(f"📚 Tools: http://{host}:{port}/tools")
    logger.info(f"🔧 Execute: http://{host}:{port}/execute")
    logger.info("=" * 60)

    app = create_mcp_app()

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


# ========================================
# MAIN ENTRY POINT
# ========================================

if __name__ == "__main__":
    start_mcp_server()
