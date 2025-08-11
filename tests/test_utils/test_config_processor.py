"""
Unit tests for the ConfigProcessor utility.

This module tests the unified configuration processing functionality that handles
merging configuration from multiple sources and processing volume mounts and command arguments.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import mock_open, patch

import pytest
import yaml

from mcp_template.utils.config_processor import ConfigProcessor


@pytest.mark.unit
class TestConfigProcessor:
    """Test ConfigProcessor class for unified configuration processing."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return {
            "config_schema": {
                "type": "object",
                "properties": {
                    "log_level": {
                        "type": "string",
                        "description": "Logging level",
                        "default": "INFO",
                        "env_mapping": "LOG_LEVEL",
                    },
                    "allowed_dirs": {
                        "type": "string",
                        "description": "Allowed directories",
                        "env_mapping": "ALLOWED_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    },
                    "read_only_mode": {
                        "type": "boolean",
                        "description": "Read-only mode",
                        "default": False,
                        "env_mapping": "READ_ONLY_MODE",
                    },
                    "port": {
                        "type": "integer",
                        "description": "Port number",
                        "default": 8080,
                        "env_mapping": "PORT",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in seconds",
                        "default": 30.0,
                        "env_mapping": "TIMEOUT",
                    },
                    "tags": {
                        "type": "array",
                        "description": "List of tags",
                        "env_mapping": "TAGS",
                    },
                },
                "required": ["allowed_dirs"],
            },
            "env_vars": {
                "LOG_LEVEL": "DEBUG",
                "DEFAULT_VALUE": "template_default",
            },
            "volumes": {
                "~/mcp-data": "/data",
            },
            "command": ["--template-arg"],
        }


