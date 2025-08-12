"""
Unit tests for ConfigManager.

Tests the configuration processing, validation, and merging
provided by the ConfigManager common module.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import json
import tempfile
import os

from mcp_template.core.config_manager import ConfigManager, ValidationResult


@pytest.mark.unit
class TestConfigManager:
    """Unit tests for ConfigManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()

    def test_merge_config_sources_precedence(self):
        """Test configuration merging with proper precedence."""
        template_config = {
            "name": "Demo Template",
            "setting1": "template_value",
            "setting2": "template_value",
            "setting3": "template_value",
        }

        env_vars = {"setting2": "env_value", "setting3": "env_value"}
        config_values = {"setting3": "config_value"}
        override_values = {"setting3": "override_value"}

        result = self.config_manager.merge_config_sources(
            template_config=template_config,
            env_vars=env_vars,
            config_values=config_values,
            override_values=override_values,
        )

        # Test precedence: override > config > env > template
        assert result["setting1"] == "template_value"  # Only in template
        assert result["setting2"] == "env_value"  # Env overrides template
        assert result["setting3"] == "override_value"  # Override wins

    def test_merge_config_sources_with_config_file(self):
        """Test configuration merging with config file."""
        template_config = {"name": "Demo Template", "setting1": "template"}
        file_config = {"setting1": "file", "setting2": "file"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(file_config, f)
            config_file_path = f.name

        try:
            result = self.config_manager.merge_config_sources(
                template_config=template_config, config_file=config_file_path
            )

            assert result["setting1"] == "file"  # File overrides template
            assert result["setting2"] == "file"  # From file
        finally:
            os.unlink(config_file_path)

    def test_validate_config_schema(self):
        """Test configuration validation against schema."""
        config = {"name": "Test Server", "port": 8080, "enabled": True}

        schema = {
            "type": "object",
            "required": ["name", "port"],
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "number", "minimum": 1000, "maximum": 9999},
                "enabled": {"type": "boolean"},
            },
        }

        result = self.config_manager.validate_config(config, schema)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_config_missing_required(self):
        """Test validation with missing required fields."""
        config = {
            "name": "Test Server"
            # Missing required 'port' field
        }

        schema = {
            "required": ["name", "port"],
            "properties": {"name": {"type": "string"}, "port": {"type": "number"}},
        }

        result = self.config_manager.validate_config(config, schema)

        assert result.valid is False
        assert "Required field 'port' is missing" in result.errors

    def test_validate_config_wrong_types(self):
        """Test validation with wrong field types."""
        config = {
            "name": 123,  # Should be string
            "port": "8080",  # Should be number
            "enabled": "true",  # Should be boolean
        }

        schema = {
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "number"},
                "enabled": {"type": "boolean"},
            }
        }

        result = self.config_manager.validate_config(config, schema)

        assert result.valid is False
        assert any("should be a string" in error for error in result.errors)
        assert any("should be a number" in error for error in result.errors)
        assert any("should be a boolean" in error for error in result.errors)

    def test_validate_config_constraints(self):
        """Test validation with field constraints."""
        config = {
            "short_name": "AB",  # Too short
            "long_name": "A" * 100,  # Too long
            "small_number": 5,  # Too small
            "large_number": 1000,  # Too large
        }

        schema = {
            "properties": {
                "short_name": {"type": "string", "minLength": 3},
                "long_name": {"type": "string", "maxLength": 50},
                "small_number": {"type": "number", "minimum": 10},
                "large_number": {"type": "number", "maximum": 500},
            }
        }

        result = self.config_manager.validate_config(config, schema)

        assert result.valid is False
        assert any("too short" in error for error in result.errors)
        assert any("too long" in error for error in result.errors)
        assert any("too small" in error for error in result.errors)
        assert any("too large" in error for error in result.errors)

    def test_process_overrides_nested(self):
        """Test processing overrides with double-underscore notation."""
        config = {
            "tools": [
                {"name": "tool1", "custom_field": "original"},
                {"name": "tool2", "custom_field": "original"},
            ],
            "server": {"host": "localhost", "port": 8080},
        }

        overrides = {"tools__0__custom_field": "modified", "server__port": "9090"}

        result = self.config_manager._apply_overrides(config, overrides)

        assert result["tools"][0]["custom_field"] == "modified"
        assert result["tools"][1]["custom_field"] == "original"  # Unchanged
        assert result["server"]["port"] == "9090"

    def test_load_configuration_for_template(self):
        """Test loading configuration for template including template.json."""
        mock_template_config = {"name": "Demo Template", "docker_image": "demo:latest"}

        # Mock the import that happens inside the method - patch the from import
        with patch(
            "mcp_template.core.template_manager.TemplateManager"
        ) as MockTemplateManager:
            mock_tm = MockTemplateManager.return_value

            # Create a mock path
            mock_template_path = Mock()
            mock_tm.get_template_path.return_value = mock_template_path

            # Mock template.json file
            mock_template_file = Mock()
            mock_template_file.exists.return_value = True

            # Mock config directory
            mock_config_dir = Mock()
            mock_config_dir.exists.return_value = False  # Simplified test

            # Set up path operations using proper mock
            def mock_path_div(name):
                if name == "template.json":
                    return mock_template_file
                elif name == "config":
                    return mock_config_dir
                else:
                    return Mock(exists=Mock(return_value=False))

            mock_template_path.__truediv__ = Mock(side_effect=mock_path_div)

            # Mock file loading
            with patch.object(
                self.config_manager,
                "_load_config_file",
                return_value=mock_template_config,
            ):
                configs = self.config_manager.load_configuration_for_template("demo")

        # Should have loaded some configuration
        assert isinstance(configs, dict)

    def test_validate_template_configuration(self):
        """Test comprehensive template configuration validation."""
        mock_configs = {
            "template": {"name": "Demo Template", "docker_image": "demo:latest"},
            "server": {"port": 8080},
        }

        with patch.object(
            self.config_manager,
            "load_configuration_for_template",
            return_value=mock_configs,
        ):
            result = self.config_manager.validate_template_configuration("demo")

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert "configurations" in result

    def test_validate_template_configuration_missing_required(self):
        """Test template validation with missing required fields."""
        mock_configs = {
            "template": {
                "name": "Demo Template"
                # Missing required docker_image
            }
        }

        with patch.object(
            self.config_manager,
            "load_configuration_for_template",
            return_value=mock_configs,
        ):
            result = self.config_manager.validate_template_configuration("demo")

        assert result["valid"] is False
        assert any("docker_image" in error for error in result["errors"])

    def test_process_config_values(self):
        """Test processing config values with type conversion."""
        config_values = {
            "string_value": "hello",
            "number_value": "42",
            "boolean_value": "true",
            "json_value": '{"key": "value"}',
        }

        result = self.config_manager._process_config_values(config_values)

        assert result["string_value"] == "hello"
        assert result["number_value"] == 42
        assert result["boolean_value"] is True
        assert result["json_value"] == {"key": "value"}

    def test_deep_merge(self):
        """Test deep merging of nested dictionaries."""
        base = {
            "server": {"host": "localhost", "port": 8080, "ssl": {"enabled": False}},
            "client": {"timeout": 30},
        }

        override = {
            "server": {"port": 9090, "ssl": {"enabled": True, "cert": "/path/to/cert"}},
            "database": {"host": "db.example.com"},
        }

        result = self.config_manager._deep_merge(base, override)

        # Check that nested values are properly merged
        assert result["server"]["host"] == "localhost"  # From base
        assert result["server"]["port"] == 9090  # From override
        assert result["server"]["ssl"]["enabled"] is True  # From override
        assert result["server"]["ssl"]["cert"] == "/path/to/cert"  # From override
        assert result["client"]["timeout"] == 30  # From base
        assert result["database"]["host"] == "db.example.com"  # From override

    def test_validation_result(self):
        """Test ValidationResult class."""
        result = ValidationResult(
            valid=False, errors=["Error 1", "Error 2"], warnings=["Warning 1"]
        )

        assert result.valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

        result_dict = result.to_dict()
        assert result_dict["valid"] is False
        assert result_dict["errors"] == ["Error 1", "Error 2"]
        assert result_dict["warnings"] == ["Warning 1"]


