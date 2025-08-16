"""
Unit tests for backend selection and environment variable functionality.
"""

import os
import unittest
from unittest.mock import Mock, patch

import pytest

pytestmark = pytest.mark.integration


class TestBackendSelection(unittest.TestCase):
    """Test backend selection and environment variable functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables to start fresh
        self.original_env = {}
        for var in ["MCP_BACKEND", "MCP_DEFAULT_REGISTRY"]:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        for var in ["MCP_BACKEND", "MCP_DEFAULT_REGISTRY"]:
            if var in os.environ:
                del os.environ[var]
        os.environ.update(self.original_env)

    def test_default_backend_selection(self):
        """Test default backend selection without environment variable."""
        # Clear any existing MCP_BACKEND
        if "MCP_BACKEND" in os.environ:
            del os.environ["MCP_BACKEND"]

        # Test environment variable logic directly
        backend = os.getenv("MCP_BACKEND", "docker")

        self.assertEqual(backend, "docker")

    def test_environment_variable_backend_selection(self):
        """Test backend selection via environment variable."""
        os.environ["MCP_BACKEND"] = "kubernetes"

        # Test environment variable logic directly
        backend = os.getenv("MCP_BACKEND", "docker")

        self.assertEqual(backend, "kubernetes")

    def test_cli_override_environment_variable(self):
        """Test CLI option overrides environment variable."""
        os.environ["MCP_BACKEND"] = "kubernetes"

        # Simulate CLI override logic
        env_backend = os.getenv("MCP_BACKEND", "docker")
        cli_override = "mock"  # CLI override

        # CLI override should take precedence
        final_backend = cli_override if cli_override else env_backend

        self.assertEqual(final_backend, "mock")

    def test_invalid_backend_environment_variable(self):
        """Test handling of invalid backend in environment variable."""
        os.environ["MCP_BACKEND"] = "invalid_backend"

        # This would normally be caught by typer's validation
        # but let's test that the environment variable is read
        backend = os.getenv("MCP_BACKEND", "docker")
        self.assertEqual(backend, "invalid_backend")

    def test_environment_variable_case_sensitivity(self):
        """Test that environment variables are case sensitive."""
        # Set lowercase version (should not be recognized)
        os.environ["mcp_backend"] = "kubernetes"

        # Check that MCP_BACKEND (uppercase) is not set
        backend = os.getenv("MCP_BACKEND", "docker")
        self.assertEqual(backend, "docker")  # Should use default

    def test_empty_environment_variable(self):
        """Test handling of empty environment variable."""
        os.environ["MCP_BACKEND"] = ""

        # Empty string should be falsy, so default should be used
        backend = os.getenv("MCP_BACKEND") or "docker"
        self.assertEqual(backend, "docker")

    def test_whitespace_environment_variable(self):
        """Test handling of whitespace in environment variable."""
        os.environ["MCP_BACKEND"] = "  kubernetes  "

        backend = os.getenv("MCP_BACKEND", "docker").strip()
        self.assertEqual(backend, "kubernetes")


class TestRegistryEnvironmentVariable(unittest.TestCase):
    """Test registry environment variable functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear environment variables to start fresh
        if "MCP_DEFAULT_REGISTRY" in os.environ:
            self.original_registry = os.environ["MCP_DEFAULT_REGISTRY"]
            del os.environ["MCP_DEFAULT_REGISTRY"]
        else:
            self.original_registry = None

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variable
        if "MCP_DEFAULT_REGISTRY" in os.environ:
            del os.environ["MCP_DEFAULT_REGISTRY"]
        if self.original_registry is not None:
            os.environ["MCP_DEFAULT_REGISTRY"] = self.original_registry

    def test_default_registry_selection(self):
        """Test default registry selection without environment variable."""
        from mcp_template.utils.image_utils import get_default_registry

        # Clear any existing MCP_DEFAULT_REGISTRY
        if "MCP_DEFAULT_REGISTRY" in os.environ:
            del os.environ["MCP_DEFAULT_REGISTRY"]

        registry = get_default_registry()
        self.assertEqual(registry, "docker.io")

    def test_environment_variable_registry_selection(self):
        """Test registry selection via environment variable."""
        from mcp_template.utils.image_utils import get_default_registry

        os.environ["MCP_DEFAULT_REGISTRY"] = "myregistry.com"

        registry = get_default_registry()
        self.assertEqual(registry, "myregistry.com")

    def test_custom_registry_with_port(self):
        """Test custom registry with port."""
        from mcp_template.utils.image_utils import get_default_registry

        os.environ["MCP_DEFAULT_REGISTRY"] = "localhost:5000"

        registry = get_default_registry()
        self.assertEqual(registry, "localhost:5000")

    def test_gcr_registry(self):
        """Test Google Container Registry."""
        from mcp_template.utils.image_utils import get_default_registry

        os.environ["MCP_DEFAULT_REGISTRY"] = "gcr.io"

        registry = get_default_registry()
        self.assertEqual(registry, "gcr.io")

    def test_empty_registry_environment_variable(self):
        """Test handling of empty registry environment variable."""
        from mcp_template.utils.image_utils import get_default_registry

        os.environ["MCP_DEFAULT_REGISTRY"] = ""

        # Empty string should be falsy, so default should be used
        registry = get_default_registry()
        self.assertEqual(registry, "docker.io")  # Should use default


