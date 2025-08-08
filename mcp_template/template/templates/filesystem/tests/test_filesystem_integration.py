"""
Integration tests for Filesystem template.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.template.utils.discovery import TemplateDiscovery


@pytest.mark.integration
class TestFilesystemIntegration:
    """Integration tests for Filesystem template."""

    def test_template_discovery(self):
        """Test that the filesystem template can be discovered."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        assert "filesystem" in templates
        filesystem_template = templates["filesystem"]

        # Verify basic template structure
        assert filesystem_template["name"] == "Filesystem"
        assert "docker_image" in filesystem_template
        assert "config_schema" in filesystem_template

    def test_template_volume_mount_configuration(self):
        """Test that volume mount configuration is properly handled."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        filesystem_template = templates["filesystem"]

        # Check that config schema has volume mount properties
        config_schema = filesystem_template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Find properties with volume_mount=true
        volume_mount_props = {
            prop_name: prop_config
            for prop_name, prop_config in properties.items()
            if prop_config.get("volume_mount") is True
        }

        assert (
            len(volume_mount_props) > 0
        ), "Template should have at least one volume mount property"

        # Check that allowed_dirs is configured as volume mount
        assert "allowed_dirs" in volume_mount_props

    def test_template_command_arg_configuration(self):
        """Test that command argument configuration is properly handled."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        filesystem_template = templates["filesystem"]

        # Check that config schema has command arg properties
        config_schema = filesystem_template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Find properties with command_arg=true
        command_arg_props = {
            prop_name: prop_config
            for prop_name, prop_config in properties.items()
            if prop_config.get("command_arg") is True
        }

        assert (
            len(command_arg_props) > 0
        ), "Template should have at least one command arg property"

        # Check that allowed_dirs is configured as command arg
        assert "allowed_dirs" in command_arg_props

    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_template_stdio_transport(self, mock_run_command):
        """Test that filesystem template uses stdio transport correctly."""
        # Mock docker ps command to return empty (no existing containers)
        mock_run_command.return_value = Mock(returncode=0, stdout="[]", stderr="")

        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        filesystem_template = templates["filesystem"]

        # Verify it's configured for stdio
        transport = filesystem_template.get("transport", {})
        assert transport.get("default") == "stdio"
        assert "stdio" in transport.get("supported", [])
