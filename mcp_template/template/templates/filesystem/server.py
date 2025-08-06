#!/usr/bin/env python3
"""
Filesystem - MCP Server Implementation.

Local filesystem access with configurable allowed paths.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .config import ServerConfig
except ImportError:
    try:
        from config import ServerConfig
    except ImportError:
        # Fallback for Docker or direct script execution
        sys.path.append(os.path.dirname(__file__))
        from config import ServerConfig


class FilesystemMCPServer:
    """
    Filesystem MCP Server implementation using FastMCP.
    """

    def __init__(self, config_dict: dict = None):
        """Initialize the Filesystem MCP Server with configuration."""
        self.config = ServerConfig(config_dict=config_dict or {})

        # Standard configuration data from config_schema
        self.config_data = self.config.get_template_config()

        # Full template data (potentially modified by double underscore notation)
        self.template_data = self.config.get_template_data()

        self.logger = self.config.logger

        self.mcp = FastMCP(
            name=self.template_data.get("name", "demo-server"),
            instructions="Local filesystem access with configurable allowed paths.",
            version="1.0.0",
        )
        logger.info(
            "%s MCP server %s created", self.template_data["name"], self.mcp.name
        )
        self.register_tools()

    def register_tools(self):
        """Register tools with the MCP server."""
        self.mcp.tool(self.example, tags=["example"])

    def example(self, message: str) -> str:
        """
        Example tool
        """

        return "Example tool executed successfully"

    def run(self):
        """Run the MCP server with the configured transport and port."""
        self.mcp.run(
            transport=os.getenv(
                "MCP_TRANSPORT",
                self.template_data.get("transport", {}).get("default", "http"),
            ),
            port=int(
                os.getenv(
                    "MCP_PORT",
                    self.template_data.get("transport", {}).get("port", 7071),
                )
            ),
            log_level=self.config_data.get("log_level", "info"),
        )


# Create the server instance
server = FilesystemMCPServer(config_dict={})

if __name__ == "__main__":
    server.run()
