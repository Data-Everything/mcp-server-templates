"""
Tests for interactive CLI argument parsing fixes.

These tests verify that the interactive CLI correctly handles:
1. Quoted space-separated values in config arguments
2. JSON arguments with spaces
3. Complex command lines with both features
"""

import unittest
from unittest.mock import MagicMock, patch

import pytest

from mcp_template.interactive_cli import InteractiveCLI, call_parser


@pytest.mark.unit
class TestInteractiveCLIArgumentParsing(unittest.TestCase):
    """Test the interactive CLI argument parsing functionality."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI instance for testing."""
        with (
            patch("mcp_template.interactive_cli.EnhancedCLI"),
            patch("mcp_template.interactive_cli.MCPDeployer"),
            patch("mcp_template.interactive_cli.CacheManager"),
            patch("mcp_template.interactive_cli.HTTPToolCaller"),
            patch("mcp_template.interactive_cli.Confirm") as mock_confirm,
        ):

            # Setup the CLI with mocked components
            cli = InteractiveCLI()
            cli.enhanced_cli.templates = {
                "filesystem": {
                    "config_schema": {
                        "properties": {
                            "allowed_dirs": {
                                "env_mapping": "ALLOWED_DIRS",
                                "volume_mount": True,
                                "command_arg": True,
                            }
                        }
                    },
                    "transport": {"default": "stdio", "supported": ["stdio", "http"]},
                }
            }

            # Mock interactive prompts to avoid stdin issues
            mock_confirm.ask.return_value = False

            return cli

    def test_simple_command_parsing(self, mock_cli):
        """Test parsing of simple commands without quotes."""
        # Mock the internal parsing logic to just return the parsed args
        with (
            patch.object(
                mock_cli, "_validate_and_get_tool_parameters"
            ) as mock_validate,
            patch.object(mock_cli.enhanced_cli, "run_stdio_tool") as mock_run,
        ):

            mock_validate.return_value = "{}"
            mock_run.return_value = True

            # Test simple command
            mock_cli.do_call("filesystem list_directory")

            # Should use the simpler code path for commands without problematic quotes
            # The method should complete without errors

    def test_quoted_space_separated_config(self, mock_cli):
        """Test parsing of quoted space-separated config values."""
        with (
            patch.object(
                mock_cli, "_validate_and_get_tool_parameters"
            ) as mock_validate,
            patch.object(mock_cli.enhanced_cli, "run_stdio_tool") as mock_run,
            patch("mcp_template.interactive_cli.merge_config_sources") as mock_merge,
        ):

            mock_validate.return_value = "{}"
            mock_run.return_value = True
            mock_merge.return_value = {"ALLOWED_DIRS": "/path1 /path2"}

            # Test command with quoted space-separated paths
            command = '-C allowed_dirs="/path1 /path2" filesystem list_directory'
            mock_cli.do_call(command)

            # Verify that the config was parsed correctly and stdio tool was called
            mock_merge.assert_called_once()
            call_args = mock_merge.call_args[1]
            self.assertEqual(call_args["inline_config"], ["allowed_dirs=/path1 /path2"])
            mock_run.assert_called_once()

    def test_json_with_spaces_parsing(self, mock_cli):
        """Test parsing of JSON arguments with spaces."""
        with (
            patch.object(
                mock_cli, "_validate_and_get_tool_parameters"
            ) as mock_validate,
            patch.object(mock_cli.enhanced_cli, "run_stdio_tool") as mock_run,
        ):

            mock_validate.return_value = '{"path": "/tmp"}'
            mock_run.return_value = True

            # Test command with JSON containing spaces
            command = 'filesystem list_directory {"path": "/tmp"}'
            mock_cli.do_call(command)

            # Should parse correctly and call the tool
            mock_run.assert_called_once()

    def test_complex_command_with_quotes_and_json(self, mock_cli):
        """Test parsing of complex commands with both quoted configs and JSON."""
        with (
            patch.object(
                mock_cli, "_validate_and_get_tool_parameters"
            ) as mock_validate,
            patch.object(mock_cli.enhanced_cli, "run_stdio_tool") as mock_run,
            patch("mcp_template.interactive_cli.merge_config_sources") as mock_merge,
        ):

            mock_validate.return_value = '{"path": "/mnt/tmp"}'
            mock_run.return_value = True
            mock_merge.return_value = {"ALLOWED_DIRS": "/path1 /path2"}

            # Test the user's exact problematic command (simplified)
            command = '-C allowed_dirs="/path1 /path2" -NP filesystem list_directory {"path": "/mnt/tmp"}'
            mock_cli.do_call(command)

            # Verify parsing was successful
            mock_merge.assert_called_once()
            call_args = mock_merge.call_args[1]
            self.assertEqual(call_args["inline_config"], ["allowed_dirs=/path1 /path2"])
            mock_run.assert_called_once()

    def test_error_handling_for_malformed_quotes(self, mock_cli):
        """Test error handling for malformed quotes."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            # Test command with unmatched quotes
            command = '-C allowed_dirs="/path1 /path2 filesystem list_directory'
            mock_cli.do_call(command)

            # Should print an error message
            mock_console.print.assert_called()
            error_calls = [
                call
                for call in mock_console.print.call_args_list
                if "Error parsing command line" in str(call)
            ]
            assert len(error_calls) > 0

    def test_fallback_to_cmd2_for_simple_cases(self, mock_cli):
        """Test that simple cases without quotes use cmd2 parsing."""
        with (
            patch.object(mock_cli, "statement_parser") as mock_parser,
            patch.object(
                mock_cli, "_validate_and_get_tool_parameters"
            ) as mock_validate,
            patch.object(mock_cli.enhanced_cli, "run_stdio_tool") as mock_run,
        ):

            # Setup mocks
            mock_statement = MagicMock()
            mock_statement.arg_list = ["filesystem", "list_directory", "{}"]
            mock_parser.parse.return_value = mock_statement
            mock_validate.return_value = "{}"
            mock_run.return_value = True

            # Test simple command without quotes
            command = "filesystem list_directory {}"
            mock_cli.do_call(command)

            # Should use cmd2 parsing for this case
            mock_parser.parse.assert_called_once_with(command)


class TestCallParserDirectly:
    """Test the call_parser argparse configuration directly."""

    def test_basic_parsing(self):
        """Test basic argument parsing functionality."""
        args = call_parser.parse_args(["filesystem", "list_directory"])
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"
        assert args.json_args == "{}"
        assert args.config is None
        assert args.no_pull is False

    def test_config_argument_parsing(self):
        """Test parsing of config arguments."""
        args = call_parser.parse_args(
            ["-C", "key1=value1", "-C", "key2=value2", "filesystem", "list_directory"]
        )
        assert args.config == ["key1=value1", "key2=value2"]

    def test_no_pull_flag(self):
        """Test parsing of no-pull flag."""
        args = call_parser.parse_args(["-NP", "filesystem", "list_directory"])
        assert args.no_pull is True

    def test_json_args_parsing(self):
        """Test parsing of JSON arguments."""
        args = call_parser.parse_args(
            ["filesystem", "list_directory", '{"path": "/tmp"}']
        )
        assert args.json_args == '{"path": "/tmp"}'


class TestIntegrationWithRealCLI:
    """Integration tests with actual CLI components."""

    def test_shlex_handling_of_quotes(self):
        """Test that shlex correctly handles quoted arguments."""
        import shlex

        # Test the problematic case
        command = '-C allowed_dirs="/path1 /path2" filesystem list_directory'
        tokens = shlex.split(command)

        expected = ["-C", "allowed_dirs=/path1 /path2", "filesystem", "list_directory"]
        assert tokens == expected

    def test_json_reconstruction_logic(self):
        """Test the JSON reconstruction logic for split arguments."""
        import shlex

        # Test JSON that gets split by shlex
        command = 'filesystem list_directory {"path": "/tmp"}'
        tokens = shlex.split(command)

        # Should be split: ['filesystem', 'list_directory', '{path:', '/tmp}']
        assert len(tokens) > 3
        assert "{" in tokens[2]

        # Test the reconstruction logic
        json_start_idx = None
        for i, arg in enumerate(tokens):
            if "{" in arg:
                json_start_idx = i
                break

        if json_start_idx is not None and json_start_idx < len(tokens) - 1:
            json_parts = tokens[json_start_idx:]
            rejoined_json = " ".join(json_parts)

            # Should create valid JSON-like structure
            assert rejoined_json.count("{") == rejoined_json.count("}")
            fixed_tokens = tokens[:json_start_idx] + [rejoined_json]

            # Should now be parseable
            args = call_parser.parse_args(fixed_tokens)
            assert args.template_name == "filesystem"
            assert args.tool_name == "list_directory"
            assert "path" in args.json_args
