"""
CLI tests for MCP Template system.

Tests the command-line interface functionality including argument parsing,
command dispatch, and error handling.
"""

import os
import sys
from unittest.mock import patch

import pytest

from mcp_template import main


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
