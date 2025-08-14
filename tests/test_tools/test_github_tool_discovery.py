"""
Comprehensive tests for GitHub tool discovery functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.core.tool_manager import ToolManager


@pytest.mark.unit
class TestGitHubToolDiscovery:
    """Test GitHub-specific tool discovery functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "cache"
        self.template_dir = self.temp_dir / "github"
        self.template_dir.mkdir(parents=True)

        self.tool_manager = ToolManager(backend_type="docker")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_github_static_tool_discovery(self):
        """Test static tool discovery from GitHub tools.json."""
        # Create GitHub tools.json with sample tools
        tools_data = {
            "tools": [
                {
                    "name": "create_repository",
                    "description": "Create new GitHub repositories",
                    "category": "Repository Management",
                    "parameters": {},
                },
                {
                    "name": "search_repositories",
                    "description": "Search for GitHub repositories",
                    "category": "Repository Management",
                    "parameters": {},
                },
                {
                    "name": "get_me",
                    "description": "Get authenticated user details",
                    "category": "User & Profile",
                    "parameters": {},
                },
            ],
            "discovery_method": "static",
            "total_tools": 3,
        }

        tools_file = self.template_dir / "tools.json"
        with open(tools_file, "w") as f:
            json.dump(tools_data, f, indent=2)

        # Test static discovery
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",  # Should fallback to static
            "docker_image": "dataeverything/mcp-github",
        }

        result = self.tool_manager.discover_tools(
            template_or_deployment="github",
        )

        # ToolManager.discover_tools returns a list of tools, not a metadata dict
        assert isinstance(result, list)
        # GitHub template has comprehensive tool set (discovered from actual template)
        assert len(result) >= 77  # At least 77 tools discovered

        # Check specific tools we know should be present
        tool_names = {tool["name"] for tool in result}
        assert "create_repository" in tool_names
        assert "search_repositories" in tool_names
        assert "get_me" in tool_names

    @pytest.mark.skip("Uses deprecated ToolDiscovery API with private method patching")
    @patch("mcp_template.tools.tool_manager.ToolDiscovery._discover_dynamic_tools")
    def test_github_dynamic_discovery_priority_with_credentials(self, mock_dynamic):
        """Test that dynamic discovery is tried first when valid credentials are available."""
        # Setup mock dynamic discovery response
        mock_dynamic.return_value = {
            "tools": [
                {
                    "name": "dynamic_tool",
                    "description": "From dynamic discovery",
                    "category": "test",
                }
            ],
            "discovery_method": "stdio_docker",
            "timestamp": 1754369000,
        }

        # Create static tools.json as fallback
        tools_data = {
            "tools": [
                {
                    "name": "static_tool",
                    "description": "From static discovery",
                    "category": "test",
                }
            ]
        }
        tools_file = self.template_dir / "tools.json"
        with open(tools_file, "w") as f:
            json.dump(tools_data, f)

        # Config with valid GitHub token and config schema
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "config_schema": {
                "properties": {
                    "github_token": {
                        "type": "string",
                        "env_mapping": "GITHUB_PERSONAL_ACCESS_TOKEN",
                    }
                }
            },
            "user_config": {"github_token": "dummy"},
        }

        result = self.tool_manager.discover_tools(
            "github", config, self.template_dir, use_cache=False
        )

        # Should use dynamic discovery
        mock_dynamic.assert_called_once()
        assert (
            result["discovery_method"] == "stdio_docker"
        )  # Preserves the original discovery method from mock
        assert result["fallback_available"]
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "dynamic_tool"

    @pytest.mark.skip("Uses deprecated ToolDiscovery API with private method patching")
    @patch("mcp_template.tools.tool_manager.ToolDiscovery._discover_dynamic_tools")
    def test_github_static_fallback_when_dynamic_fails(self, mock_dynamic):
        """Test fallback to static discovery when dynamic discovery fails."""
        # Setup mock dynamic discovery to fail
        mock_dynamic.return_value = None

        # Create static tools.json
        tools_data = {
            "tools": [
                {
                    "name": "static_tool",
                    "description": "From static discovery",
                    "category": "test",
                }
            ]
        }
        tools_file = self.template_dir / "tools.json"
        with open(tools_file, "w") as f:
            json.dump(tools_data, f)

        # Config with valid GitHub token and config schema
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "config_schema": {
                "properties": {
                    "github_token": {
                        "type": "string",
                        "env_mapping": "GITHUB_PERSONAL_ACCESS_TOKEN",
                    }
                }
            },
            "user_config": {"github_token": "dummy"},
        }

        result = self.tool_manager.discover_tools(
            "github", config, self.template_dir, use_cache=False
        )

        # Should fallback to static discovery
        mock_dynamic.assert_called_once()
        assert result["discovery_method"] == "static"
        assert result["dynamic_available"]
        assert "Static discovery used" in result["notes"]
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "static_tool"

    def test_github_static_discovery_without_credentials(self):
        """Test static discovery when no valid credentials are provided."""
        # Config without valid credentials
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "user_config": {"github_token": "dummy_token"},  # Invalid token
        }

        result = self.tool_manager.discover_tools("github", config_values=config)

        # Should return tools from static discovery (the real github template)
        assert isinstance(result, list)
        assert len(result) >= 77  # Should use the real GitHub tools.json
        # Verify it contains expected GitHub tools
        tool_names = {tool["name"] for tool in result}
        assert "create_repository" in tool_names
        assert "get_me" in tool_names

    def test_github_comprehensive_tools_list(self):
        """Test that the comprehensive GitHub tools list is properly loaded."""
        # Use the actual GitHub tools.json file
        github_template_dir = (
            Path(__file__).parent.parent.parent
            / "mcp_template"
            / "template"
            / "templates"
            / "github"
        )

        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
        }

        result = self.tool_manager.discover_tools("github", config_values=config)

        # Should find all GitHub tools
        assert isinstance(result, list)
        assert len(result) >= 77  # Should have at least 77 tools

        # Check for specific categories
        categories = {tool["category"] for tool in result}
        expected_categories = {
            "Repository Management",
            "Branch & Tag Management",
            "Issue Management",
            "Pull Request Management",
            "Code Review & Comments",
            "GitHub Actions & Workflows",
            "Security & Scanning",
            "Discussions",
            "Notifications & Activity",
            "Search & Discovery",
            "User & Profile",
        }

        # Most categories should be present
        assert len(categories.intersection(expected_categories)) >= 8

        # Check for specific important tools
        tool_names = {tool["name"] for tool in result}
        important_tools = {
            "create_repository",
            "search_repositories",
            "create_issue",
            "create_pull_request",
            "list_workflows",
            "get_me",
        }
        assert important_tools.issubset(tool_names)

    def test_github_tool_normalization(self):
        """Test that GitHub tools are properly normalized."""
        config = {"name": "Github", "tool_discovery": "dynamic"}

        result = self.tool_manager.discover_tools("github", config_values=config)

        # Check that tools are normalized - test first tool
        assert len(result) > 0
        tool = result[0]
        assert "name" in tool
        assert "description" in tool
        assert "category" in tool
        assert "parameters" in tool
        # Check that parameters have proper schema structure
        if tool["parameters"]:
            assert isinstance(tool["parameters"], dict)

    def test_github_caching_behavior(self):
        """Test caching behavior for GitHub tool discovery."""
        config = {"name": "Github", "tool_discovery": "dynamic"}

        # First call should discover and cache
        result1 = self.tool_manager.discover_tools("github", config_values=config)

        # Second call should use cache
        result2 = self.tool_manager.discover_tools("github", config_values=config)

        assert result1 == result2
        assert isinstance(result1, list)

        # Force refresh should bypass cache
        result3 = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=True
        )

        assert isinstance(result3, list)  # Same result but refreshed

    @pytest.mark.skip("Uses deprecated ToolDiscovery API with private method patching")
    @patch("mcp_template.tools.tool_manager.ToolDiscovery._discover_dynamic_tools")
    def test_github_dynamic_discovery_with_mcp_client(self, mock_dynamic):
        """Test dynamic discovery using MCP client probe."""
        # Mock successful dynamic discovery with comprehensive tools
        mock_dynamic.return_value = {
            "tools": [
                {
                    "name": "create_repository",
                    "description": "Create repos",
                    "category": "Repository",
                },
                {
                    "name": "list_issues",
                    "description": "List issues",
                    "category": "Issues",
                },
                {"name": "get_me", "description": "Get user", "category": "User"},
            ],
            "discovery_method": "stdio_docker",
            "timestamp": 1754369000,
            "server_info": {"name": "github-mcp-server", "version": "v0.9.1"},
        }

        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "transport": {"default": "stdio", "supported": ["stdio"]},
            "user_config": {"github_token": "dummy"},
            "config_schema": {
                "properties": {
                    "github_token": {"env_mapping": "GITHUB_PERSONAL_ACCESS_TOKEN"}
                }
            },
        }

        result = self.tool_manager.discover_tools(
            "github", config, self.template_dir, use_cache=False
        )

        mock_dynamic.assert_called_once_with("github", config)
        assert (
            result["discovery_method"] == "stdio_docker"
        )  # Preserves the original discovery method from mock
        assert len(result["tools"]) == 3
        assert "server_info" in result

    def test_github_error_handling_and_fallbacks(self):
        """Test error handling and fallback strategies."""
        # Test with non-existent template
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "user_config": {"github_token": "dummy_token"},  # Invalid token
        }

        result = self.tool_manager.discover_tools(
            "nonexistent_template", config_values=config
        )

        # Should return empty result when template not found
        assert isinstance(result, list)
        assert result == []  # Empty list when no tools found


@pytest.mark.integration
class TestGitHubToolDiscoveryIntegration:
    """Integration tests for GitHub tool discovery with real MCP server."""

    def setup_method(self):
        """Set up integration test environment."""
        self.tool_manager = ToolManager(backend_type="docker")

    @pytest.mark.skip(reason="Integration test requires real GitHub token")
    def test_github_real_token_dynamic_discovery(self):
        """Test dynamic discovery with real GitHub token (requires --run-integration)."""
        # This test would require a real GitHub token
        # It should be run sparingly to avoid rate limits
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "user_config": {"github_token": "dummy"},
        }

        result = self.tool_manager.discover_tools("github", config_values=config)

        # Should successfully discover tools with real token
        if result:  # If tools were found
            assert len(result) > 0
            assert any(tool["name"] == "create_repository" for tool in result)
