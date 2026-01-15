"""
Configuration Loader

Task 9: Configuration File Consolidation
Provides centralized access to application configuration.
"""

import json
from pathlib import Path
from typing import Any, Optional, Dict
from functools import lru_cache


class ConfigLoader:
    """
    Centralized configuration loader.
    
    Loads settings from app_config.json and provides easy access.
    Uses caching for performance.
    """
    
    CONFIG_FILE = "app_config.json"
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_path: Optional custom path to config file
        """
        if config_path:
            self._config_path = config_path
        else:
            self._config_path = Path(__file__).parent / self.CONFIG_FILE
        
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.
        
        Args:
            key: Dot-notation key (e.g., "app.version")
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section: Section name (top-level key)
            
        Returns:
            Section dictionary or empty dict
        """
        return self._config.get(section, {})
    
    @property
    def app_name(self) -> str:
        """Get application name."""
        return self.get("app.name", "Jigyokei System")
    
    @property
    def app_version(self) -> str:
        """Get application version."""
        return self.get("app.version", "0.0.0")
    
    @property
    def total_estimated_fields(self) -> int:
        """Get total estimated fields for progress calculation."""
        return self.get("fields.total_estimated_fields", 20)
    
    @property
    def step_thresholds(self) -> Dict[str, int]:
        """Get step progress thresholds."""
        return self.get("fields.step_thresholds", {"output": 75, "audit": 50, "interview": 25})
    
    @property
    def api_settings(self) -> Dict[str, Any]:
        """Get API settings."""
        return self.get_section("api")
    
    @property
    def available_roles(self) -> list:
        """Get available user roles."""
        return self.get("roles.available", ["経営者（事業主）"])
    
    @property
    def available_industries(self) -> list:
        """Get available industry keys."""
        return self.get("industries.available", [])
    
    @property
    def industry_labels(self) -> Dict[str, str]:
        """Get industry key to label mapping."""
        return self.get("industries.labels", {})
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()


# Global cached instance
@lru_cache(maxsize=1)
def get_config() -> ConfigLoader:
    """
    Get the global configuration loader instance.
    
    Uses LRU cache for singleton pattern.
    
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader()


# Convenience functions
def get_app_version() -> str:
    """Get application version string."""
    return get_config().app_version


def get_total_fields() -> int:
    """Get total estimated fields."""
    return get_config().total_estimated_fields


def get_step_thresholds() -> Dict[str, int]:
    """Get step progress thresholds."""
    return get_config().step_thresholds


def get_zipcloud_url() -> str:
    """Get ZipCloud API URL."""
    return get_config().get("api.zipcloud.url", "https://zipcloud.ibsnet.co.jp/api/search")


def get_zipcloud_timeout() -> int:
    """Get ZipCloud API timeout in seconds."""
    return get_config().get("api.zipcloud.timeout_seconds", 3)
