#!/usr/bin/env python3
"""
Configuration module for the Demo MCP Server.

This module provides configuration management for the demo template,
including environment variable mapping and validation.
"""

import logging
import os
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
        self.logger = self._setup_logger()

        # Load configuration with precedence: config_dict > env > defaults
        self.hello_from = self._get_config(
            "hello_from", "MCP_HELLO_FROM", "MCP Platform"
        )
        self.log_level = self._get_config("log_level", "MCP_LOG_LEVEL", "info")

        # Validate configuration
        self._validate_config()

        self.logger.info("Demo server configuration loaded")
        self.logger.debug(
            "Configuration: hello_from=%s, log_level=%s",
            self.hello_from,
            self.log_level,
        )

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for configuration."""
        logger = logging.getLogger(__name__)

        # Set initial log level from environment or default
        initial_log_level = os.getenv("MCP_LOG_LEVEL", "info").upper()
        logger.setLevel(getattr(logging, initial_log_level, logging.INFO))

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
            return self.config_dict[key]

        # Check environment variable
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value

        # Return default
        return default

    def _validate_config(self) -> None:
        """Validate configuration values."""
        valid_log_levels = ["debug", "info", "warn", "warning", "error", "critical"]
        if self.log_level.lower() not in valid_log_levels:
            self.logger.warning("Invalid log level '%s', using 'info'", self.log_level)
            self.log_level = "info"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return {"hello_from": self.hello_from, "log_level": self.log_level}

    def get_env_mappings(self) -> Dict[str, str]:
        """
        Get environment variable mappings for CLI help.

        Returns:
            Dictionary mapping config keys to environment variables
        """
        return {"hello_from": "MCP_HELLO_FROM", "log_level": "MCP_LOG_LEVEL"}
