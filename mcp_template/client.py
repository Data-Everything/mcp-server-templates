"""
MCP Client - Programmatic Python API for MCP Template system.

This module provides a high-level Python API for programmatic access to MCP servers,
using the refactored common modules for consistent functionality.

Example usage:
    ```python
    import asyncio
    from mcp_template.client import MCPClient

    async def main():
        client = MCPClient()

        # List available templates
        templates = client.list_templates()
        print(f"Available templates: {list(templates.keys())}")

        # Start a server
        server = await client.start_server("demo", {"greeting": "Hello from API!"})

        # List tools
        tools = await client.list_tools("demo")
        print(f"Available tools: {[t['name'] for t in tools]}")

        # Call a tool
        result = await client.call_tool("demo", "echo", {"message": "Hello World"})
        print(f"Tool result: {result}")

        # List running servers
        servers = client.list_servers()
        print(f"Running servers: {len(servers)}")

    asyncio.run(main())
    ```
"""

import asyncio
import logging
from typing import Any, Dict, List, Literal, Optional

from mcp_template.core import MCPConnection, ServerManager, ToolCaller, ToolManager
from mcp_template.template.utils.discovery import TemplateDiscovery

# Import CoreMCPClient for improved functionality
from mcp_template.core.core_client import CoreMCPClient

logger = logging.getLogger(__name__)


