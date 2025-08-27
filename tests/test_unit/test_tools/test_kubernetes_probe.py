"""
Unit tests for the Kubernetes probe module (mcp_template.tools.kubernetes_probe).

Tests Kubernetes pod-based MCP server tool discovery functionality.
"""

import time
from unittest.mock import Mock, patch

import pytest
from kubernetes.client.rest import ApiException

pytestmark = pytest.mark.unit

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

        probe = KubernetesProbe()
        probe._init_kubernetes_client()

        mock_incluster.assert_called_once()

    @patch("kubernetes.config.load_incluster_config")
    @patch("kubernetes.config.load_kube_config")
    def test_init_kubernetes_client_kubeconfig(self, mock_kubeconfig, mock_incluster):
        """Test Kubernetes client initialization with kubeconfig fallback."""
        from kubernetes.config import ConfigException

        mock_incluster.side_effect = ConfigException("Not in cluster")
        mock_kubeconfig.return_value = None

        probe = KubernetesProbe()
        probe._init_kubernetes_client()

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
            probe = KubernetesProbe()
            probe._init_kubernetes_client()


class TestKubernetesProbeDiscovery:
    """Test Kubernetes image discovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            self.probe = KubernetesProbe()
            # Mock Kubernetes API clients
            self.probe.apps_v1 = Mock()
            self.probe.core_v1 = Mock()

    @patch.object(KubernetesProbe, "_cleanup_resources")
    @patch.object(KubernetesProbe, "_wait_for_pod_ready")
    @patch.object(KubernetesProbe, "_create_service")
    @patch.object(KubernetesProbe, "_create_deployment")
    def test_discover_tools_from_image_success(
        self, mock_create_deployment, mock_create_service, mock_wait_pod, mock_cleanup
    ):
        """Test successful tool discovery from Kubernetes image."""
        # Mock deployment creation
        mock_deployment = Mock()
        mock_deployment.metadata.name = "probe-deployment"
        mock_create_deployment.return_value = mock_deployment

        # Mock service creation
        mock_service = Mock()
        mock_service.metadata.name = "probe-service"
        mock_service.spec.ports = [Mock(port=8080)]
        mock_create_service.return_value = mock_service

        # Mock pod ready wait
        mock_wait_pod.return_value = True

        # Mock MCP client discovery
        with patch.object(
            self.probe.mcp_client, "discover_tools_via_http"
        ) as mock_discover:
            mock_discover.return_value = {
                "tools": [{"name": "k8s_tool", "description": "Kubernetes tool"}],
                "server_info": {"name": "k8s-server"},
            }

            result = self.probe.discover_tools_from_image("test-image:latest")

            assert result is not None
            assert "tools" in result
            assert result["tools"][0]["name"] == "k8s_tool"
            mock_cleanup.assert_called()

    @patch.object(KubernetesProbe, "_cleanup_resources")
    @patch.object(KubernetesProbe, "_create_deployment")
    def test_discover_tools_from_image_deployment_failure(
        self, mock_create_deployment, mock_cleanup
    ):
        """Test discovery when deployment creation fails."""
        mock_create_deployment.side_effect = ApiException(
            status=500, reason="Server Error"
        )

        result = self.probe.discover_tools_from_image("test-image:latest")

        assert result is None
        mock_cleanup.assert_called()

    @patch.object(KubernetesProbe, "_cleanup_resources")
    @patch.object(KubernetesProbe, "_wait_for_pod_ready")
    @patch.object(KubernetesProbe, "_create_service")
    @patch.object(KubernetesProbe, "_create_deployment")
    def test_discover_tools_from_image_pod_not_ready(
        self, mock_create_deployment, mock_create_service, mock_wait_pod, mock_cleanup
    ):
        """Test discovery when pod doesn't become ready."""
        mock_create_deployment.return_value = Mock()
        mock_create_service.return_value = Mock()
        mock_wait_pod.return_value = False

        result = self.probe.discover_tools_from_image("test-image:latest")

        assert result is None
        mock_cleanup.assert_called()

    @patch.object(KubernetesProbe, "_cleanup_resources")
    @patch.object(KubernetesProbe, "_wait_for_pod_ready")
    @patch.object(KubernetesProbe, "_create_service")
    @patch.object(KubernetesProbe, "_create_deployment")
    def test_discover_tools_with_custom_args(
        self, mock_create_deployment, mock_create_service, mock_wait_pod, mock_cleanup
    ):
        """Test discovery with custom server arguments and environment variables."""
        mock_create_deployment.return_value = Mock()
        mock_service = Mock()
        mock_service.spec.ports = [Mock(port=8080)]
        mock_create_service.return_value = mock_service
        mock_wait_pod.return_value = True

        with patch.object(
            self.probe.mcp_client, "discover_tools_via_http"
        ) as mock_discover:
            mock_discover.return_value = {"tools": []}

            result = self.probe.discover_tools_from_image(
                "test-image:latest",
                server_args=["--config", "/app/config.yaml"],
                env_vars={"NAMESPACE": "test", "LOG_LEVEL": "debug"},
                timeout=45,
            )

            # Verify deployment was called with correct parameters
            mock_create_deployment.assert_called()
            deployment_call = mock_create_deployment.call_args[0]
            assert "test-image:latest" in str(deployment_call)


