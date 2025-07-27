#!/usr/bin/env python3
"""
Base MCP Server class for consistent template implementation.

This module provides the BaseMCPServer class that all MCP server templates
should inherit from to ensure consistency and shared functionality.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

try:
    from fastmcp import FastMCP
except ImportError:
    FastMCP = None

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """
    Base class for all MCP server templates.

    Provides common functionality including:
    - FastMCP integration
    - Configuration management
    - Transport handling (HTTP/stdio)
    - Logging setup
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base MCP server.

        Args:
            name: Server name for identification
            config: Server configuration dictionary
        """
        self.name = name
        self.config = config or {}

        # Setup logging
        self._setup_logging()

        # Initialize FastMCP if available
        if FastMCP is None:
            raise ImportError(
                "FastMCP is required but not installed. "
                "Install with: pip install fastmcp>=2.10.0"
            )

        self.mcp = FastMCP(name=name)
        logger.info("Initialized %s MCP server", name)

        # Register tools (implemented by subclasses)
        self.register_tools()

    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = self.config.get("log_level", "info").upper()
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @abstractmethod
    def register_tools(self) -> None:
        """
        Register tools with the MCP server.

        This method must be implemented by subclasses to define
        the specific tools available for the template.
        """

    def run(
        self, transport: str = "http", host: str = "0.0.0.0", port: int = 7071, **kwargs
    ) -> None:
        """
        Run the MCP server.

        Args:
            transport: Transport type ("http" or "stdio")
            host: Host to bind to (for HTTP transport)
            port: Port to bind to (for HTTP transport)
            **kwargs: Additional arguments passed to FastMCP run
        """
        logger.info(
            "Starting %s server on %s://%s:%d", self.name, transport, host, port
        )

        try:
            if transport == "http":
                self.mcp.run(transport="http", host=host, port=port, **kwargs)
            elif transport == "stdio":
                self.mcp.run(transport="stdio", **kwargs)
            else:
                raise ValueError(f"Unsupported transport: {transport}")
        except Exception as e:
            logger.error("Failed to start server: %s", e)
            raise

    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information.

        Returns:
            Dictionary containing server metadata
        """
        return {
            "name": self.name,
            "config": self.config,
            "tools": [tool for tool in dir(self.mcp) if not tool.startswith("_")],
        }
