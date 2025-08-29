#!/usr/bin/env python3
"""
Demo MCP Server - Reference Implementation

A demonstration MCP server that showcases two key patterns:
1. Standard configuration from template.json config_schema
2. Template data overrides via double underscore notation

This helps template authors understand both patterns.
"""

import logging
import os
import sys

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .config import DemoServerConfig
except ImportError:
    try:
        from config import DemoServerConfig
    except ImportError:
        # Fallback for Docker or direct script execution
        sys.path.append(os.path.dirname(__file__))
        from config import DemoServerConfig


class DemoMCPServer:
    """
    Demo MCP Server implementation using FastMCP.

    This demonstrates:
    1. Using standard config values from template.json config_schema
       - These are accessed via self.config_data (like hello_from, log_level)
       - Can be set via CLI: --config hello_from="Custom Name"
       - Or via env vars: MCP_HELLO_FROM="Custom Name"

    2. Using template data overrides via double underscore notation
       - These modify the template structure itself (like tools, capabilities)
       - Can be set via CLI: --tools__0__custom_field="value"
       - These allow overriding ANY part of template.json structure
    """

    def __init__(self, config_dict: dict = None):
        """Initialize the Demo MCP Server with configuration."""
        self.config = DemoServerConfig(config_dict=config_dict or {})

        # Standard configuration data from config_schema
        self.config_data = self.config.get_template_config()

        # Full template data (potentially modified by double underscore notation)
        self.template_data = self.config.get_template_data()

        self.logger = self.config.logger

        self.mcp = FastMCP(
            name=self.template_data.get("name", "demo-server"),
            instructions="Demo server showing config patterns",
            version=self.template_data.get("version", "1.0.0"),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=(
                int(
                    os.getenv(
                        "MCP_PORT",
                        self.template_data.get("transport", {}).get("port", 7071),
                    )
                )
                if not os.getenv("MCP_TRANSPORT") == "stdio"
                else None
            ),
        )
        logger.info("Demo MCP server %s created", self.mcp.name)
        self.register_tools()

    def register_tools(self):
        """Register tools with the MCP server."""
        self.mcp.tool(self.say_hello, tags=["greeting"])
        self.mcp.tool(self.get_server_info, tags=["info"])
        self.mcp.tool(self.echo_message, tags=["echo"])
        self.mcp.tool(self.demonstrate_overrides, tags=["demo"])
        logger.info("Tools registered with MCP server")

    def say_hello(self, name: str = "World") -> str:
        """
        Generate a personalized greeting message.

        PATTERN 1: Uses standard config from config_schema
        - hello_from: Set via --config hello_from="value" or MCP_HELLO_FROM env var

        PATTERN 2: Uses template data that can be overridden
        - Tool behavior can be modified via --tools__0__greeting_style="formal"

        Args:
            name: Name of the person to greet

        Returns:
            A personalized greeting message
        """

        logger.debug("Generating greeting for %s", name)
        # PATTERN 1: Standard config usage
        hello_from = self.config_data.get("hello_from", "Demo Server")

        # PATTERN 2: Template data override example
        # Check if this specific tool has been customized via double underscore
        tools = self.template_data.get("tools", [])
        say_hello_tool = next((t for t in tools if t.get("name") == "say_hello"), {})

        # Example overrides: --tools__0__greeting_style="formal"
        greeting_style = say_hello_tool.get("greeting_style", "casual")
        custom_prefix = say_hello_tool.get("custom_prefix", "")

        # Build greeting based on style
        if greeting_style == "formal":
            greeting = f"Good day, {name}. Greetings from {hello_from}."
        else:
            greeting = f"Hello {name}! Greetings from {hello_from}!"

        # Add custom prefix if set via template override
        if custom_prefix:
            greeting = f"{custom_prefix} {greeting}"

        return greeting

    def get_server_info(self) -> dict:
        """
        Get information about the demo server.

        Shows both standard config and template data that may be overridden.

        Returns:
            Dictionary containing server information
        """

        logger.debug("Fetching server info")
        return {
            # Template data (can be overridden via --name="Custom Name")
            "name": self.template_data.get("name", "Demo MCP Server"),
            "version": self.template_data.get("version", "1.0.0"),
            "description": self.template_data.get("description", "Demo MCP Server"),
            # Standard configuration from config_schema
            "standard_config": {
                "hello_from": self.config_data.get("hello_from"),
                "log_level": self.config_data.get("log_level"),
            },
            # Template structure info
            "tools": [tool.get("name") for tool in self.template_data.get("tools", [])],
            "tags": self.template_data.get("tags", []),
            # Show any custom fields added via double underscore
            "custom_fields": {
                k: v
                for k, v in self.template_data.items()
                if k
                not in [
                    "name",
                    "version",
                    "description",
                    "tools",
                    "tags",
                    "config_schema",
                ]
            },
        }

    def echo_message(self, message: str) -> str:
        """
        Echo back a message with server identification.

        Demonstrates template data override for tool behavior.

        Args:
            message: Message to echo back

        Returns:
            Echoed message with server identification
        """

        logger.debug("Echoing message: %s", message)
        # Use template data that can be overridden
        server_name = self.template_data.get("name", "Demo Server")

        # Check for tool-specific overrides
        tools = self.template_data.get("tools", [])
        echo_tool = next((t for t in tools if t.get("name") == "echo_message"), {})

        # Example override: --tools__2__echo_prefix="ECHO"
        echo_prefix = echo_tool.get("echo_prefix", "Echo from")

        return f"{echo_prefix} {server_name}: {message}"

    def demonstrate_overrides(self) -> dict:
        """
        Demonstrate the two configuration patterns.

        Returns:
            Examples of both configuration patterns
        """

        logger.debug("Demonstrating configuration overrides")
        return {
            "configuration_patterns": {
                "pattern_1_standard_config": {
                    "description": "Standard config from template.json config_schema",
                    "examples": [
                        "--config hello_from='Custom Server'",
                        "--config log_level=debug",
                        "MCP_HELLO_FROM='Custom Server' (env var)",
                    ],
                    "current_values": self.config_data,
                },
                "pattern_2_template_overrides": {
                    "description": "Template data overrides via double underscore notation",
                    "examples": [
                        "--name='Custom Server Name'",
                        "--description='Modified description'",
                        "--tools__0__greeting_style=formal",
                        "--tools__0__custom_prefix='Hey there!'",
                        "--tools__2__echo_prefix='RESPONSE'",
                        "--tags__0='custom-tag'",
                        "--custom_field='any custom value'",
                    ],
                    "current_template_data": self.template_data,
                },
            },
            "usage_guide": {
                "standard_config": "Use for values defined in config_schema - these have validation, defaults, and env var mapping",
                "template_overrides": "Use to modify ANY part of template structure - tools, capabilities, metadata, etc.",
            },
        }

    def run(self):
        """Run the MCP server with the configured transport and port."""
        self.mcp.run(
            transport=os.getenv(
                "MCP_TRANSPORT",
                self.template_data.get("transport", {}).get("default", "http"),
            ),
        )


# Create the server instance
server = DemoMCPServer(config_dict={})


@server.mcp.custom_route(path="/health", methods=["GET"])
async def health_check(request: Request):
    """
    Health check endpoint to verify server status.
    """

    return JSONResponse({"status": "healthy"})


if __name__ == "__main__":
    server.run()
