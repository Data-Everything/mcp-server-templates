"""
Unit tests for the refactored MCP Client.

Tests focus on the core MCP functionality without template/server management.
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core import MCPConnection


class TestMCPClient:
    """Test suite for the refactored MCPClient focusing on connections only."""

    @pytest.fixture
    def client(self):
        """Create an MCPClient instance for testing."""
        return MCPClient(timeout=5)

    @pytest.fixture
    def mock_connection(self):
        """Create a mock MCPConnection for testing."""
        connection = MagicMock(spec=MCPConnection)
        connection.process = True  # Simulate active connection
        connection.session_info = {"version": "1.0"}
        connection.server_info = {"name": "test_server"}
        connection.connect_stdio = AsyncMock(return_value=True)
        connection.disconnect = AsyncMock(return_value=True)
        connection.list_tools = AsyncMock(
            return_value=[{"name": "test_tool", "description": "A test tool"}]
        )
        connection.call_tool = AsyncMock(return_value={"result": "success"})
        return connection

    def test_client_initialization(self, client):
        """Test MCPClient initialization."""
        assert client.timeout == 5
        assert len(client._active_connections) == 0
        assert client._connection_counter == 0

    @pytest.mark.asyncio
    async def test_connect_with_stdio_config(self, client):
        """Test unified connect method with stdio configuration."""
        config = {
            "type": "stdio",
            "command": ["python", "server.py"],
            "working_dir": "/tmp",
            "env_vars": {"TEST": "value"},
        }

        with patch.object(
            client, "connect_stdio", new_callable=AsyncMock
        ) as mock_stdio:
            mock_stdio.return_value = "stdio_1"

            connection_id = await client.connect(config)

            assert connection_id == "stdio_1"
            mock_stdio.assert_called_once_with(
                command=["python", "server.py"],
                working_dir="/tmp",
                env_vars={"TEST": "value"},
            )

    @pytest.mark.asyncio
    async def test_connect_with_websocket_config(self, client):
        """Test unified connect method with websocket configuration."""
        config = {
            "type": "websocket",
            "url": "ws://localhost:8080",
            "headers": {"Authorization": "Bearer token"},
        }

        with patch.object(
            client, "connect_websocket", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = "websocket_1"

            connection_id = await client.connect(config)

            assert connection_id == "websocket_1"
            mock_ws.assert_called_once_with(
                url="ws://localhost:8080", headers={"Authorization": "Bearer token"}
            )

    @pytest.mark.asyncio
    async def test_connect_with_invalid_type(self, client):
        """Test unified connect method with invalid connection type."""
        config = {"type": "invalid"}

        connection_id = await client.connect(config)

        assert connection_id is None

    @pytest.mark.asyncio
    async def test_connect_stdio_success(self, client, mock_connection):
        """Test successful stdio connection."""
        with patch("mcp_template.client.MCPConnection", return_value=mock_connection):
            connection_id = await client.connect_stdio(["python", "server.py"])

            assert connection_id == "stdio_1"
            assert connection_id in client._active_connections
            mock_connection.connect_stdio.assert_called_once_with(
                command=["python", "server.py"], working_dir=None, env_vars=None
            )

    @pytest.mark.asyncio
    async def test_connect_stdio_failure(self, client, mock_connection):
        """Test failed stdio connection."""
        mock_connection.connect_stdio.return_value = False

        with patch("mcp_template.client.MCPConnection", return_value=mock_connection):
            connection_id = await client.connect_stdio(["python", "server.py"])

            assert connection_id is None
            assert len(client._active_connections) == 0
            mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_websocket_not_implemented(self, client):
        """Test websocket connection (not yet implemented)."""
        connection_id = await client.connect_websocket("ws://localhost:8080")
        assert connection_id is None

    @pytest.mark.asyncio
    async def test_connect_http_stream_not_implemented(self, client):
        """Test HTTP stream connection (not yet implemented)."""
        connection_id = await client.connect_http_stream("http://localhost:8080")
        assert connection_id is None

    def test_list_connected_servers_empty(self, client):
        """Test listing connected servers when none are connected."""
        servers = client.list_connected_servers()
        assert servers == []

    def test_list_connected_servers_with_connections(self, client, mock_connection):
        """Test listing connected servers with active connections."""
        client._active_connections["stdio_1"] = mock_connection

        servers = client.list_connected_servers()

        assert len(servers) == 1
        assert servers[0]["connection_id"] == "stdio_1"
        assert servers[0]["status"] == "connected"
        assert servers[0]["session_info"] == {"version": "1.0"}
        assert servers[0]["server_info"] == {"name": "test_server"}

    @pytest.mark.asyncio
    async def test_list_tools_from_specific_connection(self, client, mock_connection):
        """Test listing tools from a specific connection."""
        client._active_connections["stdio_1"] = mock_connection

        tools = await client.list_tools("stdio_1")

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        mock_connection.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_tools_from_nonexistent_connection(self, client):
        """Test listing tools from a nonexistent connection."""
        tools = await client.list_tools("invalid")
        assert tools == []

    @pytest.mark.asyncio
    async def test_list_tools_from_all_connections(self, client, mock_connection):
        """Test listing tools from all connections."""
        client._active_connections["stdio_1"] = mock_connection

        tools = await client.list_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert tools[0]["connection_id"] == "stdio_1"

    @pytest.mark.asyncio
    async def test_call_tool_success(self, client, mock_connection):
        """Test successful tool call."""
        client._active_connections["stdio_1"] = mock_connection

        result = await client.call_tool("stdio_1", "test_tool", {"arg": "value"})

        assert result == {"result": "success"}
        mock_connection.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_call_tool_nonexistent_connection(self, client):
        """Test calling tool on nonexistent connection."""
        result = await client.call_tool("invalid", "test_tool", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_call_tool_exception(self, client, mock_connection):
        """Test tool call with exception."""
        mock_connection.call_tool.side_effect = Exception("Tool call failed")
        client._active_connections["stdio_1"] = mock_connection

        result = await client.call_tool("stdio_1", "test_tool", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect_success(self, client, mock_connection):
        """Test successful disconnection."""
        client._active_connections["stdio_1"] = mock_connection

        result = await client.disconnect("stdio_1")

        assert result is True
        assert "stdio_1" not in client._active_connections
        mock_connection.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection(self, client):
        """Test disconnecting from nonexistent connection."""
        result = await client.disconnect("invalid")
        assert result is False

    @pytest.mark.asyncio
    async def test_disconnect_all(self, client, mock_connection):
        """Test disconnecting from all connections."""
        client._active_connections["stdio_1"] = mock_connection
        client._active_connections["stdio_2"] = mock_connection

        await client.disconnect_all()

        assert len(client._active_connections) == 0

    def test_get_connection_info_success(self, client, mock_connection):
        """Test getting connection information."""
        client._active_connections["stdio_1"] = mock_connection

        info = client.get_connection_info("stdio_1")

        assert info["connection_id"] == "stdio_1"
        assert info["status"] == "connected"
        assert info["session_info"] == {"version": "1.0"}

    def test_get_connection_info_nonexistent(self, client):
        """Test getting info for nonexistent connection."""
        info = client.get_connection_info("invalid")
        assert info is None

    def test_generate_connection_id(self, client):
        """Test connection ID generation."""
        id1 = client._generate_connection_id("stdio")
        id2 = client._generate_connection_id("websocket")

        assert id1 == "stdio_1"
        assert id2 == "websocket_2"

    @pytest.mark.asyncio
    async def test_cleanup(self, client, mock_connection):
        """Test cleanup of all connections."""
        client._active_connections["stdio_1"] = mock_connection

        await client.cleanup()

        assert len(client._active_connections) == 0

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_connection):
        """Test MCPClient as async context manager."""
        with patch("mcp_template.client.MCPConnection", return_value=mock_connection):
            async with MCPClient() as client:
                connection_id = await client.connect_stdio(["python", "server.py"])
                assert connection_id is not None
                assert len(client._active_connections) == 1

            # After context exit, cleanup should have been called
            # Note: We can't easily test this without more complex mocking


@pytest.mark.integration
class TestMCPClientIntegration:
    """Integration tests for MCPClient (require actual MCP servers)."""

    @pytest.mark.asyncio
    async def test_real_connection_with_mock_server(self):
        """Test with a mock MCP server process."""
        # This would require setting up a real MCP server
        # For now, just test the structure
        client = MCPClient()

        # Test that we can create a client and call methods
        servers = client.list_connected_servers()
        assert isinstance(servers, list)

        await client.cleanup()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
