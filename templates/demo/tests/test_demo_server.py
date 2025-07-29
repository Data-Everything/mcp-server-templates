"""
Test cases for the FastMCP server using pytest and FastMCP Client.
"""

import sys
from pathlib import Path

import pytest
from fastmcp import Client

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from templates.demo import DemoMCPServer

demo_server = DemoMCPServer()


@pytest.mark.asyncio
async def test_list_tools():
    """
    Test if the server lists tools correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        tools = await client.list_tools()
        assert isinstance(tools, list)
        assert len(tools) == 4, f"Expected 4 tools, found {len(tools)}"
        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "say_hello",
            "get_server_info",
            "echo_message",
            "demonstrate_overrides",
        ]
        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"Tool {expected_tool} not found in {tool_names}"


@pytest.mark.asyncio
async def test_echo_tool():
    """
    Test the functionality of the 'echo' tool in the FastMCP server.
    This test checks if the server can process an echo request correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        result = await client.call_tool("echo_message", {"message": "Hi There"})
        expected = "Echo from Demo Hello MCP Server: Hi There"
        assert (
            result.data == expected
        ), f"Echo message did not match expected output. Got: {result.data}, Expected: {expected}"


@pytest.mark.asyncio
async def test_greet_tool():
    """
    Test the functionality of the 'greet' tool in the FastMCP server.
    This test checks if the server can process a greeting request correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        result = await client.call_tool("say_hello", {"name": "World"})
        expected = "Hello World! Greetings from MCP Platform!"
        assert (
            result.data == expected
        ), f"Greeting message did not match expected output. Got: {result.data}, Expected: {expected}"

        result2 = await client.call_tool("say_hello", {"name": "Test"})
        expected2 = "Hello Test! Greetings from MCP Platform!"
        assert (
            result2.data == expected2
        ), f"Greeting message did not match expected output. Got: {result2.data}, Expected: {expected2}"


@pytest.mark.asyncio
async def test_get_server_info():
    """
    Test the functionality of the 'get_server_info' tool in the FastMCP server.
    This test checks if the server can provide its configuration data correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        result = await client.call_tool("get_server_info")
        assert isinstance(result.data, dict), "Server info should be a dictionary"
        assert (
            "standard_config" in result.data
        ), "Server info should contain 'standard_config' key"
        assert (
            "hello_from" in result.data["standard_config"]
        ), "Server info standard_config should contain 'hello_from' key"
        assert (
            result.data["standard_config"]["hello_from"] == "MCP Platform"
        ), "Server info hello_from did not match expected value"
