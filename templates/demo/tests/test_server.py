"""Unit tests for demo server tools."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server import DemoServer, DemoServerConfig


class TestDemoServerTools:
    """Test cases for demo server MCP tools."""

    @pytest.fixture
    def demo_server(self, mock_env_vars):
        """Create a demo server instance for testing."""
        return DemoServer()

    @pytest.mark.asyncio
    async def test_say_hello_without_name(self, demo_server):
        """Test say_hello tool without a name parameter."""
        # Get the registered tool function
        tools = demo_server.mcp._tools
        say_hello_func = None

        for tool_name, tool_info in tools.items():
            if tool_name == "say_hello":
                say_hello_func = tool_info["func"]
                break

        assert say_hello_func is not None

        # Test the function directly
        result = await say_hello_func()
        assert "Hello!" in result
        assert "Test Server" in result

    @pytest.mark.asyncio
    async def test_say_hello_with_name(self, demo_server):
        """Test say_hello tool with a name parameter."""
        tools = demo_server.mcp._tools
        say_hello_func = None

        for tool_name, tool_info in tools.items():
            if tool_name == "say_hello":
                say_hello_func = tool_info["func"]
                break

        assert say_hello_func is not None

        result = await say_hello_func(name="Alice")
        assert "Hello Alice!" in result
        assert "Test Server" in result

    @pytest.mark.asyncio
    async def test_get_server_info(self, demo_server):
        """Test get_server_info tool."""
        tools = demo_server.mcp._tools
        server_info_func = None

        for tool_name, tool_info in tools.items():
            if tool_name == "get_server_info":
                server_info_func = tool_info["func"]
                break

        assert server_info_func is not None

        result = await server_info_func()

        assert isinstance(result, dict)
        assert result["server_name"] == "Demo Hello MCP Server"
        assert result["version"] == "1.0.0"
        assert result["greeting_source"] == "Test Server"
        assert "capabilities" in result
        assert result["status"] == "running"

    def test_tools_registration(self, demo_server):
        """Test that tools are properly registered."""
        tools = demo_server.mcp._tools

        assert "say_hello" in tools
        assert "get_server_info" in tools
        assert len(tools) == 2

    def test_server_initialization(self, mock_env_vars):
        """Test that the server initializes correctly."""
        server = DemoServer()

        assert server.config is not None
        assert server.mcp is not None
        assert server.config.hello_from == "Test Server"
