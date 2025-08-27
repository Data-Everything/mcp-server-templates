"""
Unit tests for the Podman backend module (mcp_template.backends.podman).

Tests Podman container deployment functionality.
"""

import json
import subprocess
from unittest.mock import Mock, call, patch

import pytest

from mcp_template.backends.podman import PodmanDeploymentService

pytestmark = pytest.mark.unit


class TestPodmanDeploymentService:
    """Test the PodmanDeploymentService class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            self.service = PodmanDeploymentService()

    def test_init(self):
        """Test PodmanDeploymentService initialization."""
        with patch.object(
            PodmanDeploymentService, "_check_podman_available"
        ) as mock_check:
            service = PodmanDeploymentService()
            mock_check.assert_called_once()

    def test_inherits_from_base_backend(self):
        """Test that PodmanDeploymentService inherits from BaseDeploymentBackend."""
        from mcp_template.backends.base import BaseDeploymentBackend

        assert isinstance(self.service, BaseDeploymentBackend)

    @patch("subprocess.run")
    def test_check_podman_available_success(self, mock_run):
        """Test successful Podman availability check."""
        mock_run.return_value = Mock(returncode=0, stdout="podman version 4.0.0")

        service = PodmanDeploymentService()
        result = service._check_podman_available()

        assert result is True
        mock_run.assert_called_with(
            ["podman", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    @patch("subprocess.run")
    def test_check_podman_available_failure(self, mock_run):
        """Test Podman availability check failure."""
        mock_run.side_effect = FileNotFoundError("podman command not found")

        with pytest.raises(RuntimeError, match="Podman is not available"):
            PodmanDeploymentService()

    @patch("subprocess.run")
    def test_check_podman_available_non_zero_exit(self, mock_run):
        """Test Podman availability check with non-zero exit code."""
        mock_run.return_value = Mock(returncode=1, stderr="Command failed")

        with pytest.raises(RuntimeError, match="Podman is not available"):
            PodmanDeploymentService()

    @patch("subprocess.run")
    def test_is_available_property(self, mock_run):
        """Test is_available property."""
        mock_run.return_value = Mock(returncode=0)

        with patch.object(
            PodmanDeploymentService, "_check_podman_available", return_value=True
        ):
            service = PodmanDeploymentService()
            assert service.is_available is True


class TestPodmanDeploymentServiceDeployment:
    """Test deployment functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            self.service = PodmanDeploymentService()

    @patch.object(PodmanDeploymentService, "_pull_image")
    @patch.object(PodmanDeploymentService, "_run_container")
    def test_deploy_template_success(self, mock_run, mock_pull):
        """Test successful template deployment."""
        mock_pull.return_value = True
        mock_run.return_value = {
            "success": True,
            "deployment_id": "test-container-123",
            "status": "running",
        }

        result = self.service.deploy_template(
            template_id="demo",
            config={"greeting": "Hello"},
            template_data={"docker_image": "demo:latest"},
            backend_config={},
        )

        assert result["success"] is True
        assert "deployment_id" in result
        mock_pull.assert_called_once()
        mock_run.assert_called_once()

    @patch.object(PodmanDeploymentService, "_pull_image")
    def test_deploy_template_pull_failure(self, mock_pull):
        """Test deployment when image pull fails."""
        mock_pull.return_value = False

        result = self.service.deploy_template(
            template_id="demo",
            config={},
            template_data={"docker_image": "demo:latest"},
            backend_config={},
        )

        assert result["success"] is False
        assert "error" in result

    @patch.object(PodmanDeploymentService, "_pull_image")
    @patch.object(PodmanDeploymentService, "_run_container")
    def test_deploy_template_no_pull(self, mock_run, mock_pull):
        """Test deployment without image pull."""
        mock_run.return_value = {"success": True, "deployment_id": "test"}

        self.service.deploy_template(
            template_id="demo",
            config={},
            template_data={"docker_image": "demo:latest"},
            backend_config={},
            pull_image=False,
        )

        mock_pull.assert_not_called()
        mock_run.assert_called_once()

    @patch.object(PodmanDeploymentService, "_pull_image")
    def test_deploy_template_dry_run(self, mock_pull):
        """Test deployment in dry-run mode."""
        result = self.service.deploy_template(
            template_id="demo",
            config={},
            template_data={"docker_image": "demo:latest"},
            backend_config={},
            dry_run=True,
        )

        assert result["success"] is True
        assert "dry_run" in result
        mock_pull.assert_not_called()

    @patch("subprocess.run")
    def test_pull_image_success(self, mock_run):
        """Test successful image pull."""
        mock_run.return_value = Mock(returncode=0, stdout="Image pulled successfully")

        result = self.service._pull_image("demo:latest")

        assert result is True
        mock_run.assert_called_with(
            ["podman", "pull", "demo:latest"],
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

    @patch("subprocess.run")
    def test_pull_image_failure(self, mock_run):
        """Test image pull failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Pull failed")

        result = self.service._pull_image("demo:latest")

        assert result is False

    @patch("subprocess.run")
    def test_pull_image_timeout(self, mock_run):
        """Test image pull timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("podman", 300)

        result = self.service._pull_image("demo:latest")

        assert result is False

    @patch("subprocess.run")
    @patch.object(PodmanDeploymentService, "_find_available_port")
    def test_run_container_success(self, mock_port, mock_run):
        """Test successful container run."""
        mock_port.return_value = 8080
        mock_run.return_value = Mock(returncode=0, stdout="container-id-123\n")

        result = self.service._run_container(
            "demo:latest",
            "test-demo",
            config={"greeting": "Hello"},
            env_vars={"DEBUG": "true"},
        )

        assert result["success"] is True
        assert result["deployment_id"] == "container-id-123"

    @patch("subprocess.run")
    def test_run_container_failure(self, mock_run):
        """Test container run failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Run failed")

        result = self.service._run_container("demo:latest", "test-demo")

        assert result["success"] is False
        assert "error" in result

    @patch("socket.socket")
    def test_find_available_port_success(self, mock_socket):
        """Test finding an available port."""
        mock_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 1  # Port not in use

        port = self.service._find_available_port(start_port=8000, end_port=8002)

        assert port == 8000

    @patch("socket.socket")
    def test_find_available_port_all_busy(self, mock_socket):
        """Test when all ports are busy."""
        mock_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # All ports in use

        port = self.service._find_available_port(start_port=8000, end_port=8002)

        assert port is None


class TestPodmanDeploymentServiceManagement:
    """Test deployment management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            self.service = PodmanDeploymentService()

    @patch("subprocess.run")
    def test_stop_deployment_success(self, mock_run):
        """Test successful deployment stop."""
        mock_run.return_value = Mock(returncode=0)

        result = self.service.stop_deployment("container-123")

        assert result["success"] is True
        mock_run.assert_called_with(
            ["podman", "stop", "container-123"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @patch("subprocess.run")
    def test_stop_deployment_failure(self, mock_run):
        """Test deployment stop failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Stop failed")

        result = self.service.stop_deployment("container-123")

        assert result["success"] is False

    @patch("subprocess.run")
    def test_get_deployment_status_running(self, mock_run):
        """Test getting status of running deployment."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "Id": "container-123",
                        "State": {"Status": "running"},
                        "Config": {"Image": "demo:latest"},
                    }
                ]
            ),
        )

        result = self.service.get_deployment_status("container-123")

        assert result["status"] == "running"
        assert result["deployment_id"] == "container-123"

    @patch("subprocess.run")
    def test_get_deployment_status_not_found(self, mock_run):
        """Test getting status of non-existent deployment."""
        mock_run.return_value = Mock(returncode=0, stdout="[]")

        result = self.service.get_deployment_status("non-existent")

        assert result["status"] == "not_found"

    @patch("subprocess.run")
    def test_list_deployments_success(self, mock_run):
        """Test listing deployments."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(
                [
                    {
                        "Id": "container-1",
                        "State": {"Status": "running"},
                        "Config": {"Image": "demo:latest"},
                        "Labels": {"mcp-template": "demo"},
                    },
                    {
                        "Id": "container-2",
                        "State": {"Status": "stopped"},
                        "Config": {"Image": "github:latest"},
                        "Labels": {"mcp-template": "github"},
                    },
                ]
            ),
        )

        result = self.service.list_deployments()

        assert len(result) == 2
        assert result[0]["deployment_id"] == "container-1"
        assert result[0]["status"] == "running"

    @patch("subprocess.run")
    def test_get_deployment_logs_success(self, mock_run):
        """Test getting deployment logs."""
        mock_run.return_value = Mock(
            returncode=0, stdout="log line 1\nlog line 2\nlog line 3\n"
        )

        result = self.service.get_deployment_logs("container-123", lines=50)

        assert len(result) == 3
        assert result[0] == "log line 1"
        mock_run.assert_called_with(
            ["podman", "logs", "--tail", "50", "container-123"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @patch("subprocess.run")
    def test_get_deployment_logs_no_lines_limit(self, mock_run):
        """Test getting deployment logs without lines limit."""
        mock_run.return_value = Mock(returncode=0, stdout="log line 1\n")

        self.service.get_deployment_logs("container-123")

        mock_run.assert_called_with(
            ["podman", "logs", "container-123"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @patch("subprocess.run")
    def test_health_check_success(self, mock_run):
        """Test successful health check."""
        mock_run.return_value = Mock(returncode=0, stdout="podman version 4.0.0")

        result = self.service.health_check()

        assert result["status"] == "healthy"
        assert "version" in result

    @patch("subprocess.run")
    def test_health_check_failure(self, mock_run):
        """Test health check failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "podman")

        result = self.service.health_check()

        assert result["status"] == "unhealthy"


