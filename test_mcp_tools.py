#!/usr/bin/env python3
"""Test script to check MCP server tool definitions"""

import requests
import json

# Test the MCP server directly
url = "http://localhost:8001/mcp"

print("🔍 Testing MCP Server Tool Definitions\n")
print(f"Connecting to: {url}\n")

try:
    # Try to get tools via SSE endpoint
    response = requests.get(url)
    print(f"GET /mcp status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type')}")
    print(f"Response: {response.text[:500]}\n")

except Exception as e:
    print(f"❌ Error: {e}")

# Check what FastMCP exposes
print("\n🔧 Checking FastMCP server configuration...")
print("Expected endpoints:")
print("  - GET /mcp (SSE endpoint)")
print("  - POST /mcp/messages/ (JSON-RPC endpoint)")
print("\nThe issue: ChatGPT can connect but doesn't see tools as executable")
print("Likely cause: Tool schemas not properly formatted or missing input schemas")
