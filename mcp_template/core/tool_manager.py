"""
Tool Manager - Centralized tool operations.

This module provides a unified interface for tool discovery, management, and operations,
consolidating functionality from CLI and MCPClient.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from mcp_template.backends import get_backend
from mcp_template.core.cache import CacheManager
from mcp_template.core.template_manager import TemplateManager
from mcp_template.core.tool_caller import ToolCaller

logger = logging.getLogger(__name__)


class ToolManager:
    """
    Centralized tool management operations.

    Provides unified interface for tool discovery, management, and operations
    that can be shared between CLI and MCPClient implementations.
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize the tool manager."""
        self.backend = get_backend(backend_type)
        self.template_manager = TemplateManager(backend_type)
        self.tool_caller = ToolCaller(backend_type=backend_type)
        self.cache_manager = CacheManager(max_age_hours=24.0)  # 24-hour cache
        self._cache = {}  # Keep in-memory cache for session

    def list_tools(
        self,
        template_or_id: str,
        discovery_method: str = "auto",
        force_refresh: bool = False,
        timeout: int = 30,
        config_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List tools for a template or deployment using the enhanced discovery flow.

        Args:
            template_or_id: Template name or deployment ID
            discovery_method: How to discover tools (static, dynamic, image, auto)
            force_refresh: Whether to force refresh cache
            timeout: Timeout for discovery operations
            config_values: Configuration values for stdio calls

        Returns:
            Dictionary with tools and metadata:
            {
                "tools": [list of tool definitions],
                "discovery_method": "static|stdio|http|cache",
                "metadata": {
                    "source": "...",
                    "timestamp": "...",
                    "cached": bool
                }
            }
        """
        import time

        try:
            actual_discovery_method = discovery_method
            cached = False

            if discovery_method == "auto":
                # Use the enhanced discover_tools method that implements user's flow
                tools = self.discover_tools(
                    template_or_id,
                    timeout=timeout,
                    force_refresh=force_refresh,
                    config_values=config_values,
                )
                # Try to determine the actual discovery method used
                actual_discovery_method = self._determine_actual_discovery_method(
                    template_or_id, tools
                )
            else:
                # Handle specific discovery methods
                cache_key = f"{template_or_id}:{discovery_method}"

                # Try persistent cache first (24-hour expiry)
                if not force_refresh:
                    cached_data = self.cache_manager.get(cache_key)
                    if cached_data:
                        tools = cached_data.get("tools", [])
                        cached = True
                        actual_discovery_method = cached_data.get(
                            "discovery_method", discovery_method
                        )
                    elif cache_key in self._cache:
                        # Fallback to in-memory cache
                        tools = self._cache[cache_key]
                        cached = True
                        actual_discovery_method = discovery_method

                if not cached:
                    if discovery_method == "static":
                        tools = self.discover_tools_static(template_or_id)
                        actual_discovery_method = "static"
                    elif discovery_method == "dynamic":
                        tools = self.discover_tools_dynamic(template_or_id, timeout)
                        actual_discovery_method = "http"  # dynamic usually means HTTP
                    elif discovery_method == "image":
                        tools = self.discover_tools_from_image(template_or_id, timeout)
                        actual_discovery_method = "stdio"  # image discovery uses stdio
                    else:
                        logger.warning(f"Unknown discovery method: {discovery_method}")
                        tools = self.discover_tools_static(template_or_id)
                        actual_discovery_method = "static"

                    # Cache the results in both caches
                    self._cache[cache_key] = tools
                    if tools:  # Only cache non-empty results in persistent cache
                        cache_data = {
                            "tools": tools,
                            "discovery_method": actual_discovery_method,
                            "template": template_or_id,
                        }
                        self.cache_manager.set(cache_key, cache_data)

            # Normalize tool schemas
            normalized_tools = [
                self.normalize_tool_schema(tool, actual_discovery_method)
                for tool in tools
            ]

            # Build the enhanced response
            return {
                "tools": normalized_tools,
                "discovery_method": actual_discovery_method,
                "metadata": {
                    "source": template_or_id,
                    "timestamp": time.time(),
                    "cached": cached,
                    "force_refresh": force_refresh,
                    "requested_method": discovery_method,
                },
            }

        except Exception as e:
            logger.error(f"Failed to list tools for {template_or_id}: {e}")
            return {
                "tools": [],
                "discovery_method": "error",
                "metadata": {
                    "source": template_or_id,
                    "timestamp": time.time(),
                    "cached": False,
                    "error": str(e),
                },
            }

    def discover_tools(
        self,
        template_or_deployment: str,
        timeout: int = 30,
        force_refresh: bool = False,
        config_values: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """
        Discover tools using the best available method with caching.

        Implements the user's specified discovery flow:
        1. Check for running server (HTTP) first
        2. Fallback to stdio if template supports it
        3. Cache results if successful
        4. Support force_refresh to bypass cache
        5. Mock required config values for stdio calls

        Args:
            template_or_deployment: Template name or deployment ID
            timeout: Timeout for discovery operations
            force_refresh: Force refresh, bypassing cache
            config_values: Configuration values for stdio calls

        Returns:
            List of discovered tools
        """
        cache_key = f"tools_{template_or_deployment}"

        # Check cache first unless force_refresh
        if not force_refresh:
            cached_tools = self.get_cached_tools(template_or_deployment)
            if cached_tools:
                logger.info(f"Returning cached tools for {template_or_deployment}")
                return cached_tools

        try:
            # Initialize tool caller
            if not hasattr(self, "tool_caller") or self.tool_caller is None:
                self.tool_caller = ToolCaller()

            # First try: Check for running server (HTTP)
            try:
                # Get deployment info
                deployment_info = self.backend.get_deployment_info(
                    template_or_deployment
                )
                if not deployment_info:
                    # Try to find deployment by template name
                    from mcp_template.core.deployment_manager import DeploymentManager

                    deployment_manager = DeploymentManager(
                        "docker"
                    )  # Use "docker" as default backend type
                    deployments = deployment_manager.find_deployments_by_criteria(
                        template_name=template_or_deployment
                    )
                    # Find the first running deployment
                    running_deployments = [
                        d for d in deployments if d.get("status") == "running"
                    ]
                    if running_deployments:
                        deployment_info = running_deployments[0]

                # If we found a running deployment, get tools via HTTP
                if deployment_info:
                    # Extract port information and construct endpoint
                    ports = deployment_info.get("ports", "")
                    endpoint = None
                    transport = "http"

                    # Parse port mapping like "7071->7071" to extract external port
                    if "->" in ports:
                        external_port = ports.split("->")[0]
                        endpoint = f"http://127.0.0.1:{external_port}/mcp/"
                    elif deployment_info.get("endpoint"):
                        endpoint = deployment_info.get("endpoint")

                    if endpoint:
                        logger.info(
                            f"Discovering tools via HTTP for {template_or_deployment} at {endpoint}"
                        )
                        tools = self.tool_caller.list_tools_from_server(
                            endpoint, transport, timeout
                        )
                        if tools:
                            # Cache the successful result
                            self._cache[cache_key] = tools
                            logger.info(
                                f"Cached {len(tools)} tools from HTTP for {template_or_deployment}"
                            )
                            return tools

            except Exception as e:
                logger.debug(f"HTTP tool discovery failed, trying stdio: {e}")

            # Second try: Use stdio if template supports it
            try:
                # Get template info to check stdio support
                template_info = self.template_manager.get_template_info(
                    template_or_deployment
                )
                if not template_info:
                    logger.warning(f"Template '{template_or_deployment}' not found")
                    return []

                # Check if template supports stdio
                transport_config = template_info.get("transport", {})
                supported_transports = transport_config.get("supported", ["http"])
                default_transport = transport_config.get("default", "http")

                if "stdio" in supported_transports or default_transport == "stdio":
                    logger.info(
                        f"Discovering tools via stdio for {template_or_deployment}"
                    )

                    # Mock required config values if not provided
                    if config_values is None:
                        config_values = {}

                    # Auto-generate mock values for required config
                    config_schema = template_info.get("config_schema", {})
                    required_props = config_schema.get("required", [])
                    properties = config_schema.get("properties", {})

                    for prop in required_props:
                        if prop not in config_values:
                            prop_config = properties.get(prop, {})
                            # Mock value based on type or use a generic mock
                            prop_type = prop_config.get("type", "string")
                            if prop_type == "string":
                                config_values[prop] = f"mock_{prop}_value"
                            elif prop_type == "integer":
                                config_values[prop] = 8080
                            elif prop_type == "boolean":
                                config_values[prop] = True
                            else:
                                config_values[prop] = f"mock_{prop}_value"

                    # Use the existing discover_tools_from_image method which uses stdio
                    image = template_info.get("docker_image")
                    if image:
                        tools = self.discover_tools_from_image(image, timeout)
                        if tools:
                            # Cache the successful result
                            self._cache[cache_key] = tools
                            logger.info(
                                f"Cached {len(tools)} tools from stdio for {template_or_deployment}"
                            )
                            return tools

                else:
                    logger.warning(
                        f"Template '{template_or_deployment}' does not support stdio transport and no running server found"
                    )

            except Exception as e:
                logger.error(f"Stdio tool discovery failed: {e}")

            # Fallback to static discovery
            logger.info(
                f"Falling back to static tool discovery for {template_or_deployment}"
            )
            tools = self.discover_tools_static(template_or_deployment)
            if tools:
                # Cache the successful result
                self._cache[cache_key] = tools
                logger.info(
                    f"Cached {len(tools)} tools from static discovery for {template_or_deployment}"
                )
                return tools

            logger.warning(f"No tools discovered for {template_or_deployment}")
            return []

        except Exception as e:
            logger.error(f"Tool discovery failed for {template_or_deployment}: {e}")
            return []

    def discover_tools_static(self, template_id: str) -> List[Dict]:
        """
        Discover tools from template files.

        Args:
            template_id: The template identifier

        Returns:
            List of static tool definitions
        """
        try:
            # Get tools from template manager
            tools = self.template_manager.get_template_tools(template_id)

            # Also check for dedicated tools.json file
            template_path = self.template_manager.get_template_path(template_id)
            if template_path:
                tools_file = template_path / "tools.json"
                if tools_file.exists():
                    with open(tools_file, "r") as f:
                        file_tools = json.load(f)
                        if isinstance(file_tools, list):
                            tools.extend(file_tools)
                        elif isinstance(file_tools, dict) and "tools" in file_tools:
                            tools.extend(file_tools["tools"])

            return tools

        except Exception as e:
            logger.error(f"Failed to discover static tools for {template_id}: {e}")
            return []

    def discover_tools_dynamic(self, deployment_id: str, timeout: int) -> List[Dict]:
        """
        Discover tools from running server.

        Args:
            deployment_id: The deployment identifier
            timeout: Timeout for connection

        Returns:
            List of dynamic tool definitions
        """
        try:
            # Get deployment info to find connection details
            deployment_info = self.backend.get_deployment_info(deployment_id)
            if not deployment_info:
                logger.warning(
                    f"Deployment {deployment_id} not found for dynamic tool discovery"
                )
                return []

            # Extract connection details
            endpoint = deployment_info.get("endpoint")
            transport = deployment_info.get("transport", "http")

            if not endpoint:
                logger.warning(f"No endpoint found for deployment {deployment_id}")
                return []

            # Connect and list tools
            tools = self.tool_caller.list_tools_from_server(
                endpoint, transport, timeout
            )
            return tools

        except Exception as e:
            logger.error(f"Failed to discover dynamic tools for {deployment_id}: {e}")
            return []

    def discover_tools_from_image(self, image: str, timeout: int) -> List[Dict]:
        """
        Discover tools by probing Docker image.

        Args:
            image: Docker image name
            timeout: Timeout for probe operation

        Returns:
            List of tool definitions from image
        """
        try:
            # Import here to avoid circular imports
            from mcp_template.tools import DockerProbe

            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image(image, timeout)

            # DockerProbe returns a dict with tools, extract the tools list
            if result and isinstance(result, dict) and "tools" in result:
                tools = result["tools"]
                if isinstance(tools, list):
                    return tools

            return []

        except Exception as e:
            logger.error(f"Failed to discover tools from image {image}: {e}")
            return []

    def normalize_tool_schema(self, tool_data: Dict, source: str) -> Dict:
        """
        Normalize tool schemas from different sources.

        Args:
            tool_data: Raw tool data
            source: Source of the tool data (static, dynamic, image)

        Returns:
            Normalized tool definition
        """
        try:
            normalized = {
                "name": tool_data.get("name", "unknown"),
                "description": tool_data.get("description", ""),
                "source": source,
            }

            # Handle input schema
            input_schema = (
                tool_data.get("inputSchema") or tool_data.get("input_schema") or {}
            )
            if input_schema:
                normalized["inputSchema"] = input_schema

                # Extract parameter summary for display
                parameters = []
                properties = input_schema.get("properties", {})
                required = input_schema.get("required", [])

                for param_name, param_def in properties.items():
                    param_type = param_def.get("type", "unknown")
                    is_required = param_name in required
                    param_desc = param_def.get("description", "")

                    param_summary = f"{param_name}"
                    if param_type != "unknown":
                        param_summary += f" ({param_type})"
                    if not is_required:
                        param_summary += " (optional)"
                    if param_desc:
                        param_summary += f" - {param_desc}"

                    parameters.append(
                        {
                            "name": param_name,
                            "type": param_type,
                            "required": is_required,
                            "description": param_desc,
                            "summary": param_summary,
                        }
                    )

                normalized["parameters"] = parameters
            else:
                normalized["inputSchema"] = {}
                normalized["parameters"] = []

            # Add any additional metadata
            for key, value in tool_data.items():
                if key not in ["name", "description", "inputSchema", "input_schema"]:
                    normalized[key] = value

            return normalized

        except Exception as e:
            logger.error(f"Failed to normalize tool schema: {e}")
            return {
                "name": tool_data.get("name", "unknown"),
                "description": tool_data.get("description", ""),
                "source": source,
                "inputSchema": {},
                "parameters": [],
                "error": str(e),
            }

    def validate_tool_definition(self, tool: Dict) -> bool:
        """
        Validate tool definition structure.

        Args:
            tool: Tool definition to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if "name" not in tool:
                return False

            # Validate input schema if present
            input_schema = tool.get("inputSchema", {})
            if input_schema:
                # Basic schema validation
                if not isinstance(input_schema, dict):
                    return False

                # Check properties structure
                properties = input_schema.get("properties", {})
                if properties and not isinstance(properties, dict):
                    return False

                # Check required array
                required = input_schema.get("required", [])
                if required and not isinstance(required, list):
                    return False

            return True

        except Exception as e:
            logger.error(f"Tool validation failed: {e}")
            return False

    def call_tool(
        self,
        template_or_deployment: str,
        tool_name: str,
        parameters: Dict[str, Any],
        config_values: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        pull_image: bool = True,
        force_stdio: bool = False,
    ) -> Dict[str, Any]:
        """
        Call a tool using the best available transport.

        This method implements the user's specified discovery flow:
        1. Check for running server (HTTP) first
        2. Fallback to stdio if template supports it
        3. Cache results if successful
        4. Mock required config values for stdio calls

        Args:
            template_or_deployment: Template name or deployment ID
            tool_name: Name of the tool to call
            parameters: Tool parameters
            config_values: Configuration values for stdio calls
            timeout: Timeout for the call
            pull_image: Whether to pull image for stdio calls
            force_stdio: Force stdio transport even if HTTP is available

        Returns:
            Tool call result with success/error information
        """
        try:
            self.tool_caller = ToolCaller()

            # First try: Check for running server (HTTP)
            if not force_stdio:
                try:
                    # Get deployment info
                    deployment_info = self.backend.get_deployment_info(
                        template_or_deployment
                    )
                    if not deployment_info:
                        # Try to find deployment by template name
                        from mcp_template.core.deployment_manager import (
                            DeploymentManager,
                        )

                        deployment_manager = DeploymentManager(
                            self.backend.backend_type
                        )
                        deployments = deployment_manager.find_deployments_by_criteria(
                            template_name=template_or_deployment
                        )
                        # Find the first running deployment
                        running_deployments = [
                            d for d in deployments if d.get("status") == "running"
                        ]
                        if running_deployments:
                            deployment_info = running_deployments[0]

                    # If we found a running deployment, construct HTTP endpoint and use it
                    if deployment_info:
                        # Extract port information and construct endpoint
                        ports = deployment_info.get("ports", "")
                        endpoint = None
                        transport = "http"

                        # Parse port mapping like "7071->7071" to extract external port
                        if "->" in ports:
                            external_port = ports.split("->")[0]
                            endpoint = f"http://127.0.0.1:{external_port}/mcp/"
                        elif deployment_info.get("endpoint"):
                            endpoint = deployment_info.get("endpoint")

                        if endpoint:
                            logger.info(
                                f"Using HTTP transport for {template_or_deployment} at {endpoint}"
                            )
                            result = self.tool_caller.call_tool(
                                endpoint, transport, tool_name, parameters, timeout
                            )
                            return result

                except Exception as e:
                    logger.debug(f"HTTP transport failed, trying stdio: {e}")

            # Second try: Use stdio if template supports it
            try:
                # Get template info to check stdio support
                template_info = self.template_manager.get_template_info(
                    template_or_deployment
                )
                if not template_info:
                    return {
                        "success": False,
                        "error": f"Template '{template_or_deployment}' not found",
                    }

                # Check if template supports stdio
                transport_config = template_info.get("transport", {})
                supported_transports = transport_config.get("supported", ["http"])
                default_transport = transport_config.get("default", "http")

                if "stdio" in supported_transports or default_transport == "stdio":
                    logger.info(f"Using stdio transport for {template_or_deployment}")

                    # Mock required config values if not provided
                    if config_values is None:
                        config_values = {}

                    # Auto-generate mock values for required config
                    config_schema = template_info.get("config_schema", {})
                    required_props = config_schema.get("required", [])
                    properties = config_schema.get("properties", {})

                    for prop in required_props:
                        if prop not in config_values:
                            prop_config = properties.get(prop, {})
                            # Mock value based on type or use a generic mock
                            prop_type = prop_config.get("type", "string")
                            if prop_type == "string":
                                config_values[prop] = f"mock_{prop}_value"
                            elif prop_type == "integer":
                                config_values[prop] = 8080
                            elif prop_type == "boolean":
                                config_values[prop] = True
                            else:
                                config_values[prop] = f"mock_{prop}_value"

                    # Call tool via stdio
                    result = self.tool_caller.call_tool_stdio(
                        template_or_deployment,
                        tool_name,
                        parameters,
                        template_info,
                        config_values=config_values,
                        pull_image=pull_image,
                    )

                    # Convert ToolCallResult to dict format
                    if hasattr(result, "success"):
                        return {
                            "success": result.success,
                            "result": result.result if result.success else None,
                            "error": (
                                result.error_message if not result.success else None
                            ),
                        }
                    else:
                        return result

                else:
                    return {
                        "success": False,
                        "error": f"Template '{template_or_deployment}' does not support stdio transport and no running server found",
                    }

            except Exception as e:
                logger.error(f"Stdio transport failed: {e}")
                return {
                    "success": False,
                    "error": f"Failed to call tool via stdio: {e}",
                }

        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    def _discover_tools_auto(self, template_or_id: str, timeout: int) -> List[Dict]:
        """
        Automatically discover tools using the best available method.

        Args:
            template_or_id: Template name or deployment ID
            timeout: Timeout for discovery

        Returns:
            List of discovered tools
        """
        # Try dynamic discovery first (from running deployment)
        try:
            tools = self.discover_tools_dynamic(template_or_id, timeout)
            if tools:
                return tools
        except Exception:
            pass

        # Try static discovery (from template files)
        try:
            tools = self.discover_tools_static(template_or_id)
            if tools:
                return tools
        except Exception:
            pass

        # Try image-based discovery as last resort
        try:
            # Get template info to find image
            template_info = self.template_manager.get_template_info(template_or_id)
            if template_info and "docker_image" in template_info:
                image = template_info["docker_image"]
                tools = self.discover_tools_from_image(image, timeout)
                if tools:
                    return tools
        except Exception:
            pass

        # No tools found
        return []

    def clear_cache(self, template_name: Optional[str] = None):
        """
        Clear the tool discovery cache.

        Args:
            template_name: Optional template name to clear specific cache entry.
                          If None, clears entire cache.
        """
        if template_name:
            # Clear cache for specific template
            keys_to_remove = [key for key in self._cache.keys() if template_name in key]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            # Clear entire cache
            self._cache = {}

    def get_cached_tools(
        self, template_or_id: str, discovery_method: str = "auto"
    ) -> Optional[List[Dict]]:
        """
        Get cached tools if available.

        Args:
            template_or_id: Template name or deployment ID
            discovery_method: Discovery method used

        Returns:
            Cached tools or None if not cached
        """
        cache_key = f"{template_or_id}:{discovery_method}"
        return self._cache.get(cache_key)

    def _determine_actual_discovery_method(
        self, template_or_id: str, tools: List[Dict]
    ) -> str:
        """
        Determine the actual discovery method used based on template/deployment.

        Args:
            template_or_id: Template name or deployment ID
            tools: The discovered tools (for context)

        Returns:
            The actual discovery method used: static, stdio, http, or cache
        """
        try:
            # Check if it's a deployment ID (contains hyphens and numbers)
            if "-" in template_or_id and any(c.isdigit() for c in template_or_id):
                # Try to get deployment info to determine transport
                try:
                    deployment_info = self.backend.get_deployment_info(template_or_id)
                    transport = deployment_info.get("transport", "unknown")
                    if transport == "http":
                        return "http"
                    elif transport == "stdio":
                        return "stdio"
                except Exception:
                    pass

            # Check if we have running deployment for this template
            try:
                deployments = self.backend.list_deployments()
                template_deployments = [
                    d
                    for d in deployments
                    if d.get("template") == template_or_id
                    or d.get("Template") == template_or_id
                ]
                if template_deployments:
                    # Check the transport of the first running deployment
                    for deployment in template_deployments:
                        if deployment.get("status") == "running":
                            endpoint = deployment.get("endpoint", "")
                            if endpoint.startswith("http"):
                                return "http"
                            else:
                                return "stdio"
                    return "http"  # Default for deployments
            except Exception:
                pass

            # If no deployment found, it was likely static discovery
            return "static"

        except Exception as e:
            logger.debug(f"Could not determine discovery method: {e}")
            return "static"  # Default fallback

    def list_tools_legacy(
        self,
        template_or_id: str,
        discovery_method: str = "auto",
        force_refresh: bool = False,
        timeout: int = 30,
        config_values: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Legacy method that returns just the tools list for backward compatibility.

        This method is deprecated. Use list_tools() instead which returns metadata.
        """
        result = self.list_tools(
            template_or_id=template_or_id,
            discovery_method=discovery_method,
            force_refresh=force_refresh,
            timeout=timeout,
            config_values=config_values,
        )
        return result.get("tools", [])
