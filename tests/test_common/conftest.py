"""
Common test fixtures and utilities for common module testing.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from tests.test_fixtures.sample_data import (
    MOCK_FILE_STRUCTURE,
    SAMPLE_CONFIG_DATA,
    SAMPLE_DEPLOYMENT_DATA,
    SAMPLE_TEMPLATE_DATA,
    SAMPLE_TOOL_DATA,
)


@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return SAMPLE_TEMPLATE_DATA.copy()


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return SAMPLE_CONFIG_DATA.copy()


@pytest.fixture
def sample_tool_data():
    """Sample tool data for testing."""
    return SAMPLE_TOOL_DATA.copy()


@pytest.fixture
def sample_deployment_data():
    """Sample deployment data for testing."""
    return SAMPLE_DEPLOYMENT_DATA.copy()


@pytest.fixture
def temp_workspace(tmp_path):
    """Create a temporary workspace with realistic structure."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()

    # Create templates directory
    templates_dir = workspace / "templates"
    templates_dir.mkdir()

    # Create sample templates
    for template_name, template_data in SAMPLE_TEMPLATE_DATA.items():
        template_dir = templates_dir / template_name
        template_dir.mkdir()

        # Create template.json
        template_json = template_dir / "template.json"
        template_json.write_text(
            f'{{"name": "{template_name}", "version": "{template_data["version"]}"}}'
        )

        # Create README.md
        readme = template_dir / "README.md"
        readme.write_text(f"# {template_data['name']}\n{template_data['description']}")

        # Create server file
        if "server.py" in template_data.get("files", {}):
            server_file = template_dir / "server.py"
            server_file.write_text("# Server implementation")

        # Create config file
        if "config.json" in template_data.get("files", {}):
            config_file = template_dir / "config.json"
            config_file.write_text('{"name": "test-server", "port": 7071}')

    return workspace


