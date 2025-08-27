"""
Unit tests for the MCP client probe module (mcp_template.tools.mcp_client_probe).

Tests MCP server communication and tool discovery via stdio and HTTP protocols.
"""

import asyncio
import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

pytestmark = pytest.mark.unit

from mcp_template.tools.mcp_client_probe import MCPClientProbe


class TestMCPClientProbe:
    """Test the MCPClientProbe class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe()

    def test_init_default_timeout(self):
        """Test default initialization."""
        assert self.probe.timeout == 15

    def test_init_custom_timeout(self):
        """Test initialization with custom timeout."""
        probe = MCPClientProbe(timeout=30)
        assert probe.timeout == 30

    @pytest.mark.asyncio
    async def test_discover_tools_from_command_success(self):
        """Test successful tool discovery from command."""
        # Mock process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.terminate = Mock()

        # Mock the stdio communication
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch.object(self.probe, "_communicate_via_stdio") as mock_comm:
                mock_comm.return_value = {
                    "tools": [{"name": "test_tool", "description": "Test tool"}],
                    "server_info": {"name": "test-server", "version": "1.0"},
                }

                result = await self.probe.discover_tools_from_command(
                    ["python", "-m", "test_server"]
                )

                assert result is not None
                assert "tools" in result
                assert result["tools"][0]["name"] == "test_tool"
                mock_comm.assert_called_once_with(mock_process)

    @pytest.mark.asyncio
    async def test_discover_tools_from_command_process_failure(self):
        """Test discovery when process fails to start."""
        with patch(
            "asyncio.create_subprocess_exec", side_effect=OSError("Process failed")
        ):
            result = await self.probe.discover_tools_from_command(
                ["invalid", "command"]
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_discover_tools_from_command_with_working_dir(self):
        """Test discovery with custom working directory."""
        mock_process = Mock()
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.terminate = Mock()

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            with patch.object(self.probe, "_communicate_via_stdio", return_value={}):
                await self.probe.discover_tools_from_command(
                    ["python", "server.py"], working_dir="/app"
                )

                mock_exec.assert_called_once()
                call_kwargs = mock_exec.call_args[1]
                assert call_kwargs["cwd"] == "/app"

    @pytest.mark.asyncio
    async def test_discover_tools_from_command_timeout(self):
        """Test discovery with timeout."""
        mock_process = Mock()
        mock_process.wait = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_process.terminate = Mock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.probe.discover_tools_from_command(["slow", "server"])

            assert result is None
            mock_process.terminate.assert_called_once()


class TestMCPClientProbeStdioCommunication:
    """Test stdio communication functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe()

    @pytest.mark.asyncio
    async def test_communicate_via_stdio_success(self):
        """Test successful stdio communication."""
        # Mock process with stdio streams
        mock_process = Mock()
        mock_stdin = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout

        # Mock the read/write sequence
        initialize_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "test-server", "version": "1.0"},
            },
        }

        tools_response = {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {
                        "name": "search_files",
                        "description": "Search for files in the repository",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "pattern": {"type": "string"},
                                "path": {"type": "string"},
                            },
                        },
                    }
                ]
            },
        }

        # Mock readline to return our responses
        mock_stdout.readline.side_effect = [
            (json.dumps(initialize_response) + "\n").encode(),
            (json.dumps(tools_response) + "\n").encode(),
        ]

        result = await self.probe._communicate_via_stdio(mock_process)

        assert result is not None
        assert "tools" in result
        assert "server_info" in result
        assert result["tools"][0]["name"] == "search_files"
        assert result["server_info"]["name"] == "test-server"

        # Verify correct messages were sent
        assert mock_stdin.write.call_count >= 2  # initialize + list_tools
        assert mock_stdin.drain.called

    @pytest.mark.asyncio
    async def test_communicate_via_stdio_initialize_failure(self):
        """Test stdio communication when initialize fails."""
        mock_process = Mock()
        mock_stdin = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout

        # Mock error response for initialize
        error_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -1, "message": "Initialization failed"},
        }

        mock_stdout.readline.return_value = (json.dumps(error_response) + "\n").encode()

        result = await self.probe._communicate_via_stdio(mock_process)

        assert result is None

    @pytest.mark.asyncio
    async def test_communicate_via_stdio_json_parse_error(self):
        """Test stdio communication with invalid JSON response."""
        mock_process = Mock()
        mock_stdin = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout

        # Mock invalid JSON response
        mock_stdout.readline.return_value = b"invalid json\n"

        result = await self.probe._communicate_via_stdio(mock_process)

        assert result is None

    @pytest.mark.asyncio
    async def test_communicate_via_stdio_eof_error(self):
        """Test stdio communication with EOF error."""
        mock_process = Mock()
        mock_stdin = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout

        # Mock EOF
        mock_stdout.readline.return_value = b""

        result = await self.probe._communicate_via_stdio(mock_process)

        assert result is None

    @pytest.mark.asyncio
    async def test_communicate_via_stdio_timeout(self):
        """Test stdio communication timeout."""
        mock_process = Mock()
        mock_stdin = AsyncMock()
        mock_stdout = AsyncMock()
        mock_process.stdin = mock_stdin
        mock_process.stdout = mock_stdout

        # Mock timeout on readline
        mock_stdout.readline.side_effect = asyncio.TimeoutError()

        result = await self.probe._communicate_via_stdio(mock_process)

        assert result is None


