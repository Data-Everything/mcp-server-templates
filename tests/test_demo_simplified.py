#!/usr/bin/env python3
"""
Simplified tests for demo template double underscore functionality.

Tests the two core patterns:
1. Standard config from template.json config_schema
2. Template data overrides via double underscore notation
"""

import pytest

from templates.demo.config import DemoServerConfig
from templates.demo.server import DemoMCPServer


class TestDemoSimplifiedConfig:
    """Test simplified double underscore configuration patterns."""

    def test_standard_config_usage(self):
        """Test standard configuration from config_schema works."""
        config_dict = {"hello_from": "Test Server", "log_level": "debug"}

        config = DemoServerConfig(config_dict=config_dict)
        template_config = config.get_template_config()

        assert template_config["hello_from"] == "Test Server"
        assert template_config["log_level"] == "debug"

    def test_template_data_override(self):
        """Test that double underscore notation can override template data."""
        config_dict = {
            "name": "Custom Server Name",
            "description": "Modified description",
            "tools__0__custom_field": "test_value",
        }

        config = DemoServerConfig(config_dict=config_dict)
        template_data = config.get_template_data()

        # Template-level overrides
        assert template_data["name"] == "Custom Server Name"
        assert template_data["description"] == "Modified description"

        # Nested tool override
        tools = template_data.get("tools", [])
        if len(tools) > 0:
            assert tools[0].get("custom_field") == "test_value"

    def test_server_uses_both_patterns(self):
        """Test that the server properly uses both config patterns."""
        config_dict = {
            # Standard config
            "hello_from": "Pattern Test Server",
            # Template override
            "name": "Overridden Server Name",
        }

        server = DemoMCPServer(config_dict=config_dict)

        # Standard config should be accessible
        assert server.config_data["hello_from"] == "Pattern Test Server"

        # Template data should reflect overrides
        assert server.template_data["name"] == "Overridden Server Name"

    def test_demonstrate_overrides_tool(self):
        """Test the demonstrate_overrides tool shows both patterns."""
        server = DemoMCPServer()

        result = server.demonstrate_overrides()

        assert "configuration_patterns" in result
        assert "pattern_1_standard_config" in result["configuration_patterns"]
        assert "pattern_2_template_overrides" in result["configuration_patterns"]

        # Check that examples are provided
        pattern1 = result["configuration_patterns"]["pattern_1_standard_config"]
        assert "examples" in pattern1
        assert any("--config" in example for example in pattern1["examples"])

        pattern2 = result["configuration_patterns"]["pattern_2_template_overrides"]
        assert "examples" in pattern2
        assert any("__" in example for example in pattern2["examples"])


if __name__ == "__main__":
    pytest.main([__file__])
