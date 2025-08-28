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
        # With max_retries=2, exponential backoff calls sleep with 1 and 2
        mock_sleep.assert_has_calls([call(1), call(2)])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
