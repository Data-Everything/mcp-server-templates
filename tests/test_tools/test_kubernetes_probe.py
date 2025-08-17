"""
Unit tests for Kubernetes probe functionality.
"""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest
from kubernetes.client.rest import ApiException

from mcp_template.tools.kubernetes_probe import KubernetesProbe

pytestmark = pytest.mark.unit


class TestKubernetesProbe(unittest.TestCase):
    """Test Kubernetes probe functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock Kubernetes client initialization
        with (
            patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config"),
            patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api"),
            patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api"),
        ):
            self.probe = KubernetesProbe(namespace="test-namespace")

    @patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config")
    @patch("mcp_template.tools.kubernetes_probe.config.load_kube_config")
    @patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api")
    @patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api")
    def test_init_with_incluster_config(
        self,
        mock_core_v1,
        mock_apps_v1,
        mock_load_kube_config,
        mock_load_incluster_config,
    ):
        """Test initialization with in-cluster config."""
        mock_load_incluster_config.return_value = None

        probe = KubernetesProbe()

        mock_load_incluster_config.assert_called_once()
        mock_load_kube_config.assert_not_called()
        self.assertEqual(probe.namespace, "mcp-servers")

    @patch("mcp_template.tools.kubernetes_probe.config.load_incluster_config")
    @patch("mcp_template.tools.kubernetes_probe.config.load_kube_config")
    @patch("mcp_template.tools.kubernetes_probe.client.AppsV1Api")
    @patch("mcp_template.tools.kubernetes_probe.client.CoreV1Api")
    def test_init_with_kubeconfig_fallback(
        self,
        mock_core_v1,
        mock_apps_v1,
        mock_load_kube_config,
        mock_load_incluster_config,
    ):
        """Test initialization falling back to kubeconfig."""
        from kubernetes import config as k8s_config

        mock_load_incluster_config.side_effect = k8s_config.ConfigException(
            "No in-cluster config"
        )
        mock_load_kube_config.return_value = None

        probe = KubernetesProbe(namespace="custom-namespace")

        mock_load_incluster_config.assert_called_once()
        mock_load_kube_config.assert_called_once()
        self.assertEqual(probe.namespace, "custom-namespace")

    def test_generate_job_name(self):
        """Test job name generation."""
        image_name = "dataeverything/mcp-demo:latest"
        job_name = self.probe._generate_job_name(image_name)

        self.assertTrue(job_name.startswith("mcp-tool-discovery-job-"))
        self.assertIn("dataeverything-mcp-demo-latest", job_name)
        self.assertLessEqual(len(job_name), 63)  # Kubernetes name limit

    def test_generate_pod_name(self):
        """Test pod name generation."""
        image_name = "nginx:latest"
        pod_name = self.probe._generate_pod_name(image_name)

        self.assertTrue(pod_name.startswith("mcp-tool-discovery-"))
        self.assertIn("nginx-latest", pod_name)
        self.assertLessEqual(len(pod_name), 63)  # Kubernetes name limit

    def test_generate_service_name(self):
        """Test service name generation."""
        image_name = "myregistry.com/app:v1.0"
        service_name = self.probe._generate_service_name(image_name)

        self.assertTrue(service_name.startswith("mcp-discovery-svc-"))
        self.assertIn("myregistry.com-app-v1.0", service_name)
        self.assertLessEqual(len(service_name), 63)  # Kubernetes name limit

    def test_find_available_port(self):
        """Test finding available port."""
        port = self.probe._find_available_port()
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 8000)
        self.assertLessEqual(port, 9000)

    def test_create_discovery_job_manifest(self):
        """Test creating job manifest for MCP stdio discovery."""
        job_name = "test-job"
        image_name = "test-image:latest"
        args = ["--stdio"]
        env_vars = {"MCP_TEST": "value"}

        manifest = self.probe._create_discovery_job_manifest(
            job_name, image_name, args, env_vars
        )

        self.assertEqual(manifest["kind"], "Job")
        self.assertEqual(manifest["metadata"]["name"], job_name)
        self.assertEqual(manifest["metadata"]["namespace"], "test-namespace")

        container = manifest["spec"]["template"]["spec"]["containers"][0]
        self.assertEqual(container["image"], image_name)
        self.assertEqual(container["args"], args)
        self.assertEqual(container["env"], [{"name": "MCP_TEST", "value": "value"}])

    @patch("mcp_template.tools.kubernetes_probe.time.time")
    def test_wait_for_pod_ready_success(self, mock_time):
        """Test waiting for pod to be ready - success case."""
        mock_time.side_effect = [0, 1, 2, 3]  # Simulate time progression

        # Mock pod status
        mock_pod = Mock()
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = [Mock(ready=True)]

        self.probe.k8s_core_v1.read_namespaced_pod_status.return_value = mock_pod

        result = self.probe._wait_for_pod_ready("test-pod", timeout=60)

        self.assertTrue(result)

    @patch("mcp_template.tools.kubernetes_probe.time.time")
    def test_wait_for_pod_ready_timeout(self, mock_time):
        """Test waiting for pod to be ready - timeout case."""
        mock_time.side_effect = [0, 30, 60, 61]  # Simulate timeout

        # Mock pod status - never becomes ready
        mock_pod = Mock()
        mock_pod.status.phase = "Pending"
        mock_pod.status.container_statuses = [Mock(ready=False)]

        self.probe.k8s_core_v1.read_namespaced_pod_status.return_value = mock_pod

        result = self.probe._wait_for_pod_ready("test-pod", timeout=60)

        self.assertFalse(result)

    def test_get_service_url(self):
        """Test getting service URL."""
        service_name = "test-service"
        port = 8080

        url = self.probe._get_service_url(service_name, port)

        expected = "http://test-service.test-namespace.svc.cluster.local:8080"
        self.assertEqual(url, expected)

    def test_get_default_endpoints(self):
        """Test getting default probe endpoints."""
        endpoints = self.probe._get_default_endpoints()

        self.assertIsInstance(endpoints, list)
        self.assertIn("/tools", endpoints)
        self.assertIn("/mcp/tools", endpoints)
        self.assertIn("/health", endpoints)

    @patch("mcp_template.tools.kubernetes_probe.requests.get")
    def test_probe_endpoints_success(self, mock_get):
        """Test probing endpoints - success case."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tools": [{"name": "test_tool"}]}
        mock_get.return_value = mock_response

        base_url = "http://test-service:8080"
        endpoints = ["/tools"]

        result = self.probe._probe_endpoints(base_url, endpoints)

        self.assertIsNotNone(result)
        self.assertIn("tools", result)
        self.assertEqual(len(result["tools"]), 1)
        self.assertEqual(result["tools"][0]["name"], "test_tool")

    @patch("mcp_template.tools.kubernetes_probe.requests.get")
    def test_probe_endpoints_failure(self, mock_get):
        """Test probing endpoints - failure case."""
        # Mock failed response
        mock_get.side_effect = Exception("Connection failed")

        base_url = "http://test-service:8080"
        endpoints = ["/tools"]

        result = self.probe._probe_endpoints(base_url, endpoints)

        self.assertIsNone(result)

    def test_parse_mcp_tools_from_logs_success(self):
        """Test parsing MCP tools from logs - success case."""
        logs = """
        Starting MCP server...
        {"tools": [{"name": "test_tool", "description": "Test tool"}]}
        Server ready
        """

        result = self.probe._parse_mcp_tools_from_logs(logs)

        self.assertIsNotNone(result)
        self.assertIn("tools", result)
        self.assertEqual(len(result["tools"]), 1)
        self.assertEqual(result["tools"][0]["name"], "test_tool")

    def test_parse_mcp_tools_from_logs_no_tools(self):
        """Test parsing MCP tools from logs - no tools found."""
        logs = """
        Starting MCP server...
        Server ready
        No JSON output
        """

        result = self.probe._parse_mcp_tools_from_logs(logs)

        self.assertIsNone(result)

    def test_cleanup_job(self):
        """Test job cleanup."""
        job_name = "test-job"

        self.probe._cleanup_job(job_name)

        self.probe.k8s_apps_v1.delete_namespaced_job.assert_called_once_with(
            name=job_name, namespace="test-namespace", propagation_policy="Background"
        )

    def test_cleanup_pod(self):
        """Test pod cleanup."""
        pod_name = "test-pod"

        self.probe._cleanup_pod(pod_name)

        self.probe.k8s_core_v1.delete_namespaced_pod.assert_called_once_with(
            name=pod_name, namespace="test-namespace"
        )

    def test_cleanup_service(self):
        """Test service cleanup."""
        service_name = "test-service"

        self.probe._cleanup_service(service_name)

        self.probe.k8s_core_v1.delete_namespaced_service.assert_called_once_with(
            name=service_name, namespace="test-namespace"
        )

    @patch("mcp_template.tools.kubernetes_probe.logger")
    def test_cleanup_job_with_exception(self, mock_logger):
        """Test job cleanup with API exception."""
        job_name = "test-job"
        self.probe.k8s_apps_v1.delete_namespaced_job.side_effect = ApiException(
            "Not found"
        )

        self.probe._cleanup_job(job_name)

        # Should not raise exception, just log
        mock_logger.debug.assert_called_once()

    @patch("mcp_template.tools.kubernetes_probe.time.sleep")
    def test_discover_tools_from_image_stdio_success(self, mock_sleep):
        """Test discovering tools from image using stdio method."""
        image_name = "test-image:latest"

        with patch.object(self.probe, "_try_mcp_stdio_discovery") as mock_stdio:
            mock_stdio.return_value = {
                "tools": [{"name": "test_tool"}],
                "discovery_method": "kubernetes_mcp_stdio",
            }

            result = self.probe.discover_tools_from_image(image_name)

            self.assertIsNotNone(result)
            self.assertEqual(result["discovery_method"], "kubernetes_mcp_stdio")
            self.assertIn("tools", result)

    @patch("mcp_template.tools.kubernetes_probe.time.sleep")
    def test_discover_tools_from_image_http_fallback(self, mock_sleep):
        """Test discovering tools from image falling back to HTTP method."""
        image_name = "test-image:latest"

        with (
            patch.object(self.probe, "_try_mcp_stdio_discovery") as mock_stdio,
            patch.object(self.probe, "_try_http_discovery") as mock_http,
        ):

            mock_stdio.return_value = None  # Stdio fails
            mock_http.return_value = {
                "tools": [{"name": "test_tool"}],
                "discovery_method": "kubernetes_http_probe",
            }

            result = self.probe.discover_tools_from_image(image_name)

            self.assertIsNotNone(result)
            self.assertEqual(result["discovery_method"], "kubernetes_http_probe")
            mock_stdio.assert_called_once()
            mock_http.assert_called_once()

    def test_discover_tools_from_image_complete_failure(self):
        """Test discovering tools from image - complete failure."""
        image_name = "test-image:latest"

        with (
            patch.object(self.probe, "_try_mcp_stdio_discovery") as mock_stdio,
            patch.object(self.probe, "_try_http_discovery") as mock_http,
        ):

            mock_stdio.return_value = None
            mock_http.return_value = None

            result = self.probe.discover_tools_from_image(image_name)

            self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
