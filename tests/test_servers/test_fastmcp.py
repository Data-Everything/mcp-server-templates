#!/usr/bin/env python3
"""
Test suite for the BaseFastMCP class.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.servers.fastmcp import BaseFastMCP


class TestBaseFastMCP:
    """Test the BaseFastMCP class."""

    def test_initialization_with_defaults(self):
        """Test BaseFastMCP initialization with default configuration."""
        try:
            server = BaseFastMCP("test-server")

            assert server.name == "test-server"
            assert server.config == {}

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    def test_initialization_with_config(self):
        """Test BaseFastMCP initialization with custom configuration."""
        try:

            config = {"log_level": "debug", "custom_setting": "value"}
            server = BaseFastMCP("test-server", config)

            assert server.name == "test-server"
            assert server.config == config

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    @patch("mcp_template.servers.fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_get_tool_names(self, mock_fastmcp):
        """Test get_tool_names method."""
        mock_instance = Mock()
        mock_instance.get_tools = AsyncMock(
            return_value={
                "tool1": Mock(),
                "tool2": Mock(),
            }
        )
        mock_fastmcp.return_value = mock_instance

        try:

            server = BaseFastMCP("test-server")
            # Manually set the mock instance methods
            server.get_tools = mock_instance.get_tools

            tools = await server.get_tool_names()
            assert tools == ["tool1", "tool2"]

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    @patch("mcp_template.servers.fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_get_tool_info(self, mock_fastmcp):
        """Test get_tool_info method."""
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "Test tool description"
        mock_tool.parameters = {"type": "object"}
        mock_tool.enabled = True

        mock_instance = Mock()
        mock_instance.get_tools = AsyncMock(return_value={"test_tool": mock_tool})
        mock_fastmcp.return_value = mock_instance

        try:

            server = BaseFastMCP("test-server")
            # Manually set the mock instance methods
            server.get_tools = mock_instance.get_tools

            tool_info = await server.get_tool_info("test_tool")
            assert tool_info["name"] == "test_tool"
            assert tool_info["description"] == "Test tool description"
            assert tool_info["parameters"] == {"type": "object"}
            assert tool_info["enabled"] is True

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    @patch("mcp_template.servers.fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_get_tool_info_not_found(self, mock_fastmcp):
        """Test get_tool_info method with non-existent tool."""
        mock_instance = Mock()
        mock_instance.get_tools = AsyncMock(return_value={})
        mock_fastmcp.return_value = mock_instance

        try:

            server = BaseFastMCP("test-server")
            # Manually set the mock instance methods
            server.get_tools = mock_instance.get_tools

            tool_info = await server.get_tool_info("nonexistent_tool")
            assert tool_info is None

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    @patch("mcp_template.servers.fastmcp.FastMCP")
    @pytest.mark.asyncio
    async def test_get_server_info(self, mock_fastmcp):
        """Test get_server_info method."""
        mock_instance = Mock()
        mock_instance.get_tools = AsyncMock(
            return_value={
                "tool1": Mock(),
                "tool2": Mock(),
            }
        )
        mock_fastmcp.return_value = mock_instance

        try:
            config = {"setting": "value"}
            server = BaseFastMCP("test-server", config)
            # Manually set the mock instance methods
            server.get_tools = mock_instance.get_tools

            server_info = await server.get_server_info()
            assert server_info["name"] == "test-server"
            assert server_info["config"] == config
            assert server_info["tools"] == ["tool1", "tool2"]

        except ImportError:
            pytest.skip("FastMCP not available in test environment")

    def test_fastmcp_not_available(self):
        """Test that proper error is raised when FastMCP is not available."""
        with patch("mcp_template.servers.fastmcp.FastMCP", None):
            try:
                with pytest.raises(ImportError, match="FastMCP is required"):
                    BaseFastMCP("test-server")

            except ImportError:
                pytest.skip("Cannot test when module import fails")

    @patch("mcp_template.servers.fastmcp.FastMCP")
    def test_logging_setup(self, mock_fastmcp):
        """Test that logging is properly configured."""
        mock_instance = Mock()
        mock_fastmcp.return_value = mock_instance

        try:
            with patch(
                "mcp_template.servers.base.logging.basicConfig"
            ) as mock_basic_config:
                config = {"log_level": "debug"}
                BaseFastMCP("test-server", config)

                # Verify basicConfig was called
                mock_basic_config.assert_called_once()
                call_kwargs = mock_basic_config.call_args[1]
                assert "level" in call_kwargs
                assert "format" in call_kwargs

        except ImportError:
            pytest.skip("FastMCP not available in test environment")
