"""
Deployment backend interface for managing deployments across different platforms.
"""

from mcp_template.backends.base import BaseDeploymentBackend
from mcp_template.backends.docker import DockerDeploymentService
from mcp_template.backends.kubernetes import KubernetesDeploymentService
from mcp_template.backends.mock import MockDeploymentService

__all__ = [
    "BaseDeploymentBackend",
    "DockerDeploymentService",
    "KubernetesDeploymentService",
    "MockDeploymentService",
    "get_backend",
]


def get_backend(backend_type: str = "docker", **kwargs) -> BaseDeploymentBackend:
    """
    Get a deployment backend instance based on type.

    Args:
        backend_type: Type of backend ('docker', 'kubernetes', 'mock')
        **kwargs: Additional arguments for backend initialization

    Returns:
        Backend instance

    Raises:
        ValueError: If backend type is not supported
    """
    if backend_type == "docker":
        return DockerDeploymentService()
    elif backend_type == "kubernetes":
        namespace = kwargs.get("namespace", "mcp-servers")
        kubeconfig_path = kwargs.get("kubeconfig_path")
        return KubernetesDeploymentService(
            namespace=namespace, kubeconfig_path=kubeconfig_path
        )
    elif backend_type == "mock":
        return MockDeploymentService()
    else:
        raise ValueError(f"Unsupported backend type: {backend_type}")
