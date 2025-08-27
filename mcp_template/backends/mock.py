"""
Mock deployment service for testing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mcp_template.backends import BaseDeploymentBackend

logger = logging.getLogger(__name__)


class MockDeploymentService(BaseDeploymentBackend):
    """Mock deployment service for testing.

    This service simulates deployments without actually creating containers.
    Useful for testing and development scenarios.
    """

    def __init__(self):
        """Initialize mock service."""
        super().__init__()
        self.deployments = {}
        self.backend_type = "mock"

    @property
    def is_available(self):
        """
        Ensure backend is available
        """

        return True

    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        backend_config: Dict[str, Any],
        pull_image: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Mock template deployment."""
        # Validate template_data has required fields
        if not template_data.get("docker_image") and not template_data.get("image"):
            raise ValueError(
                f"Template data missing required docker image information for template '{template_id}'"
            )

        deployment_name = f"mcp-{template_id}-{datetime.now().strftime('%m%d-%H%M')}-{str(uuid.uuid4())[:8]}"

        # Call _deploy_container to enable test mocking and failure simulation
        image = template_data.get(
            "docker_image", template_data.get("image", "test").split(":")[0]
        )
        tag = template_data.get(
            "docker_tag",
            (
                template_data.get("image", "test:latest").split(":")[-1]
                if ":" in template_data.get("image", "")
                else "latest"
            ),
        )
        full_image = f"{image}:{tag}"

        # Extract ports and environment variables for container deployment
        ports = []
        env_vars = []
        volumes = []

        container_id = self._deploy_container(
            deployment_name, full_image, env_vars, ports, volumes
        )

        deployment_info = {
            "deployment_name": deployment_name,
            "template_id": template_id,
            "configuration": config,
            "template_data": template_data,
            "status": "deployed",
            "created_at": datetime.now().isoformat(),
            "mock": True,
            "container_id": container_id,
            "transport": config.get(
                "MCP_TRANSPORT", "stdio"
            ),  # Extract transport from config
        }

        self.deployments[deployment_name] = deployment_info
        logger.info("Mock deployment created: %s", deployment_name)
        return deployment_info

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List mock deployments."""
        deployments = []
        for name, info in self.deployments.items():
            # Mock always uses stdio transport, no real endpoint or ports
            deployment = {
                "name": name,
                "template": info.get("template_id", "unknown"),
                "status": "running",
                "created": info.get("created_at"),
                "mock": True,
                "endpoint": None,
                "ports": None,
                "transport": "stdio",
            }
            deployments.append(deployment)
        return deployments

    def delete_deployment(
        self, deployment_name: str, raise_on_failure: bool = False
    ) -> bool:
        """Delete mock deployment."""
        if deployment_name in self.deployments:
            del self.deployments[deployment_name]
            logger.info("Mock deployment deleted: %s", deployment_name)
            return True
        if raise_on_failure:
            raise ValueError(f"Deployment {deployment_name} not found")
        return False

    def get_deployment_info(
        self, deployment_name: str, include_logs: bool = False, lines: int = 10
    ) -> Dict[str, Any]:
        """Get detailed mock deployment info."""
        if deployment_name in self.deployments:
            info = self.deployments[deployment_name].copy()
            # Add unified fields to match docker backend
            info.update(
                {
                    "name": deployment_name,
                    "status": "running",
                    "running": True,
                    "mock": True,
                }
            )
            # Add logs if requested
            if include_logs:
                info["logs"] = f"Mock logs for {deployment_name} (last {lines} lines)"
            return info
        return None

    def stop_deployment(self, deployment_name: str, force: bool = False) -> bool:
        """Stop mock deployment."""
        if deployment_name in self.deployments:
            self.deployments[deployment_name]["status"] = "stopped"
            logger.info("Mock deployment stopped: %s", deployment_name)
            return True
        return False

    def get_deployment_logs(
        self,
        deployment_name: str,
        lines: int = 100,
        follow: bool = False,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get mock deployment logs."""
        if deployment_name in self.deployments:
            logs = f"Mock log line 1 for {deployment_name}\nMock log line 2 for {deployment_name}\nMock log line 3 for {deployment_name}"
            return {
                "success": True,
                "logs": logs,
                "lines_returned": len(logs.split("\n")),
            }
        return {
            "success": False,
            "error": f"Deployment {deployment_name} not found",
            "logs": "",
            "lines_returned": 0,
        }

    def force_stop_deployment(self, deployment_name: str) -> bool:
        """Force stop mock deployment."""
        return self.stop_deployment(deployment_name, force=True)

    def stream_deployment_logs(self, deployment_name: str, lines: int = 100):
        """Stream mock deployment logs."""
        logs = self.get_deployment_logs(deployment_name, lines)
        for log_line in logs.split("\n"):
            if log_line:
                yield log_line

    def list_all_deployments(self) -> List[Dict[str, Any]]:
        """Alias for list_deployments for test compatibility."""
        return self.list_deployments()

    def _deploy_container(
        self,
        container_name: str,
        image: str,
        env_vars: list,
        ports: list,
        volumes: list,
    ) -> str:
        """Mock container deployment method for test compatibility."""
        return f"mock-container-{container_name}"

    def deploy(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """Alias for deploy_template for test compatibility."""
        return self.deploy_template(template_id, config, template_data, pull_image)

    def cleanup_dangling_images(self) -> Dict[str, Any]:
        """Mock implementation for cleanup_dangling_images."""
        logger.info("Mock: Cleaning up dangling images")
        return {
            "success": True,
            "cleaned": 0,
            "errors": [],
            "message": "Mock cleanup - no actual images to clean",
        }

    def cleanup_stopped_containers(self) -> Dict[str, Any]:
        """Mock implementation for cleanup_stopped_containers."""
        logger.info("Mock: Cleaning up stopped containers")
        return {
            "success": True,
            "cleaned": 0,
            "errors": [],
            "message": "Mock cleanup - no actual containers to clean",
        }

    def connect_to_deployment(self, deployment_id: str) -> Optional[str]:
        """Mock implementation for connect_to_deployment."""
        logger.info("Mock: Connecting to deployment %s", deployment_id)
        if deployment_id in self.deployments:
            return f"mock-connection-{deployment_id}"
        return None
