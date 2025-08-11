"""
MCP Client - Focused Python API for MCP Server Connections.

This module provides a clean Python API for programmatic access to MCP servers,
focusing only on core MCP protocol operations without server lifecycle management.

Supported operations:
- Connect to existing MCP servers (stdio, websocket, HTTP)
- List tools from connected servers
- Invoke tools on connected servers
- Manage server connections

Excluded operations (handled by CLI):
- Template management
- Server deployment/lifecycle
- Configuration management

Example usage:
    ```python
    import asyncio
    from mcp_template.client import MCPClient

    async def main():
        client = MCPClient()

        # Connect to an existing MCP server
        connection_id = await client.connect_stdio(["python", "demo_server.py"])

        # List available tools
        tools = await client.list_tools(connection_id)
        print(f"Available tools: {[t['name'] for t in tools]}")

        # Call a tool
        result = await client.call_tool(connection_id, "echo", {"message": "Hello World"})
        print(f"Tool result: {result}")

        # List connected servers
        servers = client.list_connected_servers()
        print(f"Connected servers: {len(servers)}")

        # Clean up
        await client.disconnect(connection_id)

    asyncio.run(main())
    ```
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp_template.core import MCPConnection

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Focused MCP Client for programmatic access to MCP server connections.

    This client provides a simplified interface for core MCP operations:
    - Connecting to existing MCP servers
    - Listing and calling tools from connected servers
    - Managing server connections

    Note: This client does NOT handle server deployment, template management,
    or other CLI-specific functionality. It focuses purely on MCP protocol operations.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize MCP Client.

        Args:
            timeout: Default timeout for MCP operations in seconds
        """
        self.timeout = timeout

        # Track active connections
        self._active_connections: Dict[str, MCPConnection] = {}
        self._connection_counter = 0

    # Connection Management
    async def connect(self, connection_config: Dict[str, Any]) -> Optional[str]:
        """
        Connect to an MCP server using the specified configuration.

        Args:
            connection_config: Connection configuration dict with type and parameters:
                - {"type": "stdio", "command": ["python", "server.py"], "working_dir": "/path", "env_vars": {...}}
                - {"type": "websocket", "url": "ws://localhost:8080/mcp", "headers": {...}}
                - {"type": "http", "url": "http://localhost:8080/mcp", "headers": {...}}

        Returns:
            Connection ID if successful, None if failed
        """
        connection_type = connection_config.get("type")

        if connection_type == "stdio":
            return await self.connect_stdio(
                command=connection_config.get("command", []),
                working_dir=connection_config.get("working_dir"),
                env_vars=connection_config.get("env_vars"),
            )
        elif connection_type == "websocket":
            return await self.connect_websocket(
                url=connection_config.get("url", ""),
                headers=connection_config.get("headers"),
            )
        elif connection_type == "http":
            return await self.connect_http_stream(
                url=connection_config.get("url", ""),
                headers=connection_config.get("headers"),
            )
        else:
            logger.error("Unsupported connection type: %s", connection_type)
            return None

    async def connect_stdio(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a stdio connection to an MCP server.

        Args:
            command: Command to execute MCP server
            working_dir: Working directory for the process
            env_vars: Environment variables for the process

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("stdio")

        connection = MCPConnection(timeout=self.timeout)
        success = await connection.connect_stdio(
            command=command, working_dir=working_dir, env_vars=env_vars
        )

        if success:
            self._active_connections[connection_id] = connection
            logger.info("Connected to MCP server via stdio: %s", connection_id)
            return connection_id
        else:
            await connection.disconnect()
            logger.error("Failed to connect to MCP server via stdio")
            return None

    async def connect_websocket(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a websocket connection to an MCP server.

        Args:
            url: WebSocket URL (e.g., "ws://localhost:8080/mcp")
            headers: Optional headers for WebSocket handshake

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("websocket")

        # TODO: Implement websocket connection in MCPConnection
        logger.error("WebSocket connections not yet implemented")
        return None

    async def connect_http_stream(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create an HTTP stream connection to an MCP server.

        Args:
            url: HTTP URL (e.g., "http://localhost:8080/mcp")
            headers: Optional HTTP headers

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("http")

        # TODO: Implement HTTP stream connection in MCPConnection
        logger.error("HTTP stream connections not yet implemented")
        return None

    # Server Discovery (Connected Only)
    def list_connected_servers(self) -> List[Dict[str, Any]]:
        """
        List currently connected MCP servers.

        Returns:
            List of connected server information
        """
        servers = []
        for connection_id, connection in self._active_connections.items():
            server_info = {
                "connection_id": connection_id,
                "status": "connected" if connection.process else "disconnected",
                "session_info": connection.session_info,
                "server_info": connection.server_info,
            }
            servers.append(server_info)

        return servers

    # Tool Operations
    async def list_tools(
        self, connection_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools from connected server(s).

        Args:
            connection_id: Specific connection to get tools from (None for all connections)

        Returns:
            List of tool definitions
        """
        if connection_id:
            # Get tools from specific connection
            if connection_id not in self._active_connections:
                logger.error("Connection %s not found", connection_id)
                return []

            connection = self._active_connections[connection_id]
            tools = await connection.list_tools()
            return tools or []
        else:
            # Get tools from all connections
            all_tools = []
            for conn_id, connection in self._active_connections.items():
                try:
                    tools = await connection.list_tools()
                    if tools:
                        # Add connection_id to each tool for identification
                        for tool in tools:
                            tool["connection_id"] = conn_id
                        all_tools.extend(tools)
                except Exception as e:
                    logger.warning(
                        "Failed to get tools from connection %s: %s", conn_id, e
                    )

            return all_tools

    async def call_tool(
        self,
        connection_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on a specific MCP server connection.

        Args:
            connection_id: ID of the connection to use
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response or None if failed
        """
        if connection_id not in self._active_connections:
            logger.error("Connection %s not found", connection_id)
            return None

        connection = self._active_connections[connection_id]
        try:
            result = await connection.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(
                "Failed to call tool %s on connection %s: %s",
                tool_name,
                connection_id,
                e,
            )
            return None

    # Connection Management
    async def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect from a specific MCP server.

        Args:
            connection_id: ID of the connection to disconnect

        Returns:
            True if disconnected successfully, False if connection not found
        """
        if connection_id not in self._active_connections:
            logger.warning("Connection %s not found for disconnection", connection_id)
            return False

        connection = self._active_connections[connection_id]
        try:
            await connection.disconnect()
            del self._active_connections[connection_id]
            logger.info("Disconnected from server: %s", connection_id)
            return True
        except Exception as e:
            logger.error("Error disconnecting from %s: %s", connection_id, e)
            return False

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        connection_ids = list(self._active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    # Utility Methods
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.

        Args:
            connection_id: ID of the connection

        Returns:
            Connection information or None if not found
        """
        if connection_id not in self._active_connections:
            return None

        connection = self._active_connections[connection_id]
        return {
            "connection_id": connection_id,
            "status": "connected" if connection.process else "disconnected",
            "session_info": connection.session_info,
            "server_info": connection.server_info,
        }

    def _generate_connection_id(self, connection_type: str) -> str:
        """Generate a unique connection ID."""
        self._connection_counter += 1
        return f"{connection_type}_{self._connection_counter}"

    # Cleanup and Context Management
    async def cleanup(self) -> None:
        """Clean up all active connections and resources."""
        await self.disconnect_all()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


"""
MCP Client - Focused Python API for MCP Server Connections.

This module provides a clean Python API for programmatic access to MCP servers,
focusing only on core MCP protocol operations without server lifecycle management.

Supported operations:
- Connect to existing MCP servers (stdio, websocket, HTTP)
- List tools from connected servers
- Invoke tools on connected servers
- Manage server connections

Excluded operations (handled by CLI):
- Template management
- Server deployment/lifecycle
- Configuration management

Example usage:
    ```python
    import asyncio
    from mcp_template.client import MCPClient

    async def main():
        client = MCPClient()

        # Connect to an existing MCP server
        connection_id = await client.connect_stdio(["python", "demo_server.py"])

        # List available tools
        tools = await client.list_tools(connection_id)
        print(f"Available tools: {[t['name'] for t in tools]}")

        # Call a tool
        result = await client.call_tool(connection_id, "echo", {"message": "Hello World"})
        print(f"Tool result: {result}")

        # List connected servers
        servers = client.list_connected_servers()
        print(f"Connected servers: {len(servers)}")

        # Clean up
        await client.disconnect(connection_id)

    asyncio.run(main())
    ```
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from mcp_template.core import MCPConnection

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Focused MCP Client for programmatic access to MCP server connections.

    This client provides a simplified interface for core MCP operations:
    - Connecting to existing MCP servers
    - Listing and calling tools from connected servers
    - Managing server connections

    Note: This client does NOT handle server deployment, template management,
    or other CLI-specific functionality. It focuses purely on MCP protocol operations.
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize MCP Client.

        Args:
            timeout: Default timeout for MCP operations in seconds
        """
        self.timeout = timeout

        # Track active connections
        self._active_connections: Dict[str, MCPConnection] = {}
        self._connection_counter = 0

    # Connection Management
    async def connect(self, connection_config: Dict[str, Any]) -> Optional[str]:
        """
        Connect to an MCP server using the specified configuration.

        Args:
            connection_config: Connection configuration dict with type and parameters:
                - {"type": "stdio", "command": ["python", "server.py"], "working_dir": "/path", "env_vars": {...}}
                - {"type": "websocket", "url": "ws://localhost:8080/mcp", "headers": {...}}
                - {"type": "http", "url": "http://localhost:8080/mcp", "headers": {...}}

        Returns:
            Connection ID if successful, None if failed
        """
        connection_type = connection_config.get("type")

        if connection_type == "stdio":
            return await self.connect_stdio(
                command=connection_config.get("command", []),
                working_dir=connection_config.get("working_dir"),
                env_vars=connection_config.get("env_vars"),
            )
        elif connection_type == "websocket":
            return await self.connect_websocket(
                url=connection_config.get("url", ""),
                headers=connection_config.get("headers"),
            )
        elif connection_type == "http":
            return await self.connect_http_stream(
                url=connection_config.get("url", ""),
                headers=connection_config.get("headers"),
            )
        else:
            logger.error("Unsupported connection type: %s", connection_type)
            return None

    async def connect_stdio(
        self,
        command: List[str],
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a stdio connection to an MCP server.

        Args:
            command: Command to execute MCP server
            working_dir: Working directory for the process
            env_vars: Environment variables for the process

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("stdio")

        connection = MCPConnection(timeout=self.timeout)
        success = await connection.connect_stdio(
            command=command, working_dir=working_dir, env_vars=env_vars
        )

        if success:
            self._active_connections[connection_id] = connection
            logger.info("Connected to MCP server via stdio: %s", connection_id)
            return connection_id
        else:
            await connection.disconnect()
            logger.error("Failed to connect to MCP server via stdio")
            return None

    async def connect_websocket(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create a websocket connection to an MCP server.

        Args:
            url: WebSocket URL (e.g., "ws://localhost:8080/mcp")
            headers: Optional headers for WebSocket handshake

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("websocket")

        # TODO: Implement websocket connection in MCPConnection
        logger.error("WebSocket connections not yet implemented")
        return None

    async def connect_http_stream(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """
        Create an HTTP stream connection to an MCP server.

        Args:
            url: HTTP URL (e.g., "http://localhost:8080/mcp")
            headers: Optional HTTP headers

        Returns:
            Connection ID if successful, None if failed
        """
        connection_id = self._generate_connection_id("http")

        # TODO: Implement HTTP stream connection in MCPConnection
        logger.error("HTTP stream connections not yet implemented")
        return None

    # Server Discovery (Connected Only)
    def list_connected_servers(self) -> List[Dict[str, Any]]:
        """
        List currently connected MCP servers.

        Returns:
            List of connected server information
        """
        servers = []
        for connection_id, connection in self._active_connections.items():
            server_info = {
                "connection_id": connection_id,
                "status": "connected" if connection.process else "disconnected",
                "session_info": connection.session_info,
                "server_info": connection.server_info,
            }
            servers.append(server_info)

        return servers

    # Tool Operations
    async def list_tools(
        self, connection_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools from connected server(s).

        Args:
            connection_id: Specific connection to get tools from (None for all connections)

        Returns:
            List of tool definitions
        """
        if connection_id:
            # Get tools from specific connection
            if connection_id not in self._active_connections:
                logger.error("Connection %s not found", connection_id)
                return []

            connection = self._active_connections[connection_id]
            tools = await connection.list_tools()
            return tools or []
        else:
            # Get tools from all connections
            all_tools = []
            for conn_id, connection in self._active_connections.items():
                try:
                    tools = await connection.list_tools()
                    if tools:
                        # Add connection_id to each tool for identification
                        for tool in tools:
                            tool["connection_id"] = conn_id
                        all_tools.extend(tools)
                except Exception as e:
                    logger.warning(
                        "Failed to get tools from connection %s: %s", conn_id, e
                    )

            return all_tools

    async def call_tool(
        self,
        connection_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Call a tool on a specific MCP server connection.

        Args:
            connection_id: ID of the connection to use
            tool_name: Name of the tool to call
            arguments: Arguments to pass to the tool

        Returns:
            Tool response or None if failed
        """
        if connection_id not in self._active_connections:
            logger.error("Connection %s not found", connection_id)
            return None

        connection = self._active_connections[connection_id]
        try:
            result = await connection.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(
                "Failed to call tool %s on connection %s: %s",
                tool_name,
                connection_id,
                e,
            )
            return None

    # Connection Management
    async def disconnect(self, connection_id: str) -> bool:
        """
        Disconnect from a specific MCP server.

        Args:
            connection_id: ID of the connection to disconnect

        Returns:
            True if disconnected successfully, False if connection not found
        """
        if connection_id not in self._active_connections:
            logger.warning("Connection %s not found for disconnection", connection_id)
            return False

        connection = self._active_connections[connection_id]
        try:
            await connection.disconnect()
            del self._active_connections[connection_id]
            logger.info("Disconnected from server: %s", connection_id)
            return True
        except Exception as e:
            logger.error("Error disconnecting from %s: %s", connection_id, e)
            return False

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        connection_ids = list(self._active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

    # Utility Methods
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific connection.

        Args:
            connection_id: ID of the connection

        Returns:
            Connection information or None if not found
        """
        if connection_id not in self._active_connections:
            return None

        connection = self._active_connections[connection_id]
        return {
            "connection_id": connection_id,
            "status": "connected" if connection.process else "disconnected",
            "session_info": connection.session_info,
            "server_info": connection.server_info,
        }

    def _generate_connection_id(self, connection_type: str) -> str:
        """Generate a unique connection ID."""
        self._connection_counter += 1
        return f"{connection_type}_{self._connection_counter}"

    # Cleanup and Context Management
    async def cleanup(self) -> None:
        """Clean up all active connections and resources."""
        await self.disconnect_all()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()
