"""
Unit tests for volume mount and command argument functionality.

Tests the new functionality that allows config schema properties to be
marked with volume_mount=true or command_arg=true to become Docker
volume mounts or command line arguments instead of environment variables.
"""

import pytest

from mcp_template.template.utils.discovery import TemplateDiscovery

pytestmark = pytest.mark.unit


@pytest.mark.unit
class TestVolumeMountFunctionality:
    """Tests for volume mount functionality."""

    @pytest.fixture
    def mock_template_with_volume_mount(self):
        """Create a mock template with volume mount configuration."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "data_directory": {
                        "type": "string",
                        "description": "Directory to mount as volume",
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                    },
                    "regular_config": {
                        "type": "string",
                        "description": "Regular environment variable",
                        "env_mapping": "REGULAR_CONFIG",
                    },
                },
            },
            "volumes": {},
            "command": [],
        }


@pytest.mark.unit
class TestCommandArgumentFunctionality:
    """Tests for command argument functionality."""

    @pytest.fixture
    def mock_template_with_command_arg(self):
        """Create a mock template with command argument configuration."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "server_args": {
                        "type": "string",
                        "description": "Arguments to pass to server",
                        "env_mapping": "SERVER_ARGS",
                        "command_arg": True,
                    },
                    "regular_config": {
                        "type": "string",
                        "description": "Regular environment variable",
                        "env_mapping": "REGULAR_CONFIG",
                    },
                },
            },
            "volumes": {},
            "command": [],
        }


@pytest.mark.unit
class TestCombinedVolumeMountAndCommandArg:
    """Tests for properties that are both volume mounts and command arguments."""

    @pytest.fixture
    def mock_template_with_both(self):
        """Create a mock template with both volume mount and command arg on same property."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "data_path": {
                        "type": "string",
                        "description": "Path that is both mounted and passed as arg",
                        "env_mapping": "DATA_PATH",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                },
            },
            "volumes": {},
            "command": [],
        }


@pytest.mark.unit
class TestVolumeAndCommandIntegrationWithDeployer:
    """Integration tests with the full deployer workflow."""

    def test_demo_template_volume_command_integration(self):
        """Test the demo template's volume mount and command arg configuration."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Demo template should have the allowed_dirs property with both flags
        if "demo" in templates:
            demo_template = templates["demo"]
            config_schema = demo_template.get("config_schema", {})
            properties = config_schema.get("properties", {})

            if "allowed_dirs" in properties:
                allowed_dirs = properties["allowed_dirs"]
                assert allowed_dirs.get("volume_mount") is True
                assert allowed_dirs.get("command_arg") is True

    def test_filesystem_template_volume_command_integration(self):
        """Test the filesystem template's volume mount and command arg configuration."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Filesystem template should have the allowed_dirs property with both flags
        assert "filesystem" in templates
        filesystem_template = templates["filesystem"]
        config_schema = filesystem_template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        assert "allowed_dirs" in properties
        allowed_dirs = properties["allowed_dirs"]
        assert allowed_dirs.get("volume_mount") is True
        assert allowed_dirs.get("command_arg") is True
