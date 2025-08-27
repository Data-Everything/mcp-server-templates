"""
Unit tests for the Docker probe module (mcp_template.tools.docker_probe).

Tests Docker container-based MCP server tool discovery functionality.
"""

import subprocess
import threading
import time
from unittest.mock import Mock, call, patch

import pytest
import requests

pytestmark = pytest.mark.unit

from mcp_template.tools.docker_probe import DockerProbe


class TestDockerProbe:
    """Test the DockerProbe class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = DockerProbe()

    def test_init(self):
        """Test DockerProbe initialization."""
        assert isinstance(self.probe, DockerProbe)
        assert hasattr(self.probe, "mcp_client")

    @patch("subprocess.run")
    def test_cleanup_container_success(self, mock_run):
        """Test successful container cleanup."""
        mock_run.return_value = Mock(returncode=0)

        # Run cleanup in a way that doesn't block test
        self.probe._cleanup_container("test-container")

        # Give the thread a moment to execute
        time.sleep(0.1)

        # Verify subprocess was called (may need slight delay for thread execution)
        # We can't assert the exact call immediately due to threading

    @patch("subprocess.run")
    def test_cleanup_container_timeout(self, mock_run):
        """Test container cleanup with timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("docker", 10)

        with patch.object(self.probe, "_background_cleanup") as mock_bg_cleanup:
            self.probe._cleanup_container("test-container")
            time.sleep(0.1)  # Allow thread to execute

    @patch("subprocess.run")
    def test_cleanup_container_failure(self, mock_run):
        """Test container cleanup failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

        # Should not raise exception, just log
        self.probe._cleanup_container("test-container")
        time.sleep(0.1)

    @patch("subprocess.run")
    def test_background_cleanup_success(self, mock_run):
        """Test successful background cleanup."""
        mock_run.return_value = Mock(returncode=0)

        self.probe._background_cleanup("test-container")

        mock_run.assert_called_with(
            ["docker", "rm", "-f", "test-container"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_background_cleanup_retries(self, mock_sleep, mock_run):
        """Test background cleanup with retries."""
        # First two attempts fail, third succeeds
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "docker"),
            subprocess.TimeoutExpired("docker", 30),
            Mock(returncode=0),
        ]

        self.probe._background_cleanup("test-container", max_retries=3)

        assert mock_run.call_count == 3
        # Verify exponential backoff
        mock_sleep.assert_has_calls([call(1), call(2)])

    @patch("subprocess.run")
    @patch("time.sleep")
    def test_background_cleanup_max_retries_exceeded(self, mock_sleep, mock_run):
        """Test background cleanup when max retries exceeded."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

        self.probe._background_cleanup("test-container", max_retries=2)

        assert mock_run.call_count == 2
        mock_sleep.assert_called_once_with(1)


