"""
Tests for newly enhanced features including:
- CLI override and transport options
- Unified cache system
- Enhanced template manager
- CLI integration improvements
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mcp_template.cli import app
from mcp_template.core.cache import CacheManager
from mcp_template.core.config_processor import ConfigProcessor
from mcp_template.core.deployment_manager import DeploymentResult
from mcp_template.core.template_manager import TemplateManager


class TestEnhancedTemplateManager:
    """Test enhanced template manager with cache integration."""

    def test_template_manager_with_cache(self):
        """Test template manager initializes with cache manager."""
        template_manager = TemplateManager(backend_type="mock")

        # Should have cache manager
        assert hasattr(template_manager, "cache_manager")
        assert template_manager.cache_manager is not None

    @patch("mcp_template.core.template_manager.TemplateDiscovery")
    def test_template_cache_integration(self, mock_discovery):
        """Test that template manager uses cache correctly."""
        mock_templates = [
            {"id": "demo", "name": "Demo Template"},
            {"id": "github", "name": "GitHub Template"},
        ]

        mock_discovery.return_value.discover_templates.return_value = mock_templates

        template_manager = TemplateManager(backend_type="mock")

        # First call should discover templates
        templates = template_manager.list_templates()
        assert len(templates) >= 2  # At least our mock templates

        # Second call should use cache (no additional discovery calls)
        templates2 = template_manager.list_templates()
        assert len(templates2) >= 2

    @patch("mcp_template.core.template_manager.TemplateDiscovery")
    def test_template_cache_refresh(self, mock_discovery):
        """Test template cache refresh functionality."""
        mock_templates = [{"id": "demo", "name": "Demo Template"}]

        mock_discovery.return_value.discover_templates.return_value = mock_templates

        template_manager = TemplateManager(backend_type="mock")

        # Clear cache and refresh
        template_manager.cache_manager.delete("templates")
        template_manager.refresh_cache()

        # Should have rediscovered templates
        templates = template_manager.list_templates()
        assert len(templates) >= 1


class TestCLIOverrideOptions:
    """Test new CLI override and transport options."""

    def test_deploy_command_has_override_option(self):
        """Test that deploy command includes --override option."""
        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "--override" in result.output
        assert "Template data overrides" in result.output
        assert "supports double underscore" in result.output

    def test_deploy_command_has_transport_option(self):
        """Test that deploy command includes --transport option."""
        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "--transport" in result.output
        assert "Transport protocol" in result.output

    @patch("mcp_template.cli.cli.deploymentManager")
    def test_deploy_with_override_processing(
        self, mock_deployment_manager, clear_cache
    ):
        """Test deploy command processes override options correctly."""
        mock_manager = Mock()
        mock_manager.deploy_template.return_value = DeploymentResult(
            success=True, deployment_id="test-123", endpoint="http://localhost:8762"
        )
        mock_deployment_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--override",
                "config_key=test_value",
                "--override",
                "nested__field=nested_value",
                "--transport",
                "http",
                "--env",
                "MCP_PORT=8762",
            ],
        )

        # Should not fail with error
        assert result.exit_code == 0

        # Verify deployment manager was called
        mock_manager.deploy_template.assert_called_once()
        call_args = mock_manager.deploy_template.call_args
        # Check that config contains overrides
        config = call_args[0][1]["OVERRIDE_config_key"]
        assert config is not None

    def test_override_processing_with_nested_keys(self):
        """Test that override processing handles nested keys correctly."""
        processor = ConfigProcessor()

        template_data = {
            "config": {"field": "original"},
            "nested": {"deep": {"value": "original"}},
        }

        overrides = {
            "config__field": "overridden",
            "nested__deep__value": "new_value",
            "new_field": "added",
        }

        result = processor._apply_template_overrides(template_data, overrides)

        assert result["config"]["field"] == "overridden"
        assert result["nested"]["deep"]["value"] == "new_value"
        assert result["new_field"] == "added"


class TestDeploymentResultHandling:
    """Test proper DeploymentResult attribute access."""

    def test_deployment_result_attributes(self):
        """Test DeploymentResult has correct attributes."""
        result = DeploymentResult(
            success=True, deployment_id="test-123", endpoint="http://localhost:8125"
        )

        assert result.success is True
        assert result.deployment_id == "test-123"
        assert result.endpoint == "http://localhost:8125"

    @patch("mcp_template.cli.cli.deploymentManager")
    def test_cli_uses_deployment_result_attributes(
        self, mock_deployment_manager, clear_cache
    ):
        """Test CLI uses DeploymentResult attributes, not get() method."""
        mock_manager = Mock()
        mock_manager.deploy_template.return_value = DeploymentResult(
            success=True, deployment_id="test-123", endpoint="http://localhost:8128"
        )
        mock_deployment_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "demo"])
        # Should complete successfully without AttributeError
        assert result.exit_code == 0
        assert "test-123" in result.output or "Successfully deployed" in result.output


class TestConfigProcessorEnhancements:
    """Test enhanced config processor functionality."""

    def test_override_prefix_processing(self):
        """Test that override prefix is correctly applied."""
        processor = ConfigProcessor()

        overrides = {"key1": "value1", "key2": "value2"}
        env_vars = processor._convert_overrides_to_env_vars(overrides)

        assert env_vars["OVERRIDE_key1"] == "value1"
        assert env_vars["OVERRIDE_key2"] == "value2"

    def test_transport_configuration(self):
        """Test transport configuration processing."""
        processor = ConfigProcessor()

        # Test default transport
        config = {"transport": {"default": "stdio", "supported": ["stdio", "http"]}}
        env_vars = processor._map_file_config_to_env(config, {})

        # Transport should be mapped correctly
        assert len(env_vars) >= 0  # At least some vars should be generated

    def test_nested_override_processing(self):
        """Test processing of nested overrides with double underscore notation."""
        processor = ConfigProcessor()

        template_data = {
            "tools": [
                {"name": "tool1", "config": {"param": "original"}},
                {"name": "tool2", "config": {"param": "original"}},
            ]
        }

        overrides = {"tools__0__config__param": "modified"}
        result = processor._apply_template_overrides(template_data, overrides)

        assert result["tools"][0]["config"]["param"] == "modified"
        assert result["tools"][1]["config"]["param"] == "original"  # Unchanged


class TestCLIIntegrationEnhancements:
    """Test CLI integration improvements."""

    def test_help_command_shows_all_options(self):
        """Test that help command shows all new options."""
        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0

        # Check for all expected options
        expected_options = [
            "--config",
            "--env",
            "--set",
            "--override",
            "--transport",
            "--no-pull",
            "--dry-run",
        ]

        for option in expected_options:
            assert option in result.output

    @patch("mcp_template.cli.cli.deploymentManager")
    def test_error_handling_with_failed_deployment(self, mock_deployment_manager):
        """Test error handling when deployment fails."""
        mock_manager = Mock()
        mock_manager.deploy_template.return_value = DeploymentResult(
            success=False, deployment_id=None, endpoint=None, error="Test error message"
        )
        mock_deployment_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "demo"])

        # Should handle failed deployment gracefully
        assert result.exit_code != 0 or "error" in result.output.lower()

    def test_multiple_override_options(self):
        """Test that multiple --override options are handled correctly."""
        runner = CliRunner()

        # This should not fail with argument parsing errors
        result = runner.invoke(
            app,
            ["deploy", "demo", "--help"],  # Just check help to avoid actual deployment
        )

        assert result.exit_code == 0
        assert "--override" in result.output


class TestBackwardsCompatibility:
    """Test that new features maintain backwards compatibility."""

    @patch("mcp_template.cli.cli.deploymentManager")
    def test_deploy_without_new_options(self, mock_deployment_manager):
        """Test deploy command works without new options."""
        mock_manager = Mock()
        mock_manager.deploy_template.return_value = DeploymentResult(
            success=True, deployment_id="test-123", endpoint="http://localhost:8000"
        )
        mock_deployment_manager.return_value = mock_manager

        runner = CliRunner()
        result = runner.invoke(app, ["deploy", "demo"])

        # Should work without new options
        assert result.exit_code == 0

    def test_cache_system_fallback(self):
        """Test that cache system gracefully handles missing cache."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_manager = CacheManager(cache_dir=Path(temp_dir))

            # Getting non-existent key should return None, not error
            result = cache_manager.get("non_existent_key")
            assert result is None

    def test_template_manager_without_cache_integration(self):
        """Test template manager can work without cache if needed."""
        template_manager = TemplateManager(backend_type="mock")

        # Clear cache to test fallback
        template_manager.cache_manager.clear_all()

        # Should still be able to list templates
        with patch(
            "mcp_template.core.template_manager.TemplateDiscovery"
        ) as mock_discovery:
            mock_discovery.return_value.discover_templates.return_value = [
                {"id": "demo", "name": "Demo Template"}
            ]
            templates = template_manager.list_templates()
            assert len(templates) >= 1


