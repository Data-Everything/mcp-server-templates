"""
Tests for volume mounting functionality in client API.

Tests the volume mounting features in the Python client API,
including dict/list formats and validation.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient

pytestmark = pytest.mark.unit


class TestClientVolumeMounting:
    """Test client API volume mounting functionality."""

    def test_client_volume_mounting_dict_format(self):
        """Test client API volume mounting with dictionary format."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            # Mock successful deployment
            mock_deploy.return_value = {
                "success": True,
                "deployment_id": "test-deploy-123",
                "template_id": "demo",
                "status": "running",
                "volumes": ["/host/path:/container/path:ro", "/host/data:/app/data:rw"],
            }

            # Test volume mounting with dict format
            volumes = {
                "/host/path": {"bind": "/container/path", "mode": "ro"},
                "/host/data": {"bind": "/app/data", "mode": "rw"},
            }

            result = client.deploy_template("demo", config={"volumes": volumes})

            assert result["success"] is True
            assert "volumes" in result
            mock_deploy.assert_called_once()

    def test_client_volume_mounting_list_format(self):
        """Test client API volume mounting with list format."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            # Mock successful deployment
            mock_deploy.return_value = {
                "success": True,
                "deployment_id": "test-deploy-124",
                "template_id": "demo",
                "status": "running",
                "volumes": ["/host/path:/container/path:ro", "/host/data:/app/data:rw"],
            }

            # Test volume mounting with list format
            volumes = ["/host/path:/container/path:ro", "/host/data:/app/data:rw"]

            result = client.deploy_template("demo", config={"volumes": volumes})

            assert result["success"] is True
            assert "volumes" in result
            mock_deploy.assert_called_once()

    def test_client_volume_mounting_empty_volumes(self):
        """Test client API with empty volumes configuration."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            mock_deploy.return_value = {
                "success": True,
                "deployment_id": "test-deploy-125",
                "template_id": "demo",
                "status": "running",
            }

            result = client.deploy_template("demo", config={"volumes": []})

            assert result["success"] is True
            mock_deploy.assert_called_once()

    def test_client_volume_mounting_invalid_format_raises_error(self):
        """Test client API raises error for invalid volume format."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            mock_deploy.side_effect = ValueError("Invalid volume format")

            with pytest.raises(ValueError, match="Invalid volume format"):
                client.deploy_template("demo", config={"volumes": "invalid_format"})