class TestPodmanDeploymentServiceStdioExecution:
    """Test stdio tool execution functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            self.service = PodmanDeploymentService()

    @patch("subprocess.Popen")
    def test_execute_tool_success(self, mock_popen):
        """Test successful tool execution."""
        mock_process = Mock()
        mock_process.communicate.return_value = (
            b'{"result": {"output": "tool executed successfully"}}',
            b"",
        )
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.service.execute_tool(
            "container-123", "search_files", {"pattern": "*.py", "path": "/app"}
        )

        assert result["success"] is True
        assert "result" in result

    @patch("subprocess.Popen")
    def test_execute_tool_timeout(self, mock_popen):
        """Test tool execution timeout."""
        mock_process = Mock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("podman", 30)
        mock_process.kill = Mock()
        mock_popen.return_value = mock_process

        result = self.service.execute_tool("container-123", "slow_tool", {})

        assert result["success"] is False
        assert "timeout" in result["error"].lower()
        mock_process.kill.assert_called_once()

    @patch("subprocess.Popen")
    def test_execute_tool_invalid_json_response(self, mock_popen):
        """Test tool execution with invalid JSON response."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"invalid json", b"")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = self.service.execute_tool("container-123", "broken_tool", {})

        assert result["success"] is False
        assert "json" in result["error"].lower()

    @patch("subprocess.Popen")
    def test_execute_tool_non_zero_exit(self, mock_popen):
        """Test tool execution with non-zero exit code."""
        mock_process = Mock()
        mock_process.communicate.return_value = (b"", b"Error occurred")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = self.service.execute_tool("container-123", "failing_tool", {})

        assert result["success"] is False


