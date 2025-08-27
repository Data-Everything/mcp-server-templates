"""
Integration test specific fixtures.

These fixtures support integration testing with real components
and end-to-end scenarios.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

# =============================================================================
# Integration Test Environment Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def integration_test_workspace():
    """Create a dedicated workspace for integration tests."""
    with tempfile.TemporaryDirectory(prefix="mcp_integration_test_") as temp_dir:
        workspace = Path(temp_dir)

        # Create directory structure
        (workspace / "templates").mkdir()
        (workspace / "deployments").mkdir()
        (workspace / "logs").mkdir()

        yield workspace


@pytest.fixture
def integration_templates_dir(integration_test_workspace):
    """Create a templates directory with real template examples."""
    templates_dir = integration_test_workspace / "templates"

    # Create demo template
    demo_dir = templates_dir / "demo"
    demo_dir.mkdir()

    demo_template = demo_dir / "template.json"
    demo_template.write_text(
        """{
        "name": "Demo MCP Server",
        "description": "A demo MCP server for testing",
        "version": "1.0.0",
        "docker_image": "demo/mcp-server:latest",
        "tool_discovery": "dynamic",
        "tool_endpoint": "/tools",
        "has_image": true,
        "origin": "internal",
        "config_schema": {
            "type": "object",
            "properties": {
                "log_level": {
                    "type": "string",
                    "description": "Logging level",
                    "default": "INFO",
                    "env_mapping": "LOG_LEVEL"
                },
                "port": {
                    "type": "integer",
                    "description": "Server port",
                    "default": 8080,
                    "env_mapping": "SERVER_PORT"
                }
            }
        }
    }"""
    )

    demo_dockerfile = demo_dir / "Dockerfile"
    demo_dockerfile.write_text(
        """FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "server.py"]
"""
    )

    # Create filesystem template
    fs_dir = templates_dir / "filesystem"
    fs_dir.mkdir()

    fs_template = fs_dir / "template.json"
    fs_template.write_text(
        """{
        "name": "Filesystem MCP Server",
        "description": "A filesystem MCP server for testing",
        "version": "1.0.0",
        "docker_image": "filesystem/mcp-server:latest",
        "tool_discovery": "static",
        "has_image": true,
        "origin": "external",
        "config_schema": {
            "type": "object",
            "properties": {
                "allowed_dirs": {
                    "type": "string",
                    "description": "Allowed directories",
                    "env_mapping": "ALLOWED_DIRS",
                    "volume_mount": true,
                    "command_arg": true
                },
                "read_only": {
                    "type": "boolean",
                    "description": "Read-only mode",
                    "default": false,
                    "env_mapping": "READ_ONLY"
                }
            },
            "required": ["allowed_dirs"]
        }
    }"""
    )

    return templates_dir


@pytest.fixture
def full_deployment_config():
    """Complete deployment configuration for integration tests."""
    return {
        "template": "demo",
        "backend": "docker",
        "config": {"log_level": "DEBUG", "port": 9090},
        "environment": {"NODE_ENV": "test", "DEBUG": "true"},
        "volumes": ["/host/data:/app/data:ro"],
    }


@pytest.fixture
def multi_backend_config():
    """Configuration for testing multiple backends."""
    return {
        "backends": {
            "docker": {"enabled": True, "socket_path": "/var/run/docker.sock"},
            "kubernetes": {
                "enabled": True,
                "kubeconfig_path": "~/.kube/config",
                "namespace": "mcp-test",
            },
            "mock": {"enabled": True},
        }
    }


# =============================================================================
# Real Component Integration Fixtures
# =============================================================================


@pytest.fixture
def real_deployment_manager():
    """Create a real DeploymentManager for integration tests."""
    from mcp_template.core.deployment_manager import DeploymentManager

    return DeploymentManager("mock")  # Use mock backend for safety in tests


@pytest.fixture
def real_config_processor():
    """Create a real ConfigProcessor for integration tests."""
    from mcp_template.core.config_processor import ConfigProcessor

    return ConfigProcessor()


@pytest.fixture
def integration_test_deployment():
    """Create a test deployment for integration scenarios."""
    return {
        "id": "integration-test-deployment-001",
        "template": "demo",
        "status": "running",
        "backend_type": "mock",
        "created_at": "2024-01-15T10:00:00Z",
        "config": {"log_level": "INFO", "port": 8080},
        "environment": {"NODE_ENV": "test"},
        "ports": ["8080:8080"],
        "volumes": [],
    }


# =============================================================================
# End-to-End Scenario Fixtures
# =============================================================================


@pytest.fixture
def e2e_scenario_data():
    """Data for end-to-end testing scenarios."""
    return {
        "templates": ["demo", "filesystem"],
        "backends": ["mock", "docker"],
        "deployments": [
            {"template": "demo", "backend": "mock", "config": {"log_level": "INFO"}},
            {
                "template": "filesystem",
                "backend": "mock",
                "config": {"allowed_dirs": "/tmp", "read_only": True},
            },
        ],
    }


@pytest.fixture
def mock_external_services():
    """Mock external services for integration tests."""
    return {
        "docker_registry": Mock(),
        "kubernetes_api": Mock(),
        "monitoring_service": Mock(),
    }
