#!/usr/bin/env python3
"""
Demo MCP Server - Reference Implementation

A demonstration MCP server that showcases FastMCP best practices
following the official FastMCP documentation patterns.
"""

from fastmcp import FastMCP

# Import configuration for testing compatibility
try:
    from .config import DemoServerConfig
except ImportError:
    from config import DemoServerConfig

# Import BaseMCPServer from the correct location
try:
    from ...mcp_template.base import BaseMCPServer
except ImportError:
    try:
        from mcp_template.base import BaseMCPServer
    except ImportError:
        # Fallback for standalone usage
        import sys

        sys.path.append("../..")
        from mcp_template.base import BaseMCPServer

# Create the server instance
mcp = FastMCP(name="Demo MCP Server 🚀")


def register_tools(mcp_server, config):
    """Register tools function for compatibility with tests."""
    # Import and call the actual register_tools from tools module
    try:
        from .tools import register_tools as tools_register
    except ImportError:
        from tools import register_tools as tools_register

    return tools_register(mcp_server, config)


class DemoServer(BaseMCPServer):
    """Demo MCP Server class that extends BaseMCPServer."""

    def __init__(self, config=None):
        # Initialize demo-specific configuration
        self.demo_config = DemoServerConfig(config)

        # Initialize the base server
        super().__init__("demo-server", config)

    def register_tools(self):
        """Register demo-specific tools with the MCP server."""
        return register_tools(self.mcp, self.demo_config)

    def get_tools(self):
        """Get available tools."""
        return ["say_hello", "get_server_info", "echo_message"]


@mcp.tool
def say_hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"


@mcp.tool
def get_server_info() -> dict:
    """Get information about the server."""
    return {
        "name": "Demo MCP Server",
        "version": "1.0.0",
        "transport": "http",
        "port": 7071,
    }


@mcp.tool
def echo_message(message: str) -> str:
    """Echo back the provided message."""
    return f"You said: {message}"


if __name__ == "__main__":
    # Run with HTTP transport on port 7071 as specified in Dockerfile
    mcp.run(transport="http", host="0.0.0.0", port=7071)
