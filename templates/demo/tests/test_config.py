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
        assert config.log_level == "info"

    def test_config_dict_override(self):
        """Test configuration override with config_dict."""
        config_dict = {"hello_from": "Test Server"}
        config = DemoServerConfig(config_dict).get_template_config()
        assert config.get("hello_from") == "Test Server", "Config dict override failed"

    @patch.dict(
        os.environ, {"MCP_HELLO_FROM": "Environment Server", "MCP_LOG_LEVEL": "warning"}
    )
    def test_environment_variables(self):
        """Test configuration from environment variables."""
        config = DemoServerConfig()
        assert config.log_level == "warning"

    @patch.dict(os.environ, {"MCP_HELLO_FROM": "TEST SERVER FROM ENV"})
    def test_config_dict_precedence_over_env(self):
        """Test that config_dict takes precedence over environment."""

        config_dict = {"hello_from": "Config Dict Server"}
        config = DemoServerConfig(config_dict).get_template_config()
        assert (
            config.get("hello_from") == "Config Dict Server"
        ), "Config dict should override"

    def test_invalid_log_level_validation(self):
        """Test validation of invalid log level."""
        config_dict = {"log_level": "invalid"}
        config = DemoServerConfig(config_dict)

        # Should default to "info" for invalid log level
        assert config.log_level == "info"

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        config = DemoServerConfig()

        assert config.logger is not None
        assert config.logger.name == "config"
