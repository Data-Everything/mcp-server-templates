"""
Tests for Docker backend cleanup functionality.
"""

import subprocess
from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService


@pytest.mark.docker
@pytest.mark.unit
class TestDockerCleanup:
    """Test Docker backend cleanup functionality."""

    @pytest.fixture
    def docker_service(self):
        """Create Docker service instance for testing."""
        return DockerDeploymentService()

    def test_cleanup_stopped_containers_success(self, docker_service):
        """Test successful cleanup of stopped containers."""
        # Mock docker ps output
        ps_output = "container1\tdemo_1\tExited (0) 2 hours ago\ncontainer2\tdemo_2\tExited (1) 1 hour ago"

        # Mock subprocess calls
        with patch("subprocess.run") as mock_run:
            # Mock docker ps call
            mock_run.side_effect = [
                Mock(stdout=ps_output, returncode=0),  # docker ps
                Mock(returncode=0),  # docker rm container1
                Mock(returncode=0),  # docker rm container2
            ]

            result = docker_service.cleanup_stopped_containers()

            # Verify result
            assert result["success"] is True
            assert len(result["cleaned_containers"]) == 2
            assert result["cleaned_containers"][0]["id"] == "container1"
            assert result["cleaned_containers"][1]["id"] == "container2"
            assert len(result["failed_cleanups"]) == 0

    def test_cleanup_stopped_containers_with_template_filter(self, docker_service):
        """Test cleanup with template filter."""
        ps_output = "container1\tdemo_1\tExited (0) 2 hours ago"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(stdout=ps_output, returncode=0),  # docker ps
                Mock(returncode=0),  # docker rm
            ]

            result = docker_service.cleanup_stopped_containers("demo")

            # Verify docker ps was called with template filter
            ps_call = mock_run.call_args_list[0]
            assert "--filter" in ps_call[0][0]
            assert "label=mcp.template=demo" in ps_call[0][0]

    def test_cleanup_stopped_containers_no_containers(self, docker_service):
        """Test cleanup when no containers are found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)

            result = docker_service.cleanup_stopped_containers()

            assert result["success"] is True
            assert len(result["cleaned_containers"]) == 0
            assert result["message"] == "No stopped containers to clean up"

    def test_cleanup_stopped_containers_removal_failure(self, docker_service):
        """Test cleanup with container removal failures."""
        ps_output = "container1\tdemo_1\tExited (0) 2 hours ago\ncontainer2\tdemo_2\tExited (1) 1 hour ago"

        with patch("subprocess.run") as mock_run:
            # Mock docker ps success, first rm success, second rm failure
            mock_run.side_effect = [
                Mock(stdout=ps_output, returncode=0),  # docker ps
                Mock(returncode=0),  # docker rm container1 (success)
                subprocess.CalledProcessError(
                    1, "docker rm"
                ),  # docker rm container2 (failure)
            ]

            result = docker_service.cleanup_stopped_containers()

            # Should succeed overall but report failed cleanups
            assert result["success"] is False
            assert len(result["cleaned_containers"]) == 1
            assert len(result["failed_cleanups"]) == 1
            assert result["failed_cleanups"][0]["container"]["id"] == "container2"

    def test_cleanup_stopped_containers_ps_failure(self, docker_service):
        """Test cleanup when docker ps fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "docker ps")

            result = docker_service.cleanup_stopped_containers()

            assert result["success"] is False
            assert "Failed to list containers" in result["error"]
            assert len(result["cleaned_containers"]) == 0

    def test_cleanup_dangling_images_success(self, docker_service):
        """Test successful cleanup of dangling images."""
        images_output = "sha256:abc123\nsha256:def456"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(stdout=images_output, returncode=0),  # docker images
                Mock(returncode=0),  # docker rmi
            ]

            result = docker_service.cleanup_dangling_images()

            assert result["success"] is True
            assert len(result["cleaned_images"]) == 2
            assert "sha256:abc123" in result["cleaned_images"]
            assert "sha256:def456" in result["cleaned_images"]

    def test_cleanup_dangling_images_no_images(self, docker_service):
        """Test cleanup when no dangling images are found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", returncode=0)

            result = docker_service.cleanup_dangling_images()

            assert result["success"] is True
            assert len(result["cleaned_images"]) == 0
            assert result["message"] == "No dangling images to clean up"

    def test_cleanup_dangling_images_removal_failure(self, docker_service):
        """Test cleanup when image removal fails."""
        images_output = "sha256:abc123"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(stdout=images_output, returncode=0),  # docker images
                subprocess.CalledProcessError(1, "docker rmi"),  # docker rmi failure
            ]

            result = docker_service.cleanup_dangling_images()

            assert result["success"] is False
            assert "Failed to remove dangling images" in result["error"]
            assert len(result["cleaned_images"]) == 0

    def test_cleanup_dangling_images_list_failure(self, docker_service):
        """Test cleanup when listing images fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "docker images")

            result = docker_service.cleanup_dangling_images()

            assert result["success"] is False
            assert "Failed to list dangling images" in result["error"]
            assert len(result["cleaned_images"]) == 0
