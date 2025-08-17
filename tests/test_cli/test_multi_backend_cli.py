"""
Test Multi-Backend CLI Operations.

This module tests the new multi-backend functionality in CLI commands,
ensuring they properly aggregate data from multiple backends and provide
backward compatibility when using single-backend mode.
"""

import json
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mcp_template.typer_cli import app

pytestmark = pytest.mark.unit


@pytest.fixture
def cli_runner():
    """Fixture for CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_multi_backend_manager():
    """Fixture for mocked MultiBackendManager."""
    with patch("mcp_template.typer_cli.MultiBackendManager") as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def sample_deployments():
    """Sample deployment data for testing."""
    return [
        {
            "id": "docker-123",
            "template": "demo",
            "status": "running",
            "backend_type": "docker",
            "created_at": "2024-01-01T10:00:00Z",
            "endpoint": "http://localhost:8001",
        },
        {
            "id": "k8s-456",
            "template": "github",
            "status": "running",
            "backend_type": "kubernetes",
            "created_at": "2024-01-01T11:00:00Z",
            "endpoint": "http://github-service:8080",
        },
        {
            "id": "mock-789",
            "template": "demo",
            "status": "stopped",
            "backend_type": "mock",
            "created_at": "2024-01-01T12:00:00Z",
            "endpoint": "mock://demo",
        },
    ]


@pytest.fixture
def sample_tools():
    """Sample tool data for testing."""
    return {
        "static_tools": {
            "demo": {
                "tools": [
                    {"name": "echo", "description": "Echo a message"},
                    {"name": "greet", "description": "Greet someone"},
                ],
                "source": "template_definition",
            }
        },
        "dynamic_tools": {
            "docker": [
                {
                    "name": "echo",
                    "description": "Echo a message",
                    "deployment_id": "docker-123",
                    "template": "demo",
                    "backend": "docker",
                }
            ],
            "kubernetes": [
                {
                    "name": "create_issue",
                    "description": "Create GitHub issue",
                    "deployment_id": "k8s-456",
                    "template": "github",
                    "backend": "kubernetes",
                }
            ],
        },
        "backend_summary": {
            "docker": {"tool_count": 1, "deployment_count": 1},
            "kubernetes": {"tool_count": 1, "deployment_count": 1},
        },
    }


@pytest.mark.unit
class TestMultiBackendListDeployments:
    """Test multi-backend list deployments command."""

    def test_list_deployments_multi_backend_default(
        self, cli_runner, mock_multi_backend_manager, sample_deployments
    ):
        """Test list deployments shows all backends by default."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
            "mock",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = sample_deployments

        result = cli_runner.invoke(app, ["list-deployments"])

        assert result.exit_code == 0
        assert "docker" in result.stdout.lower()
        assert "kubernetes" in result.stdout.lower()
        assert "docker-123" in result.stdout
        assert "k8s-456" in result.stdout

        # Verify multi-backend manager was used
        mock_multi_backend_manager.get_all_deployments.assert_called_once_with(
            template_name=None
        )

    def test_list_deployments_single_backend_mode(self, cli_runner):
        """Test list deployments with --backend flag uses single backend."""
        with patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class:
            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            mock_dm.list_deployments.return_value = [
                {
                    "id": "test-123",
                    "template": "demo",
                    "status": "running",
                    "created_at": "2024-01-01T10:00:00Z",
                }
            ]

            result = cli_runner.invoke(app, ["list-deployments", "--backend", "docker"])

            assert result.exit_code == 0
            mock_dm_class.assert_called_once_with("docker")
            mock_dm.list_deployments.assert_called_once()

    def test_list_deployments_filter_by_template(
        self, cli_runner, mock_multi_backend_manager, sample_deployments
    ):
        """Test list deployments with template filter."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
            "mock",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = sample_deployments

        result = cli_runner.invoke(app, ["list-deployments", "--template", "demo"])

        assert result.exit_code == 0
        mock_multi_backend_manager.get_all_deployments.assert_called_once_with(
            template_name="demo"
        )

    def test_list_deployments_filter_by_status(
        self, cli_runner, mock_multi_backend_manager, sample_deployments
    ):
        """Test list deployments with status filter."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
            "mock",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = sample_deployments

        result = cli_runner.invoke(app, ["list-deployments", "--status", "running"])

        assert result.exit_code == 0
        # Should show only running deployments
        assert "docker-123" in result.stdout
        assert "k8s-456" in result.stdout
        assert "mock-789" not in result.stdout  # This one is stopped

    def test_list_deployments_json_output(
        self, cli_runner, mock_multi_backend_manager, sample_deployments
    ):
        """Test list deployments with JSON output format."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
            "mock",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = sample_deployments

        result = cli_runner.invoke(
            app, ["list-deployments", "--format", "json", "--all"]
        )

        assert result.exit_code == 0

        # Parse JSON output to verify structure
        output_data = json.loads(result.stdout)
        assert isinstance(output_data, list)
        assert len(output_data) == 3

    def test_list_deployments_no_backends(self, cli_runner, mock_multi_backend_manager):
        """Test list deployments when no backends are available."""
        mock_multi_backend_manager.get_available_backends.return_value = []

        result = cli_runner.invoke(app, ["list-deployments"])

        assert result.exit_code == 0
        assert "No backends available" in result.stdout

    def test_list_deployments_no_deployments(
        self, cli_runner, mock_multi_backend_manager
    ):
        """Test list deployments when no deployments exist."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = []

        result = cli_runner.invoke(app, ["list-deployments"])

        assert result.exit_code == 0
        assert "No deployments found" in result.stdout


