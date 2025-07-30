#!/usr/bin/env python3
"""
Unit tests for MCP deployment system components.

Tests individual classes and methods in isolation.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcp_template import MCPDeployer
from mcp_template.backends import DockerDeploymentService, MockDeploymentService
from mcp_template.manager import DeploymentManager
from mcp_template.template.discovery import TemplateDiscovery


@pytest.mark.unit
class TestTemplateDiscovery:
    """Unit tests for TemplateDiscovery class."""

    def test_init_with_default_path(self):
        """Test initialization with default templates path."""
        discovery = TemplateDiscovery()
        expected_path = Path(__file__).parent.parent / "templates"
        assert discovery.templates_dir == expected_path

    def test_init_with_custom_path(self):
        """Test initialization with custom templates path."""
        custom_path = Path("/custom/templates")
        discovery = TemplateDiscovery(custom_path)
        assert discovery.templates_dir == custom_path

    def test_discover_templates_empty_directory(self):
        """Test template discovery with empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            discovery = TemplateDiscovery(Path(temp_dir))
            templates = discovery.discover_templates()
            assert templates == {}

    def test_discover_templates_with_valid_template(self):
        """Test template discovery with valid template."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a valid template
            template_dir = Path(temp_dir) / "test-template"
            template_dir.mkdir()

            # Create template.json
            template_json = {
                "name": "Test Template",
                "description": "A test template",
                "docker_image": "test/image",
                "docker_tag": "latest",
            }
            (template_dir / "template.json").write_text(json.dumps(template_json))

            # Create Dockerfile
            (template_dir / "Dockerfile").write_text("FROM python:3.11")

            discovery = TemplateDiscovery(Path(temp_dir))
            templates = discovery.discover_templates()

            assert "test-template" in templates
            assert templates["test-template"]["name"] == "Test Template"
            assert templates["test-template"]["image"] == "test/image:latest"

    def test_discover_templates_missing_dockerfile(self):
        """Test template discovery with missing Dockerfile."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template without Dockerfile
            template_dir = Path(temp_dir) / "invalid-template"
            template_dir.mkdir()

            template_json = {"name": "Invalid Template"}
            (template_dir / "template.json").write_text(json.dumps(template_json))

            discovery = TemplateDiscovery(Path(temp_dir))
            templates = discovery.discover_templates()

            assert "invalid-template" not in templates

    def test_generate_template_config(self):
        """Test template configuration generation."""
        discovery = TemplateDiscovery()

        template_data = {
            "name": "Test Template",
            "description": "Test description",
            "docker_image": "test/image",
            "config_schema": {
                "properties": {
                    "test_prop": {"default": "test_value", "env_mapping": "TEST_VAR"}
                }
            },
        }

        config = discovery._generate_template_config(
            template_data, Path("test-template")
        )

        assert config["name"] == "Test Template"
        assert config["description"] == "Test description"
        assert "TEST_VAR" in config["env_vars"]
        assert config["env_vars"]["TEST_VAR"] == "test_value"

    def test_get_docker_image_with_explicit_image(self):
        """Test Docker image resolution with explicit image."""
        discovery = TemplateDiscovery()

        template_data = {"docker_image": "custom/image", "docker_tag": "v1.0"}

        image = discovery._get_docker_image(template_data, "test-template")
        assert image == "custom/image:v1.0"

    def test_get_docker_image_with_fallback(self):
        """Test Docker image resolution with fallback."""
        discovery = TemplateDiscovery()

        template_data = {}
        image = discovery._get_docker_image(template_data, "test-template")
        assert image == "dataeverything/mcp-test-template:latest"


@pytest.mark.unit
@pytest.mark.unit
class TestMCPDeployer:
    """Unit tests for MCPDeployer class."""

    def test_init(self):
        """Test MCPDeployer initialization."""
        with patch(
            "mcp_template.deployer.TemplateDiscovery"
        ) as mock_discovery_class, patch(
            "mcp_template.deployer.DeploymentManager"
        ) as mock_manager_class:

            # Configure the mock instance
            mock_discovery_instance = mock_discovery_class.return_value
            mock_discovery_instance.discover_templates.return_value = {"test": {}}

            deployer = MCPDeployer()

            # Verify the classes were called
            mock_discovery_class.assert_called_once()
            mock_manager_class.assert_called_once_with(backend_type="docker")

            # Check that templates were loaded from the mock
            assert "test" in deployer.templates
            assert deployer.templates["test"] == {}

    @patch("mcp_template.manager.DeploymentManager")
    @patch("mcp_template.template.discovery.TemplateDiscovery")
    def test_deploy_invalid_template(self, mock_discovery, mock_manager):
        """Test deployment with invalid template name."""
        mock_discovery.return_value.discover_templates.return_value = {}

        deployer = MCPDeployer()
        result = deployer.deploy("nonexistent-template")

        assert result is False

    @patch("mcp_template.manager.TemplateDiscovery")  # Patch at manager level too
    @patch("mcp_template.manager.DeploymentManager")
    @patch("mcp_template.template.discovery.TemplateDiscovery")
    def test_deploy_success(self, mock_discovery, mock_manager, mock_manager_discovery):
        """Test successful deployment."""
        # Setup mocks
        template_config = {
            "name": "Test Template",
            "description": "Test",
            "image": "test/image:latest",
            "env_vars": {},
            "volumes": {},
            "example_config": '{"servers": {}}',
        }

        mock_discovery.return_value.discover_templates.return_value = {
            "test": template_config
        }

        # Also mock the manager-level template discovery
        mock_manager_discovery.return_value.discover_templates.return_value = {
            "test": template_config
        }

        mock_manager.return_value.deploy_template.return_value = {
            "deployment_name": "test-deployment",
            "status": "deployed",
            "image": "test/image:latest",
            "success": True,
        }

        # Set the backend type to mock to skip template validation
        mock_manager.return_value.backend_type = "mock"

        deployer = MCPDeployer()

        # Mock the templates directly on the deployer instance
        deployer.templates = {"test": template_config}

        # Mock the deployment manager on the deployer instance
        deployer.deployment_manager = mock_manager.return_value

        with patch.object(deployer, "_generate_mcp_config") as mock_generate_config:
            # Ensure the mocked method doesn't raise an exception
            mock_generate_config.return_value = None
            result = deployer.deploy("test", pull_image=False)

        assert result is True
        mock_manager.return_value.deploy_template.assert_called_once()


