"""
Integration tests for the interactive CLI module.

These tests focus on realistic user workflows and interactions,
using real or controlled environments where possible.
"""

import json
from unittest.mock import Mock, patch

import pytest

from mcp_template.cli.interactive_cli import InteractiveSession


@pytest.mark.integration
class TestInteractiveSession:
    """Integration tests for InteractiveSession."""

    def test_session_persistence(self):
        """Test that session state persists across operations."""
        with patch(
            "mcp_template.cli.interactive_cli.CacheManager"
        ) as mock_cache_manager:
            mock_cache = Mock()
            mock_cache_manager.return_value = mock_cache
            mock_cache.get.return_value = {}

            session = InteractiveSession()

            # Select template and configure it
            session.select_template("demo")
            session.update_template_config(
                "demo", {"api_key": "test123", "endpoint": "https://api.example.com"}
            )

            # Verify state is maintained
            assert session.selected_template == "demo"
            config = session.get_template_config("demo")
            assert config["api_key"] == "test123"
            assert config["endpoint"] == "https://api.example.com"

    def test_multiple_templates_config(self):
        """Test managing configuration for multiple templates."""
        with patch(
            "mcp_template.cli.interactive_cli.CacheManager"
        ) as mock_cache_manager:
            mock_cache = Mock()
            mock_cache_manager.return_value = mock_cache
            mock_cache.get.return_value = {}

            session = InteractiveSession()

            # Configure multiple templates
            session.update_template_config("demo", {"api_key": "demo_key"})
            session.update_template_config(
                "github",
                {"github_token": "github_key", "github_host": "https://api.github.com"},
            )

            # Verify isolation between templates
            demo_config = session.get_template_config("demo")
            github_config = session.get_template_config("github")

            assert demo_config["api_key"] == "demo_key"
            assert github_config["github_token"] == "github_key"
            assert "github_token" not in demo_config
            assert "api_key" not in github_config

            # Verify all configs
            assert demo_config == {"api_key": "demo_key"}
            assert github_config == {
                "github_token": "github_key",
                "github_host": "https://api.github.com",
            }

    def test_template_switching_workflow(self):
        """Test switching between templates."""
        with patch(
            "mcp_template.cli.interactive_cli.CacheManager"
        ) as mock_cache_manager:
            mock_cache = Mock()
            mock_cache_manager.return_value = mock_cache
            mock_cache.get.return_value = {}

            session = InteractiveSession()

            # Start with demo template
            session.select_template("demo")
            assert session.get_prompt() == "mcpt(demo)> "

            # Switch to github template
            session.select_template("github")
            assert session.get_prompt() == "mcpt(github)> "

            # Unselect template
            session.unselect_template()
            assert session.get_prompt() == "mcpt> "