@pytest.mark.unit
class TestMultiBackendListTools:
    """Test multi-backend list tools command."""

    def test_list_tools_multi_backend_default(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools shows all backends by default."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_tools.return_value = sample_tools

        result = cli_runner.invoke(app, ["list-tools"])

        assert result.exit_code == 0
        assert "Static Tools" in result.stdout
        assert "Dynamic Tools" in result.stdout
        assert "echo" in result.stdout
        assert "create_issue" in result.stdout

        mock_multi_backend_manager.get_all_tools.assert_called_once()

    def test_list_tools_single_backend_mode(self, cli_runner):
        """Test list tools with --backend flag uses single backend."""
        with patch("mcp_template.typer_cli.ToolManager") as mock_tm_class:
            mock_tm = Mock()
            mock_tm_class.return_value = mock_tm
            mock_tm.list_tools.return_value = {
                "tools": [{"name": "test_tool", "description": "Test tool"}],
                "metadata": {"cached": False},
            }

            result = cli_runner.invoke(
                app, ["list-tools", "demo", "--backend", "docker"]
            )

            assert result.exit_code == 0
            mock_tm_class.assert_called_once_with("docker")
            mock_tm.list_tools.assert_called_once()

    def test_list_tools_filter_by_template(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools with template filter."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_tools.return_value = sample_tools

        result = cli_runner.invoke(app, ["list-tools", "demo"])

        assert result.exit_code == 0
        mock_multi_backend_manager.get_all_tools.assert_called_once_with(
            template_name="demo", discovery_method="auto", force_refresh=False
        )

    def test_list_tools_static_only(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools with only static tools."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_tools.return_value = sample_tools

        result = cli_runner.invoke(app, ["list-tools", "--no-dynamic"])

        assert result.exit_code == 0
        assert "Static Tools" in result.stdout
        # Should not show dynamic tools section
        assert "Dynamic Tools" not in result.stdout

    def test_list_tools_dynamic_only(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools with only dynamic tools."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_tools.return_value = sample_tools

        result = cli_runner.invoke(app, ["list-tools", "--no-static"])

        assert result.exit_code == 0
        assert "Dynamic Tools" in result.stdout
        # Should not show static tools section
        assert "Static Tools" not in result.stdout

    def test_list_tools_json_output(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools with JSON output format."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_tools.return_value = sample_tools

        result = cli_runner.invoke(app, ["list-tools", "--format", "json"])

        assert result.exit_code == 0

        # Extract JSON from output (skip progress spinner text and footer text)
        json_start = result.stdout.find("{")
        json_end = result.stdout.rfind("}") + 1
        json_part = (
            result.stdout[json_start:json_end]
            if json_start != -1 and json_end > json_start
            else result.stdout
        )

        # Parse JSON output to verify structure
        output_data = json.loads(json_part)
        assert "static_tools" in output_data
        assert "dynamic_tools" in output_data
        assert "backend_summary" in output_data


@pytest.mark.unit
class TestMultiBackendStop:
    """Test multi-backend stop command with auto-detection."""

    def test_stop_auto_detection_success(self, cli_runner, mock_multi_backend_manager):
        """Test stop command with successful auto-detection."""
        mock_multi_backend_manager.stop_deployment.return_value = {
            "success": True,
            "backend_type": "docker",
        }

        result = cli_runner.invoke(app, ["stop", "test-deployment-123"])

        assert result.exit_code == 0
        assert "Successfully stopped" in result.stdout
        assert "DOCKER" in result.stdout
        mock_multi_backend_manager.stop_deployment.assert_called_once_with(
            "test-deployment-123", 30
        )

    def test_stop_auto_detection_failure(self, cli_runner, mock_multi_backend_manager):
        """Test stop command when auto-detection fails."""
        mock_multi_backend_manager.stop_deployment.return_value = {
            "success": False,
            "error": "Deployment test-deployment-123 not found in any backend",
        }

        result = cli_runner.invoke(app, ["stop", "test-deployment-123"])

        assert result.exit_code == 1
        assert "Failed to stop deployment" in result.stdout
        assert "Try using --backend" in result.stdout

    def test_stop_specific_backend(self, cli_runner):
        """Test stop command with specific backend."""
        with patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class:
            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            mock_dm.stop_deployment.return_value = {"success": True}

            result = cli_runner.invoke(
                app, ["stop", "test-deployment-123", "--backend", "docker"]
            )

            assert result.exit_code == 0
            assert "Successfully stopped" in result.stdout
            mock_dm_class.assert_called_once_with("docker")
            mock_dm.stop_deployment.assert_called_once_with("test-deployment-123", 30)

    def test_stop_dry_run_mode(self, cli_runner, mock_multi_backend_manager):
        """Test stop command in dry-run mode."""
        mock_multi_backend_manager.detect_backend_for_deployment.return_value = "docker"

        result = cli_runner.invoke(app, ["stop", "test-deployment-123", "--dry-run"])

        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would stop deployment" in result.stdout
        assert "Auto-detected backend: docker" in result.stdout

        # Should not actually call stop
        mock_multi_backend_manager.stop_deployment.assert_not_called()

    def test_stop_dry_run_detection_failure(
        self, cli_runner, mock_multi_backend_manager
    ):
        """Test stop dry-run when backend detection fails."""
        mock_multi_backend_manager.detect_backend_for_deployment.return_value = None

        result = cli_runner.invoke(app, ["stop", "test-deployment-123", "--dry-run"])

        assert result.exit_code == 0
        assert "Backend auto-detection would fail" in result.stdout

    def test_stop_custom_timeout(self, cli_runner, mock_multi_backend_manager):
        """Test stop command with custom timeout."""
        mock_multi_backend_manager.stop_deployment.return_value = {
            "success": True,
            "backend_type": "docker",
        }

        result = cli_runner.invoke(
            app, ["stop", "test-deployment-123", "--timeout", "60"]
        )

        assert result.exit_code == 0
        mock_multi_backend_manager.stop_deployment.assert_called_once_with(
            "test-deployment-123", 60
        )


@pytest.mark.unit
class TestMultiBackendLogs:
    """Test multi-backend logs command with auto-detection."""

    def test_logs_auto_detection_success(self, cli_runner, mock_multi_backend_manager):
        """Test logs command with successful auto-detection."""
        mock_multi_backend_manager.get_deployment_logs.return_value = {
            "success": True,
            "logs": "Test log output\nAnother log line",
            "backend_type": "kubernetes",
        }

        result = cli_runner.invoke(app, ["logs", "test-deployment-456"])

        assert result.exit_code == 0
        assert "Test log output" in result.stdout
        assert "KUBERNETES" in result.stdout
        mock_multi_backend_manager.get_deployment_logs.assert_called_once_with(
            "test-deployment-456", lines=100, follow=False
        )

    def test_logs_auto_detection_failure(self, cli_runner, mock_multi_backend_manager):
        """Test logs command when auto-detection fails."""
        mock_multi_backend_manager.get_deployment_logs.return_value = {
            "success": False,
            "error": "Deployment test-deployment-456 not found in any backend",
        }

        result = cli_runner.invoke(app, ["logs", "test-deployment-456"])

        assert result.exit_code == 1
        assert "Failed to get logs" in result.stdout
        assert "Try using --backend" in result.stdout

    def test_logs_specific_backend(self, cli_runner):
        """Test logs command with specific backend."""
        with patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class:
            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            mock_dm.get_deployment_logs.return_value = {
                "success": True,
                "logs": "Backend-specific logs",
            }

            result = cli_runner.invoke(
                app, ["logs", "test-deployment-456", "--backend", "kubernetes"]
            )

            assert result.exit_code == 0
            assert "Backend-specific logs" in result.stdout
            mock_dm_class.assert_called_once_with("kubernetes")
            mock_dm.get_deployment_logs.assert_called_once_with(
                "test-deployment-456", lines=100, follow=False
            )

    def test_logs_custom_options(self, cli_runner, mock_multi_backend_manager):
        """Test logs command with custom lines and follow options."""
        mock_multi_backend_manager.get_deployment_logs.return_value = {
            "success": True,
            "logs": "Custom log output",
            "backend_type": "docker",
        }

        result = cli_runner.invoke(
            app, ["logs", "test-deployment-789", "--lines", "50", "--follow"]
        )

        assert result.exit_code == 0
        mock_multi_backend_manager.get_deployment_logs.assert_called_once_with(
            "test-deployment-789", lines=50, follow=True
        )


@pytest.mark.unit
class TestMultiBackendStatus:
    """Test multi-backend status command."""

    def test_status_command_success(self, cli_runner, mock_multi_backend_manager):
        """Test status command shows backend health and deployment summary."""
        health_data = {
            "docker": {"status": "healthy", "deployment_count": 2, "error": None},
            "kubernetes": {"status": "healthy", "deployment_count": 1, "error": None},
            "mock": {
                "status": "unhealthy",
                "deployment_count": 0,
                "error": "Connection failed",
            },
        }
        deployments = [
            {"id": "docker-123", "status": "running", "backend_type": "docker"},
            {"id": "docker-456", "status": "stopped", "backend_type": "docker"},
            {"id": "k8s-789", "status": "running", "backend_type": "kubernetes"},
        ]

        mock_multi_backend_manager.get_backend_health.return_value = health_data
        mock_multi_backend_manager.get_all_deployments.return_value = deployments

        result = cli_runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "Backend Health Status" in result.stdout
        assert "Deployment Summary" in result.stdout
        assert "Total deployments: 3" in result.stdout
        assert "Running deployments: 2" in result.stdout

    def test_status_json_output(self, cli_runner, mock_multi_backend_manager):
        """Test status command with JSON output."""
        health_data = {"docker": {"status": "healthy", "deployment_count": 1}}
        deployments = [
            {"id": "test-123", "status": "running", "backend_type": "docker"}
        ]

        mock_multi_backend_manager.get_backend_health.return_value = health_data
        mock_multi_backend_manager.get_all_deployments.return_value = deployments

        result = cli_runner.invoke(app, ["status", "--format", "json"])

        assert result.exit_code == 0

        # Extract JSON from output (skip progress spinner text)
        json_start = result.stdout.find("{")
        json_part = result.stdout[json_start:] if json_start != -1 else result.stdout

        # Parse JSON output
        output_data = json.loads(json_part)
        assert "backend_health" in output_data
        assert "deployments" in output_data
        assert "summary" in output_data
        assert output_data["summary"]["total_backends"] == 1
        assert output_data["summary"]["total_deployments"] == 1


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test that existing single-backend behavior is preserved."""

    def test_list_with_backend_flag_preserves_behavior(self, cli_runner):
        """Test that --backend flag preserves original single-backend behavior."""
        with (
            patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class,
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
        ):

            mock_tm = Mock()
            mock_dm = Mock()
            mock_tm_class.return_value = mock_tm
            mock_dm_class.return_value = mock_dm

            mock_tm.list_templates.return_value = {
                "demo": {"description": "Demo template"}
            }
            mock_dm.list_deployments.return_value = [
                {"template": "demo", "status": "running"}
            ]

            result = cli_runner.invoke(app, ["list", "--backend", "docker"])

            assert result.exit_code == 0
            mock_tm_class.assert_called_once_with("docker")
            mock_dm_class.assert_called_once_with("docker")

    def test_environment_variable_backend_selection(self, cli_runner):
        """Test that environment variables work for backend selection."""
        with (
            patch.dict("os.environ", {"MCP_BACKEND": "kubernetes"}),
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
        ):

            mock_dm = Mock()
            mock_dm_class.return_value = mock_dm
            mock_dm.list_deployments.return_value = []

            # Single backend commands should still use environment variable
            result = cli_runner.invoke(
                app, ["list-deployments", "--backend", "kubernetes"]
            )

            assert result.exit_code == 0
            mock_dm_class.assert_called_once_with("kubernetes")


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling in multi-backend operations."""

    def test_multi_backend_manager_initialization_failure(self, cli_runner):
        """Test graceful handling when MultiBackendManager fails to initialize."""
        with patch(
            "mcp_template.typer_cli.MultiBackendManager",
            side_effect=Exception("Backend init failed"),
        ):
            result = cli_runner.invoke(app, ["list-deployments"])

            assert result.exit_code == 1
            assert "Error listing deployments" in result.stdout

    def test_partial_backend_failure(self, cli_runner, mock_multi_backend_manager):
        """Test handling when some backends fail but others succeed."""
        # Mock scenario where some backends return data and others fail
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]
        mock_multi_backend_manager.get_all_deployments.return_value = [
            {"id": "docker-123", "status": "running", "backend_type": "docker"}
        ]  # kubernetes backend failed to return data

        result = cli_runner.invoke(app, ["list-deployments"])

        assert result.exit_code == 0
        assert "docker-123" in result.stdout

    def test_verbose_error_output(self, cli_runner):
        """Test that verbose mode shows detailed error information."""
        with patch(
            "mcp_template.typer_cli.MultiBackendManager",
            side_effect=Exception("Detailed error"),
        ):
            # Test with verbose flag
            result = cli_runner.invoke(app, ["--verbose", "list-deployments"])

            assert result.exit_code == 1
            # Should see the error in verbose mode
