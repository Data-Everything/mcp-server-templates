"""
Tests for volume mounting functionality in docker backend.

Tests the volume mounting features in the Docker backend,
focusing on current volume preparation functionality.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService

pytestmark = [pytest.mark.unit, pytest.mark.docker]


class TestDockerBackendVolumeMounting:
    """Test docker backend volume mounting functionality."""

    def test_docker_backend_volume_preparation(self):
        """Test Docker backend prepares volume mounts correctly."""

        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()

        # Test volume preparation from template data
        template_data = {
            "volumes": {"/host/path": "/container/path", "/host/data": "/app/data"}
        }

        with patch("os.makedirs"), patch("os.path.expanduser", side_effect=lambda x: x):
            volumes = service._prepare_volume_mounts(template_data)

        # Should return Docker CLI arguments
        assert isinstance(volumes, list)
        expected_volumes = [
            "--volume",
            "/host/path:/container/path",
            "--volume",
            "/host/data:/app/data",
        ]
        assert volumes == expected_volumes
