"""
Unit tests for MCP Client Probe Docker functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from mcp_template.tools.mcp_client_probe import MCPClientProbe


class TestMCPClientProbeDocker:
    """Test MCP Client Probe Docker integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe(timeout=5)

    @pytest.mark.asyncio
    @patch('mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_command')
    async def test_discover_tools_from_docker_mcp_with_env_vars(self, mock_discover_command):
        """Test Docker MCP discovery with environment variables."""
        mock_discover_command.return_value = {
            "tools": [{"name": "test_tool", "description": "Test", "category": "mcp", "parameters": {}}],
            "discovery_method": "mcp_client"
        }

        result = await self.probe.discover_tools_from_docker_mcp(
            "test/image:latest",
            args=["stdio"],
            env_vars={"API_KEY": "secret", "LOG_LEVEL": "DEBUG"}
        )

        # Verify discover_tools_from_command was called with correct Docker command
        mock_discover_command.assert_called_once()
        docker_cmd = mock_discover_command.call_args[0][0]
        
        # Check Docker command structure
        assert "docker" in docker_cmd
        assert "run" in docker_cmd
        assert "--rm" in docker_cmd
        assert "-i" in docker_cmd
        assert "-e" in docker_cmd
        assert "API_KEY=secret" in docker_cmd
        assert "LOG_LEVEL=DEBUG" in docker_cmd
        assert "test/image:latest" in docker_cmd
        assert "stdio" in docker_cmd

        assert result is not None
        assert result["tools"][0]["name"] == "test_tool"

    @pytest.mark.asyncio
    @patch('mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_command')
    async def test_discover_tools_from_docker_github_auto_stdio(self, mock_discover_command):
        """Test that GitHub images automatically get 'stdio' command."""
        mock_discover_command.return_value = {
            "tools": [{"name": "github_tool", "description": "GitHub", "category": "mcp", "parameters": {}}],
            "discovery_method": "mcp_client"
        }

        result = await self.probe.discover_tools_from_docker_mcp(
            "ghcr.io/github/github-mcp-server:0.9.1",
            args=None,  # No args provided
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "token"}
        )

        # Verify discover_tools_from_command was called
        mock_discover_command.assert_called_once()
        docker_cmd = mock_discover_command.call_args[0][0]
        
        # Should automatically add 'stdio' for GitHub image
        assert "stdio" in docker_cmd
        assert "ghcr.io/github/github-mcp-server:0.9.1" in docker_cmd

    @pytest.mark.asyncio
    @patch('mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_command')
    async def test_discover_tools_from_docker_with_custom_args(self, mock_discover_command):
        """Test Docker discovery with custom arguments."""
        mock_discover_command.return_value = {
            "tools": [{"name": "custom_tool", "description": "Custom", "category": "mcp", "parameters": {}}],
            "discovery_method": "mcp_client"
        }

        result = await self.probe.discover_tools_from_docker_mcp(
            "custom/server:latest",
            args=["--mode", "stdio", "--verbose"],
            env_vars={"CONFIG": "production"}
        )

        mock_discover_command.assert_called_once()
        docker_cmd = mock_discover_command.call_args[0][0]
        
        # Should use provided args instead of auto-adding stdio
        assert "--mode" in docker_cmd
        assert "--verbose" in docker_cmd
        assert "custom/server:latest" in docker_cmd

    def test_discover_tools_from_docker_sync_wrapper(self):
        """Test synchronous wrapper for Docker discovery."""
        with patch.object(self.probe, 'discover_tools_from_docker_mcp') as mock_async:
            mock_async.return_value = asyncio.coroutine(lambda: {
                "tools": [{"name": "sync_tool", "description": "Sync", "category": "mcp", "parameters": {}}],
                "discovery_method": "mcp_client"
            })()

            result = self.probe.discover_tools_from_docker_sync(
                "test/image:latest",
                args=["stdio"],
                env_vars={"TEST": "value"}
            )

            # Verify async method was called with correct arguments
            mock_async.assert_called_once_with(
                "test/image:latest",
                ["stdio"],
                {"TEST": "value"}
            )

    @pytest.mark.asyncio
    @patch('mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_command')
    async def test_discover_tools_error_handling(self, mock_discover_command):
        """Test error handling in Docker discovery."""
        mock_discover_command.side_effect = Exception("Docker error")

        result = await self.probe.discover_tools_from_docker_mcp(
            "failing/image:latest",
            env_vars={"KEY": "value"}
        )

        # Should return None on error
        assert result is None

    @pytest.mark.asyncio
    @patch('mcp_template.tools.mcp_client_probe.MCPClientProbe.discover_tools_from_command')
    async def test_discover_tools_no_env_vars(self, mock_discover_command):
        """Test Docker discovery without environment variables."""
        mock_discover_command.return_value = {
            "tools": [{"name": "no_env_tool", "description": "No env", "category": "mcp", "parameters": {}}],
            "discovery_method": "mcp_client"
        }

        result = await self.probe.discover_tools_from_docker_mcp(
            "simple/image:latest",
            args=["stdio"],
            env_vars=None
        )

        mock_discover_command.assert_called_once()
        docker_cmd = mock_discover_command.call_args[0][0]
        
        # Should not have any -e flags for environment variables
        env_flags = [i for i, arg in enumerate(docker_cmd) if arg == "-e"]
        assert len(env_flags) == 0

    @pytest.mark.asyncio
    async def test_container_cleanup_logic(self):
        """Test that container cleanup is attempted on completion."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock the cleanup subprocess
            mock_process = AsyncMock()
            mock_process.wait.return_value = None
            mock_subprocess.return_value = mock_process

            # Mock the main discovery to fail so cleanup is triggered
            with patch.object(self.probe, 'discover_tools_from_command', side_effect=Exception("Test error")):
                result = await self.probe.discover_tools_from_docker_mcp(
                    "test/image:latest",
                    env_vars={"TEST": "value"}
                )

                # Should return None due to error
                assert result is None

                # Verify cleanup subprocess was called
                mock_subprocess.assert_called()
                cleanup_call = mock_subprocess.call_args_list[-1]  # Last call should be cleanup
                cleanup_cmd = cleanup_call[0]
                
                assert "docker" in cleanup_cmd
                assert "stop" in cleanup_cmd


class TestMCPClientProbeProtocol:
    """Test MCP protocol communication in client probe."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = MCPClientProbe(timeout=5)

    def test_normalize_mcp_tools(self):
        """Test MCP tools normalization."""
        mcp_tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    }
                }
            },
            {
                "name": "minimal_tool",
                # Missing description and inputSchema
            }
        ]

        normalized = self.probe._normalize_mcp_tools(mcp_tools)

        assert len(normalized) == 2
        
        # First tool - complete
        assert normalized[0]["name"] == "test_tool"
        assert normalized[0]["description"] == "A test tool"
        assert normalized[0]["category"] == "mcp"
        assert "input_schema" in normalized[0]["mcp_info"]
        assert normalized[0]["mcp_info"]["input_schema"]["type"] == "object"
        
        # Second tool - minimal
        assert normalized[1]["name"] == "minimal_tool"
        assert normalized[1]["description"] == "No description available"
        assert normalized[1]["category"] == "mcp"

    def test_normalize_mcp_tools_error_handling(self):
        """Test error handling in MCP tools normalization."""
        mcp_tools = [
            {"name": "good_tool", "description": "Good"},
            None,  # Invalid tool
            {"description": "Missing name"},  # Missing name
            {"name": "another_good_tool", "description": "Also good"}
        ]

        normalized = self.probe._normalize_mcp_tools(mcp_tools)

        # Should skip invalid tools and continue with valid ones
        # None is skipped, but {"description": "Missing name"} becomes {"name": "unknown", ...}
        assert len(normalized) == 3  # good_tool, unknown (missing name), another_good_tool
        assert normalized[0]["name"] == "good_tool"
        assert normalized[1]["name"] == "unknown"  # The tool with missing name
        assert normalized[2]["name"] == "another_good_tool"

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_initialize_mcp_session_success(self, mock_subprocess):
        """Test successful MCP session initialization."""
        # Mock process with successful initialization response
        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            return_value=b'{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26","capabilities":{"tools":{}},"serverInfo":{"name":"test-server","version":"1.0.0"}}}\n'
        )
        mock_subprocess.return_value = mock_process

        result = await self.probe._initialize_mcp_session(mock_process)

        # Verify initialization request was sent
        mock_process.stdin.write.assert_called_once()
        written_data = mock_process.stdin.write.call_args[0][0].decode()
        assert '"method": "initialize"' in written_data
        assert '"protocolVersion": "2025-06-18"' in written_data

        # Verify result
        assert result is not None
        assert result["protocolVersion"] == "2025-03-26"
        assert "serverInfo" in result

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_initialize_mcp_session_error_response(self, mock_subprocess):
        """Test MCP session initialization with error response."""
        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            return_value=b'{"jsonrpc":"2.0","id":1,"error":{"code":-1,"message":"Initialization failed"}}\n'
        )
        mock_subprocess.return_value = mock_process

        result = await self.probe._initialize_mcp_session(mock_process)

        # Should return None on error
        assert result is None

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_list_tools_success(self, mock_subprocess):
        """Test successful tools listing."""
        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(
            return_value=b'{"jsonrpc":"2.0","id":2,"result":{"tools":[{"name":"test_tool","description":"A test tool"}]}}\n'
        )
        mock_subprocess.return_value = mock_process

        result = await self.probe._list_tools(mock_process)

        # Verify tools/list request was sent
        mock_process.stdin.write.assert_called_once()
        written_data = mock_process.stdin.write.call_args[0][0].decode()
        assert '"method": "tools/list"' in written_data

        # Verify result
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "test_tool"

    @pytest.mark.asyncio
    @patch('asyncio.create_subprocess_exec')
    async def test_list_tools_timeout(self, mock_subprocess):
        """Test tools listing with timeout."""
        mock_process = AsyncMock()
        mock_process.stdin.write = Mock()
        mock_process.stdin.drain = AsyncMock()
        mock_process.stdout.readline = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        result = await self.probe._list_tools(mock_process)

        # Should return None on timeout
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__])
