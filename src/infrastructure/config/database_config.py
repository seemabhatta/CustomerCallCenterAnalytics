"""
Centralized Database Configuration - NO FALLBACK.

Provides consistent database paths across all components.
"""
import os
from typing import Optional


def get_main_database_path() -> str:
    """Get the main SQLite database path - NO FALLBACK."""
    path = os.getenv('DATABASE_PATH', 'data/call_center.db')
    if not path:
        raise ValueError("DATABASE_PATH environment variable not set - NO FALLBACK")
    return path


def get_knowledge_graph_database_path() -> str:
    """Get the KuzuDB knowledge graph database path - NO FALLBACK."""
    path = os.getenv('KNOWLEDGE_DB_PATH', 'data/knowledge_graph_v2.db')
    if not path:
        raise ValueError("KNOWLEDGE_DB_PATH environment variable not set - NO FALLBACK")
    return path


def validate_database_paths() -> None:
    """Validate that all required database paths are accessible - NO FALLBACK."""
    import os
    from pathlib import Path

    # Get all database paths
    main_db_path = get_main_database_path()
    knowledge_db_path = get_knowledge_graph_database_path()

    # Validate paths don't conflict
    if main_db_path == knowledge_db_path:
        raise ValueError(f"Database paths conflict: both use {main_db_path}")

    # Ensure parent directories exist and are writable
    for db_path in [main_db_path, knowledge_db_path]:
        parent_dir = Path(db_path).parent

        # Create directory if it doesn't exist
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise RuntimeError(f"Cannot create database directory {parent_dir}: {e}")

        # Verify directory is writable
        if not os.access(parent_dir, os.W_OK):
            raise PermissionError(f"Database directory {parent_dir} is not writable")

        # Log database configuration
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Database path validated: {db_path}")


def validate_environment_variables() -> None:
    """Validate all required environment variables - NO FALLBACK."""
    import os

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API key for LLM operations',
        'TEMPERATURE_ANALYSIS': 'Temperature setting for analysis operations'
    }

    missing_vars = []
    invalid_vars = []

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)

        if not value:
            missing_vars.append(f"{var_name} ({description})")
        elif var_name == 'TEMPERATURE_ANALYSIS':
            try:
                temp = float(value)
                if not (0.0 <= temp <= 2.0):
                    invalid_vars.append(f"{var_name}={value} (must be between 0.0 and 2.0)")
            except ValueError:
                invalid_vars.append(f"{var_name}={value} (must be a valid float)")

    # NO FALLBACK: If any required environment variables are missing/invalid, fail fast
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

    if invalid_vars:
        raise ValueError(f"Invalid environment variables: {', '.join(invalid_vars)}")

    import logging
    logger = logging.getLogger(__name__)
    logger.info("✅ All environment variables validated")


def validate_system_dependencies() -> None:
    """Validate system dependencies are available - NO FALLBACK."""
    import importlib
    import logging

    logger = logging.getLogger(__name__)

    # Critical dependencies that must be available
    critical_deps = {
        'kuzu': 'KuzuDB for knowledge graph operations',
        'openai': 'OpenAI API client',
        'fastapi': 'FastAPI web framework',
        'pydantic': 'Data validation',
        'blinker': 'Event system'
    }

    missing_deps = []

    for dep_name, description in critical_deps.items():
        try:
            importlib.import_module(dep_name)
            logger.debug(f"✅ {dep_name} available")
        except ImportError:
            missing_deps.append(f"{dep_name} ({description})")

    # NO FALLBACK: If critical dependencies are missing, fail fast
    if missing_deps:
        raise ImportError(f"Missing critical dependencies: {', '.join(missing_deps)}")

    logger.info("✅ All system dependencies validated")


class DatabaseConfig:
    """Database configuration constants."""

    @property
    def main_db_path(self) -> str:
        """Main SQLite database path."""
        return get_main_database_path()

    @property
    def knowledge_db_path(self) -> str:
        """Knowledge graph database path."""
        return get_knowledge_graph_database_path()


# Global configuration instance
_config = None

def validate_all_configuration() -> None:
    """Comprehensive configuration validation - NO FALLBACK."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("🔍 Starting comprehensive configuration validation...")

    try:
        # Step 1: Validate system dependencies
        validate_system_dependencies()

        # Step 2: Validate environment variables
        validate_environment_variables()

        # Step 3: Validate database configuration
        validate_database_paths()

        logger.info("✅ All configuration validation passed")

    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        # NO FALLBACK: Configuration failures prevent system startup
        raise RuntimeError(f"System cannot start due to configuration issues: {e}")


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance."""
    global _config
    if _config is None:
        # Validate configuration before creating instance
        validate_all_configuration()
        _config = DatabaseConfig()
    return _config