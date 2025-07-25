"""
Demo Hello MCP Server

A simple demonstration MCP server that provides greeting tools using FastMCP.
This follows the same pattern as the file-server template.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict

try:
    from fastmcp import FastMCP
except ImportError as e:
    print("Required dependencies not found. Install with:")
    print("pip install fastmcp>=2.10.0")
    print(f"Error: {e}")
    sys.exit(1)


class DemoServerConfig:
    """Configuration management for the demo server."""

    def __init__(self):
        # Parse configuration from environment variables
        self.hello_from = os.getenv("MCP_HELLO_FROM", "MCP Platform")

        # Setup logging
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("demo-server")
        self.logger.info("Demo server configured with hello_from=%s", self.hello_from)


class DemoServer:
    """FastMCP-based demo server implementation."""

    def __init__(self):
        """Initialize the demo server."""

        self.config = DemoServerConfig()
        self.mcp = FastMCP(name="demo-hello-server")
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all demo server tools."""

        @self.mcp.tool()
        async def say_hello(name: str = None) -> str:
            """
            Generate a personalized greeting message.

            Args:
                name: Name of the person to greet (optional)

            Returns:
                A personalized greeting message
            """
            if name:
                return f"Hello {name}! Greetings from {self.config.hello_from}!"
            else:
                return f"Hello! Greetings from {self.config.hello_from}!"

        @self.mcp.tool()
        async def get_server_info() -> Dict[str, Any]:
            """
            Get information about the demo server.

            Returns:
                Dictionary with server information
            """
            return {
                "server_name": "Demo Hello MCP Server",
                "version": "1.0.0",
                "greeting_source": self.config.hello_from,
                "capabilities": [
                    "say_hello - Generate personalized greetings",
                    "get_server_info - Get server information",
                ],
                "status": "running",
            }

    def run(self):
        """Run the MCP server."""
        self.config.logger.info("Starting Demo Hello MCP Server")
        # FastMCP handles its own event loop
        self.mcp.run(transport="stdio")


def main():
    """Main entry point."""
    server = DemoServer()
    server.run()


if __name__ == "__main__":
    asyncio.run(main())
