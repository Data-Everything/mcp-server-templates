"""
Unit tests for volume mount and command argument functionality.

Tests the new functionality that allows config schema properties to be
marked with volume_mount=true or command_arg=true to become Docker
volume mounts or command line arguments instead of environment variables.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_template.deployer import MCPDeployer
from mcp_template.template.utils.discovery import TemplateDiscovery


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

    def test_volume_mount_property_creates_volume_mapping(
        self, mock_template_with_volume_mount
    ):
        """Test that properties with volume_mount=true create Docker volume mappings."""
        deployer = MCPDeployer()

        # Mock config with volume mount value
        config = {"DATA_DIR": "/host/data", "REGULAR_CONFIG": "some_value"}

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_volume_mount, config=config
        )

        # Check that volume was added to template
        template = result["template"]
        assert "/host/data" in template["volumes"]
        assert template["volumes"]["/host/data"] == "/mnt/host/data"

        # Check that volume mount config was removed from config
        updated_config = result["config"]
        assert "DATA_DIR" not in updated_config
        assert "REGULAR_CONFIG" in updated_config  # Regular config should remain

    def test_volume_mount_with_host_container_format(
        self, mock_template_with_volume_mount
    ):
        """Test volume mount with host:container format."""
        deployer = MCPDeployer()

        config = {"DATA_DIR": "/host/data:/app/data", "REGULAR_CONFIG": "some_value"}

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_volume_mount, config=config
        )

        template = result["template"]
        assert "/host/data" in template["volumes"]
        assert template["volumes"]["/host/data"] == "/app/data"

    def test_volume_mount_with_multiple_paths(self, mock_template_with_volume_mount):
        """Test volume mount with space-separated multiple paths."""
        deployer = MCPDeployer()

        config = {"DATA_DIR": "/host/data1 /host/data2", "REGULAR_CONFIG": "some_value"}

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_volume_mount, config=config
        )

        template = result["template"]
        assert "/host/data1" in template["volumes"]
        assert "/host/data2" in template["volumes"]
        assert template["volumes"]["/host/data1"] == "/mnt/host/data1"
        assert template["volumes"]["/host/data2"] == "/mnt/host/data2"

    def test_volume_mount_strips_leading_slash(self, mock_template_with_volume_mount):
        """Test that leading slash is stripped from host path in volume mount."""
        deployer = MCPDeployer()

        config = {
            "DATA_DIR": "/absolute/path",
        }

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_volume_mount, config=config
        )

        template = result["template"]
        # Should strip leading slash in container path
        assert template["volumes"]["/absolute/path"] == "/mnt/absolute/path"


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

    def test_command_arg_property_creates_command_args(
        self, mock_template_with_command_arg
    ):
        """Test that properties with command_arg=true create command line arguments."""
        deployer = MCPDeployer()

        config = {
            "SERVER_ARGS": "--verbose --port 8080",
            "REGULAR_CONFIG": "some_value",
        }

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_command_arg, config=config
        )

        # Check that command arg was added to template
        template = result["template"]
        assert "--verbose --port 8080" in template["command"]

        # Check that command arg config was removed from config
        updated_config = result["config"]
        assert "SERVER_ARGS" not in updated_config
        assert "REGULAR_CONFIG" in updated_config  # Regular config should remain


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

    def test_property_can_be_both_volume_and_command_arg(self, mock_template_with_both):
        """Test that a property can be both a volume mount and command argument."""
        deployer = MCPDeployer()

        config = {"DATA_PATH": "/host/data"}

        result = deployer._handle_volume_and_args_config_properties(
            template=mock_template_with_both, config=config
        )

        template = result["template"]

        # Should be added to both volumes and command
        assert "/host/data" in template["volumes"]
        assert template["volumes"]["/host/data"] == "/mnt/host/data"
        assert "/host/data" in template["command"]

        # Should be removed from config
        updated_config = result["config"]
        assert "DATA_PATH" not in updated_config


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

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    @patch("mcp_template.manager.DeploymentManager.deploy_template")
    def test_deployer_handles_volume_and_command_processing(
        self, mock_deploy, mock_docker, mock_docker_available
    ):
        """Test that the deployer correctly processes volume mounts and command args during deployment."""
        # Mock Docker availability check
        mock_docker_available.return_value = None

        # Mock Docker commands
        mock_docker.return_value = Mock(returncode=0, stdout="[]", stderr="")
        mock_deploy.return_value = {
            "deployment_name": "test-container",
            "status": "deployed",
        }

        deployer = MCPDeployer()

        # Test with demo template that has volume mount and command arg
        config_values = {"allowed_dirs": "/test/data"}

        # This should call _handle_volume_and_args_config_properties internally
        with patch.object(
            deployer, "_handle_volume_and_args_config_properties"
        ) as mock_handler:
            mock_handler.return_value = {
                "template": {
                    "volumes": {"/test/data": "/mnt/test/data"},
                    "command": ["/test/data"],
                },
                "config": {},
            }

            deployer.deploy(
                template_name="demo", config_values=config_values, pull_image=False
            )

            # Verify the handler was called
            mock_handler.assert_called_once()


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    def test_invalid_volume_mount_format_warning(self):
        """Test that invalid volume mount format generates warning."""
        deployer = MCPDeployer()

        template = {
            "config_schema": {
                "properties": {
                    "bad_volume": {"env_mapping": "BAD_VOLUME", "volume_mount": True}
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"BAD_VOLUME": "invalid:format:with:too:many:colons"}

        with patch("mcp_template.deployer.logger") as mock_logger:
            deployer._handle_volume_and_args_config_properties(
                template=template, config=config
            )

            # Should log warning for invalid format
            mock_logger.warning.assert_called_once()

    def test_empty_template_volumes_and_command_initialization(self):
        """Test that empty template gets volumes and command initialized."""
        deployer = MCPDeployer()

        template = {
            "config_schema": {"properties": {}},
            # No volumes or command defined
        }

        config = {}

        result = deployer._handle_volume_and_args_config_properties(
            template=template, config=config
        )

        # Should initialize empty volumes and command
        template = result["template"]
        assert "volumes" in template
        assert "command" in template
        assert isinstance(template["volumes"], dict)
        assert isinstance(template["command"], list)

    def test_none_template_volumes_and_command_handling(self):
        """Test that None values for volumes and command are handled correctly."""
        deployer = MCPDeployer()

        template = {
            "config_schema": {"properties": {}},
            "volumes": None,
            "command": None,
        }

        config = {}

        result = deployer._handle_volume_and_args_config_properties(
            template=template, config=config
        )

        # Should initialize empty volumes and command
        template = result["template"]
        assert template["volumes"] == {}
        assert template["command"] == []
