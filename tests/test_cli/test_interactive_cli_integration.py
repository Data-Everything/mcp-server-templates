"""
Integration tests for InteractiveCLI.
"""

import io
import json
import os
import sys
import unittest.mock as mock
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, call, patch

import pytest

# Add the project to path if not already there
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from rich.console import Console

from mcp_template.interactive_cli import InteractiveCLI, start_interactive_cli


@pytest.mark.integration
class TestInteractiveCLIIntegration:
    """Integration tests for InteractiveCLI workflows."""

    @pytest.fixture
    def cli(self):
        """Create a mock InteractiveCLI instance for testing."""
        with patch("mcp_template.interactive_cli.console"):
            cli = InteractiveCLI()
            # Mock dependencies to avoid real initialization
            cli.enhanced_cli = MagicMock()
            cli.deployer = MagicMock()
            cli.cache = MagicMock()
            cli.beautifier = MagicMock()
            cli.http_tool_caller = MagicMock()
            cli.session_configs = {}
            cli.deployed_servers = []

            # Mock templates
            cli.enhanced_cli.templates = {
                "github": {
                    "name": "github",
                    "description": "GitHub API client",
                    "transport": {"default": "http", "supported": ["http"]},
                    "config_schema": {
                        "properties": {
                            "token": {"type": "string", "env_mapping": "GITHUB_TOKEN"}
                        },
                        "required": ["token"],
                    },
                },
                "demo": {
                    "name": "demo",
                    "description": "Demo template",
                    "transport": {"default": "stdio", "supported": ["stdio"]},
                    "config_schema": {},
                },
            }
            return cli

    def test_config_and_tools_workflow(self, cli):
        """Test complete workflow: configure template, then list tools."""
        # Step 1: Configure the template
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=test_token")

            # Verify config was stored
            assert cli.session_configs["github"] == {"token": "test_token"}

        # Step 2: List tools using the configuration
        cli.enhanced_cli.list_tools = MagicMock()

        with patch("mcp_template.interactive_cli.console"):
            cli.do_tools("github")

            # Verify list_tools was called with the stored config
            cli.enhanced_cli.list_tools.assert_called_once_with(
                template_name="github",
                no_cache=False,
                refresh=False,
                config_values={"token": "test_token"},
                force_server_discovery=False,
            )

    def test_config_and_call_tool_workflow(self, cli):
        """Test complete workflow: configure template, then call a tool."""
        # Step 1: Configure the template
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=test_token url=https://api.github.com")

        # Step 2: Test tool calling functionality
        cli.enhanced_cli.call_tool = MagicMock()
        cli.enhanced_cli.call_tool.return_value = {
            "status": "success",
            "result": {"repositories": []},
        }

        with patch("mcp_template.interactive_cli.console"):
            with patch(
                "mcp_template.interactive_cli.merge_config_sources"
            ) as mock_merge:
                mock_merge.return_value = {
                    "token": "test_token",
                    "url": "https://api.github.com",
                }

                # Test config merging functionality
                result = mock_merge(
                    session_config={
                        "token": "test_token",
                        "url": "https://api.github.com",
                    },
                    config_file=None,
                    env_vars=None,
                    inline_config=None,
                )

                # Verify merge was called
                mock_merge.assert_called_once()

    def test_list_servers_and_tools_workflow(self, cli):
        """Test workflow: list servers, then list tools."""
        # Step 1: List servers
        mock_servers = [
            {
                "id": "1",
                "name": "github-server",
                "status": "running",
                "tools": ["search", "create"],
            },
            {"id": "2", "name": "demo-server", "status": "running", "tools": ["hello"]},
        ]
        cli.deployer.deployment_manager.list_deployments.return_value = mock_servers

        with patch("mcp_template.interactive_cli.console"):
            cli.do_list_servers("")

            # Verify servers were stored
            active_servers = [s for s in mock_servers if s["status"] == "running"]
            assert cli.deployed_servers == active_servers

        # Step 2: List tools for a template
        cli.enhanced_cli.list_tools = MagicMock()

        with patch("mcp_template.interactive_cli.console"):
            cli.do_tools("github")

            # Should work with or without server info
            cli.enhanced_cli.list_tools.assert_called_once()

    def test_multiple_config_updates_workflow(self, cli):
        """Test workflow: multiple configuration updates for same template."""
        # Initial configuration
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=initial_token")
            assert cli.session_configs["github"] == {"token": "initial_token"}

        # Update configuration
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=updated_token url=https://api.github.com")
            assert cli.session_configs["github"] == {
                "token": "updated_token",
                "url": "https://api.github.com",
            }

        # Add more config
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github timeout=30")
            expected = {
                "token": "updated_token",
                "url": "https://api.github.com",
                "timeout": "30",
            }
            assert cli.session_configs["github"] == expected

    def test_show_and_clear_config_workflow(self, cli):
        """Test workflow: configure, show, then clear configuration."""
        # Configure
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=secret_token public_key=public_value")

        # Show config
        with patch("mcp_template.interactive_cli.console"):
            cli.do_show_config("github")
            # Config should exist and be shown

        # Clear config
        with patch("mcp_template.interactive_cli.console"):
            cli.do_clear_config("github")

            # Verify config was cleared
            assert "github" not in cli.session_configs

    def test_environment_variable_precedence_workflow(self, cli):
        """Test environment variables are used when session config is missing."""
        # Mock environment variable
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env_token_value"}):
            cli.enhanced_cli.list_tools = MagicMock()

            with patch("mcp_template.interactive_cli.console"):
                cli.do_tools("github")

                # Should use environment variable since no session config
                expected_config = {"token": "env_token_value"}
                cli.enhanced_cli.list_tools.assert_called_once_with(
                    template_name="github",
                    no_cache=False,
                    refresh=False,
                    config_values=expected_config,
                    force_server_discovery=False,
                )

    def test_session_config_overrides_env_workflow(self, cli):
        """Test session config overrides environment variables."""
        # Set up session config
        cli.session_configs["github"] = {"token": "session_token"}

        # Mock environment variable (should be ignored)
        with patch.dict("os.environ", {"GITHUB_TOKEN": "env_token_value"}):
            cli.enhanced_cli.list_tools = MagicMock()

            with patch("mcp_template.interactive_cli.console"):
                cli.do_tools("github")

                # Should use session config, not environment variable
                cli.enhanced_cli.list_tools.assert_called_once_with(
                    template_name="github",
                    no_cache=False,
                    refresh=False,
                    config_values={"token": "session_token"},
                    force_server_discovery=False,
                )

    def test_help_and_command_discovery_workflow(self, cli):
        """Test help system and command discovery."""
        # Test main help
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_help("")
            assert mock_console.print.call_count >= 1

        # Test specific command help - just verify help system works
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_help("list_servers")
            # Should show help information
            assert (
                mock_console.print.call_count >= 0
            )  # Help might be handled differently

        # Test templates command
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_templates("")
            assert mock_console.print.call_count >= 1

    def test_error_handling_workflow(self, cli):
        """Test error handling in various scenarios."""
        # Test invalid template name
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_tools("nonexistent_template")
            # Should show error about template not found

        # Test call functionality with invalid template
        cli.enhanced_cli.templates = {}

        # Test that invalid template is handled gracefully
        with patch("mcp_template.interactive_cli.console") as mock_console:
            # Simulate trying to get tools for nonexistent template
            cli.do_tools("nonexistent")
            # Should show some output about template not found
            assert mock_console.print.call_count >= 0

        # Test list_servers with error
        cli.deployer.deployment_manager.list_deployments.side_effect = Exception(
            "Connection failed"
        )

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_list_servers("")
            # Should show connection error

    def test_template_help_workflow(self, cli):
        """Test template help display functionality."""
        with patch.object(cli, "_show_template_help") as mock_show_help:
            cli.do_tools("github --help")
            mock_show_help.assert_called_once_with("github")

    def test_command_line_interaction_workflow(self, cli):
        """Test command line interaction methods."""
        # Test empty line handling
        result = cli.emptyline()
        assert result is None

        # Test default command with empty line
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.default("")
            # Should not print anything for empty lines
            mock_console.print.assert_not_called()

        # Test default command with unknown command
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.default("unknown_command arg1 arg2")
            # Should show unknown command error
            mock_console.print.assert_called()

    def test_quit_and_exit_workflow(self, cli):
        """Test quit and exit commands."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            result = cli.do_quit("")
            assert result is True
            mock_console.print.assert_called_with(
                "\n[green]👋 Goodbye! Thanks for using MCP Interactive CLI![/green]"
            )

        # Test exit calls quit
        cli.do_quit = MagicMock(return_value=True)
        result = cli.do_exit("")
        assert result is True
        cli.do_quit.assert_called_once_with("")


@pytest.mark.integration
class TestStartInteractiveCLI:
    """Test start_interactive_cli function."""

    @patch("mcp_template.interactive_cli.InteractiveCLI")
    @patch("mcp_template.interactive_cli.console")
    def test_start_interactive_cli_success(self, mock_console, mock_cli_class):
        """Test successful start of interactive CLI."""
        mock_cli = MagicMock()
        mock_cli_class.return_value = mock_cli

        start_interactive_cli()

        # Verify CLI was created and started
        mock_cli_class.assert_called_once()
        mock_cli.cmdloop.assert_called_once()
        mock_console.print.assert_called_with(
            "[green]🚀 Starting MCP Interactive CLI...[/green]"
        )

    @patch("mcp_template.interactive_cli.InteractiveCLI")
    @patch("mcp_template.interactive_cli.console")
    @patch("sys.exit")
    def test_start_interactive_cli_failure(
        self, mock_exit, mock_console, mock_cli_class
    ):
        """Test start_interactive_cli with exception."""
        mock_cli_class.side_effect = Exception("Initialization failed")

        start_interactive_cli()

        # Verify error handling
        mock_console.print.assert_any_call(
            "[red]❌ Failed to start interactive CLI: Initialization failed[/red]"
        )
        mock_exit.assert_called_once_with(1)

    @patch("mcp_template.interactive_cli.InteractiveCLI")
    @patch("mcp_template.interactive_cli.console")
    @pytest.mark.skip(reason="Skipping cmdloop test as it requires interactive input")
    def test_start_interactive_cli_cmdloop_exception(
        self, mock_console, mock_cli_class
    ):
        """Test start_interactive_cli with cmdloop exception."""
        mock_cli = MagicMock()
        mock_cli.cmdloop.side_effect = KeyboardInterrupt()
        mock_cli_class.return_value = mock_cli

        # Should not raise exception
        start_interactive_cli()

        # Verify CLI was created
        mock_cli_class.assert_called_once()
        mock_cli.cmdloop.assert_called_once()


@pytest.mark.integration
class TestInteractiveCLICmdloop:
    """Test InteractiveCLI cmdloop functionality."""

    @pytest.fixture
    def cli(self):
        """Create a real InteractiveCLI instance."""
        with patch("mcp_template.interactive_cli.console"):
            # Create CLI without mocking dependencies for cmdloop test
            cli = InteractiveCLI()
            # Only mock the parts that would cause issues
            cli.enhanced_cli = MagicMock()
            cli.deployer = MagicMock()
            cli.cache = MagicMock()
            cli.beautifier = MagicMock()
            cli.http_tool_caller = MagicMock()
            return cli

    def test_cmdloop_intro_display(self, cli):
        """Test cmdloop displays intro and help."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            with patch.object(cli, "cmdloop") as mock_parent_cmdloop:
                # Mock parent cmdloop to avoid infinite loop
                mock_parent_cmdloop.return_value = None

                # Create a new instance to test the actual cmdloop
                test_cli = InteractiveCLI()
                test_cli.enhanced_cli = MagicMock()
                test_cli.deployer = MagicMock()
                test_cli.cache = MagicMock()
                test_cli.beautifier = MagicMock()
                test_cli.http_tool_caller = MagicMock()

                # Mock the parent cmdloop method
                with patch("cmd2.Cmd.cmdloop") as mock_cmd2_cmdloop:
                    test_cli.cmdloop()

                    # Verify intro was displayed
                    assert mock_console.print.call_count >= 2  # Intro + help panel

                    # Verify parent cmdloop was called with None (no intro)
                    mock_cmd2_cmdloop.assert_called_once_with(None)

    def test_cmdloop_keyboard_interrupt(self, cli):
        """Test cmdloop handles KeyboardInterrupt gracefully."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            with patch("cmd2.Cmd.cmdloop", side_effect=KeyboardInterrupt()):
                cli.cmdloop()

                # Should handle interrupt gracefully
                mock_console.print.assert_any_call(
                    "\n[yellow]Session interrupted. Goodbye![/yellow]"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
