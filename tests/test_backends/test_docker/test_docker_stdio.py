"""
Tests for Docker backend stdio command functionality.
"""

import json
import subprocess
from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService


@pytest.fixture
def docker_service():
    """Create DockerDeploymentService instance with mocked Docker availability."""
    with patch.object(DockerDeploymentService, "_ensure_docker_available"):
        return DockerDeploymentService()


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_success(mock_run, docker_service):
    """Test successful stdio command execution."""
    template_id = "github"
    config = {"port": 8080}
    template_data = {
        "image": "test/github:latest",
        "command": ["mcp-server-github"],
        "env_vars": {},
    }
    json_input = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "search_repositories", "arguments": {"query": "python"}},
        }
    )

    expected_stdout = json.dumps({"result": "success"})

    # Mock successful Docker pull and execution
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(returncode=0, stdout=expected_stdout, stderr=""),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout
    assert result["template_id"] == template_id

    # Verify Docker commands were called
    assert mock_run.call_count == 2

    # Verify Docker pull was called
    pull_call = mock_run.call_args_list[0]
    assert "docker" in pull_call[0][0]
    assert "pull" in pull_call[0][0]
    assert "test/github:latest" in pull_call[0][0]

    # Verify Docker run was called with proper MCP sequence
    run_call = mock_run.call_args_list[1]
    assert "/bin/bash" in run_call[0][0]
    assert "-c" in run_call[0][0]

    # Verify the bash command contains proper MCP handshake
    bash_command = run_call[0][0][2]
    assert "docker run -i --rm" in bash_command
    assert "initialize" in bash_command
    assert "notifications/initialized" in bash_command


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_docker_failure(mock_run, docker_service):
    """Test stdio command execution with Docker failure."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    # Mock Docker pull success, run failure
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull success
        subprocess.CalledProcessError(1, "docker run"),  # Docker run failure
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "failed"
    assert "docker run" in str(result["error"])


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_no_pull(mock_run, docker_service):
    """Test stdio command execution without image pull."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    expected_stdout = '{"result": "no pull success"}'

    # Mock only Docker run (no pull)
    mock_run.return_value = Mock(returncode=0, stdout=expected_stdout, stderr="")

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input, pull_image=False
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout

    # Verify only one call (no pull)
    assert mock_run.call_count == 1


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_pull_failure(mock_run, docker_service):
    """Test stdio command execution with Docker pull failure."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    # Mock Docker pull failure
    mock_run.side_effect = subprocess.CalledProcessError(1, "docker pull")

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "failed"
    assert "docker pull" in str(result["error"])


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_with_environment_vars(mock_run, docker_service):
    """Test stdio command execution with environment variables."""
    template_id = "github"
    config = {"GITHUB_TOKEN": "test_token", "API_KEY": "secret"}
    template_data = {
        "image": "test/github:latest",
        "command": ["mcp-server-github"],
        "env_vars": {"LOG_LEVEL": "debug"},
    }
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    expected_stdout = '{"result": "env success"}'

    # Mock successful execution
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(returncode=0, stdout=expected_stdout, stderr=""),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout

    # Verify environment variables were passed to Docker
    run_call = mock_run.call_args_list[1]
    bash_command = run_call[0][0][2]
    assert "--env GITHUB_TOKEN=test_token" in bash_command
    assert "--env API_KEY=secret" in bash_command
    assert "--env LOG_LEVEL=debug" in bash_command


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_with_custom_command(mock_run, docker_service):
    """Test stdio command execution with custom command."""
    template_id = "custom"
    config = {}
    template_data = {
        "image": "test/custom:latest",
        "command": ["python", "custom_server.py", "--port", "8080"],
    }
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    expected_stdout = '{"result": "custom success"}'

    # Mock successful execution
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(returncode=0, stdout=expected_stdout, stderr=""),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout

    # Verify custom command was used
    run_call = mock_run.call_args_list[1]
    bash_command = run_call[0][0][2]
    assert "python custom_server.py --port 8080" in bash_command


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_json_validation(mock_run, docker_service):
    """Test stdio command execution with various JSON inputs."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}

    # Test valid JSON
    valid_json = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "test"})

    expected_stdout = '{"result": "json success"}'
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(returncode=0, stdout=expected_stdout, stderr=""),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, valid_json
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout


@pytest.mark.docker
@pytest.mark.unit
@patch("subprocess.run")
def test_run_stdio_command_timeout_handling(mock_run, docker_service):
    """Test stdio command execution with timeout."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    # Mock timeout exception
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        subprocess.TimeoutExpired(["docker", "run"], 30),  # Docker run timeout
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "timeout"
    assert (
        "timeout" in result["error"].lower()
        or "expired" in result["error"].lower()
        or "timed out" in result["error"].lower()
    )


@pytest.mark.integration
@patch("subprocess.run")
def test_run_stdio_command_mcp_sequence_validation(mock_run, docker_service):
    """Test that the MCP handshake sequence is properly constructed."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "test_tool", "arguments": {}},
        }
    )

    # Mock successful execution
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(returncode=0, stdout='{"result": "mcp success"}', stderr=""),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "completed"

    # Verify the MCP sequence is correct
    run_call = mock_run.call_args_list[1]
    bash_command = run_call[0][0][2]

    # Check for proper MCP handshake sequence
    assert "initialize" in bash_command
    assert "notifications/initialized" in bash_command
    assert "tools/call" in bash_command

    # Verify the JSON input is properly escaped in the command
    assert '"id": 3' in bash_command or '"id":3' in bash_command


@pytest.mark.integration
@patch("subprocess.run")
def test_run_stdio_command_stderr_capture(mock_run, docker_service):
    """Test that stderr is properly captured and returned."""
    template_id = "github"
    config = {}
    template_data = {"image": "test/github:latest", "command": ["mcp-server-github"]}
    json_input = '{"jsonrpc": "2.0", "method": "test"}'

    expected_stdout = '{"result": "success"}'
    expected_stderr = "Warning: something happened"

    # Mock execution with stderr
    mock_run.side_effect = [
        Mock(returncode=0, stdout="", stderr=""),  # Docker pull
        Mock(
            returncode=0, stdout=expected_stdout, stderr=expected_stderr
        ),  # Docker run
    ]

    result = docker_service.run_stdio_command(
        template_id, config, template_data, json_input
    )

    assert result["status"] == "completed"
    assert result["stdout"] == expected_stdout
    assert result["stderr"] == expected_stderr


@pytest.mark.integration
def test_docker_service_initialization(docker_service):
    """Test DockerDeploymentService initialization."""
    assert docker_service is not None
    assert hasattr(docker_service, "run_stdio_command")
