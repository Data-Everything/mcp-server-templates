"""
Unit tests for Kubernetes backend functionality.

Tests the KubernetesDeploymentService class with comprehensive mocking
of Kubernetes client libraries and APIs.
"""

from unittest.mock import Mock, patch

import pytest
from kubernetes.client.rest import ApiException

from mcp_template.backends.kubernetes import KubernetesDeploymentService

pytestmark = [pytest.mark.unit, pytest.mark.kubernetes]


class TestKubernetesDeploymentService:
    """Test Kubernetes deployment service."""

    @patch("mcp_template.backends.kubernetes.config.load_kube_config")
    @patch("mcp_template.backends.kubernetes.client.AppsV1Api")
    @patch("mcp_template.backends.kubernetes.client.CoreV1Api")
    @patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api")
    def test_init_success(
        self, mock_autoscaling, mock_core, mock_apps, mock_load_config
    ):
        """Test successful Kubernetes service initialization."""
        # Mock API resources call
        mock_core_instance = Mock()
        mock_core.return_value = mock_core_instance
        mock_core_instance.get_api_resources.return_value = Mock()
        mock_core_instance.read_namespace.return_value = Mock()

        service = KubernetesDeploymentService(namespace="test-namespace")

        assert service.namespace == "test-namespace"
        assert service.apps_v1 is not None
        assert service.core_v1 is not None

    @patch("mcp_template.backends.kubernetes.config.load_kube_config")
    @patch("mcp_template.backends.kubernetes.client.CoreV1Api")
    def test_init_creates_namespace(self, mock_core, mock_load_config):
        """Test namespace creation when it doesn't exist."""
        mock_core_instance = Mock()
        mock_core.return_value = mock_core_instance

        # Mock namespace not found
        mock_core_instance.read_namespace.side_effect = ApiException(status=404)
        mock_core_instance.create_namespace.return_value = Mock()
        mock_core_instance.get_api_resources.return_value = Mock()

        with (
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            service = KubernetesDeploymentService(namespace="new-namespace")

        mock_core_instance.create_namespace.assert_called_once()
        assert service.namespace == "new-namespace"

    @patch("mcp_template.backends.kubernetes.config.load_kube_config")
    def test_init_fails_on_invalid_config(self, mock_load_config):
        """Test initialization failure when Kubernetes config is invalid."""
        mock_load_config.side_effect = Exception("Invalid config")

        with pytest.raises(RuntimeError, match="Kubernetes backend unavailable"):
            KubernetesDeploymentService()

    def test_generate_deployment_name(self):
        """Test deployment name generation."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            name = service._generate_deployment_name("test_template")
            assert name.startswith("test-template-")
            assert len(name.split("-")) == 3  # test-template-{uuid}

    def test_create_helm_values_http(self):
        """Test Helm values creation for HTTP server."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            template_data = {
                "docker_image": "test-image",
                "tag": "v1.0",
                "transport": ["http"],
                "port": 9000,
            }
            config = {
                "env": {"TEST_VAR": "test_value"},
            }
            k8s_config = {"replicas": 3, "service_type": "NodePort"}

            values = service._create_helm_values(
                "test", config, template_data, k8s_config
            )

            assert values["image"]["repository"] == "docker.io/test-image"
            assert values["image"]["tag"] == "v1.0"
            assert values["replicaCount"] == 3
            assert values["mcp"]["type"] == "http"
            assert values["mcp"]["port"] == 9000
            assert values["mcp"]["env"]["TEST_VAR"] == "test_value"
            assert values["service"]["type"] == "NodePort"

    def test_create_helm_values_stdio(self):
        """Test Helm values creation for stdio server."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            template_data = {
                "image": "stdio-server",
                "transport": ["stdio"],
                "command": ["python", "server.py"],
            }
            k8s_config = {"replicas": 1}

            values = service._create_helm_values(
                "stdio-test", {}, template_data, k8s_config
            )

            assert values["mcp"]["type"] == "stdio"
            assert values["mcp"]["command"] == ["python", "server.py"]

    @patch(
        "mcp_template.backends.kubernetes.KubernetesDeploymentService._wait_for_deployment_ready"
    )
    @patch(
        "mcp_template.backends.kubernetes.KubernetesDeploymentService._get_deployment_details"
    )
    def test_deploy_template_success(self, mock_get_details, mock_wait_ready):
        """Test successful template deployment."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            # Setup mocks
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            # Mock successful resource creation
            mock_apps_instance.create_namespaced_deployment.return_value = Mock(
                metadata=Mock(name="test-deployment")
            )
            mock_core_instance.create_namespaced_service.return_value = Mock(
                metadata=Mock(name="test-service")
            )

            mock_get_details.return_value = {"endpoint": "http://test:8080"}

            service = KubernetesDeploymentService()

            template_data = {"image": "test-image", "transport": ["http"], "port": 8080}
            config = {"replicas": 1}

            result = service.deploy_template("test", config, template_data, {})

            assert result["success"] is True
            assert result["template_id"] == "test"
            assert "deployment_name" in result
            assert result["status"] == "deployed"

    def test_deploy_template_failure(self):
        """Test template deployment failure."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            # Mock deployment creation failure
            mock_apps_instance.create_namespaced_deployment.side_effect = ApiException(
                status=500, reason="Internal Server Error"
            )

            service = KubernetesDeploymentService()

            template_data = {"image": "test-image", "transport": ["http"]}
            config = {"replicas": 1}

            result = service.deploy_template("test", config, template_data, {})

            assert result["success"] is False
            assert "error" in result

    def test_list_deployments(self):
        """Test listing deployments."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            # Mock deployment list
            mock_deployment = Mock()
            mock_deployment.metadata.name = "test-deployment"
            mock_apps_instance.list_namespaced_deployment.return_value = Mock(
                items=[mock_deployment]
            )

            service = KubernetesDeploymentService()

            with patch.object(service, "_get_deployment_details") as mock_get_details:
                mock_get_details.return_value = {
                    "name": "test-deployment",
                    "status": "running",
                }

                deployments = service.list_deployments()

                assert len(deployments) == 1
                assert deployments[0]["name"] == "test-deployment"

    def test_delete_deployment(self):
        """Test deployment deletion."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            result = service.delete_deployment("test-deployment")

            assert result is True
            mock_apps_instance.delete_namespaced_deployment.assert_called_once()
            mock_core_instance.delete_namespaced_service.assert_called_once()

    def test_stop_deployment(self):
        """Test stopping deployment (scaling to 0)."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            # Mock deployment read
            mock_deployment = Mock()
            mock_deployment.spec.replicas = 3
            mock_apps_instance.read_namespaced_deployment.return_value = mock_deployment

            service = KubernetesDeploymentService()

            result = service.stop_deployment("test-deployment")

            assert result is True
            assert mock_deployment.spec.replicas == 0
            mock_apps_instance.patch_namespaced_deployment.assert_called_once()

    def test_get_deployment_info(self):
        """Test getting deployment information."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            with patch.object(service, "_get_deployment_details") as mock_get_details:
                mock_get_details.return_value = {"name": "test", "status": "running"}

                info = service.get_deployment_info("test-deployment")

                assert info["name"] == "test"
                assert info["status"] == "running"

    def test_get_deployment_info_with_logs(self):
        """Test getting deployment information with logs."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            with (
                patch.object(service, "_get_deployment_details") as mock_get_details,
                patch.object(service, "get_deployment_logs") as mock_get_logs,
            ):
                mock_get_details.return_value = {"name": "test", "status": "running"}
                mock_get_logs.return_value = "Sample log output"

                info = service.get_deployment_info("test-deployment", include_logs=True)

                assert info["logs"] == "Sample log output"

    def test_connect_to_deployment_not_implemented(self):
        """Test that connect_to_deployment raises NotImplementedError."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            with pytest.raises(NotImplementedError):
                service.connect_to_deployment("test-deployment")

    def test_cleanup_stopped_containers(self):
        """Test cleanup of stopped containers (scaled to 0)."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api") as mock_apps,
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_apps_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_apps.return_value = mock_apps_instance

            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            # Mock deployment with 0 replicas
            mock_deployment = Mock()
            mock_deployment.metadata.name = "stopped-deployment"
            mock_deployment.spec.replicas = 0
            mock_apps_instance.list_namespaced_deployment.return_value = Mock(
                items=[mock_deployment]
            )

            service = KubernetesDeploymentService()

            with patch.object(service, "delete_deployment") as mock_delete:
                mock_delete.return_value = True

                result = service.cleanup_stopped_containers()

                assert result["count"] == 1
                assert "stopped-deployment" in result["cleaned_up"]

    def test_cleanup_dangling_images(self):
        """Test cleanup of dangling images (returns informational message)."""
        with (
            patch("mcp_template.backends.kubernetes.config.load_kube_config"),
            patch("mcp_template.backends.kubernetes.client.AppsV1Api"),
            patch("mcp_template.backends.kubernetes.client.CoreV1Api") as mock_core,
            patch("mcp_template.backends.kubernetes.client.AutoscalingV1Api"),
        ):
            mock_core_instance = Mock()
            mock_core.return_value = mock_core_instance
            mock_core_instance.get_api_resources.return_value = Mock()
            mock_core_instance.read_namespace.return_value = Mock()

            service = KubernetesDeploymentService()

            result = service.cleanup_dangling_images()

            assert "message" in result
            assert "not applicable" in result["message"]
