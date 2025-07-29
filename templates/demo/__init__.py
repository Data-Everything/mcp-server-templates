#!/usr/bin/env python3
"""
Demo MCP Server Template.

A simple demonstration MCP server that provides greeting tools
and server information using FastMCP and the MCP Platform architecture.
"""

from .config import DemoServerConfig
from .server import DemoMCPServer

__version__ = "1.0.0"
__all__ = ["DemoMCPServer", "DemoServerConfig"]
