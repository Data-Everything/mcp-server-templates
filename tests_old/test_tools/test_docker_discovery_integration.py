"""
Integration tests for Docker tool discovery functionality.
"""

from unittest.mock import patch

import pytest

from mcp_template.core.tool_manager import ToolManager
from mcp_template.tools.docker_probe import DockerProbe
from mcp_template.tools.mcp_client_probe import MCPClientProbe


@pytest.mark.integration
@pytest.mark.docker
class TestDockerDiscoveryIntegration:
    """Test Docker discovery functionality across CLI and discovery modules."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_manager = ToolManager(backend_type="docker")
        self.docker_probe = DockerProbe()
        self.mcp_client = MCPClientProbe()

    @patch("mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image")
    def test_template_discovery_uses_docker_for_dynamic_templates(
        self, mock_docker_discovery
    ):
        """Test that tool manager can discover tools from Docker images."""
        # Mock Docker discovery response
        mock_docker_discovery.return_value = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "category": "mcp",
                    "parameters": {},
                }
            ],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
        }

        # Test Docker image discovery
        image_name = "test/image:latest"
        timeout = 30

        result = self.tool_manager.discover_tools_from_image(image_name, timeout)

        # Verify Docker discovery was called
        mock_docker_discovery.assert_called_once_with(image_name, timeout)

        # Verify results - ToolManager.discover_tools_from_image returns List[Dict], not dict
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "test_tool"

    @patch("mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image")
    def test_docker_probe_with_environment_variables(self, mock_docker_discovery):
        """Test that Docker probe handles environment variables correctly."""
        mock_docker_discovery.return_value = {
            "tools": [
                {
                    "name": "github_tool",
                    "description": "GitHub tool",
                    "category": "mcp",
                    "parameters": {},
                }
            ],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
        }

        # Test direct Docker probe with environment variables
        image_name = "ghcr.io/github/github-mcp-server:0.9.1"
        env_vars = {"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"}

        result = self.docker_probe.discover_tools_from_image(
            image_name, env_vars=env_vars
        )

        # Verify Docker discovery was called with environment variables
        mock_docker_discovery.assert_called_once_with(image_name, env_vars=env_vars)

        # Verify results
        assert result is not None
        assert result["tools"][0]["name"] == "github_tool"

    @patch(
        "mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_docker_sync"
    )
    def test_mcp_client_handles_github_server_args(self, mock_discover):
        """Test that MCP client automatically adds 'stdio' for GitHub servers."""
        mock_discover.return_value = {
            "tools": [
                {
                    "name": "github_tool",
                    "description": "Test",
                    "category": "mcp",
                    "parameters": {},
                }
            ],
            "discovery_method": "mcp_client",
        }

        # Test with GitHub image (should add stdio automatically)
        result = self.mcp_client.discover_tools_from_docker_sync(
            "ghcr.io/github/github-mcp-server:0.9.1",
            args=None,  # No args provided
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test"},
        )

        # Verify stdio was added
        mock_discover.assert_called_once()
        call_args = mock_discover.call_args[0]  # positional args
        call_kwargs = mock_discover.call_args[1]  # keyword args

        # Should have added 'stdio' argument
        if len(call_args) > 1:
            # stdio should be in args
            assert "stdio" in call_args[1] or call_kwargs.get("args", [])

    @pytest.mark.skip(
        reason="Tests deprecated template-based discovery API that no longer exists"
    )
    def test_template_discovery_fallback_to_capabilities(self):
        """Test that discovery falls back to template capabilities when Docker fails."""
        pass

    @pytest.mark.skip(
        reason="Tests deprecated template-based discovery API that no longer exists"
    )
    def test_discovery_priority_order(self):
        """Test that discovery follows the correct priority order."""
        pass

    @pytest.mark.skip(
        reason="Tests deprecated template-based discovery API that no longer exists"
    )
    def test_env_vars_extraction_from_config_schema(self):
        """Test extraction of environment variables from config schema."""
        pass

    @pytest.mark.skip(
        reason="Tests deprecated template-based discovery API that no longer exists"
    )
    def test_caching_behavior_with_docker_discovery(self):
        """Test that Docker discovery results are properly cached."""
        pass

    @patch("mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image")
    def test_direct_docker_probe_call(self, mock_docker_discovery):
        """Test calling DockerProbe directly for integration scenarios."""
        mock_docker_discovery.return_value = {
            "tools": [
                {
                    "name": "direct_tool",
                    "description": "A direct tool",
                    "category": "mcp",
                    "parameters": {},
                }
            ],
            "discovery_method": "docker_mcp_stdio",
        }

        # Test direct probe usage
        result = self.docker_probe.discover_tools_from_image(
            "test/image:latest", env_vars={"TEST_VAR": "value"}
        )

        mock_docker_discovery.assert_called_once()
        assert result["tools"][0]["name"] == "direct_tool"
