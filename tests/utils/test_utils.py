# Test utilities for MCP Server Templates


import contextlib
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest


class TestBackendUnavailable(Exception):
    pass


class TemplateTestError(Exception):
    """Exception raised during template testing."""

    pass


# Detect container CLI (docker or nerdctl)
def detect_container_cli() -> str:
    import shutil

    for cli in ["docker", "nerdctl"]:
        if shutil.which(cli):
            return cli
    return None


CONTAINER_CLI = detect_container_cli()
if not CONTAINER_CLI:
    print(
        "WARNING: Neither 'docker' nor 'nerdctl' found in PATH. Integration tests will be skipped."
    )


def find_free_port() -> int:
    """Find a free port for testing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


class TemplateTestContainer:
    """Context manager for testing template containers."""

    def __init__(self, template_name: str, config: Dict[str, Any], port: int = None):
        self.template_name = template_name
        self.config = config
        self.port = port if port is not None else find_free_port()
        self.container_id: Optional[str] = None
        self.image_name = f"mcp-{template_name}-test"
        if not CONTAINER_CLI:
            raise TestBackendUnavailable("No container CLI available")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def start(self):
        try:
            self._build_container()
            self._start_container()
            self._wait_for_healthy()
        except Exception as e:
            self.cleanup()
            raise TemplateTestError(f"Failed to start container: {e}")

    def _build_container(self):
        template_dir = Path(__file__).parent.parent / "templates" / self.template_name
        if not template_dir.exists():
            raise TemplateTestError(f"Template directory not found: {template_dir}")
        cmd = [CONTAINER_CLI, "build", "-t", self.image_name, str(template_dir)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise TemplateTestError(f"Build failed: {result.stderr}")

    def _start_container(self):
        cmd = [
            CONTAINER_CLI,
            "run",
            "-d",
            "--name",
            f"{self.image_name}-{int(time.time())}",
        ]
        for key, value in self.config.items():
            if isinstance(value, list):
                value = ",".join(str(v) for v in value)
            cmd.extend(["--env", f"{key}={value}"])
        cmd.append(self.image_name)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise TemplateTestError(f"Failed to start container: {result.stderr}")
        self.container_id = result.stdout.strip()

    def _wait_for_healthy(self, timeout: int = 60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    [
                        CONTAINER_CLI,
                        "inspect",
                        "--format",
                        "{{.State.Status}} {{.State.ExitCode}}",
                        self.container_id,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                status_info = result.stdout.strip().split()
                status = status_info[0]
                exit_code = int(status_info[1]) if len(status_info) > 1 else 0
                if status == "running":
                    time.sleep(2)
                    return
                elif status == "exited" and exit_code == 0:
                    logs = self.get_logs()
                    if (
                        "Starting MCP server" in logs
                        and "with transport 'stdio'" in logs
                    ):
                        return
                    else:
                        raise TemplateTestError(
                            f"Container exited without proper MCP initialization. Logs: {logs}"
                        )
                elif status in ["exited", "dead"] and exit_code != 0:
                    logs = self.get_logs()
                    raise TemplateTestError(
                        f"Container failed with exit code {exit_code}. Logs: {logs}"
                    )
            except subprocess.CalledProcessError as e:
                raise TemplateTestError(f"Failed to check container status: {e}")
            time.sleep(2)
        raise TemplateTestError(
            f"Container did not become healthy within {timeout} seconds"
        )

    def cleanup(self):
        if self.container_id:
            subprocess.run(
                [CONTAINER_CLI, "rm", "-f", self.container_id], capture_output=True
            )
        subprocess.run(
            [CONTAINER_CLI, "rmi", "-f", self.image_name], capture_output=True
        )

    def get_logs(self) -> str:
        if not self.container_id:
            return ""
        result = subprocess.run(
            [CONTAINER_CLI, "logs", self.container_id], capture_output=True, text=True
        )
        return result.stdout + result.stderr

    def exec_command(self, command: str) -> str:
        if not self.container_id:
            raise TemplateTestError("Container not running")
        result = subprocess.run(
            [CONTAINER_CLI, "exec", self.container_id, "sh", "-c", command],
            capture_output=True,
            text=True,
        )
        return result.stdout


@contextlib.contextmanager
def build_and_run_template(
    template_name: str, config: Optional[Dict[str, Any]] = None, port: int = None
) -> Generator[TemplateTestContainer, None, None]:
    """Context manager for building and running a template for testing."""
    if not CONTAINER_CLI:
        pytest.skip(
            "No container CLI (docker/nerdctl) available, skipping integration test."
        )
    if config is None:
        config = get_default_test_config(template_name)
    if port is None:
        port = find_free_port()
    container = TemplateTestContainer(template_name, config, port)
    with container:
        yield container


def get_default_test_config(template_name: str) -> Dict[str, Any]:
    """Get default test configuration for a template."""

    # Load template.json to get configuration schema
    template_dir = Path(__file__).parent.parent / "templates" / template_name
    template_json_path = template_dir / "template.json"

    if not template_json_path.exists():
        raise TemplateTestError(f"template.json not found for {template_name}")

    with open(template_json_path) as f:
        template_data = json.load(f)

    config_schema = template_data.get("config_schema", {})
    properties = config_schema.get("properties", {})

    # Build default config from schema
    config = {}

    for prop_name, prop_def in properties.items():
        env_mapping = prop_def.get("env_mapping")
        if not env_mapping:
            continue

        # Use default value if available
        if "default" in prop_def:
            config[env_mapping] = prop_def["default"]
        # Use test values for required fields
        elif prop_name in config_schema.get("required", []):
            if prop_def.get("type") == "string":
                if prop_def.get("secret"):
                    config[env_mapping] = "test-secret-value"
                else:
                    config[env_mapping] = f"test-{prop_name}"
            elif prop_def.get("type") == "integer":
                config[env_mapping] = 42
            elif prop_def.get("type") == "boolean":
                config[env_mapping] = "true"
            elif prop_def.get("type") == "array":
                config[env_mapping] = ["test-item1", "test-item2"]

    return config


def validate_template_structure(template_name: str) -> bool:
    """Validate that a template has the required structure."""

    template_dir = Path(__file__).parent.parent / "templates" / template_name

    required_files = ["template.json", "Dockerfile", "README.md"]

    for file_name in required_files:
        file_path = template_dir / file_name
        if not file_path.exists():
            raise TemplateTestError(f"Required file missing: {file_name}")

    # Validate template.json structure
    template_json_path = template_dir / "template.json"
    with open(template_json_path) as f:
        template_data = json.load(f)

    required_fields = ["name", "description", "docker_image", "config_schema"]

    for field in required_fields:
        if field not in template_data:
            raise TemplateTestError(f"Required field missing in template.json: {field}")

    return True


def run_template_tests(template_name: str) -> Dict[str, Any]:
    """Run comprehensive tests for a template."""

    results = {
        "template_name": template_name,
        "structure_valid": False,
        "build_successful": False,
        "container_starts": False,
        "health_check_passes": False,
        "config_validation": {},
        "errors": [],
    }

    try:
        # Validate structure
        validate_template_structure(template_name)
        results["structure_valid"] = True

        # Test with default config
        with build_and_run_template(template_name) as container:
            results["build_successful"] = True
            results["container_starts"] = True

            # For MCP servers, we check if the container initialized properly
            # STDIO-based servers may exit with code 0 after initialization - this is OK
            try:
                result = subprocess.run(
                    [
                        "docker",
                        "inspect",
                        "--format",
                        "{{.State.Status}} {{.State.ExitCode}}",
                        container.container_id,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                status_info = result.stdout.strip().split()
                status = status_info[0]
                exit_code = int(status_info[1]) if len(status_info) > 1 else 0

                if status == "running":
                    results["health_check_passes"] = True
                elif status == "exited" and exit_code == 0:
                    # For STDIO servers, this might be expected - check logs for proper initialization
                    logs = container.get_logs()
                    if (
                        "Starting MCP server" in logs
                        and "with transport 'stdio'" in logs
                    ):
                        results["health_check_passes"] = True
                    else:
                        results["errors"].append(
                            "Container exited without proper MCP initialization"
                        )
                else:
                    results["errors"].append(
                        f"Container failed with status: {status}, exit code: {exit_code}"
                    )
            except subprocess.CalledProcessError as e:
                results["errors"].append(f"Failed to check container status: {e}")

            # Test various configuration scenarios
            results["config_validation"] = test_configuration_scenarios(
                template_name, container
            )

    except Exception as e:
        results["errors"].append(str(e))

    return results


@pytest.mark.skip(reason="Utility function, not a test.")
def test_configuration_scenarios(
    template_name: str, container: TemplateTestContainer
) -> Dict[str, Any]:
    """Test various configuration scenarios."""
    scenarios = {
        "default_config": True,  # Already tested by getting here
        "empty_config": False,
        "invalid_config": False,
        "config_file": False,
    }
    # Additional test scenarios would go here
    # This is a placeholder for more comprehensive testing
    return scenarios


class MockMCPClient:
    """Mock MCP client for testing MCP protocol interactions."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    async def list_resources(self):
        """Test listing resources."""
        # Implementation would go here
        pass

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Test calling a tool."""
        # Implementation would go here
        pass
