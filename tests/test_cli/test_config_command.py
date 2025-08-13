"""
Tests for config command functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_template.cli import CLI


@pytest.mark.unit
class TestConfigCommand:
    """Test config command functionality."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CLI()

    @pytest.fixture
    def mock_args(self):
        """Create mock args for config command."""
        args = Mock()
        args.template = None
        return args

    def test_config_with_valid_template(self, cli, mock_args):
        """Test config command with valid template."""
        mock_args.template = "demo"

        # Mock template schema
        schema = {
            "properties": {
                "hello_from": {
                    "type": "string",
                    "description": "Name or message to include in greetings",
                    "default": "MCP Platform",
                },
                "log_level": {
                    "type": "string",
                    "description": "Logging level for the server",
                    "default": "info",
                },
            }
        }

        with (
            patch.object(
                cli.template_manager, "get_template_config_schema", return_value=schema
            ),
            patch.object(cli.console, "print") as mock_print,
        ):

            cli.handle_config_command(mock_args)

            # Verify schema was retrieved
            cli.template_manager.get_template_config_schema.assert_called_once_with(
                "demo"
            )

            # Verify output was displayed
            mock_print.assert_called()

    def test_config_with_no_schema(self, cli, mock_args):
        """Test config command when template has no schema."""
        mock_args.template = "demo"

        with (
            patch.object(
                cli.template_manager, "get_template_config_schema", return_value=None
            ),
            patch.object(cli.formatter, "print_info") as mock_info,
        ):

            cli.handle_config_command(mock_args)

            mock_info.assert_called_with("No configuration schema found for demo")

    def test_config_with_empty_properties(self, cli, mock_args):
        """Test config command when schema has no properties."""
        mock_args.template = "demo"

        schema = {"properties": {}}

        with (
            patch.object(
                cli.template_manager, "get_template_config_schema", return_value=schema
            ),
            patch.object(cli.formatter, "print_info") as mock_info,
        ):

            cli.handle_config_command(mock_args)

            mock_info.assert_called_with("No configurable properties found")

    def test_config_without_template_name(self, cli, mock_args):
        """Test config command without template name."""
        # Template name is None

        with (
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_config_command(mock_args)

            mock_error.assert_called_with("Template name is required")

    def test_config_error_handling(self, cli, mock_args):
        """Test error handling in config command."""
        mock_args.template = "demo"

        with (
            patch.object(
                cli, "_show_config_options", side_effect=Exception("Schema error")
            ),
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_config_command(mock_args)

            mock_error.assert_called_with("Error showing config: Schema error")

    def test_config_complex_schema(self, cli, mock_args):
        """Test config command with complex schema including various property types."""
        mock_args.template = "complex"

        schema = {
            "properties": {
                "string_prop": {
                    "type": "string",
                    "description": "A string property",
                    "default": "default_value",
                },
                "number_prop": {
                    "type": "number",
                    "description": "A number property",
                    "default": 42,
                },
                "boolean_prop": {
                    "type": "boolean",
                    "description": "A boolean property",
                    "default": True,
                },
                "no_default_prop": {
                    "type": "string",
                    "description": "Property without default",
                },
                "no_description_prop": {"type": "string", "default": "value"},
            }
        }

        with (
            patch.object(
                cli.template_manager, "get_template_config_schema", return_value=schema
            ),
            patch.object(cli.console, "print") as mock_print,
        ):

            cli.handle_config_command(mock_args)

            # Verify schema was retrieved and printed
            cli.template_manager.get_template_config_schema.assert_called_once_with(
                "complex"
            )

            # Should have printed multiple times for each property
            assert (
                mock_print.call_count > 5
            )  # At least one call per property plus headers
