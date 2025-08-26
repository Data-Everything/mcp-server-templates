"""
Test Multi-Backend Manager functionality.

This module tests the MultiBackendManager class that provides unified
operations across multiple deployment backends.
"""

from unittest.mock import Mock, call, patch

import pytest

from mcp_template.core.multi_backend_manager import MultiBackendManager

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_backends():
    """Fixture for mocked backend instances."""
    docker_backend = Mock()
    k8s_backend = Mock()
    mock_backend = Mock()

    return {"docker": docker_backend, "kubernetes": k8s_backend, "mock": mock_backend}


@pytest.fixture
def mock_managers():
    """Fixture for mocked manager instances."""
    return {
        "docker": {"deployment": Mock(), "tool": Mock()},
        "kubernetes": {"deployment": Mock(), "tool": Mock()},
        "mock": {"deployment": Mock(), "tool": Mock()},
    }


@pytest.fixture
def sample_deployments():
    """Sample deployment data for testing."""
    return {
        "docker": [
            {
                "id": "docker-123",
                "template": "demo",
                "status": "running",
                "created_at": "2024-01-01T10:00:00Z",
            },
            {
                "id": "docker-456",
                "template": "github",
                "status": "stopped",
                "created_at": "2024-01-01T09:00:00Z",
            },
        ],
        "kubernetes": [
            {
                "id": "k8s-789",
                "template": "demo",
                "status": "running",
                "created_at": "2024-01-01T11:00:00Z",
            }
        ],
        "mock": [],
    }


