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
            template_name="demo",
            discovery_method="auto",
            force_refresh=False,
            include_static=True,
            include_dynamic=True,
        )

    def test_list_tools_static_only(
        self, cli_runner, mock_multi_backend_manager, sample_tools
    ):
        """Test list tools with only static tools."""
        mock_multi_backend_manager.get_available_backends.return_value = [
            "docker",
            "kubernetes",
        ]

        # Return only static tools when --no-dynamic is used
        static_only_tools = {
            "static_tools": sample_tools["static_tools"],
            "dynamic_tools": {},  # Empty when --no-dynamic
            "backend_summary": {},
        }
        mock_multi_backend_manager.get_all_tools.return_value = static_only_tools

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

        # Return only dynamic tools when --no-static is used
        dynamic_only_tools = {
            "static_tools": {},  # Empty when --no-static
            "dynamic_tools": sample_tools["dynamic_tools"],
            "backend_summary": sample_tools["backend_summary"],
        }
        mock_multi_backend_manager.get_all_tools.return_value = dynamic_only_tools

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


@pytest.mark.unit
class TestConfigurationHandling:
    """Test the new configuration handling features in Typer CLI."""

    def test_config_precedence_order(self, cli_runner):
        """Test that config precedence works: env vars > CLI config > config file."""
        # Mock deployment manager and template manager
        with (
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
            patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class,
            patch("mcp_template.typer_cli.ConfigManager") as mock_cm_class,
        ):

            # Setup mocks
            mock_dm = Mock()
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_dm.deploy_template.return_value = DeploymentResult(
                success=True,
                deployment_id="test",
                endpoint="http://localhost:8001",
                duration=1.0,
            )
            mock_dm_class.return_value = mock_dm

            mock_tm = Mock()
            mock_tm.get_template_info.return_value = {
                "name": "demo",
                "transport": {"default": "http", "supported": ["http", "stdio"]},
                "docker_image": "dataeverything/mcp-demo",
            }
            mock_tm.validate_template.return_value = True
            mock_tm_class.return_value = mock_tm

            mock_cm = Mock()
            mock_cm.merge_config_sources.return_value = {
                "key1": "from_env",
                "key2": "from_file",
            }
            mock_cm_class.return_value = mock_cm

            # Create a temporary config file
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                f.write('{"key1": "from_file", "key2": "from_file"}')
                config_file_path = f.name

            try:
                # Test without dry-run to ensure deployment manager is called
                result = cli_runner.invoke(
                    app,
                    [
                        "deploy",
                        "demo",
                        "--config-file",
                        config_file_path,
                        "--config",
                        "key1=from_cli",
                        "--env",
                        "key1=from_env",
                    ],
                )

                assert result.exit_code == 0
                # Verify deployment manager was called
                mock_dm.deploy_template.assert_called_once()

                # Check that config sources were passed to deployment
                call_args = mock_dm.deploy_template.call_args[0]
                template_id = call_args[0]
                config_sources = call_args[1]

                assert template_id == "demo"
                # Check that config sources contain expected structure
                assert config_sources.get("config_file") == config_file_path
                assert config_sources.get("config_values", {}).get("key1") == "from_cli"
                assert config_sources.get("env_vars", {}).get("key1") == "from_env"

            finally:
                os.unlink(config_file_path)

    def test_volumes_json_object_parsing(self, cli_runner):
        """Test that JSON object volumes are parsed correctly."""
        # Mock the dependencies directly within the test
        with (
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
            patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class,
            patch("mcp_template.typer_cli.ConfigManager") as mock_cm_class,
        ):

            # Setup mocks
            mock_dm = Mock()
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_dm.deploy_template.return_value = DeploymentResult(
                success=True,
                deployment_id="test",
                endpoint="http://localhost:8001",
                duration=1.0,
            )
            mock_dm_class.return_value = mock_dm

            mock_tm = Mock()
            mock_tm.get_template_info.return_value = {
                "name": "demo",
                "transport": {"default": "http", "supported": ["http"]},
                "docker_image": "dataeverything/mcp-demo",
                "config_schema": {"required": [], "properties": {}},
            }
            mock_tm.validate_template.return_value = True
            mock_tm_class.return_value = mock_tm

            mock_cm = Mock()
            mock_cm.merge_config_sources.return_value = {
                "VOLUMES": {"./host/path": "/container/path", "./data": "/app/data"}
            }
            mock_cm_class.return_value = mock_cm

            result = cli_runner.invoke(
                app,
                [
                    "deploy",
                    "demo",
                    "--volumes",
                    '{"./host/path": "/container/path", "./data": "/app/data"}',
                ],
            )

            assert result.exit_code == 0
            mock_dm.deploy_template.assert_called_once()

    def test_volumes_json_array_parsing(self, cli_runner):
        """Test that JSON array volumes are parsed correctly."""
        # Mock the dependencies directly within the test
        with (
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
            patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class,
            patch("mcp_template.typer_cli.ConfigManager") as mock_cm_class,
        ):

            # Setup mocks
            mock_dm = Mock()
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_dm.deploy_template.return_value = DeploymentResult(
                success=True,
                deployment_id="test",
                endpoint="http://localhost:8001",
                duration=1.0,
            )
            mock_dm_class.return_value = mock_dm

            mock_tm = Mock()
            mock_tm.get_template_info.return_value = {
                "name": "demo",
                "transport": {"default": "http", "supported": ["http"]},
                "docker_image": "dataeverything/mcp-demo",
                "config_schema": {"required": [], "properties": {}},
            }
            mock_tm.validate_template.return_value = True
            mock_tm_class.return_value = mock_tm

            mock_cm = Mock()
            mock_cm.merge_config_sources.return_value = {
                "VOLUMES": {"/host/path1": "/host/path1", "/host/path2": "/host/path2"}
            }
            mock_cm_class.return_value = mock_cm

            result = cli_runner.invoke(
                app, ["deploy", "demo", "--volumes", '["/host/path1", "/host/path2"]']
            )

            assert result.exit_code == 0
            mock_dm.deploy_template.assert_called_once()

    def test_volumes_invalid_json(self, cli_runner):
        """Test that invalid JSON volumes are handled gracefully."""
        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                '{"invalid": json}',  # Invalid JSON
                "--dry-run",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid JSON format in volumes" in result.stdout

    def test_stdio_template_detection(self, cli_runner):
        """Test that stdio templates are detected and handled properly."""
        # Mock template manager to return stdio template info
        with patch("mcp_template.typer_cli.TemplateManager") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            mock_instance.get_template_info.return_value = {
                "name": "github",
                "transport": {"default": "stdio", "supported": ["stdio"]},
                "docker_image": "dataeverything/mcp-github",
            }

            result = cli_runner.invoke(
                app,
                ["deploy", "github", "--config", "github_token=test123", "--dry-run"],
            )

            assert result.exit_code == 1
            assert "Cannot deploy stdio transport MCP servers" in result.stdout
            assert "Configuration validated successfully" in result.stdout
            assert "github_token: ***" in result.stdout  # Token should be masked

    def test_config_file_option_renamed(self, cli_runner):
        """Test that --config-file option works instead of old --config for files."""
        result = cli_runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "--config-file" in result.stdout
        assert "--config" in result.stdout
        # Should show both options with different purposes
        assert "Path to config file" in result.stdout
        assert "Configuration key=value pairs" in result.stdout

    def test_backward_compatibility_with_set_option(self, cli_runner):
        """Test that existing --set option still works alongside new --config."""
        # Mock the dependencies directly within the test
        with (
            patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class,
            patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class,
            patch("mcp_template.typer_cli.ConfigManager") as mock_cm_class,
        ):

            # Setup mocks
            mock_dm = Mock()
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_dm.deploy_template.return_value = DeploymentResult(
                success=True,
                deployment_id="test",
                endpoint="http://localhost:8001",
                duration=1.0,
            )
            mock_dm_class.return_value = mock_dm

            mock_tm = Mock()
            mock_tm.get_template_info.return_value = {
                "name": "demo",
                "transport": {"default": "http", "supported": ["http"]},
                "docker_image": "dataeverything/mcp-demo",
                "config_schema": {"required": [], "properties": {}},
            }
            mock_tm.validate_template.return_value = True
            mock_tm_class.return_value = mock_tm

            mock_cm = Mock()
            mock_cm.merge_config_sources.return_value = {
                "key1": "from_config",
                "key2": "from_set",
            }
            mock_cm_class.return_value = mock_cm

            result = cli_runner.invoke(
                app,
                [
                    "deploy",
                    "demo",
                    "--config",
                    "key1=from_config",
                    "--set",
                    "key2=from_set",
                ],
            )

            assert result.exit_code == 0
            mock_dm.deploy_template.assert_called_once()