class MCPClient:
    """
    High-level MCP Client for programmatic access to MCP servers.

    This client provides a simplified interface for common MCP operations:
    - Connecting to MCP servers
    - Listing and calling tools
    - Managing server instances
    - Template discovery

    Uses RefactoredMCPClient internally for common module functionality.
    """

    def __init__(self, backend_type: str = "docker", timeout: int = 30):
        """
        Initialize MCP Client.

        Args:
            backend_type: Deployment backend (docker, kubernetes, mock)
            timeout: Default timeout for operations in seconds
        """
        self.backend_type = backend_type
        self.timeout = timeout

        # Use CoreMCPClient for all functionality
        self._core_client = CoreMCPClient(backend_type)

        # Store configuration
        self.timeout = timeout

    # Template Management
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.

        Returns:
            Dictionary mapping template_id to template information
        """
        return self._core_client.list_templates()

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template information or None if not found
        """
        return self._core_client.get_template_info(template_id)

    # Server Management
    def list_servers(self) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers.

        Returns:
            List of running server information
        """
        return self._core_client.list_servers()

    def list_servers_by_template(self, template: str) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers for a specific template.

        Args:
            template: Template name to filter servers by

        Returns:
            List of running server information for the specified template
        """
        return self._core_client.list_servers(template_name=template)

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
            configuration: Configuration for the server
            pull_image: Whether to pull the latest image
            transport: Optional transport type (e.g., "http", "stdio")
            port: Optional port for HTTP transport

        Returns:
            Server deployment information or None if failed
        """
        return self._core_client.start_server(
            template_id, configuration, pull_image, transport, port
        )
        return self.server_manager.start_server(
            template_id=template_id,
            configuration=configuration,
            pull_image=pull_image,
            transport=transport,
            port=port,
        )

    def stop_server(self, deployment_id: str) -> Dict[str, Any]:
        """Stop a running server.

        Args:
            deployment_id: Unique identifier for the deployment

        Returns:
            Result of the stop operation
        """

        # Disconnect any active connections first
        if deployment_id in self._active_connections:
            # Don't create task if no event loop is running
            try:
                asyncio.get_running_loop()
                # Store task to prevent garbage collection
                task = asyncio.create_task(
                    self._active_connections[deployment_id].disconnect()
                )
                # Store the task in a background set
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except RuntimeError:
                # No event loop running, just remove the connection
                pass
            del self._active_connections[deployment_id]

        return self.server_manager.stop_server(deployment_id)

    def stop_all_servers(self, template: str = None) -> bool:
        """
        Stop all servers for a specific template.

        Args:
            template: Template name to stop all servers. If None, stops all servers.

        Returns:
            True if all servers were stopped successfully, False otherwise
        """

        deployments = self.server_manager.list_running_servers(template=template)
        results = []

        for deployment in deployments:
            if deployment.get("template") == template:
                result = self.stop_server(deployment["id"])
                results.append(result)

        return all(results)

    def get_server_info(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server deployment.

        Args:
            deployment_id: ID of the deployment

        Returns:
            Server information or None if not found
        """

        return self.server_manager.get_server_info(deployment_id)

    def get_server_logs(self, deployment_id: str, lines: int = 100) -> Optional[str]:
        """
        Get logs from a running server.

        Args:
            deployment_id: ID of the deployment
            lines: Number of log lines to retrieve

        Returns:
            Log content or None if failed
        """

        return self.server_manager.get_server_logs(deployment_id, lines)

    # Tool Discovery and Management
    def list_tools(
        self,
        template_name: Optional[str] = None,
        force_refresh: bool = False,
        force_server_discovery: bool = False,
    ) -> Dict[str, Any]:
        """
        List available tools from a template or all discovered tools.

        Args:
            template_name: Specific template to get tools from
            force_refresh: Force refresh of tool cache
            force_server_discovery: Force discovery from server if available

        Returns:
            Dictionary of tools with their descriptions
        """
        if force_refresh:
            self.tool_manager.clear_cache(template_name=template_name)

        if template_name:
            # Get tools for a specific template
            template_info = self.get_template_info(template_name)
            if not template_info:
                raise ValueError(f"Template '{template_name}' not found")

            return self.tool_manager.discover_tools_from_template(
                template_name=template_name,
                template_config=template_info,
                force_refresh=force_refresh,
                force_server_discovery=force_server_discovery,
            )
        else:
            # Return all discovered tools
            return self.tool_manager.list_discovered_tools(template_name=template_name)

    def call_tool(
        self,
        template_id: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        deployment_id: Optional[str] = None,
        server_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on an MCP server.

        This method supports both stdio and HTTP transports, automatically
        determining the best approach based on deployment status and template configuration.

        Args:
            template_id: Template that provides the tool
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            deployment_id: Existing deployment to use (optional)
            server_config: Configuration for server if starting new instance

        Returns:
            Tool response or None if failed
        """
        # Get template configuration
        template_info = self.get_template_info(template_id)
        if not template_info:
            logger.error("Template %s not found", template_id)
            return None

        # If deployment_id is provided, try to use running server
        if deployment_id:
            server_info = self.get_server_info(deployment_id)
            if server_info:
                # Try HTTP call first if the server supports it
                transport = server_info.get("transport", {})
                if transport.get("default") == "http" or "http" in transport.get(
                    "supported", []
                ):
                    server_url = f"http://localhost:{transport.get('port', 8080)}"
                    try:
                        return self.tool_caller.call_tool_http(
                            server_url=server_url,
                            tool_name=tool_name,
                            arguments=arguments,
                        )
                    except Exception as e:
                        logger.warning(
                            "HTTP tool call failed, falling back to stdio: %s", e
                        )

        # Use stdio approach (default)
        try:
            return self.tool_caller.call_tool_stdio(
                template_name=template_id,
                tool_name=tool_name,
                arguments=arguments,
                template_config=template_info,
                config_values=server_config or {},
            )
        except Exception as e:
            logger.error(
                "Failed to call tool %s on template %s: %s", tool_name, template_id, e
            )
            return None

    # Direct Connection Methods
    async def connect_stdio(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        connection_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a direct stdio connection to an MCP server.

        Args:
            command: Command to execute MCP server
            working_dir: Working directory for the process
            env_vars: Environment variables for the process
            connection_id: Optional ID for the connection (auto-generated if None)

        Returns:
            Connection ID if successful, None if failed
        """
        if connection_id is None:
            connection_id = f"stdio_{len(self._active_connections)}"

        connection = MCPConnection(timeout=self.timeout)
        success = await connection.connect_stdio(
            command=command, working_dir=working_dir, env_vars=env_vars
        )

        if success:
            self._active_connections[connection_id] = connection
            return connection_id
        else:
            await connection.disconnect()
            return None

    async def list_tools_from_connection(
        self, connection_id: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        List tools from an active connection.

        Args:
            connection_id: ID of the connection

        Returns:
            List of tool definitions or None if failed
        """
        if connection_id not in self._active_connections:
            logger.error("Connection %s not found", connection_id)
            return None

        connection = self._active_connections[connection_id]
        return await connection.list_tools()

    async def call_tool_from_connection(
        self, connection_id: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool using an active connection.

        Args:
            connection_id: ID of the connection
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response or None if failed
        """
        if connection_id not in self._active_connections:
            logger.error("Connection %s not found", connection_id)
            return None

        connection = self._active_connections[connection_id]
        return await connection.call_tool(tool_name, arguments)

    async def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect from an active connection.

        Args:
            connection_id: ID of the connection to disconnect

        Returns:
            True if disconnected successfully, False if connection not found
        """
        if connection_id not in self._active_connections:
            return False

        connection = self._active_connections[connection_id]
        await connection.disconnect()
        del self._active_connections[connection_id]
        return True

    # Cleanup
    async def cleanup(self) -> None:
        """Clean up all active connections and resources."""
        # Create a copy of keys to avoid modifying dict during iteration
        connection_ids = list(self._active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
