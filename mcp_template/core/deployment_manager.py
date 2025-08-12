"""
Deployment Manager - Centralized deployment operations.

This module provides a unified interface for deployment lifecycle management,
consolidating functionality from CLI and MCPClient for deployment operations.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Callable

from mcp_template.backends import get_backend
from mcp_template.core.config_manager import ConfigManager
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
    ):
        self.name = name
        self.transport = transport
        self.port = port
        self.data_dir = data_dir
        self.config_dir = config_dir
        self.pull_image = pull_image
        self.timeout = timeout


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

    def __init__(self, backend_type: str = "docker"):
        """Initialize the deployment manager."""
        self.backend = get_backend(backend_type)
        self.template_manager = TemplateManager(backend_type)
        self.config_manager = ConfigManager()

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

            # Process and merge configuration
            final_config = self.config_manager.merge_config_sources(
                template_config=template_info, **config_sources
            )

            # Validate final configuration
            validation_result = self.config_manager.validate_config(
                final_config, template_info.get("config_schema", {})
            )

            if not validation_result.get("valid", True):
                return DeploymentResult(
                    success=False,
                    error=f"Configuration validation failed: {validation_result.get('errors', [])}",
                    duration=time.time() - start_time,
                )

            # Prepare deployment specification
            deployment_spec = self._prepare_deployment_spec(
                template_id, template_info, final_config, deployment_options
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
            logs = self.backend.get_deployment_logs(
                deployment_id, lines=lines, follow=follow, since=since, until=until
            )

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
    ) -> List[Dict[str, Any]]:
        """
        Find deployments matching specified criteria.

        Args:
            template_name: Filter by template name
            custom_name: Filter by custom deployment name
            deployment_id: Specific deployment ID

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

                # Filter by deployment ID
                if deployment_id and deployment.get("id") != deployment_id:
                    continue

                matching_deployments.append(deployment)

            return matching_deployments

        except Exception as e:
            logger.error(f"Failed to find deployments: {e}")
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
            result = self.backend.deploy(deployment_spec)

            return DeploymentResult(
                success=result.get("success", False),
                deployment_id=result.get("deployment_id"),
                template=result.get("template"),
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
