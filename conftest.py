"""
Global test configuration and fixtures for MCP Server Templates.

This module provides shared fixtures and test utilities for comprehensive
testing of the MCP template system with proper isolation and cleanup.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# Import backend deployment services. Some environments running tests may not
# have optional dependencies (for example the `kubernetes` package). Import
# these lazily / with a fallback so the test collection step doesn't fail
# when optional packages are missing.
try:
    from mcp_template.backends import (
        DockerDeploymentService,
        KubernetesDeploymentService,
        MockDeploymentService,
    )
except Exception:
    # Fallback to simple stubs so tests that don't exercise the real
    # implementations can still import the fixtures. Individual tests that
    # require full backend functionality should patch/monkeypatch these
    # fixtures or skip when dependencies are not available.
    from unittest.mock import MagicMock

    DockerDeploymentService = MagicMock
    KubernetesDeploymentService = MagicMock
    MockDeploymentService = MagicMock

from mcp_template.template.utils.discovery import TemplateDiscovery


@pytest.fixture(scope="session")
def built_internal_images():
    """Build all internal template images before running deploy tests."""
    import subprocess
    from pathlib import Path

    import docker

    # Get the root directory and templates path
    root_dir = Path(__file__).parent
    templates_dir = root_dir / "templates"

    # Initialize template discovery to find internal templates
    discovery = TemplateDiscovery()
    templates = discovery.discover_templates()

    built_images = []

    try:
        client = docker.from_env()

        for template_id, template_config in templates.items():
            # Only build internal templates
            if template_config.get("origin") == "internal":
                template_path = templates_dir / template_id
                dockerfile_path = template_path / "Dockerfile"

                if dockerfile_path.exists():
                    image_name = f"mcp-{template_id}:latest"
                    print(f"Building internal template image: {image_name}")

                    try:
                        # Build the image
                        client.images.build(
                            path=str(template_path),
                            tag=image_name,
                            quiet=False,
                            rm=True,
                        )
                        built_images.append(image_name)
                        print(f"Successfully built: {image_name}")
                    except Exception as e:
                        print(f"Warning: Failed to build {image_name}: {e}")

    except Exception as e:
        print(f"Warning: Docker not available for image building: {e}")

    yield built_images

    # Cleanup built images after tests
    try:
        for image_name in built_images:
            try:
                client.images.remove(image_name, force=True)
                print(f"Cleaned up image: {image_name}")
            except Exception as e:
                print(f"Warning: Failed to cleanup {image_name}: {e}")
    except Exception:
        pass  # Docker might not be available


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_template_dir():
    """Create a temporary directory with template structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "test-template"
        template_dir.mkdir()

        # Create template.json
        template_config = {
            "name": "Test Template",
            "description": "A test template",
            "version": "1.0.0",
            "author": "Test Author",
            "category": "Test",
            "tags": ["test"],
            "docker_image": "test/template",
            "docker_tag": "latest",
            "ports": {"8080": 8080},
            "command": ["python", "server.py"],
            "transport": {
                "default": "stdio",
                "supported": ["stdio", "http"],
                "port": 8080,
            },
            "config_schema": {
                "type": "object",
                "properties": {
                    "test_param": {
                        "type": "string",
                        "default": "test_value",
                        "description": "Test parameter",
                    }
                },
            },
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f, indent=2)

        # Create basic files
        (template_dir / "server.py").write_text("# Test server")
        (template_dir / "Dockerfile").write_text("FROM python:3.12")
        (template_dir / "README.md").write_text("# Test Template")

        yield template_dir


@pytest.fixture
def mock_template_config():
    """Mock template configuration."""
    return {
        "name": "Mock Template",
        "description": "A mock template for testing",
        "version": "1.0.0",
        "author": "Test Suite",
        "category": "Test",
        "tags": ["mock", "test"],
        "docker_image": "mock/template",
        "docker_tag": "test",
        "ports": {"9000": 9000},
        "command": ["python", "mock_server.py"],
        "transport": {"default": "stdio", "supported": ["stdio"], "port": 9000},
        "config_schema": {
            "type": "object",
            "properties": {
                "mock_param": {
                    "type": "string",
                    "default": "mock_value",
                    "env_mapping": "MOCK_PARAM",
                }
            },
        },
    }


@pytest.fixture
def template_manager(temp_template_dir):
    """Template manager fixture with test template."""
    manager = TemplateDiscovery()
    # Add our test template to the discovery paths
    manager.template_paths = [temp_template_dir.parent]
    return manager


@pytest.fixture
def docker_deployment_service():
    """Docker deployment service fixture."""
    return DockerDeploymentService()


@pytest.fixture
def k8s_deployment_service():
    """Kubernetes deployment service fixture."""
    return KubernetesDeploymentService()


