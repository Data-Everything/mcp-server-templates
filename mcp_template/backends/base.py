"""
Deployment backend interface for managing deployments across different platforms.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseDeploymentBackend(ABC):
    """Abstract base class for deployment backends.

    This defines the interface that all deployment backends must implement,
    ensuring consistency across Docker, Kubernetes, and other deployment targets.
    """

    @abstractmethod
    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """Deploy a template using the backend.

        Args:
            template_id: Unique identifier for the template
            config: Configuration parameters for the deployment
            template_data: Template metadata and configuration
            pull_image: Whether to pull the container image before deployment

        Returns:
            Dict containing deployment information including name, status, etc.
        """
        pass

    @abstractmethod
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all active deployments managed by this backend.

        Returns:
            List of deployment information dictionaries
        """
        pass

    @abstractmethod
    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a deployment.

        Args:
            deployment_name: Name of the deployment to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get the status of a deployment.

        Args:
            deployment_name: Name of the deployment

        Returns:
            Dict containing deployment status information

        Raises:
            ValueError: If deployment is not found
        """
        pass
