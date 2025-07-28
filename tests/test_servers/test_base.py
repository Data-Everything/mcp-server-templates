#!/usr/bin/env python3
"""
Test suite for the BaseFastMCP class.
"""

import sys
from logging import config
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.servers.base import BaseMCP


class TestBaseMCP:
    """Test the BaseMCP class."""

    def test_initialization_with_defaults(self):
        """Test BaseMCP initialization with default configuration."""

        try:
            server = BaseMCP("test-server")

            assert server.name == "test-server"
            assert server.config == {}

        except ImportError:
            pytest.skip("BaseMCP not available in test environment")

    def test_initialization_with_config(self):
        """Test BaseMCP initialization with custom configuration."""

        try:

            config = {"log_level": "debug", "custom_setting": "value"}
            server = BaseMCP("test-server", config)

            assert server.name == "test-server"
            assert server.config == config

        except ImportError:
            pytest.skip("BaseMCP not available in test environment")

    @patch("mcp_template.servers.base.BaseMCP")
    @pytest.mark.asyncio
    async def test_get_server_info(self, mock_basemcp):
        """Test get_server_info method."""

        mock_instance = Mock()
        mock_instance.get_tools = AsyncMock(
            return_value={
                "tool1": Mock(),
                "tool2": Mock(),
            }
        )
        mock_basemcp.return_value = mock_instance

        try:
            config = {"setting": "value"}
            server = BaseMCP("test-server", config)
            # Manually set the mock instance methods
            server.get_tools = mock_instance.get_tools

            server_info = await server.get_server_info()
            assert server_info["name"] == "test-server"
            assert server_info["config"] == config
            assert server_info["tools"] == []

        except ImportError:
            pytest.skip("BaseMCP not available in test environment")

    @patch("mcp_template.servers.base.BaseMCP")
    def test_logging_setup(self, mock_basemcp):
        """Test that logging is properly configured."""

        mock_instance = Mock()
        mock_basemcp.return_value = mock_instance

        try:

            with patch(
                "mcp_template.servers.base.logging.basicConfig"
            ) as mock_basic_config:
                config = {"log_level": "debug"}
                BaseMCP("test-server", config)

                # Verify basicConfig was called
                mock_basic_config.assert_called_once()
                call_kwargs = mock_basic_config.call_args[1]
                assert "level" in call_kwargs
                assert "format" in call_kwargs

        except ImportError:
            pytest.skip("FastMCP not available in test environment")
