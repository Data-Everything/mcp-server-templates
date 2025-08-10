"""
Server management functionality for MCP Template system.

This module provides server lifecycle management including:
- Running server instances tracking
- Server deployment and management
- Integration with existing deployment backends
"""

import logging
from typing import Any, Dict, List, Optional

from mcp_template.manager import DeploymentManager
from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class ServerManager:
    """
    Manages MCP server instances and deployments.

    Provides a unified interface for server lifecycle management,
    reusing existing deployment infrastructure.
    """

    def __init__(self, backend_type: str = "docker"):
        """
        Initialize server manager.

        Args:
            backend_type: Deployment backend type (docker, kubernetes, mock)
        """
        self.deployment_manager = DeploymentManager(backend_type)
        self.template_discovery = TemplateDiscovery()
        self._templates_cache = None

    def list_running_servers(self) -> List[Dict[str, Any]]:
        """
        List currently running MCP servers.

        Returns:
            List of running server information
        """
        try:
            return self.deployment_manager.list_deployments()
        except Exception as e:
            logger.error("Failed to list running servers: %s", e)
            return []

    def get_server_info(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server deployment.

        Args:
            deployment_id: ID of the deployment

        Returns:
            Server information or None if not found
        """
        try:
            running_servers = self.list_running_servers()
            for server in running_servers:
                if (
                    server.get("id") == deployment_id
                    or server.get("name") == deployment_id
                ):
                    return server
            return None
        except Exception as e:
            logger.error("Failed to get server info for %s: %s", deployment_id, e)
            return None

    def start_server(
        self, template_id: str, configuration: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Start a new MCP server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration for the server
            deployment_name: Optional custom deployment name

        Returns:
            Deployment information or None if failed
        """
        try:
            # Get template information
            templates = self._get_templates()
            if template_id not in templates:
                logger.error("Template %s not found", template_id)
                return None

            template_data = templates[template_id]

            # Use provided configuration or empty dict
            config = configuration or {}

            # Deploy the template
            result = self.deployment_manager.deploy_template(
                template_id=template_id,
                configuration=config,
                template_data=template_data,
                pull_image=True,
            )

            if result.get("success"):
                logger.info("Successfully started server %s", template_id)
                return result
            else:
                logger.error(
                    "Failed to start server %s: %s", template_id, result.get("error")
                )
                return None

        except Exception as e:
            logger.error("Failed to start server %s: %s", template_id, e)
            return None

    def stop_server(self, deployment_id: str) -> bool:
        """
        Stop a running MCP server.

        Args:
            deployment_id: ID of the deployment to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            result = self.deployment_manager.delete_deployment(deployment_id)
            if result:
                logger.info("Successfully stopped server %s", deployment_id)
                return True
            else:
                logger.error("Failed to stop server %s", deployment_id)
                return False
        except Exception as e:
            logger.error("Failed to stop server %s: %s", deployment_id, e)
            return False

    def get_server_logs(self, deployment_id: str, lines: int = 100) -> Optional[str]:
        """
        Get logs from a running server.

        Args:
            deployment_id: ID of the deployment
            lines: Number of log lines to retrieve (note: actual implementation may vary)

        Returns:
            Log content or None if failed
        """
        # Note: lines parameter is kept for API compatibility but not used
        # by the underlying backend which returns fixed log length
        try:
            result = self.deployment_manager.get_deployment_status(deployment_id)
            if "logs" in result:
                return result["logs"]
            else:
                logger.error("No logs available for %s", deployment_id)
                return None
        except Exception as e:
            logger.error("Failed to get logs for %s: %s", deployment_id, e)
            return None

    def list_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List available MCP server templates.

        Returns:
            Dictionary of template_id -> template_info
        """
        return self._get_templates()

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template information or None if not found
        """
        templates = self._get_templates()
        return templates.get(template_id)

    def _get_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available templates with caching."""
        if self._templates_cache is None:
            self._templates_cache = self.template_discovery.discover_templates()
        return self._templates_cache

    def refresh_templates(self) -> None:
        """Refresh the templates cache."""
        self._templates_cache = None
