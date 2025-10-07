"""
MCP (Model Context Protocol) Server Infrastructure

Provides ChatGPT integration via MCP protocol, exposing
Customer Call Center Analytics tools for natural language interaction.
"""

from .mcp_server import start_mcp_server

__all__ = ['start_mcp_server']
