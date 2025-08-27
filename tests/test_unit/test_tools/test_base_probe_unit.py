"""
Unit tests for the base probe module (mcp_template.tools.base_probe).

Tests the abstract base class and shared functionality for MCP server tool discovery.
"""

import asyncio
import os
from unittest.mock import AsyncMock, Mock, patch

import pytest

from mcp_template.tools.base_probe import (
    CONTAINER_HEALTH_CHECK_TIMEOUT,
    CONTAINER_PORT_RANGE,
    DISCOVERY_RETRIES,
    DISCOVERY_RETRY_SLEEP,
    DISCOVERY_TIMEOUT,
    BaseProbe,
)
from mcp_template.tools.mcp_client_probe import MCPClientProbe


class ConcreteProbe(BaseProbe):
    """Concrete implementation of BaseProbe for testing."""

    def discover_tools_from_image(
        self, image_name, server_args=None, env_vars=None, timeout=DISCOVERY_TIMEOUT
    ):
        """Concrete implementation for testing."""
        return {"tools": [], "image": image_name}


class TestBaseProbe:
    """Test the BaseProbe abstract base class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = ConcreteProbe()

    def test_init_creates_mcp_client(self):
        """Test that BaseProbe initialization creates an MCP client."""
        assert hasattr(self.probe, "mcp_client")
        assert isinstance(self.probe.mcp_client, MCPClientProbe)

    def test_discover_tools_from_image_abstract_method(self):
        """Test that discover_tools_from_image is abstract."""
        # Test that we can't instantiate BaseProbe directly
        with pytest.raises(TypeError):
            BaseProbe()

    def test_concrete_implementation_works(self):
        """Test that concrete implementation works."""
        result = self.probe.discover_tools_from_image("test-image")
        assert result is not None
        assert result["image"] == "test-image"
        assert "tools" in result

    @patch("mcp_template.tools.base_probe.MCPClientProbe")
    def test_mcp_client_initialization(self, mock_client_class):
        """Test MCP client is properly initialized."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        probe = ConcreteProbe()
        assert probe.mcp_client == mock_client
        mock_client_class.assert_called_once()


class TestBaseProbeConstants:
    """Test module-level constants and configuration."""

    def test_default_constants(self):
        """Test default values of module constants."""
        assert DISCOVERY_TIMEOUT == 60
        assert DISCOVERY_RETRIES == 3
        assert DISCOVERY_RETRY_SLEEP == 5
        assert CONTAINER_PORT_RANGE == (8000, 9000)
        assert CONTAINER_HEALTH_CHECK_TIMEOUT == 15

    @patch.dict(os.environ, {"MCP_DISCOVERY_TIMEOUT": "120"})
    def test_timeout_from_environment(self):
        """Test that timeout can be configured via environment."""
        # Re-import to get updated environment value
        import importlib

        from mcp_template.tools import base_probe

        importlib.reload(base_probe)

        assert base_probe.DISCOVERY_TIMEOUT == 120

    @patch.dict(os.environ, {"MCP_DISCOVERY_RETRIES": "5"})
    def test_retries_from_environment(self):
        """Test that retries can be configured via environment."""
        import importlib

        from mcp_template.tools import base_probe

        importlib.reload(base_probe)

        assert base_probe.DISCOVERY_RETRIES == 5

    @patch.dict(os.environ, {"MCP_DISCOVERY_RETRY_SLEEP": "10"})
    def test_retry_sleep_from_environment(self):
        """Test that retry sleep can be configured via environment."""
        import importlib

        from mcp_template.tools import base_probe

        importlib.reload(base_probe)

        assert base_probe.DISCOVERY_RETRY_SLEEP == 10

    @patch.dict(
        os.environ,
        {"MCP_DISCOVERY_TIMEOUT": "invalid", "MCP_DISCOVERY_RETRIES": "not_a_number"},
    )
    def test_invalid_environment_values(self):
        """Test handling of invalid environment values."""
        import importlib

        from mcp_template.tools import base_probe

        # Should fall back to defaults when env vars are invalid
        try:
            importlib.reload(base_probe)
            # If it doesn't raise, values should be defaults
            assert isinstance(base_probe.DISCOVERY_TIMEOUT, int)
            assert isinstance(base_probe.DISCOVERY_RETRIES, int)
        except ValueError:
            # This is expected behavior for invalid values
            pass


