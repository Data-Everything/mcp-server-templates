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
        assert len(tools) == 3, "No tools found in the server"


@pytest.mark.asyncio
async def test_echo_tool():
    """
    Test the functionality of the 'echo' tool in the FastMCP server.
    This test checks if the server can process an echo request correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        result = await client.call_tool("echo_message", {"message": "Hi There"})
        assert (
            result.data == "[MCP Platform] Echo: Hi There"
        ), "Echo message did not match expected output"


@pytest.mark.asyncio
async def test_greet_tool():
    """
    Test the functionality of the 'greet' tool in the FastMCP server.
    This test checks if the server can process a greeting request correctly.
    """

    client = Client(demo_server.mcp)
    async with client:
        result = await client.call_tool("say_hello", {"name": "World"})
        assert (
            result.data == "Hello! Greetings from MCP Platform!"
        ), "Greeting message did not match expected output"

        result2 = await client.call_tool("say_hello", {"name": "Test"})
        assert (
            result2.data == "Hello Test! Greetings from MCP Platform!"
        ), "Greeting message did not match expected output"


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
            "hello_from" in result.data
        ), "Server info should contain 'hello_from' key"
        assert (
            result.data["hello_from"] == "MCP Platform"
        ), "Server info did not match expected value"
