"""
Test docker backend functionality.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService


@pytest.mark.unit
@pytest.mark.docker
class TestDockerDeploymentService:
    """Test Docker deployment service."""

    def test_init(self):
        """Test Docker service initialization."""
        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()
            assert service is not None

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_deploy_template_success(self, mock_run_command, mock_ensure_docker):
        """Test successful template deployment."""
        # Setup mocks
        mock_run_command.side_effect = [
            Mock(stdout="pulled", stderr=""),  # docker pull
            Mock(stdout="container123", stderr=""),  # docker run
        ]

        service = DockerDeploymentService()
        template_data = {
            "image": "test-image:latest",
            "ports": {"8080": 8080},
            "env_vars": {"TEST_VAR": "test_value"},
        }
        config = {"param1": "value1"}

        result = service.deploy_template("test", config, template_data)

        assert result["template_id"] == "test"
        assert result["status"] == "deployed"
        assert "deployment_name" in result
        assert "container_id" in result

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_deploy_template_with_pull(self, mock_run_command, mock_ensure_docker):
        """Test deployment with image pulling."""
        mock_run_command.side_effect = [
            Mock(stdout="pulled", stderr=""),  # docker pull
            Mock(stdout="container123", stderr=""),  # docker run
        ]

        service = DockerDeploymentService()
        template_data = {"image": "test-image:latest"}

        service.deploy_template("test", {}, template_data, pull_image=True)

        # Verify pull command was called
        assert mock_run_command.call_count == 2
        pull_call = mock_run_command.call_args_list[0]
        assert "pull" in pull_call[0][0]

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_deploy_template_docker_error(self, mock_run_command, mock_ensure_docker):
        """Test deployment failure handling."""
        mock_run_command.side_effect = Exception("Docker error")

        service = DockerDeploymentService()
        template_data = {"image": "test-image:latest"}

        with pytest.raises(Exception):
            service.deploy_template("test", {}, template_data)

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_list_deployments(self, mock_run_command, mock_ensure_docker):
        """Test listing deployments."""
        mock_response = """{"ID": "abc123def456", "Names": "mcp-test-123", "State": "running", "CreatedAt": "2024-01-01", "RunningFor": "2 hours ago", "Image": "test:latest", "Labels": "template=test,managed-by=mcp-template", "Ports": "0.0.0.0:8080->8080/tcp"}"""
        mock_run_command.return_value = Mock(stdout=mock_response)

        service = DockerDeploymentService()
        deployments = service.list_deployments()

        assert len(deployments) == 1
        assert deployments[0]["id"] == "abc123def456"
        assert deployments[0]["name"] == "mcp-test-123"
        assert deployments[0]["template"] == "test"

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_delete_deployment_success(self, mock_run_command, mock_ensure_docker):
        """Test successful deployment deletion."""
        mock_run_command.return_value = Mock(stdout="", stderr="")

        service = DockerDeploymentService()
        result = service.delete_deployment("test-container")

        assert result is True
        assert mock_run_command.called

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_delete_deployment_not_found(self, mock_run_command, mock_ensure_docker):
        """Test deletion of non-existent deployment."""
        from subprocess import CalledProcessError

        mock_run_command.side_effect = CalledProcessError(
            1, "docker", "No such container"
        )

        service = DockerDeploymentService()
        result = service.delete_deployment("nonexistent")

        assert result is False

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_get_deployment_status(self, mock_run_command, mock_ensure_docker):
        """Test getting deployment status with logs via unified get_deployment_info method."""
        mock_response = """[{"Name": "/test-container", "State": {"Status": "running", "Running": true}, "Created": "2024-01-01", "Config": {"Image": "test:latest", "Labels": {"template": "test"}}}]"""
        mock_run_command.return_value = Mock(stdout=mock_response)

        service = DockerDeploymentService()
        status = service.get_deployment_info("test-container", include_logs=True)

        assert status["status"] == "running"
        assert status["name"] == "test-container"
        assert status["running"] is True
        assert "created" in status
        assert "logs" in status  # Should include logs when include_logs=True

    def test_prepare_environment_variables(self):
        """Test environment variable preparation."""
        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()
            config = {"param1": "value1", "param2": "value2"}
            template_data = {"env_vars": {"TEMPLATE_VAR": "template_value"}}

            env_vars = service._prepare_environment_variables(config, template_data)

            assert "--env" in env_vars
            assert "param1=value1" in env_vars
            assert "param2=value2" in env_vars
            assert "TEMPLATE_VAR=template_value" in env_vars

    def test_prepare_port_mappings(self):
        """Test port mapping preparation."""
        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()
            template_data = {"ports": {"8080": 8080, "9000": 9001}}

            port_mappings = service._prepare_port_mappings(template_data)

            assert "-p" in port_mappings
            assert "8080:8080" in port_mappings
            assert "9000:9001" in port_mappings

    def test_prepare_volume_mounts(self):
        """Test volume mount preparation."""
        with patch(
            "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
        ):
            service = DockerDeploymentService()
            template_data = {"volumes": {"/host/path": "/container/path"}}

            with patch("os.makedirs"):
                volumes = service._prepare_volume_mounts(template_data)

                assert "--volume" in volumes
                assert "/host/path:/container/path" in volumes

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_get_deployment_logs_success(self, mock_run_command, mock_ensure_docker):
        """Test successful retrieval of deployment logs."""
        # Setup mock for docker logs command
        mock_log_output = "Log line 1\nLog line 2\nLog line 3"
        mock_run_command.return_value = Mock(
            stdout=mock_log_output, stderr="", returncode=0
        )

        service = DockerDeploymentService()

        # Test basic logs retrieval (uses default 100 lines)
        result = service.get_deployment_logs("container123")

        assert result["success"] is True
        assert result["logs"] == mock_log_output

        # Verify docker logs command was called correctly with default --tail 100
        mock_run_command.assert_called_once_with(
            ["docker", "logs", "--tail", "100", "container123"], capture_output=True
        )

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_get_deployment_logs_with_parameters(
        self, mock_run_command, mock_ensure_docker
    ):
        """Test logs retrieval with lines, since, and until parameters."""
        mock_log_output = "Recent log line"
        mock_run_command.return_value = Mock(
            stdout=mock_log_output, stderr="", returncode=0
        )

        service = DockerDeploymentService()

        # Test with lines parameter
        result = service.get_deployment_logs(
            "container123", lines=50, since="2023-01-01", until="2023-12-31"
        )

        assert result["success"] is True
        assert result["logs"] == mock_log_output

        # Verify docker logs command was called with parameters
        mock_run_command.assert_called_once_with(
            [
                "docker",
                "logs",
                "--tail",
                "50",
                "--since",
                "2023-01-01",
                "--until",
                "2023-12-31",
                "container123",
            ],
            capture_output=True,
        )

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_get_deployment_logs_failure(self, mock_run_command, mock_ensure_docker):
        """Test logs retrieval failure handling."""
        # Setup mock for failed docker logs command
        mock_run_command.return_value = Mock(
            stdout="", stderr="Error: No such container", returncode=1
        )

        service = DockerDeploymentService()

        # Test logs retrieval failure
        result = service.get_deployment_logs("nonexistent-container")

        assert result["success"] is False
        assert result["error"] == "Error: No such container"

        # Verify docker logs command was called
        mock_run_command.assert_called_once_with(
            ["docker", "logs", "--tail", "100", "nonexistent-container"],
            capture_output=True,
        )

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    def test_get_deployment_logs_default_lines(
        self, mock_run_command, mock_ensure_docker
    ):
        """Test logs retrieval uses default lines when only lines specified."""
        mock_log_output = "Default lines log"
        mock_run_command.return_value = Mock(
            stdout=mock_log_output, stderr="", returncode=0
        )

        service = DockerDeploymentService()

        # Test with only lines parameter
        result = service.get_deployment_logs("container123", lines=100)

        assert result["success"] is True
        assert result["logs"] == mock_log_output

        # Verify docker logs command was called with lines only
        mock_run_command.assert_called_once_with(
            ["docker", "logs", "--tail", "100", "container123"], capture_output=True
        )