@pytest.mark.integration
class TestCommandWorkflows:
    """Integration tests for complete command workflows."""

    @patch("mcp_template.cli.interactive_cli.MCPClient")
    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_template_selection_and_tools_workflow(
        self, mock_get_session, mock_mcp_client
    ):
        """Test selecting a template and listing its tools."""
        from mcp_template.cli.interactive_cli import list_tools, select_template

        # Setup mocks
        mock_session = Mock()
        mock_session.get_selected_template.return_value = None
        mock_get_session.return_value = mock_session

        with patch("mcp_template.cli.list_tools") as mock_cli_list_tools:
            # Select template
            select_template("demo")
            mock_session.select_template.assert_called_once_with("demo")

            # List tools for selected template
            mock_session.get_selected_template.return_value = (
                "demo"  # Simulate selection
            )
            list_tools(template=None)

            # Verify the main CLI function was called with selected template
            mock_cli_list_tools.assert_called_once_with(
                template="demo",
                backend="docker",
                force_refresh=False,
                static=True,
                dynamic=True,
                output_format="table",
            )

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_configuration_workflow(self, mock_get_session):
        """Test complete configuration workflow."""
        from mcp_template.cli.interactive_cli import (
            clear_config,
            configure_template,
            show_config,
        )

        # Setup mocks
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client = mock_client
        mock_client.list_templates.return_value = {"demo": {"version": "1.0.0"}}
        mock_session.get_selected_template.return_value = "demo"
        mock_get_session.return_value = mock_session

        with (
            patch("mcp_template.cli.interactive_cli.console"),
            patch("mcp_template.cli.interactive_cli.show_config") as mock_show_config,
        ):
            # Configure template
            configure_template(
                template=None,
                config_pairs=["api_key=test123", "endpoint=https://api.example.com"],
            )

            # Verify configuration was set with correct method
            mock_session.update_template_config.assert_called_once_with(
                "demo", {"api_key": "test123", "endpoint": "https://api.example.com"}
            )
            mock_show_config.assert_called_once_with("demo")

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_tool_call_workflow(self, mock_get_session):
        """Test calling a tool with configuration."""
        from mcp_template.cli.interactive_cli import call_tool

        # Setup mocks
        mock_session = Mock()
        mock_session.get_selected_template.return_value = "demo"
        mock_session.get_template_config.return_value = {"api_key": "test123"}

        # Mock the client methods
        mock_client = Mock()
        mock_session.client = mock_client
        mock_client.list_templates.return_value = {"demo": {"version": "1.0.0"}}
        mock_client.get_template_info.return_value = None
        mock_client.call_tool_with_config.return_value = {
            "success": True,
            "result": "Hello World",
        }

        # Mock the formatter
        mock_formatter = Mock()
        mock_session.formatter = mock_formatter

        mock_get_session.return_value = mock_session

        call_tool(
            template=None,
            tool_name="say_hello",
            args='{"name": "World"}',
            config_file=None,
            env=[],
            config=[],
            backend=None,
            no_pull=False,
            raw=False,
            force_stdio=False,
        )

        # Verify the client method was called
        mock_client.call_tool_with_config.assert_called_once()

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_server_management_workflow(self, mock_get_session):
        """Test server deployment and management workflow."""
        from mcp_template.cli.interactive_cli import deploy_template

        # Setup mocks
        mock_session = Mock()
        mock_session.get_selected_template.return_value = "demo"
        mock_session.get_template_config.return_value = {"api_key": "test123"}
        mock_get_session.return_value = mock_session

        with patch("mcp_template.cli.deploy") as mock_cli_deploy:
            # Deploy server
            deploy_template(
                template="demo",
                config_file=None,
                env=[],
                config=[],
                transport="http",
                port=None,
                no_pull=False,
            )

            # Verify the main CLI deploy function was called
            mock_cli_deploy.assert_called_once()


@pytest.mark.integration
class TestErrorRecovery:
    """Integration tests for error recovery scenarios."""

    @patch("mcp_template.cli.list")
    def test_api_error_recovery(self, mock_cli_list):
        """Test recovery from API errors."""
        from mcp_template.cli.interactive_cli import list_templates

        # Setup mock to raise exception
        mock_cli_list.side_effect = Exception("Network error")

        with patch("mcp_template.cli.interactive_cli.console") as mock_console:
            # Should not raise exception, but handle error gracefully
            list_templates()

            # Should print error message
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if "Error" in str(call) or "❌" in str(call)
            ]
            assert len(error_calls) > 0

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_missing_template_error_recovery(self, mock_get_session):
        """Test recovery from missing template errors."""
        from mcp_template.cli.interactive_cli import list_tools

        mock_session = Mock()
        mock_session.get_selected_template.return_value = None
        mock_get_session.return_value = mock_session

        with patch("mcp_template.cli.interactive_cli.console") as mock_console:
            # Should handle missing template gracefully
            list_tools(template=None)

            # Should print error message about missing template
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if "❌" in str(call)
                and ("template" in str(call) or "Template" in str(call))
            ]
            assert len(error_calls) > 0

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_invalid_config_format_recovery(self, mock_get_session):
        """Test recovery from invalid configuration format."""
        from mcp_template.cli.interactive_cli import configure_template

        mock_session = Mock()
        mock_client = Mock()
        mock_session.client = mock_client
        mock_client.list_templates.return_value = {"demo": {"version": "1.0.0"}}
        mock_session.get_selected_template.return_value = "demo"
        mock_get_session.return_value = mock_session

        with patch("mcp_template.cli.interactive_cli.console") as mock_console:
            # Should handle invalid format gracefully
            configure_template(template=None, config_pairs=["invalid_format_no_equals"])

            # Should print error message about no valid config pairs
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if "❌" in str(call)
                and ("configuration" in str(call) or "config" in str(call))
            ]
            assert len(error_calls) > 0


