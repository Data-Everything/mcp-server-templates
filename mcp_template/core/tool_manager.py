"""
Tool management functionality for MCP Template system.

This module provides tool discovery and execution capabilities,
reusing existing tool discovery and calling infrastructure.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp_template.core.mcp_connection import MCPConnection
from mcp_template.core.server_manager import ServerManager
from mcp_template.exceptions import ToolCallError
from mcp_template.tools.discovery import ToolDiscovery
from mcp_template.tools.http_tool_caller import HTTPToolCaller
from mcp_template.utils.config_processor import ConfigProcessor

logger = logging.getLogger(__name__)


class ToolManager:
    """
    Manages tool discovery and execution for MCP servers.

    Provides a unified interface for tool operations,
    reusing existing discovery and calling infrastructure.
    """

    def __init__(self, timeout: int = 30, backend: Optional[str] = "docker"):
        """
        Initialize tool manager.

        Args:
            timeout: Timeout for tool operations
        """

        self.timeout = timeout
        self.backend = backend
        self.tool_discovery = ToolDiscovery(timeout=timeout)
        self.config_processor = ConfigProcessor()
        self.server_manager = ServerManager(backend_type=self.backend)
        self._tools_cache = {}

    async def discover_tools_from_server(
        self,
        server_command: List[str],
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Discover tools directly from a running MCP server.

        Args:
            server_command: Command to start the MCP server
            working_dir: Working directory for the server
            env_vars: Environment variables for the server

        Returns:
            List of tool definitions or None if failed

        # Currently, this method is not used in the MCP Template system.
        """
        connection = MCPConnection(timeout=self.timeout)
        try:
            # Connect to the server
            success = await connection.connect_stdio(
                command=server_command, working_dir=working_dir, env_vars=env_vars
            )

            if not success:
                logger.error("Failed to connect to MCP server")
                return None

            # List tools
            tools = await connection.list_tools()
            return tools

        finally:
            await connection.disconnect()

    def discover_tools_from_template(
        self,
        template_name: str,
        template_config: Dict[str, Any],
        force_refresh: bool = False,
        force_server_discovery: bool = False,
    ) -> Dict[str, Any]:
        """
        Discover tools from a template using existing discovery infrastructure.

        Args:
            template_name: Name of the template
            template_config: Template configuration
            force_refresh: Whether to force discovery even if cached
            force_server_discovery: Whether to force server-based discovery

        Returns:
            Dictionary containing discovered tools and metadata
        """

        tools = self.tool_discovery.discover_tools(
            template_name=template_name,
            template_config=template_config,
            force_refresh=force_refresh,
            force_server_discovery=force_server_discovery,
        )
        if tools:
            # Cache the discovery result
            self.cache_tools(template_name, tools)

        return tools

    async def call_tool_stdio(
        self,
        template: str,
        tool_name: str,
        params: Dict[str, Any] = None,
        env_vars: Optional[Dict[str, str]] = None,
        config_values: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        pull_image: bool = True,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
        *kwargs: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on an MCP server via stdio.

        Args:
            template: Template name
            tool_name: Name of the tool to call
            arguments: Tool arguments
            working_dir: Working directory for the server
            env_vars: Environment variables for the server
            config_values: Configuration values to apply
            config_file: Optional configuration file to use
            pull_image: Whether to pull the image if not found

        Returns:
            Tool response or None if failed
        """

        connection = MCPConnection(timeout=self.timeout)
        template_config = self.server_manager.get_template_info(
            template_id=template,
        )
        if not template_config:
            logger.error("Template '%s' not found", template)
            return None

        config_dict = self.server_manager.generate_run_config(
            template_data=template_config,
            transport="stdio",
            port=None,
            configuration=config_values,
            config_file=config_file,
            env_vars=env_vars,
            data_dir=data_dir,
            config_dir=config_dir,
        )

        config = config_dict.get("config", {})
        template_copy = config_dict.get("template", {})
        missing_properties = config_dict.get("missing_properties", [])
        if missing_properties:
            logger.error(
                "Missing required properties for %s: %s",
                template,
                missing_properties,
            )
            return None

        try:
            server_command = None
            working_dir = None
            # Connect to the server
            success = await connection.connect_stdio(
                command=server_command, working_dir=working_dir, env_vars=env_vars
            )

            if not success:
                logger.error("Failed to connect to MCP server")
                return None

            # Call the tool
            result = await connection.call_tool(tool_name, arguments=params)
            return result

        finally:
            await connection.disconnect()

    async def call_tool_http(
        self,
        server_url: str,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on an HTTP MCP server.

        Args:
            server_url: Base URL of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            session_id: Optional session ID for stateful calls

        Returns:
            Tool response or None if failed
        """
        async with HTTPToolCaller(timeout=self.timeout) as http_caller:
            return await http_caller.call_tool(
                server_url=server_url,
                tool_name=tool_name,
                arguments=arguments,
                session_id=session_id,
            )

    def list_discovered_tools(
        self, template_name: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get previously discovered tools for a template.

        Args:
            template_name: Name of the template

        Returns:
            List of tools or None if not cached
        """

        if template_name in self._tools_cache:
            discovery_result = self._tools_cache[template_name]
            return discovery_result.get("tools", [])
        return None

    def cache_tools(self, template_name: str, discovery_result: Dict[str, Any]) -> None:
        """
        Cache discovered tools for a template.

        Args:
            template_name: Name of the template
            discovery_result: Discovery result to cache
        """
        self._tools_cache[template_name] = discovery_result

    def clear_cache(self, template_name: Optional[str] = None) -> None:
        """
        Clear the tools cache.

        Args:
            template_name: Specific template to clear, or None to clear all
        """
        if template_name:
            self._tools_cache.pop(template_name, None)
        else:
            self._tools_cache.clear()
