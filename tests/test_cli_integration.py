"""
Comprehensive integration tests for CLI override functionality
"""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_template import main
from mcp_template.deployer import MCPDeployer


@pytest.mark.integration
class TestCLIIntegration:
    """Test end-to-end CLI integration with override functionality."""

    def test_cli_override_argument_parsing(self):
        """Test that CLI properly parses override arguments."""
        # Mock sys.argv for CLI testing
        test_args = [
            "mcp_template",
            "deploy",
            "demo",
            "--override",
            "metadata__version=2.0.0",
            "--override",
            "tools__0__enabled=false",
            "--config",
            "log_level=debug",
        ]

        with patch("sys.argv", test_args):
            with patch(
                "mcp_template.backends.docker.DockerDeploymentService.deploy_template"
            ) as mock_deploy:
                mock_deploy.return_value = {
                    "success": True,
                    "deployment_id": "test-deployment",
                    "container_id": "test-container",
                }

                try:
                    main()
                except SystemExit:  # CLI may exit after successful deployment
                    pass

                # Verify deploy was called
                mock_deploy.assert_called_once()
                call_args = mock_deploy.call_args

                # Check that template_id was passed correctly
                assert call_args.kwargs["template_id"] == "demo"

                # Check that override values were processed correctly
                config = call_args.kwargs["config"]
                assert config["OVERRIDE_metadata__version"] == "2.0.0"
                assert config["OVERRIDE_tools__0__enabled"] == "false"

                # Check that config values were processed correctly
                assert config["MCP_LOG_LEVEL"] == "debug"

    def test_cli_help_shows_override_option(self, capsys):
        """Test that CLI help displays the override option clearly."""
        test_args = ["mcp_template", "deploy", "--help"]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        help_output = captured.out

        # Verify override option is documented
        assert "--override OVERRIDE" in help_output
        assert "Template data overrides" in help_output
        # The help text may have line breaks, so check for the key parts
        assert "supports double" in help_output and "underscore notation" in help_output
        assert "tools__0__custom_field=value" in help_output

    def test_deploy_with_mixed_config_and_overrides(self):
        """Test deployment with both config and override values."""
        deployer = MCPDeployer()

        # Mock deployment manager and templates
        with patch.object(deployer, "deployment_manager") as mock_manager, patch.object(
            deployer,
            "templates",
            {
                "demo": {
                    "name": "demo",
                    "image": "demo-image:latest",  # Add missing image field
                    "config_schema": {
                        "properties": {
                            "log_level": {
                                "env_mapping": "MCP_LOG_LEVEL",
                                "type": "string",
                            }
                        }
                    },
                }
            },
        ):

            mock_manager.deploy_template.return_value = {
                "deployment_name": "test-deployment",
                "image": "test-image",
                "status": "running",
            }

            # Test with both config and override values
            result = deployer.deploy(
                template_name="demo",
                config_values={"log_level": "debug"},
                override_values={
                    "metadata__version": "2.0.0",
                    "tools__0__enabled": "false",
                    "config__custom_setting": "test_value",
                },
            )

            assert result is True

            # Verify deployment was called
            mock_manager.deploy_template.assert_called_once()
            call_args = mock_manager.deploy_template.call_args

            # Check configuration contains config values
            config = call_args[1]["configuration"]
            assert "MCP_LOG_LEVEL" in config
            assert config["MCP_LOG_LEVEL"] == "debug"

            # Check configuration contains override environment variables
            assert "OVERRIDE_metadata__version" in config
            assert config["OVERRIDE_metadata__version"] == "2.0.0"
            assert "OVERRIDE_tools__0__enabled" in config
            assert config["OVERRIDE_tools__0__enabled"] == "false"
            assert "OVERRIDE_config__custom_setting" in config
            assert config["OVERRIDE_config__custom_setting"] == "test_value"

    def test_complex_nested_overrides(self):
        """Test complex nested override scenarios."""
        deployer = MCPDeployer()

        template_data = {
            "servers": [
                {"name": "server1", "config": {"host": "localhost", "port": 8080}},
                {"name": "server2", "config": {"host": "localhost", "port": 8081}},
            ],
            "global_config": {"logging": {"level": "info", "format": "json"}},
        }

        override_values = {
            "servers__0__config__host": "remote.example.com",
            "servers__1__config__port": "9090",
            "global_config__logging__level": "debug",
            "global_config__security__enabled": "true",
            "new_top_level": "added_value",
        }

        result = deployer._apply_template_overrides(template_data, override_values)

        # Verify complex nested changes
        assert result["servers"][0]["config"]["host"] == "remote.example.com"
        assert result["servers"][0]["config"]["port"] == 8080  # unchanged
        assert result["servers"][1]["config"]["port"] == 9090
        assert result["global_config"]["logging"]["level"] == "debug"
        assert result["global_config"]["logging"]["format"] == "json"  # unchanged
        assert result["global_config"]["security"]["enabled"] is True
        assert result["new_top_level"] == "added_value"

    def test_override_type_conversions(self):
        """Test all supported type conversions in overrides."""
        deployer = MCPDeployer()

        template_data = {"config": {}}
        override_values = {
            "config__boolean_true": "true",
            "config__boolean_false": "false",
            "config__integer": "42",
            "config__float": "3.14",
            "config__string": "hello world",
            "config__json_array": '["item1", "item2", "item3"]',
            "config__json_object": '{"nested": {"key": "value"}}',
            "config__invalid_json": "[invalid json",
        }

        result = deployer._apply_template_overrides(template_data, override_values)

        config = result["config"]
        assert config["boolean_true"] is True
        assert config["boolean_false"] is False
        assert config["integer"] == 42
        assert isinstance(config["integer"], int)
        assert abs(config["float"] - 3.14) < 0.001
        assert isinstance(config["float"], float)
        assert config["string"] == "hello world"
        assert config["json_array"] == ["item1", "item2", "item3"]
        assert config["json_object"] == {"nested": {"key": "value"}}
        assert config["invalid_json"] == "[invalid json"  # Falls back to string

    def test_error_handling(self):
        """Test error handling for invalid override scenarios."""
        deployer = MCPDeployer()

        # Test overriding non-dict with nested structure
        template_data = {"existing_string": "test"}
        override_values = {"existing_string__nested": "value"}

        result = deployer._apply_template_overrides(template_data, override_values)

        # Should create new nested structure at top level
        assert result["existing_string"] == "test"  # Original unchanged
        assert "existing_string__nested" not in result  # Invalid override ignored

    def test_array_boundary_handling(self):
        """Test array boundary conditions."""
        deployer = MCPDeployer()

        template_data = {"items": ["item1"]}
        override_values = {
            "items__5__name": "item6",  # Way beyond current array
            "items__0__modified": "true",  # Modify existing
        }

        result = deployer._apply_template_overrides(template_data, override_values)

        # Array should be extended with empty objects
        assert len(result["items"]) == 6
        assert result["items"][0]["modified"] is True
        assert result["items"][1] == {}  # Auto-created empty
        assert result["items"][5]["name"] == "item6"

    def test_empty_and_none_override_values(self):
        """Test handling of empty or None override values."""
        deployer = MCPDeployer()

        template_data = {"test": "data"}

        # Test empty dict
        result1 = deployer._apply_template_overrides(template_data, {})
        assert result1 == template_data

        # Test None
        result2 = deployer._apply_template_overrides(template_data, None)
        assert result2 == template_data