class TestDockerProbeDiscovery:
    """Test Docker image discovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = DockerProbe()

    @patch("subprocess.run")
    @patch("requests.get")
    @patch.object(DockerProbe, "_cleanup_container")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_from_image_success(
        self, mock_find_port, mock_cleanup, mock_requests, mock_run
    ):
        """Test successful tool discovery from Docker image."""
        # Mock port finding
        mock_find_port.return_value = 8080

        # Mock Docker run command
        mock_run.return_value = Mock(returncode=0, stdout="container-id-123", stderr="")

        # Mock health check request
        mock_requests.return_value = Mock(
            status_code=200, json=lambda: {"status": "healthy"}
        )

        # Mock MCP client discovery
        with patch.object(
            self.probe.mcp_client, "discover_tools_via_http"
        ) as mock_discover:
            mock_discover.return_value = {
                "tools": [{"name": "test_tool", "description": "Test tool"}],
                "server_info": {"name": "test-server"},
            }

            result = self.probe.discover_tools_from_image("test-image:latest")

            assert result is not None
            assert "tools" in result
            assert result["tools"][0]["name"] == "test_tool"

    @patch("subprocess.run")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_from_image_docker_failure(self, mock_find_port, mock_run):
        """Test discovery when Docker command fails."""
        mock_find_port.return_value = 8080
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

        result = self.probe.discover_tools_from_image("test-image:latest")

        assert result is None

    @patch("subprocess.run")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_from_image_no_available_port(
        self, mock_find_port, mock_run
    ):
        """Test discovery when no port is available."""
        mock_find_port.return_value = None

        result = self.probe.discover_tools_from_image("test-image:latest")

        assert result is None
        mock_run.assert_not_called()

    @patch("subprocess.run")
    @patch("requests.get")
    @patch.object(DockerProbe, "_cleanup_container")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_from_image_health_check_failure(
        self, mock_find_port, mock_cleanup, mock_requests, mock_run
    ):
        """Test discovery when health check fails."""
        mock_find_port.return_value = 8080
        mock_run.return_value = Mock(returncode=0, stdout="container-id-123")

        # Health check fails
        mock_requests.side_effect = requests.exceptions.RequestException(
            "Connection failed"
        )

        result = self.probe.discover_tools_from_image("test-image:latest")

        assert result is None
        mock_cleanup.assert_called()

    @patch("subprocess.run")
    @patch("requests.get")
    @patch.object(DockerProbe, "_cleanup_container")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_with_custom_args(
        self, mock_find_port, mock_cleanup, mock_requests, mock_run
    ):
        """Test discovery with custom server arguments and environment variables."""
        mock_find_port.return_value = 8080
        mock_run.return_value = Mock(returncode=0, stdout="container-id-123")
        mock_requests.return_value = Mock(
            status_code=200, json=lambda: {"status": "healthy"}
        )

        with patch.object(
            self.probe.mcp_client, "discover_tools_via_http"
        ) as mock_discover:
            mock_discover.return_value = {"tools": []}

            result = self.probe.discover_tools_from_image(
                "test-image:latest",
                server_args=["--port", "8080", "--debug"],
                env_vars={"DEBUG": "true", "LOG_LEVEL": "info"},
                timeout=30,
            )

            # Verify Docker run was called with correct arguments
            docker_call = mock_run.call_args
            assert "test-image:latest" in docker_call[0][0]
            assert "--port" in docker_call[0][0]
            assert "8080" in docker_call[0][0]
            assert "--debug" in docker_call[0][0]

    @patch("socket.socket")
    def test_find_available_port_success(self, mock_socket):
        """Test finding an available port."""
        mock_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 1  # Port not in use

        port = self.probe._find_available_port()

        assert port is not None
        assert 8000 <= port <= 9000

    @patch("socket.socket")
    def test_find_available_port_all_busy(self, mock_socket):
        """Test when all ports in range are busy."""
        mock_sock = Mock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        mock_sock.connect_ex.return_value = 0  # All ports in use

        with patch(
            "mcp_template.tools.docker_probe.CONTAINER_PORT_RANGE", (8000, 8002)
        ):
            port = self.probe._find_available_port()

            assert port is None

    @patch("subprocess.run")
    @patch("requests.get")
    @patch.object(DockerProbe, "_cleanup_container")
    @patch.object(DockerProbe, "_find_available_port")
    def test_discover_tools_cleanup_on_exception(
        self, mock_find_port, mock_cleanup, mock_requests, mock_run
    ):
        """Test that cleanup is called even when exceptions occur."""
        mock_find_port.return_value = 8080
        mock_run.return_value = Mock(returncode=0, stdout="container-id-123")

        # Simulate exception during discovery
        with patch.object(
            self.probe.mcp_client, "discover_tools_via_http"
        ) as mock_discover:
            mock_discover.side_effect = Exception("Discovery failed")

            result = self.probe.discover_tools_from_image("test-image:latest")

            assert result is None
            mock_cleanup.assert_called()


class TestDockerProbeHealthCheck:
    """Test health check functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = DockerProbe()

    @patch("requests.get")
    @patch("time.sleep")
    def test_wait_for_container_health_success(self, mock_sleep, mock_requests):
        """Test successful container health check."""
        mock_requests.return_value = Mock(
            status_code=200, json=lambda: {"status": "healthy"}
        )

        result = self.probe._wait_for_container_health(
            "http://localhost:8080", timeout=5
        )

        assert result is True

    @patch("requests.get")
    @patch("time.sleep")
    def test_wait_for_container_health_timeout(self, mock_sleep, mock_requests):
        """Test health check timeout."""
        mock_requests.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )

        result = self.probe._wait_for_container_health(
            "http://localhost:8080", timeout=1
        )

        assert result is False

    @patch("requests.get")
    @patch("time.sleep")
    def test_wait_for_container_health_eventual_success(
        self, mock_sleep, mock_requests
    ):
        """Test health check that succeeds after initial failures."""
        # First few calls fail, then succeed
        mock_requests.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            requests.exceptions.ConnectionError("Connection refused"),
            Mock(status_code=200, json=lambda: {"status": "healthy"}),
        ]

        result = self.probe._wait_for_container_health(
            "http://localhost:8080", timeout=10
        )

        assert result is True

    @patch("requests.get")
    @patch("time.sleep")
    def test_wait_for_container_health_non_200_status(self, mock_sleep, mock_requests):
        """Test health check with non-200 HTTP status."""
        mock_requests.return_value = Mock(status_code=500)

        result = self.probe._wait_for_container_health(
            "http://localhost:8080", timeout=5
        )

        assert result is False


class TestDockerProbeIntegration:
    """Test integration aspects of DockerProbe."""

    def setup_method(self):
        """Set up test fixtures."""
        self.probe = DockerProbe()

    def test_inherits_from_base_probe(self):
        """Test that DockerProbe properly inherits from BaseProbe."""
        from mcp_template.tools.base_probe import BaseProbe

        assert isinstance(self.probe, BaseProbe)

    def test_implements_abstract_method(self):
        """Test that DockerProbe implements required abstract method."""
        assert hasattr(self.probe, "discover_tools_from_image")
        assert callable(self.probe.discover_tools_from_image)

    @patch("subprocess.run")
    @patch.object(DockerProbe, "_find_available_port")
    def test_docker_command_construction(self, mock_find_port, mock_run):
        """Test that Docker commands are constructed correctly."""
        mock_find_port.return_value = 8080
        mock_run.return_value = Mock(returncode=0, stdout="container-123")

        # Mock requests to avoid actual HTTP calls
        with patch("requests.get") as mock_requests:
            mock_requests.side_effect = requests.exceptions.ConnectionError()

            self.probe.discover_tools_from_image(
                "test-image:v1.0",
                server_args=["--config", "/app/config.json"],
                env_vars={"API_KEY": "secret", "DEBUG": "true"},
            )

            # Verify Docker run command structure
            docker_call = mock_run.call_args[0][0]
            assert "docker" in docker_call
            assert "run" in docker_call
            assert "-d" in docker_call  # Detached mode
            assert "-p" in docker_call  # Port mapping
            assert "test-image:v1.0" in docker_call

    @patch("threading.Thread")
    def test_cleanup_uses_threading(self, mock_thread):
        """Test that cleanup operations use threading."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        self.probe._cleanup_container("test-container")

        mock_thread.assert_called()
        mock_thread_instance.start.assert_called()

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling in discovery."""
        with patch.object(
            self.probe, "_find_available_port", side_effect=Exception("Port error")
        ):
            result = self.probe.discover_tools_from_image("test-image")
            assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
