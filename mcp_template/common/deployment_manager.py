"""
Deployment management functionality shared between CLI and MCPClient.

This module provides centralized deployment orchestration, server lifecycle
management, and deployment status tracking that can be used by both the CLI
interface and the programmatic MCPClient API.
"""

import logging
from typing import Any, Dict, List, Literal, Optional

from mcp_template.common.template_manager import TemplateManager
from mcp_template.deployer import MCPDeployer
from mcp_template.exceptions import StdIoTransportDeploymentError
from mcp_template.manager import DeploymentManager as CoreDeploymentManager
from mcp_template.tools.docker_probe import DockerProbe
from mcp_template.utils.config_processor import ConfigProcessor

logger = logging.getLogger(__name__)


class DeploymentManager:
    """
    Centralized deployment management for CLI and MCPClient.

    Provides common functionality for deployment orchestration, server lifecycle
    management, and deployment status tracking.
    """

    def __init__(self, backend_type: str = "docker"):
        """
        Initialize deployment manager.

        Args:
            backend_type: Deployment backend type (docker, kubernetes, mock)
        """
        self.backend_type = backend_type
        self.core_deployment_manager = CoreDeploymentManager(backend_type)
        self.template_manager = TemplateManager()
        self.config_processor = ConfigProcessor()

    def deploy_template(
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
        Deploy a template as a running server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration values for the server
            config_file: Optional path to configuration file
            env_vars: Environment variables to set for the server
            pull_image: Whether to pull the latest image before deployment
            image: Optional custom image to use (overrides template image)
            transport: Transport type (e.g., "http", "stdio", "sse")
            port: Port for HTTP transport
            data_dir: Data directory for the server
            config_dir: Configuration directory for the server

        Returns:
            Deployment information or None if failed
        """
        if image:
            raise NotImplementedError(
                "Custom image parameter is not supported yet. "
                "Please use template_id to specify the server template."
            )

        try:
            # Get template information
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                logger.error("Template %s not found", template_id)
                return None

            # Generate deployment configuration
            config_dict = self._generate_deployment_config(
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
                logger.error(
                    "Failed to generate deployment configuration for %s", template_id
                )
                return None

            template_copy = config_dict["template"]
            config = config_dict["config"]
            missing_properties = config_dict.get("missing_properties", [])

            if missing_properties:
                logger.error(
                    "Missing required properties for %s: %s",
                    template_id,
                    missing_properties,
                )
                return None

            # Deploy the template
            result = self.core_deployment_manager.deploy_template(
                template_id=template_id,
                configuration=config,
                template_data=template_copy,
                pull_image=pull_image,
                backend=self.backend_type,
            )

            if result.get("status") == "deployed":
                logger.info("Successfully deployed template %s", template_id)
                return result
            else:
                logger.error(
                    "Failed to deploy template %s: %s", template_id, result.get("error")
                )
                return None

        except Exception as e:
            logger.error("Failed to deploy template %s: %s", template_id, e)
            return None

    def stop_deployment(self, deployment_id: str) -> bool:
        """
        Stop a running deployment.

        Args:
            deployment_id: ID of the deployment to stop

        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            result = self.core_deployment_manager.delete_deployment(
                deployment_id, raise_on_failure=True
            )
            if result:
                logger.info("Successfully stopped deployment %s", deployment_id)
                return True
            else:
                logger.error("Failed to stop deployment %s", deployment_id)
                return False
        except Exception as e:
            logger.error("Failed to stop deployment %s: %s", deployment_id, e)
            return False

    def list_deployments(
        self, template_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List currently running deployments.

        Args:
            template_filter: Optional template name to filter deployments by

        Returns:
            List of running deployment information
        """
        try:
            deployments = self.core_deployment_manager.list_deployments()

            if template_filter:
                # Filter deployments by template
                filtered_deployments = []
                for deployment in deployments:
                    if deployment.get("template") == template_filter:
                        filtered_deployments.append(deployment)
                return filtered_deployments

            return deployments
        except Exception as e:
            logger.error("Failed to list deployments: %s", e)
            return []

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific deployment.

        Args:
            deployment_id: ID of the deployment

        Returns:
            Deployment status information or None if not found
        """
        try:
            return self.core_deployment_manager.get_deployment_status(deployment_id)
        except Exception as e:
            logger.error("Failed to get deployment status for %s: %s", deployment_id, e)
            return None

    def get_deployment_logs(
        self, deployment_id: str, lines: int = 100
    ) -> Optional[str]:
        """
        Get logs from a running deployment.

        Args:
            deployment_id: ID of the deployment
            lines: Number of log lines to retrieve (implementation dependent)
                  Note: Currently unused by backend, kept for API compatibility

        Returns:
            Log content or None if failed
        """
        # Note: lines parameter is kept for API compatibility but not used
        # by the underlying backend which returns fixed log length
        _ = lines  # Explicitly mark as unused for now
        try:
            result = self.core_deployment_manager.get_deployment_status(deployment_id)
            if "logs" in result:
                return result["logs"]
            else:
                logger.error("No logs available for deployment %s", deployment_id)
                return None
        except Exception as e:
            logger.error("Failed to get logs for deployment %s: %s", deployment_id, e)
            return None

    def cleanup_deployments(
        self, template_filter: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Clean up stopped or failed deployments.

        Args:
            template_filter: Optional template name to filter cleanup by
            force: Whether to force cleanup of running deployments

        Returns:
            Dictionary with cleanup results:
            - cleaned: List of cleaned deployment IDs
            - failed: List of deployment IDs that failed to clean
            - skipped: List of deployment IDs that were skipped
        """
        result = {"cleaned": [], "failed": [], "skipped": []}

        try:
            deployments = self.list_deployments(template_filter)

            for deployment in deployments:
                deployment_id = deployment.get("id") or deployment.get("name")
                if not deployment_id:
                    continue

                status = deployment.get("status", "unknown")

                # Only clean up stopped/failed deployments unless force is True
                if not force and status in ["running", "starting"]:
                    result["skipped"].append(deployment_id)
                    continue

                try:
                    if self.stop_deployment(deployment_id):
                        result["cleaned"].append(deployment_id)
                    else:
                        result["failed"].append(deployment_id)
                except Exception as e:
                    logger.error(
                        "Failed to cleanup deployment %s: %s", deployment_id, e
                    )
                    result["failed"].append(deployment_id)

        except Exception as e:
            logger.error("Failed to cleanup deployments: %s", e)

        return result

    def _generate_deployment_config(
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
        Generate deployment configuration from template and parameters.

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
            # Find an available port for HTTP transport
            try:
                # Try to use DockerProbe's port finding method
                port = (
                    DockerProbe._find_available_port()
                )  # pylint: disable=protected-access
            except AttributeError:
                # Fallback to default port if method not available
                port = template_data.get("transport", {}).get("port", 8000)

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
        missing_properties = MCPDeployer.list_missing_properties(template_data, config)
        template_copy = MCPDeployer.append_volume_mounts_to_template(
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

    def validate_deployment_config(
        self, template_id: str, configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate deployment configuration without actually deploying.

        Args:
            template_id: Template to validate
            configuration: Configuration values to validate

        Returns:
            Dictionary with validation results:
            - valid: bool - Whether configuration is valid
            - errors: List[str] - List of validation errors
            - warnings: List[str] - List of validation warnings
            - missing_properties: List[str] - List of missing required properties
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "missing_properties": [],
        }

        try:
            # Get template information
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                result["errors"].append(f"Template '{template_id}' not found")
                return result

            # Check for missing required properties
            config = configuration or {}
            missing_properties = MCPDeployer.list_missing_properties(
                template_data, config
            )
            result["missing_properties"] = missing_properties

            if missing_properties:
                result["errors"].append(
                    f"Missing required properties: {missing_properties}"
                )

            # Validate transport configuration
            transport = config.get(
                "transport", template_data.get("transport", {}).get("default", "http")
            )
            supported_transports = template_data.get("transport", {}).get(
                "supported", []
            )

            if transport not in supported_transports:
                result["errors"].append(
                    f"Transport '{transport}' not supported. Supported: {supported_transports}"
                )

            # Validate port configuration for HTTP transport
            if transport == "http":
                port = config.get("port")
                if port:
                    try:
                        port_int = int(port)
                        if port_int < 1 or port_int > 65535:
                            result["errors"].append("Port must be between 1 and 65535")
                    except ValueError:
                        result["errors"].append("Port must be a valid integer")

            # Set valid status based on errors
            result["valid"] = len(result["errors"]) == 0

        except Exception as e:
            result["errors"].append(f"Validation failed: {str(e)}")

        return result
