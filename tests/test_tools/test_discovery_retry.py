"""
Tests for discovery retry logic using tenacity.

Tests the retry mechanisms added to Docker and Kubernetes probes
for improved reliability in tool discovery operations.
"""

import os
import subprocess
import time
import unittest.mock
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.tools.docker_probe import DockerProbe
from mcp_template.tools.kubernetes_probe import KubernetesProbe


class TestDiscoveryRetryLogic:
    """Test retry logic for discovery operations."""

    def setup_method(self):
        """Set up test fixtures."""
        # Save original environment variables
        self.original_env = {
            "MCP_DISCOVERY_RETRIES": os.environ.get("MCP_DISCOVERY_RETRIES"),
            "MCP_DISCOVERY_RETRY_SLEEP": os.environ.get("MCP_DISCOVERY_RETRY_SLEEP"),
            "MCP_DISCOVERY_TIMEOUT": os.environ.get("MCP_DISCOVERY_TIMEOUT"),
        }

        # Set test environment variables
        os.environ["MCP_DISCOVERY_RETRIES"] = "3"
        os.environ["MCP_DISCOVERY_RETRY_SLEEP"] = "1"  # Use 1 second for faster tests
        os.environ["MCP_DISCOVERY_TIMEOUT"] = "30"

    def teardown_method(self):
        """Clean up after tests."""
        # Restore original environment variables
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_docker_probe_retry_environment_variables(self):
        """Test that Docker probe uses correct environment variables for retry."""
        # Re-import to get the current environment variables
        import importlib

        import mcp_template.tools.docker_probe

        importlib.reload(mcp_template.tools.docker_probe)

        probe = mcp_template.tools.docker_probe.DockerProbe()

        # Check that constants are properly loaded from environment
        from mcp_template.tools.docker_probe import (
            DISCOVERY_RETRIES,
            DISCOVERY_RETRY_SLEEP,
            DISCOVERY_TIMEOUT,
        )

        assert DISCOVERY_RETRIES == 3
        assert DISCOVERY_RETRY_SLEEP == 1  # Set in setup_method
        assert DISCOVERY_TIMEOUT == 30

    def test_kubernetes_probe_retry_environment_variables(self):
        """Test that Kubernetes probe uses correct environment variables for retry."""
        # Re-import to get the current environment variables
        import importlib

        import mcp_template.tools.kubernetes_probe

        importlib.reload(mcp_template.tools.kubernetes_probe)

        with patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config"):
            with patch("mcp_template.tools.kubernetes_probe.config.load_kube_config"):
                with patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api"):
                    with patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api"):
                        probe = mcp_template.tools.kubernetes_probe.KubernetesProbe()

        # Check that constants are properly loaded from environment
        from mcp_template.tools.kubernetes_probe import (
            DISCOVERY_RETRIES,
            DISCOVERY_RETRY_SLEEP,
            DISCOVERY_TIMEOUT,
        )

        assert DISCOVERY_RETRIES == 3
        assert DISCOVERY_RETRY_SLEEP == 1  # Set in setup_method
        assert DISCOVERY_TIMEOUT == 30

    @patch("mcp_template.tools.docker_probe.DockerProbe._try_http_discovery")
    def test_docker_stdio_discovery_retry_on_subprocess_timeout(
        self, mock_http_discovery
    ):
        """Test Docker stdio discovery retries on subprocess timeout."""
        mock_http_discovery.return_value = None

        probe = DockerProbe()

        # Mock the MCP client to raise TimeoutExpired
        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.side_effect = subprocess.TimeoutExpired("test", 30)

            start_time = time.time()

            # Test the internal method directly to see retry behavior
            try:
                result = probe._try_mcp_stdio_discovery("test-image", [], {})
            except subprocess.TimeoutExpired:
                pass  # Expected after retries

            end_time = time.time()

            # Should have called the discovery method 3 times (original + 2 retries)
            assert mock_discover.call_count == 3

            # Should have taken at least 2 seconds (2 retry sleeps of 1 second each)
            assert end_time - start_time >= 2

    @patch("mcp_template.tools.docker_probe.DockerProbe._try_mcp_stdio_discovery")
    def test_docker_http_discovery_retry_on_subprocess_error(
        self, mock_stdio_discovery
    ):
        """Test Docker HTTP discovery retries on subprocess error."""
        mock_stdio_discovery.return_value = None

        probe = DockerProbe()

        # Mock subprocess.run to raise CalledProcessError
        with patch("mcp_template.tools.docker_probe.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "docker")

            start_time = time.time()

            # Test the internal method directly to see retry behavior
            try:
                result = probe._try_http_discovery("test-image", 30)
            except subprocess.CalledProcessError:
                pass  # Expected after retries

            end_time = time.time()

            # Should have taken at least 2 seconds (2 retry sleeps)
            assert end_time - start_time >= 2

    @patch("mcp_template.tools.docker_probe.DockerProbe._try_http_discovery")
    def test_docker_stdio_discovery_success_after_retry(self, mock_http_discovery):
        """Test Docker stdio discovery succeeds after retry."""
        mock_http_discovery.return_value = None

        probe = DockerProbe()

        # Mock the MCP client to fail twice then succeed
        call_count = 0

        def mock_discover_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise subprocess.TimeoutExpired("test", 30)
            return {"tools": [{"name": "test-tool", "description": "A test tool"}]}

        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.side_effect = mock_discover_side_effect

            # Test the internal method directly
            result = probe._try_mcp_stdio_discovery("test-image", [], {})

            # Should succeed on third attempt
            assert result is not None
            assert result["discovery_method"] == "docker_mcp_stdio"
            assert len(result["tools"]) == 1
            assert mock_discover.call_count == 3

    def test_kubernetes_stdio_discovery_retry_configuration(self):
        """Test Kubernetes stdio discovery retry decorator configuration."""
        with patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config"):
            with patch("mcp_template.tools.kubernetes_probe.config.load_kube_config"):
                with patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api"):
                    with patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api"):
                        probe = KubernetesProbe()

        # Check that the retry decorator is properly configured
        method = probe._try_mcp_stdio_discovery
        assert hasattr(method, "retry")

        # Get the retry state
        retry_state = method.retry
        assert retry_state.stop.max_attempt_number == 3

    def test_kubernetes_http_discovery_retry_configuration(self):
        """Test Kubernetes HTTP discovery retry decorator configuration."""
        with patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config"):
            with patch("mcp_template.tools.kubernetes_probe.config.load_kube_config"):
                with patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api"):
                    with patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api"):
                        probe = KubernetesProbe()

        # Check that the retry decorator is properly configured
        method = probe._try_http_discovery
        assert hasattr(method, "retry")

        # Get the retry state
        retry_state = method.retry
        assert retry_state.stop.max_attempt_number == 3

    def test_retry_logic_with_different_exception_types(self):
        """Test that retry logic handles different exception types correctly."""
        probe = DockerProbe()

        # Test with OSError
        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.side_effect = OSError("Connection failed")

            # Test the internal method directly
            try:
                result = probe._try_mcp_stdio_discovery("test-image", [], {})
            except OSError:
                pass  # Expected after retries

            assert mock_discover.call_count == 3

    def test_retry_logic_does_not_retry_on_success(self):
        """Test that retry logic doesn't retry when operation succeeds."""
        probe = DockerProbe()

        # Mock successful response
        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.return_value = {
                "tools": [{"name": "test-tool", "description": "A test tool"}]
            }

            result = probe.discover_tools_from_image("test-image")

            # Should succeed on first attempt
            assert result is not None
            assert mock_discover.call_count == 1

    def test_custom_retry_configuration_via_environment(self):
        """Test custom retry configuration through environment variables."""
        # Override environment for this test
        os.environ["MCP_DISCOVERY_RETRIES"] = "2"
        os.environ["MCP_DISCOVERY_RETRY_SLEEP"] = "1"  # Use integer instead of float

        # Force reload of constants by reimporting
        import importlib

        import mcp_template.tools.docker_probe

        importlib.reload(mcp_template.tools.docker_probe)

        probe = mcp_template.tools.docker_probe.DockerProbe()

        # Test that custom configuration is respected
        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.side_effect = subprocess.TimeoutExpired("test", 30)

            start_time = time.time()

            # Test internal method directly
            try:
                result = probe._try_mcp_stdio_discovery("test-image", [], {})
            except subprocess.TimeoutExpired:
                pass  # Expected after retries

            end_time = time.time()

            # Should use custom retry count (2 instead of 3)
            assert mock_discover.call_count == 2

            # Should use custom sleep time (1 second)
            # Total sleep should be at least 1 second (1 retry sleep)
            assert end_time - start_time >= 1
            assert end_time - start_time < 3  # Should be much less than default

    def test_retry_reraise_behavior(self):
        """Test that retry logic re-raises exceptions after all attempts."""
        probe = DockerProbe()

        with patch.object(
            probe.mcp_client, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.side_effect = subprocess.TimeoutExpired("test", 30)

            with patch(
                "mcp_template.tools.docker_probe.DockerProbe._try_http_discovery"
            ) as mock_http:
                mock_http.return_value = None

                # Should raise the last exception after all retries
                with pytest.raises(subprocess.TimeoutExpired):
                    probe._try_mcp_stdio_discovery("test-image", [], {})