@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    mock_fs = MagicMock()

    # Mock Path objects
    mock_fs.Path = Mock()
    mock_fs.exists = Mock(return_value=True)
    mock_fs.is_dir = Mock(return_value=True)
    mock_fs.is_file = Mock(return_value=True)
    mock_fs.iterdir = Mock(return_value=[])
    mock_fs.read_text = Mock(return_value='{"test": "data"}')
    mock_fs.write_text = Mock()
    mock_fs.mkdir = Mock()

    return mock_fs


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for deployment testing."""
    mock_client = MagicMock()

    # Mock container operations
    mock_container = MagicMock()
    mock_container.id = "container_123"
    mock_container.status = "running"
    mock_container.logs.return_value = b"Sample log output"
    mock_container.ports = {"7071/tcp": [{"HostPort": "7071"}]}

    mock_client.containers.run.return_value = mock_container
    mock_client.containers.get.return_value = mock_container
    mock_client.containers.list.return_value = [mock_container]

    # Mock image operations
    mock_client.images.build.return_value = (MagicMock(), [])
    mock_client.images.get.return_value = MagicMock()

    return mock_client


@pytest.fixture
def mock_kubernetes_client():
    """Mock Kubernetes client for deployment testing."""
    mock_client = MagicMock()

    # Mock V1Api
    mock_v1 = MagicMock()
    mock_client.CoreV1Api.return_value = mock_v1

    # Mock AppsV1Api
    mock_apps_v1 = MagicMock()
    mock_client.AppsV1Api.return_value = mock_apps_v1

    # Mock pod operations
    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"
    mock_pod.status.phase = "Running"
    mock_v1.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
    mock_v1.read_namespaced_pod_log.return_value = "Sample pod logs"

    # Mock deployment operations
    mock_deployment = MagicMock()
    mock_deployment.metadata.name = "test-deployment"
    mock_deployment.status.ready_replicas = 1
    mock_apps_v1.list_namespaced_deployment.return_value = MagicMock(
        items=[mock_deployment]
    )

    return mock_client


@pytest.fixture
def mock_tool_discovery():
    """Mock tool discovery operations."""
    mock_discovery = MagicMock()

    mock_discovery.discover_tools.return_value = SAMPLE_TOOL_DATA.copy()
    mock_discovery.validate_tool_schema.return_value = {"valid": True, "errors": []}
    mock_discovery.get_tool_by_name.return_value = SAMPLE_TOOL_DATA[0]

    return mock_discovery


class MockTemplateManager:
    """Mock TemplateManager for testing."""

    def __init__(self, templates_dir: Optional[str] = None):
        self.templates_dir = templates_dir or "/templates"
        self._templates = SAMPLE_TEMPLATE_DATA.copy()

    def list_templates(self) -> List[Dict[str, Any]]:
        return list(self._templates.values())

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        return self._templates.get(template_name)

    def validate_template(self, template_name: str) -> Dict[str, Any]:
        if template_name in self._templates:
            return {"valid": True, "errors": [], "warnings": []}
        return {
            "valid": False,
            "errors": [f"Template '{template_name}' not found"],
            "warnings": [],
        }

    def search_templates(self, query: str) -> List[Dict[str, Any]]:
        results = []
        for template in self._templates.values():
            if (
                query.lower() in template["name"].lower()
                or query.lower() in template["description"].lower()
                or query.lower() in " ".join(template.get("tags", []))
            ):
                results.append(template)
        return results


class MockDeploymentManager:
    """Mock DeploymentManager for testing."""

    def __init__(self, backend: str = "docker"):
        self.backend = backend
        self._deployments = SAMPLE_DEPLOYMENT_DATA.copy()

    def deploy_template(
        self, template_name: str, custom_name: Optional[str] = None, **kwargs
    ) -> Dict[str, Any]:
        deployment_id = custom_name or f"{template_name}-deployment"
        deployment = {
            "id": deployment_id,
            "template": template_name,
            "status": "running",
            "backend": self.backend,
            "created": "2024-08-11T10:30:01Z",
        }
        self._deployments[deployment_id] = deployment
        return deployment

    def stop_deployment(self, deployment_id: str) -> bool:
        if deployment_id in self._deployments:
            self._deployments[deployment_id]["status"] = "stopped"
            return True
        return False

    def list_deployments(self) -> List[Dict[str, Any]]:
        return list(self._deployments.values())

    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        return self._deployments.get(deployment_id)

    def get_deployment_logs(
        self, deployment_id: str, lines: int = 100
    ) -> Dict[str, Any]:
        if deployment_id in self._deployments:
            return {
                "logs": "Sample log output\nAnother log line",
                "deployment_id": deployment_id,
                "lines_returned": 2,
            }
        return {"error": "Deployment not found"}


class MockConfigManager:
    """Mock ConfigManager for testing."""

    def __init__(self):
        self._configs = SAMPLE_CONFIG_DATA.copy()

    def load_config_file(self, file_path: str) -> Dict[str, Any]:
        # Return different configs based on file path
        if "server" in file_path:
            return self._configs["server"]
        elif "deployment" in file_path:
            return self._configs["deployment"]
        elif "client" in file_path:
            return self._configs["client"]
        return {}

    def validate_configuration(
        self, config: Dict[str, Any], config_type: str = "server"
    ) -> Dict[str, Any]:
        required_fields = {
            "server": ["name", "port"],
            "client": ["server_url"],
            "deployment": ["backend"],
        }

        missing = []
        for field in required_fields.get(config_type, []):
            if field not in config:
                missing.append(field)

        return {
            "valid": len(missing) == 0,
            "errors": [f"Missing required field: {field}" for field in missing],
            "warnings": [],
        }

    def generate_example_config(self, config_type: str) -> Dict[str, Any]:
        return self._configs.get(config_type, {})


class MockToolManager:
    """Mock ToolManager for testing."""

    def __init__(self):
        self._tools = SAMPLE_TOOL_DATA.copy()

    def discover_tools(self, method: str = "auto", **kwargs) -> List[Dict[str, Any]]:
        return self._tools.copy()

    def validate_tool_call(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        tool = next((t for t in self._tools if t["name"] == tool_name), None)
        if not tool:
            return {"valid": False, "error": f"Tool '{tool_name}' not found"}

        # Simple validation - check required parameters
        required = tool.get("parameters", {}).get("required", [])
        missing = [param for param in required if param not in args]

        return {
            "valid": len(missing) == 0,
            "errors": [f"Missing required parameter: {param}" for param in missing],
        }

    def format_tool_for_display(
        self, tool: Dict[str, Any], format_type: str = "table"
    ) -> str:
        if format_type == "json":
            import json

            return json.dumps(tool, indent=2)
        else:
            return f"{tool['name']}: {tool['description']}"


@pytest.fixture
def mock_template_manager():
    """Mock TemplateManager instance."""
    return MockTemplateManager()


@pytest.fixture
def mock_deployment_manager():
    """Mock DeploymentManager instance."""
    return MockDeploymentManager()


@pytest.fixture
def mock_config_manager():
    """Mock ConfigManager instance."""
    return MockConfigManager()


@pytest.fixture
def mock_tool_manager():
    """Mock ToolManager instance."""
    return MockToolManager()


# Error injection fixtures for testing error scenarios
@pytest.fixture
def inject_file_not_found_error():
    """Inject FileNotFoundError for testing."""
    with patch("pathlib.Path.exists", return_value=False):
        with patch(
            "pathlib.Path.read_text", side_effect=FileNotFoundError("File not found")
        ):
            yield


@pytest.fixture
def inject_json_decode_error():
    """Inject JSON decode error for testing."""
    with patch("json.loads", side_effect=ValueError("Invalid JSON")):
        yield


@pytest.fixture
def inject_docker_connection_error():
    """Inject Docker connection error for testing."""
    from docker.errors import DockerException

    with patch(
        "docker.from_env",
        side_effect=DockerException("Cannot connect to Docker daemon"),
    ):
        yield


@pytest.fixture
def inject_kubernetes_connection_error():
    """Inject Kubernetes connection error for testing."""
    with patch(
        "kubernetes.client.CoreV1Api",
        side_effect=Exception("Cannot connect to Kubernetes cluster"),
    ):
        yield


# Performance testing fixtures
@pytest.fixture
def large_template_collection(tmp_path):
    """Create a large collection of templates for performance testing."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()

    # Create 100 test templates
    for i in range(100):
        template_dir = templates_dir / f"template_{i:03d}"
        template_dir.mkdir()

        template_json = template_dir / "template.json"
        template_json.write_text(f'{{"name": "template_{i:03d}", "version": "1.0.0"}}')

        readme = template_dir / "README.md"
        readme.write_text(f"# Template {i:03d}\nTest template number {i}")

    return templates_dir


# Integration test fixtures
@pytest.fixture(scope="session")
def integration_workspace(tmp_path_factory):
    """Create a workspace for integration testing."""
    workspace = tmp_path_factory.mktemp("integration_test")

    # Set up realistic workspace structure
    templates_dir = workspace / "templates"
    templates_dir.mkdir()

    deployments_dir = workspace / "deployments"
    deployments_dir.mkdir()

    config_dir = workspace / "config"
    config_dir.mkdir()

    return workspace