@pytest.mark.integration
class TestComplexWorkflows:
    """Integration tests for complex, multi-step workflows."""

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_complete_user_session(self, mock_get_session):
        """Test a complete user session from start to finish."""
        from mcp_template.cli.interactive_cli import (
            call_tool,
            configure_template,
            deploy_template,
            list_tools,
            select_template,
            unselect_template,
        )

        # Setup session
        mock_session = Mock()
        mock_client = Mock()
        mock_session.client = mock_client
        mock_client.list_templates.return_value = {"demo": {"version": "1.0.0"}}
        mock_client.get_template_info.return_value = None
        mock_client.call_tool_with_config.return_value = {
            "success": True,
            "result": "Hello World",
        }
        mock_session.get_selected_template.return_value = None
        mock_session.get_template_config.return_value = {}

        # Mock the formatter
        mock_formatter = Mock()
        mock_session.formatter = mock_formatter

        mock_get_session.return_value = mock_session

        with (
            patch("mcp_template.cli.list_tools") as mock_cli_list_tools,
            patch("mcp_template.cli.deploy") as mock_cli_deploy,
            patch("mcp_template.cli.interactive_cli.show_config"),
        ):

            # 1. Select template
            select_template("demo")
            mock_session.select_template.assert_called_with("demo")

            # 2. Configure template
            mock_session.get_selected_template.return_value = (
                "demo"  # Simulate selection
            )
            configure_template(template=None, config_pairs=["api_key=test123"])
            mock_session.update_template_config.assert_called_with(
                "demo", {"api_key": "test123"}
            )

            # 3. List tools
            list_tools(template=None)
            mock_cli_list_tools.assert_called()

            # 4. Call tool
            call_tool(
                template=None,
                tool_name="say_hello",
                args='{"name": "World"}',
                config_file=None,
                env=[],
                config=[],
                backend=None,
                no_pull=False,
                raw=False,
                force_stdio=False,
            )
            mock_client.call_tool_with_config.assert_called()

            # 5. Deploy template
            deploy_template(
                template="demo",
                config_file=None,
                env=[],
                config=[],
                transport="http",
                port=None,
                no_pull=False,
            )
            mock_cli_deploy.assert_called()

            # 6. Unselect template
            unselect_template()
            mock_session.unselect_template.assert_called()

    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_multi_template_workflow(self, mock_get_session):
        """Test working with multiple templates in one session."""
        from mcp_template.cli.interactive_cli import (
            configure_template,
            list_tools,
            select_template,
        )

        mock_session = Mock()
        mock_client = Mock()
        mock_session.client = mock_client
        mock_client.list_templates.return_value = {
            "demo": {"version": "1.0.0"},
            "github": {"version": "1.0.0"},
        }
        mock_get_session.return_value = mock_session

        with (
            patch("mcp_template.cli.list_tools") as mock_cli_list_tools,
            patch("mcp_template.cli.interactive_cli.show_config"),
        ):

            # Work with demo template
            mock_session.get_selected_template.return_value = "demo"
            select_template("demo")
            configure_template(template=None, config_pairs=["api_key=demo_key"])
            list_tools(template=None)

            # Switch to github template
            mock_session.get_selected_template.return_value = "github"
            select_template("github")
            configure_template(template=None, config_pairs=["github_token=github_key"])
            list_tools(template=None)

            # Verify both templates were configured
            assert mock_session.update_template_config.call_count == 2
            mock_session.update_template_config.assert_any_call(
                "demo", {"api_key": "demo_key"}
            )
            mock_session.update_template_config.assert_any_call(
                "github", {"github_token": "github_key"}
            )

            # Verify tools were listed for both templates
            assert mock_cli_list_tools.call_count == 2


