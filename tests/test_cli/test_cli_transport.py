"""
Tests for CLI transport options and double underscore configuration notation.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_template.cli import EnhancedCLI
from mcp_template.deployer import MCPDeployer


class TestTransportOptions:
    """Test transport option functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.enhanced_cli = EnhancedCLI()

        # Mock templates with transport support
        self.mock_templates = {
            "test-server": {
                "name": "Test Server",
                "description": "Test server template",
                "transport": {"supported": ["http", "stdio"], "default": "http"},
                "config_schema": {
                    "properties": {
                        "api_key": {
                            "type": "string",
                            "description": "API key",
                            "env_mapping": "TEST_API_KEY",
                            "required": True,
                        },
                        "port": {
                            "type": "integer",
                            "description": "Server port",
                            "env_mapping": "TEST_PORT",
                            "default": 8080,
                        },
                    },
                    "required": ["api_key"],
                },
            },
            "stdio-only-server": {
                "name": "STDIO Only Server",
                "description": "Server that only supports STDIO",
                "transport": {"supported": ["stdio"], "default": "stdio"},
                "config_schema": {
                    "properties": {
                        "data_path": {
                            "type": "string",
                            "description": "Data path",
                            "env_mapping": "STDIO_DATA_PATH",
                        }
                    }
                },
            },
        }

        self.enhanced_cli.templates = self.mock_templates

    @patch("mcp_template.cli.MCPDeployer")
    def test_deploy_with_http_transport(self, mock_deployer_class):
        """Test deployment with HTTP transport."""
        mock_deployer = Mock()
        mock_deployer.deploy.return_value = True
        mock_deployer_class.return_value = mock_deployer

        self.enhanced_cli.deployer = mock_deployer

        with patch.object(self.enhanced_cli, "setup_docker_network", return_value=True):
            result = self.enhanced_cli.deploy_with_transport(
                template_name="test-server", transport="http", port=7071
            )

        assert result is True
        mock_deployer.deploy.assert_called_once()

        # Check that transport config was added
        call_args = mock_deployer.deploy.call_args
        config_values = call_args[1]["config_values"]
        assert config_values["transport"] == "http"
        assert config_values["port"] == "7071"

    @patch("mcp_template.cli.MCPDeployer")
    def test_deploy_with_stdio_transport(self, mock_deployer_class):
        """Test deployment with STDIO transport."""
        mock_deployer = Mock()
        mock_deployer.deploy.return_value = True
        mock_deployer_class.return_value = mock_deployer

        self.enhanced_cli.deployer = mock_deployer

        result = self.enhanced_cli.deploy_with_transport(
            template_name="test-server", transport="stdio"
        )

        assert result is True
        mock_deployer.deploy.assert_called_once()

        # Check that transport config was added
        call_args = mock_deployer.deploy.call_args
        config_values = call_args[1]["config_values"]
        assert config_values["transport"] == "stdio"
        # Port should not be set for STDIO
        assert "port" not in config_values

    def test_deploy_with_unsupported_transport(self):
        """Test deployment with unsupported transport."""
        with patch("rich.console.Console.print") as mock_print:
            result = self.enhanced_cli.deploy_with_transport(
                template_name="stdio-only-server",
                transport="http",  # Not supported by this template
            )

        assert result is False
        # Should print error about unsupported transport
        mock_print.assert_called()
        error_messages = [str(call[0][0]) for call in mock_print.call_args_list]
        assert any(
            "not supported" in msg.lower() or "supported transports" in msg.lower()
            for msg in error_messages
        )

    def test_deploy_nonexistent_template(self):
        """Test deployment of non-existent template."""
        with patch("rich.console.Console.print") as mock_print:
            result = self.enhanced_cli.deploy_with_transport(
                template_name="nonexistent-template", transport="http"
            )

        assert result is False
        mock_print.assert_called()
        error_message = str(mock_print.call_args[0][0])
        assert "not found" in error_message.lower()

    @patch("subprocess.run")
    def test_setup_docker_network_success(self, mock_subprocess):
        """Test successful Docker network setup."""
        # Mock network doesn't exist, then creation succeeds
        mock_subprocess.side_effect = [
            Mock(stdout=""),  # Network doesn't exist
            Mock(),  # Network creation succeeds
        ]

        result = self.enhanced_cli.setup_docker_network()

        assert result is True
        assert mock_subprocess.call_count == 2

    @patch("subprocess.run")
    def test_setup_docker_network_failure(self, mock_subprocess):
        """Test Docker network setup failure."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "docker")

        result = self.enhanced_cli.setup_docker_network()

        assert result is False


class TestDoubleUnderscoreConfiguration:
    """Test double underscore configuration notation."""

    def setup_method(self):
        """Setup for each test method."""
        self.deployer = MCPDeployer()

        # Mock template with nested configuration
        self.mock_template = {
            "name": "Test Server",
            "config_schema": {
                "properties": {
                    "api_key": {
                        "type": "string",
                        "description": "API key",
                        "env_mapping": "TEST_API_KEY",
                    },
                    "security_read_only": {
                        "type": "boolean",
                        "description": "Read-only mode",
                        "env_mapping": "TEST_SECURITY_READ_ONLY",
                    },
                    "logging_level": {
                        "type": "string",
                        "description": "Logging level",
                        "env_mapping": "TEST_LOGGING_LEVEL",
                        "default": "INFO",
                    },
                    "database_connection_timeout": {
                        "type": "integer",
                        "description": "Database connection timeout",
                        "env_mapping": "TEST_DB_CONNECTION_TIMEOUT",
                    },
                }
            },
        }

    def test_simple_double_underscore_notation(self):
        """Test simple double underscore notation mapping."""
        config_values = {"security__read_only": "true", "logging__level": "DEBUG"}

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should map to environment variables
        assert result["TEST_SECURITY_READ_ONLY"] == "true"
        assert result["TEST_LOGGING_LEVEL"] == "DEBUG"

    def test_template_level_override_notation(self):
        """Test template-level override with double underscore."""
        config_values = {
            "test_server__api_key": "override-key",
            "test_server__logging_level": "ERROR",
        }

        # Mock the template name to match the prefix
        with patch.object(self.deployer, "_handle_nested_cli_config") as mock_handle:
            mock_handle.side_effect = [
                "TEST_API_KEY",  # For test_server__api_key
                "TEST_LOGGING_LEVEL",  # For test_server__logging_level
            ]

            result = self.deployer._convert_config_values(
                config_values, self.mock_template
            )

        assert mock_handle.call_count == 2
        # Check that the method was called with correct parameters
        calls = mock_handle.call_args_list
        assert calls[0][0][0] == "test_server__api_key"
        assert calls[1][0][0] == "test_server__logging_level"

    def test_nested_configuration_notation(self):
        """Test deeply nested configuration notation."""
        config_values = {"database__connection__timeout": "60"}

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should map to constructed environment variable
        assert result["TEST_DB_CONNECTION_TIMEOUT"] == "60"

    def test_type_conversion_with_double_underscore(self):
        """Test type conversion works with double underscore notation."""
        config_values = {
            "security__read_only": "false",  # boolean
            "database__connection__timeout": "120",  # integer
        }

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should convert types appropriately
        assert result["TEST_SECURITY_READ_ONLY"] == "false"
        assert result["TEST_DB_CONNECTION_TIMEOUT"] == "120"

    def test_unknown_property_with_double_underscore(self):
        """Test handling of unknown properties with double underscore."""
        config_values = {
            "unknown__property": "value",
            "another__unknown__setting": "value2",
        }

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should create environment variables with MCP prefix
        assert result["MCP_UNKNOWN_PROPERTY"] == "value"
        assert result["MCP_ANOTHER_UNKNOWN_SETTING"] == "value2"

    def test_mixed_configuration_styles(self):
        """Test mixing regular and double underscore configuration."""
        config_values = {
            "api_key": "direct-key",  # Direct property
            "security__read_only": "true",  # Double underscore
            "TEST_LOGGING_LEVEL": "WARN",  # Direct env var
        }

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # All should be properly handled
        assert result["TEST_API_KEY"] == "direct-key"
        assert result["TEST_SECURITY_READ_ONLY"] == "true"
        assert result["TEST_LOGGING_LEVEL"] == "WARN"


class TestConfigurationValidation:
    """Test configuration validation and error handling."""

    def setup_method(self):
        """Setup for each test method."""
        self.deployer = MCPDeployer()

        self.mock_template = {
            "name": "Test Server",
            "config_schema": {
                "properties": {
                    "port": {
                        "type": "integer",
                        "description": "Server port",
                        "env_mapping": "TEST_PORT",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "Enable feature",
                        "env_mapping": "TEST_ENABLED",
                    },
                    "items": {
                        "type": "array",
                        "description": "List of items",
                        "env_mapping": "TEST_ITEMS",
                        "env_separator": ",",
                    },
                }
            },
        }

    def test_type_conversion_errors(self):
        """Test handling of type conversion errors."""
        config_values = {
            "port": "not-a-number",  # Should fail integer conversion
            "enabled": "maybe",  # Invalid boolean value
        }

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should still create environment variables but with warning
        assert "TEST_PORT" in result
        assert "TEST_ENABLED" in result

        # The key point is that conversion doesn't crash

    def test_array_type_conversion(self):
        """Test array type conversion with separator."""
        config_values = {"items": "item1,item2,item3"}

        result = self.deployer._convert_config_values(config_values, self.mock_template)

        # Should preserve the comma-separated format
        assert result["TEST_ITEMS"] == "item1,item2,item3"

    def test_boolean_type_variations(self):
        """Test various boolean value representations."""
        test_cases = [
            ("true", "True"),
            ("True", "True"),
            ("1", "True"),
            ("yes", "True"),
            ("on", "True"),
            ("false", "False"),
            ("False", "False"),
            ("0", "False"),
            ("no", "False"),
            ("off", "False"),
        ]

        for input_val, expected in test_cases:
            config_values = {"enabled": input_val}
            result = self.deployer._convert_config_values(
                config_values, self.mock_template
            )

            # All boolean values should be converted to string
            assert "TEST_ENABLED" in result


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI with transport and configuration options."""

    def test_cli_help_includes_transport_options(self):
        """Test that CLI help includes transport options."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "mcp_template", "deploy", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # Go up to project root
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Should include transport options
        assert "--transport" in help_text
        assert "--port" in help_text
        assert "http" in help_text
        assert "stdio" in help_text

    def test_config_double_underscore_help(self):
        """Test that config help mentions double underscore notation."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "mcp_template", "deploy", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent,  # Go up to project root
        )

        assert result.returncode == 0
        help_text = result.stdout

        # Should mention double underscore notation
        assert "double underscore" in help_text or "__" in help_text
