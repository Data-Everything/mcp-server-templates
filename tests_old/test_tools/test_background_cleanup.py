"""
Tests for background cleanup functionality in Docker probe.
"""

import time
import unittest
from unittest.mock import Mock, patch

import pytest

from mcp_template.tools.docker_probe import DockerProbe

pytestmark = pytest.mark.unit


class TestBackgroundCleanup(unittest.TestCase):
    """Test background cleanup functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.probe = DockerProbe()

    def test_background_cleanup_success(self):
        """Test successful background cleanup."""
        container_name = "test-container-success"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            # Start background cleanup and wait for completion
            self.probe._background_cleanup(container_name)
            time.sleep(0.1)  # Give thread time to execute

            # Should call docker rm -f
            mock_run.assert_called_with(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

    def test_cleanup_container_normal_success(self):
        """Test normal container cleanup without background threading."""
        container_name = "test-container-normal"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            # Start cleanup
            self.probe._cleanup_container(container_name)

            # Should call docker stop and docker rm -f (synchronously, timeout=30)
            expected_calls = [
                unittest.mock.call(
                    ["docker", "stop", container_name],
                    capture_output=True,
                    timeout=5,
                    check=False,
                ),
                unittest.mock.call(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    timeout=30,
                    check=True,
                ),
            ]
            mock_run.assert_has_calls(expected_calls)


if __name__ == "__main__":
    unittest.main()
