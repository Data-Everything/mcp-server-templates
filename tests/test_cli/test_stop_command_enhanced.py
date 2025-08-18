"""
Tests for the enhanced stop command functionality in typer_cli.py.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from mcp_template.cli import app


@pytest.mark.unit
class TestStopCommandEnhanced:
    """Test enhanced stop command functionality."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_stop_no_arguments_fails(self, runner):
        """Test stop command fails when no arguments provided."""
        result = runner.invoke(app, ["stop"])
        assert result.exit_code == 1
        assert "Please specify what to stop" in result.stdout

    def test_stop_multiple_arguments_fails(self, runner):
        """Test stop command fails when multiple conflicting arguments provided."""
        result = runner.invoke(app, ["stop", "--all", "--template", "demo"])
        assert result.exit_code == 1
        assert "Please specify only one target" in result.stdout

    def test_stop_all_dry_run(self, runner):
        """Test stop all deployments in dry-run mode."""
        result = runner.invoke(app, ["stop", "--all", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop all running deployments" in result.stdout
        assert "Across all backends" in result.stdout

    def test_stop_all_with_backend_dry_run(self, runner):
        """Test stop all deployments on specific backend in dry-run mode."""
        result = runner.invoke(
            app, ["stop", "--all", "--backend", "docker", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop all running deployments" in result.stdout
        assert "Limited to backend: docker" in result.stdout

    def test_stop_template_dry_run(self, runner):
        """Test stop template deployments in dry-run mode."""
        result = runner.invoke(app, ["stop", "--template", "demo", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop all deployments for template: demo" in result.stdout
        assert "Across all backends" in result.stdout

    def test_stop_positional_all_dry_run(self, runner):
        """Test stop with positional 'all' argument."""
        result = runner.invoke(app, ["stop", "all", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop all running deployments" in result.stdout

    def test_stop_positional_template_dry_run(self, runner):
        """Test stop with positional template name."""
        result = runner.invoke(app, ["stop", "demo", "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop all deployments for template: demo" in result.stdout

    def test_stop_deployment_id_dry_run(self, runner):
        """Test stop with deployment ID in dry-run mode."""
        deployment_id = "abcdef123456789012345678"  # Longer than 20 chars

        with patch("mcp_template.typer_cli.MultiBackendManager") as mock_multi:
            mock_manager = Mock()
            mock_manager.detect_backend_for_deployment.return_value = "docker"
            mock_multi.return_value = mock_manager

            result = runner.invoke(app, ["stop", deployment_id, "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert f"Would stop deployment: {deployment_id}" in result.stdout
        assert "Auto-detected backend: docker" in result.stdout

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_all_deployments_single_backend(self, mock_multi, runner):
        """Test stopping all deployments on a single backend."""
        # Mock deployment manager
        mock_deployment_manager = Mock()
        mock_deployment_manager.list_deployments.return_value = [
            {"id": "dep1", "template": "demo", "status": "running"},
            {"id": "dep2", "template": "demo", "status": "running"},
        ]
        mock_deployment_manager.stop_deployment.return_value = {"success": True}

        with patch(
            "mcp_template.typer_cli.DeploymentManager",
            return_value=mock_deployment_manager,
        ):
            result = runner.invoke(
                app, ["stop", "--all", "--backend", "docker", "--force"]
            )

        assert result.exit_code == 0
        assert "Stopped 2 deployment(s)" in result.stdout
        assert mock_deployment_manager.stop_deployment.call_count == 2

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_template_deployments_single_backend(self, mock_multi, runner):
        """Test stopping template deployments on a single backend."""
        # Mock deployment manager
        mock_deployment_manager = Mock()
        mock_deployment_manager.list_deployments.return_value = [
            {"id": "dep1", "template": "demo", "status": "running"},
            {"id": "dep2", "template": "other", "status": "running"},
        ]
        mock_deployment_manager.stop_deployment.return_value = {"success": True}

        with patch(
            "mcp_template.typer_cli.DeploymentManager",
            return_value=mock_deployment_manager,
        ):
            result = runner.invoke(
                app, ["stop", "--template", "demo", "--backend", "docker", "--force"]
            )

        assert result.exit_code == 0
        assert "Stopped 1 'demo' deployment(s)" in result.stdout
        assert mock_deployment_manager.stop_deployment.call_count == 1

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_all_deployments_multi_backend(self, mock_multi, runner):
        """Test stopping all deployments across multiple backends."""
        # Mock multi-backend manager
        mock_manager = Mock()
        mock_manager.get_available_backends.return_value = ["docker", "kubernetes"]
        mock_manager.get_all_deployments.return_value = [
            {
                "id": "dep1",
                "template": "demo",
                "status": "running",
                "backend_type": "docker",
            },
            {
                "id": "dep2",
                "template": "demo",
                "status": "running",
                "backend_type": "kubernetes",
            },
        ]
        mock_manager.stop_deployment.return_value = {"success": True}
        mock_multi.return_value = mock_manager

        result = runner.invoke(app, ["stop", "--all", "--force"])

        assert result.exit_code == 0
        assert "Stopped 2 deployment(s)" in result.stdout
        assert mock_manager.stop_deployment.call_count == 2

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_single_deployment_auto_detection(self, mock_multi, runner):
        """Test stopping single deployment with backend auto-detection."""
        deployment_id = "abcdef123456789012345678"

        # Mock multi-backend manager
        mock_manager = Mock()
        mock_manager.stop_deployment.return_value = {
            "success": True,
            "backend_type": "docker",
        }
        mock_multi.return_value = mock_manager

        result = runner.invoke(app, ["stop", deployment_id])

        assert result.exit_code == 0
        assert f"Successfully stopped deployment '{deployment_id}'" in result.stdout
        assert mock_manager.stop_deployment.called

    @patch("mcp_template.typer_cli.DeploymentManager")
    def test_stop_single_deployment_specific_backend(self, mock_deployment_cls, runner):
        """Test stopping single deployment on specific backend."""
        deployment_id = "abcdef123456789012345678"

        # Mock deployment manager
        mock_deployment_manager = Mock()
        mock_deployment_manager.stop_deployment.return_value = {"success": True}
        mock_deployment_cls.return_value = mock_deployment_manager

        result = runner.invoke(app, ["stop", deployment_id, "--backend", "docker"])

        assert result.exit_code == 0
        assert f"Successfully stopped deployment '{deployment_id}'" in result.stdout
        assert mock_deployment_manager.stop_deployment.called

    def test_stop_no_running_deployments(self, runner):
        """Test stop when no running deployments found."""
        mock_deployment_manager = Mock()
        mock_deployment_manager.list_deployments.return_value = []

        with patch(
            "mcp_template.typer_cli.DeploymentManager",
            return_value=mock_deployment_manager,
        ):
            result = runner.invoke(app, ["stop", "--all", "--backend", "docker"])

        assert result.exit_code == 0
        assert "No running deployments found" in result.stdout

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_deployment_failure(self, mock_multi, runner):
        """Test stop deployment failure handling."""
        deployment_id = "abcdef123456789012345678"

        # Mock multi-backend manager with failure
        mock_manager = Mock()
        mock_manager.stop_deployment.return_value = {
            "success": False,
            "error": "Container not found",
        }
        mock_multi.return_value = mock_manager

        result = runner.invoke(app, ["stop", deployment_id])

        assert result.exit_code == 1
        assert "Failed to stop deployment" in result.stdout
        assert "Container not found" in result.stdout

    def test_stop_help_message(self, runner):
        """Test stop command help message."""
        result = runner.invoke(app, ["stop", "--help"])
        assert result.exit_code == 0
        assert "Stop MCP server deployments" in result.stdout
        assert "Stop specific deployment by ID" in result.stdout
        assert "Stop all deployments" in result.stdout
        assert "Stop all deployments for a template" in result.stdout


@pytest.mark.unit
class TestStopCommandEdgeCases:
    """Test edge cases for stop command."""

    @pytest.fixture
    def runner(self):
        """Create CLI runner for testing."""
        return CliRunner()

    def test_stop_with_custom_timeout(self, runner):
        """Test stop command with custom timeout."""
        deployment_id = "abcdef123456789012345678"

        with patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_cls:
            mock_dm = Mock()
            mock_dm.stop_deployment.return_value = {"success": True}
            mock_dm_cls.return_value = mock_dm

            result = runner.invoke(
                app, ["stop", deployment_id, "--backend", "docker", "--timeout", "60"]
            )

            assert result.exit_code == 0
            # Verify timeout was passed correctly
            mock_dm.stop_deployment.assert_called_with(deployment_id, 60)

    @patch("mcp_template.typer_cli.MultiBackendManager")
    def test_stop_partial_failures(self, mock_multi, runner):
        """Test stop command with some deployment failures."""
        # Mock multi-backend manager
        mock_manager = Mock()
        mock_manager.get_available_backends.return_value = ["docker"]
        mock_manager.get_all_deployments.return_value = [
            {"id": "dep1", "template": "demo", "status": "running"},
            {"id": "dep2", "template": "demo", "status": "running"},
        ]

        # Mock mixed success/failure results
        mock_manager.stop_deployment.side_effect = [
            {"success": True},
            {"success": False, "error": "Network error"},
        ]
        mock_multi.return_value = mock_manager

        result = runner.invoke(app, ["stop", "--all", "--force"])

        assert result.exit_code == 0
        assert "Stopped 1 deployment(s)" in result.stdout
        assert "Failed to stop 1 deployment(s)" in result.stdout

    def test_stop_user_cancellation(self, runner):
        """Test stop command when user cancels confirmation."""
        mock_deployment_manager = Mock()
        mock_deployment_manager.list_deployments.return_value = [
            {"id": "dep1", "template": "demo", "status": "running"},
        ]

        with patch(
            "mcp_template.typer_cli.DeploymentManager",
            return_value=mock_deployment_manager,
        ):
            # Simulate user typing 'n' for no
            result = runner.invoke(
                app, ["stop", "--all", "--backend", "docker"], input="n\n"
            )

        assert result.exit_code == 0
        assert "Stop cancelled" in result.stdout
        # Verify no deployments were actually stopped
        assert not mock_deployment_manager.stop_deployment.called
