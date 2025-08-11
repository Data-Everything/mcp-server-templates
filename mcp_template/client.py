"""
MCP Client - Programmatic Python API for MCP Template system.

This module provides a high-level Python API for programmatic access to MCP servers,
reusing existing CLI infrastructure while providing a clean client interface.

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

from mcp_template.core import MCPConnection, ServerManager, ToolManager
from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class MCPClient:
    """
    High-level MCP Client for programmatic access to MCP servers.

    This client provides a simplified interface for common MCP operations:
    - Connecting to MCP servers
    - Listing and calling tools
    - Managing server instances
    - Template discovery
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

        # Initialize managers
        self.server_manager = ServerManager(backend_type)
        self.tool_manager = ToolManager(timeout)
        self.template_discovery = TemplateDiscovery()

        # Track active connections for cleanup
        self._active_connections: Dict[str, MCPConnection] = {}
        self._background_tasks: set = set()  # Track background tasks

    # Template Management
    def list_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.

        Returns:
            Dictionary mapping template_id to template information
        """
        return self.server_manager.list_available_templates()

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template information or None if not found
        """
        return self.server_manager.get_template_info(template_id)

    # Server Management
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
            configuration: Configuration for the server
            pull_image: Whether to pull the latest image
            transport: Optional transport type (e.g., "http", "stdio")
            port: Optional port for HTTP transport

        Returns:
            Server deployment information or None if failed
        """
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
        self, template_name: Optional[str] = None, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        List available tools from a template or all discovered tools.

        Args:
            template_name: Specific template to get tools from
            force_refresh: Force refresh of tool cache

        Returns:
            Dictionary of tools with their descriptions
        """

        if template_name:
            # Get tools for a specific template
            template_info = self.get_template_info(template_name)
            if not template_info:
                raise ValueError(f"Template '{template_name}' not found")

            return self.tool_manager.discover_tools_from_template(
                template_info,
                force_refresh,
                template_config=template_info,  # Vibe coder did not even add this. I added it to remove warning. But its wrong i think.
            )
        else:
            # Return all discovered tools
            return self.tool_manager.list_discovered_tools(template_name=template_name)

    async def call_tool(
        self,
        template_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        deployment_id: Optional[str] = None,
        server_config: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on an MCP server.

        Args:
            template_id: Template that provides the tool
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            deployment_id: Existing deployment to use (optional)
            server_config: Configuration for server if starting new instance

        Returns:
            Tool response or None if failed
        """
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
                    return await self.tool_manager.call_tool_http(
                        server_url=server_url, tool_name=tool_name, arguments=arguments
                    )

        # Fall back to stdio call with template
        template_info = self.get_template_info(template_id)
        if not template_info:
            logger.error("Template %s not found", template_id)
            return None

        # Build command for stdio execution
        from mcp_template.deployer import MCPDeployer

        deployer = MCPDeployer()

        try:
            # Prepare configuration
            config = server_config or {}

            # Get stdio command from deployer
            command_info = deployer.build_stdio_command(
                template_id=template_id, config=config, template_data=template_info
            )

            if not command_info.get("success"):
                logger.error(
                    "Failed to build stdio command: %s", command_info.get("error")
                )
                return None

            # Call tool via stdio
            return await self.tool_manager.call_tool_stdio(
                server_command=command_info["command"],
                tool_name=tool_name,
                arguments=arguments,
                working_dir=command_info.get("working_dir"),
                env_vars=command_info.get("env_vars"),
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
