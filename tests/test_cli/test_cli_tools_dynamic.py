#!/usr/bin/env python3
"""
Tests for enhanced CLI tools command with dynamic Docker discovery.

Tests the new functionality where the tools command can fallback to Docker image
discovery for templates with tool_discovery="dynamic" when standard discovery fails.
"""

import pytest
from unittest.mock import Mock, patch

from mcp_template.cli import EnhancedCLI, handle_enhanced_cli_commands


@pytest.mark.unit
class TestEnhancedCLIToolsDynamic:
    """Test enhanced CLI tools command with dynamic discovery."""

    @pytest.fixture
    def enhanced_cli(self):
        """Create an Enhanced CLI instance with mocked dependencies."""
        with (
            patch("mcp_template.cli.MCPDeployer"),
            patch("mcp_template.cli.TemplateDiscovery"),
            patch("mcp_template.cli.ToolDiscovery"),
            patch("mcp_template.cli.DockerProbe"),
        ):
            cli = EnhancedCLI()

            # Mock templates
            cli.templates = {
                "github": {
                    "name": "Github",
                    "docker_image": "ghcr.io/github/github-mcp-server",
                    "docker_tag": "latest",
                    "tool_discovery": "dynamic",
                },
                "demo": {"name": "Demo", "tool_discovery": "static"},
            }

            # Mock dependencies
            cli.tool_discovery = Mock()
            cli.docker_probe = Mock()
            cli.template_discovery = Mock()

            return cli

    def test_list_tools_standard_discovery_success(self, enhanced_cli, capsys):
        """Test successful tool discovery using standard methods."""
        # Mock successful standard discovery
        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [{"name": "test_tool", "description": "A test tool"}],
            "discovery_method": "static",
            "timestamp": 1234567890,
        }

        enhanced_cli.list_tools("demo")

        # Should not call docker probe
        enhanced_cli.docker_probe.discover_tools_from_image.assert_not_called()

        captured = capsys.readouterr()
        assert "Discovery method: static" in captured.out
        assert "test_tool" in captured.out

    def test_list_tools_dynamic_fallback_success(self, enhanced_cli, capsys):
        """Test fallback to Docker discovery when standard discovery fails."""
        # Mock failed standard discovery
        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [],
            "discovery_method": "unknown",
            "warnings": ["Could not connect to server"],
        }

        # Mock successful Docker discovery
        enhanced_cli.docker_probe.discover_tools_from_image.return_value = {
            "tools": [{"name": "docker_tool", "description": "Tool from Docker"}],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
        }

        enhanced_cli.list_tools("github")

        # Should call docker probe as fallback
        enhanced_cli.docker_probe.discover_tools_from_image.assert_called_once_with(
            "ghcr.io/github/github-mcp-server:latest", None
        )

        captured = capsys.readouterr()
        assert "Discovery method: docker_mcp_stdio" in captured.out
        assert "docker_tool" in captured.out

    def test_list_tools_dynamic_fallback_with_config(self, enhanced_cli, capsys):
        """Test Docker fallback with config values."""
        # Mock failed standard discovery
        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [],
            "discovery_method": "unknown",
        }

        # Mock successful Docker discovery
        enhanced_cli.docker_probe.discover_tools_from_image.return_value = {
            "tools": [{"name": "configured_tool", "description": "Tool with config"}],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
        }

        # Add config schema to template to enable env mapping
        enhanced_cli.templates["github"]["config_schema"] = {
            "properties": {
                "github_token": {"env_mapping": "GITHUB_TOKEN"},
                "log_level": {"env_mapping": "LOG_LEVEL"},
            }
        }

        config_values = {"github_token": "test123", "log_level": "DEBUG"}
        enhanced_cli.list_tools("github", config_values=config_values)

        # Should pass config as server args with env flags
        enhanced_cli.docker_probe.discover_tools_from_image.assert_called_once_with(
            "ghcr.io/github/github-mcp-server:latest",
            ["--env", "GITHUB_TOKEN=test123", "--env", "LOG_LEVEL=DEBUG"],
        )

    def test_list_tools_dynamic_fallback_docker_fails(self, enhanced_cli, capsys):
        """Test when both standard and Docker discovery fail."""
        # Mock failed standard discovery
        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [],
            "discovery_method": "unknown",
        }

        # Mock failed Docker discovery
        enhanced_cli.docker_probe.discover_tools_from_image.return_value = None

        enhanced_cli.list_tools("github")

        captured = capsys.readouterr()
        assert "⚠️  No tools found" in captured.out

    def test_list_tools_static_no_fallback(self, enhanced_cli, capsys):
        """Test that static discovery templates don't use Docker fallback."""
        # Mock failed discovery for static template
        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [],
            "discovery_method": "static",
            "warnings": ["tools.json not found"],
        }

        enhanced_cli.list_tools("demo")

        # Should not call docker probe for static templates
        enhanced_cli.docker_probe.discover_tools_from_image.assert_not_called()

        captured = capsys.readouterr()
        assert "Discovery method: static" in captured.out

    def test_list_tools_no_docker_image(self, enhanced_cli, capsys):
        """Test dynamic template without docker_image config."""
        # Add template without docker_image
        enhanced_cli.templates["nodockerimage"] = {
            "name": "No Docker Image",
            "tool_discovery": "dynamic",
        }

        enhanced_cli.tool_discovery.discover_tools.return_value = {
            "tools": [],
            "discovery_method": "unknown",
        }

        enhanced_cli.list_tools("nodockerimage")

        # Should not call docker probe
        enhanced_cli.docker_probe.discover_tools_from_image.assert_not_called()

    def test_list_tools_template_not_found(self, enhanced_cli, capsys):
        """Test behavior when template is not found."""
        enhanced_cli.list_tools("nonexistent")

        captured = capsys.readouterr()
        assert "❌ Template 'nonexistent' not found" in captured.out

    @patch("mcp_template.cli.console")
    @patch("mcp_template.cli.EnhancedCLI")
    def test_handle_enhanced_cli_commands_tools_with_config(
        self, mock_enhanced_cli, mock_console
    ):
        """Test CLI command handler with config values."""
        args = Mock()
        args.command = "tools"
        args.image = None
        args.template = "github"
        args.config = ["github_token=test123", "log_level=DEBUG"]
        args.no_cache = False
        args.refresh = False
        args.force_server = False

        enhanced_cli = Mock()
        mock_enhanced_cli.return_value = enhanced_cli

        result = handle_enhanced_cli_commands(args)

        assert result is True
        enhanced_cli.list_tools.assert_called_once_with(
            "github",
            no_cache=False,
            refresh=False,
            config_values={"github_token": "test123", "log_level": "DEBUG"},
            force_server_discovery=False,
        )

    @patch("mcp_template.cli.console")
    @patch("mcp_template.cli.EnhancedCLI")
    def test_handle_enhanced_cli_commands_invalid_config_format(
        self, mock_enhanced_cli_class, mock_console
    ):
        """Test CLI command handler with invalid config format."""
        # Mock args with invalid config
        args = Mock()
        args.command = "tools"
        args.image = None
        args.template = "github"
        args.config = ["invalid_format"]  # Missing =

        # Mock the enhanced CLI instance
        enhanced_cli_instance = Mock()
        mock_enhanced_cli_class.return_value = enhanced_cli_instance

        result = handle_enhanced_cli_commands(args)

        assert result is False
        # Should print error message about invalid config format
        mock_console.print.assert_called_with(
            "[red]❌ Invalid config format: invalid_format. Use KEY=VALUE[/red]"
        )

    @patch("mcp_template.cli.console")
    def test_handle_enhanced_cli_commands_tools_help_examples(self, mock_console_class):
        """Test that help examples include config option."""
        # Mock console instance
        mock_console = Mock()
        mock_console_class.return_value = mock_console

        args = Mock()
        args.command = "tools"
        args.image = None
        args.template = None
        args.config = None

        result = handle_enhanced_cli_commands(args)

        assert result is False
        # Get console output
        mock_console_class.print.assert_called()
        output = "".join(str(call) for call in mock_console_class.print.call_args_list)
        assert "Must provide either a template name" in output


class TestEnhancedCLIIntegration:
    """Integration tests for enhanced CLI functionality."""

    def test_real_template_discovery_fallback(self):
        """Test template discovery with real Template Discovery but mocked Docker."""
        with (
            patch("mcp_template.cli.MCPDeployer"),
            patch("mcp_template.cli.DockerProbe") as mock_docker_probe,
        ):

            # Mock Docker probe to return tools
            mock_docker_probe.return_value.discover_tools_from_image.return_value = {
                "tools": [
                    {"name": "integration_tool", "description": "Integration test tool"}
                ],
                "discovery_method": "docker_mcp_stdio",
                "timestamp": 1234567890,
            }

            cli = EnhancedCLI()

            # Mock a template with dynamic discovery
            cli.templates = {
                "test": {
                    "name": "Test Template",
                    "tool_discovery": "dynamic",
                    "docker_image": "test/image",
                    "docker_tag": "latest",
                }
            }

            # This should work with real TemplateDiscovery but mocked Docker
            cli.list_tools("test")

            # Verify Docker probe was called
            mock_docker_probe.return_value.discover_tools_from_image.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
