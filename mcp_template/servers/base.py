#!/usr/bin/env python3
"""
Base FastMCP class for consistent template implementation.

This module provides the BaseFastMCP class that extends FastMCP with
package-specific functionality for MCP server templates.
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseMCP:
    """
    Base class for MCP server templates. Its sort of a mixin which
    provides common functionality including:
    - Enhanced tool introspection
    - Configuration management
    - Logging setup
    - Server information methods

    This class will most likely be the second inheritance in the
    server implementation, after FastMCP or any other base class.
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base MCP server.

        Args:
            name: Server name for identification
            config: Server configuration dictionary
        """

        self._name = name
        self.config = config or {}
        # Setup logging
        self._setup_logging()
        self.logger = logger
        self.logger.info("Initialized %s MCP server", name)

    def _setup_logging(self) -> None:
        """Setup logging configuration."""

        log_level = self.config.get("log_level", "info").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @property
    def name(self) -> str:
        """
        Get the server name.
        """
        # If a parent class defines a property, use it
        # Otherwise, use our own _name
        return getattr(super(), "name", self._name)

    @name.setter
    def name(self, value: str):
        """Set the server name. This is a setter for the name property."""

        self._name = value

    @abstractmethod
    async def get_tool_names(self) -> List[str]:
        """
        Get list of available tool names.

        Uses FastMCP's native introspection capabilities.

        Returns:
            List of tool names

        """

        return []

    @abstractmethod
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific tool.

        Args:
            tool_name: Name of the tool to get info for

        Returns:
            Dictionary with tool information or None if not found
        """

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
