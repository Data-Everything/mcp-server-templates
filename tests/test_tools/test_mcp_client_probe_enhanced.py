"""
Tests for enhanced MCP client probe functionality.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_template.tools.mcp_client_probe import MCPClientProbe


@pytest.mark.unit
class TestMCPClientProbeEnhancements:
    """Test enhanced MCP client probe functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.probe = MCPClientProbe(timeout=5)

    @pytest.mark.asyncio
    async def test_initialize_mcp_session_json_parsing_robustness(self):
        """Test that MCP initialization can handle non-JSON lines in output."""
        # Mock process with mixed output (non-JSON + JSON)
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        # Simulate output with startup messages followed by JSON
        responses = [
            b"Starting MCP server with stdio transport\n",  # Non-JSON startup message
            b"GitHub MCP Server running on stdio\n",        # Another startup message
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":true}},"serverInfo":{"name":"github-mcp-server","version":"v0.9.1"}}}\n'
        ]
        
        mock_process.stdout.readline = AsyncMock(side_effect=responses)

        result = await self.probe._initialize_mcp_session(mock_process)

        # Should successfully parse the JSON response despite non-JSON lines
        assert result is not None
        assert result["protocolVersion"] == "2024-11-05"
        assert result["serverInfo"]["name"] == "github-mcp-server"

    @pytest.mark.asyncio
    async def test_list_tools_json_parsing_robustness(self):
        """Test that tools listing can handle non-JSON lines in output."""
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        # Simulate mixed output for tools list
        responses = [
            b"Loading tools...\n",  # Non-JSON message
            b'{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"create_repository","description":"Create repos"},{"name":"search_repositories","description":"Search repos"}]}}\n'
        ]
        
        mock_process.stdout.readline = AsyncMock(side_effect=responses)

        result = await self.probe._list_tools(mock_process)

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "create_repository"
        assert result[1]["name"] == "search_repositories"

    @pytest.mark.asyncio
    async def test_discover_tools_from_docker_environment_variables(self):
        """Test that Docker discovery properly sets environment variables."""
        with patch('asyncio.create_subprocess_exec') as mock_create_process:
            mock_process = AsyncMock()
            mock_process.returncode = None
            mock_create_process.return_value = mock_process

            # Mock the MCP communication
            with patch.object(self.probe, 'discover_tools_from_command') as mock_discover:
                mock_discover.return_value = {
                    "tools": [{"name": "test_tool"}],
                    "discovery_method": "mcp_client"
                }

                env_vars = {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token",
                    "MCP_TRANSPORT": "stdio",
                    "GITHUB_TOOLSET": "all"
                }

                result = await self.probe.discover_tools_from_docker_mcp(
                    "dataeverything/mcp-github:latest",
                    env_vars=env_vars
                )

                # Verify the docker command includes environment variables
                args, kwargs = mock_discover.call_args
                docker_cmd = args[0]
                
                assert "docker" in docker_cmd
                assert "run" in docker_cmd
                assert "--rm" in docker_cmd
                assert "-i" in docker_cmd
                
                # Check environment variables are included
                env_args = []
                for i, arg in enumerate(docker_cmd):
                    if arg == "-e":
                        env_args.append(docker_cmd[i + 1])
                
                assert "GITHUB_PERSONAL_ACCESS_TOKEN=test_token" in env_args
                assert "MCP_TRANSPORT=stdio" in env_args
                assert "GITHUB_TOOLSET=all" in env_args

    @pytest.mark.asyncio
    async def test_mcp_protocol_version_compatibility(self):
        """Test that the correct MCP protocol version is used."""
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = AsyncMock()

        # Capture the request sent to verify protocol version
        written_data = []
        
        def capture_write(data):
            written_data.append(data)
            
        mock_process.stdin.write = capture_write
        mock_process.stdin.drain = AsyncMock()

        # Mock successful response
        mock_process.stdout.readline = AsyncMock(return_value=b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n')

        await self.probe._initialize_mcp_session(mock_process)

        # Verify the correct protocol version was sent
        assert len(written_data) == 1
        request = json.loads(written_data[0].decode())
        assert request["params"]["protocolVersion"] == "2024-11-05"

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test proper timeout handling in MCP communication."""
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        # Simulate timeout
        mock_process.stdout.readline = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await self.probe._initialize_mcp_session(mock_process)

        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_json_handling(self):
        """Test handling of malformed JSON responses."""
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        # Simulate malformed JSON responses
        responses = [
            b"Starting server...\n",
            b'{"jsonrpc":"2.0","id":1,"result":{"incomplete":}\n',  # Malformed JSON
            b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n'  # Valid JSON
        ]
        
        mock_process.stdout.readline = AsyncMock(side_effect=responses)

        result = await self.probe._initialize_mcp_session(mock_process)

        # Should successfully parse the valid JSON despite malformed ones
        assert result is not None
        assert result["protocolVersion"] == "2024-11-05"

    @pytest.mark.asyncio
    async def test_no_valid_json_response(self):
        """Test handling when no valid JSON response is found."""
        mock_process = MagicMock()
        mock_process.stdin = AsyncMock()
        mock_process.stdout = AsyncMock()

        # Only non-JSON responses
        responses = [
            b"Starting server...\n",
            b"Server ready\n",
            b"Waiting for input\n",
            b"Invalid JSON here\n",
            b"Still no JSON\n"
        ]
        
        mock_process.stdout.readline = AsyncMock(side_effect=responses)

        result = await self.probe._initialize_mcp_session(mock_process)

        assert result is None

    def test_synchronous_wrapper_functionality(self):
        """Test the synchronous wrapper for Docker discovery."""
        with patch.object(self.probe, 'discover_tools_from_docker_mcp') as mock_async:
            mock_async.return_value = {
                "tools": [{"name": "sync_test_tool"}],
                "discovery_method": "mcp_client"
            }

            result = self.probe.discover_tools_from_docker_sync(
                "test/image:latest",
                args=["stdio"],
                env_vars={"TEST_VAR": "value"}
            )

            assert result is not None
            assert result["tools"][0]["name"] == "sync_test_tool"
            mock_async.assert_called_once_with("test/image:latest", ["stdio"], {"TEST_VAR": "value"})


@pytest.mark.integration
class TestMCPClientProbeIntegration:
    """Integration tests for MCP client probe."""

    def setup_method(self):
        """Set up integration test environment."""
        self.probe = MCPClientProbe(timeout=10)

    @pytest.mark.skip(reason="Integration test requires Docker environment")
    def test_demo_server_stdio_discovery(self):
        """Test MCP discovery with demo server (requires --run-integration)."""
        # Test with demo server which should be more reliable
        env_vars = {
            "MCP_TRANSPORT": "stdio",
            "MCP_HELLO_FROM": "Test Platform"
        }

        result = self.probe.discover_tools_from_docker_sync(
            "dataeverything/mcp-demo:latest",
            env_vars=env_vars
        )

        if result:  # Only assert if discovery succeeded
            assert "tools" in result
            assert result["discovery_method"] == "mcp_client"
            # Demo server should have at least one tool
            assert len(result["tools"]) >= 1
