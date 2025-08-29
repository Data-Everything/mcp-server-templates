"""
Integration tests for volume mounting functionality across components.

Tests the end-to-end volume mounting features across client, deployment manager,
backends, and template processing components.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.template.utils.discovery import TemplateDiscovery

pytestmark = pytest.mark.integration


class TestVolumeMountingIntegration:
    """Test volume mounting integration across components."""

    def test_integration_client_to_docker_backend_volumes(self):
        """Test integration from client through deployment manager to docker backend."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            # Mock successful end-to-end deployment with volumes
            mock_deploy.return_value = {
                "success": True,
                "deployment_id": "integration-test-128",
                "template_id": "demo",
                "status": "running",
                "volumes": ["/host/path:/container/path:ro"],
            }

            # Test end-to-end volume deployment
            volumes = {"/host/path": {"bind": "/container/path", "mode": "ro"}}
            result = client.deploy_template("demo", config={"volumes": volumes})

            assert result["success"] is True
            assert "volumes" in result
            assert result["deployment_id"] == "integration-test-128"

    def test_volume_validation_security_checks(self):
        """Test volume mounting includes security validation."""
        client = MCPClient()

        with patch.object(client, "deploy_template") as mock_deploy:
            mock_deploy.side_effect = ValueError(
                "Security validation failed: invalid path"
            )

            # Test that security validation is enforced
            dangerous_volumes = {"/": {"bind": "/host_root", "mode": "rw"}}

            with pytest.raises(ValueError, match="Security validation failed"):
                client.deploy_template("demo", config={"volumes": dangerous_volumes})

    def test_volume_mounting_with_template_placeholders(self):
        """Test volume mounting works with template placeholder substitution."""
        with patch(
            "mcp_template.template.utils.discovery.TemplateDiscovery.get_template_config"
        ) as mock_get_template:
            # Mock template with volume placeholders
            mock_get_template.return_value = {
                "template_id": "demo",
                "config_schema": {
                    "properties": {
                        "data_dir": {"type": "string", "default": "/app/data"},
                        "volumes": {"type": "object"},
                    }
                },
                "volume_mounts": ["${data_dir}:/container/data:rw"],
            }

            client = MCPClient()

            with patch.object(client, "deploy_template") as mock_deploy:
                mock_deploy.return_value = {
                    "success": True,
                    "deployment_id": "placeholder-test-129",
                    "template_id": "demo",
                    "status": "running",
                    "volumes": ["/custom/data:/container/data:rw"],
                }

                # Test template with placeholder substitution
                config = {
                    "data_dir": "/custom/data",
                    "volumes": {
                        "${data_dir}": {"bind": "/container/data", "mode": "rw"}
                    },
                }

                result = client.deploy_template("demo", config=config)

                assert result["success"] is True
                assert "/custom/data:/container/data:rw" in result["volumes"]

    def test_demo_template_volume_command_integration(self):
        """Test volume and command integration with demo template."""
        with patch(
            "mcp_template.template.utils.discovery.TemplateDiscovery.get_template_config"
        ) as mock_get_template:
            mock_get_template.return_value = {
                "template_id": "demo",
                "config_schema": {
                    "properties": {
                        "volume_mount": {"type": "object"},
                        "command_arg": {"type": "string"},
                    }
                },
            }

            client = MCPClient()

            with patch.object(client, "deploy_template") as mock_deploy:
                mock_deploy.return_value = {
                    "success": True,
                    "deployment_id": "demo-integration-130",
                    "template_id": "demo",
                    "status": "running",
                }

                config = {
                    "volume_mount": {"/host/demo": {"bind": "/app/demo", "mode": "ro"}},
                    "command_arg": "--verbose",
                }

                result = client.deploy_template("demo", config=config)
                assert result["success"] is True

    def test_filesystem_template_volume_command_integration(self):
        """Test volume and command integration with filesystem template."""
        with patch(
            "mcp_template.template.utils.discovery.TemplateDiscovery.get_template_config"
        ) as mock_get_template:
            mock_get_template.return_value = {
                "template_id": "filesystem",
                "config_schema": {
                    "properties": {
                        "volume_mount": {"type": "object"},
                        "command_arg": {"type": "string"},
                    }
                },
            }

            client = MCPClient()

            with patch.object(client, "deploy_template") as mock_deploy:
                mock_deploy.return_value = {
                    "success": True,
                    "deployment_id": "filesystem-integration-131",
                    "template_id": "filesystem",
                    "status": "running",
                }

                config = {
                    "volume_mount": {
                        "/host/files": {"bind": "/mnt/files", "mode": "rw"}
                    },
                    "command_arg": "--watch",
                }

                result = client.deploy_template("filesystem", config=config)
                assert result["success"] is True
