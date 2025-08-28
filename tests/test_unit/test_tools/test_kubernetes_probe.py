"""
Unit tests for the Kubernetes probe module (mcp_template.tools.kubernetes_probe).

Tests Kubernetes pod-based MCP server tool discovery functionality.
"""

from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.unit, pytest.mark.kubernetes]

from mcp_template.tools.kubernetes_probe import KubernetesProbe


class TestKubernetesProbe:
    """Test the KubernetesProbe class."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            self.probe = KubernetesProbe()

    def test_init_default_namespace(self):
        """Test default initialization with default namespace."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client") as mock_init:
            probe = KubernetesProbe()
            assert probe.namespace == "mcp-servers"
            mock_init.assert_called_once()

    def test_init_custom_namespace(self):
        """Test initialization with custom namespace."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client") as mock_init:
            probe = KubernetesProbe(namespace="custom-namespace")
            assert probe.namespace == "custom-namespace"
            mock_init.assert_called_once()

    @patch("kubernetes.config.load_incluster_config")
    def test_init_kubernetes_client_incluster(self, mock_incluster):
        """Test Kubernetes client initialization with in-cluster config."""
        mock_incluster.return_value = None

        # Mock the kubernetes client APIs to avoid actual initialization
        with patch("kubernetes.client.AppsV1Api"), patch("kubernetes.client.CoreV1Api"):
            probe = KubernetesProbe()

        # The mock should be called once during __init__
        mock_incluster.assert_called_once()

    @patch("kubernetes.config.load_incluster_config")
    @patch("kubernetes.config.load_kube_config")
    def test_init_kubernetes_client_kubeconfig(self, mock_kubeconfig, mock_incluster):
        """Test Kubernetes client initialization with kubeconfig fallback."""
        from kubernetes.config import ConfigException

        mock_incluster.side_effect = ConfigException("Not in cluster")
        mock_kubeconfig.return_value = None

        # Mock the kubernetes client APIs to avoid actual initialization
        with patch("kubernetes.client.AppsV1Api"), patch("kubernetes.client.CoreV1Api"):
            probe = KubernetesProbe()

        # Both methods should be called once during __init__
        mock_incluster.assert_called_once()
        mock_kubeconfig.assert_called_once()

    @patch("kubernetes.config.load_incluster_config")
    @patch("kubernetes.config.load_kube_config")
    def test_init_kubernetes_client_both_fail(self, mock_kubeconfig, mock_incluster):
        """Test Kubernetes client initialization when both methods fail."""
        from kubernetes.config import ConfigException

        mock_incluster.side_effect = ConfigException("Not in cluster")
        mock_kubeconfig.side_effect = ConfigException("No kubeconfig")

        with pytest.raises(ConfigException):
            # This will fail during __init__ when _init_kubernetes_client is called
            KubernetesProbe()


class TestKubernetesProbeConfiguration:
    """Test Kubernetes-specific configuration and constants."""

    def test_pod_ready_timeout_constant(self):
        """Test POD_READY_TIMEOUT constant."""
        from mcp_template.tools.kubernetes_probe import POD_READY_TIMEOUT

        assert POD_READY_TIMEOUT == 60

    def test_service_port_range_constant(self):
        """Test SERVICE_PORT_RANGE constant."""
        from mcp_template.tools.kubernetes_probe import SERVICE_PORT_RANGE

        assert SERVICE_PORT_RANGE == (8000, 9000)

    def test_inherits_base_constants(self):
        """Test that Kubernetes probe inherits base probe constants."""
        from mcp_template.tools.kubernetes_probe import (
            DISCOVERY_RETRIES,
            DISCOVERY_RETRY_SLEEP,
            DISCOVERY_TIMEOUT,
        )

        assert DISCOVERY_RETRIES == 3
        assert DISCOVERY_RETRY_SLEEP == 5
        assert DISCOVERY_TIMEOUT == 60


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