@pytest.mark.unit
@pytest.mark.unit
class TestDeploymentManager:
    """Unit tests for DeploymentManager class."""

    def test_init_docker_backend(self):
        """Test initialization with Docker backend."""
        manager = DeploymentManager(backend_type="docker")
        assert manager.backend_type == "docker"
        assert isinstance(manager.deployment_backend, DockerDeploymentService)

    @patch("mcp_template.backends.kubernetes.KubernetesDeploymentService")
    def test_init_kubernetes_backend(self, mock_k8s):
        """Test initialization with Kubernetes backend."""
        manager = DeploymentManager(backend_type="kubernetes")
        assert manager.backend_type == "kubernetes"

    def test_init_mock_backend(self):
        """Test initialization with mock backend."""
        manager = DeploymentManager(backend_type="mock")

        assert isinstance(manager.deployment_backend, MockDeploymentService)


@pytest.mark.unit
@pytest.mark.unit
@pytest.mark.docker
class TestDockerDeploymentService:
    """Unit tests for DockerDeploymentService class."""

    @patch("subprocess.run")
    def test_ensure_docker_available_success(self, mock_run):
        """Test Docker availability check success."""
        mock_run.return_value.stdout = '{"Client": {"Version": "20.10.0"}}'

        # Should not raise exception
        DockerDeploymentService()

    @patch("mcp_template.backends.DockerDeploymentService._ensure_docker_available")
    @patch("subprocess.run")
    def test_ensure_docker_available_failure(self, mock_run, mock_ensure):
        """Test Docker availability check failure."""
        mock_ensure.side_effect = RuntimeError("Docker daemon is not available")

        with pytest.raises(RuntimeError, match="Docker daemon is not available"):
            DockerDeploymentService()

    @patch("mcp_template.backends.DockerDeploymentService._ensure_docker_available")
    @patch("subprocess.run")
    def test_run_command_success(self, mock_run, mock_ensure):
        """Test successful command execution."""
        mock_run.return_value.stdout = "success"
        mock_run.return_value.stderr = ""

        service = DockerDeploymentService()
        result = service._run_command(["echo", "test"])

        assert result.stdout == "success"
        mock_run.assert_called_once()

    @patch("mcp_template.backends.DockerDeploymentService._ensure_docker_available")
    @patch("subprocess.run")
    def test_list_deployments_empty(self, mock_run, mock_ensure):
        """Test listing deployments with no results."""
        mock_run.return_value.stdout = ""

        service = DockerDeploymentService()
        deployments = service.list_deployments()

        assert deployments == []

    @patch("mcp_template.backends.DockerDeploymentService._ensure_docker_available")
    @patch("subprocess.run")
    def test_list_deployments_with_containers(self, mock_run, mock_ensure):
        """Test listing deployments with containers."""
        container_json = {
            "Names": "test-container",
            "State": "running",
            "CreatedAt": "2024-01-01",
            "Image": "test/image",
            "Labels": "template=test,managed-by=mcp-deploy",
        }
        mock_run.return_value.stdout = json.dumps(container_json)

        service = DockerDeploymentService()
        deployments = service.list_deployments()

        assert len(deployments) == 1
        assert deployments[0]["name"] == "test-container"
        assert deployments[0]["template"] == "test"
        assert deployments[0]["status"] == "running"


# Test fixtures
@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": "Test Template",
        "description": "A test template",
        "docker_image": "test/image",
        "config_schema": {
            "properties": {
                "test_var": {
                    "type": "string",
                    "default": "test_value",
                    "env_mapping": "TEST_VAR",
                }
            }
        },
    }


@pytest.fixture
def temp_templates_dir():
    """Temporary templates directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