class TestMCPClientProbeHttpCommunication:
    """Test HTTP communication functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe()

    @pytest.mark.asyncio
    async def test_discover_tools_via_http_success(self):
        """Test successful HTTP tool discovery."""
        mock_session = AsyncMock()

        # Mock initialize response
        mock_init_response = Mock()
        mock_init_response.status = 200
        mock_init_response.json = AsyncMock(
            return_value={
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "http-server", "version": "1.0"},
                }
            }
        )

        # Mock tools list response
        mock_tools_response = Mock()
        mock_tools_response.status = 200
        mock_tools_response.json = AsyncMock(
            return_value={
                "result": {
                    "tools": [
                        {
                            "name": "http_tool",
                            "description": "HTTP-based tool",
                            "inputSchema": {"type": "object"},
                        }
                    ]
                }
            }
        )

        mock_session.post.side_effect = [mock_init_response, mock_tools_response]

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await self.probe.discover_tools_via_http("http://localhost:8080")

            assert result is not None
            assert "tools" in result
            assert "server_info" in result
            assert result["tools"][0]["name"] == "http_tool"
            assert result["server_info"]["name"] == "http-server"

    @pytest.mark.asyncio
    async def test_discover_tools_via_http_connection_error(self):
        """Test HTTP discovery with connection error."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            mock_session.post.side_effect = Exception("Connection failed")

            result = await self.probe.discover_tools_via_http("http://localhost:8080")

            assert result is None

    @pytest.mark.asyncio
    async def test_discover_tools_via_http_non_200_status(self):
        """Test HTTP discovery with non-200 status."""
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status = 500
        mock_session.post.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await self.probe.discover_tools_via_http("http://localhost:8080")

            assert result is None

    @pytest.mark.asyncio
    async def test_discover_tools_via_http_initialize_error(self):
        """Test HTTP discovery when initialize returns error."""
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={"error": {"code": -1, "message": "Init failed"}}
        )
        mock_session.post.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await self.probe.discover_tools_via_http("http://localhost:8080")

            assert result is None

    @pytest.mark.asyncio
    async def test_discover_tools_via_http_with_headers(self):
        """Test HTTP discovery with custom headers."""
        mock_session = AsyncMock()
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(
            return_value={
                "result": {"capabilities": {}, "serverInfo": {"name": "test"}}
            }
        )
        mock_session.post.return_value = mock_response

        with patch("aiohttp.ClientSession", return_value=mock_session):
            await self.probe.discover_tools_via_http(
                "http://localhost:8080", headers={"Authorization": "Bearer token123"}
            )

            # Verify headers were passed
            call_args = mock_session.post.call_args_list[0]
            assert "headers" in call_args[1]
            assert call_args[1]["headers"]["Authorization"] == "Bearer token123"


class TestMCPClientProbeMessageFormatting:
    """Test MCP message formatting."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe()

    def test_create_initialize_message(self):
        """Test initialize message creation."""
        message = self.probe._create_initialize_message()

        assert message["jsonrpc"] == "2.0"
        assert message["method"] == "initialize"
        assert "params" in message
        assert "clientInfo" in message["params"]
        assert message["params"]["protocolVersion"] == "2024-11-05"

    def test_create_list_tools_message(self):
        """Test list tools message creation."""
        message = self.probe._create_list_tools_message()

        assert message["jsonrpc"] == "2.0"
        assert message["method"] == "tools/list"
        assert "id" in message

    def test_message_id_increment(self):
        """Test that message IDs are incremented."""
        msg1 = self.probe._create_initialize_message()
        msg2 = self.probe._create_list_tools_message()

        assert msg2["id"] == msg1["id"] + 1

    def test_format_message_for_stdio(self):
        """Test message formatting for stdio."""
        message = {"test": "data"}
        formatted = self.probe._format_message_for_stdio(message)

        assert formatted.endswith("\n")
        parsed = json.loads(formatted.strip())
        assert parsed["test"] == "data"


class TestMCPClientProbeIntegration:
    """Test integration aspects of MCPClientProbe."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe()

    @pytest.mark.asyncio
    async def test_end_to_end_stdio_workflow(self):
        """Test complete stdio discovery workflow."""
        # This test verifies the complete flow without external dependencies
        mock_process = Mock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()
        mock_process.wait = AsyncMock(return_value=0)
        mock_process.terminate = Mock()

        # Simulate complete successful exchange
        responses = [
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "test", "version": "1.0"},
                    },
                }
            )
            + "\n",
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": [{"name": "test_tool"}]},
                }
            )
            + "\n",
        ]

        mock_process.stdout.readline.side_effect = [r.encode() for r in responses]

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.probe.discover_tools_from_command(["test", "server"])

            assert result is not None
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "test_tool"

    def test_error_logging(self):
        """Test that errors are properly logged."""
        with patch("mcp_template.tools.mcp_client_probe.logger") as mock_logger:
            # Test will depend on specific error scenarios
            pass

    def test_timeout_configuration(self):
        """Test timeout configuration affects behavior."""
        short_timeout_probe = MCPClientProbe(timeout=1)
        long_timeout_probe = MCPClientProbe(timeout=60)

        assert short_timeout_probe.timeout == 1
        assert long_timeout_probe.timeout == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
