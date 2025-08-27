"""
Unit tests for the main CLI module (mcp_template.cli.cli).

These tests focus on individual CLI commands and functions in isolation,
using mocks for external dependencies like MCPClient.
"""

import os
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

pytestmark = pytest.mark.unit

from mcp_template.cli.cli import (
    AliasGroup,
    app,
    cli_state,
    format_discovery_hint,
    setup_logging,
    split_command_args,
)


class TestCLIUtilities:
    """Test utility functions in the CLI module."""

    def test_format_discovery_hint(self):
        """Test discovery hint formatting."""
        hint = format_discovery_hint("cache")
        assert "cached" in hint.lower()
        assert "force-refresh" in hint.lower()

        hint = format_discovery_hint("static")
        assert "template files" in hint.lower()

        hint = format_discovery_hint("stdio")
        assert "stdio" in hint.lower()

        hint = format_discovery_hint("http")
        assert "http server" in hint.lower()

        hint = format_discovery_hint("error")
        assert "error" in hint.lower()

    def test_split_command_args(self):
        """Test command argument splitting."""
        # Test simple case
        result = split_command_args(["arg1", "arg2"])
        assert result == ["arg1", "arg2"]

        # Test with None
        result = split_command_args(None)
        assert result == []

        # Test empty list
        result = split_command_args([])
        assert result == []

    def test_setup_logging(self):
        """Test logging setup."""
        with patch("mcp_template.cli.cli.logging.basicConfig") as mock_config:
            setup_logging(verbose=False)
            mock_config.assert_called_once()

            # Reset mock
            mock_config.reset_mock()

            setup_logging(verbose=True)
            mock_config.assert_called_once()


class TestAliasGroup:
    """Test the AliasGroup class for command aliases."""

    def test_alias_group_initialization(self):
        """Test AliasGroup can be initialized."""
        group = AliasGroup()
        assert isinstance(group, typer.core.TyperGroup)

    def test_group_cmd_name(self):
        """Test command name grouping logic."""
        group = AliasGroup()

        # Test with default name when no commands exist
        result = group._group_cmd_name("test")
        assert result == "test"


class TestCLIState:
    """Test CLI global state management."""

    def test_cli_state_initialization(self):
        """Test that CLI state is properly initialized."""
        assert "backend_type" in cli_state
        assert "verbose" in cli_state
        assert "dry_run" in cli_state

    @patch.dict(os.environ, {"MCP_BACKEND": "mock"})
    def test_cli_state_backend_from_env(self):
        """Test CLI state reads backend from environment."""
        # Re-import to get updated state
        from importlib import reload

        from mcp_template.cli import cli

        reload(cli)
        assert cli.cli_state["backend_type"] == "mock"

    @patch.dict(os.environ, {"MCP_VERBOSE": "true"})
    def test_cli_state_verbose_from_env(self):
        """Test CLI state reads verbose from environment."""
        from importlib import reload

        from mcp_template.cli import cli

        reload(cli)
        assert cli.cli_state["verbose"] is True

    @patch.dict(os.environ, {"MCP_DRY_RUN": "true"})
    def test_cli_state_dry_run_from_env(self):
        """Test CLI state reads dry_run from environment."""
        from importlib import reload

        from mcp_template.cli import cli

        reload(cli)
        assert cli.cli_state["dry_run"] is True


