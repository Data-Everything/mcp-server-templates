"""Unit tests for the demo server configuration."""

import os
from unittest.mock import patch

import pytest
from server import DemoServerConfig


class TestDemoServerConfig:
    """Test cases for DemoServerConfig."""

    def test_default_configuration(self, clean_env):
        """Test default configuration values."""
        config = DemoServerConfig()

        assert config.hello_from == "MCP Platform"
        assert config.logger.name == "demo-server"

    def test_environment_variable_configuration(self, mock_env_vars):
        """Test configuration from environment variables."""
        config = DemoServerConfig()

        assert config.hello_from == "Test Server"

    def test_custom_hello_from(self, monkeypatch):
        """Test custom hello_from configuration."""
        monkeypatch.setenv("MCP_HELLO_FROM", "Custom Bot")

        config = DemoServerConfig()
        assert config.hello_from == "Custom Bot"

    def test_log_level_configuration(self, monkeypatch):
        """Test log level configuration."""
        monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")

        config = DemoServerConfig()
        # Logger should be configured with DEBUG level
        assert config.logger.level <= 10  # DEBUG is 10

    def test_invalid_log_level_fallback(self, monkeypatch):
        """Test that invalid log level falls back gracefully."""
        monkeypatch.setenv("MCP_LOG_LEVEL", "INVALID")

        # Should not raise an exception
        config = DemoServerConfig()
        assert config.hello_from == "MCP Platform"

    def test_empty_hello_from(self, monkeypatch):
        """Test empty hello_from environment variable."""
        monkeypatch.setenv("MCP_HELLO_FROM", "")

        config = DemoServerConfig()
        assert config.hello_from == ""  # Should accept empty string
