"""
Tests for Docker backend connect functionality.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService


@pytest.mark.docker
@pytest.mark.unit
class TestDockerConnect:
    """Test Docker backend connect functionality."""

    @pytest.fixture
    def docker_service(self):
        """Create Docker service instance for testing."""
        return DockerDeploymentService()

    def test_connect_to_deployment_container_not_running(self, docker_service):
        """Test connection when container is not running."""
        deployment_id = "test_container"

        # Mock container info showing stopped status
        container_info = {"status": "stopped"}

        with patch.object(
            docker_service, "get_deployment_info", return_value=container_info
        ):
            with pytest.raises(
                RuntimeError, match="Container test_container is not running"
            ):
                docker_service.connect_to_deployment(deployment_id)

    def test_connect_to_deployment_container_not_found(self, docker_service):
        """Test connection when container is not found."""
        deployment_id = "nonexistent_container"

        with patch.object(docker_service, "get_deployment_info", return_value=None):
            with pytest.raises(
                RuntimeError, match="Container nonexistent_container is not running"
            ):
                docker_service.connect_to_deployment(deployment_id)

    def test_connect_to_deployment_shell_detection_success(self, docker_service):
        """Test successful shell detection and connection."""
        deployment_id = "running_container"

        # Mock container info showing running status
        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch("mcp_template.backends.docker.os.execvp") as mock_execvp,
        ):

            # Mock successful shell detection for bash
            mock_run.return_value = Mock(returncode=0)

            # os.execvp should be called and replace the process, so we don't expect return
            docker_service.connect_to_deployment(deployment_id)

            # Verify shell detection was attempted
            mock_run.assert_called()

            # Verify execvp was called with correct arguments
            mock_execvp.assert_called_once_with(
                "docker", ["docker", "exec", "-it", "running_container", "bash"]
            )

    def test_connect_to_deployment_shell_detection_fallback(self, docker_service):
        """Test shell detection with fallback to basic shells."""
        deployment_id = "running_container"

        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch("mcp_template.backends.docker.os.execvp") as mock_execvp,
        ):

            # Mock shell detection failure, forcing fallback
            mock_run.side_effect = subprocess.CalledProcessError(1, "which")

            docker_service.connect_to_deployment(deployment_id)

            # Should fallback to sh or bash
            mock_execvp.assert_called_once()
            args = mock_execvp.call_args[0][1]
            assert args[-1] in ["sh", "bash"]

    def test_connect_to_deployment_all_shells_fail(self, docker_service):
        """Test connection when all shells fail."""
        deployment_id = "running_container"

        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch(
                "mcp_template.backends.docker.os.execvp",
                side_effect=Exception("Connection failed"),
            ),
        ):

            # Mock shell detection failure
            mock_run.side_effect = subprocess.CalledProcessError(1, "which")

            with pytest.raises(
                RuntimeError, match="Could not connect to container running_container"
            ):
                docker_service.connect_to_deployment(deployment_id)

    def test_connect_to_deployment_shell_detection_timeout(self, docker_service):
        """Test shell detection with timeout."""
        deployment_id = "running_container"

        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch("mcp_template.backends.docker.os.execvp") as mock_execvp,
        ):

            # Mock timeout during shell detection
            mock_run.side_effect = subprocess.TimeoutExpired("which", 5)

            docker_service.connect_to_deployment(deployment_id)

            # Should still attempt connection with fallback shells
            mock_execvp.assert_called_once()

    def test_connect_to_deployment_finds_multiple_shells(self, docker_service):
        """Test that connection uses the first available shell."""
        deployment_id = "running_container"

        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch("mcp_template.backends.docker.os.execvp") as mock_execvp,
        ):

            # Mock successful detection of bash (first shell to try)
            def mock_run_side_effect(cmd, **kwargs):
                if "bash" in cmd:
                    return Mock(returncode=0)
                else:
                    return Mock(returncode=1)

            mock_run.side_effect = mock_run_side_effect

            docker_service.connect_to_deployment(deployment_id)

            # Should use bash since it was found first
            mock_execvp.assert_called_once_with(
                "docker", ["docker", "exec", "-it", "running_container", "bash"]
            )

    def test_connect_to_deployment_prefers_bash_over_sh(self, docker_service):
        """Test that bash is preferred over sh when both are available."""
        deployment_id = "running_container"

        container_info = {"status": "running"}

        with (
            patch.object(
                docker_service, "get_deployment_info", return_value=container_info
            ),
            patch("mcp_template.backends.docker.subprocess.run") as mock_run,
            patch("mcp_template.backends.docker.os.execvp") as mock_execvp,
        ):

            # Mock both bash and sh being available
            mock_run.return_value = Mock(returncode=0)

            docker_service.connect_to_deployment(deployment_id)

            # Should prefer bash (first in the list)
            mock_execvp.assert_called_once_with(
                "docker", ["docker", "exec", "-it", "running_container", "bash"]
            )
