"""
Tool management functionality shared between CLI and MCPClient.

This module provides centralized tool discovery, validation, and management
capabilities that can be used by both the CLI interface and the programmatic
MCPClient API.
"""

import logging
from typing import Any, Dict, List, Optional

from mcp_template.tools.discovery import ToolDiscovery
from mcp_template.tools.docker_probe import DockerProbe

logger = logging.getLogger(__name__)


class ToolManager:
    """
    Centralized tool management for CLI and MCPClient.

    Provides common functionality for tool discovery, validation, and management
    across different discovery methods and template types.
    """

    def __init__(self, backend_type: str = "docker"):
        """
        Initialize tool manager.

        Args:
            backend_type: Deployment backend type (docker, kubernetes, mock)
        """
        self.backend_type = backend_type
        self.tool_discovery = ToolDiscovery()
        self.docker_probe = DockerProbe()
        self._cache = {}

    def discover_tools(
        self,
        template_name: str,
        template_config: Dict[str, Any],
        discovery_method: str = "auto",
        use_cache: bool = True,
        force_refresh: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Discover tools using the specified method.

        Args:
            template_name: Name of the template
            template_config: Template configuration data
            discovery_method: Discovery method ("static", "dynamic", "docker", "auto")
            use_cache: Whether to use cached results
            force_refresh: Force refresh of cached results
            timeout: Timeout for discovery operations

        Returns:
            Discovery result with tools, method, and metadata
        """
        cache_key = f"{template_name}_{discovery_method}_{hash(str(template_config))}"

        # Check cache
        if use_cache and not force_refresh and cache_key in self._cache:
            logger.debug("Using cached tool discovery for %s", template_name)
            return self._cache[cache_key]

        try:
            if discovery_method == "auto":
                result = self._discover_tools_auto(
                    template_name, template_config, timeout
                )
            elif discovery_method == "static":
                result = self._discover_tools_static(template_name, template_config)
            elif discovery_method == "dynamic":
                result = self._discover_tools_dynamic(
                    template_name, template_config, timeout
                )
            elif discovery_method == "docker":
                result = self._discover_tools_from_docker(
                    template_name, template_config, timeout
                )
            else:
                result = {
                    "tools": [],
                    "discovery_method": "unknown",
                    "error": f"Unknown discovery method: {discovery_method}",
                }

            # Cache successful results
            if use_cache and result.get("tools"):
                self._cache[cache_key] = result

            return result

        except Exception as e:
            logger.error("Tool discovery failed for %s: %s", template_name, e)
            return {"tools": [], "discovery_method": discovery_method, "error": str(e)}

    def _discover_tools_auto(
        self, template_name: str, template_config: Dict[str, Any], timeout: int
    ) -> Dict[str, Any]:
        """Auto discovery tries multiple methods in order of preference."""
        # Try static discovery first (fastest)
        result = self._discover_tools_static(template_name, template_config)
        if result.get("tools"):
            return result

        # Try dynamic discovery if template supports it
        tool_discovery_method = template_config.get("tool_discovery")
        if tool_discovery_method == "dynamic":
            result = self._discover_tools_dynamic(
                template_name, template_config, timeout
            )
            if result.get("tools"):
                return result

        # Fall back to Docker discovery
        return self._discover_tools_from_docker(template_name, template_config, timeout)

    def _discover_tools_static(
        self, template_name: str, template_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Discover tools from static template configuration."""
        try:
            # Use existing tool discovery system
            result = self.tool_discovery.discover_tools(
                template_name=template_name,
                template_config=template_config,
                use_cache=True,
                force_refresh=False,
                force_server_discovery=False,
            )

            return {
                "tools": result.get("tools", []),
                "discovery_method": "static",
                "source": result.get("source_file", "template.json"),
                "timestamp": result.get("timestamp"),
            }

        except Exception as e:
            logger.error("Static tool discovery failed for %s: %s", template_name, e)
            return {"tools": [], "discovery_method": "static", "error": str(e)}

    def _discover_tools_dynamic(
        self, template_name: str, template_config: Dict[str, Any], timeout: int
    ) -> Dict[str, Any]:
        """Discover tools from running MCP server."""
        try:
            # Use existing tool discovery system with server discovery
            result = self.tool_discovery.discover_tools(
                template_name=template_name,
                template_config=template_config,
                use_cache=False,
                force_refresh=True,
                force_server_discovery=True,
            )

            return {
                "tools": result.get("tools", []),
                "discovery_method": "dynamic",
                "source": result.get("source_endpoint", "mcp_server"),
                "timestamp": result.get("timestamp"),
            }

        except Exception as e:
            logger.error("Dynamic tool discovery failed for %s: %s", template_name, e)
            return {"tools": [], "discovery_method": "dynamic", "error": str(e)}

    def _discover_tools_from_docker(
        self, template_name: str, template_config: Dict[str, Any], timeout: int
    ) -> Dict[str, Any]:
        """Discover tools by probing Docker image."""
        try:
            docker_image = template_config.get("docker_image")
            docker_tag = template_config.get("docker_tag", "latest")

            if not docker_image:
                return {
                    "tools": [],
                    "discovery_method": "docker",
                    "error": "No Docker image specified in template",
                }

            full_image_name = f"{docker_image}:{docker_tag}"

            # Prepare server arguments from config values
            env_vars = template_config.get("env_vars", {})
            server_args = []

            # Convert environment variables to Docker arguments
            for key, value in env_vars.items():
                server_args.extend(["--env", f"{key}={value}"])

            # Use Docker probe for discovery
            result = self.docker_probe.discover_tools_from_image(
                full_image_name, server_args if server_args else None
            )

            if result:
                return {
                    "tools": result.get("tools", []),
                    "discovery_method": "docker",
                    "source": f"Docker image: {full_image_name}",
                    "timestamp": result.get("timestamp"),
                }
            else:
                return {
                    "tools": [],
                    "discovery_method": "docker",
                    "error": f"Failed to discover tools from {full_image_name}",
                }

        except Exception as e:
            logger.error("Docker tool discovery failed for %s: %s", template_name, e)
            return {"tools": [], "discovery_method": "docker", "error": str(e)}

    def list_tools(
        self,
        template_or_deployment: str,
        discovery_method: str = "auto",
        force_refresh: bool = False,
        timeout: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        List tools for a template or deployment.

        Args:
            template_or_deployment: Template name or deployment ID
            discovery_method: Discovery method to use
            force_refresh: Force refresh of cached results
            timeout: Timeout for discovery operations

        Returns:
            List of tool definitions
        """
        try:
            # For now, assume it's a template name
            # In a full implementation, you'd check if it's a deployment ID first
            from mcp_template.common.template_manager import TemplateManager

            template_manager = TemplateManager()

            template_config = template_manager.get_template(template_or_deployment)
            if not template_config:
                logger.error("Template %s not found", template_or_deployment)
                return []

            result = self.discover_tools(
                template_name=template_or_deployment,
                template_config=template_config,
                discovery_method=discovery_method,
                force_refresh=force_refresh,
                timeout=timeout,
            )

            return result.get("tools", [])

        except Exception as e:
            logger.error("Failed to list tools for %s: %s", template_or_deployment, e)
            return []

    def validate_tool_call(
        self, tool_name: str, tool_args: Dict[str, Any], tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate a tool call against tool definitions.

        Args:
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool call
            tools: List of available tool definitions

        Returns:
            Validation result with success/error information
        """
        result = {"valid": False, "errors": [], "warnings": []}

        # Find the tool definition
        tool_def = None
        for tool in tools:
            if tool.get("name") == tool_name:
                tool_def = tool
                break

        if not tool_def:
            result["errors"].append(f"Tool '{tool_name}' not found")
            return result

        # Validate arguments against tool schema
        input_schema = tool_def.get("inputSchema", {})
        if input_schema:
            # Check required properties
            required_props = input_schema.get("required", [])
            for prop in required_props:
                if prop not in tool_args:
                    result["errors"].append(f"Missing required argument: {prop}")

            # Check argument types
            properties = input_schema.get("properties", {})
            for arg_name, arg_value in tool_args.items():
                if arg_name in properties:
                    prop_schema = properties[arg_name]
                    validation_error = self._validate_tool_argument(
                        arg_name, arg_value, prop_schema
                    )
                    if validation_error:
                        result["errors"].append(validation_error)
                else:
                    result["warnings"].append(f"Unknown argument: {arg_name}")

        result["valid"] = len(result["errors"]) == 0
        return result

    def _validate_tool_argument(
        self, name: str, value: Any, schema: Dict[str, Any]
    ) -> Optional[str]:
        """Validate a single tool argument against its schema."""
        arg_type = schema.get("type", "string")

        # Type validation
        if arg_type == "string" and not isinstance(value, str):
            return f"Argument '{name}' must be a string, got {type(value).__name__}"
        elif arg_type == "integer" and not isinstance(value, int):
            return f"Argument '{name}' must be an integer, got {type(value).__name__}"
        elif arg_type == "number" and not isinstance(value, (int, float)):
            return f"Argument '{name}' must be a number, got {type(value).__name__}"
        elif arg_type == "boolean" and not isinstance(value, bool):
            return f"Argument '{name}' must be a boolean, got {type(value).__name__}"
        elif arg_type == "array" and not isinstance(value, list):
            return f"Argument '{name}' must be an array, got {type(value).__name__}"
        elif arg_type == "object" and not isinstance(value, dict):
            return f"Argument '{name}' must be an object, got {type(value).__name__}"

        return None

    def call_tool(
        self,
        template_name: str,
        tool_name: str,
        tool_args: Dict[str, Any],
        template_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call a tool from a template.

        Args:
            template_name: Name of the template
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool call
            template_config: Optional template configuration

        Returns:
            Tool call result
        """
        try:
            if not template_config:
                from mcp_template.common.template_manager import TemplateManager

                template_manager = TemplateManager()
                template_config = template_manager.get_template(template_name)

                if not template_config:
                    return {
                        "success": False,
                        "error": f"Template '{template_name}' not found",
                    }

            # Get available tools for validation
            tools_result = self.discover_tools(template_name, template_config)
            tools = tools_result.get("tools", [])

            # Validate the tool call
            validation = self.validate_tool_call(tool_name, tool_args, tools)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": "Validation failed",
                    "validation_errors": validation["errors"],
                }

            # Use ToolCaller for the actual call
            # This would integrate with the existing tool calling infrastructure
            return {
                "success": True,
                "result": "Tool call functionality requires integration with existing ToolCaller",
            }

        except Exception as e:
            logger.error("Tool call failed for %s.%s: %s", template_name, tool_name, e)
            return {"success": False, "error": str(e)}

    def get_tool_schema(
        self, tool_name: str, tools: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the schema for a specific tool.

        Args:
            tool_name: Name of the tool
            tools: List of available tool definitions

        Returns:
            Tool schema or None if not found
        """
        for tool in tools:
            if tool.get("name") == tool_name:
                return tool.get("inputSchema", {})
        return None

    def format_tool_for_display(self, tool: Dict[str, Any]) -> Dict[str, str]:
        """
        Format tool information for display purposes.

        Args:
            tool: Tool definition

        Returns:
            Formatted tool information for display
        """
        name = tool.get("name", "Unknown")
        description = tool.get("description", "No description")

        # Format parameters
        input_schema = tool.get("inputSchema", {})
        parameters = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        if parameters:
            param_count = len(parameters)
            required_count = len(required)
            if required_count > 0:
                param_text = f"{param_count} parameters ({required_count} required)"
            else:
                param_text = f"{param_count} parameters"
        else:
            param_text = "No parameters"

        return {
            "name": name,
            "description": description,
            "parameters": param_text,
            "category": tool.get("category", "general"),
        }

    def clear_cache(self) -> None:
        """Clear the tool discovery cache."""
        self._cache.clear()
        logger.debug("Tool discovery cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._cache),
            "cached_templates": list(
                set(key.split("_")[0] for key in self._cache.keys())
            ),
        }
