"""
CLI tests for MCP Template system.

Tests the command-line interface functionality including argument parsing,
command dispatch, and error handling.
"""

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
            # Should exit without error (help is shown)
            assert exc_info.value.code is None or exc_info.value.code == 0

    @patch("mcp_template.CLI")
    def test_list_command(self, mock_cli_class):
        """Test list command."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        # Test default list
        sys.argv = ["mcp_template", "list"]
        main()
        mock_cli.handle_list_command.assert_called_once()

        # Test list with --deployed
        mock_cli.reset_mock()
        sys.argv = ["mcp_template", "list", "--deployed"]
        main()
        mock_cli.handle_list_command.assert_called_once()

    @patch("mcp_template.CLI")
    def test_deploy_command(self, mock_cli_class):
        """Test deploy command."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        sys.argv = ["mcpt", "deploy", "demo"]

        main()
        mock_cli.handle_deploy_command.assert_called_once()

    @patch("mcp_template.CLI")
    def test_stop_command(self, mock_cli_class):
        """Test stop command with various options."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        # Stop by template
        sys.argv = ["mcp_template", "stop", "demo"]
        main()
        mock_cli.handle_stop_command.assert_called_once()
        mock_cli.reset_mock()

        # Stop all deployments of a template
        sys.argv = ["mcp_template", "stop", "demo", "--all"]
        main()
        mock_cli.handle_stop_command.assert_called_once()
        mock_cli.reset_mock()

        # Stop by custom name
        sys.argv = ["mcp_template", "stop", "--name", "mcp-demo-123"]
        main()
        mock_cli.handle_stop_command.assert_called_once()
        mock_cli.reset_mock()

        # Stop all deployments (global)
        sys.argv = ["mcp_template", "stop", "--all"]
        main()
        mock_cli.handle_stop_command.assert_called_once()

    @patch("mcp_template.CLI")
    def test_logs_command(self, mock_cli_class):
        """Test logs command."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        sys.argv = ["mcp_template", "logs", "demo"]

        main()
        mock_cli.handle_logs_command.assert_called_once()

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

    @patch("mcp_template.CLI")
    def test_cleanup_command(self, mock_cli_class):
        """Test cleanup command."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        sys.argv = ["mcp_template", "cleanup"]

        main()
        mock_cli.handle_cleanup_command.assert_called_once()

    @patch("mcp_template.TemplateCreator")
    def test_create_command(self, mock_creator_class):
        """Test create command."""
        mock_creator = Mock()
        mock_creator.create_template_interactive.return_value = True
        mock_creator_class.return_value = mock_creator

        sys.argv = ["mcp_template", "create", "test-template"]

        main()
        mock_creator.create_template_interactive.assert_called_once()


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

    @patch("mcp_template.cli.EnhancedCLI")
    def test_config_command(self, mock_enhanced_cli_class):
        """Test config command."""
        mock_enhanced_cli = Mock()
        mock_enhanced_cli_class.return_value = mock_enhanced_cli

        sys.argv = ["mcp_template", "config", "demo"]

        main()
        mock_enhanced_cli.show_config_options.assert_called_once_with("demo")

    @patch("mcp_template.CLI")
    def test_logs_command_with_lines_parameter(self, mock_cli_class):
        """Test logs command with --lines parameter."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        sys.argv = ["mcp_template", "logs", "demo", "--lines", "50"]

        main()
        mock_cli.handle_logs_command.assert_called_once()

    @patch("mcp_template.CLI")
    def test_deploy_command_with_reserved_env_vars(self, mock_cli_class):
        """Test deploy command with RESERVED_ENV_VARS (transport and port)."""
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli

        sys.argv = [
            "mcp_template",
            "deploy",
            "demo",
            "--transport",
            "http",
            "--port",
            "8080",
        ]

        main()
        mock_cli.handle_deploy_command.assert_called_once()

    @patch("mcp_template.cli.EnhancedCLI")
    def test_examples_command(self, mock_enhanced_cli_class):
        """Test examples command."""
        mock_enhanced_cli = Mock()
        mock_enhanced_cli.template_manager = Mock()
        mock_enhanced_cli.console = Mock()
        mock_enhanced_cli.template_manager.get_template_info.return_value = {
            "name": "demo"
        }
        mock_enhanced_cli_class.return_value = mock_enhanced_cli

        sys.argv = ["mcp_template", "examples", "demo"]

        main()
        mock_enhanced_cli.template_manager.get_template_info.assert_called_once_with(
            "demo"
        )
