#!/usr/bin/env python3
"""
Tools module for the Demo MCP Server.

This module defines the tools available in the demo template,
implementing them using FastMCP decorators and best practices.
"""

import json
import logging
from typing import Any, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

logger = logging.getLogger(__name__)


def register_tools(mcp, config: Any) -> None:
    """
    Register all demo tools with the MCP server.

    Args:
        mcp: FastMCP server instance
        config: Server configuration object
    """
    if FastMCP is None:
        raise ImportError("FastMCP is required for tool registration")

    logger.info("Registering demo tools")

    @mcp.tool()
    def say_hello(name: Optional[str] = None) -> str:
        """
        Generate a personalized greeting message.

        Args:
            name: Name of the person to greet (optional)

        Returns:
            A personalized greeting message
        """
        if name:
            greeting = f"Hello {name}! Greetings from {config.hello_from}!"
        else:
            greeting = f"Hello! Greetings from {config.hello_from}!"

        logger.debug("Generated greeting: %s", greeting)
        return greeting

    @mcp.tool()
    def get_server_info() -> str:
        """
        Get information about the demo MCP server.

        Returns:
            JSON string containing server information
        """
        server_info = {
            "name": "Demo Hello MCP Server",
            "version": "1.0.0",
            "description": "A simple demonstration MCP server that provides greeting tools",
            "hello_from": config.hello_from,
            "log_level": config.log_level,
            "capabilities": ["Greeting Tools", "Server Information"],
            "tools": [
                {
                    "name": "say_hello",
                    "description": "Generate a personalized greeting message",
                    "parameters": ["name (optional)"],
                },
                {
                    "name": "get_server_info",
                    "description": "Get information about the demo MCP server",
                    "parameters": [],
                },
                {
                    "name": "echo_message",
                    "description": "Echo back a message with server identification",
                    "parameters": ["message (required)"],
                },
            ],
        }

        logger.debug("Returning server info")
        return json.dumps(server_info, indent=2)

    @mcp.tool()
    def echo_message(message: str) -> str:
        """
        Echo back a message with server identification.

        Args:
            message: Message to echo back

        Returns:
            Echoed message with server identification
        """
        echoed = f"[{config.hello_from}] Echo: {message}"
        logger.debug("Echoing message: %s", echoed)
        return echoed

    logger.info("Successfully registered %d demo tools", 3)
