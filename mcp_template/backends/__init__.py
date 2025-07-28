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
]
