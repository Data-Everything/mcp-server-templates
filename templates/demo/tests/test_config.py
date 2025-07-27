#!/usr/bin/env python3
"""
Test suite for demo server configuration.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import DemoServerConfig
except ImportError:
    # Fallback for testing
    import importlib.util

    config_path = Path(__file__).parent.parent / "config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    DemoServerConfig = config_module.DemoServerConfig


class TestDemoServerConfig:
    """Test cases for DemoServerConfig."""

    def test_default_configuration(self):
        """Test default configuration values."""
        config = DemoServerConfig()

        assert config.hello_from == "MCP Platform"
        assert config.log_level == "info"

    def test_config_dict_override(self):
        """Test configuration override with config_dict."""
        config_dict = {"hello_from": "Test Server", "log_level": "debug"}
        config = DemoServerConfig(config_dict)

        assert config.hello_from == "Test Server"
        assert config.log_level == "debug"

    @patch.dict(
        os.environ, {"MCP_HELLO_FROM": "Environment Server", "MCP_LOG_LEVEL": "warning"}
    )
    def test_environment_variables(self):
        """Test configuration from environment variables."""
        config = DemoServerConfig()

        assert config.hello_from == "Environment Server"
        assert config.log_level == "warning"

    @patch.dict(
        os.environ, {"MCP_HELLO_FROM": "Environment Server", "MCP_LOG_LEVEL": "error"}
    )
    def test_config_dict_precedence_over_env(self):
        """Test that config_dict takes precedence over environment."""
        config_dict = {"hello_from": "Config Dict Server", "log_level": "debug"}
        config = DemoServerConfig(config_dict)

        assert config.hello_from == "Config Dict Server"
        assert config.log_level == "debug"

    def test_invalid_log_level_validation(self):
        """Test validation of invalid log level."""
        config_dict = {"log_level": "invalid"}
        config = DemoServerConfig(config_dict)

        # Should default to "info" for invalid log level
        assert config.log_level == "info"

    def test_to_dict(self):
        """Test configuration conversion to dictionary."""
        config_dict = {"hello_from": "Test Server", "log_level": "debug"}
        config = DemoServerConfig(config_dict)
        result = config.to_dict()

        expected = {"hello_from": "Test Server", "log_level": "debug"}
        assert result == expected

    def test_get_env_mappings(self):
        """Test environment variable mappings."""
        config = DemoServerConfig()
        mappings = config.get_env_mappings()

        expected = {"hello_from": "MCP_HELLO_FROM", "log_level": "MCP_LOG_LEVEL"}
        assert mappings == expected

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        config = DemoServerConfig()

        assert config.logger is not None
        assert config.logger.name == "config"
