"""
Centralized pytest fixtures for the mcp-template test suite.

This module provides commonly used fixtures across unit and integration tests
to reduce duplication and improve test maintainability.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from mcp_template.core.config_processor import ConfigProcessor
from mcp_template.core.deployment_manager import DeploymentManager

# =============================================================================
# Core Component Fixtures
# =============================================================================


@pytest.fixture
def config_processor():
    """Create a ConfigProcessor instance for testing."""
    return ConfigProcessor()


@pytest.fixture
def deployment_manager():
    """Create a DeploymentManager instance with docker backend for testing."""
    return DeploymentManager("docker")


@pytest.fixture
def deployment_manager_mock():
    """Create a DeploymentManager instance with mock backend for testing."""
    return DeploymentManager("mock")


# =============================================================================
# Mock Backend Fixtures
# =============================================================================


@pytest.fixture
def mock_docker_backend():
    """Create a mocked Docker backend for testing."""
    mock_backend = Mock()
    mock_backend.backend_type = "docker"
    mock_backend.deploy.return_value = {
        "success": True,
        "deployment_id": "test-deployment-123",
        "message": "Deployment successful",
    }
    mock_backend.list_deployments.return_value = []
    mock_backend.cleanup_stopped_containers.return_value = {
        "success": True,
        "cleaned_containers": [],
        "failed_cleanups": [],
        "message": "No containers to clean up",
    }
    return mock_backend


@pytest.fixture
def mock_kubernetes_backend():
    """Create a mocked Kubernetes backend for testing."""
    mock_backend = Mock()
    mock_backend.backend_type = "kubernetes"
    mock_backend.deploy.return_value = {
        "success": True,
        "deployment_id": "test-k8s-deployment-456",
        "message": "Kubernetes deployment successful",
    }
    mock_backend.list_deployments.return_value = []
    return mock_backend


@pytest.fixture
def mock_backends():
    """Create a collection of mocked backend instances."""
    docker_backend = Mock()
    docker_backend.backend_type = "docker"

    k8s_backend = Mock()
    k8s_backend.backend_type = "kubernetes"

    mock_backend = Mock()
    mock_backend.backend_type = "mock"

    return {"docker": docker_backend, "kubernetes": k8s_backend, "mock": mock_backend}


# =============================================================================
# Template and Configuration Fixtures
# =============================================================================


@pytest.fixture
def sample_template():
    """Create a sample template configuration for testing."""
    return {
        "config_schema": {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "description": "Logging level",
                    "default": "INFO",
                    "env_mapping": "LOG_LEVEL",
                },
                "allowed_dirs": {
                    "type": "string",
                    "description": "Allowed directories",
                    "env_mapping": "ALLOWED_DIRS",
                    "volume_mount": True,
                    "command_arg": True,
                },
                "read_only_mode": {
                    "type": "boolean",
                    "description": "Read-only mode",
                    "default": False,
                    "env_mapping": "READ_ONLY_MODE",
                },
            },
            "required": ["allowed_dirs"],
        },
        "env_vars": {
            "LOG_LEVEL": "INFO",
        },
        "environment_variables": {
            "NODE_ENV": "production",
            "MCP_LOG_LEVEL": "INFO",
        },
    }


@pytest.fixture
def sample_template_minimal():
    """Create a minimal template configuration for testing."""
    return {
        "name": "Test Template",
        "description": "A template for testing",
        "version": "1.0.0",
        "docker_image": "test/image:latest",
        "tool_discovery": "dynamic",
        "tool_endpoint": "/tools",
        "has_image": True,
        "origin": "internal",
    }


@pytest.fixture
def sample_deployments():
    """Create sample deployment data for testing."""
    return [
        {
            "id": "docker-123",
            "template": "demo",
            "status": "running",
            "backend_type": "docker",
            "created_at": "2024-01-01T10:00:00Z",
        },
        {
            "id": "docker-456",
            "template": "filesystem",
            "status": "stopped",
            "backend_type": "docker",
            "created_at": "2024-01-01T11:00:00Z",
        },
        {
            "id": "k8s-789",
            "template": "demo",
            "status": "running",
            "backend_type": "kubernetes",
            "created_at": "2024-01-01T12:00:00Z",
        },
    ]


# =============================================================================
# File System Fixtures
# =============================================================================


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_templates_dir(temp_dir):
    """Create a temporary templates directory with sample structure."""
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir()

    # Create a sample template directory
    demo_dir = templates_dir / "demo"
    demo_dir.mkdir()

    # Create sample template.json
    template_json = demo_dir / "template.json"
    template_json.write_text(
        """{
        "name": "Demo Template",
        "description": "A demo template for testing",
        "version": "1.0.0",
        "docker_image": "demo/image:latest",
        "tool_discovery": "dynamic",
        "tool_endpoint": "/tools",
        "has_image": true,
        "origin": "internal"
    }"""
    )

    # Create sample Dockerfile
    dockerfile = demo_dir / "Dockerfile"
    dockerfile.write_text("FROM python:3.9\nRUN echo 'Hello World'")

    return templates_dir


# =============================================================================
# Test Data Fixtures
# =============================================================================


@pytest.fixture
def sample_config_values():
    """Sample configuration values for testing."""
    return {
        "log_level": "DEBUG",
        "allowed_dirs": "/tmp,/var/log",
        "read_only_mode": True,
        "custom_setting": "test_value",
    }


@pytest.fixture
def sample_environment_vars():
    """Sample environment variables for testing."""
    return {
        "MCP_LOG_LEVEL": "INFO",
        "MCP_ALLOWED_DIRS": "/home/user",
        "MCP_READ_ONLY_MODE": "false",
        "NODE_ENV": "production",
    }


@pytest.fixture
def sample_volume_mounts():
    """Sample volume mount configurations for testing."""
    return [
        "/host/path:/container/path:ro",
        "/another/host/path:/another/container/path:rw",
        {"host": "/host/volume", "container": "/container/volume", "mode": "ro"},
    ]
