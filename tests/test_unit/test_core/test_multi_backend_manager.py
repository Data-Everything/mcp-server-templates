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

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_all_deployments_with_template_filter(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test getting deployments filtered by template."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = [
            {"id": "demo-deploy-1", "template": "demo", "status": "running"}
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_all_deployments(template_name="demo")

        # Verify that mocks were used
        assert mock_get_backend.called
        assert mock_dm_class.called
        assert mock_tm_class.called

        # Verify result contains expected deployments (2 backends × 1 deployment each = 2 total)
        assert (
            len(result) == 2
        )  # 1 deployment from docker backend + 1 from kubernetes backend

        # Verify template filter was passed to deployment manager (called once per backend)
        assert mock_deployment_manager.find_deployments_by_criteria.call_count == 2

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_all_deployments_with_backend_failure(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test getting deployments when one backend fails."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks - one that succeeds, one that fails
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [
                {"id": "docker-123", "template": "demo", "status": "running"}
            ],  # First backend succeeds
            Exception("K8s failed"),  # Second backend fails
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_all_deployments()

        # Should still get deployments from working backends
        assert len(result) == 1
        assert result[0]["backend_type"] == "docker"


class TestBackendDetection:
    """Test backend detection functionality."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_detect_backend_for_deployment_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful detection of backend for a deployment."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks to return different results for each backend call
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [],  # First backend (docker) returns empty
            [
                {"id": "k8s-789", "template": "demo", "status": "running"}
            ],  # Second backend (kubernetes) finds the deployment
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.detect_backend_for_deployment("k8s-789")

        assert result == "kubernetes"

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_detect_backend_for_deployment_not_found(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test detection when deployment is not found in any backend."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks to return empty for all backends
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = []
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.detect_backend_for_deployment("non-existent-123")

        assert result is None

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_deployment_by_id_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test getting deployment by ID with auto-detection."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        deployment_data = {"id": "k8s-789", "template": "demo", "status": "running"}
        mock_deployment_manager = Mock()

        # Mock find_deployments_by_criteria to return:
        # - Empty for docker (first call)
        # - Deployment for kubernetes (second call)
        # - Empty for mock (third call - not reached)
        # - Then return deployment for the actual get call
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [],  # docker backend - detect call
            [deployment_data],  # kubernetes backend - detect call (finds it)
            [deployment_data],  # kubernetes backend - get call
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_deployment_by_id("k8s-789")

        assert result is not None
        assert result["backend_type"] == "kubernetes"
        assert result["id"] == "k8s-789"


class TestStopDeployment:
    """Test stopping deployments with auto-detection."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_stop_deployment_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful stop deployment with auto-detection."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        deployment_data = {"id": "k8s-789", "template": "demo", "status": "running"}
        mock_deployment_manager = Mock()

        # Mock find_deployments_by_criteria for detection:
        # - Empty for docker (first call)
        # - Deployment for kubernetes (second call - finds it)
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [],  # docker backend - detect call
            [deployment_data],  # kubernetes backend - detect call (finds it)
        ]

        # Mock stop operation to succeed
        mock_deployment_manager.stop_deployment.return_value = {"success": True}
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.stop_deployment("k8s-789", timeout=30)

        assert result["success"] is True
        assert result["backend_type"] == "kubernetes"
        mock_deployment_manager.stop_deployment.assert_called_once_with("k8s-789", 30)

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_stop_deployment_not_found(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test stop deployment when deployment is not found."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks to return empty for all backends
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = []
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.stop_deployment("non-existent-123")

        assert result["success"] is False
        assert "not found in any backend" in result["error"]

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_stop_deployment_operation_failure(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test stop deployment when the stop operation fails."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        deployment_data = {"id": "docker-123", "template": "demo", "status": "running"}
        mock_deployment_manager = Mock()

        # Mock find_deployments_by_criteria for detection:
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [deployment_data],  # docker backend - detect call (finds it)
        ]

        # Mock stop operation to fail
        mock_deployment_manager.stop_deployment.side_effect = Exception("Stop failed")
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.stop_deployment("docker-123")

        assert result["success"] is False
        assert "Stop failed" in result["error"]
        assert result["backend_type"] == "docker"


class TestGetDeploymentLogs:
    """Test getting deployment logs with auto-detection."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_deployment_logs_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful log retrieval with auto-detection."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        deployment_data = {"id": "docker-123", "template": "demo", "status": "running"}
        mock_deployment_manager = Mock()

        # Mock find_deployments_by_criteria for detection:
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [deployment_data],  # docker backend - detect call (finds it)
        ]

        # Mock log retrieval to succeed
        mock_deployment_manager.get_deployment_logs.return_value = {
            "success": True,
            "logs": "Application log output\nAnother log line",
        }
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_deployment_logs("docker-123", lines=50, follow=True)

        assert result["success"] is True
        assert result["backend_type"] == "docker"
        assert "Application log output" in result["logs"]
        mock_deployment_manager.get_deployment_logs.assert_called_once_with(
            "docker-123", lines=50, follow=True
        )

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_deployment_logs_not_found(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test log retrieval when deployment is not found."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks to return empty for all backends
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = []
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_deployment_logs("non-existent-123")

        assert result["success"] is False
        assert "not found in any backend" in result["error"]


class TestGetAllTools:
    """Test getting tools from all backends and templates."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    @patch("mcp_template.core.multi_backend_manager.TemplateManager")
    def test_get_all_tools_success(
        self, mock_template_class, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful tool retrieval from all sources."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup template manager mocks
        mock_template_manager = Mock()
        mock_template_manager.list_templates.return_value = {
            "demo": {"description": "Demo template"},
            "github": {"description": "GitHub integration"},
        }
        mock_template_class.return_value = mock_template_manager

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [{"id": "docker-123", "template": "demo", "status": "running"}],  # docker
            [
                {"id": "k8s-456", "template": "github", "status": "running"}
            ],  # kubernetes
            [],  # mock backend
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tool_manager.list_tools.side_effect = [
            {
                "tools": [{"name": "echo", "description": "Echo tool"}]
            },  # demo template static
            {
                "tools": [{"name": "create_issue", "description": "Create issue"}]
            },  # github template static
            {
                "tools": [{"name": "echo", "description": "Echo tool"}]
            },  # docker deployment dynamic
            {
                "tools": [{"name": "create_issue", "description": "Create issue"}]
            },  # kubernetes deployment dynamic
            {"tools": []},  # mock deployment dynamic
        ]
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_all_tools()

        # Verify result structure
        assert "static_tools" in result
        assert "dynamic_tools" in result
        assert "backend_summary" in result

        # Check that we have both static and dynamic tools
        assert len(result["static_tools"]) > 0
        assert len(result["dynamic_tools"]) > 0

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    @patch("mcp_template.core.multi_backend_manager.TemplateManager")
    def test_get_all_tools_with_template_filter(
        self, mock_template_class, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test tool retrieval with template filter."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup template manager mocks
        mock_template_manager = Mock()
        mock_template_manager.list_templates.return_value = {
            "demo": {"description": "Demo template"}
        }
        mock_template_class.return_value = mock_template_manager

        # Setup deployment manager mocks to return filtered results
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.return_value = []
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_all_tools(template_name="demo")

        # Verify template filter was applied - should be called 2 times for production backends
        assert mock_deployment_manager.find_deployments_by_criteria.call_count == 2
        # Check that calls were made with template filter
        calls = mock_deployment_manager.find_deployments_by_criteria.call_args_list
        for call_obj in calls:
            assert call_obj[1]["template_name"] == "demo"


class TestCleanupOperations:
    """Test cleanup operations across all backends."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_cleanup_all_backends_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful cleanup across all backends."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.cleanup_deployments.return_value = {"success": True}
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.cleanup_all_backends(force=True)

        # Verify cleanup was called for production backends (should be 2 calls - docker and kubernetes)
        assert mock_deployment_manager.cleanup_deployments.call_count == 2
        # Check that all calls were made with force=True
        for call_obj in mock_deployment_manager.cleanup_deployments.call_args_list:
            assert call_obj[1]["force"] is True

        # Check summary (should be 2 production backends)
        assert result["summary"]["total_backends"] == 2
        assert result["summary"]["successful_cleanups"] == 2
        assert result["summary"]["failed_cleanups"] == 0

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_cleanup_all_backends_partial_failure(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test cleanup when some backends fail."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks with mixed results
        mock_deployment_manager = Mock()
        mock_deployment_manager.cleanup_deployments.side_effect = [
            {"success": True},  # First backend (docker) succeeds
            Exception("Cleanup failed"),  # Second backend (kubernetes) fails
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
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

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_backend_health_all_healthy(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test health check when all backends are healthy."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [{"id": "docker-123", "status": "running"}],  # docker
            [],  # kubernetes
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_backend_health()

        # Production backends should be marked as healthy
        assert result["docker"]["status"] == "healthy"
        assert result["docker"]["deployment_count"] == 1
        assert result["kubernetes"]["status"] == "healthy"
        assert result["kubernetes"]["deployment_count"] == 0

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_get_backend_health_with_failures(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test health check when some backends have issues."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.find_deployments_by_criteria.side_effect = [
            [{"id": "docker-123", "status": "running"}],  # docker - healthy
            Exception("Connection failed"),  # kubernetes - unhealthy
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.get_backend_health()

        # Check health states
        assert result["docker"]["status"] == "healthy"
        assert result["kubernetes"]["status"] == "unhealthy"
        assert result["kubernetes"]["error"] == "Connection failed"


class TestExecuteOnBackend:
    """Test executing operations on specific backends."""

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_execute_on_backend_success(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test successful execution on specific backend."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_deployment_manager.list_deployments.return_value = [
            {"id": "docker-123", "status": "running"}
        ]
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()
        result = manager.execute_on_backend("docker", "deployment", "list_deployments")

        assert len(result) == 1
        assert result[0]["id"] == "docker-123"
        mock_deployment_manager.list_deployments.assert_called_once()

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_execute_on_backend_invalid_backend(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test execution on invalid backend."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()

        with pytest.raises(ValueError, match="Backend invalid not available"):
            manager.execute_on_backend("invalid", "deployment", "list_deployments")

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_execute_on_backend_invalid_manager(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test execution with invalid manager type."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Setup deployment manager mocks
        mock_deployment_manager = Mock()
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()

        with pytest.raises(ValueError, match="Invalid manager type: invalid"):
            manager.execute_on_backend("docker", "invalid", "some_method")

    @patch("mcp_template.core.multi_backend_manager.get_backend")
    @patch("mcp_template.core.multi_backend_manager.DeploymentManager")
    @patch("mcp_template.core.multi_backend_manager.ToolManager")
    def test_execute_on_backend_invalid_method(
        self, mock_tm_class, mock_dm_class, mock_get_backend
    ):
        """Test execution with invalid method."""

        # Setup backend mocks
        mock_backend = Mock()
        mock_get_backend.return_value = mock_backend

        # Create a mock that doesn't auto-create attributes
        mock_deployment_manager = Mock(spec=[])  # No methods available
        mock_dm_class.return_value = mock_deployment_manager

        # Setup tool manager mocks
        mock_tool_manager = Mock()
        mock_tm_class.return_value = mock_tool_manager

        # Create the manager
        manager = MultiBackendManager()

        with pytest.raises(
            AttributeError, match="Manager deployment has no method invalid_method"
        ):
            manager.execute_on_backend("docker", "deployment", "invalid_method")
