import yaml
import os
from pathlib import Path
from typing import Dict, Any
from ..models.config_models import LegalConfig
from dotenv import load_dotenv

load_dotenv()


def load_config(config_path: str = "src/config/legal_config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file with environment variable substitution"""

    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as f:
        config_content = f.read()

    # Replace environment variables
    config_content = _substitute_env_vars(config_content)

    # Parse YAML
    config = yaml.safe_load(config_content)

    return config


def _substitute_env_vars(content: str) -> str:
    """Substitute environment variables in config content"""
    import re

    def replace_env_var(match):
        var_name = match.group(1)
        res = os.getenv(var_name, f"${{{var_name}}}")  # Keep original if not found
        return res

    # Replace ${VAR_NAME} patterns
    return re.sub(r"\$\{([^}]+)\}", replace_env_var, content)


def get_database_config(config: Dict[str, Any], db_type: str) -> Dict[str, Any]:
    """Get specific database configuration"""
    return config.get("databases", {}).get(db_type, {})


def get_llm_config(config: Dict[str, Any], provider: str = "openai") -> Dict[str, Any]:
    """Get LLM configuration for specific provider"""
    return config.get("llm", {}).get(provider, {})
