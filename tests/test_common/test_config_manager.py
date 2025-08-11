"""
Unit tests for ConfigManager in the common module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
import yaml

from mcp_template.common.config_manager import ConfigManager
from tests.test_fixtures.sample_data import (
    CONFIG_SCHEMAS,
    ERROR_SCENARIOS,
    SAMPLE_CONFIG_DATA,
)


@pytest.mark.unit
class TestConfigManagerCore:
    """Core functionality tests for ConfigManager."""

    def test_init_default(self):
        """Test initialization with default parameters."""
        manager = ConfigManager()
        assert manager.core_config_processor is not None

    @patch(
        "builtins.open", mock_open(read_data='{"name": "test-server", "port": 8080}')
    )
    @patch("pathlib.Path.exists")
    def test_load_config_file_json(self, mock_exists):
        """Test loading JSON configuration file."""
        mock_exists.return_value = True

        manager = ConfigManager()
        config = manager.load_config_file("/path/to/config.json")

        assert config is not None
        assert config["name"] == "test-server"
        assert config["port"] == 8080

    @patch("builtins.open", mock_open(read_data="name: test-server\nport: 8080"))
    @patch("pathlib.Path.exists")
    def test_load_config_file_yaml(self, mock_exists):
        """Test loading YAML configuration file."""
        mock_exists.return_value = True

        manager = ConfigManager()
        config = manager.load_config_file("/path/to/config.yaml")

        assert config is not None
        assert config["name"] == "test-server"

    def test_load_config_file_not_found(self):
        """Test loading non-existent configuration file."""
        manager = ConfigManager()

        with pytest.raises(FileNotFoundError):
            manager.load_config_file("/path/to/nonexistent.json")

    @patch("builtins.open", mock_open(read_data="invalid json content"))
    @patch("pathlib.Path.exists")
    def test_load_config_file_invalid_json(self, mock_exists):
        """Test loading invalid JSON file."""
        mock_exists.return_value = True

        manager = ConfigManager()

        with pytest.raises(ValueError):
            manager.load_config_file("/path/to/invalid.json")

    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        manager = ConfigManager()
        template = {
            "config_schema": {
                "properties": {"name": {"type": "string"}, "port": {"type": "integer"}}
            }
        }
        config = SAMPLE_CONFIG_DATA["server"].copy()

        result = manager.validate_configuration(template, config)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_configuration_missing_required(self):
        """Test validation with missing required fields."""
        manager = ConfigManager()
        template = {
            "config_schema": {
                "properties": {"name": {"type": "string"}, "port": {"type": "integer"}}
            }
        }
        config = {"name": "test-server"}  # Missing port

        with patch(
            "mcp_template.deployer.MCPDeployer.list_missing_properties"
        ) as mock_missing:
            mock_missing.return_value = ["port"]

            result = manager.validate_configuration(template, config)

            assert result["valid"] is False
            assert len(result["missing_properties"]) == 1
            assert "port" in result["missing_properties"]

    def test_validate_configuration_invalid_types(self):
        """Test validation with invalid field types."""
        manager = ConfigManager()
        template = {"config_schema": {"properties": {"port": {"type": "integer"}}}}
        config = {"port": "not-a-number"}  # Should be integer

        with patch(
            "mcp_template.deployer.MCPDeployer.list_missing_properties"
        ) as mock_missing:
            mock_missing.return_value = []

            result = manager.validate_configuration(template, config)

            assert result["valid"] is False
            assert any("must be an integer" in error for error in result["errors"])

    def test_process_command_line_config_override(self):
        """Test command line configuration override."""
        manager = ConfigManager()
        base_config = SAMPLE_CONFIG_DATA["server"].copy()
        overrides = {"port": 8080, "log_level": "DEBUG"}

        result = manager.merge_configurations(base_config, overrides)

        assert result["port"] == 8080
        assert result["log_level"] == "DEBUG"
        assert result["name"] == base_config["name"]  # Unchanged

    def test_generate_example_config_mcp_server(self):
        """Test generating example MCP server configuration."""
        manager = ConfigManager()
        template = {
            "config_schema": {
                "properties": {
                    "name": {"type": "string", "default": "mcp-server"},
                    "port": {"type": "integer", "default": 8080},
                }
            }
        }

        config = manager.generate_example_config(template)

        assert config is not None
        assert "name" in config
        assert "port" in config
        assert isinstance(config["port"], int)

    def test_generate_example_config_deployment(self):
        """Test generating example deployment configuration."""
        manager = ConfigManager()
        template = {
            "config_schema": {
                "properties": {
                    "backend": {
                        "type": "string",
                        "enum": ["docker", "kubernetes"],
                        "default": "docker",
                    }
                }
            }
        }

        config = manager.generate_example_config(template)

        assert config is not None
        assert "backend" in config
        assert config["backend"] in ["docker", "kubernetes"]

    def test_merge_configurations_success(self):
        """Test successful configuration merging."""
        manager = ConfigManager()
        base_config = {"name": "server", "port": 7071, "timeout": 30}
        override_config = {"port": 8080, "log_level": "DEBUG"}

        result = manager.merge_configurations(base_config, override_config)

        assert result["name"] == "server"  # From base
        assert result["port"] == 8080  # Overridden
        assert result["timeout"] == 30  # From base
        assert result["log_level"] == "DEBUG"  # From override

    def test_merge_configurations_conflict_resolution(self):
        """Test configuration merging with conflicts."""
        manager = ConfigManager()
        base_config = {"port": 7071, "host": "localhost"}
        override_config = {"port": 8080, "host": "0.0.0.0"}

        result = manager.merge_configurations(base_config, override_config)

        # Override should win
        assert result["port"] == 8080
        assert result["host"] == "0.0.0.0"


@pytest.mark.unit
class TestConfigManagerTemplateOperations:
    """Test template-specific configuration operations."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.iterdir")
    def test_load_configuration_for_template(self, mock_iterdir, mock_exists):
        """Test loading all configurations for a template."""
        # Mock template directory structure
        mock_exists.return_value = True

        config_files = [
            Mock(name="server.json", suffix=".json"),
            Mock(name="client.json", suffix=".json"),
            Mock(name="deployment.yaml", suffix=".yaml"),
        ]
        mock_iterdir.return_value = config_files

        with patch.object(ConfigManager, "load_config_file") as mock_load:
            mock_load.side_effect = [
                SAMPLE_CONFIG_DATA["server"],
                SAMPLE_CONFIG_DATA["client"],
                SAMPLE_CONFIG_DATA["deployment"],
            ]

            manager = ConfigManager()
            configs = manager.load_configuration_for_template("demo")

            assert len(configs) == 3
            assert "server.json" in configs
            assert "client.json" in configs
            assert "deployment.yaml" in configs

    def test_validate_template_configuration(self):
        """Test comprehensive template configuration validation."""
        template_configs = {
            "server.json": SAMPLE_CONFIG_DATA["server"],
            "deployment.yaml": SAMPLE_CONFIG_DATA["deployment"],
        }

        with patch.object(
            ConfigManager, "load_configuration_for_template"
        ) as mock_load:
            mock_load.return_value = template_configs

            manager = ConfigManager()
            result = manager.validate_template_configuration("demo")

            assert "overall_valid" in result
            assert "file_results" in result
            assert len(result["file_results"]) == 2

    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.exists")
    def test_edit_configuration_file(self, mock_exists, mock_write):
        """Test safe configuration file editing."""
        mock_exists.return_value = True

        manager = ConfigManager()
        new_config = {"name": "updated-server", "port": 8080}

        result = manager.edit_configuration_file("demo", "server.json", new_config)

        assert result is True
        mock_write.assert_called_once()

    @patch("pathlib.Path.write_text")
    @patch("shutil.copy2")
    def test_export_configuration_package(self, mock_copy, mock_write):
        """Test exporting complete configuration package."""
        template_configs = {
            "server.json": SAMPLE_CONFIG_DATA["server"],
            "deployment.yaml": SAMPLE_CONFIG_DATA["deployment"],
        }

        with patch.object(
            ConfigManager, "load_configuration_for_template"
        ) as mock_load:
            mock_load.return_value = template_configs

            manager = ConfigManager()
            result = manager.export_configuration_package("demo", "/export/path")

            assert result is True

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.read_text")
    def test_import_configuration_package(self, mock_read, mock_exists):
        """Test importing and validating configuration package."""
        mock_exists.return_value = True
        mock_read.return_value = json.dumps(SAMPLE_CONFIG_DATA["server"])

        manager = ConfigManager()
        result = manager.import_configuration_package("/import/package.zip", "demo")

        assert result is True


