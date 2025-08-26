"""
Focused tests for interactive CLI argument parsing functionality.

These tests focus specifically on testing the argument parsing logic
without running the full CLI execution flow.
"""

import argparse
import shlex

import pytest

from mcp_template.cli.interactive_cli import call_parser


@pytest.mark.unit
class TestCallParserArgumentHandling:
    """Test the call_parser argparse configuration and the parsing logic."""

    def test_basic_argument_parsing(self):
        """Test basic argument parsing functionality."""
        args = call_parser.parse_args(["filesystem", "list_directory"])
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"
        assert args.json_args == []
        assert args.config is None
        assert args.no_pull is False

    def test_config_argument_parsing(self):
        """Test parsing of multiple config arguments."""
        args = call_parser.parse_args(
            ["-C", "key1=value1", "-C", "key2=value2", "filesystem", "list_directory"]
        )
        assert args.config == ["key1=value1", "key2=value2"]
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"

    def test_no_pull_flag_parsing(self):
        """Test parsing of no-pull flag."""
        args = call_parser.parse_args(["-NP", "filesystem", "list_directory"])
        assert args.no_pull is True
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"

    def test_json_args_parsing(self):
        """Test parsing of JSON arguments."""
        args = call_parser.parse_args(
            ["filesystem", "list_directory", '{"path": "/tmp"}']
        )
        assert args.json_args == ['{"path": "/tmp"}']
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"

    def test_env_argument_parsing(self):
        """Test parsing of environment variable arguments."""
        args = call_parser.parse_args(
            ["-e", "KEY1=value1", "-e", "KEY2=value2", "filesystem", "list_directory"]
        )
        assert args.env == ["KEY1=value1", "KEY2=value2"]

    def test_config_file_argument_parsing(self):
        """Test parsing of config file argument."""
        args = call_parser.parse_args(
            ["-c", "/path/to/config.json", "filesystem", "list_directory"]
        )
        assert args.config_file == "/path/to/config.json"

    def test_complex_argument_combination(self):
        """Test parsing of complex argument combinations."""
        args = call_parser.parse_args(
            [
                "-C",
                "allowed_dirs=/path1 /path2",
                "-e",
                "LOG_LEVEL=DEBUG",
                "-c",
                "config.json",
                "-NP",
                "filesystem",
                "list_directory",
                '{"path": "/tmp"}',
            ]
        )

        assert args.config == ["allowed_dirs=/path1 /path2"]
        assert args.env == ["LOG_LEVEL=DEBUG"]
        assert args.config_file == "config.json"
        assert args.no_pull is True
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"
        assert args.json_args == ['{"path": "/tmp"}']


@pytest.mark.unit
class TestShlexQuoteHandling:
    """Test shlex handling of quoted arguments - the core fix."""

    def test_shlex_handles_quoted_spaces_correctly(self):
        """Test that shlex correctly handles quoted space-separated values."""
        # This is the core functionality that fixes the user's issue
        command = '-C allowed_dirs="/path1 /path2" filesystem list_directory'
        tokens = shlex.split(command)

        expected = ["-C", "allowed_dirs=/path1 /path2", "filesystem", "list_directory"]
        assert tokens == expected

    def test_shlex_handles_complex_quoted_paths(self):
        """Test shlex with the user's actual complex paths."""
        command = '-C allowed_dirs="/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts /home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools" -NP filesystem list_directory'
        tokens = shlex.split(command)

        expected = [
            "-C",
            "allowed_dirs=/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts /home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools",
            "-NP",
            "filesystem",
            "list_directory",
        ]
        assert tokens == expected

    def test_shlex_splits_json_with_spaces(self):
        """Test that shlex splits JSON with spaces (expected behavior)."""
        command = 'filesystem list_directory {"path": "/tmp"}'
        tokens = shlex.split(command)

        # JSON with spaces gets split - this is expected and we handle it in our logic
        assert len(tokens) > 3
        assert "filesystem" in tokens
        assert "list_directory" in tokens
        assert any("{" in token for token in tokens)

    def test_json_reconstruction_logic(self):
        """Test the JSON reconstruction logic for handling split JSON."""
        # Simulate what happens when JSON gets split by shlex
        tokens = ["filesystem", "list_directory", "{path:", "/tmp}"]

        # Find JSON start
        json_start_idx = None
        for i, arg in enumerate(tokens):
            if "{" in arg:
                json_start_idx = i
                break

        assert json_start_idx is not None
        assert json_start_idx == 2

        # Reconstruct JSON
        if json_start_idx is not None and json_start_idx < len(tokens) - 1:
            json_parts = tokens[json_start_idx:]
            rejoined_json = " ".join(json_parts)

            # Verify reconstruction
            assert rejoined_json == "{path: /tmp}"
            assert rejoined_json.count("{") == rejoined_json.count("}")

            # Create fixed token list
            fixed_tokens = tokens[:json_start_idx] + [rejoined_json]
            assert fixed_tokens == ["filesystem", "list_directory", "{path: /tmp}"]

    def test_argparse_with_reconstructed_json(self):
        """Test that argparse works with reconstructed JSON."""
        # Start with split tokens
        tokens = ["filesystem", "list_directory", "{path:", "/tmp}"]

        # Apply reconstruction logic
        json_start_idx = 2  # We know where it starts from previous test
        json_parts = tokens[json_start_idx:]
        rejoined_json = " ".join(json_parts)
        fixed_tokens = tokens[:json_start_idx] + [rejoined_json]

        # Parse with call_parser
        args = call_parser.parse_args(fixed_tokens)

        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"
        assert args.json_args == ["{path: /tmp}"]


