"""
Deployment Manager - Centralized deployment operations.

This module provides a unified interface for deployment lifecycle management,
consolidating functionality from CLI and MCPClient for deployment operations.
"""

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from mcp_template.backends import get_backend
from mcp_template.core.config_processor import RESERVED_ENV_VARS, ConfigProcessor
from mcp_template.core.template_manager import TemplateManager

logger = logging.getLogger(__name__)


class DeploymentOptions:
    """Options for deployment configuration."""

    def __init__(
        self,
        name: Optional[str] = None,
        transport: Optional[str] = None,
        port: int = 7071,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
        pull_image: bool = True,
        timeout: int = 300,
        dry_run: bool = False,
    ):
        self.name = name
        self.transport = transport
        self.port = port
        self.data_dir = data_dir
        self.config_dir = config_dir
        self.pull_image = pull_image
        self.timeout = timeout
        self.dry_run = dry_run


class DeploymentResult:
    """Result of a deployment operation."""

    def __init__(
        self,
        success: bool,
        deployment_id: Optional[str] = None,
        template: Optional[str] = None,
        status: Optional[str] = None,
        container_id: Optional[str] = None,
        image: Optional[str] = None,
        ports: Optional[Dict[str, int]] = None,
        config: Optional[Dict[str, Any]] = None,
        mcp_config_path: Optional[str] = None,
        transport: Optional[str] = None,
        endpoint: Optional[str] = None,
        error: Optional[str] = None,
        duration: float = 0.0,
    ):
        self.success = success
        self.deployment_id = deployment_id
        self.template = template
        self.status = status
        self.container_id = container_id
        self.image = image
        self.ports = ports or {}
        self.config = config or {}
        self.mcp_config_path = mcp_config_path
        self.transport = transport
        self.endpoint = endpoint
        self.error = error
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "deployment_id": self.deployment_id,
            "template": self.template,
            "status": self.status,
            "container_id": self.container_id,
            "image": self.image,
            "ports": self.ports,
            "config": self.config,
            "mcp_config_path": self.mcp_config_path,
            "transport": self.transport,
            "endpoint": self.endpoint,
            "error": self.error,
            "duration": self.duration,
        }


