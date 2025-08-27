"""
Tests for volume mounting functionality in deployment manager.

Tests the volume mounting features in the DeploymentManager,
including volume processing and backend integration.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.core.deployment_manager import DeploymentManager, DeploymentResult

pytestmark = pytest.mark.unit


class TestDeploymentManagerVolumeMounting:
    """Test deployment manager volume mounting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.deployment_manager = DeploymentManager("docker")
        self.deployment_manager.backend = self.mock_backend

    def test_deployment_manager_volume_handling_dict(self):
        """Test DeploymentManager handles dict format volumes correctly."""
        from mcp_template.core.deployment_manager import DeploymentOptions

        # Mock backend response
        self.mock_backend.deploy_template.return_value = {
            "success": True,
            "deployment_id": "test-deploy-126",
            "template_id": "demo",
            "status": "running",
        }

        # Test configuration with dict volumes
        config = {
            "volumes": {
                "/host/path": {"bind": "/container/path", "mode": "ro"},
                "/host/data": {"bind": "/app/data", "mode": "rw"},
            }
        }

        deployment_options = DeploymentOptions()

        result = self.deployment_manager.deploy_template(
            "demo", config, deployment_options
        )

        assert isinstance(result, DeploymentResult)
        assert result.success is True
        assert result.deployment_id == "test-deploy-126"
        self.mock_backend.deploy_template.assert_called_once()

    def test_deployment_manager_volume_handling_list(self):
        """Test DeploymentManager handles list format volumes correctly."""
        from mcp_template.core.deployment_manager import DeploymentOptions

        # Mock backend response
        self.mock_backend.deploy_template.return_value = {
            "success": True,
            "deployment_id": "test-deploy-127",
            "template_id": "demo",
            "status": "running",
        }

        # Test configuration with list volumes
        config = {
            "volumes": ["/host/path:/container/path:ro", "/host/data:/app/data:rw"]
        }

        deployment_options = DeploymentOptions()

        result = self.deployment_manager.deploy_template(
            "demo", config, deployment_options
        )

        assert isinstance(result, DeploymentResult)
        assert result.success is True
        assert result.deployment_id == "test-deploy-127"
        self.mock_backend.deploy_template.assert_called_once()