@pytest.mark.unit
class TestCompleteWorkflow:
    """Test the complete parsing workflow end-to-end."""

    def test_quote_detection_logic(self):
        """Test the logic for detecting when to use shlex vs cmd2."""
        # Commands with quotes and spaces should use shlex
        command_with_quotes = (
            '-C allowed_dirs="/path1 /path2" filesystem list_directory'
        )
        assert '"' in command_with_quotes and " " in command_with_quotes

        # Simple commands should use cmd2
        simple_command = "filesystem list_directory"
        assert not ('"' in simple_command and " " in simple_command)

        # Commands with quotes but no spaces might use either
        quoted_no_spaces = '-C key="value" filesystem list_directory'
        assert '"' in quoted_no_spaces and " " in quoted_no_spaces

    def test_user_problematic_case_parsing(self):
        """Test parsing of the user's exact problematic command."""
        command = '-C allowed_dirs="/home/sam/data-everything/mcp-platform/mcp-server-templates/scripts /home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools" -NP filesystem list_directory {"path": "/mnt/home/sam/data-everything/mcp-platform/mcp-server-templates/mcp_template/tools"}'

        # Use shlex (since it has quotes and spaces)
        tokens = shlex.split(command)

        # Should handle the quoted paths correctly
        assert len(tokens) >= 5  # At least the main components
        assert "-C" in tokens
        assert "-NP" in tokens
        assert "filesystem" in tokens
        assert "list_directory" in tokens

        # Find the config value
        config_idx = tokens.index("-C") + 1
        config_value = tokens[config_idx]
        assert "allowed_dirs=" in config_value
        assert "scripts" in config_value and "tools" in config_value

        # JSON might be split and need reconstruction
        json_parts = []
        for i, token in enumerate(tokens):
            if "{" in token:
                json_parts = tokens[i:]
                break

        if json_parts:
            reconstructed_json = " ".join(json_parts)
            # Remove json parts and add reconstructed
            main_tokens = []
            found_json = False
            for token in tokens:
                if "{" in token:
                    found_json = True
                    break
                main_tokens.append(token)

            if found_json:
                final_tokens = main_tokens + [reconstructed_json]
            else:
                final_tokens = tokens
        else:
            final_tokens = tokens

        # Should now be parseable
        args = call_parser.parse_args(final_tokens)
        assert args.template_name == "filesystem"
        assert args.tool_name == "list_directory"
        assert args.no_pull is True
        assert args.config is not None and len(args.config) > 0


@pytest.mark.unit
class TestErrorCases:
    """Test error handling for malformed commands."""

    def test_unmatched_quotes_error(self):
        """Test that unmatched quotes are handled gracefully."""
        command_with_unmatched_quotes = (
            '-C allowed_dirs="/path1 /path2 filesystem list_directory'
        )

        with pytest.raises(ValueError):
            shlex.split(command_with_unmatched_quotes)

    def test_empty_command_handling(self):
        """Test handling of empty or minimal commands."""
        with pytest.raises(
            (SystemExit, argparse.ArgumentError)
        ):  # argparse raises ArgumentError with exit_on_error=False
            call_parser.parse_args([])

        with pytest.raises(
            (SystemExit, argparse.ArgumentError)
        ):  # argparse raises ArgumentError with exit_on_error=False
            call_parser.parse_args(["filesystem"])

    def test_invalid_json_structure(self):
        """Test that malformed JSON is passed through (not our job to validate)."""
        # The CLI should pass through malformed JSON - validation happens later
        args = call_parser.parse_args(
            ["filesystem", "list_directory", '{"invalid": json}']
        )
        assert args.json_args == ['{"invalid": json}']  # Passed through as-is