class DeploymentManager:
    """
    Centralized deployment management operations.

    Provides unified interface for deployment lifecycle management that can be
    shared between CLI and MCPClient implementations.
    """

    def __init__(self, backend_type: str = "docker", **backend_kwargs):
        """Initialize the deployment manager."""
        self.backend_type = backend_type
        self.backend = get_backend(backend_type, **backend_kwargs)
        self.template_manager = TemplateManager(backend_type)
        self.config_processor = ConfigProcessor()

    def deploy_template(
        self,
        template_id: str,
        config_sources: Dict[str, Any],
        deployment_options: DeploymentOptions,
    ) -> DeploymentResult:
        """
        Deploy a template with specified configuration.

        Args:
            template_id: The template to deploy
            config_sources: Various configuration sources to merge
            deployment_options: Deployment-specific options

        Returns:
            DeploymentResult with deployment information
        """
        start_time = time.time()

        try:
            # Validate template exists
            if not self.template_manager.validate_template(template_id):
                return DeploymentResult(
                    success=False,
                    error=f"Template '{template_id}' not found or invalid",
                    duration=time.time() - start_time,
                )

            # Get template information
            template_info = self.template_manager.get_template_info(template_id)
            if not template_info:
                return DeploymentResult(
                    success=False,
                    error=f"Failed to load template info for '{template_id}'",
                    duration=time.time() - start_time,
                )

            # Validate and set transport
            transport_result = self._validate_and_set_transport(
                template_info, deployment_options
            )
            if not transport_result["success"]:
                return DeploymentResult(
                    success=False,
                    error=transport_result["error"],
                    duration=time.time() - start_time,
                )

            # Process Kubernetes-specific configuration if backend is Kubernetes
            # k8s_config = {}
            # if self.backend == "kubernetes":
            #    k8s_config = self.config_processor.merge_k8s_config_sources(
            #        k8s_config_file=config_sources.get("k8s_config_file"),
            #        k8s_config_values=config_sources.get("k8s_config_values"),
            #    )
            # Set the Kubernetes configuration on the backend
            #    if hasattr(self.backend, "set_k8s_config"):
            #        self.backend.set_k8s_config(k8s_config)

            # Prepare configuration using the unified config processor
            volume_config = config_sources.pop("volume_config", None)
            config = self.config_processor.prepare_configuration(
                template=template_info,
                config_values=config_sources.get("config_values", {}),
                env_vars=config_sources.get("env_vars", {}),
                config_file=config_sources.get("config_file", None),
                override_values=config_sources.get("override_values", None),
            )

            # Handle volume mounts and command arguments
            template_config_dict = (
                self.config_processor.handle_volume_and_args_config_properties(
                    template_info, config, volume_config
                )
            )
            config = template_config_dict.get("config", config)
            template_info = template_config_dict.get("template", template_info)

            # Validate final configuration
            validation_result = self.config_processor.validate_config(
                config, template_info.get("config_schema", {})
            )

            if not validation_result.valid:
                return DeploymentResult(
                    success=False,
                    error=f"Configuration validation failed: {validation_result.errors}",
                    duration=time.time() - start_time,
                )

            # Prepare deployment specification
            deployment_spec = self._prepare_deployment_spec(
                template_id,
                template_info,
                config,
                deployment_options,
            )

            # Execute deployment
            deployment_result = self._execute_deployment(deployment_spec)
            deployment_result.duration = time.time() - start_time

            return deployment_result

        except Exception as e:
            logger.error(f"Deployment failed for {template_id}: {e}")
            return DeploymentResult(
                success=False, error=str(e), duration=time.time() - start_time
            )

    def stop_deployment(
        self, deployment_id: str, timeout: int = 30, force: bool = False
    ) -> Dict[str, Any]:
        """
        Stop a deployment.

        Args:
            deployment_id: The deployment to stop
            timeout: Timeout for graceful shutdown
            force: Whether to force stop if graceful fails

        Returns:
            Dictionary with stop operation results
        """
        start_time = time.time()

        try:
            # Check if deployment exists
            deployment_info = self.backend.get_deployment_info(deployment_id)
            if not deployment_info:
                return {
                    "success": False,
                    "error": f"Deployment '{deployment_id}' not found",
                    "duration": time.time() - start_time,
                }

            # Attempt graceful stop
            success = self.backend.stop_deployment(deployment_id, timeout)

            if not success and force:
                # Force stop if graceful failed
                success = self.backend.force_stop_deployment(deployment_id)

            return {
                "success": success,
                "deployment_id": deployment_id,
                "stopped_deployments": [deployment_id] if success else [],
                "duration": time.time() - start_time,
                "error": None if success else "Failed to stop deployment",
            }

        except Exception as e:
            logger.error(f"Failed to stop deployment {deployment_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
            }

    def stop_deployments_bulk(
        self, deployment_filters: List[str], timeout: int = 30, force: bool = False
    ) -> Dict[str, Any]:
        """
        Stop multiple deployments.

        Args:
            deployment_filters: List of deployment IDs to stop
            timeout: Timeout for each graceful shutdown
            force: Whether to force stop if graceful fails

        Returns:
            Dictionary with bulk stop operation results
        """
        start_time = time.time()
        stopped_deployments = []
        failed_deployments = []

        for deployment_id in deployment_filters:
            result = self.stop_deployment(deployment_id, timeout, force)
            if result["success"]:
                stopped_deployments.append(deployment_id)
            else:
                failed_deployments.append(
                    {"deployment_id": deployment_id, "error": result["error"]}
                )

        return {
            "success": len(failed_deployments) == 0,
            "stopped_deployments": stopped_deployments,
            "failed_deployments": failed_deployments,
            "duration": time.time() - start_time,
        }

    def get_deployment_logs(
        self,
        deployment_id: str,
        lines: int = 100,
        follow: bool = False,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get logs from a deployment.

        Args:
            deployment_id: The deployment to get logs from
            lines: Number of log lines to retrieve
            follow: Whether to stream logs in real-time
            since: Start time for log filtering
            until: End time for log filtering

        Returns:
            Dictionary with log content and metadata
        """
        try:
            # Check if deployment exists
            deployment_info = self.backend.get_deployment_info(deployment_id)
            if not deployment_info:
                return {
                    "success": False,
                    "error": f"Deployment '{deployment_id}' not found",
                    "logs": "",
                    "lines_returned": 0,
                }

            # Get logs from backend
            logs_result = self.backend.get_deployment_logs(
                deployment_id, lines=lines, follow=follow, since=since, until=until
            )

            if not logs_result.get("success", False):
                return {
                    "success": False,
                    "error": logs_result.get("error", "Failed to retrieve logs"),
                    "logs": "",
                    "lines_returned": 0,
                }

            logs = logs_result.get("logs", "")
            lines_returned = len(logs.split("\n")) if logs else 0

            return {
                "success": True,
                "logs": logs,
                "deployment_id": deployment_id,
                "lines_returned": lines_returned,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

        except Exception as e:
            logger.error(f"Failed to get logs for deployment {deployment_id}: {e}")
            return {"success": False, "error": str(e), "logs": "", "lines_returned": 0}

    def stream_deployment_logs(
        self, deployment_id: str, callback: Callable[[str], None], lines: int = 100
    ) -> None:
        """
        Stream logs from a deployment with callback.

        Args:
            deployment_id: The deployment to stream logs from
            callback: Function to call with each log line
            lines: Number of initial lines to retrieve
        """
        try:
            self.backend.stream_deployment_logs(deployment_id, callback, lines)
        except Exception as e:
            logger.error(f"Failed to stream logs for deployment {deployment_id}: {e}")
            callback(f"Error streaming logs: {e}")

    def find_deployments_by_criteria(
        self,
        template_name: Optional[str] = None,
        custom_name: Optional[str] = None,
        deployment_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find deployments matching specified criteria.

        Args:
            template_name: Filter by template name
            custom_name: Filter by custom deployment name
            deployment_id: Specific deployment ID
            status: Deployment status

        Returns:
            List of matching deployment information
        """
        try:
            all_deployments = self.backend.list_deployments()
            matching_deployments = []

            for deployment in all_deployments:
                # Filter by template name
                if template_name and deployment.get("template") != template_name:
                    continue

                # Filter by custom name
                if custom_name and deployment.get("name") != custom_name:
                    continue

                # Filter by deployment ID (check both 'id' and 'name' fields)
                if deployment_id and (
                    deployment.get("id") != deployment_id
                    and deployment.get("name") != deployment_id
                ):
                    continue

                if status and deployment.get("status") != status:
                    continue

                matching_deployments.append(deployment)

            return matching_deployments

        except Exception as e:
            logger.error(f"Failed to find deployments: {e}")
            return []

    def list_deployments(self, running_only: bool = False) -> List[Dict[str, Any]]:
        """
        List all deployments, optionally filtering to running only.

        Args:
            running_only: If True, only return running deployments

        Returns:
            List of deployment information dictionaries
        """
        try:
            all_deployments = self.backend.list_deployments()

            if running_only:
                # Filter to only running deployments
                return [
                    deployment
                    for deployment in all_deployments
                    if deployment.get("status") == "running"
                ]

            return all_deployments

        except Exception as e:
            logger.error(f"Failed to list deployments: {e}")
            return []

    def find_deployment_for_logs(
        self, template_name: Optional[str] = None, custom_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Find deployment ID for log operations.

        Args:
            template_name: Template name to find deployment for
            custom_name: Custom deployment name to find

        Returns:
            Deployment ID if found, None otherwise
        """
        deployments = self.find_deployments_by_criteria(
            template_name=template_name, custom_name=custom_name
        )

        if not deployments:
            return None

        # Return the first matching deployment
        return deployments[0].get("id")

    def _prepare_deployment_spec(
        self,
        template_id: str,
        template_info: Dict[str, Any],
        config: Dict[str, Any],
        options: DeploymentOptions,
    ) -> Dict[str, Any]:
        """Prepare deployment specification for backend."""
        return {
            "template_id": template_id,
            "template_info": template_info,
            "config": config,
            "options": options.__dict__,
        }

    def _execute_deployment(self, deployment_spec: Dict[str, Any]) -> DeploymentResult:
        """Execute the actual deployment using the backend."""
        try:
            # Extract the spec components for the backend interface
            template_id = deployment_spec["template_id"]
            template_info = deployment_spec["template_info"]
            config = deployment_spec["config"]
            options = deployment_spec["options"]

            # Apply deployment options to config using RESERVED_ENV_VARS mapping
            for option_key, env_var_key in RESERVED_ENV_VARS.items():
                if option_key in options and options[option_key] is not None:
                    config[env_var_key] = options[option_key]

            # Call the correct backend method
            result = self.backend.deploy_template(
                template_id=template_id,
                config=config,
                template_data=template_info,
                pull_image=options.get("pull_image", True),
                dry_run=options.get("dry_run", False),
            )

            # If deployment returned a result without exception, consider it successful
            # unless explicitly marked as failed
            success = (
                result.get("success", True) or result.get("status") == "running"
            )  # Default to True if no explicit success key

            return DeploymentResult(
                success=success,
                deployment_id=result.get(
                    "deployment_id", result.get("deployment_name")
                ),
                template=result.get("template", result.get("template_id")),
                status=result.get("status"),
                container_id=result.get("container_id"),
                image=result.get("image"),
                ports=result.get("ports", {}),
                config=result.get("config", {}),
                mcp_config_path=result.get("mcp_config_path"),
                transport=result.get("transport"),
                endpoint=result.get("endpoint"),
                error=result.get("error"),
            )

        except Exception as e:
            logger.error(f"Backend deployment failed: {e}")
            return DeploymentResult(
                success=False, error=f"Backend deployment failed: {str(e)}"
            )

    def _validate_and_set_transport(
        self, template_info: Dict[str, Any], deployment_options: DeploymentOptions
    ) -> Dict[str, Any]:
        """
        Validate transport selection and set the appropriate transport.

        Args:
            template_info: Template information containing transport configuration
            deployment_options: Deployment options that may include transport override

        Returns:
            Dictionary with success status and error message if failed
        """
        transport_config = template_info.get("transport", {})

        # Get supported transports and default
        supported_transports = transport_config.get(
            "supported", ["stdio"]
        )  # Default to stdio if not specified
        default_transport = transport_config.get(
            "default", supported_transports[0] if supported_transports else "stdio"
        )

        # Use provided transport or fall back to template default
        requested_transport = deployment_options.transport or default_transport

        # Validate that requested transport is supported
        if requested_transport not in supported_transports:
            return {
                "success": False,
                "error": f"Transport '{requested_transport}' is not supported by template. "
                f"Supported transports: {', '.join(supported_transports)}. "
                f"Template default: {default_transport}",
            }

        # Set the validated transport back to deployment options
        deployment_options.transport = requested_transport

        logger.info(
            f"Using transport: {requested_transport} (supported: {supported_transports})"
        )

        return {"success": True}

    def connect_to_deployment(self, deployment_id: str):
        """
        Connect to deployment shell.
        """
        self.backend.connect_to_deployment(deployment_id)

    def cleanup_stopped_deployments(
        self, template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up stopped/failed deployments.

        Args:
            template_name: If provided, only clean deployments for this template

        Returns:
            Dict with cleanup results
        """
        return self.backend.cleanup_stopped_containers(template_name)

    def cleanup_dangling_images(self) -> Dict[str, Any]:
        """
        Clean up dangling images.

        Returns:
            Dict with cleanup results
        """
        return self.backend.cleanup_dangling_images()
