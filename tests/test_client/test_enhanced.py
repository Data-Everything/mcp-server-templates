"""
Unit tests for the enhanced MCPClient.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.exceptions import ToolCallError
from mcp_template.core.tool_caller import ToolCallResult


@pytest.mark.unit
class TestMCPClient:
    """Test cases for MCPClient functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            self.client = MCPClient()

    def test_initialization(self):
        """Test MCPClient initialization."""
        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):

            # Test default initialization
            client = MCPClient()
            assert client.timeout == 30

            # Test custom timeout
            client = MCPClient(timeout=60)
            assert client.timeout == 60

    def test_list_templates(self):
        """Test template listing."""
        # Use real template manager to get actual template data
        # The client should return the real template discovery results
        templates = self.client.list_templates()

        # Verify we get actual templates from discovery
        assert isinstance(templates, dict)
        assert "demo" in templates

        # Check demo template has expected structure
        demo_template = templates["demo"]
        assert "name" in demo_template
        assert "transport" in demo_template
        assert demo_template["transport"]["default"] in ["http", "stdio"]

    def test_get_template_info(self):
        """Test getting template information."""
        # Test getting info for demo template
        template_info = self.client.get_template_info("demo")

        # Verify we get actual template info
        assert template_info is not None
        assert isinstance(template_info, dict)
        assert "name" in template_info
        assert "transport" in template_info

        # Test getting info for non-existent template
        non_existent = self.client.get_template_info("nonexistent")
        assert non_existent is None

    def test_list_tools_demo_template(self):
        """Test tool listing for demo template (hardcoded)."""
        # Mock the tool manager's list_tools method to return expected tools
        with patch.object(self.client.tool_manager, "list_tools") as mock_list_tools:
            mock_tools = [
                {"name": "say_hello", "description": "Say hello"},
                {"name": "echo_message", "description": "Echo a message"},
            ]
            mock_list_tools.return_value = {
                "tools": mock_tools,
                "discovery_method": "auto",
                "metadata": {},
            }

            tools = self.client.list_tools("demo")

            # Verify we get tools for demo template
            assert isinstance(tools, list)
            assert len(tools) == 2

            # Check each tool has expected structure
            for tool in tools:
                assert isinstance(tool, dict)
                assert "name" in tool

    def test_call_tool_success(self):
        """Test successful tool call."""
        # Mock the tool manager's call_tool to return a successful result
        with patch.object(self.client.tool_manager, "call_tool") as mock_call:
            mock_call.return_value = {
                "success": True,
                "result": {"content": [{"type": "text", "text": "Hello World"}]},
                "is_error": False,
            }

            result = self.client.call_tool("demo", "test_tool", {"arg": "value"})

            assert result is not None
            assert result["success"]

    def test_call_tool_error(self):
        """Test tool call error handling."""
        # Mock the tool manager's call_tool to return an error result
        with patch.object(self.client.tool_manager, "call_tool") as mock_call:
            mock_call.return_value = {
                "success": False,
                "is_error": True,
                "error_message": "Tool execution failed",
            }

            result = self.client.call_tool("demo", "test_tool", {"arg": "value"})

            assert result is not None
            assert not result["success"]

    def test_call_tool_template_not_found(self):
        """Test tool call with non-existent template."""
        # Mock the tool manager to raise an exception for non-existent template
        with patch.object(self.client.tool_manager, "call_tool") as mock_call:
            mock_call.side_effect = Exception("Template not found")

            result = self.client.call_tool("nonexistent", "test_tool", {"arg": "value"})

            # Should return None on exception
            assert result is None

    def test_list_servers(self):
        """Test listing running servers."""
        # Mock the deployment manager to return deployments
        with patch.object(
            self.client.deployment_manager, "find_deployments_by_criteria"
        ) as mock_find:
            mock_deployments = [{"id": "server1", "template": "demo"}]
            mock_find.return_value = mock_deployments

            servers = self.client.list_servers()

            assert servers == mock_deployments

    def test_start_server(self):
        """Test starting a server."""
        # Mock the deployment manager to return successful deployment
        with patch.object(
            self.client.deployment_manager, "deploy_template"
        ) as mock_deploy:
            # Mock successful deployment result
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_result = DeploymentResult(
                success=True, deployment_id="server1", template="demo", status="running"
            )
            mock_deploy.return_value = mock_result

            server_info = self.client.start_server("demo", {"config": "value"})

            # Should get the result dict
            assert server_info is not None
            assert isinstance(server_info, dict)

    def test_stop_server(self):
        """Test stopping a server."""
        # Mock the deployment manager to return successful stop
        with patch.object(
            self.client.deployment_manager, "stop_deployment"
        ) as mock_stop:
            mock_result = {"success": True}
            mock_stop.return_value = mock_result

            result = self.client.stop_server("server1")

            # stop_server returns the deployment manager result
            assert result == mock_result


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
