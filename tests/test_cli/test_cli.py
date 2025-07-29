"""
CLI tests for MCP Template system.

Tests the command-line interface functionality including argument parsing,
command dispatch, and error handling.
"""

import sys
from unittest.mock import Mock, patch

import pytest

from mcp_template import MCPDeployer, main


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

    @patch("mcp_template.MCPDeployer")
    def test_list_command(self, mock_deployer_class):
        """Test list command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo", "file-server"]
        mock_deployer_class.return_value = mock_deployer

        sys.argv = ["mcp_template", "list"]

        main()
        mock_deployer.list_templates.assert_called_once()

    @patch("mcp_template.EnhancedCLI")
    @patch("mcp_template.MCPDeployer")
    def test_deploy_command(self, mock_deployer_class, mock_enhanced_cli_class):
        """Test deploy command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        mock_enhanced_cli = Mock()
        mock_enhanced_cli.deploy_with_transport.return_value = True
        mock_enhanced_cli_class.return_value = mock_enhanced_cli

        sys.argv = ["mcp_template", "deploy", "demo"]

        main()
        mock_enhanced_cli.deploy_with_transport.assert_called_once()

    @patch("mcp_template.MCPDeployer")
    def test_stop_command(self, mock_deployer_class):
        """Test stop command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        sys.argv = ["mcp_template", "stop", "demo"]

        main()
        mock_deployer.stop.assert_called_once_with("demo", custom_name=None)

    @patch("mcp_template.MCPDeployer")
    def test_logs_command(self, mock_deployer_class):
        """Test logs command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        sys.argv = ["mcp_template", "logs", "demo"]

        main()
        mock_deployer.logs.assert_called_once_with("demo", custom_name=None)

    @patch("mcp_template.MCPDeployer")
    def test_shell_command(self, mock_deployer_class):
        """Test shell command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        sys.argv = ["mcp_template", "shell", "demo"]

        main()
        mock_deployer.shell.assert_called_once_with("demo", custom_name=None)

    @patch("mcp_template.MCPDeployer")
    def test_cleanup_command(self, mock_deployer_class):
        """Test cleanup command."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        sys.argv = ["mcp_template", "cleanup"]

        main()
        mock_deployer.cleanup.assert_called_once()

    @patch("mcp_template.TemplateCreator")
    def test_create_command(self, mock_creator_class):
        """Test create command."""
        mock_creator = Mock()
        mock_creator.create_template_interactive.return_value = True
        mock_creator_class.return_value = mock_creator

        sys.argv = ["mcp_template", "create", "test-template"]

        main()
        mock_creator.create_template_interactive.assert_called_once()

    @patch("mcp_template.EnhancedCLI")
    @patch("mcp_template.MCPDeployer")
    def test_error_handling(self, mock_deployer_class, mock_enhanced_cli_class):
        """Test error handling in main CLI."""
        mock_deployer = Mock()
        mock_deployer.templates.keys.return_value = ["demo"]
        mock_deployer_class.return_value = mock_deployer

        mock_enhanced_cli = Mock()
        mock_enhanced_cli.deploy_with_transport.return_value = False  # Simulate failure
        mock_enhanced_cli_class.return_value = mock_enhanced_cli

        sys.argv = ["mcp_template", "deploy", "demo"]

        with pytest.raises(SystemExit):
            main()


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
            "demo": {"name": "Demo Template", "image": "demo:latest"}
        }
        mock_discovery_class.return_value = mock_discovery

        mock_manager = Mock()
        mock_manager.deploy_template.return_value = {
            "deployment_name": "demo-123",
            "status": "deployed",
        }
        mock_manager_class.return_value = mock_manager

        deployer = MCPDeployer()

        with patch("mcp_template.console"):
            deployer.deploy("demo")

        mock_manager.deploy_template.assert_called_once()

    @patch("mcp_template.template.discovery.TemplateDiscovery")
    @patch("mcp_template.manager.DeploymentManager")
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