@pytest.mark.integration
class TestPerformanceAndLimits:
    """Integration tests for performance and edge cases."""

    @patch("mcp_template.cli.interactive_cli.CacheManager")
    def test_large_configuration_handling(self, mock_cache_manager):
        """Test handling of large configuration sets."""
        mock_cache = Mock()
        mock_cache_manager.return_value = mock_cache
        mock_cache.get.return_value = {}

        session = InteractiveSession()

        # Set many configuration values
        config_dict = {}
        for i in range(100):
            config_dict[f"key_{i}"] = f"value_{i}"

        session.update_template_config("demo", config_dict)

        # Verify all configs are accessible
        all_config = session.get_template_config("demo")
        assert len(all_config) == 100

        for i in range(100):
            assert all_config[f"key_{i}"] == f"value_{i}"

    def test_deeply_nested_json_args(self):
        """Test handling of complex JSON arguments."""
        complex_json = {
            "user": {
                "name": "John Doe",
                "settings": {
                    "theme": "dark",
                    "notifications": {
                        "email": True,
                        "push": False,
                        "categories": ["updates", "alerts"],
                    },
                },
            },
            "data": [1, 2, 3, {"nested": True}],
        }

        json_str = json.dumps(complex_json)

        # Test that JSON can be parsed correctly
        parsed = json.loads(json_str)
        assert parsed == complex_json


