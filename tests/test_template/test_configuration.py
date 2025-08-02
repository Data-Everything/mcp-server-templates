"""
Tests for configuration mapping and type conversion functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_template import MCPDeployer


@pytest.mark.unit
class TestConfigurationMapping:
    """Test configuration mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

        # Mock template with comprehensive schema
        self.mock_template = {
            "name": "test-server",
            "config_schema": {
                "properties": {
                    "log_level": {
                        "type": "string",
                        "default": "info",
                        "env_mapping": "MCP_LOG_LEVEL",
                        "description": "Logging level",
                    },
                    "read_only_mode": {
                        "type": "boolean",
                        "default": False,
                        "env_mapping": "MCP_READ_ONLY",
                        "description": "Enable read-only mode",
                    },
                    "max_file_size": {
                        "type": "integer",
                        "default": 100,
                        "env_mapping": "MCP_MAX_FILE_SIZE",
                        "description": "Maximum file size in MB",
                    },
                    "allowed_directories": {
                        "type": "array",
                        "default": ["/data"],
                        "env_mapping": "MCP_ALLOWED_DIRS",
                        "env_separator": ":",
                        "description": "Allowed directories",
                    },
                    "custom_property": {
                        "type": "string",
                        "env_mapping": "MCP_CUSTOM",
                        "file_mapping": "custom.nested.value",
                        "description": "Custom property with explicit file mapping",
                    },
                },
                "required": ["log_level"],
            },
        }

    def test_snake_to_camel_conversion(self):
        """Test snake_case to camelCase conversion."""
        assert self.deployer._snake_to_camel("log_level") == "logLevel"
        assert self.deployer._snake_to_camel("read_only_mode") == "readOnlyMode"
        assert self.deployer._snake_to_camel("max_file_size") == "maxFileSize"
        assert self.deployer._snake_to_camel("single") == "single"

    def test_convert_value_to_env_string(self):
        """Test value conversion to environment string format."""
        prop_config = {"env_separator": ":"}

        # Test list conversion
        assert (
            self.deployer._convert_value_to_env_string(
                ["/data", "/config"], prop_config
            )
            == "/data:/config"
        )

        # Test boolean conversion
        assert self.deployer._convert_value_to_env_string(True, {}) == "true"
        assert self.deployer._convert_value_to_env_string(False, {}) == "false"

        # Test string/number conversion
        assert self.deployer._convert_value_to_env_string("debug", {}) == "debug"
        assert self.deployer._convert_value_to_env_string(42, {}) == "42"

    def test_get_nested_value(self):
        """Test nested value extraction."""
        data = {
            "security": {"readOnly": True, "nested": {"deep": "value"}},
            "simple": "test",
        }

        assert self.deployer._get_nested_value(data, "security.readOnly") is True
        assert self.deployer._get_nested_value(data, "security.nested.deep") == "value"
        assert self.deployer._get_nested_value(data, "simple") == "test"
        assert self.deployer._get_nested_value(data, "missing.path") is None

    def test_generate_common_patterns(self):
        """Test common pattern generation."""
        patterns = self.deployer._generate_common_patterns("log_level")
        assert "logging.level" in patterns
        assert "log.level" in patterns
        assert "config.log_level" in patterns
        assert "settings.logLevel" in patterns

    def test_map_file_config_direct_property_match(self):
        """Test direct property name mapping from config file."""
        file_config = {
            "log_level": "debug",
            "read_only_mode": True,
            "max_file_size": 50,
        }

        result = self.deployer._map_file_config_to_env(file_config, self.mock_template)

        assert result["MCP_LOG_LEVEL"] == "debug"
        assert result["MCP_READ_ONLY"] == "true"
        assert result["MCP_MAX_FILE_SIZE"] == "50"

    def test_map_file_config_camel_case_conversion(self):
        """Test camelCase property mapping from config file."""
        file_config = {"logLevel": "debug", "readOnlyMode": True, "maxFileSize": 50}

        result = self.deployer._map_file_config_to_env(file_config, self.mock_template)

        assert result["MCP_LOG_LEVEL"] == "debug"
        assert result["MCP_READ_ONLY"] == "true"
        assert result["MCP_MAX_FILE_SIZE"] == "50"

    def test_map_file_config_nested_patterns(self):
        """Test nested configuration pattern mapping."""
        file_config = {
            "logging": {"level": "debug"},
            "security": {
                "readOnly": True,
                "maxFileSize": 50,
                "allowedDirs": ["/data", "/workspace"],
            },
        }

        result = self.deployer._map_file_config_to_env(file_config, self.mock_template)

        assert result["MCP_LOG_LEVEL"] == "debug"
        assert result["MCP_READ_ONLY"] == "true"
        assert result["MCP_MAX_FILE_SIZE"] == "50"
        assert result["MCP_ALLOWED_DIRS"] == "/data:/workspace"

    def test_map_file_config_explicit_file_mapping(self):
        """Test explicit file mapping from property config."""
        file_config = {"custom": {"nested": {"value": "test_value"}}}

        result = self.deployer._map_file_config_to_env(file_config, self.mock_template)

        assert result["MCP_CUSTOM"] == "test_value"

    def test_convert_config_values_with_type_conversion(self):
        """Test CLI config value conversion with proper types."""
        config_values = {
            "log_level": "debug",
            "read_only_mode": "true",
            "max_file_size": "50",
            "MCP_ALLOWED_DIRS": "/data,/config",  # Direct env mapping
        }

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        assert result["MCP_LOG_LEVEL"] == "debug"
        assert result["MCP_READ_ONLY"] == "True"
        assert result["MCP_MAX_FILE_SIZE"] == "50"
        assert result["MCP_ALLOWED_DIRS"] == "/data,/config"

    def test_prepare_configuration_precedence(self):
        """Test configuration precedence: defaults < file < CLI < env."""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {"logging": {"level": "warning"}, "security": {"readOnly": True}}, f
            )
            config_file_path = f.name

        try:
            # Test configuration precedence
            result = self.deployer._prepare_configuration(
                template=self.mock_template,
                env_vars={"MCP_LOG_LEVEL": "error"},  # Highest priority
                config_file=config_file_path,  # Medium priority
                config_values={
                    "read_only_mode": "false"
                },  # Lower priority than env, higher than file
            )

            # Environment variable should override file
            assert result["MCP_LOG_LEVEL"] == "error"
            # CLI config should override file
            assert result["MCP_READ_ONLY"] == "False"

        finally:
            Path(config_file_path).unlink()

    def test_load_config_file_json(self):
        """Test loading JSON configuration file."""
        config_data = {"logging": {"level": "debug"}, "security": {"readOnly": True}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file_path = f.name

        try:
            result = self.deployer._load_config_file(
                config_file_path, self.mock_template
            )
            assert result["MCP_LOG_LEVEL"] == "debug"
            assert result["MCP_READ_ONLY"] == "true"
        finally:
            Path(config_file_path).unlink()

    def test_load_config_file_yaml(self):
        """Test loading YAML configuration file."""
        pytest.importorskip("yaml")  # Skip if PyYAML not available

        config_content = """
        logging:
          level: debug
        security:
          readOnly: true
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write(config_content)
            config_file_path = f.name

        try:
            result = self.deployer._load_config_file(
                config_file_path, self.mock_template
            )
            assert result["MCP_LOG_LEVEL"] == "debug"
            assert result["MCP_READ_ONLY"] == "true"
        finally:
            Path(config_file_path).unlink()


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

    def test_file_server_template_config_mapping(self):
        """Test configuration mapping for file-server template."""
        if "file-server" not in self.deployer.templates:
            pytest.skip("file-server template not available")

        template = self.deployer.templates["file-server"]

        # Test with realistic file-server config
        file_config = {
            "security": {
                "allowedDirs": ["/data", "/workspace"],
                "readOnly": False,
                "maxFileSize": 100,
                "excludePatterns": ["*.tmp", "*.log"],
            },
            "logging": {"level": "info", "enableAudit": True},
        }

        result = self.deployer._map_file_config_to_env(file_config, template)

        # Should map to appropriate environment variables
        assert "MCP_ALLOWED_DIRECTORIES" in result or "MCP_ALLOWED_DIRS" in result
        assert "MCP_READ_ONLY_MODE" in result or "MCP_READ_ONLY" in result
        assert "MCP_LOG_LEVEL" in result
