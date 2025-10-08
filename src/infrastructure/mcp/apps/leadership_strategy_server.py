"""
Leadership Strategy Advisor - MCP Server

Strategic insights and system optimization for leadership:
- Execution statistics and success rates
- Pipeline performance
- Optimization opportunities
- Strategic insights

Port: 8005
Tools: 7 (metrics, orchestration tracking, analysis)
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

APP_NAME = "leadership_strategy"
mcp, PORT, CONFIG = create_single_app(APP_NAME)
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


def _log_startup_details() -> None:
    logger.info("=" * 70)
    logger.info(f"🚀 {CONFIG['name']}")
    logger.info("=" * 70)
    logger.info(f"📝 {CONFIG['description']}")
    logger.info(f"🌐 Server: http://0.0.0.0:{PORT}")
    logger.info(f"📡 SSE endpoint: http://0.0.0.0:{PORT}/mcp")
    logger.info(f"💬 Messages endpoint: http://0.0.0.0:{PORT}/mcp/messages")
    logger.info(f"🔧 Tools: {len(CONFIG['tools'])}")
    logger.info("=" * 70)
    logger.info("🎯 USE CASE: Strategic insights and system optimization")
    logger.info("🔑 KEYWORDS: performance, statistics, optimization, analytics")
    logger.info("=" * 70)


_log_startup_details()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        reload=False,
    )
