"""
Universal Call Center Analytics - MCP Server

Complete analytics suite with all 26 tools for admin/power users.
This is the main MCP server running on port 8001.

For focused persona-specific apps, see:
- src/infrastructure/mcp/apps/advisor_borrower_server.py (port 8002)
- src/infrastructure/mcp/apps/advisor_performance_server.py (port 8003)
- src/infrastructure/mcp/apps/leadership_portfolio_server.py (port 8004)
- src/infrastructure/mcp/apps/leadership_strategy_server.py (port 8005)

Port: 8001
Tools: 26 (all tools)
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

from src.infrastructure.mcp.shared.app_factory import create_single_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import uvicorn

    # Create universal app using factory
    app_name = "universal"
    mcp, port, config = create_single_app(app_name)

    # Create HTTP app with CORS
    app = mcp.streamable_http_app()

    try:
        from starlette.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
            allow_credentials=False,
        )
    except Exception:
        pass

    # Startup info
    logger.info("=" * 70)
    logger.info(f"🚀 {config['name']}")
    logger.info("=" * 70)
    logger.info(f"📝 {config['description']}")
    logger.info(f"🌐 Server: http://0.0.0.0:{port}")
    logger.info(f"📡 SSE endpoint: http://0.0.0.0:{port}/mcp")
    logger.info(f"💬 Messages endpoint: http://0.0.0.0:{port}/mcp/messages")
    logger.info(f"🔧 Tools: {len(config['tools'])}")
    logger.info("=" * 70)
    logger.info("WORKFLOW: Transcript → Analysis → Plan → Workflows → Steps → Execute")
    logger.info("ORCHESTRATION: Complete end-to-end pipeline automation")
    logger.info("=" * 70)
    logger.info("🎯 USE CASE: Complete analytics suite for all users")
    logger.info("🔑 KEYWORDS: admin, system wide, all tools, power users")
    logger.info("=" * 70)
    logger.info("")
    logger.info("💡 TIP: For focused apps, use:")
    logger.info("   - Port 8002: Advisor Borrower Assistant")
    logger.info("   - Port 8003: Advisor Performance Coach")
    logger.info("   - Port 8004: Leadership Portfolio Manager")
    logger.info("   - Port 8005: Leadership Strategy Advisor")
    logger.info("=" * 70)

    # Run server
    uvicorn.run(
        "src.infrastructure.mcp.mcp_server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