class TestMultiBackendManagerInitialization:
    """Test MultiBackendManager initialization."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.deployment_manager.DeploymentManager")
    @patch("mcp_template.core.tool_manager.ToolManager")
    def test_initialization_success(
        self, mock_tool_manager_class, mock_deployment_manager_class, mock_get_backend
    ):
        """Test successful initialization of all backends."""
        # Setup mocks
        mock_backends = {"docker": Mock(), "kubernetes": Mock(), "mock": Mock()}
        mock_get_backend.side_effect = lambda backend_type: mock_backends[backend_type]

        mock_deployment_manager_class.side_effect = lambda backend_type: Mock()
        mock_tool_manager_class.side_effect = lambda backend_type: Mock()

        # Test initialization
        manager = MultiBackendManager()

        # Verify production backends were initialized (mock excluded by default)
        assert manager.get_available_backends() == ["docker", "kubernetes"]
        assert len(manager.backends) == 2
        assert len(manager.deployment_managers) == 2
        assert len(manager.tool_managers) == 2

        # Verify get_backend was called for each production backend
        expected_calls = [call("docker"), call("kubernetes")]
        mock_get_backend.assert_has_calls(expected_calls, any_order=True)

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    def test_initialization_with_failed_backend(self, mock_get_backend):
        """Test initialization when one backend fails."""

        def get_backend_side_effect(backend_type):
            if backend_type == "kubernetes":
                raise Exception("Kubernetes not available")
            return Mock()

        mock_get_backend.side_effect = get_backend_side_effect

        with (
            patch("mcp_template.core.deployment_manager.DeploymentManager"),
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            manager = MultiBackendManager()

            # Should only have docker backend (kubernetes failed, mock excluded by default)
            available_backends = manager.get_available_backends()
            assert "docker" in available_backends
            assert "kubernetes" not in available_backends

    def test_initialization_with_custom_backends(self):
        """Test initialization with custom backend list."""
        with (
            patch(
                "mcp_template.core.multi_backend_manager.get_backend"
            ) as mock_get_backend,
            patch("mcp_template.core.deployment_manager.DeploymentManager"),
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_get_backend.return_value = Mock()

            manager = MultiBackendManager(enabled_backends=["docker", "mock"])

            assert manager.get_available_backends() == ["docker", "mock"]
            # Should not try to initialize kubernetes
            calls = [call[0][0] for call in mock_get_backend.call_args_list]
            assert "kubernetes" not in calls


class TestGetAllDeployments:
    """Test getting deployments from all backends."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_all_deployments_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful retrieval of deployments from all backends."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = [
            {"id": "docker-123", "template": "demo", "status": "running"},
            {"id": "docker-456", "template": "github", "status": "stopped"},
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_all_deployments()

        # Verify that mocks were used
        assert mock_get_backend.called
        assert mock_dm_class.called
        assert mock_tm_class.called

        # Verify result contains expected deployments (2 backends × 2 deployments each = 4 total)
        assert (
            len(result) == 4
        )  # 2 deployments from docker backend + 2 from kubernetes backend

        # Check that backend_type was added to each deployment
        backend_types = [d["backend_type"] for d in result]
        assert "docker" in backend_types
        assert "kubernetes" in backend_types

        # Verify the deployment manager was called to get deployments
        assert (
            mock_deployment_manager.find_deployments_by_criteria.call_count == 2
        )  # Called once per backend

    def test_get_all_deployments_with_template_filter(
        self, mock_managers, sample_deployments
    ):
        """Test getting deployments filtered by template."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            for backend_type, deployments in sample_deployments.items():
                mock_managers[backend_type][
                    "deployment"
                ].find_deployments_by_criteria.return_value = deployments

            manager = MultiBackendManager()
            result = manager.get_all_deployments(template_name="demo")

            # Verify template filter was passed only to production backend managers
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.assert_called_once_with(template_name="demo")
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.assert_called_once_with(template_name="demo")
            # Mock backend should not be called
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.assert_not_called()

    def test_get_all_deployments_with_backend_failure(self, mock_managers):
        """Test getting deployments when one backend fails."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup one backend to fail
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "template": "demo", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.side_effect = Exception("K8s failed")
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.get_all_deployments()

            # Should still get deployments from working backends
            assert len(result) == 1
            assert result[0]["backend_type"] == "docker"


class TestBackendDetection:
    """Test backend detection functionality."""

    def test_detect_backend_for_deployment_success(self, mock_managers):
        """Test successful detection of backend for a deployment."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup: docker returns empty, kubernetes finds the deployment, mock returns empty
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "k8s-789", "template": "demo", "status": "running"}
            ]
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.detect_backend_for_deployment("k8s-789")

            assert result == "kubernetes"

    def test_detect_backend_for_deployment_not_found(self, mock_managers):
        """Test detection when deployment is not found in any backend."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup all backends to return empty
            for backend_managers in mock_managers.values():
                backend_managers[
                    "deployment"
                ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.detect_backend_for_deployment("non-existent-123")

            assert result is None

    def test_get_deployment_by_id_success(self, mock_managers):
        """Test getting deployment by ID with auto-detection."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup kubernetes to find the deployment
            deployment_data = {"id": "k8s-789", "template": "demo", "status": "running"}
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [deployment_data]
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.get_deployment_by_id("k8s-789")

            assert result is not None
            assert result["backend_type"] == "kubernetes"
            assert result["id"] == "k8s-789"


class TestStopDeployment:
    """Test stopping deployments with auto-detection."""

    def test_stop_deployment_success(self, mock_managers):
        """Test successful stop deployment with auto-detection."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup detection to find deployment in kubernetes
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "k8s-789", "template": "demo", "status": "running"}
            ]
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            # Setup stop operation to succeed
            mock_managers["kubernetes"]["deployment"].stop_deployment.return_value = {
                "success": True
            }

            manager = MultiBackendManager()
            result = manager.stop_deployment("k8s-789", timeout=30)

            assert result["success"] is True
            assert result["backend_type"] == "kubernetes"
            mock_managers["kubernetes"][
                "deployment"
            ].stop_deployment.assert_called_once_with("k8s-789", 30)

    def test_stop_deployment_not_found(self, mock_managers):
        """Test stop deployment when deployment is not found."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup all backends to return empty (deployment not found)
            for backend_managers in mock_managers.values():
                backend_managers[
                    "deployment"
                ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.stop_deployment("non-existent-123")

            assert result["success"] is False
            assert "not found in any backend" in result["error"]

    def test_stop_deployment_operation_failure(self, mock_managers):
        """Test stop deployment when the stop operation fails."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup detection to find deployment in docker
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "template": "demo", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            # Setup stop operation to fail
            mock_managers["docker"]["deployment"].stop_deployment.side_effect = (
                Exception("Stop failed")
            )

            manager = MultiBackendManager()
            result = manager.stop_deployment("docker-123")

            assert result["success"] is False
            assert "Stop failed" in result["error"]
            assert result["backend_type"] == "docker"


