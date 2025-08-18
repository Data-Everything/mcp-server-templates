"""
Server management functionality for MCP Template system.

This module provides server lifecycle management including:
- Running server instances tracking
- Server deployment and management
- Integration with existing deployment backends
"""

import logging
from typing import Any, Dict, List, Literal, Optional

from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.exceptions import StdIoTransportDeploymentError
from mcp_template.template.utils.discovery import TemplateDiscovery
from mcp_template.tools.docker_probe import DockerProbe
from mcp_template.utils.config_processor import ConfigProcessor

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

        self.backend_type = backend_type
        self.deployment_manager = DeploymentManager(backend_type)
        self.template_discovery = TemplateDiscovery()
        self.config_processor = ConfigProcessor()
        self._templates_cache = None

    def list_running_servers(self, template: str = None) -> List[Dict[str, Any]]:
        """
        List currently running MCP servers.

        Returns:
            List of running server information
        """

        deployments = []
        try:
            deployments = self.deployment_manager.list_deployments()
        except Exception as e:
            logger.error("Failed to list running servers: %s", e)
        else:
            if template:
                deployments = [
                    server
                    for server in deployments
                    if server.get("template") == template
                ]

        return deployments

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

    @staticmethod
    def list_missing_properties(
        template: Dict[str, Any], config: Dict[str, Any]
    ) -> List[str]:
        """Check for missing required properties in the configuration."""

        missing_properties = []
        required_properties = template.get("config_schema", {}).get("required", [])
        required_properties_env_vars = {
            prop: template["config_schema"]["properties"][prop].get("env_mapping")
            for prop in required_properties
            if prop in template.get("config_schema", {}).get("properties", {})
            and template["config_schema"]["properties"][prop].get("env_mapping")
        }
        for prop in required_properties:
            if (
                prop not in config
                and required_properties_env_vars.get(prop) not in config
            ):
                missing_properties.append(prop)
        return missing_properties

    @staticmethod
    def append_volume_mounts_to_template(
        template: Dict[str, Any],
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get volume mounts from the template and configuration."""

        template_copy = template.copy()
        if data_dir or config_dir:
            template_copy["volumes"] = template["volumes"].copy()

            if data_dir:
                for key in template_copy["volumes"]:
                    if "/data" in template_copy["volumes"][key]:
                        template_copy["volumes"][key] = template_copy["volumes"][
                            key
                        ].replace("/data", data_dir)

            if config_dir:
                for key in template_copy["volumes"]:
                    if "/config" in template_copy["volumes"][key]:
                        template_copy["volumes"][key] = template_copy["volumes"][
                            key
                        ].replace("/config", config_dir)

        return template_copy

    def generate_run_config(
        self,
        template_data: Dict[str, Any],
        transport: Optional[Literal["http", "stdio", "sse", "http-stream"]] = None,
        port: Optional[int] = None,
        configuration: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate configuration for running a server.

        Args:
            template_data: Template data to use
            transport: Transport type (e.g., "http", "stdio")
            port: Port for HTTP transport
            configuration: Configuration values to apply
            config_file: Optional configuration file to use
            env_vars: Environment variables to set for the server
            data_dir: Data directory for the server
            config_dir: Configuration directory for the server

        Returns:
            Configuration dictionary or None if failed
        """

        template_id = template_data.get("id")
        supported_transports = template_data.get("transport", {}).get("supported", [])
        default_transport = template_data.get("transport", {}).get("default", "http")
        if not transport:
            # Default to HTTP transport if not specified
            transport = default_transport
        else:
            if transport not in supported_transports:
                logger.error(
                    "Transport %s not supported by template %s",
                    transport,
                    template_id,
                )
                return None

        if transport == "stdio":
            raise StdIoTransportDeploymentError()

        if not port and transport == "http":
            port = template_data.get("transport", {}).get(
                "port", DockerProbe._find_available_port()
            )

        # Use provided configuration or empty dict
        config = configuration or {}
        env_vars = env_vars or {}

        config["transport"] = transport
        if port:
            # Ensure port is a string for JSON serialization
            config["port"] = str(port)

        config = self.config_processor.prepare_configuration(
            template=template_data,
            env_vars=env_vars,
            config_file=config_file,
            config_values=config,
        )
        missing_properties = self.list_missing_properties(template_data, config)
        template_copy = self.append_volume_mounts_to_template(
            template=template_data,
            data_dir=data_dir,
            config_dir=config_dir,
        )
        template_config_dict = (
            self.config_processor.handle_volume_and_args_config_properties(
                template_copy, config
            )
        )
        config = template_config_dict.get("config", config)
        template_copy = template_config_dict.get("template", template_copy)

        return {
            "template": template_copy,
            "config": config,
            "transport": transport,
            "port": port,
            "missing_properties": missing_properties,
        }

    def start_server(
        self,
        template_id: str,
        configuration: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
        image: Optional[str] = None,
        transport: Optional[Literal["http", "stdio", "sse", "http-stream"]] = None,
        port: Optional[int] = None,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a new MCP server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration for the server
            config_file: Optional path to configuration file
            env_vars: Environment variables to set for the server.
                      This is primarily for exported templates
            deployment_name: Optional custom deployment name
            pull_image: Whether to pull the latest image
            image: Optional custom image to use
            transport: Optional transport type (e.g., "http", "stdio")
            port: Optional port for HTTP transport
            data_dir: Optional data directory for the server
            config_dir: Optional configuration directory for the server

        Returns:
            Deployment information or None if failed
        """

        if image:
            raise NotImplementedError(
                "Image parameter is not supported yet. "
                "Please use template_id to specify the server template."
            )
            # if len(image.split(":")) == 1:
            #    # If no tag is provided, default to "latest"
            #    image += ":latest"

        try:
            # Get template information
            templates = self._get_templates()
            if template_id not in templates:
                logger.error("Template %s not found", template_id)
                return None

            template_data = templates[template_id]

            config_dict = self.generate_run_config(
                template_data=template_data,
                transport=transport,
                port=port,
                configuration=configuration,
                config_file=config_file,
                env_vars=env_vars,
                data_dir=data_dir,
                config_dir=config_dir,
            )
            if not config_dict:
                logger.error("Failed to generate run configuration for %s", template_id)
                return None

            template_copy = config_dict["template"]
            config = config_dict["config"]
            transport = config_dict["transport"]
            port = config_dict.get("port")
            missing_properties = config_dict.get("missing_properties", [])

            if missing_properties:
                logger.error(
                    "Missing required properties for %s: %s",
                    template_id,
                    missing_properties,
                )
                return None

            # Deploy the template
            result = self.deployment_manager.deploy_template(
                template_id=template_id,
                configuration=config,
                template_data=template_copy,
                pull_image=pull_image,
                backend=self.backend_type,
            )

            if result.get("status") == "deployed":
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
            result = self.deployment_manager.delete_deployment(
                deployment_id, raise_on_failure=True
            )
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
            result = self.deployment_manager.backend.get_deployment_info(
                deployment_id, include_logs=True
            )
            if result and "logs" in result:
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
