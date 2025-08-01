"""
Test CLI override functionality for double underscore notation
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_template.deployer import MCPDeployer


@pytest.mark.unit
class TestCLIOverrides:
    """Test CLI override functionality with double underscore notation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

    def test_simple_override(self):
        """Test simple field override."""
        template_data = {"name": "test", "version": "1.0.0"}
        override_values = {"version": "2.0.0", "author": "Test User"}

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result["version"] == "2.0.0"
        assert result["author"] == "Test User"
        assert result["name"] == "test"  # unchanged

    def test_nested_override(self):
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

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result["metadata"]["version"] == "2.0.0"
        assert result["metadata"]["author"] == "Test User"
        assert result["metadata"]["description"] == "Test"  # unchanged
        assert result["config"]["debug"] is True  # converted to boolean
        assert result["config"]["port"] == 8080  # converted to int

    def test_array_override(self):
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

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result["tools"][0]["enabled"] is False
        assert result["tools"][0]["name"] == "tool1"  # unchanged
        assert result["tools"][1]["description"] == "Updated tool"
        assert result["tools"][1]["name"] == "tool2"  # unchanged

    def test_deep_nested_override(self):
        """Test deeply nested override."""
        template_data = {
            "config": {"database": {"connection": {"host": "localhost", "port": 5432}}}
        }
        override_values = {
            "config__database__connection__host": "remote.example.com",
            "config__database__connection__timeout": "30",
        }

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert (
            result["config"]["database"]["connection"]["host"] == "remote.example.com"
        )
        assert result["config"]["database"]["connection"]["port"] == 5432  # unchanged
        assert result["config"]["database"]["connection"]["timeout"] == 30  # new field

    def test_type_conversion(self):
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

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result["config"]["debug"] is True
        assert result["config"]["verbose"] is False
        assert result["config"]["port"] == 8080
        assert result["config"]["timeout"] == 30.5
        assert result["config"]["name"] == "test-server"
        assert result["config"]["tags"] == ["tag1", "tag2"]
        assert result["config"]["metadata"] == {"key": "value"}

    def test_deploy_method_integration(self):
        """Test that override values are properly passed through deploy method."""
        # Mock the deployment manager and template discovery
        with patch.object(
            self.deployer, "deployment_manager"
        ) as mock_manager, patch.object(
            self.deployer,
            "templates",
            {"test": {"name": "test", "image": "test:latest"}},
        ), patch.object(
            self.deployer, "_generate_mcp_config"
        ):

            mock_manager.deploy_template.return_value = {
                "deployment_name": "test-deployment",
                "status": "deployed",
                "image": "test:latest",
            }

            # Test deploy with override values
            result = self.deployer.deploy(
                template_name="test", override_values={"metadata__version": "2.0.0"}
            )

            # Verify that deploy_template was called and deployment succeeded
            assert mock_manager.deploy_template.called
            assert result is True
            call_args = mock_manager.deploy_template.call_args

            # Check that override values were converted to environment variables
            config = call_args[1]["configuration"]
            assert "OVERRIDE_metadata__version" in config
            assert config["OVERRIDE_metadata__version"] == "2.0.0"


@pytest.mark.unit
class TestCLIOverrideEdgeCases:
    """Test edge cases for CLI override functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

    def test_array_extension(self):
        """Test that arrays are extended when accessing out-of-bounds indices."""
        template_data = {"tools": [{"name": "tool1"}]}
        override_values = {"tools__2__name": "tool3"}

        result = self.deployer._apply_template_overrides(template_data, override_values)

        # Array should be extended with empty objects
        assert len(result["tools"]) == 3
        assert result["tools"][0]["name"] == "tool1"
        assert result["tools"][1] == {}  # empty placeholder
        assert result["tools"][2]["name"] == "tool3"

    def test_invalid_array_index(self):
        """Test handling of non-numeric array indices."""
        template_data = {"config": {"debug": True}}
        override_values = {"config__invalid__nested": "value"}

        # Should create nested dict structure
        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result["config"]["debug"] is True
        assert result["config"]["invalid"]["nested"] == "value"

    def test_empty_override_values(self):
        """Test with empty override values."""
        template_data = {"name": "test"}
        override_values = {}

        result = self.deployer._apply_template_overrides(template_data, override_values)

        assert result == template_data

    def test_none_override_values(self):
        """Test with None override values."""
        template_data = {"name": "test"}

        result = self.deployer._apply_template_overrides(template_data, None)

        assert result == template_data
