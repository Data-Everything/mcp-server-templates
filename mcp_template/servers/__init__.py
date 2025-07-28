"""
Initialization module for MCP server templates.
"""

from mcp_template.servers.base import BaseMCP
from mcp_template.servers.fastmcp import BaseFastMCP

__all__ = ["BaseMCP", "BaseFastMCP"]
