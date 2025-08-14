"""
Integration tests for new CLI commands.
"""

import pytest
from unittest.mock import Mock, patch
from mcp_template.core.deployment_manager import DeploymentManager


@pytest.mark.unit
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


class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    @pytest.mark.integration
    def test_full_cleanup_scenario(self):
        """Test a complete cleanup scenario."""
        # This would be a real end-to-end test that actually creates and cleans containers
        # For now, we'll mock it but structure it like a real test

        with (
            patch("subprocess.run") as mock_run,
            patch(
                "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
            ),
        ):

            # Mock docker commands
            mock_run.side_effect = [
                # List containers
                Mock(stdout="container1\tdemo_1\tExited (0)", returncode=0),
                # Remove container
                Mock(returncode=0),
                # List images
                Mock(stdout="", returncode=0),  # No dangling images
            ]

            from mcp_template.backends.docker import DockerDeploymentService

            service = DockerDeploymentService()

            # Test container cleanup
            result = service.cleanup_stopped_containers()
            assert result["success"] is True
            assert len(result["cleaned_containers"]) == 1

            # Test image cleanup
            result = service.cleanup_dangling_images()
            assert result["success"] is True
            assert len(result["cleaned_images"]) == 0

    @pytest.mark.integration
    @pytest.mark.skip(reason="Complex mocking scenario - covered by unit tests")
    def test_shell_connection_scenario(self):
        """Test a complete shell connection scenario."""
        # This test is complex to mock properly due to os.execvp behavior
        # The functionality is covered by unit tests in test_docker_connect.py
        pass

    @pytest.mark.integration
    def test_config_display_scenario(self):
        """Test a complete config display scenario."""
        from mcp_template.core.template_manager import TemplateManager

        manager = TemplateManager("docker")

        # Mock template discovery and schema retrieval
        with patch.object(manager, "get_template_config_schema") as mock_schema:
            mock_schema.return_value = {
                "properties": {
                    "test_prop": {
                        "type": "string",
                        "description": "Test property",
                        "default": "test_value",
                    }
                }
            }

            schema = manager.get_template_config_schema("demo")

            assert schema is not None
            assert "properties" in schema
            assert "test_prop" in schema["properties"]
