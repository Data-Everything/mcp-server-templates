"""
Core shared modules for MCP Template system.

This module contains shared functionality used by both CLI and Client components:
- MCP Server connection and protocol handling
- Tool discovery and management
- Server lifecycle management
- Common data structures and utilities

These modules enable code reuse between the CLI interface and the programmatic Client API.
"""

from .mcp_connection import MCPConnection
from .server_manager import ServerManager
from .tool_caller import ToolCaller
from .tool_manager import ToolManager

__all__ = ["MCPConnection", "ServerManager", "ToolCaller", "ToolManager"]
