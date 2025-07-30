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


class TestProcessNestedConfig:
    """Test the _process_nested_config method and type coercion."""

    def setup_method(self):
        """Setup for each test method."""
        # Mock template data
        self.mock_template_data = {
            "config_schema": {
                "properties": {
                    "hello_from": {
                        "type": "string",
                        "default": "MCP Platform",
                        "env_mapping": "MCP_HELLO_FROM",
                    },
                    "log_level": {
                        "type": "string",
                        "default": "info",
                        "env_mapping": "MCP_LOG_LEVEL",
                    },
                    "debug_mode": {
                        "type": "boolean",
                        "default": False,
                        "env_mapping": "MCP_DEBUG_MODE",
                    },
                    "max_connections": {
                        "type": "integer",
                        "default": 10,
                        "env_mapping": "MCP_MAX_CONNECTIONS",
                    },
                    "timeout_seconds": {
                        "type": "number",
                        "default": 30.5,
                        "env_mapping": "MCP_TIMEOUT_SECONDS",
                    },
                    "allowed_hosts": {
                        "type": "array",
                        "default": ["localhost"],
                        "env_mapping": "MCP_ALLOWED_HOSTS",
                        "env_separator": ",",
                    },
                    "metadata": {
                        "type": "object",
                        "default": {},
                        "env_mapping": "MCP_METADATA",
                    },
                }
            }
        }

    def test_process_nested_config_simple(self):
        """Test processing simple double underscore notation."""
        config_dict = {
            "demo__hello_from": "Custom Server",
            "template__log_level": "debug",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should process template-level overrides
            assert config.config_dict["hello_from"] == "Custom Server"
            assert config.config_dict["log_level"] == "debug"

    def test_process_nested_config_deep(self):
        """Test processing deep nested double underscore notation."""
        config_dict = {
            "system__config__debug_mode": "true",
            "app__settings__timeout": "45.0",
            "server__network__max_connections": "20",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should process deep nested configs
            # Config properties get their prefixes stripped
            assert (
                config.config_dict["debug_mode"] is True
            )  # Recognized as config property, type coerced
            assert (
                config.config_dict["max_connections"] == 20
            )  # Recognized as config property, type coerced
            # Non-config properties keep their nested structure
            assert config.config_dict["app_settings_timeout"] == "45.0"

    def test_type_coercion_boolean(self):
        """Test boolean type coercion."""
        config_dict = {
            "debug_mode": "true",
            "MCP_DEBUG_MODE": "false",  # Test env_mapping lookup too
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert config.config_dict["debug_mode"] is True
            assert config.config_dict["MCP_DEBUG_MODE"] is False

    def test_type_coercion_integer(self):
        """Test integer type coercion."""
        config_dict = {"max_connections": "25"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert config.config_dict["max_connections"] == 25
            assert isinstance(config.config_dict["max_connections"], int)

    def test_type_coercion_number(self):
        """Test number (float) type coercion."""
        config_dict = {"timeout_seconds": "45.5"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert abs(config.config_dict["timeout_seconds"] - 45.5) < 0.001
            assert isinstance(config.config_dict["timeout_seconds"], float)

    def test_type_coercion_array_json(self):
        """Test array type coercion from JSON string."""
        config_dict = {"allowed_hosts": '["host1", "host2", "host3"]'}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert config.config_dict["allowed_hosts"] == ["host1", "host2", "host3"]
            assert isinstance(config.config_dict["allowed_hosts"], list)

    def test_type_coercion_array_comma_separated(self):
        """Test array type coercion from comma-separated string."""
        config_dict = {"allowed_hosts": "host1,host2,host3"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert config.config_dict["allowed_hosts"] == ["host1", "host2", "host3"]
            assert isinstance(config.config_dict["allowed_hosts"], list)

    def test_type_coercion_object(self):
        """Test object type coercion from JSON string."""
        config_dict = {"metadata": '{"version": "1.0.0", "author": "Test"}'}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            expected = {"version": "1.0.0", "author": "Test"}
            assert config.config_dict["metadata"] == expected
            assert isinstance(config.config_dict["metadata"], dict)

    def test_type_coercion_fallback_on_error(self):
        """Test that invalid values fall back to original value."""
        config_dict = {
            "max_connections": "not_a_number",
            "debug_mode": "invalid_bool",
            "allowed_hosts": "[malformed json]",  # Malformed JSON array
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should fall back to original string values
            assert config.config_dict["max_connections"] == "not_a_number"
            assert config.config_dict["debug_mode"] == "invalid_bool"
            assert config.config_dict["allowed_hosts"] == "[malformed json]"

    def test_env_mapping_lookup(self):
        """Test that type coercion works with env_mapping lookup."""
        config_dict = {"MCP_DEBUG_MODE": "true", "MCP_MAX_CONNECTIONS": "15"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should find property by env_mapping and coerce types
            assert config.config_dict["MCP_DEBUG_MODE"] is True
            assert config.config_dict["MCP_MAX_CONNECTIONS"] == 15

    def test_unknown_properties_remain_unchanged(self):
        """Test that unknown properties are not type-coerced."""
        config_dict = {"unknown_property": "123", "another_unknown": "true"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should remain as strings since no schema is found
            assert config.config_dict["unknown_property"] == "123"
            assert config.config_dict["another_unknown"] == "true"

    def test_complex_nested_override_with_coercion(self):
        """Test complex nested override with type coercion."""
        config_dict = {
            "app__debug_mode": "true",
            "system__max_connections": "50",
            "network__log_level": "warning",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Should process nested keys and apply type coercion for schema properties
            assert config.config_dict["debug_mode"] is True  # schema property, coerced
            assert (
                config.config_dict["max_connections"] == 50
            )  # schema property, coerced
            assert (
                config.config_dict["log_level"] == "warning"
            )  # schema property, no coercion needed

    def test_custom_separator_array(self):
        """Test array parsing with custom separator."""
        # Add custom separator to mock template
        self.mock_template_data["config_schema"]["properties"]["custom_list"] = {
            "type": "array",
            "env_mapping": "MCP_CUSTOM_LIST",
            "env_separator": "|",
        }

        config_dict = {"custom_list": "item1|item2|item3"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            assert config.config_dict["custom_list"] == ["item1", "item2", "item3"]

    def test_empty_template_data_no_coercion(self):
        """Test that no coercion happens when template_data is empty."""
        config_dict = {"debug_mode": "true", "max_connections": "15"}

        with patch.object(DemoServerConfig, "_load_template", return_value={}):
            config = DemoServerConfig(config_dict)

            # Should remain as strings since no schema is available
            assert config.config_dict["debug_mode"] == "true"
            assert config.config_dict["max_connections"] == "15"


class TestTemplateOverrides:
    """Test template.json structure overrides using double underscore notation."""

    def setup_method(self):
        """Setup for each test method."""
        self.mock_template_data = {
            "name": "Demo Server",
            "version": "1.0.0",
            "tools": [
                {"name": "say_hello", "description": "Say hello", "enabled": True},
                {"name": "get_info", "description": "Get info", "enabled": False},
            ],
            "metadata": {"author": "Original Author", "category": "demo"},
            "config_schema": {
                "properties": {
                    "hello_from": {
                        "type": "string",
                        "default": "MCP Platform",
                        "env_mapping": "MCP_HELLO_FROM",
                    }
                }
            },
        }

    def test_simple_template_override(self):
        """Test simple template property override."""
        config_dict = {"name": "Custom Demo Server", "version": "2.0.0"}

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            assert template_data["name"] == "Custom Demo Server"
            assert template_data["version"] == "2.0.0"

    def test_nested_tool_override(self):
        """Test overriding nested tool properties."""
        config_dict = {
            "tools__0__name": "custom_hello",
            "tools__0__enabled": "false",
            "tools__1__description": "Custom get info tool",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            assert template_data["tools"][0]["name"] == "custom_hello"
            assert template_data["tools"][0]["enabled"] is False
            assert template_data["tools"][1]["description"] == "Custom get info tool"

    def test_deep_nested_metadata_override(self):
        """Test deep nested metadata overrides."""
        config_dict = {
            "metadata__author": "New Author",
            "metadata__custom__field": "custom_value",
            "metadata__nested__deep__property": "deep_value",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            assert template_data["metadata"]["author"] == "New Author"
            assert template_data["metadata"]["custom"]["field"] == "custom_value"
            assert (
                template_data["metadata"]["nested"]["deep"]["property"] == "deep_value"
            )

    def test_array_creation_override(self):
        """Test creating new array elements through overrides."""
        config_dict = {
            "tools__2__name": "new_tool",
            "tools__2__description": "A newly created tool",
            "tools__2__enabled": "true",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            # Should extend the tools array to include index 2
            assert len(template_data["tools"]) >= 3
            assert template_data["tools"][2]["name"] == "new_tool"
            assert template_data["tools"][2]["description"] == "A newly created tool"
            assert template_data["tools"][2]["enabled"] is True

    def test_json_object_override(self):
        """Test overriding with JSON object strings."""
        config_dict = {
            "metadata__config": '{"timeout": 30, "retry": true}',
            "tools__0__parameters": '["name", "message"]',
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            expected_config = {"timeout": 30, "retry": True}
            expected_params = ["name", "message"]

            assert template_data["metadata"]["config"] == expected_config
            assert template_data["tools"][0]["parameters"] == expected_params

    def test_numeric_type_inference(self):
        """Test automatic type inference for numeric values."""
        config_dict = {
            "metadata__version_number": "123",
            "metadata__rating": "4.5",
            "tools__0__timeout": "30",
            "tools__0__max_retries": "5",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            assert template_data["metadata"]["version_number"] == 123
            assert abs(template_data["metadata"]["rating"] - 4.5) < 0.001
            assert template_data["tools"][0]["timeout"] == 30
            assert template_data["tools"][0]["max_retries"] == 5

    def test_boolean_type_inference(self):
        """Test automatic type inference for boolean values."""
        config_dict = {
            "tools__0__enabled": "false",
            "tools__1__enabled": "true",
            "metadata__deprecated": "false",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            assert template_data["tools"][0]["enabled"] is False
            assert template_data["tools"][1]["enabled"] is True
            assert template_data["metadata"]["deprecated"] is False

    def test_complex_nested_structure_creation(self):
        """Test creating complex nested structures."""
        config_dict = {
            "servers__0__config__database__host": "localhost",
            "servers__0__config__database__port": "5432",
            "servers__0__config__redis__host": "redis-server",
            "servers__0__config__redis__port": "6379",
            "servers__1__name": "backup_server",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            # Should create the entire nested structure
            assert (
                template_data["servers"][0]["config"]["database"]["host"] == "localhost"
            )
            assert template_data["servers"][0]["config"]["database"]["port"] == 5432
            assert (
                template_data["servers"][0]["config"]["redis"]["host"] == "redis-server"
            )
            assert template_data["servers"][0]["config"]["redis"]["port"] == 6379
            assert template_data["servers"][1]["name"] == "backup_server"

    def test_override_vs_config_distinction(self):
        """Test that template overrides and config properties are handled separately."""
        config_dict = {
            # This should be treated as a config property (has env_mapping)
            "hello_from": "Config Hello",
            # This should be treated as template override (no env_mapping)
            "tools__0__custom_field": "template_override",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)

            # Config property should be in config_dict
            assert config.config_dict["hello_from"] == "Config Hello"

            # Template override should modify the template structure
            template_data = config.get_template_data()
            assert template_data["tools"][0]["custom_field"] == "template_override"

    def test_malformed_json_fallback(self):
        """Test that malformed JSON falls back to string value."""
        config_dict = {
            "metadata__config": '{"malformed": json}',
            "tools__0__bad_array": "[invalid, json]",
        }

        with patch.object(
            DemoServerConfig, "_load_template", return_value=self.mock_template_data
        ):
            config = DemoServerConfig(config_dict)
            template_data = config.get_template_data()

            # Should fall back to string values
            assert template_data["metadata"]["config"] == '{"malformed": json}'
            assert template_data["tools"][0]["bad_array"] == "[invalid, json]"