@pytest.mark.unit
class TestConfigManagerAdvancedFeatures:
    """Test advanced configuration features."""

    def test_configuration_templating(self):
        """Test configuration templating with variable substitution."""
        manager = ConfigManager()
        template_config = {
            "name": "${SERVER_NAME}",
            "port": "${SERVER_PORT}",
            "host": "localhost",
        }
        variables = {"SERVER_NAME": "my-server", "SERVER_PORT": 8080}

        result = manager.apply_configuration_template(template_config, variables)

        assert result["name"] == "my-server"
        assert result["port"] == 8080
        assert result["host"] == "localhost"

    def test_environment_specific_configuration(self):
        """Test environment-specific configuration generation."""
        manager = ConfigManager()
        base_config = SAMPLE_CONFIG_DATA["server"].copy()

        # Test development environment
        dev_config = manager.generate_environment_config(base_config, "development")
        assert dev_config["log_level"] == "DEBUG"

        # Test production environment
        prod_config = manager.generate_environment_config(base_config, "production")
        assert prod_config["log_level"] == "INFO"

    def test_configuration_backup_restore(self):
        """Test configuration backup and restore functionality."""
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("shutil.copy2") as mock_copy:
                mock_exists.return_value = True

                manager = ConfigManager()

                # Test backup
                backup_path = manager.create_configuration_backup("/config/server.json")
                assert backup_path is not None
                mock_copy.assert_called()

                # Test restore
                result = manager.restore_configuration_backup(
                    backup_path, "/config/server.json"
                )
                assert result is True

    def test_configuration_diff(self):
        """Test configuration difference detection."""
        manager = ConfigManager()
        config1 = {"name": "server", "port": 7071, "timeout": 30}
        config2 = {"name": "server", "port": 8080, "log_level": "DEBUG"}

        diff = manager.diff_configurations(config1, config2)

        assert "changed" in diff
        assert "added" in diff
        assert "removed" in diff
        assert "port" in diff["changed"]
        assert "log_level" in diff["added"]
        assert "timeout" in diff["removed"]


