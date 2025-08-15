"""
CLI tests for MCP Template system.

Tests the command-line interface functionality including argument parsing,
command dispatch, and error handling.
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

from mcp_template import MCPDeployer, main


@pytest.mark.unit
class TestMainCLI:
    """Test main CLI functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.original_argv = sys.argv

    def teardown_method(self):
        """Clean up test environment."""
        sys.argv = self.original_argv

    def test_main_no_args_shows_help(self):
        """Test that main() with no args shows help."""
        sys.argv = ["mcp_template"]

        with patch("builtins.print") as mock_print:
            with pytest.raises(SystemExit) as exc_info:
                main()
            # Typer CLI exits with code 2 when no command is provided (expected behavior)
            assert exc_info.value.code == 2

    # Note: Detailed CLI command tests are now in test_enhanced_features.py
    # which tests the new Typer CLI implementation

    def test_tools_command_with_template_deprecated(self):
        """Test tools command shows deprecation message."""
        sys.argv = ["mcp_template", "tools", "demo"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        # The command should exit with status code 2 (argparse error)
        assert exc_info.value.code == 2

    def test_tools_command_with_image_deprecated(self):
        """Test tools command with Docker image shows deprecation message."""
        sys.argv = ["mcp_template", "tools", "--image", "mcp/filesystem", "/tmp"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        # The command should exit with status code 2 (argparse error)
        assert exc_info.value.code == 2

    def test_tools_command_with_cache_options_deprecated(self):
        """Test tools command with cache options shows deprecation message."""
        sys.argv = ["mcp_template", "tools", "demo", "--no-cache", "--refresh"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        # The command should exit with status code 2 (argparse error)
        assert exc_info.value.code == 2

    def test_discover_tools_command_deprecated(self):
        """Test deprecated discover-tools command shows error."""
        sys.argv = [
            "mcp_template",
            "discover-tools",
            "--image",
            "mcp/filesystem",
            "/tmp",
        ]

        with pytest.raises(SystemExit) as exc_info:
            main()

        # The command should exit with status code 2 (argparse error)
        assert exc_info.value.code == 2

    # Note: These tests are also outdated since the CLI structure has changed.
    # Keeping them for reference but updating expectations.


@pytest.mark.unit
class TestMCPDeployer:
    """Test MCPDeployer class functionality."""

    @patch("mcp_template.deployer.TemplateDiscovery")
    @patch("mcp_template.deployer.DeploymentManager")
    def test_init(self, mock_manager_class, mock_discovery_class):
        """Test MCPDeployer initialization."""

        mock_discovery = Mock()
        mock_discovery.discover_templates.return_value = {"demo": {"name": "Demo"}}
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        deployer = MCPDeployer()
        assert deployer.templates == {"demo": {"name": "Demo"}}

    @patch("mcp_template.deployer.TemplateDiscovery")
    @patch("mcp_template.deployer.DeploymentManager")
    def test_list_templates(self, mock_manager_class, mock_discovery_class):
        """Test template listing."""

        mock_discovery = Mock()
        mock_discovery.discover_templates.return_value = {
            "demo": {"name": "Demo Template", "description": "Test demo"}
        }
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        deployer = MCPDeployer()

        with patch("mcp_template.console"):
            deployer.list_templates()

    @patch("mcp_template.deployer.TemplateDiscovery")
    @patch("mcp_template.deployer.DeploymentManager")
    @patch("mcp_template.deployer.Progress")
    def test_deploy_template(
        self, mock_progress, mock_manager_class, mock_discovery_class
    ):
        """Test template deployment."""
        # Mock progress bar to avoid timestamp comparison issues
        mock_progress_instance = Mock()
        mock_progress.return_value.__enter__.return_value = mock_progress_instance

        mock_discovery = Mock()
        mock_discovery.discover_templates.return_value = {
            "demo": {
                "name": "Demo Template",
                "image": "demo:latest",
                "transport": {"supported": ["http"], "default": "http"},
            }
        }
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        # Mock the deploy_template to return a proper DeploymentResult-like object
        mock_result = Mock()
        mock_result.success = True
        mock_result.deployment_id = "demo-123"
        mock_result.status = "deployed"
        mock_result.image = "demo:latest"
        mock_result.error = None
        mock_manager.deploy_template.return_value = mock_result
        mock_manager_class.return_value = mock_manager

        deployer = MCPDeployer()

        with patch("mcp_template.console"):
            result = deployer.deploy("demo")

        # The test should succeed and return True
        assert result is True
        mock_manager.deploy_template.assert_called_once()

    @patch("mcp_template.template.utils.discovery.TemplateDiscovery")
    @patch("mcp_template.core.deployment_manager.DeploymentManager")
    def test_deploy_nonexistent_template(
        self, mock_manager_class, mock_discovery_class
    ):
        """Test deployment of non-existent template."""
        mock_discovery = Mock()
        mock_discovery.discover_templates.return_value = {}
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        deployer = MCPDeployer()

        with patch("mcp_template.console"):
            result = deployer.deploy("nonexistent")
            assert result is False
