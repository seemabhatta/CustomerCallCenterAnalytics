#!/usr/bin/env python3
"""
MCP Server Runner for Customer Call Center Analytics
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.mcp_server import run_mcp_server

if __name__ == "__main__":
    print("🚀 Starting MCP Server for Customer Call Center Analytics...")
    print("📡 Server will be available at: http://localhost:8000")
    print("🔧 MCP endpoint: http://localhost:8000/mcp")
    print("\n📚 Available Tools:")
    print("  • generate_transcripts - Generate realistic call transcripts")
    print("  • analyze_transcript - Analyze transcripts for insights")
    print("  • search_transcripts - Search through call data")
    print("  • list_transcripts - List recent transcripts")
    print("  • plan_mode - Create actionable plans")
    print("  • execute_mode - Execute plans with integrations")
    print("  • get_system_status - Get system status\n")
    
    try:
        run_mcp_server()
    except KeyboardInterrupt:
        print("\n👋 MCP Server stopped")