"""
Deployment backend interface for managing deployments across different platforms.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


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
    def stop_deployment(self, deployment_name: str, force: bool = False) -> bool:
        """Stop a deployment.

        Args:
            deployment_name: Name of the deployment to stop
            force: Whether to force stop the deployment

        Returns:
            True if stop was successful, False otherwise
        """
        pass

    @abstractmethod
    def get_deployment_info(self, deployment_name: str, include_logs: bool = False, lines: int = 10) -> Dict[str, Any]:
        """Get detailed information about a specific deployment.

        Args:
            deployment_name: Name or ID of the deployment
            include_logs: Whether to include container logs in the response
            lines: Number of log lines to retrieve (only if include_logs=True)

        Returns:
            Dictionary with deployment information, or None if not found
        """
        pass


    @abstractmethod
    def connect_to_deployment(self, deployment_id: str):
        """
        Connecton to deployment
        Args:
            deployment_name: Name or ID of the deployment

        Returns:
            None - Gives access to deployment shell
        """

        pass