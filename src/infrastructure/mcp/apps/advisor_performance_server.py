"""
Advisor Performance Coach - MCP Server

Personal performance review and coaching for mortgage advisors:
- Call handling analysis
- Customer satisfaction tracking
- Improvement opportunities
- Self-reflection

Port: 8003
Tools: 5 (transcripts, analysis, metrics)
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from src.infrastructure.mcp.shared.app_factory import create_single_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    import uvicorn

    # Create app using factory
    app_name = "advisor_performance"
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
    logger.info("🎯 USE CASE: Personal performance review and coaching")
    logger.info("🔑 KEYWORDS: my performance, self review, improvement, feedback")
    logger.info("=" * 70)

    # Run server
    uvicorn.run(
        "src.infrastructure.mcp.apps.advisor_performance_server:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
