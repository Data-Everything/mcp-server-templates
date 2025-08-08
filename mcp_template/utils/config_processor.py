"""
Configuration processing utility for MCP templates.

This module provides a unified way to process configuration from multiple sources
and handle special properties like volume mounts and command arguments.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ConfigProcessor:
    """Unified configuration processor for MCP templates."""

    def __init__(self):
        """Initialize the configuration processor."""
        pass

    def prepare_configuration(
        self,
        template: Dict[str, Any],
        env_vars: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
        config_values: Optional[Dict[str, str]] = None,
        session_config: Optional[Dict[str, Any]] = None,
        inline_config: Optional[List[str]] = None,
        env_var_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare configuration from multiple sources with proper type conversion.

        Priority order (highest to lowest):
        1. env_vars (Dict)
        2. inline_config (List of KEY=VALUE)
        3. env_var_list (List of KEY=VALUE)
        4. config_values (Dict)
        5. config_file (JSON/YAML file)
        6. session_config (persistent session config)
        7. template defaults

        Args:
            template: Template configuration
            env_vars: Environment variables as dict (highest priority)
            config_file: Path to JSON/YAML configuration file
            config_values: Configuration values as dict
            session_config: Base configuration from interactive session
            inline_config: List of KEY=VALUE inline config pairs
            env_var_list: List of KEY=VALUE environment variable pairs

        Returns:
            Processed configuration dictionary
        """
        config = {}

        # Start with template defaults
        template_env = template.get("env_vars", {})
        for key, value in template_env.items():
            config[key] = value

        # Apply session config if provided
        if session_config:
            config.update(session_config)

        # Load from config file if provided
        if config_file:
            config.update(self._load_config_file(config_file, template))

        # Apply CLI config values with type conversion
        if config_values:
            config.update(self._convert_config_values(config_values, template))

        # Apply environment variable list (medium priority)
        if env_var_list:
            for pair in env_var_list:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    config[k] = v

        # Apply inline config list (higher priority)
        if inline_config:
            for pair in inline_config:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    config[k] = v

        # Apply environment variables dict (highest priority)
        if env_vars:
            config.update(env_vars)

        return config

    def handle_volume_and_args_config_properties(
        self,
        template: Dict[str, Any],
        config: Dict[str, Any],
        default_mount_path: str = "/mnt",
    ) -> Dict[str, Any]:
        """
        Process properties that have volume_mount or command_arg set to True.
        These should not be treated as environment variables but as Docker volumes/commands.

        Args:
            template: Template configuration
            config: Configuration dictionary
            default_mount_path: Default mount path for volumes

        Returns:
            Dictionary with updated template and config
        """
        config_properties = template.get("config_schema", {}).get("properties", {})
        command = []
        volumes = {}

        # Make a copy to avoid modifying during iteration
        config_copy = config.copy()

        for prop_key, prop_value in config_properties.items():
            delete_key = False
            env_var_name = prop_value.get("env_mapping", prop_key.upper())
            container_mount_path = None
            host_path = None
            final_container_paths = []

            # Check if this property is a volume mount
            if (
                env_var_name in config_copy
                and prop_value.get("volume_mount", False) is True
            ):
                config_value = config_copy[env_var_name]

                # Clean up the value - remove Docker command artifacts and split by space
                # Handle cases where users accidentally include Docker syntax
                cleaned_value = config_value.strip()

                # Remove common Docker command artifacts more carefully
                docker_artifacts = ["--volume ", "-v ", "--env ", "-e "]
                for artifact in docker_artifacts:
                    cleaned_value = cleaned_value.replace(artifact, " ")

                # Also handle cases where artifacts are at the end
                end_artifacts = ["--volume", "-v", "--env", "-e"]
                for artifact in end_artifacts:
                    if cleaned_value.endswith(artifact):
                        cleaned_value = cleaned_value[: -len(artifact)]

                # Split by space to handle multiple paths, then filter out empty strings
                path_parts = [
                    part.strip() for part in cleaned_value.split() if part.strip()
                ]

                for path_part in path_parts:
                    if not path_part:
                        continue

                    mount_value = path_part.split(":")
                    container_mount_path = None
                    host_path = None

                    # In most cases, it would be only the host path
                    if len(mount_value) == 1:
                        container_mount_path = None
                        host_path = mount_value[0]
                    elif len(mount_value) == 2:
                        # Assume format is host_path:container_path
                        container_mount_path = mount_value[1]
                        host_path = mount_value[0]
                    else:
                        logger.warning("Invalid volume mount format: %s", path_part)
                        continue  # Skip this path and continue with others

                    if host_path and host_path.startswith(
                        "/"
                    ):  # Only process absolute paths
                        if container_mount_path:
                            volumes[host_path] = container_mount_path
                            final_container_paths.append(container_mount_path)
                        else:
                            container_path = (
                                f"{default_mount_path}/{host_path.lstrip('/')}"
                            )
                            volumes[host_path] = container_path
                            final_container_paths.append(container_path)

                delete_key = True

            # Check if this property is a command argument
            if (
                env_var_name in config_copy
                and prop_value.get("command_arg", False) is True
            ):
                # If this property is both volume_mount and command_arg, use container paths
                if final_container_paths:
                    # Use the container paths for command arguments since the container
                    # needs to access the mounted paths, not the original host paths
                    command.extend(final_container_paths)
                else:
                    # If not a volume mount, use the original value as-is
                    config_value = config_copy[env_var_name]

                    # Clean up the value for command arguments (remove Docker artifacts if any)
                    cleaned_value = config_value.strip()
                    docker_artifacts = ["--volume ", "-v ", "--env ", "-e "]
                    for artifact in docker_artifacts:
                        cleaned_value = cleaned_value.replace(artifact, " ")

                    end_artifacts = ["--volume", "-v", "--env", "-e"]
                    for artifact in end_artifacts:
                        if cleaned_value.endswith(artifact):
                            cleaned_value = cleaned_value[: -len(artifact)]

                    # For space-separated paths in command args, split and add each
                    path_parts = [
                        part.strip() for part in cleaned_value.split() if part.strip()
                    ]
                    command.extend(path_parts)

                delete_key = True

            if delete_key:
                # Remove the key from config to avoid duplication
                config.pop(env_var_name, None)

        # Update template with volumes and commands
        if "volumes" not in template or template["volumes"] is None:
            template["volumes"] = {}
        template["volumes"].update(volumes)

        if "command" not in template or template["command"] is None:
            template["command"] = []
        template["command"].extend(command)

        return {
            "template": template,
            "config": config,
        }

    def _load_config_file(
        self, config_file: str, template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load configuration from JSON/YAML file and map to environment variables."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")

            # Load based on extension
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                import yaml

                with open(config_path, "r") as f:
                    file_config = yaml.safe_load(f)
            else:
                with open(config_path, "r") as f:
                    file_config = json.load(f)

            # Map file config to environment variables
            return self._map_file_config_to_env(file_config, template)

        except Exception as e:
            logger.error(f"Failed to load config file {config_file}: {e}")
            raise

    def _map_file_config_to_env(
        self, file_config: Dict[str, Any], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map config file values to environment variables based on template schema."""
        env_config = {}

        # Get the config schema from template
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Generic mapping: try to map config values directly to properties
        # First, try direct property name mapping
        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping", prop_name.upper())

            # Try direct property name mapping
            if prop_name in file_config:
                env_config[env_mapping] = self._convert_value_to_env_string(
                    file_config[prop_name], prop_config
                )

            # Try nested mapping patterns
            else:
                nested_value = self._find_nested_config_value(
                    file_config, prop_name, prop_config
                )
                if nested_value is not None:
                    env_config[env_mapping] = self._convert_value_to_env_string(
                        nested_value, prop_config
                    )

        return env_config

    def _find_nested_config_value(
        self, file_config: Dict[str, Any], prop_name: str, prop_config: Dict[str, Any]
    ) -> Any:
        """Find config value using common nested patterns."""
        # Check if property config has a file_mapping hint
        if "file_mapping" in prop_config:
            return self._get_nested_value(file_config, prop_config["file_mapping"])

        # Try common nested patterns based on property name
        common_patterns = self._generate_common_patterns(prop_name)
        for pattern in common_patterns:
            try:
                value = self._get_nested_value(file_config, pattern)
                if value is not None:
                    return value
            except (KeyError, AttributeError):
                continue

        return None

    def _generate_common_patterns(self, prop_name: str) -> List[str]:
        """Generate common nested configuration patterns for a property."""
        patterns = []

        # Common category mappings
        category_mappings = {
            "log_level": ["logging.level", "log.level"],
            "enable_audit_logging": [
                "logging.enableAudit",
                "logging.audit",
                "log.audit",
            ],
            "read_only_mode": ["security.readOnly", "security.readonly", "readonly"],
            "max_file_size": [
                "security.maxFileSize",
                "limits.maxFileSize",
                "performance.maxFileSize",
            ],
            "allowed_directories": [
                "security.allowedDirs",
                "security.directories",
                "paths.allowed",
            ],
            "exclude_patterns": [
                "security.excludePatterns",
                "security.exclude",
                "filters.exclude",
            ],
            "max_concurrent_operations": [
                "performance.maxConcurrentOperations",
                "limits.concurrent",
            ],
            "timeout_ms": [
                "performance.timeoutMs",
                "performance.timeout",
                "limits.timeout",
            ],
        }

        if prop_name in category_mappings:
            patterns.extend(category_mappings[prop_name])

        # Generate generic patterns
        camel_name = self._snake_to_camel(prop_name)
        patterns.extend(
            [
                f"config.{prop_name}",
                f"settings.{prop_name}",
                f"options.{prop_name}",
                f"config.{camel_name}",
                f"settings.{camel_name}",
                f"options.{camel_name}",
            ]
        )

        return patterns

    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise KeyError(f"Key '{key}' not found in path '{path}'")
        return value

    def _convert_value_to_env_string(
        self, value: Any, prop_config: Dict[str, Any]
    ) -> str:
        """Convert a value to environment variable string format."""
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def _convert_config_values(
        self, config_values: Dict[str, str], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert CLI config values to proper types based on template schema."""
        converted_config = {}
        # Get the config schema from template
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for key, value in config_values.items():
            # Handle nested CLI config using double underscore notation
            if "__" in key:
                nested_key = self._handle_nested_cli_config(key, value, properties)
                if nested_key:
                    key = nested_key

            # Find the property config for type conversion
            prop_config = None
            env_mapping = None

            # Try to find the property by name or env_mapping
            for prop_name, prop_cfg in properties.items():
                prop_env_mapping = prop_cfg.get("env_mapping", prop_name.upper())
                if key == prop_name or key == prop_env_mapping:
                    prop_config = prop_cfg
                    env_mapping = prop_env_mapping
                    break

            # Convert value based on property type
            if prop_config:
                prop_type = prop_config.get("type", "string")
                try:
                    if prop_type == "boolean":
                        converted_config[env_mapping] = str(value).lower() in (
                            "true",
                            "1",
                            "yes",
                        )
                    elif prop_type == "integer":
                        converted_config[env_mapping] = int(value)
                    elif prop_type == "number":
                        converted_config[env_mapping] = float(value)
                    elif prop_type == "array":
                        # Handle comma-separated values
                        if isinstance(value, str):
                            converted_config[env_mapping] = value
                        else:
                            converted_config[env_mapping] = ",".join(
                                str(v) for v in value
                            )
                    else:
                        converted_config[env_mapping] = str(value)
                except (ValueError, TypeError) as e:
                    logger.warning(
                        f"Failed to convert {key}={value} to {prop_type}: {e}"
                    )
                    converted_config[env_mapping] = str(value)
            else:
                # No property config found, use the key as-is
                converted_config[key] = str(value)

        return converted_config

    def _handle_nested_cli_config(
        self, nested_key: str, value: str, properties: Dict[str, Any]
    ) -> Optional[str]:
        """Handle nested CLI configuration using double underscore notation."""
        # Convert security__read_only to find read_only_mode in properties
        # Also supports template__property notation for template-level overrides
        parts = nested_key.split("__")
        if len(parts) < 2:
            return None

        # Handle template-level overrides (template_name__property)
        if len(parts) == 2:
            category, prop = parts
            # Try to find property with this category prefix
            for prop_name in properties:
                if prop_name.startswith(category.lower()) or prop_name == prop:
                    return prop_name
        elif len(parts) == 3:
            # Handle three-part notation: category__subcategory__property
            category, subcategory, prop = parts
            search_patterns = [
                f"{category}_{subcategory}_{prop}",
                f"{category}_{prop}",
                prop,
            ]
            for pattern in search_patterns:
                if pattern in properties:
                    return pattern

        return None
