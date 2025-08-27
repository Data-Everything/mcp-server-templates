"""
Unit tests for new CLI commands.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.core.deployment_manager import DeploymentManager

pytestmark = pytest.mark.unit


@pytest.mark.docker
class TestCommandIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def deployment_manager(self):
        """Create deployment manager for testing."""
        return DeploymentManager("docker")

    def test_cleanup_integration(self, deployment_manager):
        """Test cleanup integration between components."""
        # Test that cleanup flows correctly through the stack
        with patch.object(
            deployment_manager.backend, "cleanup_stopped_containers"
        ) as mock_cleanup:
            mock_cleanup.return_value = {
                "success": True,
                "cleaned_containers": [],
                "failed_cleanups": [],
                "message": "No stopped containers to clean up",
            }

            result = deployment_manager.cleanup_stopped_deployments()

            assert result["success"] is True
            mock_cleanup.assert_called_once_with(None)

    def test_cleanup_with_template_integration(self, deployment_manager):
        """Test cleanup with template filter integration."""
        with patch.object(
            deployment_manager.backend, "cleanup_stopped_containers"
        ) as mock_cleanup:
            mock_cleanup.return_value = {
                "success": True,
                "cleaned_containers": [{"id": "container1", "name": "demo_1"}],
                "failed_cleanups": [],
                "message": "Cleaned up 1 containers",
            }

            result = deployment_manager.cleanup_stopped_deployments("demo")

            assert result["success"] is True
            mock_cleanup.assert_called_once_with("demo")

    def test_connect_integration(self, deployment_manager):
        """Test connect integration between components."""
        deployment_id = "test_container"

        with patch.object(
            deployment_manager.backend, "connect_to_deployment"
        ) as mock_connect:
            deployment_manager.connect_to_deployment(deployment_id)

            mock_connect.assert_called_once_with(deployment_id)

    def test_dangling_images_cleanup_integration(self, deployment_manager):
        """Test dangling images cleanup integration."""
        with patch.object(
            deployment_manager.backend, "cleanup_dangling_images"
        ) as mock_cleanup:
            mock_cleanup.return_value = {
                "success": True,
                "cleaned_images": ["img1", "img2"],
                "message": "Cleaned up 2 dangling images",
            }

            result = deployment_manager.cleanup_dangling_images()

            assert result["success"] is True
            assert len(result["cleaned_images"]) == 2
            mock_cleanup.assert_called_once()
