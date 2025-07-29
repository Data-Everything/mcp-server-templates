"""
Mock deployment service for testing.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List

from mcp_template.backends import BaseDeploymentBackend

logger = logging.getLogger(__name__)


class MockDeploymentService(BaseDeploymentBackend):
    """Mock deployment service for testing.

    This service simulates deployments without actually creating containers.
    Useful for testing and development scenarios.
    """

    def __init__(self):
        """Initialize mock service."""
        self.deployments = {}

    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        pull_image: bool = True,
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
        }

        self.deployments[deployment_name] = deployment_info
        logger.info("Mock deployment created: %s", deployment_name)
        return deployment_info

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List mock deployments."""
        return [
            {
                "name": name,
                "template": info["template_id"],
                "status": "running",
                "created": info["created_at"],
                "mock": True,
            }
            for name, info in self.deployments.items()
        ]

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete mock deployment."""
        if deployment_name in self.deployments:
            del self.deployments[deployment_name]
            logger.info("Mock deployment deleted: %s", deployment_name)
            return True
        return False

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get mock deployment status."""
        if deployment_name in self.deployments:
            info = self.deployments[deployment_name]
            return {
                "name": deployment_name,
                "template": info["template_id"],
                "status": "running",
                "created": info["created_at"],
                "mock": True,
            }
        raise ValueError(f"Deployment {deployment_name} not found")

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
