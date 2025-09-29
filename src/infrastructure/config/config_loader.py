"""
Configuration Loader - Centralized configuration management
Loads configuration from config/system.yaml with fallbacks to environment variables
"""
import yaml
import os
from typing import Any, Dict, Optional
from pathlib import Path

class ConfigLoader:
    """Singleton configuration loader"""
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent.parent.parent.parent / "config" / "system.yaml"

        try:
            with open(config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}, using defaults")
            self._config = {}
        except yaml.YAMLError as e:
            print(f"Error parsing config YAML: {e}")
            self._config = {}

    def get(self, key_path: str, default: Any = None, env_fallback: Optional[str] = None) -> Any:
        """
        Get configuration value using dot notation

        Args:
            key_path: Dot-separated path (e.g., 'analysis.risk_threshold_prediction_creation')
            default: Default value if key not found
            env_fallback: Environment variable to check as fallback

        Returns:
            Configuration value
        """
        # Check environment variable first if provided
        if env_fallback and env_fallback in os.environ:
            value = os.environ[env_fallback]
            # Try to convert to appropriate type
            try:
                if value.lower() in ('true', 'false'):
                    return value.lower() == 'true'
                if '.' in value:
                    return float(value)
                return int(value)
            except ValueError:
                return value

        # Navigate through nested dictionary
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

# Global configuration instance
_config = ConfigLoader()

# Helper functions for common configuration values
def get_risk_threshold() -> float:
    """Get risk threshold for prediction creation"""
    return _config.get('analysis.risk_threshold_prediction_creation', 0.3, 'RISK_THRESHOLD_PREDICTION_CREATION')

def get_default_confidence() -> float:
    """Get default confidence score"""
    return _config.get('analysis.default_confidence_score', 0.8, 'DEFAULT_CONFIDENCE_SCORE')

def get_default_satisfaction() -> float:
    """Get default satisfaction score"""
    return _config.get('analysis.default_satisfaction_score', 0.7, 'DEFAULT_SATISFACTION_SCORE')

def get_pattern_strength() -> float:
    """Get pattern link strength"""
    return _config.get('analysis.pattern_link_strength', 0.8, 'PATTERN_LINK_STRENGTH')

def get_default_risk_score() -> float:
    """Get default risk score"""
    return _config.get('analysis.default_risk_score', 0.5, 'DEFAULT_RISK_SCORE')

def get_temperature(agent_type: str) -> float:
    """Get temperature for specific agent type"""
    return _config.get(f'temperature.{agent_type}', 0.2, f'TEMPERATURE_{agent_type.upper()}')

def get_default_effectiveness_score() -> float:
    """Get default effectiveness score"""
    return _config.get('analysis.default_effectiveness_score', 0.8)

def get_default_customer_rating() -> float:
    """Get default customer rating"""
    return _config.get('analysis.default_customer_rating', 4.0)

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature flag is enabled"""
    return _config.get(f'features.{feature_name}', True)

def get_learning_threshold(node_type: str) -> float:
    """Get confidence threshold for learning node types"""
    return _config.get(f'learning.confidence_thresholds.{node_type}', 0.6)

def is_learning_enabled(learning_type: str) -> bool:
    """Check if a learning feature is enabled"""
    return _config.get(f'learning.{learning_type}', True)

def get_prediction_config(key: str, default=None):
    """Get prediction system configuration"""
    return _config.get(f'predictions.{key}', default)

def get_agent_config_value(agent_name: str, config_key: str, default=None):
    """Get specific configuration value for an agent"""
    return _config.get(f'agents.{agent_name}.{config_key}', default)