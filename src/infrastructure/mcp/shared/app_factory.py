"""
MCP App Factory

Creates configured FastMCP app instances based on mcp_apps_config.yaml.
Each app gets a filtered tool set, custom metadata, and shared HTTP client.
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List
from copy import deepcopy
import httpx

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from src.infrastructure.mcp.tool_definitions import get_all_tool_definitions
from src.infrastructure.mcp.shared.tool_handlers import HANDLER_REGISTRY, create_http_client


logger = logging.getLogger(__name__)


def load_app_config(config_path: str = "config/mcp_apps_config.yaml") -> Dict[str, Any]:
    """Load MCP apps configuration from YAML file."""
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)

    return config


def validate_app_config(app_name: str, app_config: Dict[str, Any], all_tools: List[str]) -> None:
    """Validate app configuration against available tools."""
    required_fields = ['name', 'description', 'port', 'tools']

    for field in required_fields:
        if field not in app_config:
            raise ValueError(f"App '{app_name}' missing required field: {field}")

    # Validate tools exist
    configured_tools = app_config['tools']
    invalid_tools = [t for t in configured_tools if t not in all_tools]

    if invalid_tools:
        raise ValueError(f"App '{app_name}' references invalid tools: {invalid_tools}")

    # Validate prompt file if specified
    if app_config.get('prompt_file'):
        prompt_path = Path(app_config['prompt_file'])
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found for app '{app_name}': {prompt_path}")

    logger.info(f"✅ App '{app_name}' configuration validated ({len(configured_tools)} tools)")


def create_mcp_app(
    app_name: str,
    app_config: Dict[str, Any],
    http_client: httpx.AsyncClient
) -> FastMCP:
    """
    Create a FastMCP app instance with filtered tools.

    Args:
        app_name: Internal app identifier (e.g., 'advisor_borrower')
        app_config: App configuration from YAML
        http_client: Shared HTTP client for backend calls

    Returns:
        Configured FastMCP instance
    """
    # Get all available tool definitions
    all_tool_defs = {defn['name']: defn for defn in get_all_tool_definitions()}

    # Filter tools for this app
    app_tool_names = app_config['tools']
    app_tool_defs = [all_tool_defs[name] for name in app_tool_names if name in all_tool_defs]

    logger.info(f"🏗️  Creating MCP app '{app_name}' with {len(app_tool_defs)} tools")

    # Create FastMCP instance
    mcp = FastMCP(
        name=app_config['name'],
        sse_path="/mcp",
        message_path="/mcp/messages",
        stateless_http=True
    )

    # Helper to create Tool from definition
    def _tool_from_definition(definition: Dict[str, Any]) -> types.Tool:
        """Construct a FastMCP tool from canonical definition data."""
        return types.Tool(
            name=definition["name"],
            title=definition["title"],
            description=definition["description"],
            inputSchema=deepcopy(definition["input_schema"]),
            _meta=deepcopy(definition.get("_meta")),
        )

    # Register list_tools handler (returns filtered tools)
    @mcp._mcp_server.list_tools()
    async def _list_tools() -> List[types.Tool]:
        """Return filtered tool list for this app."""
        return [_tool_from_definition(defn) for defn in app_tool_defs]

    # Register resources handler (empty - we only use tools)
    @mcp._mcp_server.list_resources()
    async def _list_resources() -> List[types.Resource]:
        """Return empty list - we don't use resources, only tools."""
        return []

    # Register call_tool handler (routes to shared handlers)
    async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
        """Handle tool execution requests."""
        tool_name = req.params.name
        arguments = req.params.arguments or {}

        logger.info(f"🔧 [{app_name}] Tool called: {tool_name} with args: {arguments}")

        try:
            # Check if tool is allowed for this app
            if tool_name not in app_tool_names:
                raise ValueError(f"Tool '{tool_name}' not available in app '{app_name}'")

            # Route to shared handler
            if tool_name not in HANDLER_REGISTRY:
                raise ValueError(f"No handler registered for tool: {tool_name}")

            handler = HANDLER_REGISTRY[tool_name]
            result = await handler(http_client, arguments)

            return types.ServerResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=result,
                    )
                ]
            )

        except Exception as e:
            error_message = f"❌ Error executing {tool_name}: {str(e)}"
            logger.error(f"[{app_name}] {error_message}")

            return types.ServerResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=error_message,
                    )
                ],
                isError=True,
            )

    # Register the handler
    mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request

    logger.info(f"✅ MCP app '{app_name}' created successfully")

    return mcp


def create_all_apps(config_path: str = "config/mcp_apps_config.yaml") -> Dict[str, tuple]:
    """
    Create all MCP apps defined in config.

    Returns:
        Dict mapping app_name to (mcp_instance, port, app_config)
    """
    # Load config
    config = load_app_config(config_path)
    apps_config = config.get('apps', {})
    settings = config.get('settings', {})

    # Get API base URL
    api_base_url = settings.get('api_base_url', os.getenv('API_BASE_URL', 'http://localhost:8000'))
    http_timeout = settings.get('http_timeout', 30.0)

    logger.info(f"🔧 API base URL: {api_base_url}")
    logger.info(f"🔧 HTTP timeout: {http_timeout}s")

    # Create shared HTTP client
    http_client = create_http_client(api_base_url, http_timeout)
    logger.info("✅ Shared HTTP client created")

    # Get all available tool names for validation
    all_tool_names = [defn['name'] for defn in get_all_tool_definitions()]
    logger.info(f"📚 Total available tools: {len(all_tool_names)}")

    # Create each app
    apps = {}
    for app_name, app_config in apps_config.items():
        try:
            # Validate config
            validate_app_config(app_name, app_config, all_tool_names)

            # Create app
            mcp_instance = create_mcp_app(app_name, app_config, http_client)
            port = app_config['port']

            apps[app_name] = (mcp_instance, port, app_config)

            logger.info(f"✅ App '{app_name}' ready on port {port}")

        except Exception as e:
            logger.error(f"❌ Failed to create app '{app_name}': {e}")
            if settings.get('validation', {}).get('fail_on_missing_tools', True):
                raise

    logger.info(f"🎉 Created {len(apps)} MCP apps successfully")

    return apps


def create_single_app(
    app_name: str,
    config_path: str = "config/mcp_apps_config.yaml"
) -> tuple:
    """
    Create a single MCP app by name.

    Args:
        app_name: Name of app to create (e.g., 'advisor_borrower')
        config_path: Path to config file

    Returns:
        Tuple of (mcp_instance, port, app_config)
    """
    # Load config
    config = load_app_config(config_path)
    apps_config = config.get('apps', {})

    if app_name not in apps_config:
        raise ValueError(f"App '{app_name}' not found in config. Available: {list(apps_config.keys())}")

    app_config = apps_config[app_name]
    settings = config.get('settings', {})

    # Get API base URL
    api_base_url = settings.get('api_base_url', os.getenv('API_BASE_URL', 'http://localhost:8000'))
    http_timeout = settings.get('http_timeout', 30.0)

    # Create HTTP client
    http_client = create_http_client(api_base_url, http_timeout)

    # Validate
    all_tool_names = [defn['name'] for defn in get_all_tool_definitions()]
    validate_app_config(app_name, app_config, all_tool_names)

    # Create app
    mcp_instance = create_mcp_app(app_name, app_config, http_client)
    port = app_config['port']

    return (mcp_instance, port, app_config)
