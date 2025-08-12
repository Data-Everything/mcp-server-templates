"""
Refactored MCP Client using common modules.

This module provides the MCPClient interface that uses the common modules for
shared functionality, keeping client-specific logic focused on programmatic
access and data transformation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp_template.common import (
    TemplateManager,
    DeploymentManager,
    ConfigManager,
    ToolManager,
)
from mcp_template.common.deployment_manager import DeploymentOptions

logger = logging.getLogger(__name__)


class RefactoredMCPClient:
    """
    Refactored MCP Client that uses common modules for shared functionality.
    
    This client focuses on:
    - Programmatic interface design
    - Data structure consistency
    - Error handling for integration
    - Async operation support where appropriate
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize the refactored MCP client."""
        self.backend_type = backend_type
        self.template_manager = TemplateManager(backend_type)
        self.deployment_manager = DeploymentManager(backend_type)
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager(backend_type)

    def list_templates(self, include_deployed_status: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        List all available templates.
        
        Args:
            include_deployed_status: Whether to include deployment status
            
        Returns:
            Dictionary mapping template names to template metadata
        """
        try:
            return self.template_manager.list_templates(
                include_deployed_status=include_deployed_status
            )
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return {}

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific template.
        
        Args:
            template_id: The template identifier
            
        Returns:
            Template metadata dictionary or None if not found
        """
        try:
            return self.template_manager.get_template_info(template_id)
        except Exception as e:
            logger.error(f"Failed to get template info for {template_id}: {e}")
            return None

    def validate_template(self, template_id: str) -> bool:
        """
        Validate that a template exists and is properly structured.
        
        Args:
            template_id: The template identifier
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            return self.template_manager.validate_template(template_id)
        except Exception as e:
            logger.error(f"Failed to validate template {template_id}: {e}")
            return False

    def search_templates(self, query: str) -> Dict[str, Dict[str, Any]]:
        """
        Search templates by name, description, or tags.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary of matching templates
        """
        try:
            return self.template_manager.search_templates(query)
        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return {}

    def start_server(self, 
                    template_id: str, 
                    config: Optional[Dict[str, Any]] = None, 
                    name: Optional[str] = None,
                    transport: Optional[str] = None,
                    port: int = 7071,
                    timeout: int = 300) -> Dict[str, Any]:
        """
        Start a server instance from a template.
        
        Args:
            template_id: The template to deploy
            config: Configuration overrides
            name: Custom deployment name
            transport: Transport protocol
            port: Port for HTTP transport
            timeout: Deployment timeout
            
        Returns:
            Dictionary with deployment information
        """
        try:
            config_sources = {
                'config_values': config or {}
            }
            
            deployment_options = DeploymentOptions(
                name=name,
                transport=transport,
                port=port,
                timeout=timeout
            )

            result = self.deployment_manager.deploy_template(
                template_id, config_sources, deployment_options
            )
            
            return result.to_dict()
            
        except Exception as e:
            logger.error(f"Failed to start server for {template_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def stop_server(self, deployment_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop a server instance.
        
        Args:
            deployment_id: The deployment to stop
            timeout: Timeout for graceful shutdown
            
        Returns:
            Dictionary with stop operation results
        """
        try:
            return self.deployment_manager.stop_deployment(deployment_id, timeout)
        except Exception as e:
            logger.error(f"Failed to stop server {deployment_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def stop_servers_by_template(self, template_name: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop all servers for a template.
        
        Args:
            template_name: Template name
            timeout: Timeout for each graceful shutdown
            
        Returns:
            Dictionary with bulk stop operation results
        """
        try:
            targets = self.deployment_manager.find_deployments_by_criteria(
                template_name=template_name
            )
            
            if not targets:
                return {
                    "success": True,
                    "stopped_deployments": [],
                    "message": f"No deployments found for template {template_name}"
                }
            
            return self.deployment_manager.stop_deployments_bulk(
                [t["id"] for t in targets], timeout
            )
            
        except Exception as e:
            logger.error(f"Failed to stop servers for template {template_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def list_servers(self, template_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List running server instances.
        
        Args:
            template_name: Optional filter by template name
            
        Returns:
            List of server information dictionaries
        """
        try:
            return self.deployment_manager.find_deployments_by_criteria(
                template_name=template_name
            )
        except Exception as e:
            logger.error(f"Failed to list servers: {e}")
            return []

    def get_server_info(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server.
        
        Args:
            deployment_id: The deployment identifier
            
        Returns:
            Server information dictionary or None if not found
        """
        try:
            deployments = self.deployment_manager.find_deployments_by_criteria(
                deployment_id=deployment_id
            )
            return deployments[0] if deployments else None
        except Exception as e:
            logger.error(f"Failed to get server info for {deployment_id}: {e}")
            return None

    def get_server_logs(self, deployment_id: str, lines: int = 100, follow: bool = False) -> Dict[str, Any]:
        """
        Get logs from a server.
        
        Args:
            deployment_id: The deployment to get logs from
            lines: Number of log lines to retrieve
            follow: Whether to stream logs in real-time
            
        Returns:
            Dictionary with log content and metadata
        """
        try:
            return self.deployment_manager.get_deployment_logs(
                deployment_id, lines=lines, follow=follow
            )
        except Exception as e:
            logger.error(f"Failed to get server logs for {deployment_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": ""
            }

    def stream_server_logs(self, deployment_id: str, callback, lines: int = 100) -> None:
        """
        Stream logs from a server with callback.
        
        Args:
            deployment_id: The deployment to stream logs from
            callback: Function to call with each log line
            lines: Number of initial lines to retrieve
        """
        try:
            self.deployment_manager.stream_deployment_logs(deployment_id, callback, lines)
        except Exception as e:
            logger.error(f"Failed to stream server logs for {deployment_id}: {e}")
            callback(f"Error streaming logs: {e}")

    def list_tools(self, 
                  template_or_id: str, 
                  discovery_method: str = "auto", 
                  force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        List available tools for a template or deployment.
        
        Args:
            template_or_id: Template name or deployment ID
            discovery_method: How to discover tools (static, dynamic, image, auto)
            force_refresh: Whether to force refresh cache
            
        Returns:
            List of tool definitions
        """
        try:
            return self.tool_manager.list_tools(
                template_or_id,
                discovery_method=discovery_method,
                force_refresh=force_refresh
            )
        except Exception as e:
            logger.error(f"Failed to list tools for {template_or_id}: {e}")
            return []

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
            return self.tool_manager.call_tool(
                template_or_deployment, tool_name, parameters, timeout
            )
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def discover_tools(self,
                      template_or_id: str,
                      method: str = "auto",
                      timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Discover tools using a specific method.
        
        Args:
            template_or_id: Template name or deployment ID
            method: Discovery method (static, dynamic, image, auto)
            timeout: Timeout for discovery operations
            
        Returns:
            List of discovered tools
        """
        try:
            return self.tool_manager.list_tools(
                template_or_id,
                discovery_method=method,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Failed to discover tools for {template_or_id}: {e}")
            return []

    def get_template_configuration(self, template_name: str) -> Dict[str, Any]:
        """
        Get all configurations for a template.
        
        Args:
            template_name: The template name
            
        Returns:
            Dictionary with all template configurations
        """
        try:
            return self.config_manager.load_configuration_for_template(template_name)
        except Exception as e:
            logger.error(f"Failed to get template configuration for {template_name}: {e}")
            return {}

    def validate_template_configuration(self, template_name: str) -> Dict[str, Any]:
        """
        Validate template configuration.
        
        Args:
            template_name: The template name
            
        Returns:
            Validation results dictionary
        """
        try:
            return self.config_manager.validate_template_configuration(template_name)
        except Exception as e:
            logger.error(f"Failed to validate template configuration for {template_name}: {e}")
            return {
                "valid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": []
            }

    def update_template_configuration(self, 
                                    template_name: str, 
                                    config_updates: Dict[str, Any]) -> bool:
        """
        Update template configuration (placeholder for future implementation).
        
        Args:
            template_name: The template name
            config_updates: Configuration updates to apply
            
        Returns:
            True if update was successful
        """
        # This would be implemented in the future
        logger.warning("update_template_configuration not yet implemented")
        return False

    async def start_server_async(self, 
                               template_id: str, 
                               config: Optional[Dict[str, Any]] = None, 
                               name: Optional[str] = None,
                               transport: Optional[str] = None,
                               port: int = 7071,
                               timeout: int = 300) -> Dict[str, Any]:
        """
        Async version of start_server.
        
        Args:
            template_id: The template to deploy
            config: Configuration overrides
            name: Custom deployment name
            transport: Transport protocol
            port: Port for HTTP transport
            timeout: Deployment timeout
            
        Returns:
            Dictionary with deployment information
        """
        # Run the synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.start_server, 
            template_id, config, name, transport, port, timeout
        )

    async def list_tools_async(self, 
                             template_or_id: str, 
                             discovery_method: str = "auto", 
                             force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Async version of list_tools.
        
        Args:
            template_or_id: Template name or deployment ID
            discovery_method: How to discover tools
            force_refresh: Whether to force refresh cache
            
        Returns:
            List of tool definitions
        """
        # Run the synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.list_tools, 
            template_or_id, discovery_method, force_refresh
        )

    async def call_tool_async(self,
                            template_or_deployment: str,
                            tool_name: str,
                            parameters: Dict[str, Any],
                            timeout: int = 30) -> Dict[str, Any]:
        """
        Async version of call_tool.
        
        Args:
            template_or_deployment: Template name or deployment ID
            tool_name: Name of the tool to call
            parameters: Tool parameters
            timeout: Timeout for the call
            
        Returns:
            Tool call result
        """
        # Run the synchronous version in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.call_tool, 
            template_or_deployment, tool_name, parameters, timeout
        )

    def clear_caches(self) -> None:
        """Clear all internal caches."""
        try:
            self.template_manager.refresh_cache()
            self.tool_manager.clear_cache()
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")

    def get_backend_type(self) -> str:
        """Get the backend type being used."""
        return self.backend_type

    def set_backend_type(self, backend_type: str) -> None:
        """
        Change the backend type (reinitializes all managers).
        
        Args:
            backend_type: New backend type (docker, kubernetes, mock)
        """
        try:
            self.backend_type = backend_type
            self.template_manager = TemplateManager(backend_type)
            self.deployment_manager = DeploymentManager(backend_type)
            self.tool_manager = ToolManager(backend_type)
        except Exception as e:
            logger.error(f"Failed to set backend type to {backend_type}: {e}")
            raise
