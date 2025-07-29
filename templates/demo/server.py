#!/usr/bin/env python3
"""
Demo MCP Server - Reference Implementation

A demonstration MCP server that showcases FastMCP best practices
following the official FastMCP documentation patterns.
"""

import os
import sys
from typing import Any, Dict

from fastmcp import FastMCP

try:
    from .config import DemoServerConfig
except ImportError:
    try:
        from config import DemoServerConfig
    except ImportError:
        # Fallback for Docker or direct script execution
        sys.path.append(os.path.dirname(__file__))
        from config import DemoServerConfig


def load_value_from_env_or_config(
    key: str,
    config: Dict[str, Any],
    env_var_name: str = None,
    env_var_prefix: str = None,
    default_value: Any = None,
) -> str:
    """
    Load a value from the environment or the template data.

    Args:
        key: The key to look up
        config: The template data dictionary
        env_var_name: The name of the environment variable
        env_var_prefix: Optional prefix for the environment variable
        default_value: The default value if neither is found

    Returns:
        The value from the environment or template data
    """

    if not env_var_name:
        env_var_name = key.upper()

    if env_var_prefix:
        env_var_name = f"{env_var_prefix}_{env_var_name}"

    # Check environment variable first
    env_value = os.getenv(env_var_name)
    if env_value is not None:
        return env_value

    return config.get(key, default_value)


class DemoMCPServer:
    """
    Demo MCP Server implementation using FastMCP.
    """

    def __init__(self, config_dict: dict = None):
        """
        Initialize the Demo MCP Server with configuration.
        """

        self.config = DemoServerConfig(config_dict=config_dict or {})
        self.template_data = self.config._load_template()
        self.config_data = self.config.get_template_config()
        self.logger = self.config.logger
        self.logger.info("Demo MCP Server initialized with configuration")
        self.mcp = FastMCP(
            name=self.template_data.get("name", "demo-server"),
            instructions="A simple demonstration MCP server that provides greeting tools",
            include_tags=self.template_data.get("tags", ["fastmcp", "http"]),
            version=self.template_data.get("version", "1.0.0"),
        )
        self.register_tools()

    def register_tools(self):
        """
        Register tools with the MCP server.
        """

        self.mcp.tool(self.say_hello, tags=["fastmcp", "greeting"])
        self.mcp.tool(self.get_server_info, tags=["fastmcp", "info"])
        self.mcp.tool(self.echo_message, tags=["fastmcp", "http"])

    def say_hello(self, name: str = "World") -> str:
        """
        Generate a personalized greeting message.

        Args:
            name: Name of the person to greet (optional)

        Returns:
            A personalized greeting message
        """

        if name and name != "World":
            greeting = f"Hello {name}! Greetings from {self.config_data.get('hello_from', 'Demo Server')}!"
        else:
            greeting = f"Hello! Greetings from {self.config_data.get('hello_from', 'Demo Server')}!"

        return greeting

    def get_server_info(self) -> dict:
        """
        Get information about the demo MCP server.

        Returns:
            Dictionary containing server information
        """

        return {
            "name": "Demo MCP Server",
            "version": "1.0.0",
            "description": "A simple demonstration MCP server that provides greeting tools",
            "hello_from": self.config_data.get("hello_from", "Demo Server"),
            "log_level": self.template_data.get("log_level", "info"),
            "capabilities": ["Greeting Tools", "Server Information"],
            "transport": "http",
            "port": 7071,
        }

    def echo_message(self, message: str) -> str:
        """
        Echo back a message with server identification.

        Args:
            message: Message to echo back

        Returns:
            Echoed message with server identification
        """

        echoed = (
            f"[{self.config_data.get('hello_from', 'Demo Server')}] Echo: {message}"
        )
        return echoed

    def run(self):
        """
        Run the MCP server with the configured transport and port.
        """

        self.mcp.run(
            transport=os.getenv(
                "MCP_TRANSPORT",
                self.template_data.get("transport", {}).get("default", "http"),
            ),
            port=os.getenv(
                "MCP_PORT", self.template_data.get("transport", {}).get("port", 7071)
            ),
            log_level=self.config.log_level,
        )


server = DemoMCPServer(config_dict={})

# Create the server instance for standalone usage
if __name__ == "__main__":
    # Create a DemoServer instance for direct usage
    server.run()
