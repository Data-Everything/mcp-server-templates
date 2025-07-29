"""
Test docker backend functionality.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.backends.docker import DockerDeploymentService


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
        mock_response = """{"Names": "mcp-test-123", "State": "running", "CreatedAt": "2024-01-01", "Image": "test:latest", "Labels": "template=test,managed-by=mcp-template"}"""
        mock_run_command.return_value = Mock(stdout=mock_response)

        service = DockerDeploymentService()
        deployments = service.list_deployments()

        assert len(deployments) == 1
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
        """Test getting deployment status."""
        mock_response = """[{"Name": "/test-container", "State": {"Status": "running", "Running": true}, "Created": "2024-01-01", "Config": {"Image": "test:latest"}}]"""
        mock_run_command.return_value = Mock(stdout=mock_response)

        service = DockerDeploymentService()
        status = service.get_deployment_status("test-container")

        assert status["status"] == "running"
        assert status["name"] == "test-container"
        assert "created" in status

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
            assert "MCP_PARAM1=value1" in env_vars
            assert "MCP_PARAM2=value2" in env_vars
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