class TestVolumeMountingCLI:
    """Test volume mounting functionality in CLI deploy command."""

    @pytest.fixture
    def mock_deployment_manager(self):
        """Mock deployment manager for volume tests."""
        with patch("mcp_template.typer_cli.DeploymentManager") as mock_dm_class:
            mock_dm = Mock()
            # Mock successful deployment with proper DeploymentResult
            from mcp_template.core.deployment_manager import DeploymentResult

            mock_dm.deploy_template.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                endpoint="http://localhost:8001",
                duration=1.0,
            )
            mock_dm_class.return_value = mock_dm
            yield mock_dm

    @pytest.fixture
    def mock_template_manager(self):
        """Mock template manager for volume tests."""
        with patch("mcp_template.typer_cli.TemplateManager") as mock_tm_class:
            mock_tm = Mock()
            mock_tm.get_template_info.return_value = {
                "name": "demo",
                "docker_image": "dataeverything/mcp-demo",
                "transport": {"default": "http", "supported": ["http"]},
                "config_schema": {"required": [], "properties": {}},
            }
            mock_tm.validate_template.return_value = True
            mock_tm_class.return_value = mock_tm
            yield mock_tm

    @pytest.fixture
    def mock_config_manager(self):
        """Mock config manager for volume tests."""
        with patch("mcp_template.typer_cli.ConfigManager") as mock_cm_class:
            mock_cm = Mock()
            # Mock merge_config_sources to return a simple config
            mock_cm.merge_config_sources.return_value = {"api_key": "test123"}
            mock_cm_class.return_value = mock_cm
            yield mock_cm

    def test_deploy_with_volumes_json_object(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with volumes as JSON object."""
        volumes_json = (
            '{"@HOST_DATA_PATH@": "/app/data", "@HOST_CONFIG_PATH@": "/app/config"}'
        )

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        # Check that volumes were parsed and passed correctly
        call_args = mock_deployment_manager.deploy_template.call_args
        config_sources = call_args[0][1]  # Second positional argument in args tuple
        volumes_arg = config_sources.get("config_values", {}).get("VOLUMES")

        expected_volumes = {
            "@HOST_DATA_PATH@": "/app/data",
            "@HOST_CONFIG_PATH@": "/app/config",
        }
        assert volumes_arg == expected_volumes

    def test_deploy_with_volumes_json_array(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with volumes as JSON array."""
        volumes_json = (
            '["@HOST_DATA_PATH@:/app/data", "@HOST_CONFIG_PATH@:/app/config:ro"]'
        )

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        # Check that volumes were parsed and passed correctly
        call_args = mock_deployment_manager.deploy_template.call_args
        config_sources = call_args[0][1]  # Second positional argument in args tuple
        volumes_config = config_sources.get("config_values", {}).get("VOLUMES")

        # For JSON array format, each item is treated as both host and container path
        expected_volumes_dict = {
            "@HOST_DATA_PATH@:/app/data": "@HOST_DATA_PATH@:/app/data",
            "@HOST_CONFIG_PATH@:/app/config:ro": "@HOST_CONFIG_PATH@:/app/config:ro",
        }
        assert volumes_config == expected_volumes_dict

    def test_deploy_with_volumes_invalid_json(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with invalid JSON volumes."""
        volumes_json = '{"invalid": json}'

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 1
        assert "Invalid JSON format" in result.stdout

    def test_deploy_with_volumes_unsupported_type(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with unsupported volume type."""
        volumes_json = '"just a string"'

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 1
        assert "must be a JSON object or array" in result.stdout

    def test_deploy_with_volumes_help_text(self, cli_runner):
        """Test that deploy command help includes volume documentation."""
        result = cli_runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "--volumes" in result.stdout
        assert "Volume mounts (JSON object or array)" in result.stdout

    def test_deploy_with_volumes_and_config_integration(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with both volumes and config working together."""
        volumes_json = '{"@HOST_DATA_PATH@": "/app/data"}'

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "HOST_DATA_PATH=/home/user/data",
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        call_args = mock_deployment_manager.deploy_template.call_args
        config_sources = call_args[0][1]  # Second positional argument in args tuple
        volumes_arg = config_sources.get("config_values", {}).get("VOLUMES")
        config_values = config_sources.get("config_values", {})

        # Check both volumes and config were passed
        assert volumes_arg == {"@HOST_DATA_PATH@": "/app/data"}
        assert config_values.get("HOST_DATA_PATH") == "/home/user/data"
        assert config_values.get("api_key") == "test123"

    def test_deploy_with_volumes_dry_run(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command dry run includes volume information."""
        volumes_json = (
            '{"@HOST_DATA_PATH@": "/app/data", "@HOST_LOGS_PATH@": "/app/logs"}'
        )

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "VOLUMES" in result.stdout
        assert "Config Keys" in result.stdout

        # Should not actually deploy
        mock_deployment_manager.deploy_template.assert_not_called()

    def test_deploy_with_volumes_empty_object(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with empty volume object."""
        volumes_json = "{}"

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        call_args = mock_deployment_manager.deploy_template.call_args
        config_sources = call_args[0][1]  # Second positional argument in args tuple
        volumes_arg = config_sources.get("config_values", {}).get("VOLUMES")
        assert volumes_arg == {}

    def test_deploy_with_volumes_empty_array(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command with empty volume array."""
        volumes_json = "[]"

        result = cli_runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--volumes",
                volumes_json,
                "--config",
                "api_key=test123",
            ],
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        call_args = mock_deployment_manager.deploy_template.call_args
        config_sources = call_args[0][1]  # Second positional argument in args tuple
        volumes_arg = config_sources.get("config_values", {}).get("VOLUMES")
        assert volumes_arg == {}

    def test_deploy_without_volumes_parameter(
        self,
        cli_runner,
        mock_deployment_manager,
        mock_template_manager,
        mock_config_manager,
    ):
        """Test deploy command works normally without volumes parameter."""
        result = cli_runner.invoke(
            app, ["deploy", "demo", "--config", "api_key=test123"]
        )

        assert result.exit_code == 0
        mock_deployment_manager.deploy_template.assert_called_once()

        call_args = mock_deployment_manager.deploy_template.call_args
        # volumes should not be in the call when not specified
        assert "volumes" not in call_args[1] or call_args[1].get("volumes") is None