@pytest.mark.integration
class TestCommandlineArgumentParsing:
    """Test complex command line argument parsing in main interactive loop."""

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_logs_command_backend_flag_parsing(
        self, mock_get_session, mock_console, mock_input
    ):
        """Test logs command with --backend flag parsing."""
        mock_session = Mock()
        mock_session.get_selected_template.return_value = "test-template"
        mock_get_session.return_value = mock_session

        mock_input.side_effect = ["logs target --backend docker", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_get_logs.assert_called_with(
                target="target", backend="docker", lines=100
            )

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_logs_command_lines_flag_parsing(self, mock_console, mock_input):
        """Test logs command with --lines flag parsing."""
        mock_input.side_effect = ["logs target --lines 50", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_get_logs.assert_called_with(target="target", backend=None, lines=50)

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_logs_command_lines_flag_invalid_number(self, mock_console, mock_input):
        """Test logs command with invalid --lines number."""
        mock_input.side_effect = ["logs target --lines invalid", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_console.print.assert_any_call(
                "[red]❌ --lines requires a valid number[/red]"
            )

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_logs_command_backend_flag_missing_value(self, mock_console, mock_input):
        """Test logs command with --backend flag missing value."""
        mock_input.side_effect = ["logs target --backend", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_console.print.assert_any_call(
                "[red]❌ --backend requires a backend name[/red]"
            )

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_logs_command_unknown_flag_warning(self, mock_console, mock_input):
        """Test logs command with unknown flag shows warning."""
        mock_input.side_effect = ["logs target --unknown-flag", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_console.print.assert_any_call(
                "[yellow]⚠️ Ignoring unknown flag: --unknown-flag[/yellow]"
            )

    @patch("mcp_template.cli.interactive_cli.input")
    @patch("mcp_template.cli.interactive_cli.console")
    @patch("mcp_template.cli.interactive_cli.get_session")
    def test_logs_command_no_target_no_selected_template(
        self, mock_get_session, mock_console, mock_input
    ):
        """Test logs command with no target and no selected template."""
        mock_session = Mock()
        mock_session.get_selected_template.return_value = None
        mock_get_session.return_value = mock_session

        mock_input.side_effect = ["logs", "exit"]

        with patch("mcp_template.cli.interactive_cli.get_logs") as mock_get_logs:
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()
            mock_console.print.assert_any_call(
                "[red]❌ Target required: deployment ID or template name[/red]"
            )


@pytest.mark.integration
class TestInteractiveLoopMainFlow:
    """Test main interactive loop functionality."""

    @patch("mcp_template.cli.interactive_cli.READLINE_AVAILABLE", True)
    @patch("mcp_template.cli.interactive_cli.setup_completion")
    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_run_interactive_shell_with_readline(
        self, mock_console, mock_get_session, mock_setup
    ):
        """Test interactive shell with readline available."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session
        mock_setup.return_value = "/tmp/history"

        # Mock input to return exit immediately
        with patch("builtins.input", side_effect=["exit"]):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        mock_setup.assert_called_once()
        mock_console.print.assert_any_call(
            "[dim]✨ Command history and tab completion enabled[/dim]"
        )

    @patch("mcp_template.cli.interactive_cli.READLINE_AVAILABLE", False)
    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_run_interactive_shell_no_readline(self, mock_console, mock_get_session):
        """Test interactive shell without readline."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session

        # Mock input to return exit immediately
        with patch("builtins.input", side_effect=["exit"]):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        mock_console.print.assert_any_call(
            "[dim]💡 Install readline for command history and tab completion[/dim]"
        )

    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_interactive_shell_keyboard_interrupt(self, mock_console, mock_get_session):
        """Test keyboard interrupt handling in interactive shell."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session

        # Mock input to raise KeyboardInterrupt then exit
        with patch("builtins.input", side_effect=[KeyboardInterrupt(), "exit"]):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        mock_console.print.assert_any_call(
            "\n[yellow]Use 'exit' or 'quit' to leave the interactive shell[/yellow]"
        )

    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_interactive_shell_eof_error(self, mock_console, mock_get_session):
        """Test EOF error handling in interactive shell."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session

        # Mock input to raise EOFError
        with patch("builtins.input", side_effect=EOFError()):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        mock_console.print.assert_any_call("\n[yellow]Goodbye![/yellow]")

    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_interactive_shell_unknown_command(self, mock_console, mock_get_session):
        """Test unknown command handling."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session

        with patch("builtins.input", side_effect=["unknown_command", "exit"]):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        mock_console.print.assert_any_call(
            "[red]❌ Unknown command: unknown_command[/red]"
        )

    @patch("mcp_template.cli.interactive_cli.get_session")
    @patch("mcp_template.cli.interactive_cli.console")
    def test_interactive_shell_empty_command(self, mock_console, mock_get_session):
        """Test empty command handling."""
        mock_session = Mock()
        mock_session.get_prompt.return_value = "mcpt> "
        mock_get_session.return_value = mock_session

        with patch("builtins.input", side_effect=["", "   ", "exit"]):
            from mcp_template.cli.interactive_cli import run_interactive_shell

            run_interactive_shell()

        # Should not print any error messages for empty commands
        assert not any(
            "❌" in str(call)
            for call in mock_console.print.call_args_list
            if "command" in str(call)
        )


@pytest.mark.integration
class TestMainFunctionIntegration:
    """Test main function behavior."""

    @patch("sys.argv", ["script", "--help"])
    @patch("mcp_template.cli.interactive_cli.console")
    def test_main_with_help_flag(self, mock_console):
        """Test main function with --help flag."""
        from mcp_template.cli import interactive_cli

        interactive_cli.main()
        mock_console.print.assert_any_call("Enhanced MCP Interactive CLI")

    @patch("sys.argv", ["script", "-h"])
    @patch("mcp_template.cli.interactive_cli.console")
    def test_main_with_h_flag(self, mock_console):
        """Test main function with -h flag."""
        from mcp_template.cli import interactive_cli

        interactive_cli.main()
        mock_console.print.assert_any_call("Enhanced MCP Interactive CLI")

    @patch("sys.argv", ["script"])
    @patch("mcp_template.cli.interactive_cli.run_interactive_shell")
    def test_main_without_args(self, mock_run_shell):
        """Test main function without arguments."""
        from mcp_template.cli import interactive_cli

        interactive_cli.main()
        mock_run_shell.assert_called_once()