@pytest.fixture
def mock_deployment_service():
    """Mock deployment service fixture."""
    return MockDeploymentService()


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for unit tests."""
    with patch("docker.from_env") as mock_docker:
        mock_client = MagicMock()
        mock_docker.return_value = mock_client

        # Configure container mocks
        mock_container = MagicMock()
        mock_container.id = "test_container_id"
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.attrs = {
            "State": {"Status": "running", "Health": {"Status": "healthy"}},
            "Config": {"Labels": {"template": "test", "managed-by": "mcp-template"}},
            "NetworkSettings": {"Ports": {"8080/tcp": [{"HostPort": "8080"}]}},
        }

        mock_client.containers.run.return_value = mock_container
        mock_client.containers.get.return_value = mock_container
        mock_client.containers.list.return_value = [mock_container]

        yield mock_client


@pytest.fixture
def sample_deployment_config():
    """Sample deployment configuration for tests."""
    return {
        "template_id": "demo",
        "deployment_name": "test-deployment",
        "config": {"hello_from": "Test", "log_level": "debug"},
        "pull_image": False,
    }


@pytest.fixture(autouse=True)
def cleanup_test_containers(mock_docker_client):
    """Automatically cleanup test containers after each test."""
    yield

    if mock_docker_client:
        try:
            # Clean up any test containers
            containers = mock_docker_client.containers.list(
                all=True, filters={"label": "test=true"}
            )
            for container in containers:
                try:
                    container.remove(force=True)
                except Exception:
                    pass  # Ignore cleanup errors
        except Exception:
            pass  # Ignore if Docker is not available


@pytest.fixture
def captured_logs():
    """Capture log output for testing."""
    import logging
    from io import StringIO

    log_capture_string = StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.DEBUG)

    # Get the root logger
    logger = logging.getLogger()
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    yield log_capture_string

    # Cleanup
    logger.removeHandler(ch)


@pytest.fixture
def mock_filesystem():
    """Mock filesystem operations for testing."""
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.is_file") as mock_is_file,
        patch("pathlib.Path.is_dir") as mock_is_dir,
        patch("builtins.open", create=True) as mock_open,
    ):

        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True

        yield {
            "exists": mock_exists,
            "is_file": mock_is_file,
            "is_dir": mock_is_dir,
            "open": mock_open,
        }


# Prevent unit tests from attempting to contact a real Kubernetes cluster.
# Tests that require Kubernetes should be marked with @pytest.mark.kubernetes
@pytest.fixture(autouse=True)
def _mock_kubernetes_service_for_unit_tests(request):
    """
    Autouse fixture that replaces the real KubernetesDeploymentService with a MagicMock
    for tests that are NOT marked with the 'kubernetes' marker. This prevents
    accidental attempts to load kubeconfig or contact the API server during
    fast unit test runs or in CI environments that don't provide a cluster.
    """
    # If the test explicitly needs kubernetes, don't mock.
    # Use get_closest_marker for robust detection (module/class/function markers).
    if request.node.get_closest_marker("kubernetes") is not None:
        yield
        return

    # Allow CI to disable the mock globally by setting env var
    # e.g. CI_DISABLE_K8S_MOCK=1 will skip the autouse mocking.
    import os

    if os.environ.get("CI_DISABLE_K8S_MOCK") == "1":
        yield
        return

    try:
        # Patch the internal methods that touch kubeconfig / API so creating
        # the service is safe in CI when no cluster is present. Tests that
        # require real Kubernetes behavior should use @pytest.mark.kubernetes
        # and will not have these patches applied.
        # Patch both the class object referenced from the package namespace
        # (`mcp_template.backends.KubernetesDeploymentService`) and the
        # original module path (`mcp_template.backends.kubernetes...`) so the
        # patch works regardless of import ordering in CI.
        with (
            patch(
                "mcp_template.backends.KubernetesDeploymentService._ensure_kubernetes_available",
                new=lambda self: True,
            ),
            patch(
                "mcp_template.backends.KubernetesDeploymentService._ensure_namespace_exists",
                new=lambda self, dry_run=False: None,
            ),
            patch(
                "mcp_template.backends.kubernetes.KubernetesDeploymentService._ensure_kubernetes_available",
                new=lambda self: True,
            ),
            patch(
                "mcp_template.backends.kubernetes.KubernetesDeploymentService._ensure_namespace_exists",
                new=lambda self, dry_run=False: None,
            ),
        ):
            yield
    except Exception:
        # If patching fails, yield to allow tests to surface real errors.
        yield


@pytest.fixture
def clear_cache():
    """
    Clear cache
    """

    from mcp_template.core.cache import CacheManager

    cache_manager = CacheManager()
    cache_manager.clear_all()


# Test markers for different test categories
pytestmark = [
    pytest.mark.asyncio,
]


# Helper functions for tests
def create_test_template(temp_dir: Path, template_id: str, **kwargs) -> Path:
    """Create a test template directory structure."""
    template_dir = temp_dir / template_id
    template_dir.mkdir(exist_ok=True)

    # Default template config
    config = {
        "name": f"Test {template_id.title()}",
        "description": f"Test template {template_id}",
        "version": "1.0.0",
        "author": "Test Suite",
        "docker_image": f"test/{template_id}",
        **kwargs,
    }

    # Write template.json
    with open(template_dir / "template.json", "w") as f:
        json.dump(config, f, indent=2)

    # Create basic files
    (template_dir / "server.py").write_text("# Test server")
    (template_dir / "Dockerfile").write_text("FROM python:3.12")
    (template_dir / "README.md").write_text(f"# Test {template_id}")

    return template_dir


def assert_deployment_success(result: Dict[str, Any]) -> None:
    """Assert that a deployment was successful."""
    assert result is not None
    assert "deployment_name" in result
    assert "status" in result
    assert result["status"] in ["deployed", "running"]


def assert_valid_template_config(config: Dict[str, Any]) -> None:
    """Assert that a template configuration is valid."""
    required_fields = ["name", "description", "version", "author"]
    for field in required_fields:
        assert field in config, f"Missing required field: {field}"
