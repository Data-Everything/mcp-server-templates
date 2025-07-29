"""
FastMCP server implementation.
"""

from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from mcp_template.servers.base import BaseMCP


class BaseFastMCP(FastMCP, BaseMCP):
    """
    Base class that extends FastMCP with package-specific functionality.
    Also extends BaseMCP for consistent template implementation.

    Provides common functionality including:
    - Enhanced tool introspection
    - Configuration management
    - Logging setup
    - Server information methods
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None, **kwargs):
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
        BaseMCP.__init__(self, name=name, config=config)
        super().__init__(name=name, **kwargs)
        self.logger.info("Initialized %s FastMCP server", name)

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
            self.logger.warning("Failed to get tools from FastMCP: %s", e)
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
            self.logger.warning("Failed to get tool info from FastMCP: %s", e)

        return None
