"""
Tests for GitHub tool discovery functionality.
Migrated from tests_old/test_tools/test_github_tool_discovery.py
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_template.core.cache import CacheManager
from mcp_template.core.tool_manager import ToolManager


@pytest.mark.unit
@pytest.mark.docker
class TestGitHubToolDiscovery:
    """Test GitHub-specific tool discovery functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.cache_dir = self.temp_dir / "cache"
        self.template_dir = self.temp_dir / "github"
        self.template_dir.mkdir(parents=True)

        self.tool_manager = ToolManager(backend_type="docker")
        self.tool_manager.cache_manager = CacheManager(cache_dir=self.cache_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_github_static_tool_discovery(self):
        """Test static tool discovery from GitHub tools.json."""
        # Test basic discovery functionality using the actual GitHub template
        # Force refresh to avoid cache issues in tests
        result = self.tool_manager.discover_tools(
            template_or_deployment="github", force_refresh=True
        )

        # ToolManager.discover_tools returns a dict with tools and metadata
        assert isinstance(result, dict)
        assert "tools" in result
        assert "discovery_method" in result

        tools = result["tools"]
        assert isinstance(tools, list)

        # GitHub template should have exactly 77 tools defined in tools.json
        assert len(tools) == 77, f"Expected 77 GitHub tools, got {len(tools)}"

        # Check specific tools we know should be present from the real tools.json
        tool_names = {tool["name"] for tool in tools}
        required_tools = {
            "create_repository",
            "search_repositories",
            "get_me",
            "create_issue",
            "create_pull_request",
        }
        missing_tools = required_tools - tool_names
        assert not missing_tools, f"Missing required GitHub tools: {missing_tools}"

    def test_github_static_discovery_without_credentials(self):
        """Test static discovery when no valid credentials are provided."""
        # Config without valid credentials
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
            "user_config": {"github_token": "dummy_token"},  # Invalid token
        }

        result = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=True
        )

        # Should return tools from static discovery (the real github template)
        assert isinstance(result, dict)
        assert "tools" in result

        tools = result["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 77, f"Expected 77 GitHub tools, got {len(tools)}"

        # Verify it contains expected GitHub tools from the actual tools.json
        tool_names = {tool["name"] for tool in tools}
        required_tools = {"create_repository", "get_me", "search_repositories"}
        missing_tools = required_tools - tool_names
        assert not missing_tools, f"Missing required GitHub tools: {missing_tools}"

    def test_github_comprehensive_tools_list(self):
        """Test that the comprehensive GitHub tools list is properly loaded."""
        # Use the actual GitHub tools.json file

        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "docker_image": "dataeverything/mcp-github",
        }

        result = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=True
        )

        # Should find all GitHub tools
        assert isinstance(result, dict)
        assert "tools" in result

        tools = result["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 77, f"Expected exactly 77 tools, got {len(tools)}"

        # Check for specific categories (the MCP server returns "mcp" category)
        categories = {tool.get("category", "uncategorized") for tool in tools}

        # The dynamic discovery from Docker container returns tools with "mcp" category
        # So let's check for the presence of tools from different functional areas instead
        tool_names = {tool["name"] for tool in tools}

        # Check functional coverage by verifying tools from major GitHub feature areas
        repo_tools = [
            name
            for name in tool_names
            if "repositor" in name.lower() or "repo" in name.lower()
        ]
        issue_tools = [name for name in tool_names if "issue" in name.lower()]
        pr_tools = [
            name
            for name in tool_names
            if "pull" in name.lower() or "_pr" in name.lower()
        ]
        workflow_tools = [
            name
            for name in tool_names
            if "workflow" in name.lower() or "job" in name.lower()
        ]
        search_tools = [name for name in tool_names if "search" in name.lower()]

        # Should have tools covering major GitHub functionality areas
        assert len(repo_tools) >= 2, f"Expected repository tools, found: {repo_tools}"
        assert (
            len(issue_tools) >= 3
        ), f"Expected issue management tools, found: {issue_tools}"
        assert len(pr_tools) >= 5, f"Expected pull request tools, found: {pr_tools}"
        assert (
            len(workflow_tools) >= 3
        ), f"Expected workflow/actions tools, found: {workflow_tools}"
        assert len(search_tools) >= 2, f"Expected search tools, found: {search_tools}"

        # Check for specific important tools
        tool_names = {tool["name"] for tool in tools}
        important_tools = {
            "create_repository",
            "search_repositories",
            "create_issue",
            "create_pull_request",
            "list_workflows",
            "get_me",
        }
        missing_important = important_tools - tool_names
        assert (
            not missing_important
        ), f"Missing important GitHub tools: {missing_important}"

    def test_github_tool_normalization(self):
        """Test that GitHub tools are properly normalized."""
        config = {"name": "Github", "tool_discovery": "dynamic"}

        result = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=True
        )

        # Should have exactly 77 tools from the GitHub template
        assert isinstance(result, dict)
        assert "tools" in result

        tools = result["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 77, f"Expected 77 GitHub tools, got {len(tools)}"

        # Test normalization of first few tools
        for i in range(min(3, len(tools))):
            tool = tools[i]
            assert "name" in tool, f"Tool {i} missing 'name' field"
            assert "description" in tool, f"Tool {i} missing 'description' field"
            assert "category" in tool, f"Tool {i} missing 'category' field"
            assert "parameters" in tool, f"Tool {i} missing 'parameters' field"

            # Check that parameters have proper schema structure
            assert isinstance(
                tool["parameters"], dict
            ), f"Tool {i} parameters should be dict"

            # Verify name and description are non-empty strings
            assert (
                isinstance(tool["name"], str) and tool["name"]
            ), f"Tool {i} name should be non-empty string"
            assert (
                isinstance(tool["description"], str) and tool["description"]
            ), f"Tool {i} description should be non-empty string"

    def test_github_caching_behavior(self):
        """Test caching behavior for GitHub tool discovery."""
        config = {"name": "Github", "tool_discovery": "dynamic"}

        tools = ["search_repo", "get_repo"]
        discovery_method_used = "stdio"
        source = "cache"
        self.tool_manager._cache_tools("github", tools, discovery_method_used, source)
        # First call should discover and cache (force refresh to ensure clean state)
        result1 = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=False
        )

        # Verify first result is valid
        assert isinstance(result1, dict)
        assert "tools" in result1
        assert result1["tools"] is not None, "First result should have tools"
        assert result1["discovery_method"] == "cache"
        assert len(result1["tools"]) == 2

    def test_github_error_handling_and_fallbacks(self):
        """Test error handling and fallback strategies."""
        # Test with non-existent template - this should genuinely return empty
        result = self.tool_manager.discover_tools("nonexistent_template_12345")

        # Should return empty result when template not found
        assert isinstance(result, dict)
        assert "tools" in result
        assert (
            result["tools"] is None or result["tools"] == []
        ), "Non-existent template should return empty tools"

        # Test with valid template but bad config should still work (fallback to static)
        config = {
            "name": "Github",
            "tool_discovery": "dynamic",
            "user_config": {"github_token": "dummy_token"},  # Invalid token
        }

        result_with_bad_config = self.tool_manager.discover_tools(
            "github", config_values=config, force_refresh=True
        )

        # Should still get tools via static discovery fallback
        assert isinstance(result_with_bad_config, dict)
        assert "tools" in result_with_bad_config
        tools = result_with_bad_config["tools"]
        assert isinstance(tools, list)
        assert len(tools) == 77, "Should fallback to static discovery with 77 tools"