class TestGetDeploymentLogs:
    """Test getting deployment logs with auto-detection."""

    def test_get_deployment_logs_success(self, mock_managers):
        """Test successful log retrieval with auto-detection."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup detection to find deployment in docker
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "template": "demo", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            # Setup log retrieval to succeed
            mock_managers["docker"]["deployment"].get_deployment_logs.return_value = {
                "success": True,
                "logs": "Application log output\nAnother log line",
            }

            manager = MultiBackendManager()
            result = manager.get_deployment_logs("docker-123", lines=50, follow=True)

            assert result["success"] is True
            assert result["backend_type"] == "docker"
            assert "Application log output" in result["logs"]
            mock_managers["docker"][
                "deployment"
            ].get_deployment_logs.assert_called_once_with(
                "docker-123", lines=50, follow=True
            )

    def test_get_deployment_logs_not_found(self, mock_managers):
        """Test log retrieval when deployment is not found."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup all backends to return empty (deployment not found)
            for backend_managers in mock_managers.values():
                backend_managers[
                    "deployment"
                ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.get_deployment_logs("non-existent-123")

            assert result["success"] is False
            assert "not found in any backend" in result["error"]


class TestGetAllTools:
    """Test getting tools from all backends and templates."""

    def test_get_all_tools_success(self, mock_managers):
        """Test successful tool retrieval from all sources."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager") as mock_tm_class,
            patch(
                "mcp_template.core.template_manager.TemplateManager"
            ) as mock_template_class,
        ):

            # Setup manager mocks
            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]
            mock_tm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["tool"]

            mock_template_manager = Mock()
            mock_template_class.return_value = mock_template_manager

            # Setup template manager to return templates
            mock_template_manager.list_templates.return_value = {
                "demo": {"description": "Demo template"},
                "github": {"description": "GitHub integration"},
            }

            # Setup tool manager to return static tools
            mock_managers["docker"]["tool"].list_tools.side_effect = [
                {
                    "tools": [{"name": "echo", "description": "Echo tool"}]
                },  # demo template
                {
                    "tools": [{"name": "create_issue", "description": "Create issue"}]
                },  # github template
            ]

            # Setup deployment managers to return deployments
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "template": "demo", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "k8s-456", "template": "github", "status": "running"}
            ]
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            # Setup tool managers to return dynamic tools
            mock_managers["docker"]["tool"].list_tools.return_value = {
                "tools": [{"name": "echo", "description": "Echo tool"}]
            }
            mock_managers["kubernetes"]["tool"].list_tools.return_value = {
                "tools": [{"name": "create_issue", "description": "Create issue"}]
            }
            mock_managers["mock"]["tool"].list_tools.return_value = {"tools": []}

            manager = MultiBackendManager()
            result = manager.get_all_tools()

            # Verify result structure
            assert "static_tools" in result
            assert "dynamic_tools" in result
            assert "backend_summary" in result

            # Check that we have both static and dynamic tools
            assert len(result["static_tools"]) > 0
            assert len(result["dynamic_tools"]) > 0

    def test_get_all_tools_with_template_filter(self, mock_managers):
        """Test tool retrieval with template filter."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager") as mock_tm_class,
            patch(
                "mcp_template.core.template_manager.TemplateManager"
            ) as mock_template_class,
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]
            mock_tm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["tool"]

            mock_template_manager = Mock()
            mock_template_class.return_value = mock_template_manager
            mock_template_manager.list_templates.return_value = {
                "demo": {"description": "Demo template"}
            }

            # Setup deployments to be filtered by template
            for backend_type in ["docker", "kubernetes"]:
                mock_managers[backend_type][
                    "deployment"
                ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.get_all_tools(template_name="demo")

            # Verify template filter was applied only to production backend deployment queries
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.assert_called_with(template_name="demo")
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.assert_called_with(template_name="demo")
            # Mock backend should not be called
            mock_managers["mock"][
                "deployment"
            ].find_deployments_by_criteria.assert_not_called()


class TestCleanupOperations:
    """Test cleanup operations across all backends."""

    def test_cleanup_all_backends_success(self, mock_managers):
        """Test successful cleanup across all backends."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup cleanup operations to succeed for production backends
            mock_managers["docker"]["deployment"].cleanup_deployments.return_value = {
                "success": True
            }
            mock_managers["kubernetes"][
                "deployment"
            ].cleanup_deployments.return_value = {"success": True}

            manager = MultiBackendManager()
            result = manager.cleanup_all_backends(force=True)

            # Verify production backends were cleaned up
            mock_managers["docker"][
                "deployment"
            ].cleanup_deployments.assert_called_once_with(force=True)
            mock_managers["kubernetes"][
                "deployment"
            ].cleanup_deployments.assert_called_once_with(force=True)

            # Check summary (should be 2 production backends)
            assert result["summary"]["total_backends"] == 2
            assert result["summary"]["successful_cleanups"] == 2
            assert result["summary"]["failed_cleanups"] == 0

    def test_cleanup_all_backends_partial_failure(self, mock_managers):
        """Test cleanup when some backends fail."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup mixed success/failure - only production backends
            mock_managers["docker"]["deployment"].cleanup_deployments.return_value = {
                "success": True
            }
            mock_managers["kubernetes"][
                "deployment"
            ].cleanup_deployments.side_effect = Exception("Cleanup failed")

            manager = MultiBackendManager()
            result = manager.cleanup_all_backends()

            # Check individual results
            assert result["docker"]["success"] is True
            assert result["kubernetes"]["success"] is False

            # Check summary - only production backends
            assert result["summary"]["successful_cleanups"] == 1
            assert result["summary"]["failed_cleanups"] == 1


class TestBackendHealth:
    """Test backend health checking."""

    def test_get_backend_health_all_healthy(self, mock_managers):
        """Test health check when all backends are healthy."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup production backends to return deployments (indicating health)
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.return_value = []

            manager = MultiBackendManager()
            result = manager.get_backend_health()

            # Production backends should be marked as healthy
            assert result["docker"]["status"] == "healthy"
            assert result["docker"]["deployment_count"] == 1
            assert result["kubernetes"]["status"] == "healthy"
            assert result["kubernetes"]["deployment_count"] == 0

    def test_get_backend_health_with_failures(self, mock_managers):
        """Test health check when some backends have issues."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup mixed health states
            mock_managers["docker"][
                "deployment"
            ].find_deployments_by_criteria.return_value = [
                {"id": "docker-123", "status": "running"}
            ]
            mock_managers["kubernetes"][
                "deployment"
            ].find_deployments_by_criteria.side_effect = Exception("Connection failed")

            manager = MultiBackendManager()
            result = manager.get_backend_health()

            # Check health states
            assert result["docker"]["status"] == "healthy"
            assert result["kubernetes"]["status"] == "unhealthy"
            assert result["kubernetes"]["error"] == "Connection failed"


class TestExecuteOnBackend:
    """Test executing operations on specific backends."""

    def test_execute_on_backend_success(self, mock_managers):
        """Test successful execution on specific backend."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            mock_dm_class.side_effect = lambda backend_type: mock_managers[
                backend_type
            ]["deployment"]

            # Setup deployment manager method
            mock_managers["docker"]["deployment"].list_deployments.return_value = [
                {"id": "docker-123", "status": "running"}
            ]

            manager = MultiBackendManager()
            result = manager.execute_on_backend(
                "docker", "deployment", "list_deployments"
            )

            assert len(result) == 1
            assert result[0]["id"] == "docker-123"
            mock_managers["docker"]["deployment"].list_deployments.assert_called_once()

    def test_execute_on_backend_invalid_backend(self, mock_managers):
        """Test execution on invalid backend."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch("mcp_template.core.deployment_manager.DeploymentManager"),
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            manager = MultiBackendManager()

            with pytest.raises(ValueError, match="Backend invalid not available"):
                manager.execute_on_backend("invalid", "deployment", "list_deployments")

    def test_execute_on_backend_invalid_manager(self, mock_managers):
        """Test execution with invalid manager type."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch("mcp_template.core.deployment_manager.DeploymentManager"),
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            manager = MultiBackendManager()

            with pytest.raises(ValueError, match="Invalid manager type: invalid"):
                manager.execute_on_backend("docker", "invalid", "some_method")

    def test_execute_on_backend_invalid_method(self):
        """Test execution with invalid method."""
        with (
            patch("mcp_template.core.multi_backend_manager.get_backend"),
            patch(
                "mcp_template.core.deployment_manager.DeploymentManager"
            ) as mock_dm_class,
            patch("mcp_template.core.tool_manager.ToolManager"),
        ):

            # Create a mock that doesn't auto-create attributes
            mock_deployment_manager = Mock(spec=[])  # No methods available
            mock_dm_class.return_value = mock_deployment_manager

            manager = MultiBackendManager()

            with pytest.raises(
                AttributeError, match="Manager deployment has no method invalid_method"
            ):
                manager.execute_on_backend("docker", "deployment", "invalid_method")