@pytest.mark.unit
class TestConfigManagerErrorHandling:
    """Test error handling in ConfigManager."""

    def test_handle_file_permission_error(self):
        """Test handling of file permission errors."""
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Permission denied")
        ):
            manager = ConfigManager()
            config = manager.load_config_file("/protected/config.json")

            assert config is None

    def test_handle_yaml_parse_error(self):
        """Test handling of YAML parsing errors."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch(
                "pathlib.Path.read_text", return_value="invalid: yaml: content:"
            ):
                manager = ConfigManager()
                config = manager.load_config_file("/config/invalid.yaml")

                assert config is None

    def test_handle_configuration_validation_errors(self):
        """Test handling of configuration validation errors."""
        manager = ConfigManager()
        invalid_config = {"invalid_field": "value"}

        result = manager.validate_configuration(invalid_config, config_type="server")

        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_handle_template_not_found(self):
        """Test handling when template directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            manager = ConfigManager()
            configs = manager.load_configuration_for_template("nonexistent")

            assert configs == {}


@pytest.mark.integration
class TestConfigManagerIntegration:
    """Integration tests for ConfigManager."""

    def test_config_loading_real_files(self, temp_workspace):
        """Test configuration loading with real files."""
        # Create test config files
        config_dir = temp_workspace / "config"
        config_dir.mkdir()

        server_config = config_dir / "server.json"
        server_config.write_text(json.dumps(SAMPLE_CONFIG_DATA["server"]))

        manager = ConfigManager()
        config = manager.load_config_file(str(server_config))

        assert config is not None
        assert config["name"] == SAMPLE_CONFIG_DATA["server"]["name"]

    def test_config_validation_real_templates(self, temp_workspace):
        """Test configuration validation with actual templates."""
        # Create template with config
        template_dir = temp_workspace / "templates" / "test-template"
        template_dir.mkdir(parents=True)

        config_file = template_dir / "server.json"
        config_file.write_text(json.dumps(SAMPLE_CONFIG_DATA["server"]))

        manager = ConfigManager()
        result = manager.validate_template_configuration("test-template")

        assert "overall_valid" in result


@pytest.mark.slow
class TestConfigManagerPerformance:
    """Performance tests for ConfigManager."""

    def test_large_configuration_processing(self):
        """Test performance with large configuration files."""
        import time

        # Create large configuration
        large_config = {}
        for i in range(1000):
            large_config[f"setting_{i}"] = f"value_{i}"

        manager = ConfigManager()

        start_time = time.time()
        result = manager.validate_configuration(large_config, config_type="custom")
        elapsed_time = time.time() - start_time

        assert elapsed_time < 2.0  # Should complete within 2 seconds
        assert "valid" in result

    def test_concurrent_config_operations(self):
        """Test concurrent configuration operations."""
        import threading
        import time

        manager = ConfigManager()
        results = []

        def process_config(config_data):
            try:
                result = manager.validate_configuration(
                    config_data, config_type="server"
                )
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        # Start 10 concurrent operations
        threads = []
        for i in range(10):
            config = SAMPLE_CONFIG_DATA["server"].copy()
            config["name"] = f"server-{i}"

            thread = threading.Thread(target=process_config, args=(config,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)

        assert len(results) == 10
        successful = [r for r in results if "error" not in r]
        assert len(successful) >= 8  # At least 8 should succeed