class TestBaseProbeInheritance:
    """Test inheritance behavior and abstract method enforcement."""

    def test_subclass_must_implement_abstract_method(self):
        """Test that subclasses must implement discover_tools_from_image."""

        class IncompleteProbe(BaseProbe):
            pass

        with pytest.raises(TypeError):
            IncompleteProbe()

    def test_subclass_with_implementation_works(self):
        """Test that subclass with proper implementation works."""

        class WorkingProbe(BaseProbe):
            def discover_tools_from_image(self, image_name, **kwargs):
                return {"working": True}

        probe = WorkingProbe()
        result = probe.discover_tools_from_image("test")
        assert result["working"] is True

    def test_multiple_inheritance_compatibility(self):
        """Test that BaseProbe works with multiple inheritance."""

        class Mixin:
            def extra_method(self):
                return "mixin"

        class MultiInheritanceProbe(BaseProbe, Mixin):
            def discover_tools_from_image(self, image_name, **kwargs):
                return {"multi": True}

        probe = MultiInheritanceProbe()
        assert probe.discover_tools_from_image("test")["multi"] is True
        assert probe.extra_method() == "mixin"


class TestBaseProbeIntegration:
    """Test integration aspects of BaseProbe."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = ConcreteProbe()

    @patch("mcp_template.tools.base_probe.MCPClientProbe")
    def test_mcp_client_interaction(self, mock_client_class):
        """Test interaction with MCP client."""
        mock_client = Mock()
        mock_client.discover_tools_from_command = AsyncMock(return_value={"tools": []})
        mock_client_class.return_value = mock_client

        probe = ConcreteProbe()
        assert probe.mcp_client == mock_client

    def test_method_signature_compatibility(self):
        """Test that method signatures are compatible across implementations."""
        # Test with minimal args
        result = self.probe.discover_tools_from_image("image")
        assert result is not None

        # Test with all optional args
        result = self.probe.discover_tools_from_image(
            "image",
            server_args=["--port", "8080"],
            env_vars={"VAR": "value"},
            timeout=30,
        )
        assert result is not None

    def test_error_handling_in_concrete_implementation(self):
        """Test error handling behavior."""

        class ErrorProbe(BaseProbe):
            def discover_tools_from_image(self, image_name, **kwargs):
                if image_name == "error":
                    raise Exception("Test error")
                return {"success": True}

        probe = ErrorProbe()

        # Normal case should work
        result = probe.discover_tools_from_image("normal")
        assert result["success"] is True

        # Error case should raise
        with pytest.raises(Exception, match="Test error"):
            probe.discover_tools_from_image("error")


class TestBaseProbeLogging:
    """Test logging behavior in BaseProbe."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = ConcreteProbe()

    @patch("mcp_template.tools.base_probe.logger")
    def test_logger_is_available(self, mock_logger):
        """Test that logger is properly imported and available."""
        # Import the module to trigger logger usage
        from mcp_template.tools.base_probe import logger

        assert logger is not None

    def test_logger_name(self):
        """Test that logger has correct name."""
        from mcp_template.tools.base_probe import logger

        assert logger.name == "mcp_template.tools.base_probe"


class TestBaseProbeDocumentation:
    """Test documentation and type hints."""

    def test_class_docstring(self):
        """Test that BaseProbe has proper documentation."""
        assert BaseProbe.__doc__ is not None
        assert "Base class for MCP server tool discovery probes" in BaseProbe.__doc__

    def test_abstract_method_docstring(self):
        """Test that abstract method has proper documentation."""
        assert BaseProbe.discover_tools_from_image.__doc__ is not None
        assert (
            "Discover tools from MCP server image"
            in BaseProbe.discover_tools_from_image.__doc__
        )

    def test_module_docstring(self):
        """Test that module has proper documentation."""
        from mcp_template.tools import base_probe

        assert base_probe.__doc__ is not None
        assert "Base probe for discovering MCP server tools" in base_probe.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