@pytest.mark.integration
class TestCLIDocumentationExamples:
    """Test that documentation examples actually work."""

    def test_help_examples_are_valid(self):
        """Test that examples shown in help actually work."""
        deployer = MCPDeployer()

        # Example from help text: tools__0__custom_field=value
        template_data = {"tools": [{"name": "tool1"}]}
        override_values = {"tools__0__custom_field": "example_value"}

        result = deployer._apply_template_overrides(template_data, override_values)

        assert result["tools"][0]["custom_field"] == "example_value"
        assert result["tools"][0]["name"] == "tool1"  # Original preserved

    def test_readme_examples_work(self):
        """Test common patterns that would be documented."""
        deployer = MCPDeployer()

        # Common documentation examples
        template_data = {
            "metadata": {"version": "1.0.0"},
            "tools": [{"name": "tool1", "enabled": True}],
            "config": {"debug": False},
        }

        # Examples that should be in documentation
        override_values = {
            "metadata__version": "2.0.0",
            "metadata__author": "User Name",
            "tools__0__enabled": "false",
            "tools__0__description": "Modified tool",
            "config__debug": "true",
            "config__new_setting": "added",
        }

        result = deployer._apply_template_overrides(template_data, override_values)

        # Verify all examples work as expected
        assert result["metadata"]["version"] == "2.0.0"
        assert result["metadata"]["author"] == "User Name"
        assert result["tools"][0]["enabled"] is False
        assert result["tools"][0]["description"] == "Modified tool"
        assert result["tools"][0]["name"] == "tool1"  # Original preserved
        assert result["config"]["debug"] is True
        assert result["config"]["new_setting"] == "added"
