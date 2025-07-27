#!/usr/bin/env python3
"""
Base FastMCP class for consistent template implementation.

This module provides the BaseFastMCP class that extends FastMCP with
package-specific functionality for MCP server templates.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

logger = logging.getLogger(__name__)


class BaseFastMCP(FastMCP):
    """
    Base class that extends FastMCP with package-specific functionality.

    Provides common functionality including:
    - Enhanced tool introspection
    - Configuration management
    - Logging setup
    - Server information methods
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base FastMCP server.

        Args:
            name: Server name for identification
            config: Server configuration dictionary
        """
        if FastMCP is None:
            raise ImportError(
                "FastMCP is required but not installed. "
                "Install with: pip install fastmcp>=2.10.0"
            )

        # Initialize FastMCP
        super().__init__(name=name)

        self.config = config or {}
        logger.info("Initialized %s FastMCP server", name)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = self.config.get("log_level", "info").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    async def get_tool_names(self) -> List[str]:
        """
        Get list of available tool names.

        Uses FastMCP's native introspection capabilities.

        Returns:
            List of tool names
        """
        try:
            tools_dict = await self.get_tools()
            return list(tools_dict.keys())
        except Exception as e:
            logger.warning("Failed to get tools from FastMCP: %s", e)
            return []

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool to get info for

        Returns:
            Dictionary with tool information or None if not found
        """
        try:
            tools_dict = await self.get_tools()
            if tool_name in tools_dict:
                tool = tools_dict[tool_name]
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "enabled": tool.enabled,
                }
        except Exception as e:
            logger.warning("Failed to get tool info from FastMCP: %s", e)

        return None

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information including available tools.

        Returns:
            Dictionary containing server metadata
        """
        return {
            "name": self.name,
            "config": self.config,
            "tools": await self.get_tool_names(),
        }