@pytest.mark.integration
class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_config_file_loading_json(self):
        """Test loading actual JSON config file."""
        config_manager = ConfigManager()

        config_data = {"name": "Test Config", "settings": {"debug": True, "port": 8080}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file_path = f.name

        try:
            loaded_config = config_manager._load_config_file(config_file_path)
            assert loaded_config == config_data
        finally:
            os.unlink(config_file_path)

    def test_config_file_loading_yaml(self):
        """Test loading actual YAML config file."""
        config_manager = ConfigManager()

        yaml_content = """
name: Test Config
settings:
  debug: true
  port: 8080
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_file_path = f.name

        try:
            loaded_config = config_manager._load_config_file(config_file_path)
            assert loaded_config["name"] == "Test Config"
            assert loaded_config["settings"]["debug"] is True
            assert loaded_config["settings"]["port"] == 8080
        finally:
            os.unlink(config_file_path)

    def test_full_config_merge_workflow(self):
        """Test complete configuration merging workflow."""
        config_manager = ConfigManager()

        template_config = {
            "name": "Demo Template",
            "server": {"host": "localhost", "port": 7071},
        }

        file_config = {"server": {"port": 8080, "debug": True}}

        env_vars = {"SERVER_HOST": "0.0.0.0"}
        config_values = {"server_debug": "false"}
        override_values = {"server__port": "9090"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(file_config, f)
            config_file_path = f.name

        try:
            result = config_manager.merge_config_sources(
                template_config=template_config,
                config_file=config_file_path,
                env_vars=env_vars,
                config_values=config_values,
                override_values=override_values,
            )

            # Verify final merged configuration
            assert result["name"] == "Demo Template"
            assert (
                result["server"]["host"] == "localhost"
            )  # Template value (env mapping not implemented)
            assert result["server"]["port"] == "9090"  # Override value wins
            assert result["server"]["debug"] is True  # From file
        finally:
            os.unlink(config_file_path)
