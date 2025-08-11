"""
Unit tests for DeploymentManager in the common module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.common.deployment_manager import DeploymentManager
from tests.test_fixtures.sample_data import SAMPLE_DEPLOYMENT_DATA, SAMPLE_TEMPLATE_DATA


@pytest.mark.unit
class TestDeploymentManagerCore:
    """Core functionality tests for DeploymentManager."""

    def test_init_docker_backend(self):
        """Test initialization with Docker backend."""
        manager = DeploymentManager(backend_type="docker")
        assert manager.backend_type == "docker"
        assert manager.core_deployment_manager is not None
        assert manager.template_manager is not None

    def test_init_kubernetes_backend(self):
        """Test initialization with Kubernetes backend."""
        manager = DeploymentManager(backend_type="kubernetes")
        assert manager.backend_type == "kubernetes"
        assert manager.core_deployment_manager is not None

    def test_init_mock_backend(self):
        """Test initialization with mock backend."""
        manager = DeploymentManager(backend_type="mock")
        assert manager.backend_type == "mock"
        assert manager.core_deployment_manager is not None

    def test_init_invalid_backend(self):
        """Test initialization with invalid backend type."""
        with pytest.raises(ValueError):
            DeploymentManager(backend_type="invalid")

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.deploy_template"
    )
    def test_deploy_template_success(self, mock_deploy):
        """Test successful template deployment."""
        # Mock successful deployment
        mock_deploy.return_value = {
            "deployment_id": "demo-deployment-123",
            "status": "deployed",
            "container_id": "abc123",
        }

        # Mock template manager to return template data
        with patch.object(
            DeploymentManager, "_generate_deployment_config"
        ) as mock_config:
            mock_config.return_value = {
                "template": SAMPLE_TEMPLATE_DATA["demo"],
                "config": {"port": 7071},
                "missing_properties": [],
            }

            manager = DeploymentManager(backend_type="docker")
            result = manager.deploy_template("demo")

            assert result["deployment_id"] == "demo-deployment-123"
            assert result["status"] == "deployed"
            mock_deploy.assert_called_once()

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.deploy_template"
    )
    def test_deploy_template_failure(self, mock_deploy):
        """Test failed template deployment."""
        # Mock deployment failure
        mock_deploy.side_effect = Exception("Deployment failed")

        with patch.object(
            DeploymentManager, "_generate_deployment_config"
        ) as mock_config:
            mock_config.return_value = {
                "template": SAMPLE_TEMPLATE_DATA["demo"],
                "config": {"port": 7071},
                "missing_properties": [],
            }

            manager = DeploymentManager(backend_type="docker")
            result = manager.deploy_template("demo")

            assert result is None  # Should return None on failure

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.delete_deployment"
    )
    def test_stop_deployment_success(self, mock_stop):
        """Test successful deployment stop."""
        mock_stop.return_value = True

        manager = DeploymentManager(backend_type="docker")
        result = manager.stop_deployment("demo-deployment-123")

        assert result is True
        mock_stop.assert_called_once_with("demo-deployment-123", raise_on_failure=True)

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.delete_deployment"
    )
    def test_stop_deployment_not_found(self, mock_stop):
        """Test stopping non-existent deployment."""
        mock_stop.return_value = False

        manager = DeploymentManager(backend_type="docker")
        result = manager.stop_deployment("non-existent")

        assert result is False

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.list_deployments"
    )
    def test_list_deployments_empty(self, mock_list):
        """Test listing deployments when none exist."""
        mock_list.return_value = []

        manager = DeploymentManager(backend_type="docker")
        deployments = manager.list_deployments()

        assert deployments == []

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.list_deployments"
    )
    def test_list_deployments_multiple(self, mock_list):
        """Test listing multiple deployments."""
        mock_deployments = list(SAMPLE_DEPLOYMENT_DATA.values())
        mock_list.return_value = mock_deployments

        manager = DeploymentManager(backend_type="docker")
        deployments = manager.list_deployments()

        assert len(deployments) == len(mock_deployments)
        assert all("id" in d for d in deployments)

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.get_deployment_status"
    )
    def test_get_deployment_status_running(self, mock_status):
        """Test getting status of running deployment."""
        mock_status.return_value = {
            "id": "demo-deployment-123",
            "status": "running",
            "health": "healthy",
        }

        manager = DeploymentManager(backend_type="docker")
        status = manager.get_deployment_status("demo-deployment-123")

        assert status["status"] == "running"
        assert status["health"] == "healthy"

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.get_deployment_status"
    )
    def test_get_deployment_status_stopped(self, mock_status):
        """Test getting status of stopped deployment."""
        mock_status.return_value = {"id": "demo-deployment-123", "status": "stopped"}

        manager = DeploymentManager(backend_type="docker")
        status = manager.get_deployment_status("demo-deployment-123")

        assert status["status"] == "stopped"

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.get_deployment_status"
    )
    def test_get_deployment_logs_success(self, mock_status):
        """Test successful log retrieval."""
        mock_status.return_value = {"logs": "Sample log output\nAnother log line"}

        manager = DeploymentManager(backend_type="docker")
        logs = manager.get_deployment_logs("demo-deployment-123", lines=100)

        assert "Sample log output" in logs
        mock_status.assert_called_once_with("demo-deployment-123")

    @patch(
        "mcp_template.common.deployment_manager.CoreDeploymentManager.get_deployment_status"
    )
    def test_get_deployment_logs_not_found(self, mock_status):
        """Test log retrieval for non-existent deployment."""
        mock_status.side_effect = Exception("Deployment not found")

        manager = DeploymentManager(backend_type="docker")
        result = manager.get_deployment_logs("non-existent")

        assert result is None


@pytest.mark.unit
class TestDeploymentManagerTemplateOperations:
    """Test template-specific operations in DeploymentManager."""

    def test_deploy_template_with_config(self):
        """Test template deployment with custom configuration."""
        with patch(
            "mcp_template.common.deployment_manager.CoreDeploymentManager.deploy_template"
        ) as mock_deploy:
            mock_deploy.return_value = {
                "deployment_id": "demo-deployment-123",
                "status": "deployed",
            }

            with patch.object(
                DeploymentManager, "_generate_deployment_config"
            ) as mock_config:
                mock_config.return_value = {
                    "template": SAMPLE_TEMPLATE_DATA["demo"],
                    "config": {"port": 8080, "environment": {"LOG_LEVEL": "DEBUG"}},
                    "missing_properties": [],
                }

                config = {"port": 8080, "environment": {"LOG_LEVEL": "DEBUG"}}

                manager = DeploymentManager(backend_type="docker")
                result = manager.deploy_template("demo", configuration=config)

                assert result["status"] == "deployed"
                # Verify deploy was called with config
                mock_deploy.assert_called_once()

    def test_deploy_template_with_custom_name(self):
        """Test template deployment with custom configuration."""
        with patch(
            "mcp_template.common.deployment_manager.CoreDeploymentManager.deploy_template"
        ) as mock_deploy:
            mock_deploy.return_value = {
                "deployment_id": "my-custom-demo",
                "status": "deployed",
            }

            with patch.object(
                DeploymentManager, "_generate_deployment_config"
            ) as mock_config:
                mock_config.return_value = {
                    "template": SAMPLE_TEMPLATE_DATA["demo"],
                    "config": {"port": 7071},
                    "missing_properties": [],
                }

                manager = DeploymentManager(backend_type="docker")
                result = manager.deploy_template("demo", port=8080)

                assert result["status"] == "deployed"

    def test_cleanup_deployments(self):
        """Test cleaning up all deployments."""
        with patch.object(DeploymentManager, "list_deployments") as mock_list:
            with patch.object(DeploymentManager, "stop_deployment") as mock_stop:
                mock_list.return_value = [{"id": "deployment1"}, {"id": "deployment2"}]
                mock_stop.return_value = True

                manager = DeploymentManager(backend_type="docker")
                result = manager.cleanup_deployments()

                assert result["stopped"] == 2
                assert result["failed"] == 0
                assert mock_stop.call_count == 2


@pytest.mark.unit
class TestDeploymentManagerErrorHandling:
    """Test error handling in DeploymentManager."""

    def test_handle_backend_connection_error(self):
        """Test handling backend connection errors."""
        with patch(
            "mcp_template.backends.docker.DockerBackend.__init__",
            side_effect=Exception("Cannot connect"),
        ):
            with pytest.raises(Exception):
                DeploymentManager(backend_type="docker")

    def test_handle_deployment_timeout(self):
        """Test handling deployment timeouts."""
        with patch(
            "mcp_template.backends.docker.DockerBackend.deploy",
            side_effect=TimeoutError("Deployment timed out"),
        ):
            manager = DeploymentManager(backend_type="docker")

            with pytest.raises(TimeoutError):
                manager.deploy_template("demo")

    def test_handle_insufficient_resources(self):
        """Test handling insufficient resource errors."""
        with patch(
            "mcp_template.backends.docker.DockerBackend.deploy",
            side_effect=RuntimeError("Insufficient resources"),
        ):
            manager = DeploymentManager(backend_type="docker")

            with pytest.raises(RuntimeError):
                manager.deploy_template("demo")


@pytest.mark.integration
class TestDeploymentManagerIntegration:
    """Integration tests for DeploymentManager."""

    def test_mock_backend_integration(self):
        """Test integration with mock backend."""
        manager = DeploymentManager(backend_type="mock")

        # Test full deployment workflow
        result = manager.deploy_template("demo")
        assert "deployment_id" in result

        deployments = manager.list_deployments()
        assert len(deployments) >= 1

        deployment_id = result["deployment_id"]
        status = manager.get_deployment_status(deployment_id)
        assert status is not None

        logs = manager.get_deployment_logs(deployment_id)
        assert logs is not None

        stopped = manager.stop_deployment(deployment_id)
        assert stopped is True

    def test_deployment_lifecycle(self):
        """Test complete deployment lifecycle."""
        manager = DeploymentManager(backend_type="mock")

        # Deploy
        deploy_result = manager.deploy_template("demo")
        deployment_id = deploy_result["deployment_id"]

        # Check status
        status = manager.get_deployment_status(deployment_id)
        assert status["status"] in ["running", "pending", "stopped"]

        # Get logs
        logs = manager.get_deployment_logs(deployment_id, lines=50)
        assert isinstance(logs, str)

        # Stop
        stop_result = manager.stop_deployment(deployment_id)
        assert stop_result is True


@pytest.mark.docker
class TestDeploymentManagerDocker:
    """Docker-specific tests (requires Docker daemon)."""

    def test_docker_backend_availability(self):
        """Test if Docker backend can be initialized."""
        try:
            manager = DeploymentManager(backend_type="docker")
            assert manager.backend_type == "docker"
        except Exception as e:
            pytest.skip(f"Docker not available: {e}")

    def test_docker_deployment_dry_run(self):
        """Test Docker deployment preparation without actual deployment."""
        try:
            manager = DeploymentManager(backend_type="docker")

            # Test that we can prepare deployment without errors
            # This would test image building, config validation, etc.
            # Implementation depends on backend interface
            assert manager.deployment_backend is not None

        except Exception as e:
            pytest.skip(f"Docker not available: {e}")


@pytest.mark.kubernetes
class TestDeploymentManagerKubernetes:
    """Kubernetes-specific tests (requires Kubernetes cluster)."""

    def test_kubernetes_backend_availability(self):
        """Test if Kubernetes backend can be initialized."""
        try:
            manager = DeploymentManager(backend_type="kubernetes")
            assert manager.backend_type == "kubernetes"
        except Exception as e:
            pytest.skip(f"Kubernetes not available: {e}")

    def test_kubernetes_deployment_dry_run(self):
        """Test Kubernetes deployment preparation without actual deployment."""
        try:
            manager = DeploymentManager(backend_type="kubernetes")

            # Test that we can prepare deployment without errors
            assert manager.deployment_backend is not None

        except Exception as e:
            pytest.skip(f"Kubernetes not available: {e}")


@pytest.mark.slow
class TestDeploymentManagerPerformance:
    """Performance tests for DeploymentManager."""

    def test_concurrent_deployments(self):
        """Test handling multiple concurrent deployments."""
        import threading
        import time

        manager = DeploymentManager(backend_type="mock")
        results = []

        def deploy_template(template_name, deployment_name):
            try:
                result = manager.deploy_template(template_name)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})

        # Start 5 concurrent deployments
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=deploy_template, args=("demo", f"concurrent-deployment-{i}")
            )
            threads.append(thread)
            thread.start()

        # Wait for all to complete
        for thread in threads:
            thread.join(timeout=10.0)

        # Check results
        assert len(results) == 5
        successful = [r for r in results if "error" not in r]
        assert len(successful) >= 3  # At least 3 should succeed

    def test_large_deployment_list_performance(self):
        """Test performance with many deployments."""
        import time

        manager = DeploymentManager(backend_type="mock")

        # Create many mock deployments
        deployments = []
        for i in range(100):
            deployments.append(
                {"id": f"deployment-{i:03d}", "template": "demo", "status": "running"}
            )

        with patch.object(
            manager.deployment_backend, "list_deployments", return_value=deployments
        ):
            start_time = time.time()
            result = manager.list_deployments()
            elapsed_time = time.time() - start_time

            assert len(result) == 100
            assert elapsed_time < 1.0  # Should complete within 1 second
