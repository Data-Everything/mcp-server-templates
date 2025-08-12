"""
Unit tests for the enhanced MCPClient.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.tool_caller import ToolCallResult
from mcp_template.exceptions import ToolCallError


@pytest.mark.unit
class TestMCPClient:
    """Test cases for MCPClient functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with (
            patch("mcp_template.client.ServerManager"),
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            self.client = MCPClient()

    def test_initialization(self):
        """Test MCPClient initialization."""
        with (
            patch("mcp_template.client.ServerManager"),
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):

            # Test default initialization
            client = MCPClient()
            assert client.timeout == 30

            # Test custom timeout
            client = MCPClient(timeout=60)
            assert client.timeout == 60

    @patch("mcp_template.client.ServerManager")
    def test_list_templates(self, mock_server_manager):
        """Test template listing."""
        # Mock server manager response
        mock_templates = {
            "demo": {"name": "demo", "transport": {"default": "stdio"}},
            "test": {"name": "test", "transport": {"default": "http"}},
        }
        mock_server_manager.return_value.list_available_templates.return_value = (
            mock_templates
        )

        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            templates = client.list_templates()

        assert templates == mock_templates
        mock_server_manager.return_value.list_available_templates.assert_called_once()

    @patch("mcp_template.client.ServerManager")
    def test_get_template_info(self, mock_server_manager):
        """Test getting template information."""
        # Mock server manager response
        mock_template_info = {"name": "demo", "transport": {"default": "stdio"}}
        mock_server_manager.return_value.get_template_info.return_value = (
            mock_template_info
        )

        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            template_info = client.get_template_info("demo")

        assert template_info == mock_template_info
        mock_server_manager.return_value.get_template_info.assert_called_once_with(
            "demo"
        )

    def test_list_tools_demo_template(self):
        """Test tool listing for demo template (hardcoded)."""
        with (
            patch("mcp_template.client.ServerManager"),
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            tools = client.list_tools("demo")

        # Should return hardcoded demo tools
        assert len(tools) == 3
        tool_names = [tool["name"] for tool in tools]
        assert "say_hello" in tool_names
        assert "get_server_info" in tool_names
        assert "echo_message" in tool_names

    @patch("mcp_template.client.ToolCaller")
    def test_call_tool_success(self, mock_tool_caller):
        """Test successful tool call."""
        # Mock ToolCaller response
        mock_result = ToolCallResult(
            success=True,
            result={
                "content": [{"type": "text", "text": "Hello World"}],
                "isError": False,
            },
            content=[{"type": "text", "text": "Hello World"}],
            is_error=False,
        )
        mock_tool_caller.return_value.call_tool_stdio.return_value = mock_result

        # Mock server manager to return template info
        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager"),
        ):
            mock_server_manager.return_value.get_template_info.return_value = {
                "transport": {"supported": ["stdio"]}
            }

            client = MCPClient()
            result = client.call_tool("demo", "test_tool", {"arg": "value"})

        assert result["success"]
        assert not result["is_error"]
        assert result["result"] is not None
        assert result["error_message"] is None

    @patch("mcp_template.client.ToolCaller")
    def test_call_tool_error(self, mock_tool_caller):
        """Test tool call error handling."""
        # Mock ToolCaller error response
        mock_result = ToolCallResult(
            success=False, is_error=True, error_message="Tool execution failed"
        )
        mock_tool_caller.return_value.call_tool_stdio.return_value = mock_result

        # Mock server manager to return template info
        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager"),
        ):
            mock_server_manager.return_value.get_template_info.return_value = {
                "transport": {"supported": ["stdio"]}
            }

            client = MCPClient()
            result = client.call_tool("demo", "test_tool", {"arg": "value"})

        assert not result["success"]
        assert result["is_error"]
        assert result["error_message"] == "Tool execution failed"

    def test_call_tool_template_not_found(self):
        """Test tool call with non-existent template."""
        with (
            patch("mcp_template.client.ServerManager") as mock_server_manager,
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            mock_server_manager.return_value.get_template_info.return_value = None

            client = MCPClient()
            with pytest.raises(ToolCallError, match="Template 'nonexistent' not found"):
                client.call_tool("nonexistent", "test_tool")

    @patch("mcp_template.client.ServerManager")
    def test_list_servers(self, mock_server_manager):
        """Test listing running servers."""
        mock_servers = [{"id": "server1", "template": "demo"}]
        mock_server_manager.return_value.list_running_servers.return_value = (
            mock_servers
        )

        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            servers = client.list_servers()

        assert servers == mock_servers
        mock_server_manager.return_value.list_running_servers.assert_called_once()

    @patch("mcp_template.client.ServerManager")
    def test_start_server(self, mock_server_manager):
        """Test starting a server."""
        mock_server_info = {"id": "server1", "template": "demo", "status": "running"}
        mock_server_manager.return_value.start_server.return_value = mock_server_info

        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            server_info = client.start_server("demo", {"config": "value"})

        assert server_info == mock_server_info
        mock_server_manager.return_value.start_server.assert_called_once_with(
            template_id="demo",
            configuration={"config": "value"},
            pull_image=True,
            transport=None,
            port=None,
        )

    @patch("mcp_template.client.ServerManager")
    def test_stop_server(self, mock_server_manager):
        """Test stopping a server."""
        mock_server_manager.return_value.stop_server.return_value = True

        with (
            patch("mcp_template.client.ToolManager"),
            patch("mcp_template.client.ToolCaller"),
        ):
            client = MCPClient()
            success = client.stop_server("server1")

        assert success
        mock_server_manager.return_value.stop_server.assert_called_once_with("server1")


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
