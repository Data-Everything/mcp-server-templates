#!/usr/bin/env python3
"""
Configuration module for the Demo MCP Server.

This module provides configuration management for the demo template,
including environment variable mapping and validation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional


class DemoServerConfig:
    """
    Configuration class for the Demo MCP Server.

    Handles configuration loading from environment variables,
    provides defaults, and validates settings.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize demo server configuration.

        Args:
            config_dict: Optional configuration dictionary to override defaults
        """

        self.config_dict = config_dict or {}
        self.log_level = None
        self.logger = self._setup_logger()
        # Validate configuration
        self._validate_config()
        self.logger.info("Demo server configuration loaded")
        self.template_data = self._load_template()
        self.logger.debug("Template data loaded")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for configuration."""
        logger = logging.getLogger(__name__)

        # Set initial log level from environment or default
        initial_log_level = os.getenv("MCP_LOG_LEVEL", "info").upper()
        logger.setLevel(getattr(logging, initial_log_level, logging.INFO))
        self.log_level = initial_log_level.lower()

        return logger

    def _get_config(self, key: str, env_var: str, default: Any) -> Any:
        """
        Get configuration value with precedence handling.

        Args:
            key: Configuration key in config_dict
            env_var: Environment variable name
            default: Default value if not found

        Returns:
            Configuration value
        """
        # Check config_dict first
        if key in self.config_dict:
            self.logger.debug(
                "Using config_dict value for '%s': %s", key, self.config_dict[key]
            )
            return self.config_dict[key]

        # Check environment variable
        env_value = os.getenv(env_var)
        if env_value is not None:
            self.logger.debug("Using environment variable '%s': %s", env_var, env_value)
            return env_value

        # Return default
        self.logger.debug("Using default value for '%s': %s", key, default)
        return default

    def _load_template(self, template_path: str = None) -> Dict[str, Any]:
        """
        Load template data from a JSON file.

        Args:
            template_path: Path to the template JSON file

        Returns:
            Parsed template data as dictionary
        """

        if not template_path:
            template_path = Path(__file__).parent / "template.json"

        with open(template_path, mode="r", encoding="utf-8") as template_file:
            return json.load(template_file)

    def get_template_config(self, template_path: str = None) -> Dict[str, Any]:
        """
        Get configuration properties from the template.

        Args:
            template_path: Path to the template JSON file

        Returns:
            Dictionary containing template configuration properties
        """

        if template_path:
            template_data = self._load_template(template_path)
        else:
            template_data = self._load_template()

        properties_dict = {}
        properties = template_data.get("config_schema", {}).get("properties", {})
        for key, value in properties.items():
            # Load default values from environment or template
            env_var = value.get("env_mapping", key.upper())
            default_value = value.get("default", None)
            properties_dict[key] = self._get_config(key, env_var, default_value)

        return properties_dict

    def _validate_config(self) -> None:
        """Validate configuration values."""
        valid_log_levels = ["debug", "info", "warn", "warning", "error", "critical"]
        if self.log_level.lower() not in valid_log_levels:
            self.logger.warning("Invalid log level '%s', using 'info'", self.log_level)
            self.log_level = "info"
