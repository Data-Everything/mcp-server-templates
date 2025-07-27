#!/usr/bin/env python3
"""
Comprehensive tests for mcp_template.base module.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestBaseMCPServer:
    """Test the BaseMCPServer abstract base class."""

    def setup_method(self):
        """Setup for each test method."""

        # Create a concrete implementation for testing
        class TestMCPServer:
            def __init__(self, name: str, config: Dict[str, Any] = None):
                from mcp_template.base import BaseMCPServer

                # Mock FastMCP to avoid import issues
                with patch("mcp_template.base.FastMCP") as mock_fastmcp:
                    mock_fastmcp.return_value = Mock()

                    # Create a test class that inherits from BaseMCPServer
                    class ConcreteServer(BaseMCPServer):
                        def register_tools(self):
                            """Concrete implementation of abstract method."""
                            pass

                    self.server = ConcreteServer(name, config)

        self.test_server_class = TestMCPServer

    @patch("mcp_template.base.FastMCP")
    def test_init_with_default_config(self, mock_fastmcp):
        """Test initialization with default configuration."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")

        assert server.name == "test-server"
        assert server.config == {}
        mock_fastmcp.assert_called_once_with(name="test-server")
        assert server.mcp == mock_mcp_instance

    @patch("mcp_template.base.FastMCP")
    def test_init_with_custom_config(self, mock_fastmcp):
        """Test initialization with custom configuration."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        config = {"log_level": "debug", "custom_setting": "value"}
        server = ConcreteServer("test-server", config)

        assert server.name == "test-server"
        assert server.config == config
        mock_fastmcp.assert_called_once_with(name="test-server")

    @patch("mcp_template.base.FastMCP", None)
    def test_init_without_fastmcp_raises_import_error(self):
        """Test that initialization fails gracefully when FastMCP is not available."""
        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        with pytest.raises(ImportError, match="FastMCP is required but not installed"):
            ConcreteServer("test-server")

    @patch("mcp_template.base.FastMCP")
    @patch("logging.basicConfig")
    def test_setup_logging_default(self, mock_basic_config, mock_fastmcp):
        """Test logging setup with default log level."""
        mock_fastmcp.return_value = Mock()

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")

        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @patch("mcp_template.base.FastMCP")
    @patch("logging.basicConfig")
    def test_setup_logging_custom_level(self, mock_basic_config, mock_fastmcp):
        """Test logging setup with custom log level."""
        mock_fastmcp.return_value = Mock()

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        config = {"log_level": "debug"}
        server = ConcreteServer("test-server", config)

        mock_basic_config.assert_called_once_with(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @patch("mcp_template.base.FastMCP")
    @patch("logging.basicConfig")
    def test_setup_logging_invalid_level(self, mock_basic_config, mock_fastmcp):
        """Test logging setup with invalid log level falls back to INFO."""
        mock_fastmcp.return_value = Mock()

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        config = {"log_level": "invalid"}
        server = ConcreteServer("test-server", config)

        mock_basic_config.assert_called_once_with(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    @patch("mcp_template.base.FastMCP")
    def test_run_http_transport(self, mock_fastmcp):
        """Test running server with HTTP transport."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")
        server.run(transport="http", host="localhost", port=8080)

        mock_mcp_instance.run.assert_called_once_with(
            transport="http", host="localhost", port=8080
        )

    @patch("mcp_template.base.FastMCP")
    def test_run_stdio_transport(self, mock_fastmcp):
        """Test running server with stdio transport."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")
        server.run(transport="stdio")

        mock_mcp_instance.run.assert_called_once_with(transport="stdio")

    @patch("mcp_template.base.FastMCP")
    def test_run_invalid_transport(self, mock_fastmcp):
        """Test running server with invalid transport raises ValueError."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")

        with pytest.raises(ValueError, match="Unsupported transport: invalid"):
            server.run(transport="invalid")

    @patch("mcp_template.base.FastMCP")
    def test_run_with_exception(self, mock_fastmcp):
        """Test that exceptions during server run are re-raised."""
        mock_mcp_instance = Mock()
        mock_mcp_instance.run.side_effect = Exception("Server failed")
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")

        with pytest.raises(Exception, match="Server failed"):
            server.run(transport="http")

    @patch("mcp_template.base.FastMCP")
    def test_get_server_info(self, mock_fastmcp):
        """Test getting server information."""
        mock_mcp_instance = Mock()
        # Fix: dir() should return a list, not a lambda
        mock_mcp_instance.__dir__ = Mock(
            return_value=["tool1", "tool2", "_private", "__dunder__"]
        )
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        config = {"setting1": "value1"}
        server = ConcreteServer("test-server", config)

        info = server.get_server_info()

        assert info["name"] == "test-server"
        assert info["config"] == config
        # Should only include public attributes (not starting with _)
        assert "tool1" in info["tools"]
        assert "tool2" in info["tools"]
        assert "_private" not in info["tools"]
        assert "__dunder__" not in info["tools"]

    def test_abstract_class_cannot_be_instantiated(self):
        """Test that BaseMCPServer cannot be instantiated directly."""
        from mcp_template.base import BaseMCPServer

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseMCPServer("test-server")

    @patch("mcp_template.base.FastMCP")
    def test_register_tools_is_called(self, mock_fastmcp):
        """Test that register_tools is called during initialization."""
        mock_fastmcp.return_value = Mock()

        from mcp_template.base import BaseMCPServer

        register_tools_called = False

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                nonlocal register_tools_called
                register_tools_called = True

        server = ConcreteServer("test-server")
        assert register_tools_called

    @patch("mcp_template.base.FastMCP")
    def test_run_with_additional_kwargs(self, mock_fastmcp):
        """Test running server with additional keyword arguments."""
        mock_mcp_instance = Mock()
        mock_fastmcp.return_value = mock_mcp_instance

        from mcp_template.base import BaseMCPServer

        class ConcreteServer(BaseMCPServer):
            def register_tools(self):
                pass

        server = ConcreteServer("test-server")
        server.run(
            transport="http",
            host="localhost",
            port=8080,
            debug=True,
            extra_param="value",
        )

        mock_mcp_instance.run.assert_called_once_with(
            transport="http",
            host="localhost",
            port=8080,
            debug=True,
            extra_param="value",
        )
