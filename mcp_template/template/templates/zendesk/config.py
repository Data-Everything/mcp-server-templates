#!/usr/bin/env python3
"""
Configuration module for the Zendesk MCP Server.

This module provides configuration management for the Zendesk template,
including environment variable mapping, validation, and support for
double underscore notation from CLI arguments.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


class ZendeskServerConfig:
    """
    Configuration class for the Zendesk MCP Server.

    Handles configuration loading from environment variables,
    provides defaults, validates settings, and supports double underscore
    notation for nested configuration override.
    """

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """
        Initialize Zendesk server configuration.

        Args:
            config_dict: Optional configuration dictionary to override defaults
        """
        self.config_dict = config_dict or {}
        self.log_level = None
        self.logger = self._setup_logger()

        # Load template data first so we can use it for type coercion
        self.template_data = self._load_template()
        self.logger.debug("Template data loaded")

        # Load override environment variables from deployer
        self._load_override_env_vars()

        # Process any double underscore configurations passed from CLI
        self._process_nested_config()

        self.logger.info("Zendesk server configuration loaded")

    def _setup_logger(self) -> logging.Logger:
        """Set up and configure logging for the configuration manager."""
        # Get log level from config_dict first, then env var, then default
        log_level = (
            self.config_dict.get("log_level")
            or os.getenv("MCP_LOG_LEVEL", "info").upper()
        )
        self.log_level = log_level

        logger = logging.getLogger(__name__)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # Only add handler if it doesn't exist
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_template(self) -> Dict[str, Any]:
        """Load the template.json file."""
        template_path = Path(__file__).parent / "template.json"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)
            self.logger.debug("Template loaded from %s", template_path)
            return template_data
        except Exception as e:
            self.logger.error("Failed to load template.json: %s", e)
            return {}

    def _load_override_env_vars(self):
        """Load environment variables for config overrides."""
        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for key, schema in properties.items():
            env_var = schema.get("env_mapping")
            if env_var and env_var in os.environ:
                env_value = os.environ[env_var]

                # Type coercion based on schema
                schema_type = schema.get("type", "string")
                try:
                    if schema_type == "integer":
                        env_value = int(env_value)
                    elif schema_type == "boolean":
                        env_value = env_value.lower() in ("true", "1", "yes", "on")
                    elif schema_type == "array":
                        # Simple comma-separated array support
                        env_value = [item.strip() for item in env_value.split(",")]
                except (ValueError, AttributeError) as e:
                    self.logger.warning(
                        "Failed to convert env var %s: %s, using string value",
                        env_var,
                        e,
                    )

                # Only set if not already in config_dict
                if key not in self.config_dict:
                    self.config_dict[key] = env_value
                    self.logger.debug("Loaded %s from env var %s", key, env_var)

    def _process_nested_config(self):
        """Process double underscore notation for nested configuration."""
        # This will be applied to template_data, not config_dict
        # Look for keys with double underscores and convert to nested structure
        nested_updates = {}

        for key, value in self.config_dict.items():
            if "__" in key:
                # Split by double underscore and create nested structure
                parts = key.split("__")
                current = nested_updates

                for part in parts[:-1]:
                    # Handle array indices
                    if part.isdigit():
                        part = int(part)
                        if not isinstance(current, list):
                            # Convert to list if needed
                            current = []
                        # Extend list if necessary
                        while len(current) <= part:
                            current.append({})
                        current = current[part]
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]

                # Set the final value
                final_key = parts[-1]
                if final_key.isdigit():
                    final_key = int(final_key)
                    if not isinstance(current, list):
                        current = []
                    while len(current) <= final_key:
                        current.append(None)
                    current[final_key] = value
                else:
                    current[final_key] = value

        # Apply nested updates to template_data
        if nested_updates:
            self._deep_update(self.template_data, nested_updates)
            self.logger.debug("Applied nested configuration updates")

    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Recursively update a dictionary with another dictionary."""
        for key, value in update_dict.items():
            if (
                isinstance(value, dict)
                and key in base_dict
                and isinstance(base_dict[key], dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _validate_config(self):
        """Validate the configuration against the schema."""
        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in self.config_dict:
                self.logger.error("Required configuration field '%s' is missing", field)
                raise ValueError(f"Required configuration field '{field}' is missing")

        # Validate field types and values
        for key, value in self.config_dict.items():
            if key in properties:
                schema = properties[key]
                self._validate_field(key, value, schema)

        # Validate Zendesk-specific requirements
        self._validate_zendesk_config()

    def _validate_field(self, key: str, value: Any, schema: Dict):
        """Validate a single configuration field."""
        expected_type = schema.get("type", "string")

        # Type validation
        if expected_type == "string" and not isinstance(value, str):
            raise ValueError(
                f"Field '{key}' must be a string, got {type(value).__name__}"
            )
        elif expected_type == "integer" and not isinstance(value, int):
            raise ValueError(
                f"Field '{key}' must be an integer, got {type(value).__name__}"
            )
        elif expected_type == "boolean" and not isinstance(value, bool):
            raise ValueError(
                f"Field '{key}' must be a boolean, got {type(value).__name__}"
            )
        elif expected_type == "array" and not isinstance(value, (list, tuple)):
            raise ValueError(
                f"Field '{key}' must be an array, got {type(value).__name__}"
            )

        # Enum validation
        if "enum" in schema and value not in schema["enum"]:
            raise ValueError(
                f"Field '{key}' must be one of {schema['enum']}, got '{value}'"
            )

        # Range validation for integers
        if expected_type == "integer":
            if "minimum" in schema and value < schema["minimum"]:
                raise ValueError(
                    f"Field '{key}' must be >= {schema['minimum']}, got {value}"
                )
            if "maximum" in schema and value > schema["maximum"]:
                raise ValueError(
                    f"Field '{key}' must be <= {schema['maximum']}, got {value}"
                )

    def _validate_zendesk_config(self):
        """Validate Zendesk-specific configuration requirements."""
        # Validate subdomain format
        subdomain = self.config_dict.get("zendesk_subdomain")
        if subdomain and not re.match(r"^[a-zA-Z0-9-]+$", subdomain):
            raise ValueError(
                "zendesk_subdomain must contain only alphanumeric characters and hyphens"
            )

        # Validate email format
        email = self.config_dict.get("zendesk_email")
        if email and not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            raise ValueError("zendesk_email must be a valid email address")

        # Ensure we have either API token or OAuth token
        api_token = self.config_dict.get("zendesk_api_token")
        oauth_token = self.config_dict.get("zendesk_oauth_token")
        if not api_token and not oauth_token:
            self.logger.warning("No authentication token provided. API calls may fail.")

        # Validate rate limit
        rate_limit = self.config_dict.get("rate_limit_requests", 200)
        if rate_limit < 1 or rate_limit > 10000:
            raise ValueError("rate_limit_requests must be between 1 and 10000")

        # Validate timeout
        timeout = self.config_dict.get("timeout_seconds", 30)
        if timeout < 1 or timeout > 300:
            raise ValueError("timeout_seconds must be between 1 and 300")

    def get_template_config(self) -> Dict[str, Any]:
        """
        Get configuration values from the config_schema.

        This returns the standard configuration values that can be set via
        CLI --config parameters or environment variables.
        """
        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        config = {}

        for key, schema in properties.items():
            if key in self.config_dict:
                config[key] = self.config_dict[key]
            elif "default" in schema:
                config[key] = schema["default"]
            else:
                config[key] = None

        return config

    def get_template_data(self) -> Dict[str, Any]:
        """
        Get the full template data, potentially modified by double underscore notation.

        This returns the complete template structure that may have been modified
        by CLI parameters using double underscore notation.
        """
        return self.template_data.copy()

    def get_zendesk_url(self) -> str:
        """Get the base Zendesk URL."""
        subdomain = self.config_dict.get("zendesk_subdomain", "subdomain")
        if not subdomain:
            raise ValueError("zendesk_subdomain is required")
        return f"https://{subdomain}.zendesk.com"

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Zendesk API requests."""
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        oauth_token = self.config_dict.get("zendesk_oauth_token")
        if oauth_token:
            headers["Authorization"] = f"Bearer {oauth_token}"
            return headers

        # Fall back to email/token authentication
        email = self.config_dict.get("zendesk_email")
        api_token = self.config_dict.get("zendesk_api_token")

        if email and api_token:
            import base64

            credentials = f"{email}/token:{api_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            headers["Authorization"] = f"Basic {encoded_credentials}"
        elif email:
            # Basic email authentication (less secure)
            import base64

            encoded_email = base64.b64encode(f"{email}:".encode()).decode()
            headers["Authorization"] = f"Basic {encoded_email}"

        return headers

    def get_rate_limit_config(self) -> Dict[str, int]:
        """Get rate limiting configuration."""
        return {
            "requests_per_minute": self.config_dict.get("rate_limit_requests", 200),
            "timeout_seconds": self.config_dict.get("timeout_seconds", 30),
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get caching configuration."""
        return {
            "enabled": self.config_dict.get("enable_cache", True),
            "ttl_seconds": self.config_dict.get("cache_ttl_seconds", 300),
        }

    def get_default_ticket_config(self) -> Dict[str, str]:
        """Get default ticket configuration."""
        return {
            "priority": self.config_dict.get("default_ticket_priority", "normal"),
            "type": self.config_dict.get("default_ticket_type", "question"),
        }

    def is_sensitive_field(self, field_name: str) -> bool:
        """Check if a field contains sensitive information."""
        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        field_schema = properties.get(field_name, {})
        return field_schema.get("sensitive", False)

    def get_sanitized_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive fields masked."""
        config = self.get_template_config()
        sanitized = {}

        for key, value in config.items():
            if self.is_sensitive_field(key) and value:
                sanitized[key] = "*" * 8
            else:
                sanitized[key] = value

        return sanitized