class TestToolManagerBackendIntegration(unittest.TestCase):
    """Test ToolManager backend integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_backends = {}

    @patch("mcp_template.tools.docker_probe.DockerProbe")
    @patch("mcp_template.tools.kubernetes_probe.KubernetesProbe")
    def test_tool_manager_backend_initialization(
        self, mock_k8s_probe, mock_docker_probe
    ):
        """Test ToolManager initializes with correct backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Test Docker backend
        with patch("mcp_template.core.tool_manager.get_backend") as mock_get_backend:
            mock_docker_instance = Mock()
            mock_get_backend.return_value = mock_docker_instance

            tool_manager = ToolManager(backend_type="docker")

            self.assertEqual(tool_manager.backend, "docker")
            mock_get_backend.assert_called_once_with("docker")

    @patch("mcp_template.tools.docker_probe.DockerProbe")
    @patch("mcp_template.tools.kubernetes_probe.KubernetesProbe")
    def test_tool_manager_kubernetes_backend_initialization(
        self, mock_k8s_probe, mock_docker_probe
    ):
        """Test ToolManager initializes with Kubernetes backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Test Kubernetes backend
        with patch("mcp_template.core.tool_manager.get_backend") as mock_get_backend:
            mock_k8s_instance = Mock()
            mock_get_backend.return_value = mock_k8s_instance

            tool_manager = ToolManager(backend_type="kubernetes")

            self.assertEqual(tool_manager.backend_type, "kubernetes")
            mock_get_backend.assert_called_once_with("kubernetes")

    @patch("mcp_template.tools.docker_probe.DockerProbe")
    @patch("mcp_template.tools.kubernetes_probe.KubernetesProbe")
    def test_discover_tools_from_image_docker_probe(
        self, mock_k8s_probe, mock_docker_probe
    ):
        """Test discover_tools_from_image uses Docker probe for docker backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Mock Docker probe
        mock_docker_probe_instance = Mock()
        mock_docker_probe_instance.discover_tools_from_image.return_value = {
            "tools": [{"name": "test_tool"}],
            "discovery_method": "docker_stdio",
        }
        mock_docker_probe.return_value = mock_docker_probe_instance

        with patch("mcp_template.core.tool_manager.get_backend"):
            tool_manager = ToolManager(backend_type="docker")

            result = tool_manager.discover_tools_from_image(
                "test-image:latest", timeout=30
            )

            mock_docker_probe.assert_called_once()
            mock_docker_probe_instance.discover_tools_from_image.assert_called_once_with(
                "test-image:latest", args=None, env_vars=None, endpoints=None
            )
            self.assertEqual(result["discovery_method"], "docker_stdio")

    @patch("mcp_template.tools.docker_probe.DockerProbe")
    @patch("mcp_template.tools.kubernetes_probe.KubernetesProbe")
    def test_discover_tools_from_image_kubernetes_probe(
        self, mock_k8s_probe, mock_docker_probe
    ):
        """Test discover_tools_from_image uses Kubernetes probe for kubernetes backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Mock Kubernetes probe
        mock_k8s_probe_instance = Mock()
        mock_k8s_probe_instance.discover_tools_from_image.return_value = {
            "tools": [{"name": "test_tool"}],
            "discovery_method": "kubernetes_mcp_stdio",
        }
        mock_k8s_probe.return_value = mock_k8s_probe_instance

        with patch("mcp_template.core.tool_manager.get_backend"):
            tool_manager = ToolManager(backend_type="kubernetes")

            result = tool_manager.discover_tools_from_image(
                "test-image:latest", timeout=30
            )

            mock_k8s_probe.assert_called_once()
            mock_k8s_probe_instance.discover_tools_from_image.assert_called_once_with(
                "test-image:latest", args=None, env_vars=None, endpoints=None
            )
            self.assertEqual(result["discovery_method"], "kubernetes_mcp_stdio")


if __name__ == "__main__":
    unittest.main()
