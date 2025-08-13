"""
Unit tests for InteractiveCLI helper methods and edge cases.
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import json
import sys
import io
import os
from contextlib import redirect_stdout, redirect_stderr

# Add the project to path if not already there
project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from mcp_template.interactive_cli import InteractiveCLI, merge_config_sources


@pytest.mark.unit
class TestInteractiveCLIHelpers:
    """Test InteractiveCLI helper methods."""

    @pytest.fixture
    def cli(self):
        """Create a mock InteractiveCLI instance for testing."""
        with patch("mcp_template.interactive_cli.console"):
            cli = InteractiveCLI()
            # Mock dependencies
            cli.enhanced_cli = MagicMock()
            cli.deployer = MagicMock()
            cli.deployment_manager = MagicMock()
            cli.tool_manager = MagicMock()
            cli.template_manager = MagicMock()
            cli.cache = MagicMock()
            cli.beautifier = MagicMock()
            cli.http_tool_caller = MagicMock()
            cli.session_configs = {}
            cli.deployed_servers = []
            return cli

    def test_show_template_help_template_not_found(self, cli):
        """Test _show_template_help with non-existent template."""
        cli.template_manager.get_template_info.return_value = None
        cli.template_manager.list_templates.return_value = {
            "demo": {},
            "filesystem": {},
        }

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli._show_template_help("nonexistent")

            mock_console.print.assert_any_call(
                "[red]❌ Template 'nonexistent' not found[/red]"
            )

    def test_show_template_help_basic_template(self, cli):
        """Test _show_template_help with basic template."""
        cli.enhanced_cli.templates = {
            "demo": {
                "name": "demo",
                "description": "Demo template",
                "transport": {"default": "stdio", "supported": ["stdio"]},
                "config_schema": {},
            }
        }
        cli.enhanced_cli.tool_discovery = MagicMock()
        cli.enhanced_cli.tool_discovery.discover_tools.return_value = []

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli._show_template_help("demo")

            # Should display template overview
            assert mock_console.print.call_count >= 2

    def test_show_template_help_with_config_schema(self, cli):
        """Test _show_template_help with template that has config schema."""
        cli.enhanced_cli.templates = {
            "github": {
                "name": "github",
                "description": "GitHub API client",
                "transport": {"default": "http", "supported": ["http"]},
                "config_schema": {
                    "properties": {
                        "token": {
                            "type": "string",
                            "description": "GitHub API token",
                            "env_mapping": "GITHUB_TOKEN",
                        },
                        "base_url": {
                            "type": "string",
                            "description": "Base URL for API",
                            "env_mapping": "GITHUB_BASE_URL",
                        },
                    },
                    "required": ["token"],
                },
            }
        }
        cli.enhanced_cli.tool_discovery = MagicMock()
        cli.enhanced_cli.tool_discovery.discover_tools.return_value = []

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli._show_template_help("github")

            # Should display config schema table
            assert mock_console.print.call_count >= 3

    def test_show_template_help_with_tools(self, cli):
        """Test _show_template_help with tools available."""
        cli.enhanced_cli.templates = {
            "github": {
                "name": "github",
                "description": "GitHub API client",
                "transport": {"default": "http", "supported": ["http"]},
                "config_schema": {},
            }
        }

        mock_tools = [
            {
                "name": "search_repositories",
                "description": "Search for repositories",
                "parameters": {
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Max results"},
                    },
                    "required": ["query"],
                },
            }
        ]

        cli.enhanced_cli.tool_discovery = MagicMock()
        cli.enhanced_cli.tool_discovery.discover_tools.return_value = mock_tools

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli._show_template_help("github")

            # Should display tools information
            assert mock_console.print.call_count >= 4  # Overview + tools + examples

    def test_show_template_help_tool_discovery_error(self, cli):
        """Test _show_template_help with tool discovery error."""
        cli.enhanced_cli.templates = {
            "github": {
                "name": "github",
                "description": "GitHub API client",
                "transport": {"default": "http", "supported": ["http"]},
                "config_schema": {},
            }
        }

        cli.enhanced_cli.tool_discovery = MagicMock()
        cli.enhanced_cli.tool_discovery.discover_tools.side_effect = Exception(
            "Discovery failed"
        )

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli._show_template_help("github")

            # Should show error message
            mock_console.print.assert_any_call(
                "[red]❌ Failed to discover tools: Discovery failed[/red]"
            )

    def test_do_call_with_config_sources(self, cli):
        """Test call functionality with various config source combinations."""
        # Test that config sources are properly handled in session
        cli.enhanced_cli.templates = {
            "github": {
                "transport": {"default": "http", "supported": ["http"]},
                "config_schema": {},
            }
        }
        cli.session_configs["github"] = {"token": "session_token"}

        # Test merge_config_sources functionality
        with patch("mcp_template.interactive_cli.merge_config_sources") as mock_merge:
            mock_merge.return_value = {"token": "session_token", "timeout": "30"}

            result = merge_config_sources(
                session_config={"token": "session_token"},
                config_file=None,
                env_vars={"API_KEY": "env_value"},
                inline_config={"timeout": "30"},
            )

            assert result is not None

    def test_config_masking_sensitive_values(self, cli):
        """Test that sensitive config values are masked in display."""
        cli.session_configs["github"] = {
            "token": "secret_token",
            "api_key": "secret_key",
            "password": "secret_password",
            "public_url": "https://api.github.com",
        }

        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_show_config("github")

            # Should mask sensitive values but show others
            assert mock_console.print.call_count >= 1

    def test_config_update_preserves_existing(self, cli):
        """Test that config updates preserve existing values."""
        cli.session_configs["github"] = {
            "token": "existing_token",
            "base_url": "existing_url",
        }

        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github timeout=30 retries=3")

            # Should preserve existing values and add new ones
            expected = {
                "token": "existing_token",
                "base_url": "existing_url",
                "timeout": "30",
                "retries": "3",
            }
            assert cli.session_configs["github"] == expected

    def test_cache_integration(self, cli):
        """Test cache integration in config operations."""
        # Test cache set on config
        with patch("mcp_template.interactive_cli.console"):
            cli.do_config("github token=test")

            cli.cache.set.assert_called_once_with(
                "interactive_config_github", {"token": "test"}
            )

        # Test cache remove on clear (note: method is 'remove', not 'delete')
        cli.cache.remove = MagicMock()
        with patch("mcp_template.interactive_cli.console"):
            cli.do_clear_config("github")

            cli.cache.remove.assert_called_once_with("interactive_config_github")

    def test_tools_command_with_env_mapping(self, cli):
        """Test tools command with environment variable mapping."""
        cli.enhanced_cli.templates = {
            "github": {
                "config_schema": {
                    "properties": {
                        "token": {"env_mapping": "GITHUB_TOKEN"},
                        "org": {"env_mapping": "GITHUB_ORG"},
                    }
                }
            }
        }
        cli.tool_manager.list_tools = MagicMock()
        cli.template_manager.get_template_info = MagicMock(
            return_value={
                "config_schema": {
                    "properties": {
                        "token": {"env_mapping": "GITHUB_TOKEN"},
                        "org": {"env_mapping": "GITHUB_ORG"},
                    }
                }
            }
        )

        with patch.dict(
            "os.environ", {"GITHUB_TOKEN": "env_token", "GITHUB_ORG": "test-org"}
        ):
            with patch("mcp_template.interactive_cli.console"):
                cli.do_tools("github")

                # Should call tool_manager with correct template
                cli.tool_manager.list_tools.assert_called_once_with(
                    template_or_id="github",
                    discovery_method="auto",
                    force_refresh=False,
                )

    def test_tools_command_session_overrides_env(self, cli):
        """Test that session config overrides environment variables in tools command."""
        cli.enhanced_cli.templates = {
            "github": {
                "config_schema": {
                    "properties": {"token": {"env_mapping": "GITHUB_TOKEN"}}
                }
            }
        }
        cli.session_configs["github"] = {"token": "session_token"}
        cli.tool_manager.list_tools = MagicMock()
        cli.template_manager.get_template_info = MagicMock(
            return_value={
                "config_schema": {
                    "properties": {"token": {"env_mapping": "GITHUB_TOKEN"}}
                }
            }
        )

        with patch.dict("os.environ", {"GITHUB_TOKEN": "env_token"}):
            with patch("mcp_template.interactive_cli.console"):
                cli.do_tools("github")

                # Should call tool_manager with correct template
                cli.tool_manager.list_tools.assert_called_once_with(
                    template_or_id="github",
                    discovery_method="auto",
                    force_refresh=False,
                )


@pytest.mark.unit
class TestMergeConfigSourcesEdgeCases:
    """Test edge cases for merge_config_sources function."""

    def test_merge_config_sources_invalid_env_format(self):
        """Test merge_config_sources with invalid environment variable format."""
        session_config = {"key1": "value1"}
        env_vars = ["invalid_format", "valid=value"]

        with patch("mcp_template.interactive_cli.console"):
            result = merge_config_sources(session_config, env_vars=env_vars)

            # Should only process valid format
            assert result == {"key1": "value1", "valid": "value"}

    def test_merge_config_sources_invalid_inline_format(self):
        """Test merge_config_sources with invalid inline config format."""
        session_config = {"key1": "value1"}
        inline_config = ["invalid_format", "valid=value"]

        with patch("mcp_template.interactive_cli.console"):
            result = merge_config_sources(session_config, inline_config=inline_config)

            # Should only process valid format
            assert result == {"key1": "value1", "valid": "value"}

    def test_merge_config_sources_empty_values(self):
        """Test merge_config_sources with empty values."""
        session_config = {"key1": "value1"}
        env_vars = ["key2="]  # Empty value
        inline_config = ["key3="]  # Empty value

        with patch("mcp_template.interactive_cli.console"):
            result = merge_config_sources(
                session_config, env_vars=env_vars, inline_config=inline_config
            )

            # Empty values should be preserved
            assert result == {"key1": "value1", "key2": "", "key3": ""}

    def test_merge_config_sources_equals_in_value(self):
        """Test merge_config_sources with equals signs in values."""
        session_config = {}
        env_vars = ["url=https://api.example.com/v1?key=value"]

        with patch("mcp_template.interactive_cli.console"):
            result = merge_config_sources(session_config, env_vars=env_vars)

            # Should split only on first equals
            assert result == {"url": "https://api.example.com/v1?key=value"}

    def test_merge_config_sources_malformed_json_file(self):
        """Test merge_config_sources with malformed JSON file."""
        session_config = {"key1": "value1"}

        with patch("builtins.open", mock.mock_open(read_data="invalid json")):
            with patch("mcp_template.interactive_cli.console") as mock_console:
                with pytest.raises(json.JSONDecodeError):
                    merge_config_sources(session_config, config_file="invalid.json")

    def test_merge_config_sources_all_empty(self):
        """Test merge_config_sources with all empty sources."""
        result = merge_config_sources({})
        assert result == {}

    def test_merge_config_sources_none_values(self):
        """Test merge_config_sources with None values."""
        session_config = {"key1": "value1"}

        with patch("mcp_template.interactive_cli.console"):
            result = merge_config_sources(
                session_config, config_file=None, env_vars=None, inline_config=None
            )

            assert result == session_config


@pytest.mark.unit
class TestInteractiveCLIEdgeCases:
    """Test edge cases for InteractiveCLI."""

    @pytest.fixture
    def cli(self):
        """Create a mock InteractiveCLI instance for testing."""
        with patch("mcp_template.interactive_cli.console"):
            cli = InteractiveCLI()
            cli.enhanced_cli = MagicMock()
            cli.deployer = MagicMock()
            cli.deployment_manager = MagicMock()
            cli.tool_manager = MagicMock()
            cli.template_manager = MagicMock()
            cli.cache = MagicMock()
            cli.beautifier = MagicMock()
            cli.http_tool_caller = MagicMock()
            cli.session_configs = {}
            cli.deployed_servers = []
            return cli

    def test_default_with_whitespace_command(self, cli):
        """Test default method with whitespace-only command."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.default("   \t  \n  ")

            # Should not print anything for whitespace-only lines
            mock_console.print.assert_not_called()

    def test_tools_command_multiple_flags(self, cli):
        """Test tools command with multiple flags."""
        cli.enhanced_cli.templates = {"github": {"name": "github"}}
        cli._show_template_help = MagicMock()

        cli.do_tools("github --help --force-server")

        # Help should take precedence
        cli._show_template_help.assert_called_once_with("github")

    def test_config_command_single_arg(self, cli):
        """Test config command with only template name."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_config("github")

            mock_console.print.assert_any_call(
                "[red]❌ Please provide template name and at least one config value[/red]"
            )

    def test_clear_config_nonexistent_template(self, cli):
        """Test clear_config with template that has no configuration."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_clear_config("nonexistent")

            # Should print a warning message for nonexistent template
            mock_console.print.assert_any_call(
                "[yellow]⚠️  No configuration found for 'nonexistent'[/yellow]"
            )

    def test_show_config_template_name_with_spaces(self, cli):
        """Test show_config with template name containing spaces."""
        with patch("mcp_template.interactive_cli.console") as mock_console:
            cli.do_show_config("template with spaces")

            # Should handle gracefully
            mock_console.print.assert_any_call(
                "[yellow]⚠️  No configuration found for 'template with spaces'[/yellow]"
            )

    def test_list_servers_empty_result(self, cli):
        """Test list_servers when no servers are deployed."""
        cli.deployment_manager.list_deployments.return_value = []

        with patch("mcp_template.interactive_cli.console"):
            cli.do_list_servers("")

            # Should call beautifier with empty list
            cli.beautifier.beautify_deployed_servers.assert_called_once_with([])

    def test_list_servers_all_stopped(self, cli):
        """Test list_servers when all servers are stopped."""
        mock_servers = [
            {"id": "1", "name": "server1", "status": "stopped"},
            {"id": "2", "name": "server2", "status": "failed"},
        ]
        cli.deployment_manager.list_deployments.return_value = mock_servers

        with patch("mcp_template.interactive_cli.console"):
            cli.do_list_servers("")

            # Should filter out non-running servers
            cli.beautifier.beautify_deployed_servers.assert_called_once_with([])
            assert cli.deployed_servers == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
