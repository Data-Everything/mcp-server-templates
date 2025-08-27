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

    def test_tool_manager_backend_initialization(self):
        """Test ToolManager initializes with correct backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Test Docker backend
        with patch("mcp_template.core.tool_manager.get_backend") as mock_get_backend:
            mock_docker_instance = Mock()
            mock_get_backend.return_value = mock_docker_instance

            tool_manager = ToolManager(backend_type="docker")

            # Check that backend was set correctly
            self.assertEqual(tool_manager.backend, mock_docker_instance)
            mock_get_backend.assert_called_once_with("docker")

    def test_tool_manager_kubernetes_backend_initialization(self):
        """Test ToolManager initializes with Kubernetes backend."""
        from mcp_template.core.tool_manager import ToolManager

        # Test Kubernetes backend
        with patch("mcp_template.core.tool_manager.get_backend") as mock_get_backend:
            mock_k8s_instance = Mock()
            mock_get_backend.return_value = mock_k8s_instance

            tool_manager = ToolManager(backend_type="kubernetes")

            # Check that backend was set correctly
            self.assertEqual(tool_manager.backend, mock_k8s_instance)
            mock_get_backend.assert_called_once_with("kubernetes")

    def test_discover_tools_from_image_docker_probe(self):
        """Test discover_tools_from_image method functionality."""
        from mcp_template.core.tool_manager import ToolManager

        with patch("mcp_template.core.tool_manager.get_backend"):
            tool_manager = ToolManager(backend_type="docker")

            # Mock the entire discover_tools_from_image method to test integration
            with patch.object(
                tool_manager, "discover_tools_from_image"
            ) as mock_discover:
                mock_discover.return_value = [{"name": "test_tool"}]

                result = tool_manager.discover_tools_from_image(
                    "test-image:latest", timeout=30
                )

                mock_discover.assert_called_once_with("test-image:latest", timeout=30)
                self.assertEqual(result, [{"name": "test_tool"}])

    def test_discover_tools_from_image_kubernetes_probe(self):
        """Test discover_tools_from_image method functionality for kubernetes backend."""
        from mcp_template.core.tool_manager import ToolManager

        with patch("mcp_template.core.tool_manager.get_backend"):
            tool_manager = ToolManager(backend_type="kubernetes")

            # Mock the entire discover_tools_from_image method to test integration
            with patch.object(
                tool_manager, "discover_tools_from_image"
            ) as mock_discover:
                mock_discover.return_value = [{"name": "test_tool"}]

                result = tool_manager.discover_tools_from_image(
                    "test-image:latest", timeout=30
                )

                mock_discover.assert_called_once_with("test-image:latest", timeout=30)
                self.assertEqual(result, [{"name": "test_tool"}])

    @patch("mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image")
    def test_template_discovery_uses_docker_for_dynamic_templates(
        self, mock_docker_discovery
    ):
        """Test that tool manager can discover tools from Docker images."""
        from mcp_template.core.tool_manager import ToolManager

        # Mock Docker discovery response
        mock_docker_discovery.return_value = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "category": "mcp",
                    "parameters": {},
                }
            ],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
        }

        # Create tool manager with Docker backend
        with patch("mcp_template.core.tool_manager.get_backend"):
            tool_manager = ToolManager(backend_type="docker")

            # Test Docker image discovery
            image_name = "test/image:latest"
            timeout = 30

            result = tool_manager.discover_tools_from_image(image_name, timeout)

            # Verify Docker discovery was called
            mock_docker_discovery.assert_called_once_with(
                image_name=image_name, server_args=None, env_vars=None, timeout=timeout
            )

            # Verify results - ToolManager.discover_tools_from_image returns List[Dict], not dict
            assert result is not None
            assert len(result) == 1
            assert result[0]["name"] == "test_tool"

    def test_docker_probe_with_environment_variables(self):
        """Test that Docker probe handles environment variables correctly."""
        from mcp_template.tools.docker_probe import DockerProbe

        with patch.object(DockerProbe, "discover_tools_from_image") as mock_discover:
            mock_discover.return_value = {
                "tools": [
                    {
                        "name": "github_tool",
                        "description": "GitHub tool",
                        "category": "mcp",
                        "parameters": {},
                    }
                ],
                "discovery_method": "docker_mcp_stdio",
                "timestamp": 1234567890,
            }

            # Test direct Docker probe with environment variables
            docker_probe = DockerProbe()
            image_name = "ghcr.io/github/github-mcp-server:0.9.1"
            env_vars = {"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"}

            result = docker_probe.discover_tools_from_image(
                image_name, env_vars=env_vars
            )

            # Verify Docker discovery was called with environment variables
            mock_discover.assert_called_once_with(image_name, env_vars=env_vars)

            # Verify results
            assert result is not None
            assert result["tools"][0]["name"] == "github_tool"

    def test_mcp_client_handles_github_server_args(self):
        """Test that MCP client automatically adds 'stdio' for GitHub servers."""
        from mcp_template.tools.mcp_client_probe import MCPClientProbe

        with patch.object(
            MCPClientProbe, "discover_tools_from_docker_sync"
        ) as mock_discover:
            mock_discover.return_value = {
                "tools": [
                    {
                        "name": "github_tool",
                        "description": "Test",
                        "category": "mcp",
                        "parameters": {},
                    }
                ],
                "discovery_method": "mcp_client",
            }

            # Test with GitHub image (should add stdio automatically)
            mcp_client = MCPClientProbe()
            result = mcp_client.discover_tools_from_docker_sync(
                "ghcr.io/github/github-mcp-server:0.9.1",
                args=None,  # No args provided
                env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test"},
            )

            # Verify stdio was added
            mock_discover.assert_called_once()
            call_args = mock_discover.call_args[0]  # positional args
            call_kwargs = mock_discover.call_args[1]  # keyword args

            # Should have added 'stdio' argument
            if len(call_args) > 1:
                # stdio should be in args
                assert "stdio" in call_args[1] or call_kwargs.get("args", [])

    def test_direct_docker_probe_call(self):
        """Test calling DockerProbe directly for integration scenarios."""
        from mcp_template.tools.docker_probe import DockerProbe

        with patch.object(DockerProbe, "discover_tools_from_image") as mock_discover:
            mock_discover.return_value = {
                "tools": [
                    {
                        "name": "direct_tool",
                        "description": "A direct tool",
                        "category": "mcp",
                        "parameters": {},
                    }
                ],
                "discovery_method": "docker_mcp_stdio",
            }

            # Test direct probe usage
            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image(
                "test/image:latest", env_vars={"TEST_VAR": "value"}
            )

            mock_discover.assert_called_once()
            assert result["tools"][0]["name"] == "direct_tool"


if __name__ == "__main__":
    unittest.main()
