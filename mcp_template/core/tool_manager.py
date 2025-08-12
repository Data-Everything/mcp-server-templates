"""
Tool Manager - Centralized tool operations.

This module provides a unified interface for tool discovery, management, and operations,
consolidating functionality from CLI and MCPClient.
"""

import logging
import json
from typing import Any, Dict, List, Optional

from mcp_template.backends import get_backend
from mcp_template.core.template_manager import TemplateManager

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
        self._cache = {}

    def list_tools(self,
                   template_or_id: str,
                   discovery_method: str = "auto",
                   force_refresh: bool = False,
                   timeout: int = 30) -> List[Dict[str, Any]]:
        """
        List tools for a template or deployment.
        
        Args:
            template_or_id: Template name or deployment ID
            discovery_method: How to discover tools (static, dynamic, image, auto)
            force_refresh: Whether to force refresh cache
            timeout: Timeout for discovery operations
            
        Returns:
            List of tool definitions
        """
        try:
            # Check cache first
            cache_key = f"{template_or_id}:{discovery_method}"
            if not force_refresh and cache_key in self._cache:
                return self._cache[cache_key]
            
            tools = []
            
            if discovery_method == "auto":
                # Try different methods in order of preference
                tools = self._discover_tools_auto(template_or_id, timeout)
            elif discovery_method == "static":
                tools = self.discover_tools_static(template_or_id)
            elif discovery_method == "dynamic":
                tools = self.discover_tools_dynamic(template_or_id, timeout)
            elif discovery_method == "image":
                tools = self.discover_tools_from_image(template_or_id, timeout)
            else:
                logger.warning(f"Unknown discovery method: {discovery_method}")
                tools = self.discover_tools_static(template_or_id)
            
            # Normalize tool schemas
            normalized_tools = [
                self.normalize_tool_schema(tool, discovery_method) 
                for tool in tools
            ]
            
            # Cache the results
            self._cache[cache_key] = normalized_tools
            
            return normalized_tools
            
        except Exception as e:
            logger.error(f"Failed to list tools for {template_or_id}: {e}")
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
                    with open(tools_file, 'r') as f:
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
            # Import here to avoid circular imports
            from mcp_template.core.tool_caller import ToolCaller
            
            tool_caller = ToolCaller()
            
            # Get deployment info to find connection details
            deployment_info = self.backend.get_deployment_info(deployment_id)
            if not deployment_info:
                logger.warning(f"Deployment {deployment_id} not found for dynamic tool discovery")
                return []
            
            # Extract connection details
            endpoint = deployment_info.get("endpoint")
            transport = deployment_info.get("transport", "http")
            
            if not endpoint:
                logger.warning(f"No endpoint found for deployment {deployment_id}")
                return []
            
            # Connect and list tools
            tools = tool_caller.list_tools_from_server(endpoint, transport, timeout)
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
            tools = docker_probe.discover_tools_from_image(image, timeout)
            return tools
            
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
                "source": source
            }
            
            # Handle input schema
            input_schema = tool_data.get("inputSchema") or tool_data.get("input_schema") or {}
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
                        
                    parameters.append({
                        "name": param_name,
                        "type": param_type,
                        "required": is_required,
                        "description": param_desc,
                        "summary": param_summary
                    })
                
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
                "error": str(e)
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

    def call_tool(self,
                  template_or_deployment: str,
                  tool_name: str,
                  parameters: Dict[str, Any],
                  timeout: int = 30) -> Dict[str, Any]:
        """
        Call a tool on a running server.
        
        Args:
            template_or_deployment: Template name or deployment ID
            tool_name: Name of the tool to call
            parameters: Tool parameters
            timeout: Timeout for the call
            
        Returns:
            Tool call result
        """
        try:
            # Import here to avoid circular imports
            from mcp_template.core.tool_caller import ToolCaller
            
            tool_caller = ToolCaller()
            
            # Get deployment info
            deployment_info = self.backend.get_deployment_info(template_or_deployment)
            if not deployment_info:
                # Try to find deployment by template name
                from mcp_template.core.deployment_manager import DeploymentManager
                deployment_manager = DeploymentManager(self.backend.backend_type)
                deployments = deployment_manager.find_deployments_by_criteria(
                    template_name=template_or_deployment
                )
                if not deployments:
                    return {
                        "success": False,
                        "error": f"No deployment found for {template_or_deployment}"
                    }
                deployment_info = deployments[0]
            
            # Extract connection details
            endpoint = deployment_info.get("endpoint")
            transport = deployment_info.get("transport", "http")
            
            if not endpoint:
                return {
                    "success": False,
                    "error": f"No endpoint found for {template_or_deployment}"
                }
            
            # Call the tool
            result = tool_caller.call_tool(endpoint, transport, tool_name, parameters, timeout)
            return result
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

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

    def clear_cache(self):
        """Clear the tool discovery cache."""
        self._cache = {}

    def get_cached_tools(self, template_or_id: str, discovery_method: str = "auto") -> Optional[List[Dict]]:
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
