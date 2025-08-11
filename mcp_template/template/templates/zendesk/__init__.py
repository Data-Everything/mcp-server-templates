#!/usr/bin/env python3
"""
Zendesk MCP Server Package

A comprehensive Zendesk integration MCP server providing:
- Complete ticket management (CRUD operations)
- User and organization management
- Knowledge base article access
- Analytics and reporting capabilities
- Comment and note management
- Rate limiting and caching for optimal performance

This package uses FastMCP for modern MCP protocol implementation.
"""

from .config import ZendeskServerConfig
from .server import ZendeskMCPServer

__all__ = ["ZendeskMCPServer", "ZendeskServerConfig"]
__version__ = "1.0.0"
