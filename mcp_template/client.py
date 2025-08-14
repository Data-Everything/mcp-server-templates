"""
MCP Client - Programmatic Python API for MCP Template system.

This module provides a high-level Python API for programmatic access to MCP servers,
using the refactored core modules for consistent functionality.

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
        server = client.start_server("demo", {"greeting": "Hello from API!"})

        # List tools
        tools = client.list_tools("demo")
        print(f"Available tools: {[t['name'] for t in tools]}")

        # Call a tool
        result = client.call_tool("demo", "echo", {"message": "Hello World"})
        print(f"Tool result: {result}")

        # List running servers
        servers = client.list_servers()
        print(f"Running servers: {len(servers)}")

    asyncio.run(main())
    ```
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
import weakref

from mcp_template.core import (
    TemplateManager,
    DeploymentManager,
    ConfigManager,
    ToolManager,
    MCPConnection,
    ServerManager,
    ToolCaller,
)
from mcp_template.core.deployment_manager import DeploymentOptions
from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Unified MCP Client for programmatic access to MCP servers.

    This client provides a simplified interface for common MCP operations:
    - Connecting to MCP servers
    - Listing and calling tools
    - Managing server instances
    - Template discovery

    Consolidates functionality from both MCPClient and CoreMCPClient for simplicity.
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

        # Initialize core managers
        self.template_manager = TemplateManager(backend_type)
        self.deployment_manager = DeploymentManager(backend_type)
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager(backend_type)

        # Connection management for direct MCP connections
        self._active_connections = {}
        self._background_tasks = set()

        # Initialize other components
        self.template_discovery = TemplateDiscovery()
        self.server_manager = ServerManager(backend_type)
        self.tool_caller = ToolCaller(backend_type)

    # Template Management
    def list_templates(
        self, include_deployed_status: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.

        Args:
            include_deployed_status: Whether to include deployment status

        Returns:
            Dictionary mapping template_id to template information
        """
        try:
            return self.template_manager.list_templates(
                include_deployed_status=include_deployed_status
            )
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return {}

    def get_template_info(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Template information or None if not found
        """
        try:
            return self.template_manager.get_template_info(template_id)
        except Exception as e:
            logger.error(f"Failed to get template info for {template_id}: {e}")
            return None

    def validate_template(self, template_id: str) -> bool:
        """
        Validate that a template exists and is properly structured.

        Args:
            template_id: The template identifier

        Returns:
            True if template is valid, False otherwise
        """
        try:
            return self.template_manager.validate_template(template_id)
        except Exception as e:
            logger.error(f"Failed to validate template {template_id}: {e}")
            return False

    def search_templates(self, query: str) -> Dict[str, Dict[str, Any]]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query string

        Returns:
            Dictionary of matching templates
        """
        try:
            return self.template_manager.search_templates(query)
        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return {}

    # Server Management
    def list_servers(self, template_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers.

        Args:
            template_name: Optional filter by template name

        Returns:
            List of running server information
        """
        try:
            return self.deployment_manager.find_deployments_by_criteria(
                template_name=template_name
            )
        except Exception as e:
            logger.error(f"Failed to list servers: {e}")
            return []

    def list_servers_by_template(self, template: str) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers for a specific template.

        Args:
            template: Template name to filter servers by

        Returns:
            List of running server information for the specified template
        """
        return self.list_servers(template_name=template)

    def start_server(
        self,
        template_id: str,
        configuration: Optional[Dict[str, Any]] = None,
        pull_image: bool = True,
        transport: Optional[str] = None,
        port: Optional[int] = None,
        name: Optional[str] = None,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a new MCP server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration for the server
            pull_image: Whether to pull the latest image
            transport: Optional transport type (e.g., "http", "stdio")
            port: Optional port for HTTP transport
            name: Custom deployment name
            timeout: Deployment timeout

        Returns:
            Server deployment information or None if failed
        """
        try:
            config_sources = {"config_values": configuration or {}}

            deployment_options = DeploymentOptions(
                name=name,
                transport=transport,
                port=port or 7071,
                pull_image=pull_image,
                timeout=timeout,
            )

            result = self.deployment_manager.deploy_template(
                template_id, config_sources, deployment_options
            )

            return result.to_dict() if result.success else None

        except Exception as e:
            logger.error(f"Failed to start server for {template_id}: {e}")
            return None

    def stop_server(self, deployment_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Stop a running server.

        Args:
            deployment_id: Unique identifier for the deployment
            timeout: Timeout for graceful shutdown

        Returns:
            Result of the stop operation
        """
        try:
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

            return self.deployment_manager.stop_deployment(deployment_id, timeout)
        except Exception as e:
            logger.error(f"Failed to stop server {deployment_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_all_servers(self, template: str = None) -> bool:
        """
        Stop all servers for a specific template.

        Args:
            template: Template name to stop all servers. If None, stops all servers.

        Returns:
            True if all servers were stopped successfully, False otherwise
        """
        try:
            targets = self.deployment_manager.find_deployments_by_criteria(
                template_name=template
            )

            if not targets:
                return True  # No servers to stop is considered success

            result = self.deployment_manager.stop_deployments_bulk(
                [t["id"] for t in targets]
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"Failed to stop all servers for template {template}: {e}")
            return False

    def get_server_info(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific server deployment.

        Args:
            deployment_id: ID of the deployment

        Returns:
            Server information or None if not found
        """
        try:
            deployments = self.deployment_manager.find_deployments_by_criteria(
                deployment_id=deployment_id
            )
            return deployments[0] if deployments else None
        except Exception as e:
            logger.error(f"Failed to get server info for {deployment_id}: {e}")
            return None

    def get_server_logs(
        self, deployment_id: str, lines: int = 100, follow: bool = False
    ) -> Optional[str]:
        """
        Get logs from a running server.

        Args:
            deployment_id: ID of the deployment
            lines: Number of log lines to retrieve
            follow: Whether to stream logs in real-time

        Returns:
            Log content or None if failed
        """
        try:
            result = self.deployment_manager.get_deployment_logs(
                deployment_id, lines=lines, follow=follow
            )
            return result.get("logs") if result.get("success") else None
        except Exception as e:
            logger.error(f"Failed to get server logs for {deployment_id}: {e}")
            return None

    # Tool Discovery and Management
    def list_tools(
        self,
        template_name: Optional[str] = None,
        force_refresh: bool = False,
        force_server_discovery: bool = False,
        discovery_method: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        List available tools from a template or all discovered tools.

        Args:
            template_name: Specific template to get tools from
            force_refresh: Force refresh of tool cache
            force_server_discovery: Force discovery from server if available
            discovery_method: How to discover tools (static, dynamic, image, auto)

        Returns:
            List of tools with their descriptions
        """
        try:
            if force_refresh:
                self.tool_manager.clear_cache(template_name=template_name)

            return self.tool_manager.list_tools(
                template_name or "",
                discovery_method=discovery_method,
                force_refresh=force_refresh,
            )
        except Exception as e:
            logger.error(f"Failed to list tools for {template_name}: {e}")
            return []

    def call_tool(
        self,
        template_id: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        deployment_id: Optional[str] = None,
        server_config: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
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
            timeout: Timeout for the call

        Returns:
            Tool response or None if failed
        """
        try:
            return self.tool_manager.call_tool(
                template_id, tool_name, arguments or {}, timeout
            )
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
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

    # Async versions of main methods
    async def start_server_async(
        self,
        template_id: str,
        configuration: Optional[Dict[str, Any]] = None,
        pull_image: bool = True,
        transport: Optional[str] = None,
        port: Optional[int] = None,
        name: Optional[str] = None,
        timeout: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Async version of start_server."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.start_server,
            template_id,
            configuration,
            pull_image,
            transport,
            port,
            name,
            timeout,
        )

    async def list_tools_async(
        self,
        template_name: Optional[str] = None,
        force_refresh: bool = False,
        discovery_method: str = "auto",
    ) -> List[Dict[str, Any]]:
        """Async version of list_tools."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.list_tools, template_name, force_refresh, False, discovery_method
        )

    async def call_tool_async(
        self,
        template_id: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        timeout: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """Async version of call_tool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.call_tool, template_id, tool_name, arguments, None, None, timeout
        )

    # Utility methods
    def clear_caches(self) -> None:
        """Clear all internal caches."""
        try:
            self.template_manager.refresh_cache()
            self.tool_manager.clear_cache()
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")

    def get_backend_type(self) -> str:
        """Get the backend type being used."""
        return self.backend_type

    def set_backend_type(self, backend_type: str) -> None:
        """
        Change the backend type (reinitializes all managers).

        Args:
            backend_type: New backend type (docker, kubernetes, mock)
        """
        try:
            self.backend_type = backend_type
            self.template_manager = TemplateManager(backend_type)
            self.deployment_manager = DeploymentManager(backend_type)
            self.tool_manager = ToolManager(backend_type)
            self.server_manager = ServerManager(backend_type)
            self.tool_caller = ToolCaller(backend_type)
        except Exception as e:
            logger.error(f"Failed to set backend type to {backend_type}: {e}")
            raise

    # Cleanup methods
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


# Legacy compatibility - some methods for backward compatibility
class CoreMCPClient(MCPClient):
    """Legacy alias for backward compatibility."""

    def __init__(self, backend_type: str = "docker"):
        super().__init__(backend_type=backend_type)