class TestKubernetesProbeResourceManagement:
    """Test Kubernetes resource creation and management."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            self.probe = KubernetesProbe()
            self.probe.apps_v1 = Mock()
            self.probe.core_v1 = Mock()

    def test_generate_resource_name(self):
        """Test resource name generation."""
        name = self.probe._generate_resource_name("test-image:v1.0")

        assert name.startswith("mcp-probe-")
        assert len(name) <= 63  # Kubernetes name length limit
        assert name.replace("-", "").replace("mcp", "").replace("probe", "").isalnum()

    def test_create_deployment_success(self):
        """Test successful deployment creation."""
        mock_deployment = Mock()
        self.probe.apps_v1.create_namespaced_deployment.return_value = mock_deployment

        result = self.probe._create_deployment(
            "test-image:latest",
            "test-deployment",
            server_args=["--port", "8080"],
            env_vars={"DEBUG": "true"},
        )

        assert result == mock_deployment
        self.probe.apps_v1.create_namespaced_deployment.assert_called_once()

    def test_create_deployment_api_exception(self):
        """Test deployment creation with API exception."""
        self.probe.apps_v1.create_namespaced_deployment.side_effect = ApiException(
            status=400, reason="Bad Request"
        )

        with pytest.raises(ApiException):
            self.probe._create_deployment("test-image", "test-deployment")

    def test_create_service_success(self):
        """Test successful service creation."""
        mock_service = Mock()
        self.probe.core_v1.create_namespaced_service.return_value = mock_service

        result = self.probe._create_service("test-service", {"app": "test"})

        assert result == mock_service
        self.probe.core_v1.create_namespaced_service.assert_called_once()

    def test_create_service_api_exception(self):
        """Test service creation with API exception."""
        self.probe.core_v1.create_namespaced_service.side_effect = ApiException(
            status=409, reason="Already Exists"
        )

        with pytest.raises(ApiException):
            self.probe._create_service("test-service", {"app": "test"})

    @patch("time.sleep")
    def test_wait_for_pod_ready_success(self, mock_sleep):
        """Test successful pod ready wait."""
        # Mock pod with ready condition
        mock_pod = Mock()
        mock_pod.status.conditions = [Mock(type="Ready", status="True")]

        # First call returns not ready, second returns ready
        self.probe.core_v1.list_namespaced_pod.side_effect = [
            Mock(
                items=[
                    Mock(status=Mock(conditions=[Mock(type="Ready", status="False")]))
                ]
            ),
            Mock(items=[mock_pod]),
        ]

        result = self.probe._wait_for_pod_ready({"app": "test"}, timeout=10)

        assert result is True

    @patch("time.sleep")
    def test_wait_for_pod_ready_timeout(self, mock_sleep):
        """Test pod ready wait timeout."""
        # Always return not ready pod
        mock_pod = Mock()
        mock_pod.status.conditions = [Mock(type="Ready", status="False")]
        self.probe.core_v1.list_namespaced_pod.return_value = Mock(items=[mock_pod])

        result = self.probe._wait_for_pod_ready({"app": "test"}, timeout=1)

        assert result is False

    @patch("time.sleep")
    def test_wait_for_pod_ready_no_pods(self, mock_sleep):
        """Test pod ready wait when no pods exist."""
        self.probe.core_v1.list_namespaced_pod.return_value = Mock(items=[])

        result = self.probe._wait_for_pod_ready({"app": "test"}, timeout=1)

        assert result is False

    @patch("time.sleep")
    def test_wait_for_pod_ready_api_exception(self, mock_sleep):
        """Test pod ready wait with API exception."""
        self.probe.core_v1.list_namespaced_pod.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        result = self.probe._wait_for_pod_ready({"app": "test"}, timeout=1)

        assert result is False

    def test_cleanup_resources_success(self):
        """Test successful resource cleanup."""
        self.probe._cleanup_resources("test-deployment", "test-service")

        # Verify both delete calls were made
        self.probe.apps_v1.delete_namespaced_deployment.assert_called_once_with(
            name="test-deployment", namespace=self.probe.namespace
        )
        self.probe.core_v1.delete_namespaced_service.assert_called_once_with(
            name="test-service", namespace=self.probe.namespace
        )

    def test_cleanup_resources_api_exceptions(self):
        """Test resource cleanup with API exceptions."""
        # Make both deletes fail
        self.probe.apps_v1.delete_namespaced_deployment.side_effect = ApiException(
            status=404, reason="Not Found"
        )
        self.probe.core_v1.delete_namespaced_service.side_effect = ApiException(
            status=404, reason="Not Found"
        )

        # Should not raise exception, just log errors
        self.probe._cleanup_resources("test-deployment", "test-service")

    def test_cleanup_resources_partial_cleanup(self):
        """Test cleanup when only deployment name is provided."""
        self.probe._cleanup_resources("test-deployment", None)

        # Only deployment should be deleted
        self.probe.apps_v1.delete_namespaced_deployment.assert_called_once()
        self.probe.core_v1.delete_namespaced_service.assert_not_called()


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


class TestKubernetesProbeIntegration:
    """Test integration aspects of KubernetesProbe."""

    def setup_method(self):
        """Set up test fixtures."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            self.probe = KubernetesProbe()

    def test_inherits_from_base_probe(self):
        """Test that KubernetesProbe properly inherits from BaseProbe."""
        from mcp_template.tools.base_probe import BaseProbe

        assert isinstance(self.probe, BaseProbe)

    def test_implements_abstract_method(self):
        """Test that KubernetesProbe implements required abstract method."""
        assert hasattr(self.probe, "discover_tools_from_image")
        assert callable(self.probe.discover_tools_from_image)

    @patch("kubernetes.client.AppsV1Api")
    @patch("kubernetes.client.CoreV1Api")
    def test_kubernetes_client_setup(self, mock_core_v1, mock_apps_v1):
        """Test that Kubernetes API clients are properly set up."""
        with patch("kubernetes.config.load_incluster_config"):
            probe = KubernetesProbe()
            probe._init_kubernetes_client()

            # Verify clients were created
            mock_apps_v1.assert_called_once()
            mock_core_v1.assert_called_once()

    def test_error_handling_comprehensive(self):
        """Test comprehensive error handling in discovery."""
        with patch.object(
            self.probe, "_create_deployment", side_effect=Exception("K8s error")
        ):
            result = self.probe.discover_tools_from_image("test-image")
            assert result is None

    def test_resource_name_generation_uniqueness(self):
        """Test that resource names are unique across calls."""
        name1 = self.probe._generate_resource_name("test-image:v1")
        name2 = self.probe._generate_resource_name("test-image:v1")

        # Should be different due to timestamp component
        assert name1 != name2

    def test_namespace_validation(self):
        """Test namespace validation and usage."""
        with patch.object(KubernetesProbe, "_init_kubernetes_client"):
            # Test valid namespace
            probe = KubernetesProbe(namespace="valid-namespace")
            assert probe.namespace == "valid-namespace"

            # Test namespace with special characters (should still work)
            probe = KubernetesProbe(namespace="test.namespace-123")
            assert probe.namespace == "test.namespace-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
