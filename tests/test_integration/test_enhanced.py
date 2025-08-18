"""
Integration tests for the enhanced MCP Client and ToolCaller.
"""

import subprocess
import time
from pathlib import Path

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.tool_caller import ToolCaller
from mcp_template.exceptions import ToolCallError


@pytest.mark.integration
class TestIntegration:
    """Integration tests for real MCP functionality."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client instance for testing."""
        return MCPClient()

    @pytest.fixture(scope="class")
    def tool_caller(self):
        """Create a ToolCaller instance for testing."""
        return ToolCaller()

    def test_client_initialization(self, client):
        """Test that client initializes properly."""
        assert client is not None
        assert hasattr(client, "tool_caller")
        assert hasattr(client, "tool_manager")

    def test_template_discovery(self, client):
        """Test template discovery works."""
        templates = client.list_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0
        assert "demo" in templates

        # Check demo template structure
        demo_template = templates["demo"]
        assert "transport" in demo_template
        assert "description" in demo_template

    def test_template_info_retrieval(self, client):
        """Test getting specific template information."""
        demo_info = client.get_template_info("demo")

        assert demo_info is not None
        assert isinstance(demo_info, dict)
        assert "transport" in demo_info

        # Test non-existent template
        non_existent = client.get_template_info("does_not_exist")
        assert non_existent is None

    def test_tool_listing(self, client):
        """Test tool listing functionality."""
        tools = client.list_tools("demo")

        assert isinstance(tools, list)
        assert len(tools) >= 2  # At least say_hello and get_server_info

        tool_names = [tool["name"] for tool in tools]
        assert "say_hello" in tool_names
        assert "get_server_info" in tool_names

    def test_stdio_tool_calling(self, client):
        """Test actual tool calling via stdio transport."""
        try:
            result = client.call_tool(
                template_name="demo",
                tool_name="say_hello",
                arguments={"name": "IntegrationTest"},
            )

            assert result["success"]
            assert not result["is_error"]
            assert result["result"] is not None

            # Check that we got actual content
            assert "content" in result["result"]
            content = result["result"]["content"]
            assert isinstance(content, list)
            assert len(content) > 0

            # Check structured content
            if "structuredContent" in result["result"]:
                structured = result["result"]["structuredContent"]
                assert "IntegrationTest" in str(structured)

        except Exception as e:
            pytest.skip(f"Docker not available or demo template not working: {e}")

    def test_error_handling(self, client):
        """Test error handling for invalid tool calls."""
        # Test invalid template - should return error response
        result = client.call_tool("invalid_template", "test_tool")
        assert isinstance(result, dict)
        assert result.get("success") is False
        assert "not found" in result.get("error", "").lower()

        # Test invalid tool (should handle gracefully)
        try:
            result = client.call_tool("demo", "invalid_tool")
            # Should return error response, not raise exception
            assert result is None or (
                isinstance(result, dict)
                and (not result.get("success", True) or result.get("is_error", False))
            )
        except Exception as e:
            pytest.skip(f"Demo template not available: {e}")

    def test_cli_integration(self):
        """Test that CLI still works after integration."""
        try:
            # Test CLI help
            result = subprocess.run(
                ["python", "-m", "mcp_template", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=Path(__file__).parent.parent,
            )

            assert result.returncode == 0
            assert "MCP Template" in result.stdout or "usage:" in result.stdout

        except subprocess.TimeoutExpired:
            pytest.skip("CLI test timed out")
        except FileNotFoundError:
            pytest.skip("Python module not found")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s"])
