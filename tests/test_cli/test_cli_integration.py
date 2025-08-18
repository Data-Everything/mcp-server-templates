"""
Comprehensive integration tests for CLI override functionality
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template import main


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
            "--transport",
            "http",
            "--override",
            "metadata__version=2.0.0",
            "--override",
            "tools__0__enabled=false",
            "--set",
            "log_level=debug",
        ]

        with patch("sys.argv", test_args):
            with patch(
                "mcp_template.core.deployment_manager.DeploymentManager.deploy_template"
            ) as mock_deploy:
                from mcp_template.core.deployment_manager import DeploymentResult

                mock_deploy.return_value = DeploymentResult(
                    success=True,
                    deployment_id="test-deployment",
                    container_id="test-container",
                )

                try:
                    main()
                except SystemExit:  # CLI may exit after successful deployment
                    pass

                # Verify deploy was called
                mock_deploy.assert_called_once()
                call_args = mock_deploy.call_args

                # Check that template name was passed correctly
                assert call_args.args[0] == "demo"  # First positional argument

                # Check that config values were processed correctly
                config_sources = call_args.args[
                    1
                ]  # Second positional argument (now config_sources)

                # The new structure passes config_sources, so we need to check the appropriate fields
                # Override values should be in 'override_values'
                assert config_sources["override_values"]["metadata__version"] == "2.0.0"
                assert config_sources["override_values"]["tools__0__enabled"] == "false"
                # Config values should be in 'config_values'
                assert config_sources["config_values"]["log_level"] == "debug"
                assert config_sources["config_values"]["MCP_TRANSPORT"] == "http"

    def test_cli_help_shows_override_option(self, capsys):
        """Test that CLI help displays the override option clearly."""
        test_args = ["mcp_template", "deploy", "--help"]

        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        help_output = captured.out

        # Verify override option is documented
        assert "--override" in help_output
        assert "Template data overrides" in help_output
        # The help text may have line breaks, so check for the key parts
        assert (
            "supports double underscore" in help_output
            and "notation for nested fields" in help_output
        )
        assert "tools__0__custom_field=value" in help_output
