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

from mcp_template.backends import (
    DockerDeploymentService,
    KubernetesDeploymentService,
    MockDeploymentService,
)
from mcp_template.template.discovery import TemplateDiscovery


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
    with patch("pathlib.Path.exists") as mock_exists, patch(
        "pathlib.Path.is_file"
    ) as mock_is_file, patch("pathlib.Path.is_dir") as mock_is_dir, patch(
        "builtins.open", create=True
    ) as mock_open:

        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True

        yield {
            "exists": mock_exists,
            "is_file": mock_is_file,
            "is_dir": mock_is_dir,
            "open": mock_open,
        }


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