class TestCLICommands:
    """Test CLI command functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_list_templates_command(self, mock_client_class):
        """Test list_templates command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_templates.return_value = {
            "demo": {"name": "Demo", "description": "Demo template"},
            "github": {"name": "GitHub", "description": "GitHub template"},
        }

        result = self.runner.invoke(app, ["list_templates"])

        assert result.exit_code == 0
        mock_client.list_templates.assert_called_once()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_list_deployments_command(self, mock_client_class):
        """Test list_deployments command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_servers.return_value = [
            {"id": "demo-1", "template": "demo", "status": "running"},
            {"id": "github-1", "template": "github", "status": "stopped"},
        ]

        result = self.runner.invoke(app, ["list_deployments"])

        assert result.exit_code == 0
        mock_client.list_servers.assert_called_once()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_command_success(self, mock_client_class):
        """Test deploy command with successful deployment."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock successful deployment
        mock_result = Mock()
        mock_result.success = True
        mock_result.deployment_id = "demo-123"
        mock_result.status = "running"
        mock_result.to_dict.return_value = {
            "deployment_id": "demo-123",
            "status": "running",
            "success": True,
        }
        mock_client.start_server.return_value = mock_result

        result = self.runner.invoke(app, ["deploy", "demo"])

        assert result.exit_code == 0
        mock_client.start_server.assert_called_once()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_command_failure(self, mock_client_class):
        """Test deploy command with failed deployment."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock failed deployment
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Deployment failed"
        mock_result.to_dict.return_value = {
            "success": False,
            "error": "Deployment failed",
        }
        mock_client.start_server.return_value = mock_result

        result = self.runner.invoke(app, ["deploy", "demo"])

        # Should exit with error code
        assert result.exit_code != 0
        mock_client.start_server.assert_called_once()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_stop_command(self, mock_client_class):
        """Test stop command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.stop_server.return_value = {"success": True}

        result = self.runner.invoke(app, ["stop", "demo-123"])

        assert result.exit_code == 0
        mock_client.stop_server.assert_called()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_logs_command(self, mock_client_class):
        """Test logs command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get_server_logs.return_value = [
            "2024-01-01 10:00:00 INFO: Server started",
            "2024-01-01 10:00:01 INFO: Ready to serve requests",
        ]

        result = self.runner.invoke(app, ["logs", "demo-123"])

        assert result.exit_code == 0
        mock_client.get_server_logs.assert_called()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_status_command(self, mock_client_class):
        """Test status command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock MultiBackendManager through client
        mock_multi_manager = Mock()
        mock_client.multi_manager = mock_multi_manager
        mock_multi_manager.get_backend_health.return_value = {
            "docker": {"status": "healthy", "containers": 5},
            "kubernetes": {"status": "unavailable"},
        }
        mock_multi_manager.get_all_deployments.return_value = []

        result = self.runner.invoke(app, ["status"])

        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_list_tools_command(self, mock_client_class):
        """Test list_tools command."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_tools.return_value = [
            {"name": "search", "description": "Search repositories"},
            {"name": "create_issue", "description": "Create an issue"},
        ]

        result = self.runner.invoke(app, ["list_tools", "github"])

        assert result.exit_code == 0
        mock_client.list_tools.assert_called_with("github")

    @patch("mcp_template.cli.cli.MCPClient")
    def test_list_command_servers(self, mock_client_class):
        """Test list command for servers."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_servers.return_value = [
            {"id": "demo-1", "template": "demo", "status": "running"}
        ]

        result = self.runner.invoke(app, ["list", "servers"])

        assert result.exit_code == 0
        mock_client.list_servers.assert_called()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_list_command_templates(self, mock_client_class):
        """Test list command for templates."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_templates.return_value = {
            "demo": {"name": "Demo", "description": "Demo template"}
        }

        result = self.runner.invoke(app, ["list", "templates"])

        assert result.exit_code == 0
        mock_client.list_templates.assert_called()

    @patch("mcp_template.cli.cli.run_interactive_shell")
    def test_interactive_command(self, mock_interactive):
        """Test interactive command."""
        result = self.runner.invoke(app, ["interactive"])

        assert result.exit_code == 0
        mock_interactive.assert_called_once()

    def test_main_callback(self):
        """Test main callback function."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "MCP Template CLI" in result.output

    def test_install_completion_command(self):
        """Test install completion command."""
        with patch("mcp_template.cli.cli.install_completion") as mock_install:
            result = self.runner.invoke(app, ["install-completion"])

            assert result.exit_code == 0
            mock_install.assert_called_once()


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_with_invalid_template(self, mock_client_class):
        """Test deploy command with invalid template."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.start_server.side_effect = Exception("Template not found")

        result = self.runner.invoke(app, ["deploy", "nonexistent"])

        # Should handle error gracefully
        assert result.exit_code != 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_client_initialization_error(self, mock_client_class):
        """Test handling of client initialization errors."""
        mock_client_class.side_effect = Exception("Failed to initialize client")

        result = self.runner.invoke(app, ["list_templates"])

        # Should handle error gracefully
        assert result.exit_code != 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_backend_unavailable_error(self, mock_client_class):
        """Test handling when backend is unavailable."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.list_servers.side_effect = Exception("Backend unavailable")

        result = self.runner.invoke(app, ["list_deployments"])

        # Should handle error gracefully
        assert result.exit_code != 0


class TestCLIDryRunMode:
    """Test CLI dry-run functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_dry_run(self, mock_client_class):
        """Test deploy command in dry-run mode."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        result = self.runner.invoke(app, ["deploy", "demo", "--dry-run"])

        # In dry-run mode, should not actually call start_server
        assert result.exit_code == 0
        # The actual dry-run behavior depends on implementation
        # This test verifies the command accepts the flag

    @patch("mcp_template.cli.cli.MCPClient")
    def test_stop_dry_run(self, mock_client_class):
        """Test stop command in dry-run mode."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        result = self.runner.invoke(app, ["stop", "demo-123", "--dry-run"])

        assert result.exit_code == 0


class TestCLIConfigurationOptions:
    """Test CLI configuration and option handling."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_with_backend_option(self, mock_client_class):
        """Test deploy command with backend specification."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_client.start_server.return_value = mock_result

        result = self.runner.invoke(app, ["deploy", "demo", "--backend", "mock"])

        assert result.exit_code == 0
        # Verify backend was passed to client
        mock_client_class.assert_called_with(backend_type="mock")

    @patch("mcp_template.cli.cli.MCPClient")
    def test_deploy_with_config_file(self, mock_client_class):
        """Test deploy command with configuration file."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {"success": True}
        mock_client.start_server.return_value = mock_result

        # Create a temporary config file
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"key": "value"}')
            config_file = f.name

        try:
            result = self.runner.invoke(
                app, ["deploy", "demo", "--config-file", config_file]
            )
            assert result.exit_code == 0
        finally:
            os.unlink(config_file)

    def test_verbose_flag(self):
        """Test verbose flag functionality."""
        result = self.runner.invoke(app, ["--verbose", "--help"])
        assert result.exit_code == 0

    def test_version_display(self):
        """Test version display functionality."""
        # This test depends on how version is implemented
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
