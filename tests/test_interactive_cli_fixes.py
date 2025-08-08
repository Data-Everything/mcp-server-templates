"""
Integration tests for the interactive CLI tool parameter validation and volume mount fixes.

These tests ensure that the specific issues reported by the user are resolved:
1. Tool parameter validation and prompting
2. Volume mount path parsing with Docker artifacts
3. Command line argument parsing for config values
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.interactive_cli import InteractiveCLI
from mcp_template.utils.config_processor import ConfigProcessor


@pytest.mark.integration
class TestInteractiveCLIParameterValidation:
    """Test interactive CLI tool parameter validation improvements."""

    @pytest.fixture
    def mock_interactive_cli(self):
        """Create a mock InteractiveCLI instance."""
        cli = Mock(spec=InteractiveCLI)

        # Mock the enhanced CLI and its components
        cli.enhanced_cli = Mock()
        cli.enhanced_cli.templates = {
            "filesystem": {
                "config_schema": {
                    "properties": {
                        "allowed_dirs": {
                            "type": "string",
                            "env_mapping": "ALLOWED_DIRS",
                            "volume_mount": True,
                            "command_arg": True,
                        }
                    },
                    "required": ["allowed_dirs"],
                },
                "transport": {"default": "stdio", "supported": ["stdio"]},
            }
        }

        # Mock tool discovery
        cli.enhanced_cli.tool_discovery = Mock()
        cli.enhanced_cli.tool_discovery.discover_tools.return_value = [
            {
                "name": "list_directory",
                "description": "List directory contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path to list",
                        }
                    },
                    "required": ["path"],
                },
            }
        ]

        return cli

    def test_parameter_validation_with_missing_required_param(
        self, mock_interactive_cli
    ):
        """Test that parameter validation detects missing required parameters."""
        # Create actual InteractiveCLI instance for the method we're testing
        real_cli = InteractiveCLI()
        real_cli.enhanced_cli = mock_interactive_cli.enhanced_cli

        # Test the parameter validation method
        with (
            patch("rich.prompt.Confirm.ask", return_value=True),
            patch("rich.prompt.Prompt.ask", return_value="/test/path"),
            patch("rich.console.Console.print"),
        ):

            result = real_cli._validate_and_get_tool_parameters(
                "filesystem", "list_directory", "{}", {"allowed_dirs": "/tmp"}
            )

            # Should return updated JSON with the prompted parameter
            assert result is not None
            parsed_result = json.loads(result)
            assert "path" in parsed_result
            assert parsed_result["path"] == "/test/path"

    def test_parameter_validation_with_existing_params(self, mock_interactive_cli):
        """Test that parameter validation succeeds when all required params are provided."""
        real_cli = InteractiveCLI()
        real_cli.enhanced_cli = mock_interactive_cli.enhanced_cli

        with patch("rich.console.Console.print"):
            result = real_cli._validate_and_get_tool_parameters(
                "filesystem",
                "list_directory",
                '{"path": "/existing/path"}',
                {"allowed_dirs": "/tmp"},
            )

            # Should return original args since all required params are present
            assert result == '{"path": "/existing/path"}'

    def test_parameter_validation_graceful_failure(self, mock_interactive_cli):
        """Test that parameter validation fails gracefully when tool discovery fails."""
        real_cli = InteractiveCLI()
        real_cli.enhanced_cli = mock_interactive_cli.enhanced_cli

        # Make tool discovery fail
        mock_interactive_cli.enhanced_cli.tool_discovery.discover_tools.side_effect = (
            Exception("Discovery failed")
        )

        with patch("rich.console.Console.print"):
            result = real_cli._validate_and_get_tool_parameters(
                "filesystem", "list_directory", "{}", {"allowed_dirs": "/tmp"}
            )

            # Should return original args when discovery fails
            assert result == "{}"


@pytest.mark.integration
class TestVolumeMountParsing:
    """Test volume mount parsing with Docker artifacts and complex input."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance."""
        return ConfigProcessor()

    def test_real_world_docker_artifact_input(self, config_processor):
        """Test parsing of input that contains Docker command artifacts."""
        template = {
            "config_schema": {
                "properties": {
                    "allowed_dirs": {
                        "env_mapping": "ALLOWED_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        # This is the actual problematic input from the user
        problematic_input = "/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts:/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts  /home/sam/mcp-data:/data --volume /home/sam/.mcp/logs:/logs --volume /home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools"

        config = {"ALLOWED_DIRS": problematic_input}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should extract valid paths and create proper mappings
        volumes = result["template"]["volumes"]

        # Check expected volume mappings
        expected_volumes = {
            "/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts": "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts",
            "/home/sam/mcp-data": "/data",
            "/home/sam/.mcp/logs": "/logs",
            "/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools": "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools",
        }

        for host_path, expected_container_path in expected_volumes.items():
            assert host_path in volumes
            assert volumes[host_path] == expected_container_path

        # Check command arguments use container paths
        command = result["template"]["command"]
        expected_command_args = [
            "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts",
            "/data",
            "/logs",
            "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools",
        ]

        for expected_arg in expected_command_args:
            assert expected_arg in command

        # Config should be cleaned up
        assert "ALLOWED_DIRS" not in result["config"]

    def test_clean_space_separated_paths(self, config_processor):
        """Test parsing of clean space-separated paths."""
        template = {
            "config_schema": {
                "properties": {
                    "allowed_dirs": {
                        "env_mapping": "ALLOWED_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        clean_input = "/home/sam/scripts /home/sam/tools /home/sam/data"
        config = {"ALLOWED_DIRS": clean_input}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should create individual volume mounts
        volumes = result["template"]["volumes"]
        expected_paths = ["/home/sam/scripts", "/home/sam/tools", "/home/sam/data"]

        for path in expected_paths:
            assert path in volumes
            assert volumes[path] == f"/mnt{path}"

        # Should use container paths in command
        command = result["template"]["command"]
        for path in expected_paths:
            assert f"/mnt{path}" in command

    def test_mixed_host_container_format(self, config_processor):
        """Test parsing of mixed host:container and plain path formats."""
        template = {
            "config_schema": {
                "properties": {
                    "allowed_dirs": {
                        "env_mapping": "ALLOWED_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        mixed_input = (
            "/host/path1:/custom/container1 /host/path2 /host/path3:/custom/container3"
        )
        config = {"ALLOWED_DIRS": mixed_input}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        volumes = result["template"]["volumes"]

        # Check mixed format handling
        assert volumes["/host/path1"] == "/custom/container1"
        assert volumes["/host/path2"] == "/mnt/host/path2"  # Auto-generated
        assert volumes["/host/path3"] == "/custom/container3"

        command = result["template"]["command"]
        assert "/custom/container1" in command
        assert "/mnt/host/path2" in command
        assert "/custom/container3" in command


@pytest.mark.integration
class TestEndToEndCLIFixes:
    """End-to-end tests for the complete CLI fix workflow."""

    def test_filesystem_template_full_workflow(self):
        """Test the complete workflow that was failing for the user."""
        config_processor = ConfigProcessor()

        # Simulate the filesystem template
        filesystem_template = {
            "config_schema": {
                "properties": {
                    "allowed_dirs": {
                        "type": "string",
                        "description": "Allowed directories to scan, create or read from",
                        "env_mapping": "ALLOWED_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                },
                "required": ["allowed_dirs"],
            },
            "volumes": {},
            "command": [],
            "env_vars": {},
            "transport": {"default": "stdio", "supported": ["stdio"]},
        }

        # Simulate user input with space-separated paths
        user_input = "/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts /home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools"
        config_values = {"allowed_dirs": user_input}

        # Step 1: Prepare configuration
        prepared_config = config_processor.prepare_configuration(
            template=filesystem_template, config_values=config_values
        )

        assert "ALLOWED_DIRS" in prepared_config
        assert prepared_config["ALLOWED_DIRS"] == user_input

        # Step 2: Handle volume mounts and command arguments
        result = config_processor.handle_volume_and_args_config_properties(
            filesystem_template, prepared_config
        )

        # Verify results
        template_result = result["template"]
        config_result = result["config"]

        # Should have proper volume mounts
        expected_volumes = {
            "/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts": "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts",
            "/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools": "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools",
        }

        for host_path, expected_container_path in expected_volumes.items():
            assert host_path in template_result["volumes"]
            assert template_result["volumes"][host_path] == expected_container_path

        # Should have container paths in command
        expected_command_args = [
            "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts",
            "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools",
        ]

        for expected_arg in expected_command_args:
            assert expected_arg in template_result["command"]

        # ALLOWED_DIRS should be removed from config since it's now handled as volume mount + command arg
        assert "ALLOWED_DIRS" not in config_result

        # This validates that the Docker command would be constructed correctly
        # (without the problematic host paths as command arguments)
        assert (
            len(
                [
                    arg
                    for arg in template_result["command"]
                    if arg.startswith("/home/sam")
                ]
            )
            == 0
        )
        assert (
            len([arg for arg in template_result["command"] if arg.startswith("/mnt/")])
            == 2
        )
