#!/usr/bin/env python3
"""
Test suite for demo server tools.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import DemoServerConfig
    from tools import register_tools
except ImportError:
    # Fallback for testing
    import importlib.util

    tools_path = Path(__file__).parent.parent / "tools.py"
    spec = importlib.util.spec_from_file_location("tools", tools_path)
    tools_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tools_module)
    register_tools = tools_module.register_tools

    config_path = Path(__file__).parent.parent / "config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    DemoServerConfig = config_module.DemoServerConfig


class TestDemoTools:
    """Test cases for demo server tools."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_mcp = Mock()
        self.mock_tools = {}

        # Mock the @mcp.tool() decorator
        def mock_tool_decorator():
            def decorator(func):
                self.mock_tools[func.__name__] = func
                return func

            return decorator

        self.mock_mcp.tool = mock_tool_decorator

        # Create test configuration
        self.config = DemoServerConfig(
            {"hello_from": "Test Server", "log_level": "debug"}
        )

    def test_register_tools(self):
        """Test that all tools are registered correctly."""
        register_tools(self.mock_mcp, self.config)

        # Check that expected tools were registered
        expected_tools = ["say_hello", "get_server_info", "echo_message"]
        for tool_name in expected_tools:
            assert tool_name in self.mock_tools

    def test_say_hello_without_name(self):
        """Test say_hello tool without name parameter."""
        register_tools(self.mock_mcp, self.config)

        say_hello = self.mock_tools["say_hello"]
        result = say_hello()

        assert result == "Hello! Greetings from Test Server!"

    def test_say_hello_with_name(self):
        """Test say_hello tool with name parameter."""
        register_tools(self.mock_mcp, self.config)

        say_hello = self.mock_tools["say_hello"]
        result = say_hello(name="Alice")

        assert result == "Hello Alice! Greetings from Test Server!"

    def test_get_server_info(self):
        """Test get_server_info tool."""
        register_tools(self.mock_mcp, self.config)

        get_server_info = self.mock_tools["get_server_info"]
        result = get_server_info()

        # Parse the JSON result
        server_info = json.loads(result)

        assert server_info["name"] == "Demo Hello MCP Server"
        assert server_info["hello_from"] == "Test Server"
        assert server_info["log_level"] == "debug"
        assert "capabilities" in server_info
        assert "tools" in server_info
        assert len(server_info["tools"]) == 3

    def test_echo_message(self):
        """Test echo_message tool."""
        register_tools(self.mock_mcp, self.config)

        echo_message = self.mock_tools["echo_message"]
        result = echo_message(message="Hello World")

        assert result == "[Test Server] Echo: Hello World"

    def test_server_info_structure(self):
        """Test the structure of server info response."""
        register_tools(self.mock_mcp, self.config)

        get_server_info = self.mock_tools["get_server_info"]
        result = get_server_info()
        server_info = json.loads(result)

        # Check required fields
        required_fields = [
            "name",
            "version",
            "description",
            "hello_from",
            "log_level",
            "capabilities",
            "tools",
        ]
        for field in required_fields:
            assert field in server_info

        # Check capabilities structure
        assert isinstance(server_info["capabilities"], list)
        assert len(server_info["capabilities"]) >= 2

        # Check tools structure
        assert isinstance(server_info["tools"], list)
        tool_names = [tool["name"] for tool in server_info["tools"]]
        expected_tools = ["say_hello", "get_server_info", "echo_message"]
        for tool_name in expected_tools:
            assert tool_name in tool_names

    def test_tools_with_different_config(self):
        """Test tools behavior with different configuration."""
        different_config = DemoServerConfig(
            {"hello_from": "Different Server", "log_level": "info"}
        )

        register_tools(self.mock_mcp, different_config)

        # Test say_hello with different config
        say_hello = self.mock_tools["say_hello"]
        result = say_hello(name="Bob")
        assert result == "Hello Bob! Greetings from Different Server!"

        # Test echo_message with different config
        echo_message = self.mock_tools["echo_message"]
        result = echo_message(message="Test")
        assert result == "[Different Server] Echo: Test"
