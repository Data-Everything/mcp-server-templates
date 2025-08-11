"""
MCP Client - Programmatic interface for MCP server template management.

This module provides a clean, programmatic API for managing MCP server templates,
complementing the existing CLI interface. It allows users to:
- Deploy and manage MCP server templates programmatically
- Discover available templates and their configurations
- List and monitor deployments
- Access tool discovery and execution capabilities

Example usage:
    from mcp_template import MCPClient
    
    client = MCPClient()
    
    # List available templates
    templates = client.list_templates()
    
    # Deploy a template
    deployment = client.deploy("github", config={"github_token": "your_token"})
    
    # List active deployments
    deployments = client.list_deployments()
    
    # Stop a deployment
    client.stop("github")
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_template.deployer import MCPDeployer
from mcp_template.manager import DeploymentManager
from mcp_template.template.utils.discovery import TemplateDiscovery
from mcp_template.tools.discovery import ToolDiscovery
from mcp_template.utils.config_processor import ConfigProcessor

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Programmatic client for MCP server template management.
    
    Provides a clean, object-oriented interface for managing MCP server templates
    without requiring CLI usage. Wraps existing functionality from MCPDeployer,
    DeploymentManager, and related classes.
    """

    def __init__(self, backend_type: str = "docker", config_dir: Optional[Path] = None):
        """
        Initialize the MCP client.
        
        Args:
            backend_type: Deployment backend ("docker", "kubernetes", "mock")
            config_dir: Custom configuration directory (defaults to ~/.mcp)
        """
        self.backend_type = backend_type
        self.config_dir = config_dir or Path.home() / ".mcp"
        self.config_dir.mkdir(exist_ok=True)
        
        # Initialize core components
        self.deployment_manager = DeploymentManager(backend_type=backend_type)
        self.template_discovery = TemplateDiscovery()
        self.tool_discovery = ToolDiscovery()
        self.config_processor = ConfigProcessor()
        
        # Cache templates for efficient access
        self._templates_cache = None

    @property
    def templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available templates (cached)."""
        if self._templates_cache is None:
            self._templates_cache = self.template_discovery.discover_templates()
        return self._templates_cache

    def list_templates(self, as_dict: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.
        
        Args:
            as_dict: If True, return as dict; if False, return list of template info
            
        Returns:
            Dictionary of template_name -> template_config or list of template info
        """
        templates = self.templates
        
        if as_dict:
            return templates
        
        # Convert to list format with status information
        template_list = []
        for name, template in templates.items():
            # Check deployment status
            try:
                deployments = self.list_deployments()
                template_deployments = [d for d in deployments if d.get("template") == name]
                if template_deployments:
                    status = "running"
                    running_count = len(template_deployments)
                else:
                    status = "not_deployed"
                    running_count = 0
            except Exception:
                status = "unknown"
                running_count = 0
            
            template_info = {
                "name": name,
                "description": template.get("description", ""),
                "version": template.get("version", ""),
                "status": status,
                "running_count": running_count,
                "config_schema": template.get("config_schema", {})
            }
            template_list.append(template_info)
        
        return template_list

    def get_template_config(self, template_name: str) -> Dict[str, Any]:
        """
        Get configuration schema for a specific template.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template configuration schema
            
        Raises:
            ValueError: If template not found
        """
        if template_name not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")
        
        return self.templates[template_name].get("config_schema", {})

    def deploy(
        self,
        template_name: str,
        config: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Deploy an MCP server template.
        
        Args:
            template_name: Name of the template to deploy
            config: Configuration values for the template
            name: Custom deployment name (optional)
            **kwargs: Additional configuration options
            
        Returns:
            Deployment information
            
        Raises:
            ValueError: If template not found or configuration invalid
            RuntimeError: If deployment fails
        """
        if template_name not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(f"Template '{template_name}' not found. Available: {available}")
        
        template_data = self.templates[template_name].copy()
        
        # Apply custom name if provided
        if name:
            template_data["name"] = name
        
        # Merge configuration
        final_config = {}
        if config:
            final_config.update(config)
        final_config.update(kwargs)
        
        try:
            result = self.deployment_manager.deploy_template(
                template_id=template_name,
                configuration=final_config,
                template_data=template_data,
                pull_image=True
            )
            logger.info(f"Successfully deployed template '{template_name}'")
            return result
        except Exception as e:
            error_msg = f"Failed to deploy template '{template_name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all active deployments.
        
        Returns:
            List of deployment information dictionaries
        """
        try:
            return self.deployment_manager.list_deployments()
        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            raise RuntimeError(f"Failed to list deployments: {e}") from e

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """
        Get status of a specific deployment.
        
        Args:
            deployment_name: Name of the deployment
            
        Returns:
            Deployment status information
        """
        try:
            return self.deployment_manager.get_deployment_status(deployment_name)
        except Exception as e:
            logger.error(f"Failed to get status for deployment '{deployment_name}': {e}")
            raise RuntimeError(f"Failed to get deployment status: {e}") from e

    def stop(self, template_name: str, deployment_name: Optional[str] = None) -> bool:
        """
        Stop a running deployment.
        
        Args:
            template_name: Name of the template
            deployment_name: Specific deployment name (optional)
            
        Returns:
            True if successfully stopped
            
        Raises:
            RuntimeError: If stop operation fails
        """
        try:
            # If no specific deployment name, use template name
            name_to_stop = deployment_name or template_name
            result = self.deployment_manager.delete_deployment(name_to_stop)
            logger.info(f"Successfully stopped deployment '{name_to_stop}'")
            return result
        except Exception as e:
            error_msg = f"Failed to stop deployment '{template_name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def discover_tools(self, template_name: str, endpoint: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Discover tools available in a deployed template.
        
        Args:
            template_name: Name of the deployed template
            endpoint: Custom endpoint URL (optional, auto-discovered if not provided)
            
        Returns:
            List of available tools
            
        Raises:
            RuntimeError: If tool discovery fails
        """
        try:
            # If endpoint not provided, try to discover from deployments
            if endpoint is None:
                deployments = self.list_deployments()
                template_deployments = [d for d in deployments if d.get("template") == template_name]
                if not template_deployments:
                    raise RuntimeError(f"No running deployments found for template '{template_name}'")
                
                # Use the first deployment's endpoint
                deployment = template_deployments[0]
                endpoint = deployment.get("endpoint") or deployment.get("url")
                if not endpoint:
                    raise RuntimeError(f"No endpoint found for deployment of '{template_name}'")
            
            tools = self.tool_discovery.discover_tools(endpoint)
            logger.info(f"Discovered {len(tools)} tools from '{template_name}'")
            return tools
        except Exception as e:
            error_msg = f"Failed to discover tools for '{template_name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def call_tool(
        self,
        template_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call a specific tool on a deployed template.
        
        Args:
            template_name: Name of the deployed template
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            endpoint: Custom endpoint URL (optional)
            
        Returns:
            Tool execution result
            
        Raises:
            RuntimeError: If tool call fails
        """
        try:
            # Import at runtime to avoid circular imports
            from mcp_template.tools.http_tool_caller import HTTPToolCaller
            
            # Discover endpoint if not provided
            if endpoint is None:
                deployments = self.list_deployments()
                template_deployments = [d for d in deployments if d.get("template") == template_name]
                if not template_deployments:
                    raise RuntimeError(f"No running deployments found for template '{template_name}'")
                
                deployment = template_deployments[0]
                endpoint = deployment.get("endpoint") or deployment.get("url")
                if not endpoint:
                    raise RuntimeError(f"No endpoint found for deployment of '{template_name}'")
            
            caller = HTTPToolCaller(base_url=endpoint, timeout=30)
            result = caller.call_tool(tool_name, arguments)
            logger.info(f"Successfully called tool '{tool_name}' on '{template_name}'")
            return result
        except Exception as e:
            error_msg = f"Failed to call tool '{tool_name}' on '{template_name}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def cleanup(self, template_name: Optional[str] = None, all_deployments: bool = False) -> bool:
        """
        Clean up stopped or failed deployments.
        
        Args:
            template_name: Specific template to clean up (optional)
            all_deployments: Clean up all deployments (optional)
            
        Returns:
            True if cleanup successful
        """
        try:
            # Use MCPDeployer for cleanup functionality
            deployer = MCPDeployer()
            deployer.cleanup(template_name=template_name, all_containers=all_deployments)
            logger.info("Cleanup completed successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to cleanup: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def refresh_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Refresh the templates cache and return updated templates.
        
        Returns:
            Updated templates dictionary
        """
        self._templates_cache = None
        return self.templates