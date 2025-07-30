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
from typing import Any, Dict, List, Optional


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

        # Load template data first so we can use it for type coercion
        self.template_data = self._load_template()
        self.logger.debug("Template data loaded")

        # Load override environment variables from deployer
        self._load_override_env_vars()

        # Process any double underscore configurations passed from CLI
        self._process_nested_config()

        # Validate configuration
        self._validate_config()
        self.logger.info("Demo server configuration loaded")

    def _load_override_env_vars(self) -> None:
        """
        Load override environment variables set by the deployer.

        Environment variables with OVERRIDE_ prefix are processed as template overrides.
        These allow the deployer to pass override values without parsing template.json.
        """
        override_dict = {}

        # Scan environment for OVERRIDE_ variables
        for env_var, env_value in os.environ.items():
            override_key = None

            if env_var.startswith("OVERRIDE_"):
                # Remove OVERRIDE_ prefix to get the original key
                override_key = env_var[9:]
            elif env_var.startswith("MCP_OVERRIDE_"):
                # Handle case where deployment pipeline adds MCP_ prefix
                override_key = env_var[13:]

            if override_key:
                override_dict[override_key] = env_value
                self.logger.debug(
                    "Found override environment variable: %s = %s",
                    override_key,
                    env_value,
                )

        # Add override values to config_dict so they get processed by _process_nested_config
        if override_dict:
            self.config_dict.update(override_dict)
            self.logger.info(
                "Loaded %d override environment variables", len(override_dict)
            )

    def _validate_config(self) -> None:
        """Validate configuration values."""
        valid_log_levels = ["debug", "info", "warn", "warning", "error", "critical"]
        if self.log_level.lower() not in valid_log_levels:
            self.logger.warning("Invalid log level '%s', using 'info'", self.log_level)
            self.log_level = "info"

    def _process_nested_config(self) -> None:
        """
        Process double underscore notation in configuration.

        Recursively processes nested keys using double underscore notation and
        attempts to cast values using the original data type from template.json.
        """
        processed_config = {}

        for key, value in self.config_dict.items():
            if "__" in key:
                processed_key, processed_value = self._process_double_underscore_key(
                    key, value
                )
                if processed_key:
                    # Attempt type coercion based on template.json schema
                    coerced_value = self._coerce_value_type(
                        processed_key, processed_value
                    )
                    processed_config[processed_key] = coerced_value
            else:
                # Keep non-nested configurations as-is, but still attempt type coercion
                coerced_value = self._coerce_value_type(key, value)
                processed_config[key] = coerced_value

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

        # Check if the final key is a known config property
        if self._is_config_property(config_key):
            self.logger.debug("Processed config property: %s = %s", config_key, value)
            return config_key, value

        # Handle template-level overrides (legacy for backward compatibility)
        elif prefix.lower() in ["demo", "template"]:
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

    def _is_config_property(self, key: str) -> bool:
        """Check if a key is a known configuration property."""
        if not hasattr(self, "template_data") or not self.template_data:
            return False

        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Check if it's a direct property
        if key in properties:
            return True

        # Check if it matches any env_mapping
        for prop_data in properties.values():
            if prop_data.get("env_mapping") == key:
                return True

        return False

    def _handle_multi_part_key(self, parts: list[str], value: Any) -> tuple[str, Any]:
        """
        Handle multi-part keys like category__subcategory__property.

        For template.json overrides, this preserves the nested structure.
        For config properties, this flattens to underscore-separated keys.
        """
        # For template.json structure overrides, preserve the full nested path
        # This will be handled by _apply_nested_override in get_template_data()
        if self._is_template_structure_override(parts):
            # Return the original key to preserve nested structure for template overrides
            full_key = "__".join(parts)
            self.logger.debug(
                "Processed template structure override: %s = %s", full_key, value
            )
            return full_key, value
        else:
            # For config properties, check if the final part is a known config property
            final_key = parts[-1]
            if self._is_config_property(final_key):
                self.logger.debug(
                    "Processed config property: %s = %s", final_key, value
                )
                return final_key, value
            else:
                # For non-config properties, create nested structure
                nested_key = "_".join(parts)
                self.logger.debug(
                    "Processed nested structure: %s = %s", nested_key, value
                )
                return nested_key, value

    def _is_template_structure_override(self, parts: list[str]) -> bool:
        """
        Determine if a multi-part key is overriding template.json structure.

        Template structure overrides typically target:
        - tools__0__name, tools__1__enabled
        - metadata__version, metadata__author
        - servers__0__config__host
        - Any nested object/array in template.json
        """
        if not parts:
            return False

        first_part = parts[0].lower()

        # Common template.json top-level keys that contain nested structures
        template_structure_keys = {
            "tools",
            "metadata",
            "servers",
            "capabilities",
            "examples",
            "config",
            "volumes",
            "ports",
            "transport",
            "requirements",
        }

        # If first part matches known template structure keys
        if first_part in template_structure_keys:
            return True

        # If second part is numeric (likely array index), it's probably template structure
        if len(parts) > 1 and parts[1].isdigit():
            return True

        # If we have more than 2 parts and it's not a simple config override pattern
        if len(parts) > 2:
            # Check if this looks like a config property pattern
            # Config patterns: demo__log_level, system__config__debug
            # Template patterns: tools__0__name, metadata__custom__field
            return not self._looks_like_config_pattern(parts)

        return False

    def _looks_like_config_pattern(self, parts: list[str]) -> bool:
        """
        Check if a multi-part key looks like a config property pattern.

        Config patterns usually have prefixes like:
        - demo__, template__, system__, config__, app__, settings__
        """
        if not parts:
            return False

        config_prefixes = {
            "demo",
            "template",
            "system",
            "config",
            "app",
            "settings",
            "server",
            "client",
            "service",
            "api",
            "database",
            "security",
        }

        return parts[0].lower() in config_prefixes

    def _coerce_value_type(self, key: str, value: Any) -> Any:
        """
        Attempt to coerce value to the appropriate type based on template.json schema.

        Args:
            key: Configuration key
            value: String value to coerce

        Returns:
            Coerced value or original value if coercion fails
        """
        if not hasattr(self, "template_data") or not self.template_data:
            return value

        prop_config = self._find_property_config(key)
        if not prop_config:
            return value

        try:
            prop_type = prop_config.get("type", "string")
            return self._convert_value_by_type(value, prop_type, prop_config)

        except (ValueError, json.JSONDecodeError) as e:
            self.logger.warning(
                "Failed to coerce value '%s' for key '%s' to type '%s': %s. Using original value.",
                value,
                key,
                prop_config.get("type", "unknown"),
                str(e),
            )
            return value

    def _find_property_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Find property configuration for a given key."""
        config_schema = self.template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Direct key lookup
        prop_config = properties.get(key)
        if prop_config:
            return prop_config

        # Try to find by env_mapping as fallback
        for prop_data in properties.values():
            if prop_data.get("env_mapping") == key:
                return prop_data

        return None

    def _convert_value_by_type(
        self, value: Any, prop_type: str, prop_config: Dict[str, Any]
    ) -> Any:
        """Convert value based on property type."""
        if prop_type == "boolean":
            return self._convert_to_boolean(value)
        elif prop_type == "integer":
            return int(value)
        elif prop_type == "number":
            return float(value)
        elif prop_type == "array":
            return self._convert_to_array(value, prop_config)
        elif prop_type == "object":
            return self._convert_to_object(value)
        else:  # string or unknown type
            return str(value)

    def _convert_to_boolean(self, value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ("true", "1", "yes", "on"):
                return True
            elif lower_value in ("false", "0", "no", "off"):
                return False
            else:
                raise ValueError(f"Invalid boolean value: {value}")
        return bool(value)

    def _convert_to_array(self, value: Any, prop_config: Dict[str, Any]) -> List[Any]:
        """Convert value to array."""
        if isinstance(value, str):
            # Handle JSON array strings
            if value.startswith("["):
                if not value.endswith("]"):
                    raise ValueError(f"Malformed JSON array: {value}")
                try:
                    return json.loads(value)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON array: {value}") from e
            else:
                # Handle comma-separated values
                separator = prop_config.get("env_separator", ",")
                return [item.strip() for item in value.split(separator)]
        elif isinstance(value, list):
            return value
        else:
            return [value]

    def _convert_to_object(self, value: Any) -> Any:
        """Convert value to object."""
        if isinstance(value, str) and value.startswith("{"):
            return json.loads(value)
        return value

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
        template_config_keys = set(self.get_template_config().keys())
        for key, value in self.config_dict.items():
            if "__" in key:
                # Apply nested override to template data
                self._apply_nested_override(template_data, key, value)
            elif key.lower() not in template_config_keys:
                # Direct template-level override (not in config_schema)
                # Convert key to lowercase to match template.json keys
                template_key = key.lower()
                template_data[template_key] = value
                self.logger.debug(
                    "Applied template override: %s = %s", template_key, value
                )

        return template_data

    def _apply_nested_override(
        self, data: Dict[str, Any], key: str, value: Any
    ) -> None:
        """
        Apply a nested override using double underscore notation.

        Supports deeply nested structures like:
        - tools__0__name -> data["tools"][0]["name"]
        - metadata__custom__nested__field -> data["metadata"]["custom"]["nested"]["field"]
        - servers__0__config__database__host -> data["servers"][0]["config"]["database"]["host"]

        Args:
            data: Dictionary to modify
            key: Double underscore key (e.g., "tools__0__custom_field")
            value: Value to set
        """
        parts = key.split("__")
        current = data

        # Navigate to the nested location, creating structure as needed
        for i, part in enumerate(parts[:-1]):
            next_part = parts[i + 1] if i + 1 < len(parts) - 1 else parts[-1]
            current = self._navigate_to_nested_key(current, part, next_part)
            if current is None:
                self.logger.warning("Failed to navigate to nested key: %s", part)
                return

        # Set the final value with type inference
        final_key = parts[-1]
        coerced_value = self._infer_and_convert_override_value(value)
        self._set_final_value(current, final_key, coerced_value)
        self.logger.debug("Applied nested override: %s = %s", key, coerced_value)

    def _infer_and_convert_override_value(self, value: str) -> Any:
        """
        Infer the appropriate type for an override value and convert it.

        This handles JSON strings, boolean strings, numeric strings, etc.
        """
        if not isinstance(value, str):
            return value

        # Handle JSON objects and arrays
        if (value.startswith("{") and value.endswith("}")) or (
            value.startswith("[") and value.endswith("]")
        ):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        # Handle boolean strings
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Handle numeric strings
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _navigate_to_nested_key(
        self, current: Any, part: str, next_part: str = None
    ) -> Any:
        """
        Navigate to a nested key, handling both list indices and object keys.
        Creates intermediate structures as needed.

        Args:
            current: Current data structure to navigate
            part: Current key/index to navigate to
            next_part: Next part in the path (used for type hint of what to create)
        """
        if part.isdigit():
            return self._handle_list_index(current, int(part))
        else:
            return self._handle_object_key(current, part, next_part)

    def _handle_list_index(self, current: Any, index: int) -> Any:
        """
        Handle navigation to a list index.
        Creates list if current is not a list, extends list if needed.
        """
        # If current is not a list, we can't navigate to an index
        if not isinstance(current, list):
            self.logger.warning(
                "Trying to index non-list type %s with index %s",
                type(current).__name__,
                index,
            )
            return None

        # Extend list if necessary
        while len(current) <= index:
            current.append({})
        return current[index]

    def _handle_object_key(self, current: Any, key: str, next_part: str = None) -> Any:
        """
        Handle navigation to an object key.
        Creates nested dict or list if key doesn't exist, based on next_part.

        Args:
            current: Current data structure (should be dict-like)
            key: The key to navigate to
            next_part: Next part in the path (used to determine if we need list or dict)
        """
        # If current is not a dict, we can't navigate into it
        if not isinstance(current, dict):
            self.logger.warning(
                "Trying to access key '%s' on non-dict type: %s", key, type(current)
            )
            return None

        # Create key if it doesn't exist
        if key not in current:
            # If next part is numeric, create a list; otherwise, create a dict
            if next_part and next_part.isdigit():
                current[key] = []
            else:
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
