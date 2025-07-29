#!/usr/bin/env python3
"""
Configuration module for the Demo MCP Server.

This module provides configuration management for the demo template,
including environment variable mapping, validation, and support for
double underscore notation from CLI arguments.
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
    provides defaults, validates settings, and supports double underscore
    notation for nested configuration override.
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

        # Process any double underscore configurations passed from CLI
        self._process_nested_config()

        # Validate configuration
        self._validate_config()
        self.logger.info("Demo server configuration loaded")
        self.template_data = self._load_template()
        self.logger.debug("Template data loaded")

    def _validate_config(self) -> None:
        """Validate configuration values."""
        valid_log_levels = ["debug", "info", "warn", "warning", "error", "critical"]
        if self.log_level.lower() not in valid_log_levels:
            self.logger.warning("Invalid log level '%s', using 'info'", self.log_level)
            self.log_level = "info"

    def _process_nested_config(self) -> None:
        """
        Process double underscore notation in configuration.
        """
        processed_config = {}

        for key, value in self.config_dict.items():
            if "__" in key:
                processed_key, processed_value = self._process_double_underscore_key(
                    key, value
                )
                if processed_key:
                    processed_config[processed_key] = processed_value
            else:
                # Keep non-nested configurations as-is
                processed_config[key] = value

        # Update config_dict with processed configurations
        self.config_dict.update(processed_config)

    def _process_double_underscore_key(
        self, key: str, value: Any
    ) -> tuple[Optional[str], Any]:
        """
        Process a single double underscore key.

        Returns:
            Tuple of (processed_key, value) or (None, value) if no processing needed
        """
        parts = key.split("__")

        if len(parts) == 2:
            return self._handle_two_part_key(parts, value)
        elif len(parts) > 2:
            return self._handle_multi_part_key(parts, value)

        return key, value

    def _handle_two_part_key(self, parts: list[str], value: Any) -> tuple[str, Any]:
        """Handle two-part keys like demo__hello_from."""
        prefix, config_key = parts

        # Handle template-level overrides
        if prefix.lower() in ["demo", "template"]:
            self.logger.debug("Processed template override: %s = %s", config_key, value)
            return config_key, value

        # Handle transport configuration
        elif prefix.lower() == "transport":
            self.logger.debug("Processed transport config: %s = %s", config_key, value)
            # Note: Transport config handling would need additional logic in caller
            return f"transport_{config_key}", value

        # Handle nested configuration for custom properties
        else:
            nested_key = f"{prefix}_{config_key}"
            self.logger.debug("Processed nested config: %s = %s", nested_key, value)
            return nested_key, value

    def _handle_multi_part_key(self, parts: list[str], value: Any) -> tuple[str, Any]:
        """Handle multi-part keys like category__subcategory__property."""
        nested_key = "_".join(parts[1:])  # Join all parts except first
        self.logger.debug("Processed deep nested config: %s = %s", nested_key, value)
        return nested_key, value

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

    def get_template_data(self) -> Dict[str, Any]:
        """
        Get the full template data, potentially modified by double underscore notation.

        This allows double underscore CLI arguments to override ANY part of the
        template structure, not just config_schema values.

        Examples:
        - --name="Custom Server" -> modifies template_data["name"]
        - --tools__0__custom_field="value" -> adds custom_field to first tool
        - --description="New desc" -> modifies template_data["description"]

        Returns:
            Template data dictionary with any double underscore overrides applied
        """
        # Start with base template data
        template_data = self.template_data.copy()

        # Apply any template-level overrides from double underscore notation
        for key, value in self.config_dict.items():
            if "__" in key:
                # Apply nested override to template data
                self._apply_nested_override(template_data, key, value)
            elif key not in self.get_template_config():
                # Direct template-level override (not in config_schema)
                template_data[key] = value
                self.logger.debug("Applied template override: %s = %s", key, value)

        return template_data

    def _apply_nested_override(
        self, data: Dict[str, Any], key: str, value: Any
    ) -> None:
        """
        Apply a nested override using double underscore notation.

        Args:
            data: Dictionary to modify
            key: Double underscore key (e.g., "tools__0__custom_field")
            value: Value to set
        """
        parts = key.split("__")
        current = data

        # Navigate to the nested location
        for part in parts[:-1]:
            current = self._navigate_to_nested_key(current, part)
            if current is None:
                return

        # Set the final value
        self._set_final_value(current, parts[-1], value)
        self.logger.debug("Applied nested override: %s = %s", key, value)

    def _navigate_to_nested_key(self, current: Any, part: str) -> Any:
        """Navigate to a nested key, handling both list indices and object keys."""
        if part.isdigit():
            return self._handle_list_index(current, int(part))
        else:
            return self._handle_object_key(current, part)

    def _handle_list_index(self, current: Any, index: int) -> Any:
        """Handle navigation to a list index."""
        if not isinstance(current, list):
            self.logger.warning("Trying to index non-list with %s", index)
            return None
        # Extend list if necessary
        while len(current) <= index:
            current.append({})
        return current[index]

    def _handle_object_key(self, current: Any, key: str) -> Any:
        """Handle navigation to an object key."""
        if key not in current:
            current[key] = {}
        return current[key]

    def _set_final_value(self, current: Any, final_key: str, value: Any) -> None:
        """Set the final value in the nested structure."""
        if final_key.isdigit() and isinstance(current, list):
            index = int(final_key)
            while len(current) <= index:
                current.append({})
            current[index] = value
        else:
            current[final_key] = value
