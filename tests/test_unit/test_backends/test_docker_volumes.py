"""
Tests for volume mounting functionality in docker backend.

Tests the volume mounting features in the Docker backend,
including volume conversion and docker-specific handling.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService

pytestmark = [pytest.mark.unit, pytest.mark.docker]


class TestDockerBackendVolumeMounting:
    """Test docker backend volume mounting functionality."""

    def test_docker_backend_volume_conversion_dict_to_list(self):
        """Test Docker backend converts dict volumes to list format."""

        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()

        # Mock the volume conversion method if it exists
        with patch.object(
            service,
            "_convert_volumes_to_docker_format",
            return_value=["/host/path:/container/path:ro", "/host/data:/app/data:rw"],
        ) as mock_convert:

            # Test dict format volumes
            volumes_dict = {
                "/host/path": {"bind": "/container/path", "mode": "ro"},
                "/host/data": {"bind": "/app/data", "mode": "rw"},
            }

            converted = service._convert_volumes_to_docker_format(volumes_dict)

            assert isinstance(converted, list)
            assert "/host/path:/container/path:ro" in converted
            assert "/host/data:/app/data:rw" in converted
            mock_convert.assert_called_once_with(volumes_dict)

    def test_docker_backend_volume_conversion_list_passthrough(self):
        """Test Docker backend passes through list format volumes."""

        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()

        # Mock the volume conversion method
        with patch.object(
            service,
            "_convert_volumes_to_docker_format",
            return_value=["/host/path:/container/path:ro", "/host/data:/app/data:rw"],
        ) as mock_convert:

            # Test list format volumes
            volumes_list = ["/host/path:/container/path:ro", "/host/data:/app/data:rw"]

            converted = service._convert_volumes_to_docker_format(volumes_list)

            assert isinstance(converted, list)
            assert converted == volumes_list
            mock_convert.assert_called_once_with(volumes_list)
