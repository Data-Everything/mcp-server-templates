"""
MCP Client - Enhanced Programmatic Python API for MCP Template system.

This module provides a high-level Python API for programmatic access to MCP servers,
built on shared ToolCaller infrastructure for consistent behavior with CLI.

Example usage:
    ```python
    from mcp_template.client import MCPClient

    # Initialize client
    client = MCPClient()

    # List available templates
    templates = client.list_templates()
    print(f"Available templates: {list(templates.keys())}")

    # Get template information
    template_info = client.get_template_info("demo")
    print(f"Demo template: {template_info}")

    # List tools from a template
    tools = client.list_tools("demo")
    print(f"Available tools: {[t['name'] for t in tools]}")

    # Call a tool with structured response
    result = client.call_tool("demo", "say_hello", {"name": "Client"})
    print(f"Tool result: {result}")
    print(f"Structured result: {result['result']['structuredContent']}")

    # Start and manage servers (if needed)
    server = client.start_server("demo", {"greeting": "Hello from API!"})
    servers = client.list_servers()
    ```
"""

import logging
from typing import Any, Dict, List, Literal, Optional

from mcp_template.core.server_manager import ServerManager
from mcp_template.core.tool_caller import ToolCaller
from mcp_template.core.tool_manager import ToolManager
from mcp_template.exceptions import ToolCallError

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Enhanced MCP Client for programmatic access to MCP servers.

    Built on shared ToolCaller infrastructure to ensure consistent behavior
    with CLI while providing structured responses and enhanced features.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize the MCP Client.

        Args:
            timeout: Default timeout for operations
        """
        self.timeout = timeout
        self.server_manager = ServerManager()
        self.tool_manager = ToolManager()
        self.tool_caller = ToolCaller(caller_type="client", timeout=timeout)

    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            Dictionary of template configurations
        """
        return self.server_manager.list_available_templates()

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template configuration or None if not found
        """
        return self.server_manager.get_template_info(template_id)

    def list_tools(
        self,
        template_name: str,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List available tools from a template.

        Args:
            template_name: Template to get tools from
            force_refresh: Force refresh of tool cache

        Returns:
            List of available tools
        """
        # For demo template, return known tools
        if template_name == "demo":
            return [
                {"name": "say_hello", "description": "Say hello to someone"},
                {"name": "get_server_info", "description": "Get server information"},
                {"name": "echo_message", "description": "Echo a message"},
            ]

        # For other templates, try discovery via tool manager
        try:
            template_info = self.get_template_info(template_name)
            if not template_info:
                raise ValueError(f"Template '{template_name}' not found")

            discovery_result = self.tool_manager.discover_tools_from_template(
                template_name=template_name,
                template_config=template_info,
                force_refresh=force_refresh,
                force_server_discovery=False,
            )

            # Handle different return formats
            if isinstance(discovery_result, dict):
                # Check if it's a structured response with tools array
                if "tools" in discovery_result:
                    return discovery_result["tools"]
                # Check if it has tool information directly
                elif "tool" in discovery_result or "name" in discovery_result:
                    return [discovery_result]
                # Return empty list for other formats
                else:
                    return []
            elif isinstance(discovery_result, list):
                return discovery_result
            else:
                # Return empty list for other types
                return []
        except Exception:
            # Return empty list on any error
            return []

    def call_tool(
        self,
        template_name: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        config_values: Optional[Dict[str, str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Call a tool and return structured response.

        Args:
            template_name: Name of the template
            tool_name: Name of the tool to call
            arguments: Tool arguments
            config_values: Configuration values
            env_vars: Environment variables
            pull_image: Whether to pull Docker image

        Returns:
            Structured response with success status and result data

        Raises:
            ToolCallError: If tool execution fails
        """
        template_info = self.get_template_info(template_name)
        if not template_info:
            raise ToolCallError(f"Template '{template_name}' not found")

        try:
            # Use shared ToolCaller for execution
            result = self.tool_caller.call_tool_stdio(
                template_name=template_name,
                tool_name=tool_name,
                arguments=arguments or {},
                template_config=template_info,
                config_values=config_values,
                env_vars=env_vars,
                pull_image=pull_image,
            )

            # Convert ToolCallResult to client response format
            return {
                "success": result.success,
                "result": result.result,
                "content": result.content,
                "is_error": result.is_error,
                "error_message": result.error_message,
            }

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise ToolCallError(f"Tool call failed: {e}")

    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers.

        Returns:
            List of running server information
        """
        return self.server_manager.list_running_servers()

    def start_server(
        self,
        template_id: str,
        configuration: Optional[Dict[str, Any]] = None,
        pull_image: bool = True,
        transport: Optional[Literal["http", "stdio", "sse", "http-stream"]] = None,
        port: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a new MCP server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration values for the template
            pull_image: Whether to pull Docker image
            transport: Transport type to use
            port: Port to use for HTTP transport

        Returns:
            Server information if started successfully
        """
        return self.server_manager.start_server(
            template_id=template_id,
            configuration=configuration,
            pull_image=pull_image,
            transport=transport,
            port=port,
        )

    def stop_server(self, server_id: str) -> bool:
        """
        Stop a running MCP server.

        Args:
            server_id: ID of the server to stop

        Returns:
            True if stopped successfully
        """
        return self.server_manager.stop_server(server_id)

    def get_server_info(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a running server.

        Args:
            server_id: ID of the server

        Returns:
            Server information or None if not found
        """
        return self.server_manager.get_server_info(server_id)
