"""
Config Manager - Centralized configuration operations.

This module provides a unified interface for configuration processing, validation,
and merging, consolidating functionality from CLI and MCPClient.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of configuration validation."""

    def __init__(
        self, valid: bool = True, errors: List[str] = None, warnings: List[str] = None
    ):
        self.valid = valid
        self.errors = errors or []
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


class ConfigManager:
    """
    Centralized configuration management operations.

    Provides unified interface for configuration processing, validation, and merging
    that can be shared between CLI and MCPClient implementations.
    """

    def __init__(self):
        """Initialize the config manager."""
        pass

    def merge_config_sources(
        self,
        template_config: Dict[str, Any],
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        config_values: Optional[Dict[str, str]] = None,
        override_values: Optional[Dict[str, str]] = None,
        k8s_config_file: Optional[str] = None,
        k8s_config_values: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Merge all configuration sources with proper precedence.

        Precedence order (highest to lowest):
        1. override_values (CLI --override)
        2. config_values (CLI --config)
        3. env_vars (CLI --env)
        4. config_file (CLI --config-file)
        5. template defaults (from config_schema)

        Args:
            template_config: Base template configuration (contains metadata and schema)
            config_file: Path to JSON/YAML configuration file
            env_vars: Environment variables dictionary
            config_values: Configuration values dictionary
            override_values: Override values dictionary (with double-underscore notation)

        Returns:
            Merged configuration dictionary (only user config values, not template metadata)
        """
        try:
            # Start with defaults from config schema, not the entire template
            merged_config = {}
            config_schema = template_config.get("config_schema", {})
            properties = config_schema.get("properties", {})

            # Apply defaults from schema
            for prop_name, prop_config in properties.items():
                if "default" in prop_config:
                    merged_config[prop_name] = prop_config["default"]

            # Merge system environment variables (lowest precedence after defaults)
            system_env_config = self._load_system_env_vars(template_config)
            if system_env_config:
                merged_config = self._deep_merge(merged_config, system_env_config)

            # Load and merge config file
            if config_file and os.path.exists(config_file):
                file_config = self._load_config_file(config_file)
                merged_config = self._deep_merge(merged_config, file_config)

            # Merge environment variables
            if env_vars:
                env_config = self._process_env_vars(env_vars, merged_config)
                merged_config = self._deep_merge(merged_config, env_config)

            # Merge config values
            if config_values:
                config_config = self._process_config_values(config_values)
                merged_config = self._deep_merge(merged_config, config_config)

            # Apply overrides with double-underscore notation
            if override_values:
                merged_config = self._apply_overrides(merged_config, override_values)

                # Also add override values with OVERRIDE_ prefix for CLI compatibility
                for key, value in override_values.items():
                    merged_config[f"OVERRIDE_{key}"] = value

            return merged_config

        except Exception as e:
            logger.error(f"Failed to merge config sources: {e}")
            # Return just defaults from schema on error
            defaults = {}
            config_schema = template_config.get("config_schema", {})
            properties = config_schema.get("properties", {})
            for prop_name, prop_config in properties.items():
                if "default" in prop_config:
                    defaults[prop_name] = prop_config["default"]
            return defaults

    def validate_config(
        self, config: Dict[str, Any], schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate configuration against a schema.

        Args:
            config: Configuration to validate
            schema: Configuration schema

        Returns:
            ValidationResult with validation status and messages
        """
        try:
            errors = []
            warnings = []

            # If no schema provided, assume valid
            if not schema:
                return ValidationResult(valid=True)

            # Check required fields
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in config:
                    errors.append(f"Required field '{field}' is missing")

            # Check field types and constraints
            properties = schema.get("properties", {})
            for field, value in config.items():
                if field in properties:
                    field_schema = properties[field]
                    field_errors = self._validate_field(field, value, field_schema)
                    errors.extend(field_errors)

            # Check for unknown fields
            if schema.get("additionalProperties", True) is False:
                for field in config:
                    if field not in properties:
                        warnings.append(f"Unknown field '{field}' in configuration")

            return ValidationResult(
                valid=len(errors) == 0, errors=errors, warnings=warnings
            )

        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return ValidationResult(valid=False, errors=[f"Validation error: {str(e)}"])

    def load_configuration_for_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load all configurations for a template.

        Args:
            template_name: The template name

        Returns:
            Dictionary with all template configurations
        """
        try:
            from mcp_template.core.template_manager import TemplateManager

            template_manager = TemplateManager()
            template_path = template_manager.get_template_path(template_name)

            if not template_path:
                return {}

            configurations = {}

            # Load main template configuration
            template_config_file = template_path / "template.json"
            if template_config_file.exists():
                configurations["template"] = self._load_config_file(
                    str(template_config_file)
                )

            # Load other configuration files
            config_dir = template_path / "config"
            if config_dir.exists():
                for config_file in config_dir.glob("*.json"):
                    config_name = config_file.stem
                    configurations[config_name] = self._load_config_file(
                        str(config_file)
                    )

                for config_file in config_dir.glob("*.yaml"):
                    config_name = config_file.stem
                    configurations[config_name] = self._load_config_file(
                        str(config_file)
                    )

                for config_file in config_dir.glob("*.yml"):
                    config_name = config_file.stem
                    configurations[config_name] = self._load_config_file(
                        str(config_file)
                    )

            return configurations

        except Exception as e:
            logger.error(
                f"Failed to load configurations for template {template_name}: {e}"
            )
            return {}

    def validate_template_configuration(self, template_name: str) -> Dict[str, Any]:
        """
        Comprehensive configuration validation for a template.

        Args:
            template_name: The template name

        Returns:
            Validation results dictionary
        """
        try:
            configurations = self.load_configuration_for_template(template_name)

            if not configurations:
                return {
                    "valid": False,
                    "errors": [f"No configurations found for template {template_name}"],
                    "warnings": [],
                }

            all_errors = []
            all_warnings = []

            # Validate each configuration
            for config_name, config_data in configurations.items():
                # For now, do basic structure validation
                if not isinstance(config_data, dict):
                    all_errors.append(
                        f"Configuration '{config_name}' is not a valid object"
                    )
                    continue

                # Check for common required fields based on config type
                if config_name == "template":
                    required_fields = ["name", "docker_image"]
                    for field in required_fields:
                        if field not in config_data:
                            all_errors.append(
                                f"Template configuration missing required field: {field}"
                            )

            return {
                "valid": len(all_errors) == 0,
                "errors": all_errors,
                "warnings": all_warnings,
                "configurations": configurations,
            }

        except Exception as e:
            logger.error(
                f"Failed to validate template configuration for {template_name}: {e}"
            )
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": [],
            }

    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON or YAML file."""
        try:
            with open(file_path, "r") as f:
                if file_path.endswith((".yml", ".yaml")):
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
            return {}

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _process_env_vars(
        self, env_vars: Dict[str, str], context_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process environment variables into configuration structure."""
        config = {}

        for key, value in env_vars.items():
            # Convert environment variable to config path
            # For now, just use direct mapping
            config[key] = value

        return config

    def _process_config_values(self, config_values: Dict[str, str]) -> Dict[str, Any]:
        """Process config values into proper types."""
        config = {}

        for key, value in config_values.items():
            # Try to convert to appropriate type
            try:
                # Try JSON parsing first
                config[key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Fall back to string
                config[key] = value

        return config

    def _apply_overrides(
        self, config: Dict[str, Any], overrides: Dict[str, str]
    ) -> Dict[str, Any]:
        """Apply overrides with double-underscore notation."""
        result = config.copy()

        for key, value in overrides.items():
            # Handle double-underscore notation (e.g., tools__0__custom_field)
            parts = key.split("__")
            current = result

            # Navigate to the target location
            for i, part in enumerate(parts[:-1]):
                if part.isdigit():
                    # Array index
                    idx = int(part)
                    if not isinstance(current, list):
                        continue
                    if idx >= len(current):
                        continue
                    current = current[idx]
                else:
                    # Object key
                    if part not in current:
                        current[part] = {}
                    current = current[part]

            # Set the final value
            final_key = parts[-1]
            if final_key.isdigit() and isinstance(current, list):
                idx = int(final_key)
                if idx < len(current):
                    current[idx] = value
            else:
                current[final_key] = value

        return result

    def _validate_field(
        self, field_name: str, value: Any, field_schema: Dict[str, Any]
    ) -> List[str]:
        """Validate a single field against its schema."""
        errors = []

        # Check type
        expected_type = field_schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                errors.append(
                    f"Field '{field_name}' should be a string, got {type(value).__name__}"
                )
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(
                    f"Field '{field_name}' should be a number, got {type(value).__name__}"
                )
            elif expected_type == "boolean" and not isinstance(value, bool):
                errors.append(
                    f"Field '{field_name}' should be a boolean, got {type(value).__name__}"
                )
            elif expected_type == "array" and not isinstance(value, list):
                errors.append(
                    f"Field '{field_name}' should be an array, got {type(value).__name__}"
                )
            elif expected_type == "object" and not isinstance(value, dict):
                errors.append(
                    f"Field '{field_name}' should be an object, got {type(value).__name__}"
                )

        # Check constraints
        if isinstance(value, str):
            min_length = field_schema.get("minLength")
            if min_length and len(value) < min_length:
                errors.append(
                    f"Field '{field_name}' is too short (minimum {min_length} characters)"
                )

            max_length = field_schema.get("maxLength")
            if max_length and len(value) > max_length:
                errors.append(
                    f"Field '{field_name}' is too long (maximum {max_length} characters)"
                )

        if isinstance(value, (int, float)):
            minimum = field_schema.get("minimum")
            if minimum is not None and value < minimum:
                errors.append(f"Field '{field_name}' is too small (minimum {minimum})")

            maximum = field_schema.get("maximum")
            if maximum is not None and value > maximum:
                errors.append(f"Field '{field_name}' is too large (maximum {maximum})")

        return errors

    def merge_k8s_config_sources(
        self,
        k8s_config_file: Optional[str] = None,
        k8s_config_values: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Merge Kubernetes-specific configuration sources.

        Args:
            k8s_config_file: Path to Kubernetes configuration file
            k8s_config_values: Kubernetes configuration values from CLI

        Returns:
            Merged Kubernetes configuration dictionary
        """
        merged_config = {}

        # Start with file-based configuration if provided
        if k8s_config_file:
            try:
                file_config = self._load_config_file(k8s_config_file)
                merged_config.update(file_config)
                logger.debug(f"Loaded Kubernetes config from file: {k8s_config_file}")
            except Exception as e:
                logger.warning(
                    f"Failed to load Kubernetes config file {k8s_config_file}: {e}"
                )

        # Override with CLI values
        if k8s_config_values:
            # Process special values that need type conversion
            processed_values = {}
            for key, value in k8s_config_values.items():
                processed_values[key] = self._convert_config_value(value)

            merged_config.update(processed_values)
            logger.debug(
                f"Applied Kubernetes config values: {list(k8s_config_values.keys())}"
            )

        return merged_config

    def _convert_config_value(self, value: str) -> Any:
        """Convert string configuration value to appropriate type."""
        # Handle boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Handle numeric values
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Handle JSON objects/arrays
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Return as string
        return value

    def _load_system_env_vars(self, template_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load system environment variables that match template config properties.

        Looks for environment variables that exactly match config property names.
        Uses template's config schema to determine which env vars to look for.

        Args:
            template_config: Template configuration with config_schema

        Returns:
            Dictionary of matching environment variables
        """
        import os

        system_env_config = {}
        config_schema = template_config.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Check for environment variables that exactly match config property names
        for prop_name, prop_config in properties.items():
            env_value = os.environ.get(prop_name)
            if env_value is not None:
                system_env_config[prop_name] = self._convert_config_value(env_value)

        return system_env_config
