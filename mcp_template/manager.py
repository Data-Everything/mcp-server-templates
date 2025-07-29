"""
Deployment manager for MCP server templates with backend abstraction.
"""

import logging
from typing import Any, Dict, List

from mcp_template.backends.docker import DockerDeploymentService
from mcp_template.backends.kubernetes import KubernetesDeploymentService
from mcp_template.backends.mock import MockDeploymentService
from mcp_template.template.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Unified deployment manager with backend abstraction."""

    def __init__(self, backend_type: str = "docker"):
        """Initialize deployment manager with specified backend."""
        self.backend_type = backend_type
        self._cached_backend = None
        self.deployment_backend = self._get_deployment_backend()

    def _get_deployment_backend(self):
        """Get the appropriate deployment backend."""
        # Use cached backend if available and backend type hasn't changed
        if self._cached_backend is not None:
            return self._cached_backend

        if self.backend_type == "docker":
            backend = DockerDeploymentService()
        elif self.backend_type == "kubernetes":
            try:
                backend = KubernetesDeploymentService()
            except ImportError as e:
                logger.warning(
                    "Kubernetes client not available, falling back to Docker: %s", e
                )
                backend = DockerDeploymentService()
        else:
            backend = MockDeploymentService()

        # Cache the backend for reuse
        self._cached_backend = backend
        return backend

    def deploy_template(
        self,
        template_id: str,
        configuration: Dict[str, Any] = None,
        template_data: Dict[str, Any] = None,
        pull_image: bool = True,
        # Backward compatibility for tests
        config: Dict[str, Any] = None,
        backend: str = None,
    ) -> Dict[str, Any]:
        """Deploy an MCP server template."""
        # Handle backward compatibility
        if config is not None and configuration is None:
            configuration = config

        # Handle backend override
        if backend is not None:
            original_backend = self.backend_type
            original_deployment_backend = self.deployment_backend
            original_cached_backend = self._cached_backend
            self.backend_type = backend
            self._cached_backend = None  # Clear cache for new backend
            self.deployment_backend = self._get_deployment_backend()
            try:
                result = self._deploy_with_backend(
                    template_id, configuration, template_data, pull_image
                )
            finally:
                self.backend_type = original_backend
                self.deployment_backend = original_deployment_backend
                self._cached_backend = original_cached_backend
            return result

        return self._deploy_with_backend(
            template_id, configuration, template_data, pull_image
        )

    def _deploy_with_backend(
        self,
        template_id: str,
        configuration: Dict[str, Any] = None,
        template_data: Dict[str, Any] = None,
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """Internal deployment method with current backend."""
        if configuration is None:
            raise ValueError("configuration parameter is required")

        if template_data is None:
            raise ValueError("template_data parameter is required")

        # Validate template exists (skip for mock backend in tests)
        if self.backend_type != "mock":
            discovery = TemplateDiscovery()
            available_templates = discovery.discover_templates()
            if template_id not in available_templates:
                raise ValueError(
                    f"Template '{template_id}' not found. Available templates: {list(available_templates.keys())}"
                )

        try:
            logger.info(
                "Deploying template %s with configuration: %s",
                template_id,
                configuration,
            )

            # Get the appropriate backend (may have been overridden)
            backend = self._get_deployment_backend()
            result = backend.deploy_template(
                template_id=template_id,
                config=configuration,
                template_data=template_data,
                pull_image=pull_image,
            )

            logger.info("Successfully deployed template %s", template_id)
            return result

        except Exception as e:
            logger.error("Failed to deploy template %s: %s", template_id, e)
            raise

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all active deployments."""
        return self.deployment_backend.list_deployments()

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a deployment."""
        return self.deployment_backend.delete_deployment(deployment_name)

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get the status of a deployment."""
        return self.deployment_backend.get_deployment_status(deployment_name)
