"""
Tool Registry for YAML-driven tool configuration.
Loads tool configuration from YAML and provides tools for role-based agents.
Follows core principles: agentic, no fallback logic, fail-fast.
"""
import yaml
import os
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

# Configuration cache
_config_cache: Optional[Dict[str, Any]] = None


def _clear_cache():
    """Clear configuration cache (for testing)."""
    global _config_cache
    _config_cache = None


def get_tool_config(config_path: str = "config/prompt_mapping.yaml") -> Dict[str, Any]:
    """Load tool configuration from YAML file with caching.

    Args:
        config_path: Path to configuration YAML file

    Returns:
        Configuration dictionary with roles and tool_registry

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If config is missing required sections
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None:
        return _config_cache

    # Check if file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    # Load and parse YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in configuration file: {e}")

    # Validate required structure
    if 'roles' not in config:
        raise ValueError("Configuration missing 'roles' section")

    # Cache and return
    _config_cache = config
    return config


def get_tools_for_role_mode(
    role: str,
    mode: str,
    config_path: str = "config/prompt_mapping.yaml"
) -> List[str]:
    """Get list of tool names for a specific role+mode combination.

    Args:
        role: Role identifier (e.g., 'advisor', 'leadership')
        mode: Mode identifier (e.g., 'borrower', 'selfreflection')
        config_path: Path to configuration file

    Returns:
        List of tool names for this role+mode

    Raises:
        ValueError: If role or mode not found in configuration
    """
    config = get_tool_config(config_path)

    # Validate role exists
    if role not in config['roles']:
        available_roles = list(config['roles'].keys())
        raise ValueError(f"Role '{role}' not found. Available roles: {available_roles}")

    role_config = config['roles'][role]

    # Validate mode exists
    if 'modes' not in role_config or mode not in role_config['modes']:
        available_modes = list(role_config.get('modes', {}).keys())
        raise ValueError(f"Mode '{mode}' not found for role '{role}'. Available modes: {available_modes}")

    mode_config = role_config['modes'][mode]

    # Get tools list (may be empty)
    tools = mode_config.get('tools', [])
    return tools


def get_tool_filters(
    role: str,
    mode: str,
    config_path: str = "config/prompt_mapping.yaml"
) -> Dict[str, Any]:
    """Get tool filters for a specific role+mode combination.

    Tool filters define access control rules like workflow_types, access_level, etc.

    Args:
        role: Role identifier
        mode: Mode identifier
        config_path: Path to configuration file

    Returns:
        Dictionary of tool filters, or empty dict if none defined

    Raises:
        ValueError: If role or mode not found
    """
    config = get_tool_config(config_path)

    # Validate role and mode exist
    if role not in config['roles']:
        available_roles = list(config['roles'].keys())
        raise ValueError(f"Role '{role}' not found. Available roles: {available_roles}")

    role_config = config['roles'][role]

    if 'modes' not in role_config or mode not in role_config['modes']:
        available_modes = list(role_config.get('modes', {}).keys())
        raise ValueError(f"Mode '{mode}' not found for role '{role}'. Available modes: {available_modes}")

    mode_config = role_config['modes'][mode]

    # Get tool_filters (may be empty)
    filters = mode_config.get('tool_filters', {})
    return filters


def resolve_tools_to_functions(
    tool_names: List[str],
    tool_function_map: Dict[str, Callable]
) -> List[Callable]:
    """Resolve tool names to actual function objects.

    Args:
        tool_names: List of tool names from configuration
        tool_function_map: Dictionary mapping tool names to functions

    Returns:
        List of callable function objects

    Raises:
        ValueError: If a tool name is not found in the function map
    """
    functions = []

    for tool_name in tool_names:
        if tool_name not in tool_function_map:
            available_tools = list(tool_function_map.keys())
            raise ValueError(
                f"Unknown tool: {tool_name}. Available tools: {available_tools}"
            )
        functions.append(tool_function_map[tool_name])

    return functions


def get_agent_tool_config(
    role: str,
    mode: str,
    config_path: str = "config/prompt_mapping.yaml",
    tool_function_map: Optional[Dict[str, Callable]] = None
) -> Dict[str, Any]:
    """Get complete tool configuration for agent creation.

    This is the main entry point for agent creation - provides everything needed.

    Args:
        role: Role identifier
        mode: Mode identifier
        config_path: Path to configuration file
        tool_function_map: Dictionary mapping tool names to functions

    Returns:
        Dictionary with:
        - tool_names: List of tool names
        - tool_functions: List of callable functions (if tool_function_map provided)
        - tool_filters: Dictionary of access control filters

    Raises:
        ValueError: If role or mode not found, or tool resolution fails
    """
    # Get tool names
    tool_names = get_tools_for_role_mode(role, mode, config_path)

    # Get tool filters
    tool_filters = get_tool_filters(role, mode, config_path)

    # Build result
    result = {
        'tool_names': tool_names,
        'tool_filters': tool_filters
    }

    # Resolve to functions if map provided
    if tool_function_map is not None:
        result['tool_functions'] = resolve_tools_to_functions(tool_names, tool_function_map)
    else:
        result['tool_functions'] = []

    return result


def get_tool_metadata(
    tool_name: str,
    config_path: str = "config/prompt_mapping.yaml"
) -> Dict[str, Any]:
    """Get metadata for a specific tool from the tool registry.

    Args:
        tool_name: Name of the tool
        config_path: Path to configuration file

    Returns:
        Tool metadata including description, category, parameters

    Raises:
        ValueError: If tool not found in registry
    """
    config = get_tool_config(config_path)

    if 'tool_registry' not in config:
        return {}

    tool_registry = config['tool_registry']

    if tool_name not in tool_registry:
        available_tools = list(tool_registry.keys())
        raise ValueError(
            f"Tool '{tool_name}' not found in registry. Available tools: {available_tools}"
        )

    return tool_registry[tool_name]


def validate_tool_config(config_path: str = "config/prompt_mapping.yaml") -> bool:
    """Validate tool configuration file.

    Checks:
    - File exists and is valid YAML
    - Has required 'roles' section
    - All tool names referenced in roles exist in tool_registry
    - No duplicate tool definitions

    Args:
        config_path: Path to configuration file

    Returns:
        True if valid

    Raises:
        ValueError: If validation fails with specific error message
    """
    config = get_tool_config(config_path)

    # Get all tools referenced in roles
    referenced_tools = set()
    for role_name, role_config in config['roles'].items():
        for mode_name, mode_config in role_config.get('modes', {}).items():
            tools = mode_config.get('tools', [])
            referenced_tools.update(tools)

    # Get all tools defined in registry
    registry_tools = set(config.get('tool_registry', {}).keys())

    # Check for tools referenced but not defined
    undefined_tools = referenced_tools - registry_tools
    if undefined_tools:
        raise ValueError(
            f"Tools referenced but not defined in tool_registry: {sorted(undefined_tools)}"
        )

    # Check for tools defined but never used
    unused_tools = registry_tools - referenced_tools
    if unused_tools:
        # This is a warning, not an error - tools can be defined for future use
        import logging
        logging.warning(f"Tools defined but not used: {sorted(unused_tools)}")

    return True
