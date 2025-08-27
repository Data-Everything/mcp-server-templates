"""Unit tests for MCP Connection functionality."""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.core.mcp_connection import MCPConnection


@pytest.mark.unit
class TestMCPConnection:
    """Test cases for the MCPConnection class."""

    def test_initialization(self):
        """Test connection initialization."""
        conn = MCPConnection(timeout=60)
        assert conn.timeout == 60
        assert conn.process is None
        assert conn.session_info is None
        assert conn.server_info is None

    def test_initialization_default_timeout(self):
        """Test connection initialization with default timeout."""
        conn = MCPConnection()
        assert conn.timeout == 30

    @pytest.mark.asyncio
    async def test_connect_stdio_success(self):
        """Test successful stdio connection."""
        conn = MCPConnection()

        # Mock the subprocess and initialization
        mock_process = AsyncMock()
        mock_process.returncode = None

        with (
            patch(
                "asyncio.create_subprocess_exec", return_value=mock_process
            ) as mock_exec,
            patch.object(
                conn, "_initialize_mcp_session", return_value=True
            ) as mock_init,
        ):

            result = await conn.connect_stdio(["python", "server.py"])

            assert result is True
            assert conn.process == mock_process
            mock_exec.assert_called_once()
            mock_init.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_stdio_initialization_failure(self):
        """Test stdio connection with initialization failure."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.returncode = None

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            patch.object(conn, "_initialize_mcp_session", return_value=False),
            patch.object(conn, "disconnect") as mock_disconnect,
        ):

            result = await conn.connect_stdio(["python", "server.py"])

            assert result is False
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_stdio_with_env_vars(self):
        """Test stdio connection with environment variables."""
        conn = MCPConnection()

        mock_process = AsyncMock()

        with (
            patch(
                "asyncio.create_subprocess_exec", return_value=mock_process
            ) as mock_exec,
            patch.object(conn, "_initialize_mcp_session", return_value=True),
            patch("os.environ") as mock_environ,
        ):

            mock_environ.copy.return_value = {"PATH": "/usr/bin"}
            env_vars = {"API_KEY": "secret"}

            await conn.connect_stdio(
                ["python", "server.py"], working_dir="/tmp", env_vars=env_vars
            )

            # Verify subprocess was called with correct parameters
            call_args = mock_exec.call_args
            assert call_args[1]["cwd"] == "/tmp"
            assert call_args[1]["env"]["API_KEY"] == "secret"

    @pytest.mark.asyncio
    async def test_connect_stdio_exception(self):
        """Test stdio connection with exception."""
        conn = MCPConnection()

        with (
            patch(
                "asyncio.create_subprocess_exec",
                side_effect=Exception("Connection failed"),
            ),
            patch.object(conn, "disconnect") as mock_disconnect,
        ):

            result = await conn.connect_stdio(["python", "server.py"])

            assert result is False
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_mcp_session_success(self):
        """Test successful MCP session initialization."""
        conn = MCPConnection()

        # Mock process
        mock_process = AsyncMock()
        conn.process = mock_process

        # Mock successful initialization response
        init_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-server", "version": "1.0.0"},
            },
        }

        with (
            patch.object(
                conn, "_send_request", return_value=init_response
            ) as mock_send,
            patch.object(conn, "_send_notification") as mock_notify,
        ):

            result = await conn._initialize_mcp_session()

            assert result is True
            assert conn.session_info == init_response["result"]
            assert conn.server_info == init_response["result"]["serverInfo"]
            mock_send.assert_called_once()
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_mcp_session_failure(self):
        """Test MCP session initialization failure."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        conn.process = mock_process

        # Mock failed response
        with patch.object(conn, "_send_request", return_value=None):
            result = await conn._initialize_mcp_session()
            assert result is False

    @pytest.mark.asyncio
    async def test_list_tools_success(self):
        """Test successful tool listing."""
        conn = MCPConnection()
        conn.process = AsyncMock()
        conn.transport_type = (
            "stdio"  # Set up transport type to simulate active connection
        )

        tools_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {"name": "echo", "description": "Echo a message"},
                    {"name": "greet", "description": "Greet someone"},
                ]
            },
        }

        with patch.object(conn, "_send_request", return_value=tools_response):
            result = await conn.list_tools()

            assert result == tools_response["result"]["tools"]

    @pytest.mark.asyncio
    async def test_list_tools_no_connection(self):
        """Test tool listing without connection."""
        conn = MCPConnection()

        result = await conn.list_tools()
        assert result is None

    @pytest.mark.asyncio
    async def test_list_tools_invalid_response(self):
        """Test tool listing with invalid response."""
        conn = MCPConnection()
        conn.process = AsyncMock()

        with patch.object(
            conn, "_send_request", return_value={"error": "Invalid request"}
        ):
            result = await conn.list_tools()
            assert result is None

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call."""
        conn = MCPConnection()
        conn.process = AsyncMock()
        conn.transport_type = (
            "stdio"  # Set up transport type to simulate active connection
        )

        tool_response = {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {"content": [{"type": "text", "text": "Hello World"}]},
        }

        with patch.object(conn, "_send_request", return_value=tool_response):
            result = await conn.call_tool("echo", {"message": "Hello World"})

            assert result == tool_response["result"]

    @pytest.mark.asyncio
    async def test_call_tool_no_connection(self):
        """Test tool call without connection."""
        conn = MCPConnection()

        result = await conn.call_tool("echo", {"message": "Hello"})
        assert result is None

    @pytest.mark.asyncio
    async def test_send_request_success(self):
        """Test successful request sending."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            return_value=b'{"jsonrpc": "2.0", "id": 1, "result": {"success": true}}\n'
        )
        conn.process = mock_process

        request = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        result = await conn._send_request(request)

        expected_result = {"jsonrpc": "2.0", "id": 1, "result": {"success": True}}
        assert result == expected_result

    @pytest.mark.asyncio
    async def test_send_request_timeout(self):
        """Test request timeout."""
        conn = MCPConnection(timeout=1)

        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(side_effect=asyncio.TimeoutError())
        conn.process = mock_process

        request = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        result = await conn._send_request(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_send_request_empty_response(self):
        """Test request with empty response."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(return_value=b"")
        conn.process = mock_process

        request = {"jsonrpc": "2.0", "id": 1, "method": "test"}
        result = await conn._send_request(request)

        assert result is None

    @pytest.mark.asyncio
    async def test_send_notification(self):
        """Test sending notification."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        conn.process = mock_process

        notification = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        await conn._send_notification(notification)

        expected_json = json.dumps(notification) + "\n"
        mock_process.stdin.write.assert_called_once_with(expected_json.encode())
        mock_process.stdin.drain.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_running_process(self):
        """Test disconnecting from running process."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.wait = AsyncMock()
        conn.process = mock_process

        await conn.disconnect()

        assert conn.process is None
        assert conn.session_info is None
        assert conn.server_info is None
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_timeout_then_kill(self):
        """Test disconnecting with timeout then kill."""
        conn = MCPConnection()

        mock_process = AsyncMock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        # First call times out, second call succeeds
        mock_process.wait = AsyncMock(side_effect=[asyncio.TimeoutError(), None])
        mock_process.kill = Mock()
        conn.process = mock_process

        await conn.disconnect()

        mock_process.terminate.assert_called_once()
        mock_process.kill.assert_called_once()
        assert mock_process.wait.call_count == 2

    def test_is_connected_true(self):
        """Test is_connected when connected."""
        conn = MCPConnection()

        mock_process = Mock()
        mock_process.returncode = None
        conn.process = mock_process
        conn.transport_type = "stdio"  # Set transport type to complete connection state

        assert conn.is_connected() is True

    def test_is_connected_false_no_process(self):
        """Test is_connected when no process."""
        conn = MCPConnection()
        assert conn.is_connected() is False

    def test_is_connected_false_process_ended(self):
        """Test is_connected when process ended."""
        conn = MCPConnection()

        mock_process = Mock()
        mock_process.returncode = 0
        conn.process = mock_process

        assert conn.is_connected() is False

    def test_get_server_info(self):
        """Test getting server info."""
        conn = MCPConnection()

        server_info = {"name": "test-server", "version": "1.0.0"}
        conn.server_info = server_info

        assert conn.get_server_info() == server_info

    def test_get_session_info(self):
        """Test getting session info."""
        conn = MCPConnection()

        session_info = {"protocolVersion": "2024-11-05"}
        conn.session_info = session_info

        assert conn.get_session_info() == session_info