@pytest.mark.unit
class TestConfigProcessorPrepareConfiguration:
    """Test ConfigProcessor.prepare_configuration method."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    @pytest.fixture
    def sample_template(self):
        """Create a sample template for testing."""
        return {
            "config_schema": {
                "properties": {
                    "log_level": {
                        "type": "string",
                        "env_mapping": "LOG_LEVEL",
                    },
                    "allowed_dirs": {
                        "type": "string",
                        "env_mapping": "ALLOWED_DIRS",
                    },
                }
            },
            "env_vars": {"LOG_LEVEL": "INFO"},
        }

    def test_prepare_configuration_template_defaults_only(
        self, config_processor, sample_template
    ):
        """Test configuration preparation with only template defaults."""
        result = config_processor.prepare_configuration(template=sample_template)

        assert result["LOG_LEVEL"] == "INFO"

    def test_prepare_configuration_with_session_config(
        self, config_processor, sample_template
    ):
        """Test configuration preparation with session config."""
        session_config = {"LOG_LEVEL": "DEBUG", "CUSTOM_VAR": "session_value"}

        result = config_processor.prepare_configuration(
            template=sample_template, session_config=session_config
        )

        assert result["LOG_LEVEL"] == "DEBUG"
        assert result["CUSTOM_VAR"] == "session_value"

    def test_prepare_configuration_with_config_values(
        self, config_processor, sample_template
    ):
        """Test configuration preparation with config values."""
        config_values = {"log_level": "WARNING", "allowed_dirs": "/tmp"}

        result = config_processor.prepare_configuration(
            template=sample_template, config_values=config_values
        )

        assert result["LOG_LEVEL"] == "WARNING"
        assert result["ALLOWED_DIRS"] == "/tmp"

    def test_prepare_configuration_with_env_vars(
        self, config_processor, sample_template
    ):
        """Test configuration preparation with environment variables."""
        env_vars = {"LOG_LEVEL": "ERROR", "CUSTOM_ENV": "env_value"}

        result = config_processor.prepare_configuration(
            template=sample_template, env_vars=env_vars
        )

        assert result["LOG_LEVEL"] == "ERROR"
        assert result["CUSTOM_ENV"] == "env_value"

    def test_prepare_configuration_priority_order(
        self, config_processor, sample_template
    ):
        """Test that configuration sources are merged in correct priority order."""
        session_config = {"LOG_LEVEL": "session", "session_only": "session"}
        config_values = {"log_level": "config", "config_only": "config"}
        env_vars = {"LOG_LEVEL": "env", "env_only": "env"}

        result = config_processor.prepare_configuration(
            template=sample_template,
            session_config=session_config,
            config_values=config_values,
            env_vars=env_vars,
        )

        # env_vars should have highest priority
        assert result["LOG_LEVEL"] == "env"
        assert result["session_only"] == "session"
        assert result["config_only"] == "config"
        assert result["env_only"] == "env"

    def test_prepare_configuration_with_config_file_json(self, config_processor):
        """Test configuration preparation with JSON config file."""
        template = {
            "config_schema": {
                "properties": {
                    "log_level": {"env_mapping": "LOG_LEVEL"},
                    "port": {"env_mapping": "PORT", "type": "integer"},
                }
            },
            "env_vars": {},
        }

        file_content = {"log_level": "DEBUG", "port": 9000}

        with patch("builtins.open", mock_open(read_data=json.dumps(file_content))):
            with patch("pathlib.Path.exists", return_value=True):
                result = config_processor.prepare_configuration(
                    template=template, config_file="config.json"
                )

                assert result["LOG_LEVEL"] == "DEBUG"
                assert result["PORT"] == "9000"  # Config file values become strings

    def test_prepare_configuration_with_config_file_yaml(self, config_processor):
        """Test configuration preparation with YAML config file."""
        template = {
            "config_schema": {
                "properties": {
                    "log_level": {"env_mapping": "LOG_LEVEL"},
                    "enable_feature": {
                        "env_mapping": "ENABLE_FEATURE",
                        "type": "boolean",
                    },
                }
            },
            "env_vars": {},
        }

        file_content = {"log_level": "WARNING", "enable_feature": True}

        with patch("builtins.open", mock_open(read_data=yaml.dump(file_content))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("yaml.safe_load", return_value=file_content):
                    result = config_processor.prepare_configuration(
                        template=template, config_file="config.yaml"
                    )

                    assert result["LOG_LEVEL"] == "WARNING"
                    assert (
                        result["ENABLE_FEATURE"] == "true"
                    )  # Config file values become strings

    def test_prepare_configuration_config_file_not_found(self, config_processor):
        """Test configuration preparation with non-existent config file."""
        template = {"config_schema": {"properties": {}}, "env_vars": {}}

        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                config_processor.prepare_configuration(
                    template=template, config_file="nonexistent.json"
                )


@pytest.mark.unit
class TestConfigProcessorVolumeAndCommandArgs:
    """Test ConfigProcessor.handle_volume_and_args_config_properties method."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    def test_handle_volume_mount_property(self, config_processor):
        """Test handling of volume mount properties."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dir": {
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"DATA_DIR": "/host/data"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should create volume mount
        assert "/host/data" in result["template"]["volumes"]
        assert result["template"]["volumes"]["/host/data"] == "/mnt/host/data"

        # Should remove from config
        assert "DATA_DIR" not in result["config"]

    def test_handle_command_arg_property(self, config_processor):
        """Test handling of command argument properties."""
        template = {
            "config_schema": {
                "properties": {
                    "server_args": {
                        "env_mapping": "SERVER_ARGS",
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"SERVER_ARGS": "--verbose --debug"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should add to command (split into individual arguments)
        assert "--verbose" in result["template"]["command"]
        assert "--debug" in result["template"]["command"]

        # Should remove from config
        assert "SERVER_ARGS" not in result["config"]

    def test_handle_combined_volume_and_command_property(self, config_processor):
        """Test handling of properties that are both volume mount and command arg."""
        template = {
            "config_schema": {
                "properties": {
                    "shared_path": {
                        "env_mapping": "SHARED_PATH",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"SHARED_PATH": "/shared/data"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should create volume mount
        assert "/shared/data" in result["template"]["volumes"]
        assert result["template"]["volumes"]["/shared/data"] == "/mnt/shared/data"

        # Should add container path to command (not host path)
        assert "/mnt/shared/data" in result["template"]["command"]

        # Should remove from config
        assert "SHARED_PATH" not in result["config"]

    def test_handle_host_container_volume_format(self, config_processor):
        """Test handling of host:container volume format."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dir": {
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"DATA_DIR": "/host/data:/custom/container/path"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should use custom container path
        assert "/host/data" in result["template"]["volumes"]
        assert result["template"]["volumes"]["/host/data"] == "/custom/container/path"

    def test_handle_multiple_space_separated_paths(self, config_processor):
        """Test handling of multiple space-separated paths."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dirs": {
                        "env_mapping": "DATA_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        config = {"DATA_DIRS": "/path1 /path2 /path3"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should create separate volume mounts for each path
        volumes = result["template"]["volumes"]
        assert "/path1" in volumes
        assert "/path2" in volumes
        assert "/path3" in volumes
        assert volumes["/path1"] == "/mnt/path1"
        assert volumes["/path2"] == "/mnt/path2"
        assert volumes["/path3"] == "/mnt/path3"

        # Should add container paths to command
        command = result["template"]["command"]
        assert "/mnt/path1" in command
        assert "/mnt/path2" in command
        assert "/mnt/path3" in command

    def test_preserve_existing_volumes_and_commands(self, config_processor):
        """Test that existing volumes and commands are preserved."""
        template = {
            "config_schema": {
                "properties": {
                    "new_path": {
                        "env_mapping": "NEW_PATH",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {"/existing/volume": "/app/existing"},
            "command": ["--existing-arg"],
        }

        config = {"NEW_PATH": "/new/path"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should preserve existing volumes and add new ones
        volumes = result["template"]["volumes"]
        assert "/existing/volume" in volumes
        assert volumes["/existing/volume"] == "/app/existing"
        assert "/new/path" in volumes
        assert volumes["/new/path"] == "/mnt/new/path"

        # Should preserve existing commands and add container path for new one
        command = result["template"]["command"]
        assert "--existing-arg" in command
        assert "/mnt/new/path" in command

    def test_handle_none_volumes_and_commands(self, config_processor):
        """Test handling when template has None for volumes and command."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dir": {
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": None,
            "command": None,
        }

        config = {"DATA_DIR": "/test/path"}

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should initialize volumes and command with container path
        assert result["template"]["volumes"] == {"/test/path": "/mnt/test/path"}
        assert result["template"]["command"] == ["/mnt/test/path"]

    def test_invalid_volume_mount_format_warning(self, config_processor):
        """Test warning for invalid volume mount format."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dir": {
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        # Invalid format with too many colons
        config = {"DATA_DIR": "/host:/container:/extra"}

        with patch("mcp_template.utils.config_processor.logger") as mock_logger:
            result = config_processor.handle_volume_and_args_config_properties(
                template, config
            )

            # Should log warning
            mock_logger.warning.assert_called_once()

            # Should not create volume mount for invalid format
            assert not result["template"]["volumes"]

    def test_docker_artifact_removal(self, config_processor):
        """Test removal of Docker command artifacts from volume mount paths."""
        template = {
            "config_schema": {
                "properties": {
                    "data_dirs": {
                        "env_mapping": "DATA_DIRS",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                }
            },
            "volumes": {},
            "command": [],
        }

        # Input with Docker command artifacts (like what user might accidentally paste)
        config = {
            "DATA_DIRS": "/path1:/container1 --volume /path2:/container2 --volume /path3"
        }

        result = config_processor.handle_volume_and_args_config_properties(
            template, config
        )

        # Should clean up artifacts and create proper volume mounts
        volumes = result["template"]["volumes"]
        assert "/path1" in volumes
        assert volumes["/path1"] == "/container1"
        assert "/path2" in volumes
        assert volumes["/path2"] == "/container2"
        assert "/path3" in volumes
        assert volumes["/path3"] == "/mnt/path3"

        # Should add container paths to command
        command = result["template"]["command"]
        assert "/container1" in command
        assert "/container2" in command
        assert "/mnt/path3" in command


@pytest.mark.unit
class TestConfigProcessorTypeConversion:
    """Test ConfigProcessor type conversion functionality."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    def test_convert_boolean_values(self, config_processor):
        """Test conversion of boolean values."""
        template = {
            "config_schema": {
                "properties": {
                    "enable_feature": {
                        "type": "boolean",
                        "env_mapping": "ENABLE_FEATURE",
                    }
                }
            },
            "env_vars": {},
        }

        test_cases = [
            ("true", True),
            ("false", False),
            ("True", True),
            ("False", False),
            ("1", True),
            ("0", False),
        ]

        for input_value, expected in test_cases:
            config_values = {"enable_feature": input_value}
            result = config_processor._convert_config_values(config_values, template)
            assert result["ENABLE_FEATURE"] == expected

    def test_convert_integer_values(self, config_processor):
        """Test conversion of integer values."""
        template = {
            "config_schema": {
                "properties": {
                    "port": {
                        "type": "integer",
                        "env_mapping": "PORT",
                    }
                }
            },
            "env_vars": {},
        }

        config_values = {"port": "8080"}
        result = config_processor._convert_config_values(config_values, template)
        assert result["PORT"] == 8080

    def test_convert_number_values(self, config_processor):
        """Test conversion of number (float) values."""
        template = {
            "config_schema": {
                "properties": {
                    "timeout": {
                        "type": "number",
                        "env_mapping": "TIMEOUT",
                    }
                }
            },
            "env_vars": {},
        }

        config_values = {"timeout": "30.5"}
        result = config_processor._convert_config_values(config_values, template)
        assert abs(result["TIMEOUT"] - 30.5) < 0.001

    def test_convert_array_values(self, config_processor):
        """Test conversion of array values."""
        template = {
            "config_schema": {
                "properties": {
                    "tags": {
                        "type": "array",
                        "env_mapping": "TAGS",
                    }
                }
            },
            "env_vars": {},
        }

        # Test comma-separated string
        config_values = {"tags": "tag1,tag2,tag3"}
        result = config_processor._convert_config_values(config_values, template)
        assert result["TAGS"] == "tag1,tag2,tag3"

    def test_convert_string_values(self, config_processor):
        """Test conversion of string values (default case)."""
        template = {
            "config_schema": {
                "properties": {
                    "name": {
                        "type": "string",
                        "env_mapping": "NAME",
                    }
                }
            },
            "env_vars": {},
        }

        config_values = {"name": "test_value"}
        result = config_processor._convert_config_values(config_values, template)
        assert result["NAME"] == "test_value"

    def test_convert_values_type_error_fallback(self, config_processor):
        """Test fallback to string when type conversion fails."""
        template = {
            "config_schema": {
                "properties": {
                    "port": {
                        "type": "integer",
                        "env_mapping": "PORT",
                    }
                }
            },
            "env_vars": {},
        }

        # Invalid integer value
        config_values = {"port": "not_a_number"}

        with patch("mcp_template.utils.config_processor.logger") as mock_logger:
            result = config_processor._convert_config_values(config_values, template)

            # Should fall back to string and log warning
            assert result["PORT"] == "not_a_number"
            mock_logger.warning.assert_called_once()


@pytest.mark.unit
class TestConfigProcessorNestedConfiguration:
    """Test ConfigProcessor nested configuration handling."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    def test_handle_nested_cli_config_two_parts(self, config_processor):
        """Test handling of double underscore notation with two parts."""
        properties = {
            "allowed_dirs": {"env_mapping": "ALLOWED_DIRS"},
            "log_level": {"env_mapping": "LOG_LEVEL"},
        }

        # Test category__property format
        result = config_processor._handle_nested_cli_config(
            "allowed__dirs", "value", properties
        )
        assert result == "allowed_dirs"

    def test_handle_nested_cli_config_three_parts(self, config_processor):
        """Test handling of double underscore notation with three parts."""
        properties = {
            "security_read_only_mode": {"env_mapping": "SECURITY_READ_ONLY_MODE"},
            "security_mode": {"env_mapping": "SECURITY_MODE"},
            "mode": {"env_mapping": "MODE"},
        }

        # Test category__subcategory__property format
        result = config_processor._handle_nested_cli_config(
            "security__read__only_mode", "value", properties
        )
        assert result == "security_read_only_mode"

    def test_handle_nested_cli_config_not_found(self, config_processor):
        """Test handling when nested config property is not found."""
        properties = {
            "existing_prop": {"env_mapping": "EXISTING_PROP"},
        }

        result = config_processor._handle_nested_cli_config(
            "nonexistent__prop", "value", properties
        )
        assert result is None

    def test_snake_to_camel_conversion(self, config_processor):
        """Test snake_case to camelCase conversion."""
        test_cases = [
            ("snake_case", "snakeCase"),
            ("single", "single"),
            ("multi_word_case", "multiWordCase"),
            ("a_b_c", "aBC"),
        ]

        for snake_str, expected_camel in test_cases:
            result = config_processor._snake_to_camel(snake_str)
            assert result == expected_camel

    def test_get_nested_value(self, config_processor):
        """Test getting nested values from dictionary."""
        data = {
            "level1": {"level2": {"level3": "nested_value"}},
            "simple": "simple_value",
        }

        # Test nested access
        result = config_processor._get_nested_value(data, "level1.level2.level3")
        assert result == "nested_value"

        # Test simple access
        result = config_processor._get_nested_value(data, "simple")
        assert result == "simple_value"

        # Test missing key
        with pytest.raises(KeyError):
            config_processor._get_nested_value(data, "nonexistent.key")


@pytest.mark.unit
class TestConfigProcessorFileMapping:
    """Test ConfigProcessor file mapping functionality."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    def test_map_file_config_to_env_direct_mapping(self, config_processor):
        """Test direct property name mapping from file config."""
        template = {
            "config_schema": {
                "properties": {
                    "log_level": {"env_mapping": "LOG_LEVEL"},
                    "port": {"env_mapping": "PORT"},
                }
            }
        }

        file_config = {
            "log_level": "DEBUG",
            "port": 9000,
        }

        result = config_processor._map_file_config_to_env(file_config, template)

        assert result["LOG_LEVEL"] == "DEBUG"
        assert result["PORT"] == "9000"

    def test_map_file_config_to_env_with_file_mapping_hint(self, config_processor):
        """Test file mapping with explicit file_mapping hint."""
        template = {
            "config_schema": {
                "properties": {
                    "log_level": {
                        "env_mapping": "LOG_LEVEL",
                        "file_mapping": "logging.level",
                    }
                }
            }
        }

        file_config = {"logging": {"level": "WARNING"}}

        result = config_processor._map_file_config_to_env(file_config, template)

        assert result["LOG_LEVEL"] == "WARNING"

    def test_generate_common_patterns(self, config_processor):
        """Test generation of common nested patterns."""
        # Test specific property with predefined patterns
        patterns = config_processor._generate_common_patterns("log_level")
        assert "logging.level" in patterns
        assert "log.level" in patterns

        # Test generic property
        patterns = config_processor._generate_common_patterns("custom_prop")
        assert "config.custom_prop" in patterns
        assert "settings.custom_prop" in patterns
        assert "config.customProp" in patterns  # camelCase version

    def test_convert_value_to_env_string(self, config_processor):
        """Test conversion of values to environment variable string format."""
        prop_config = {}

        # Test list conversion
        result = config_processor._convert_value_to_env_string([1, 2, 3], prop_config)
        assert result == "1,2,3"

        # Test boolean conversion
        result = config_processor._convert_value_to_env_string(True, prop_config)
        assert result == "true"

        result = config_processor._convert_value_to_env_string(False, prop_config)
        assert result == "false"

        # Test string conversion
        result = config_processor._convert_value_to_env_string("test", prop_config)
        assert result == "test"

        # Test number conversion
        result = config_processor._convert_value_to_env_string(42, prop_config)
        assert result == "42"


@pytest.mark.unit
class TestConfigProcessorTemplateOverrides:
    """Test template override functionality in ConfigProcessor."""

    @pytest.fixture
    def config_processor(self):
        """Create a ConfigProcessor instance for testing."""
        return ConfigProcessor()

    def test_simple_override(self, config_processor):
        """Test simple field override."""
        template_data = {"name": "test", "version": "1.0.0"}
        override_values = {"version": "2.0.0", "author": "Test User"}

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["version"] == "2.0.0"
        assert result["author"] == "Test User"
        assert result["name"] == "test"  # unchanged

    def test_nested_override(self, config_processor):
        """Test nested field override with double underscores."""
        template_data = {
            "metadata": {"version": "1.0.0", "description": "Test"},
            "config": {"debug": False},
        }
        override_values = {
            "metadata__version": "2.0.0",
            "metadata__author": "Test User",
            "config__debug": "true",
            "config__port": "8080",
        }

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["metadata"]["version"] == "2.0.0"
        assert result["metadata"]["author"] == "Test User"
        assert result["metadata"]["description"] == "Test"  # unchanged
        assert result["config"]["debug"] is True  # converted to boolean
        assert result["config"]["port"] == 8080  # converted to int

    def test_array_override(self, config_processor):
        """Test array element override."""
        template_data = {
            "tools": [
                {"name": "tool1", "enabled": True},
                {"name": "tool2", "enabled": True},
            ]
        }
        override_values = {
            "tools__0__enabled": "false",
            "tools__1__description": "Updated tool",
        }

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["tools"][0]["enabled"] is False
        assert result["tools"][0]["name"] == "tool1"  # unchanged
        assert result["tools"][1]["description"] == "Updated tool"
        assert result["tools"][1]["name"] == "tool2"  # unchanged

    def test_deep_nested_override(self, config_processor):
        """Test deeply nested override."""
        template_data = {
            "config": {"database": {"connection": {"host": "localhost", "port": 5432}}}
        }
        override_values = {
            "config__database__connection__host": "remote.example.com",
            "config__database__connection__timeout": "30",
        }

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert (
            result["config"]["database"]["connection"]["host"] == "remote.example.com"
        )
        assert result["config"]["database"]["connection"]["port"] == 5432  # unchanged
        assert result["config"]["database"]["connection"]["timeout"] == 30  # new field

    def test_type_conversion(self, config_processor):
        """Test automatic type conversion of override values."""
        template_data = {"config": {}}
        override_values = {
            "config__debug": "true",
            "config__verbose": "false",
            "config__port": "8080",
            "config__timeout": "30.5",
            "config__name": "test-server",
            "config__tags": '["tag1", "tag2"]',
            "config__metadata": '{"key": "value"}',
        }

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["config"]["debug"] is True
        assert result["config"]["verbose"] is False
        assert result["config"]["port"] == 8080
        assert result["config"]["timeout"] == 30.5
        assert result["config"]["name"] == "test-server"
        assert result["config"]["tags"] == ["tag1", "tag2"]
        assert result["config"]["metadata"] == {"key": "value"}

    def test_array_extension(self, config_processor):
        """Test that arrays are extended when accessing out-of-bounds indices."""
        template_data = {"tools": [{"name": "tool1"}]}
        override_values = {"tools__2__name": "tool3"}

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        # Array should be extended with empty objects
        assert len(result["tools"]) == 3
        assert result["tools"][0]["name"] == "tool1"
        assert result["tools"][1] == {}  # empty placeholder
        assert result["tools"][2]["name"] == "tool3"

    def test_invalid_array_index(self, config_processor):
        """Test handling of non-numeric array indices."""
        template_data = {"config": {"debug": True}}
        override_values = {"config__invalid__nested": "value"}

        # Should create nested dict structure
        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["config"]["debug"] is True
        assert result["config"]["invalid"]["nested"] == "value"

    def test_empty_override_values(self, config_processor):
        """Test with empty override values."""
        template_data = {"name": "test"}
        override_values = {}

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result == template_data

    def test_none_override_values(self, config_processor):
        """Test with None override values."""
        template_data = {"name": "test"}

        result = config_processor._apply_template_overrides(template_data, None)

        assert result == template_data

    def test_override_creates_missing_structure(self, config_processor):
        """Test that override can create completely new nested structures."""
        template_data = {"existing": "value"}
        override_values = {
            "new__section__subsection__value": "new_value",
            "new__array__0__item": "first_item",
        }

        result = config_processor._apply_template_overrides(
            template_data, override_values
        )

        assert result["existing"] == "value"  # unchanged
        assert result["new"]["section"]["subsection"]["value"] == "new_value"
        assert result["new"]["array"][0]["item"] == "first_item"
