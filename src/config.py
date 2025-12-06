"""
Configuration loader for SkylarIQ agent
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    # MCP Server URLs
    atlas_mcp_url: str = "http://localhost:8001"
    common_mcp_url: str = "http://localhost:8002"

    # Agent settings
    agent_name: str = "SkylarIQ"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load agent configuration from YAML file.

    Args:
        config_path: Path to config file (default: ./config.yaml)

    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Substitute environment variables
    config = _substitute_env_vars(config)

    return config


def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively substitute environment variables in config.

    Args:
        config: Configuration dictionary

    Returns:
        Config with substituted values
    """
    if isinstance(config, dict):
        return {k: _substitute_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_substitute_env_vars(item) for item in config]
    elif isinstance(config, str) and config.startswith("${") and config.endswith("}"):
        # Extract environment variable name
        env_var = config[2:-1]
        return os.getenv(env_var, config)
    else:
        return config


def get_settings() -> Settings:
    """
    Get application settings.

    Returns:
        Settings instance
    """
    return Settings()
