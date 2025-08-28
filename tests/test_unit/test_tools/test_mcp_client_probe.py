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
        mock_process.returncode = None

        # Mock the MCP session methods
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch.object(self.probe, "_initialize_mcp_session") as mock_init:
                with patch.object(self.probe, "_list_tools") as mock_list:
                    mock_init.return_value = {
                        "serverInfo": {"name": "test-server", "version": "1.0"}
                    }
                    mock_list.return_value = [
                        {"name": "test_tool", "description": "Test tool"}
                    ]

                    result = await self.probe.discover_tools_from_command(
                        ["python", "-m", "test_server"]
                    )

                    assert result is not None
                    assert "tools" in result
                    assert result["tools"][0]["name"] == "test_tool"
                    assert result["server_info"]["name"] == "test-server"
                    mock_init.assert_called_once_with(mock_process)
                    mock_list.assert_called_once_with(mock_process)

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
        mock_process.returncode = None

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            with patch.object(self.probe, "_initialize_mcp_session", return_value={}):
                with patch.object(self.probe, "_list_tools", return_value=[]):
                    await self.probe.discover_tools_from_command(
                        ["python", "server.py"], working_dir="/app"
                    )

                    mock_exec.assert_called_once()
                    call_kwargs = mock_exec.call_args[1]
                    assert call_kwargs["cwd"] == "/app"

    @pytest.mark.asyncio
    async def test_discover_tools_from_command_timeout(self):
        """Test discovery with timeout during MCP session."""
        mock_process = Mock()
        mock_process.returncode = None
        mock_process.terminate = Mock()
        mock_process.wait = AsyncMock(return_value=0)

        # Mock the _initialize_mcp_session to raise timeout
        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with patch.object(
                self.probe,
                "_initialize_mcp_session",
                side_effect=asyncio.TimeoutError(),
            ):
                result = await self.probe.discover_tools_from_command(
                    ["slow", "server"]
                )

                assert result is None
                mock_process.terminate.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
