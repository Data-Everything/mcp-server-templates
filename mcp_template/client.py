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
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

from mcp_template.backends import available_valid_backends
from mcp_template.core import (
    DeploymentManager,
    MCPConnection,
    TemplateManager,
    ToolCaller,
    ToolManager,
)
from mcp_template.core.deployment_manager import DeploymentOptions
from mcp_template.core.multi_backend_manager import MultiBackendManager
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
        self.tool_manager = ToolManager(backend_type)

        # Connection management for direct MCP connections
        self._active_connections = {}
        self._background_tasks = set()

        # Initialize other components
        self.template_discovery = TemplateDiscovery()
        self.tool_caller = ToolCaller(backend_type)
        self.multi_manager = MultiBackendManager(self.backend_type)

        # This is a temp MultiBackendManager which is set by methods that
        # also accept backend as input and set the value scoped for that method
        self._multi_manager = None

    # Template Management
    def list_templates(
        self,
        include_deployed_status: bool = False,
        all_backends: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.

        Args:
            include_deployed_status: Whether to include deployment status
            all_backends: False

        Returns:
            Dictionary mapping template_id to template information
        """

        if all_backends:
            # Overwrite self.multi_manager to use all backends
            self._multi_manager = MultiBackendManager(enabled_backends=None)
        else:
            self._multi_manager = self.multi_manager

        available_backends = self._multi_manager.get_available_backends()

        # Get templates (backend-agnostic)
        template_manager = TemplateManager(
            available_backends[0]
        )  # Use any backend for template listing

        templates = template_manager.list_templates(include_deployed_status=False)
        # Get all deployments across backends
        if include_deployed_status:
            all_deployments = self._multi_manager.get_all_deployments()

            # Count running instances per template per backend
            deployment_info = {}
            for deployment in all_deployments:
                if deployment.get("status") == "running":
                    template_name = deployment.get("template", "unknown")
                    backend_type = deployment.get("backend_type", "unknown")
                    deployment_id = deployment.get(
                        "id", deployment.get("deployment_id", None)
                    )

                    if template_name not in deployment_info:
                        deployment_info[template_name] = {}
                    if backend_type not in deployment_info[template_name]:
                        deployment_info[template_name][backend_type] = {
                            "count": 0,
                            "deployment_ids": [],
                        }
                    deployment_info[template_name][backend_type]["count"] += 1
                    if deployment_id:
                        deployment_info[template_name][backend_type][
                            "deployment_ids"
                        ].append(deployment_id)

            for template_name, template_info in templates.items():
                template_info["deployments"] = deployment_info.get(template_name, {})
                templates[template_name] = template_info

        return templates

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
    def list_servers(
        self,
        template_name: Optional[str] = None,
        all_backends: bool = False,
        status: str = None,
    ) -> List[Dict[str, Any]]:
        """
        List all currently running MCP servers.

        Args:
            template_name: Optional filter by template name
            all_backends: All backend

        Returns:
            List of running server information
        """
        if all_backends:
            self._multi_manager = MultiBackendManager(enabled_backends=None)
        else:
            self._multi_manager = self.multi_manager

        try:
            all_deployments = self._multi_manager.get_all_deployments(
                template_name=template_name, status=status
            )
            return all_deployments
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
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        overrides: Optional[Dict[str, str]] = None,
        volumes: Optional[Union[Dict[str, str], List[str]]] = None,
        pull_image: bool = True,
        transport: Optional[str] = "http",
        host: Optional[str] = "0.0.0.0",
        port: Optional[int] = None,
        name: Optional[str] = None,
        timeout: int = 300,
        backend_config: Optional[Dict[str, Any]] = None,
        backend_config_file: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Start a new MCP server instance.

        Args:
            template_id: Template to deploy
            configuration: Configuration key-value pairs
            config_file: Path to configuration file
            env_vars: Environment variables (highest precedence)
            overrides: Template overrides values
            volumes: Volume mounts as {host_path: container_path}
            pull_image: Whether to pull the latest image
            transport: Optional transport type (e.g., "http", "stdio")
            host: Optional host
            port: Optional port for HTTP transport
            name: Custom deployment name
            timeout: Deployment timeout
            backend_config: Backend specific config
            backend_config_file: Backend config file

        Returns:
            Server deployment information or None if failed
        """

        if backend_config or backend_config_file:
            raise ValueError("Backend config support to be added in future")

        try:

            if not configuration:
                configuration = {}

            if host:
                configuration["MCP_HOST"] = host

            if transport:
                configuration["MCP_TRANSPORT"] = transport

            if port:
                configuration["MCP_PORT"] = str(port)

            # Structure config sources for deployment manager
            config_sources = {
                "config_file": config_file or None,
                "env_vars": env_vars if env_vars else None,
                "config_values": configuration,
                "override_values": overrides if overrides else None,
                "volume_config": volumes if volumes else None,
                "backend_config": backend_config if backend_config else None,
                "backend_config_file": backend_config_file,
            }

            # Handle volumes
            if volumes:
                if not config_sources.get("config_values"):
                    config_sources["config_values"] = {}

                # Process volumes: convert list to dict if needed
                if isinstance(volumes, list):
                    processed_volumes = {path: path for path in volumes}
                else:
                    processed_volumes = volumes

                config_sources["config_values"]["VOLUMES"] = processed_volumes

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

    def deploy_template(
        self,
        template_id: str,
        config_file: Optional[str] = None,
        config: Optional[Dict[str, str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        overrides: Optional[Dict[str, str]] = None,
        volumes: Optional[Union[Dict[str, str], List[str]]] = None,
        transport: Optional[str] = None,
        pull_image: bool = True,
        name: Optional[str] = None,
        timeout: int = 300,
        host: str = "0.0.0.0",
        port: int = None,
        backend_config: Optional[Dict[str, Any]] = None,
        backend_config_file: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Deploy a template with CLI-like interface supporting config precedence and volumes.

        Args:
            template_id: Template to deploy
            config_file: Path to configuration file
            config: Configuration key=value pairs
            env_vars: Environment variables (highest precedence)
            volumes: Volume mounts - dict {host_path: container_path} or list of paths
            transport: Transport protocol (http, stdio)
            pull_image: Whether to pull the latest image
            name: Custom deployment name
            timeout: Deployment timeout
            host: Host
            port: Port
            backend_config: Backend config
            backend_config_file: Backend config file

        Returns:
            Server deployment information or None if failed
        """
        try:
            # Process volumes
            processed_volumes = None
            if volumes:
                if isinstance(volumes, dict):
                    processed_volumes = volumes
                elif isinstance(volumes, list):
                    processed_volumes = {path: path for path in volumes}
                else:
                    raise ValueError("Invalid volume format. Expected dict or list")

            return self.start_server(
                template_id=template_id,
                configuration=config,
                config_file=config_file,
                env_vars=env_vars,
                overrides=overrides,
                volumes=processed_volumes,
                pull_image=pull_image,
                transport=transport,
                host=host,
                port=str(port) if port else None,
                name=name,
                timeout=timeout,
                backend_config=backend_config,
                backend_config_file=backend_config_file,
            )

        except Exception as e:
            logger.error(f"Failed to deploy template {template_id}: {e}")
            return None

    def stop_server(self, deployment_id: str, timeout: int = 30) -> Dict[str, Any]:
        """Stop a running server.

        Args:
            deployment_id: Unique identifier for the deployment
            timeout: Timeout for graceful shutdown

        Returns:
            Result of the stop operation
        """

        self._multi_manager = MultiBackendManager(enabled_backends=None)
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

            return self.multi_manager.stop_deployment(deployment_id, timeout)
        except Exception as e:
            logger.error(f"Failed to stop server {deployment_id}: {e}")
            return {"success": False, "error": str(e)}

    def stop_all_servers(
        self,
        template: str = None,
        all_backends: bool = False,
        timeout: int = 30,
        force: bool = False,
    ) -> bool:
        """
        Stop all servers for a specific template.

        Args:
            template: Template name to stop all servers. If None, stops all servers.
            all_backends: Shall all deployments cross banckend be stopped?

        Returns:
            True if all servers were stopped successfully, False otherwise
        """

        if all_backends:
            self._multi_manager = MultiBackendManager(enabled_backends=None)
        else:
            self._multi_manager = self.multi_manager

        try:
            targets = self.list_servers(
                template_name=template, all_backends=all_backends, status="running"
            )

            if not targets:
                return {None: {"success": True}}

            results = {}
            for deployment in targets:
                backend = deployment.get("backend_type", "unknown")
                deployment_id = deployment.get(
                    "id", deployment.get("deployment_id", deployment.get("name", None))
                )
                deployment_manager = self._multi_manager.deployment_managers.get(
                    backend
                )
                result = {"success": False}
                if backend and deployment_id and deployment_manager:
                    try:
                        result = deployment_manager.stop_deployment(
                            deployment_id, timeout=timeout, force=force
                        )
                    except Exception as e:
                        logger.error(f"Failed to stop server {deployment_id}: {e}")

                results[deployment_id] = result

        except Exception as e:
            logger.error(f"Failed to stop all servers for template {template}: {e}")

        return results

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

        self._multi_manager = MultiBackendManager(enabled_backends=None)

        try:
            result = self._multi_manager.get_deployment_logs(
                deployment_id, lines=lines, follow=follow
            )
            return result.get("logs") if result.get("success") else None
        except Exception as e:
            logger.error(f"Failed to get server logs for {deployment_id}: {e}")
            return None

    def get_template_logs(
        self,
        template: str,
        lines: int = 100,
        all_backends: bool = False,
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get logs for all running deployments of a template, grouped by backend_type.

        Args:
            template: Template name to filter deployments
            lines: Number of log lines to retrieve per deployment
            all_backends: Whether to include all backends

        Returns:
            Dict of backend_type -> list of {deployment_id: logs}
        """

        if all_backends:
            self._multi_manager = MultiBackendManager(enabled_backends=None)
        else:
            self._multi_manager = self.multi_manager

        result = defaultdict(list)
        try:
            deployments = self.list_servers(
                template_name=template, all_backends=all_backends, status="running"
            )
            for dep in deployments:
                backend = dep.get("backend_type", "unknown")
                deployment_id = dep.get(
                    "id", dep.get("deployment_id", dep.get("name", None))
                )
                logs = self.get_server_logs(deployment_id, lines=lines)
                result[backend].append({deployment_id: logs})
        except Exception as e:
            logger.error(f"Failed to get logs for template {template}: {e}")
        return dict(result)

    # Tool Discovery and Management
    def list_tools(
        self,
        template_name: str,
        force_refresh: bool = False,
        static: bool = True,
        dynamic: bool = True,
        include_metadata: bool = False,
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """
        List available tools from a template or all discovered tools.

        Args:
            template_name: Specific template to get tools from
            force_refresh: Force refresh of tool cache
            static: Allow static discovery
            dynamic: Allow dynamic discovery
            include_metadata: Whether to return metadata about discovery method

        Returns:
            If include_metadata=True: Dict with tools and metadata
            If include_metadata=False: List of tools (backward compatible)
        """
        try:
            if force_refresh:
                self.tool_manager.clear_cache(template_name=template_name)

            result = self.tool_manager.list_tools(
                template_name,
                static=static,
                dynamic=dynamic,
                force_refresh=force_refresh,
            )

            if include_metadata:
                return result
            else:
                # Backward compatible - return just the tools list
                return result.get("tools", [])
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
        pull_image: bool = True,
        force_stdio: bool = False,
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
            pull_image: Whether to pull images for stdio calls
            force_stdio: Force stdio transport even if HTTP is available

        Returns:
            Tool response or None if failed
        """
        try:
            return self.tool_manager.call_tool(
                template_id,
                tool_name,
                arguments or {},
                config_values=server_config,
                timeout=timeout,
                pull_image=pull_image,
                force_stdio=force_stdio,
            )
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return None

    def call_tool_with_config(
        self,
        template_id: str,
        tool_name: str,
        arguments: Dict[str, Any] = None,
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        config_values: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        pull_image: bool = True,
        force_stdio: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool with flexible configuration support for interactive CLI.

        Args:
            template_id: Template that provides the tool
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool
            config_file: Path to configuration file
            env_vars: Environment variables
            config_values: Direct configuration values
            timeout: Timeout for the call
            pull_image: Whether to pull images for stdio calls
            force_stdio: Force stdio transport

        Returns:
            Tool response or None if failed
        """
        try:
            from mcp_template.core.config_processor import ConfigProcessor

            # Get template info for configuration processing
            template_info = self.get_template_info(template_id)
            if not template_info:
                logger.error(f"Template {template_id} not found")
                return None

            # Merge configuration from all sources
            config_processor = ConfigProcessor()
            final_config = config_processor.prepare_configuration(
                template=template_info,
                session_config=config_values or {},
                config_file=config_file,
                config_values={},  # inline configs handled via config_values param
                env_vars=env_vars or {},
            )

            return self.call_tool(
                template_id=template_id,
                tool_name=tool_name,
                arguments=arguments,
                server_config=final_config,
                timeout=timeout,
                pull_image=pull_image,
                force_stdio=force_stdio,
            )
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} with config: {e}")
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