class TestPodmanDeploymentServiceConfiguration:
    """Test configuration and environment handling."""

    def test_stdio_timeout_default(self):
        """Test default STDIO timeout."""
        from mcp_template.backends.podman import STDIO_TIMEOUT

        assert STDIO_TIMEOUT == 30

    @patch.dict("os.environ", {"MCP_STDIO_TIMEOUT": "60"})
    def test_stdio_timeout_from_env(self):
        """Test STDIO timeout from environment."""
        # Re-import to get updated environment value
        import importlib

        from mcp_template.backends import podman

        importlib.reload(podman)

        assert podman.STDIO_TIMEOUT == 60

    @patch.dict("os.environ", {"MCP_STDIO_TIMEOUT": "invalid"})
    def test_stdio_timeout_invalid_env(self):
        """Test STDIO timeout with invalid environment value."""
        import importlib

        from mcp_template.backends import podman

        importlib.reload(podman)

        # Should fall back to default
        assert podman.STDIO_TIMEOUT == 30

    def test_generate_container_name(self):
        """Test container name generation."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            service = PodmanDeploymentService()

            name = service._generate_container_name("demo")

            assert name.startswith("mcp-demo-")
            assert len(name.split("-")) >= 3  # mcp-demo-<uuid>

    def test_build_podman_command(self):
        """Test Podman command building."""
        with patch.object(PodmanDeploymentService, "_check_podman_available"):
            service = PodmanDeploymentService()

            cmd = service._build_run_command(
                image="demo:latest",
                container_name="mcp-demo-123",
                port=8080,
                env_vars={"DEBUG": "true"},
                server_args=["--config", "/app/config.yaml"],
            )

            assert "podman" in cmd
            assert "run" in cmd
            assert "-d" in cmd  # Detached
            assert "demo:latest" in cmd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
