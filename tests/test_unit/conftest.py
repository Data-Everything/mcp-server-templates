"""
Unit test specific fixtures.

These fixtures are tailored for unit testing individual components
in isolation with minimal dependencies.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# =============================================================================
# Mock Service Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_file_service():
    """Mock file service for unit tests."""
    mock_service = Mock()
    mock_service.read_file.return_value = "mock file content"
    mock_service.write_file.return_value = True
    mock_service.exists.return_value = True
    mock_service.list_files.return_value = ["file1.txt", "file2.txt"]
    return mock_service


@pytest.fixture
def mock_template_loader():
    """Mock template loader for unit tests."""
    mock_loader = Mock()
    mock_loader.load_template.return_value = {
        "name": "Mock Template",
        "description": "Mock template for testing",
        "version": "1.0.0",
    }
    mock_loader.list_templates.return_value = ["template1", "template2"]
    return mock_loader


@pytest.fixture
def mock_container_runtime():
    """Mock container runtime for unit tests."""
    mock_runtime = Mock()
    mock_runtime.run_container.return_value = {
        "container_id": "mock-container-123",
        "status": "running",
    }
    mock_runtime.stop_container.return_value = True
    mock_runtime.list_containers.return_value = []
    return mock_runtime


# =============================================================================
# Patching Fixtures for Unit Tests
# =============================================================================


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls for unit tests."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "mock output"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for unit tests."""
    with patch("docker.from_env") as mock_client:
        mock_instance = Mock()
        mock_instance.containers.run.return_value = Mock(id="mock-container-id")
        mock_instance.containers.list.return_value = []
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_kubernetes_client():
    """Mock Kubernetes client for unit tests."""
    with patch("kubernetes.client.ApiClient") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        yield mock_instance


# =============================================================================
# Test Data for Unit Tests
# =============================================================================


@pytest.fixture
def minimal_config():
    """Minimal configuration for unit tests."""
    return {"backend": "mock", "log_level": "INFO"}


@pytest.fixture
def unit_test_template():
    """Simplified template for unit tests."""
    return {
        "name": "Unit Test Template",
        "description": "Template for unit testing",
        "version": "1.0.0",
        "config_schema": {
            "type": "object",
            "properties": {"test_param": {"type": "string", "default": "test_value"}},
        },
    }
