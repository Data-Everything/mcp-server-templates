"""
Tool Manager - Centralized tool operations.

This module provides a unified interface for tool discovery, management, and operations,
consolidating functionality from CLI and MCPClient.
"""

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional

from mcp_template.backends import get_backend
from mcp_template.core.cache import CacheManager
from mcp_template.core.config_processor import ConfigProcessor
from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.core.template_manager import TemplateManager
from mcp_template.core.tool_caller import ToolCaller
from mcp_template.tools import DockerProbe, KubernetesProbe

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
        self.backend_type = backend_type
        self.template_manager = TemplateManager(backend_type)
        self.tool_caller = ToolCaller(backend_type=backend_type)
        self.cache_manager = CacheManager(max_age_hours=24.0)  # 24-hour cache

    def _get_cache_key(self, template: str) -> str:
        """
        Get cache key
        """

        return f"tools_{re.sub(r'[^a-zA-Z0-9_]', '', template)}"

    def list_tools(
        self,
        template_or_id: str,
        static: bool = True,
        dynamic: bool = True,
        timeout: int = 30,
        force_refresh: bool = False,
        config_values: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        List tools for a template or deployment using priority-based discovery.

        Discovery Priority: cache → running deployments → stdio → http → static
        Returns first successful result with metadata about discovery method and source.

        Args:
            template_or_id: Template name or deployment ID
            static: Are static methods allowed
            dynamic: Are dynamic methods allowed
            timeout: Timeout for operations
            force_refresh: Force refresh, bypassing cache
            config_values: Configuration values for discovery

        Returns:
            Dictionary containing tools and metadata
        """
        # Check if this looks like a deployment ID vs template name
        is_template = not re.match(r".*-\d+(-\d+)?$", template_or_id)
        tools = []
        discovery_method_used = None

        if not force_refresh:
            cached_tools = (self.get_cached_tools(template_or_id) or {}).get("data", {})
            if cached_tools:
                tools = cached_tools.get("tools", [])
                if cached_tools and tools:
                    logger.debug("Returning cached tools")
                    discovery_method_used = cached_tools.get("discovery_method")
                    return {
                        "tools": tools,
                        "count": len(tools),
                        "discovery_method": (
                            cached_tools.get("discovery_method") + " (cached)"
                            if cached_tools.get("discovery_method")
                            else "Cache"
                        ),
                        "source": cached_tools.get("source", "cache"),
                        "template": template_or_id,
                    }

        if not tools:
            try:
                if dynamic:
                    # Use priority-based discovery (full priority chain)
                    discovery_result = self.discover_tools(
                        template_or_id,
                        timeout=timeout,
                        config_values=config_values,
                        is_template=is_template,
                        force_refresh=True,  # Since we already checked cached, it does not make sense to try again
                    )

                    tools = discovery_result.get("tools", [])
                    discovery_method_used = discovery_result.get(
                        "discovery_method", "unknown"
                    )
                    source = discovery_result.get("source", "unknown")

                    # If result was static, reject it since --no-static was specified
                    if discovery_method_used == "static":
                        tools = []
                        discovery_method_used = "none"
                        source = "none"

                else:
                    # Direct method specified - bypass priority system
                    if static:
                        tools = self.discover_tools_static(template_or_id)
                        discovery_method_used = "static"
                        source = "template"
                    elif dynamic:
                        tools = self.discover_tools_dynamic(template_or_id, timeout)
                        discovery_method_used = "http"
                        source = "dynamic"
                    else:
                        logger.warning("Unknown discovery method")
                        tools = self.discover_tools_static(template_or_id)
                        discovery_method_used = "static"
                        source = "template"

                    # Cache non-auto discoveries if successful
                    if tools and dynamic:
                        self._cache_tools(
                            template_or_id, tools, discovery_method_used, source
                        )

            except Exception as e:
                logger.error(f"Tool listing failed for {template_or_id}: {e}")
                return {
                    "tools": [],
                    "count": 0,
                    "discovery_method": "error",
                    "source": "none",
                    "template": template_or_id,
                    "error": str(e),
                }

            normalized_tools = []

            # Normalize tool schemas
            for tool in tools:
                normalized_tools.append(
                    self.normalize_tool_schema(tool, discovery_method_used)
                )

            return {
                "tools": normalized_tools,
                "count": len(normalized_tools),
                "discovery_method": discovery_method_used,
                "source": source,
                "template": template_or_id,
            }

    def discover_tools(
        self,
        template_or_deployment: str,
        timeout: int = 30,
        force_refresh: bool = False,
        config_values: Optional[Dict[str, Any]] = None,
        is_template: bool = True,
    ) -> Dict[str, Any]:
        """
        Discover tools using priority order: cache → running deployments → stdio → http → static.

        Returns first successful discovery with metadata indicating source and method.

        Args:
            template_or_deployment: Template name or deployment ID
            timeout: Timeout for discovery operations
            force_refresh: Force refresh, bypassing cache
            config_values: Configuration values for stdio calls
            is_template: Whether this is a template name vs deployment ID

        Returns:
            Dict with tools list and metadata about discovery method and source
        """

        # 1. PRIORITY: Check cache first (unless force_refresh)
        if not force_refresh:
            cached_tools = self.get_cached_tools(template_or_deployment)
            if cached_tools:
                logger.info(f"✓ Found tools in cache for {template_or_deployment}")
                if "data" in cached_tools:
                    cached_tools = cached_tools["data"]
                return {
                    "tools": cached_tools.get("tools"),
                    "discovery_method": cached_tools.get("discovery_method", "cache"),
                    "source": cached_tools.get("source", "cache"),
                }

        # 2. PRIORITY: Check for running deployments (dynamic discovery via HTTP)
        logger.info(f"Checking for running deployments of {template_or_deployment}")
        try:
            deployment_manager = DeploymentManager(self.backend_type)
            deployments = deployment_manager.find_deployments_by_criteria(
                template_name=template_or_deployment if is_template else None
            )

            # Find first running deployment
            running_deployments = [
                d for d in deployments if d.get("status") == "running"
            ]
            if running_deployments:
                deployment = running_deployments[0]
                tools = self._discover_from_running_deployment(deployment, timeout)
                if tools:
                    logger.info(f"✓ Found {len(tools)} tools from running deployment")
                    self._cache_tools(template_or_deployment, tools, "http", "dynamic")
                    return {
                        "tools": tools,
                        "discovery_method": "http",
                        "source": "dynamic",
                    }
        except Exception as e:
            logger.debug(f"Running deployment check failed: {e}")

        # 3. PRIORITY: Try stdio discovery (if template supports it)
        logger.info(f"Attempting stdio discovery for {template_or_deployment}")
        try:
            tools = self._discover_via_stdio(
                template_or_deployment, timeout, config_values
            )
            if tools:
                logger.info(f"✓ Found {len(tools)} tools via stdio")
                self._cache_tools(template_or_deployment, tools, "stdio", "image")
                return {
                    "tools": tools,
                    "discovery_method": "stdio",
                    "source": "image",
                }
        except Exception as e:
            logger.debug(f"Stdio discovery failed: {e}")

        # 4. PRIORITY: Try HTTP discovery (for deployed templates)
        logger.info(f"Attempting HTTP discovery for {template_or_deployment}")
        try:
            tools = self._discover_via_http(template_or_deployment, timeout)
            if tools:
                logger.info(f"✓ Found {len(tools)} tools via HTTP")
                self._cache_tools(template_or_deployment, tools, "http", "dynamic")
                return {
                    "tools": tools,
                    "discovery_method": "http",
                    "source": "dynamic",
                }
        except Exception as e:
            logger.debug(f"HTTP discovery failed: {e}")

        # 5. PRIORITY: Fall back to static tools from template definition
        logger.info(f"Falling back to static tools for {template_or_deployment}")
        try:
            tools = self.discover_tools_static(template_or_deployment)
            if tools:
                logger.info(f"✓ Found {len(tools)} static tools from template")
                self._cache_tools(template_or_deployment, tools, "static", "template")
                return {
                    "tools": tools,
                    "discovery_method": "static",
                    "source": "template",
                }
        except Exception as e:
            logger.debug(f"Static discovery failed: {e}")

        logger.warning(f"No tools found for {template_or_deployment} using any method")
        return {
            "tools": [],
            "discovery_method": "none",
            "source": "none",
        }

    def _discover_from_running_deployment(
        self, deployment: Dict, timeout: int
    ) -> List[Dict]:
        """Helper method to discover tools from a running deployment via MCP JSON-RPC."""
        try:
            # Use BaseProbe's HTTP discovery methods
            if self.backend_type == "kubernetes":
                probe = KubernetesProbe()
            elif self.backend_type == "docker":
                probe = DockerProbe()
            else:
                raise ValueError("Only docker and kubernetes backends are supported")

            return probe.discover_tools_from_deployment(deployment, timeout)

        except Exception as e:
            logger.debug(f"Failed to discover from running deployment: {e}")
            return []

    def _discover_via_stdio(
        self, template_name: str, timeout: int, config_values: Optional[Dict] = None
    ) -> List[Dict]:
        """Helper method to discover tools via stdio."""
        try:
            # Get template info to check stdio support
            template_info = self.template_manager.get_template_info(template_name)
            if not template_info:
                return []

            # Check if template supports stdio
            transport_config = template_info.get("transport", {})
            supported_transports = transport_config.get("supported", ["http"])

            if "stdio" not in supported_transports:
                return []

            # Get Docker image info
            docker_image = template_info.get("docker_image") or template_info.get(
                "image"
            )
            if not docker_image:
                logger.debug(f"No docker_image specified for template {template_name}")
                return []

            if not len(docker_image.split(":")) > 1:
                docker_image += f":{template_info.get('docker_tag', 'latest')}"

            # Generate environment variables with dummy values for discovery
            env_vars = self._generate_discovery_env_vars(template_info, config_values)

            return self.discover_tools_from_image(
                docker_image, timeout, env_vars=env_vars
            )
        except Exception as e:
            logger.debug(f"Stdio discovery failed: {e}")
        return []

    def _generate_discovery_env_vars(
        self, template_info: Dict[str, Any], config_values: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate environment variables for tool discovery, using dummy values for required config.

        This method reuses the same logic as deployment but generates dummy values
        for required configuration fields when actual values aren't provided.
        """
        # Start with provided config values or empty dict
        discovery_config = config_values.copy() if config_values else {}

        # Get config schema to understand required fields
        config_schema = template_info.get("config_schema", {})
        required_props = config_schema.get("required", [])
        properties = config_schema.get("properties", {})

        # Generate dummy values for required properties that aren't provided
        for prop in required_props:
            if prop not in discovery_config:
                prop_config = properties.get(prop, {})
                discovery_config[prop] = self._generate_dummy_value(prop, prop_config)

        # Use the same configuration processor as deployment to generate env vars
        config_processor = ConfigProcessor()

        # Prepare configuration using the same method as deployment
        final_config = config_processor.prepare_configuration(
            template=template_info,
            config_values=discovery_config,
            env_vars={},  # No additional env vars for discovery
        )

        # Add MCP transport setting
        final_config["MCP_TRANSPORT"] = "stdio"

        return final_config

    def _generate_dummy_value(self, prop_name: str, prop_config: Dict[str, Any]) -> Any:
        """Generate a dummy value for a configuration property based on its type."""
        # Check if there's a default value
        if "default" in prop_config:
            return prop_config["default"]

        # Generate dummy based on type
        prop_type = prop_config.get("type", "string")

        if prop_type == "string":
            # Check for special patterns in the property name or description
            prop_lower = prop_name.lower()
            description = prop_config.get("description", "").lower()

            if any(
                keyword in prop_lower or keyword in description
                for keyword in ["token", "key", "password", "secret", "auth"]
            ):
                return f"dummy_token_for_{prop_name}"
            elif any(
                keyword in prop_lower or keyword in description
                for keyword in ["url", "endpoint", "host"]
            ):
                return f"https://example.com/{prop_name}"
            elif any(
                keyword in prop_lower or keyword in description
                for keyword in ["path", "dir", "directory"]
            ):
                return f"/tmp/{prop_name}"
            elif any(
                keyword in prop_lower or keyword in description
                for keyword in ["email", "mail"]
            ):
                return "dummy@example.com"
            else:
                return f"dummy_{prop_name}_value"

        elif prop_type == "integer":
            # Use reasonable defaults for common integer types
            prop_lower = prop_name.lower()
            if "port" in prop_lower:
                return 8080
            elif "timeout" in prop_lower:
                return 30
            elif "limit" in prop_lower or "max" in prop_lower:
                return 100
            else:
                return 42

        elif prop_type == "number":
            return 42.0

        elif prop_type == "boolean":
            # Default to True for most boolean flags
            return True

        elif prop_type == "array":
            # Generate a simple array with one dummy element
            items_config = prop_config.get("items", {})
            if items_config:
                dummy_item = self._generate_dummy_value(
                    f"{prop_name}_item", items_config
                )
                return [dummy_item]
            else:
                return [f"dummy_{prop_name}_item"]

        elif prop_type == "object":
            # Generate a simple object
            return {f"dummy_{prop_name}_key": f"dummy_{prop_name}_value"}

        else:
            # Fallback for unknown types
            return f"dummy_{prop_name}_value"

    def _discover_via_http(
        self, template_or_deployment: str, timeout: int
    ) -> List[Dict]:
        """Helper method to discover tools via MCP JSON-RPC (for already deployed services)."""
        try:
            # Get deployment manager to find running deployments
            deployment_manager = DeploymentManager(self.backend_type)

            # Find deployments for this template
            deployments = deployment_manager.find_deployments_by_criteria(
                template_name=template_or_deployment
            )

            if not deployments:
                return []

            # Use the first running deployment
            deployment = deployments[0]

            # Use BaseProbe's HTTP discovery methods
            if self.backend_type == "kubernetes":
                probe = KubernetesProbe()
            else:
                probe = DockerProbe()

            return probe.discover_tools_from_deployment(deployment, timeout)

        except Exception as e:
            logger.debug(
                f"MCP JSON-RPC discovery failed for {template_or_deployment}: {e}"
            )
            return []

    def _cache_tools(
        self, template_name: str, tools: List[Dict], method: str, source: str
    ):
        """Helper method to cache discovered tools with metadata."""
        cache_key = self._get_cache_key(template_name)
        cache_data = {
            "tools": tools,
            "discovery_method": method,  # stdio, http, static
            "source": source,  # dynamic, image, template
            "template": template_name,
            "timestamp": time.time(),
        }
        self.cache_manager.set(cache_key, cache_data)

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

    def discover_tools_dynamic(
        self, template_or_deployment_id: str, timeout: int
    ) -> List[Dict]:
        """
        Discover tools from running server.

        Args:
            template_or_deployment_id: Template name or deployment identifier
            timeout: Timeout for connection

        Returns:
            List of dynamic tool definitions
        """
        try:
            # First try to get deployment info directly (if it's a deployment ID)
            deployment_info = self.backend.get_deployment_info(
                template_or_deployment_id
            )

            # If not found, try to find deployment by template name
            if not deployment_info:
                deployment_manager = DeploymentManager(self.backend_type)
                deployments = deployment_manager.find_deployments_by_criteria(
                    template_name=template_or_deployment_id, status="running"
                )
                if deployments:
                    # Use the first running deployment
                    deployment = deployments[0]
                    deployment_info = deployment

            if not deployment_info:
                logger.warning(
                    f"No running deployment found for {template_or_deployment_id}"
                )
                return []

            # Try HTTP discovery first
            tools = self._discover_from_running_deployment(deployment_info, timeout)
            if tools:
                return tools

            # If HTTP fails, try stdio discovery as fallback
            logger.info(
                f"HTTP discovery failed, trying stdio for {template_or_deployment_id}"
            )
            try:
                stdio_tools = self._discover_via_stdio(
                    template_or_deployment_id, timeout
                )
                if stdio_tools:
                    return stdio_tools
            except Exception as e:
                logger.debug(f"Stdio fallback failed: {e}")

            logger.warning(
                f"Both HTTP and stdio discovery failed for {template_or_deployment_id}"
            )
            return []

        except Exception as e:
            logger.error(
                f"Failed to discover dynamic tools for {template_or_deployment_id}: {e}"
            )
            return []

    def discover_tools_from_image(
        self, image: str, timeout: int, env_vars: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Discover tools by probing container image using the appropriate backend.

        Args:
            image: Container image name
            timeout: Timeout for probe operation
            env_vars: Environment variables to pass to container

        Returns:
            List of tool definitions from image
        """
        try:
            if self.backend_type == "kubernetes":
                probe = KubernetesProbe()
            else:
                probe = DockerProbe()

            result = probe.discover_tools_from_image(
                image_name=image, server_args=None, env_vars=env_vars, timeout=timeout
            )

            # Both probes return a dict with tools, extract the tools list
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
            # Convert Pydantic model to dict if needed (from FastMCP client)
            if hasattr(tool_data, "model_dump"):
                tool_dict = tool_data.model_dump()
            elif hasattr(tool_data, "dict"):
                tool_dict = tool_data.dict()
            else:
                tool_dict = tool_data

            normalized = {
                "name": tool_dict.get("name", "unknown"),
                "description": tool_dict.get("description", ""),
                "source": source,
            }

            # Handle input schema
            input_schema = (
                tool_dict.get("inputSchema") or tool_dict.get("input_schema") or {}
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
            for key, value in tool_dict.items():
                if key not in ["name", "description", "inputSchema", "input_schema"]:
                    normalized[key] = value

            return normalized

        except Exception as e:
            logger.error(f"Failed to normalize tool schema: {e}")
            # Fallback handling for Pydantic objects
            try:
                if hasattr(tool_data, "model_dump"):
                    tool_dict = tool_data.model_dump()
                elif hasattr(tool_data, "dict"):
                    tool_dict = tool_data.dict()
                else:
                    tool_dict = tool_data

                return {
                    "name": tool_dict.get("name", "unknown"),
                    "description": tool_dict.get("description", ""),
                    "source": source,
                    "inputSchema": {},
                    "parameters": [],
                    "error": str(e),
                }
            except:
                return {
                    "name": "unknown",
                    "description": "",
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
            cache_key = self._get_cache_key(template_name)
            self.cache_manager.delete(cache_key)
        else:
            # Clear entire cache
            self.cache_manager.clear()

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
        cache_key = self._get_cache_key(template_or_id)
        return self.cache_manager.get(cache_key) or None

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
