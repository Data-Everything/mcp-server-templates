"""
Configuration management functionality shared between CLI and MCPClient.

This module provides centralized configuration processing, merging, validation,
and transformation capabilities that can be used by both the CLI interface
and the programmatic MCPClient API.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from mcp_template.deployer import MCPDeployer
from mcp_template.utils.config_processor import ConfigProcessor as CoreConfigProcessor

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Centralized configuration management for CLI and MCPClient.

    Provides common functionality for configuration processing, merging,
    validation, and transformation across different input sources.
    """

    def __init__(self):
        """Initialize configuration manager."""
        self.core_config_processor = CoreConfigProcessor()

    def prepare_configuration(
        self,
        template: Dict[str, Any],
        config_values: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare configuration from multiple sources.

        Args:
            template: Template data
            config_values: Configuration values from command line
            config_file: Path to configuration file
            env_vars: Environment variables

        Returns:
            Processed configuration dictionary
        """
        try:
            return self.core_config_processor.prepare_configuration(
                template=template,
                config_values=config_values,
                config_file=config_file,
                env_vars=env_vars,
            )
        except Exception as e:
            logger.error("Failed to prepare configuration: %s", e)
            raise

    def load_config_file(self, file_path: str) -> Dict[str, Any]:
        """
        Load configuration from JSON or YAML file.

        Args:
            file_path: Path to configuration file

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")

            with open(path, "r", encoding="utf-8") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    config = yaml.safe_load(f)
                elif path.suffix.lower() == ".json":
                    config = json.load(f)
                else:
                    # Try JSON first, then YAML
                    content = f.read()
                    f.seek(0)
                    try:
                        config = json.loads(content)
                    except json.JSONDecodeError:
                        try:
                            config = yaml.safe_load(content)
                        except yaml.YAMLError as e:
                            raise ValueError(
                                f"Invalid file format. Must be JSON or YAML: {e}"
                            )

            return config or {}

        except Exception as e:
            logger.error("Failed to load config file %s: %s", file_path, e)
            raise

    def merge_configurations(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge multiple configuration dictionaries.

        Args:
            *configs: Configuration dictionaries to merge

        Returns:
            Merged configuration dictionary
        """
        merged = {}

        for config in configs:
            if config:
                merged.update(config)

        return merged

    def validate_configuration(
        self, template: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate configuration against template schema.

        Args:
            template: Template data with config_schema
            config: Configuration to validate

        Returns:
            Dictionary with validation results:
            - valid: bool - Whether configuration is valid
            - errors: List[str] - List of validation errors
            - warnings: List[str] - List of validation warnings
            - missing_properties: List[str] - Missing required properties
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "missing_properties": [],
        }

        try:
            # Check for missing required properties
            missing_properties = MCPDeployer.list_missing_properties(template, config)
            result["missing_properties"] = missing_properties

            if missing_properties:
                result["errors"].append(
                    f"Missing required properties: {missing_properties}"
                )

            # Validate against config schema
            config_schema = template.get("config_schema", {})
            if config_schema:
                properties = config_schema.get("properties", {})

                # Validate each property
                for prop_name, value in config.items():
                    if prop_name in properties:
                        prop_schema = properties[prop_name]
                        validation_error = self._validate_property(
                            prop_name, value, prop_schema
                        )
                        if validation_error:
                            result["errors"].append(validation_error)
                    else:
                        result["warnings"].append(f"Unknown property: {prop_name}")

            # Set valid status
            result["valid"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"Validation failed: {str(e)}")

        return result

    def _validate_property(
        self, name: str, value: Any, schema: Dict[str, Any]
    ) -> Optional[str]:
        """
        Validate a single property against its schema.

        Args:
            name: Property name
            value: Property value
            schema: Property schema

        Returns:
            Error message if invalid, None if valid
        """
        prop_type = schema.get("type", "string")

        # Type validation
        if prop_type == "string" and not isinstance(value, str):
            return f"Property '{name}' must be a string, got {type(value).__name__}"
        elif prop_type == "integer" and not isinstance(value, int):
            return f"Property '{name}' must be an integer, got {type(value).__name__}"
        elif prop_type == "number" and not isinstance(value, (int, float)):
            return f"Property '{name}' must be a number, got {type(value).__name__}"
        elif prop_type == "boolean" and not isinstance(value, bool):
            return f"Property '{name}' must be a boolean, got {type(value).__name__}"
        elif prop_type == "array" and not isinstance(value, list):
            return f"Property '{name}' must be an array, got {type(value).__name__}"

        # Range validation for numbers
        if prop_type in ["integer", "number"]:
            minimum = schema.get("minimum")
            maximum = schema.get("maximum")

            if minimum is not None and value < minimum:
                return f"Property '{name}' must be >= {minimum}, got {value}"
            if maximum is not None and value > maximum:
                return f"Property '{name}' must be <= {maximum}, got {value}"

        # Length validation for strings and arrays
        if prop_type in ["string", "array"]:
            min_length = schema.get("minLength")
            max_length = schema.get("maxLength")
            length = len(value)

            if min_length is not None and length < min_length:
                return (
                    f"Property '{name}' must have length >= {min_length}, got {length}"
                )
            if max_length is not None and length > max_length:
                return (
                    f"Property '{name}' must have length <= {max_length}, got {length}"
                )

        # Enum validation
        enum_values = schema.get("enum")
        if enum_values and value not in enum_values:
            return f"Property '{name}' must be one of {enum_values}, got {value}"

        return None

    def process_command_line_config(self, config_args: List[str]) -> Dict[str, Any]:
        """
        Process configuration from command line arguments.

        Args:
            config_args: List of KEY=VALUE strings

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If argument format is invalid
        """
        config = {}

        for arg in config_args:
            if "=" not in arg:
                raise ValueError(f"Invalid config format: {arg}. Use KEY=VALUE")

            key, value = arg.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Try to parse as JSON for complex values
            try:
                parsed_value = json.loads(value)
                config[key] = parsed_value
            except json.JSONDecodeError:
                # Use as string if not valid JSON
                config[key] = value

        return config

    def process_environment_variables(self, env_args: List[str]) -> Dict[str, str]:
        """
        Process environment variables from command line arguments.

        Args:
            env_args: List of KEY=VALUE strings

        Returns:
            Environment variables dictionary

        Raises:
            ValueError: If argument format is invalid
        """
        env_vars = {}

        for arg in env_args:
            if "=" not in arg:
                raise ValueError(f"Invalid env format: {arg}. Use KEY=VALUE")

            key, value = arg.split("=", 1)
            env_vars[key.strip()] = value.strip()

        return env_vars

    def apply_template_overrides(
        self, template: Dict[str, Any], overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply override values to template data.

        Args:
            template: Original template data
            overrides: Override values with double-underscore notation support

        Returns:
            Template data with overrides applied
        """
        import copy

        result = copy.deepcopy(template)

        for key, value in overrides.items():
            if "__" in key:
                # Handle nested overrides (e.g., "tools__0__name")
                self._apply_nested_override(result, key, value)
            else:
                # Simple override
                result[key] = value

        return result

    def _apply_nested_override(
        self, data: Dict[str, Any], key: str, value: Any
    ) -> None:
        """
        Apply nested override using double-underscore notation.

        Args:
            data: Target data structure
            key: Override key with double-underscore notation
            value: Override value
        """
        parts = key.split("__")
        current = data

        # Navigate to the parent of the target
        for part in parts[:-1]:
            # Handle array indices
            if part.isdigit():
                index = int(part)
                if not isinstance(current, list):
                    return  # Cannot index non-list
                if index >= len(current):
                    return  # Index out of bounds
                current = current[index]
            else:
                # Handle object keys
                if not isinstance(current, dict):
                    return  # Cannot access property on non-dict
                if part not in current:
                    current[part] = {}  # Create missing intermediate objects
                current = current[part]

        # Set the final value
        final_key = parts[-1]
        if final_key.isdigit() and isinstance(current, list):
            index = int(final_key)
            if index < len(current):
                current[index] = value
        elif isinstance(current, dict):
            current[final_key] = value

    def handle_volume_and_args_config(
        self, template: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle volume mounts and command arguments configuration.

        Args:
            template: Template data
            config: Configuration data

        Returns:
            Dictionary with processed template and config
        """
        try:
            return self.core_config_processor.handle_volume_and_args_config_properties(
                template, config
            )
        except Exception as e:
            logger.error("Failed to handle volume and args config: %s", e)
            raise

    def export_configuration(
        self, config: Dict[str, Any], file_path: str, format_type: str = "json"
    ) -> bool:
        """
        Export configuration to file.

        Args:
            config: Configuration to export
            file_path: Output file path
            format_type: Export format ("json" or "yaml")

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding="utf-8") as f:
                if format_type.lower() == "yaml":
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error("Failed to export configuration to %s: %s", file_path, e)
            return False

    def get_configuration_schema(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the configuration schema for a template.

        Args:
            template: Template data

        Returns:
            Configuration schema
        """
        return template.get("config_schema", {})

    def generate_example_config(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate example configuration from template schema.

        Args:
            template: Template data

        Returns:
            Example configuration with default values
        """
        config = {}
        schema = self.get_configuration_schema(template)
        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            if "default" in prop_schema:
                config[prop_name] = prop_schema["default"]
            elif "example" in prop_schema:
                config[prop_name] = prop_schema["example"]
            else:
                # Generate example based on type
                prop_type = prop_schema.get("type", "string")
                if prop_type == "string":
                    config[prop_name] = f"example_{prop_name}"
                elif prop_type == "integer":
                    config[prop_name] = 0
                elif prop_type == "number":
                    config[prop_name] = 0.0
                elif prop_type == "boolean":
                    config[prop_name] = False
                elif prop_type == "array":
                    config[prop_name] = []
                elif prop_type == "object":
                    config[prop_name] = {}

        return config