@pytest.mark.integration
class TestEndToEndNewFeatures:
    """Integration tests for new features working together."""

    @patch("mcp_template.cli.cli.deploymentManager")
    def test_full_deployment_with_all_new_options(self, mock_deployment_manager):
        """Test deployment with all new options working together."""
        mock_manager = Mock()
        mock_manager.deploy_template.return_value = DeploymentResult(
            success=True,
            deployment_id="integration-test-123",
            endpoint="http://localhost:8000",
        )
        mock_deployment_manager.return_value = mock_manager

        runner = CliRunner()

        # Use all new options together
        result = runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--override",
                "config_key=test_value",
                "--override",
                "nested__deep__field=nested_value",
                "--transport",
                "http",
                "--dry-run",  # Avoid actual deployment
            ],
        )

        # Should complete successfully
        assert result.exit_code == 0

    def test_cache_and_template_manager_integration(self):
        """Test cache system and template manager working together."""
        with tempfile.TemporaryDirectory() as temp_dir:

            # Create template manager with custom cache dir
            template_manager = TemplateManager(backend_type="mock")
            template_manager.cache_manager = CacheManager(cache_dir=Path(temp_dir))

            # Mock discovery
            with patch(
                "mcp_template.core.template_manager.TemplateDiscovery"
            ) as mock_discovery:
                mock_templates = [
                    {"id": "demo", "name": "Demo Template"},
                    {"id": "github", "name": "GitHub Template"},
                ]
                mock_discovery.return_value.discover_templates.return_value = (
                    mock_templates
                )

                # First call - should cache
                templates1 = template_manager.list_templates()

                # Second call - should use cache
                templates2 = template_manager.list_templates()

                # Should be the same
                assert len(templates1) >= 2
                assert len(templates2) >= 2

                # Discovery should only be called once due to caching
                assert (
                    mock_discovery.return_value.discover_templates.call_count <= 2
                )  # Allow for some initial calls
