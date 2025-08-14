"""
Tests for shell command functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_template.cli import CLI


@pytest.mark.unit
class TestShellCommand:
    """Test shell command functionality."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CLI()

    @pytest.fixture
    def mock_args(self):
        """Create mock args for shell command."""
        args = Mock()
        args.template = None
        args.name = None
        return args

    def test_shell_with_template_name_single_deployment(self, cli, mock_args):
        """Test shell access with template name and single running deployment."""
        mock_args.template = "demo"

        # Mock single running deployment
        running_deployments = [{"id": "demo_container_1", "status": "running"}]

        with (
            patch.object(
                cli.deployment_manager,
                "find_deployments_by_criteria",
                return_value=running_deployments,
            ),
            patch.object(
                cli.deployment_manager, "connect_to_deployment"
            ) as mock_connect,
            patch.object(cli.formatter, "print_info") as mock_info,
        ):

            cli.handle_shell_command(mock_args)

            # Verify deployment was found and connection attempted
            cli.deployment_manager.find_deployments_by_criteria.assert_called_once_with(
                template_name="demo", status="running"
            )
            mock_connect.assert_called_once_with("demo_container_1")

    def test_shell_with_template_name_multiple_deployments(self, cli, mock_args):
        """Test shell access with template name and multiple running deployments."""
        mock_args.template = "demo"

        # Mock multiple running deployments
        running_deployments = [
            {"id": "demo_container_1", "status": "running"},
            {"id": "demo_container_2", "status": "running"},
        ]

        with (
            patch.object(
                cli.deployment_manager,
                "find_deployments_by_criteria",
                return_value=running_deployments,
            ),
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_shell_command(mock_args)

            # Verify error was shown for multiple deployments
            mock_error.assert_called_once()
            assert "Multiple running deployments found" in mock_error.call_args[0][0]

    def test_shell_with_template_name_no_deployments(self, cli, mock_args):
        """Test shell access with template name but no running deployments."""
        mock_args.template = "demo"

        # Mock no running deployments
        running_deployments = []

        with (
            patch.object(
                cli.deployment_manager,
                "find_deployments_by_criteria",
                return_value=running_deployments,
            ),
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_shell_command(mock_args)

            # Verify error was shown for no deployments
            mock_error.assert_called_with("Template demo has no running deployments")

    def test_shell_with_custom_name(self, cli, mock_args):
        """Test shell access with custom container name."""
        mock_args.name = "custom_container"

        with (
            patch.object(
                cli.deployment_manager, "connect_to_deployment"
            ) as mock_connect,
            patch.object(cli.formatter, "print_info") as mock_info,
        ):

            cli.handle_shell_command(mock_args)

            # Verify connection was attempted with custom name
            mock_connect.assert_called_once_with("custom_container")

    def test_shell_without_template_or_name(self, cli, mock_args):
        """Test shell command without template name or custom name."""
        # Both template and name are None

        with (
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_shell_command(mock_args)

            mock_error.assert_called_with("Template name or custom name is required")

    def test_shell_connection_failure(self, cli, mock_args):
        """Test shell command when connection fails."""
        mock_args.name = "custom_container"

        with (
            patch.object(
                cli.deployment_manager,
                "connect_to_deployment",
                side_effect=Exception("Connection failed"),
            ),
            patch.object(cli.formatter, "print_error") as mock_error,
            pytest.raises(SystemExit),
        ):

            cli.handle_shell_command(mock_args)

            mock_error.assert_called_with("Error accessing shell: Connection failed")

    def test_shell_with_template_and_custom_name(self, cli, mock_args):
        """Test shell access when both template and custom name are provided."""
        mock_args.template = "demo"
        mock_args.name = "custom_container"

        # When both are provided, custom name should take precedence
        with (
            patch.object(
                cli.deployment_manager, "connect_to_deployment"
            ) as mock_connect,
            patch.object(cli.formatter, "print_info") as mock_info,
        ):

            cli.handle_shell_command(mock_args)

            # Should connect directly with custom name, not search for deployments
            mock_connect.assert_called_once_with("custom_container")
