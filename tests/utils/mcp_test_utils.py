"""
MCP Test Utilities for template testing.

Provides common testing utilities for MCP server templates.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from mcp_template.utils import TEMPLATES_DIR


class MCPTestClient:
    """Test client for MCP servers."""

    def __init__(self, server_script: Path):
        self.server_script = server_script
        self.process = None
        self.session = None

    async def start(self):
        """Start the MCP server process."""
        # TODO: Implement MCP server startup
        pass

    async def stop(self):
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the server."""
        # TODO: Implement tool listing
        return []

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the server."""
        # TODO: Implement tool calling
        return {"result": "mock_result"}


class TemplateTestBase:
    """Base class for template tests."""

    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.config = self._load_template_config()

    def _load_template_config(self) -> Dict[str, Any]:
        """Load template configuration."""
        config_file = self.template_dir / "template.json"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_expected_tools(self) -> List[str]:
        """Get list of expected tools from template config."""
        capabilities = self.config.get("capabilities", [])
        return [cap.get("name", "").lower().replace(" ", "_") for cap in capabilities]

    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema from template config."""
        return self.config.get("config_schema", {})

    def create_mock_env(self) -> Dict[str, str]:
        """Create mock environment variables for testing."""
        env_vars = {}
        schema = self.get_config_schema()
        properties = schema.get("properties", {})

        for param_name, param_config in properties.items():
            env_name = param_config.get("env_mapping", param_name.upper())
            default_val = param_config.get("default", "test_value")
            env_vars[env_name] = str(default_val)

        return env_vars


def run_docker_command(
    args: List[str], cwd: Optional[Path] = None
) -> subprocess.CompletedProcess:
    """Run a docker command and return the result."""
    cmd = ["docker"] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=False)


def build_template_image(template_dir: Path, tag: str) -> bool:
    """Build a Docker image for a template."""
    result = run_docker_command(["build", "-t", tag, "."], cwd=template_dir)
    return result.returncode == 0


def run_template_container(
    image_tag: str, env_vars: Optional[Dict[str, str]] = None
) -> str:
    """Run a template container and return container ID."""
    args = ["run", "-d"]

    if env_vars:
        for key, value in env_vars.items():
            args.extend(["-e", f"{key}={value}"])

    args.append(image_tag)

    result = run_docker_command(args)
    if result.returncode == 0:
        return result.stdout.strip()
    return ""


def stop_container(container_id: str) -> bool:
    """Stop and remove a container."""
    stop_result = run_docker_command(["stop", container_id])
    rm_result = run_docker_command(["rm", container_id])
    return stop_result.returncode == 0 and rm_result.returncode == 0


def get_container_logs(container_id: str) -> str:
    """Get logs from a container."""
    result = run_docker_command(["logs", container_id])
    return result.stdout if result.returncode == 0 else ""


@pytest.fixture
def template_base():
    """Fixture providing TemplateTestBase for current template."""
    # This will be overridden in specific template conftest.py files
    return None


@pytest.fixture
def docker_client():
    """Fixture providing docker utilities."""
    return {
        "build": build_template_image,
        "run": run_template_container,
        "stop": stop_container,
        "logs": get_container_logs,
    }


class TemplateTestContainer:
    """Context manager for running template containers in tests."""

    def __init__(self, template_name: str, config: Dict[str, Any]):
        self.template_name = template_name
        self.config = config
        self.container_id = None

    def __enter__(self):
        # Build template image
        template_dir = (
            Path(__file__).parent.parent.parent / "templates" / self.template_name
        )
        tag = f"mcp-test-{self.template_name}"

        if not build_template_image(template_dir, tag):
            raise RuntimeError(
                f"Failed to build template image for {self.template_name}"
            )

        # Create config file
        config_data = json.dumps(self.config, indent=2)
        env_vars = {"MCP_CONFIG": config_data}

        # Run container
        self.container_id = run_template_container(tag, env_vars)
        if not self.container_id:
            raise RuntimeError(f"Failed to start container for {self.template_name}")

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.container_id:
            stop_container(self.container_id)

    def get_logs(self) -> str:
        """Get container logs."""
        if self.container_id:
            return get_container_logs(self.container_id)
        return ""


def build_and_run_template(template_name: str, config: Dict[str, Any]):
    """Context manager for building and running template containers.

    This is an alias for TemplateTestContainer for backward compatibility.
    """
    return TemplateTestContainer(template_name, config)


def get_template_list() -> List[str]:
    """Get list of available templates using TemplateDiscovery."""
    # Import here to avoid circular imports
    from mcp_template.template.discovery import TemplateDiscovery

    discovery = TemplateDiscovery()
    templates = discovery.discover_templates()
    return list(templates.keys())


def validate_template_structure(template_name: str) -> bool:
    """Validate that a template has the required structure."""
    template_dir = Path(__file__).parent.parent.parent / "templates" / template_name

    # Check required files
    required_files = ["template.json", "README.md", "docs/index.md"]
    for file in required_files:
        if not (template_dir / file).exists():
            return False

    # Check template.json structure
    try:
        template_json = json.loads((template_dir / "template.json").read_text())
        required_keys = ["name", "version", "description"]
        for key in required_keys:
            if key not in template_json:
                return False
    except (json.JSONDecodeError, FileNotFoundError):
        return False

    return True


def run_template_tests(template_name: str) -> subprocess.CompletedProcess:
    """Run pytest tests for a specific template."""
    # Tests are now located in templates/{template_name}/tests/
    test_dir = TEMPLATES_DIR / template_name / "tests"
    if not test_dir.exists():
        raise ValueError(f"No tests found for template: {template_name}")

    # Run without coverage requirements for template tests
    # The `--no-cov` flag is used here because template tests are designed to validate
    # the functionality of user-provided templates, not the core application code.
    # Coverage metrics for these tests are not meaningful as they do not reflect
    # the coverage of the main application logic.
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(test_dir), "-v", "--tb=short", "--no-cov"],
        capture_output=True,
        text=True,
    )
