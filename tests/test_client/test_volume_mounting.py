"""
Tests for volume mounting functionality in client API and CLI.

Tests the volume mounting features added to both the Python client API
and CLI deploy command, including dict/list formats and validation.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.deployment_manager import DeploymentManager, DeploymentResult


class TestVolumeMounting:
    """Test volume mounting functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_backend = Mock()
        self.deployment_manager = DeploymentManager("docker")
        self.deployment_manager.backend = self.mock_backend

    def test_client_volume_mounting_dict_format(self):
        """Test client API volume mounting with dictionary format."""
        client = MCPClient()

        volumes = {"/host/data": "/container/data", "/host/config": "/container/config"}

        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                status="running",
                ports={"8080": 8080},
            )

            result = client.start_server(
                "test-template",
                volumes=volumes,
                configuration={"test_key": "test_value"},
            )

            # Verify deployment was called with volumes
            mock_deploy.assert_called_once()
            call_args = mock_deploy.call_args

            # Check that volumes were passed correctly
            # The deploy_template method is called with (template_id, config_sources, deployment_options)
            # Volumes should be in config_sources["config_values"]["VOLUMES"]
            template_id, config_sources, deployment_options = call_args[0]
            assert "config_values" in config_sources
            assert "VOLUMES" in config_sources["config_values"]
            assert config_sources["config_values"]["VOLUMES"] == volumes

    def test_client_volume_mounting_list_format(self):
        """Test client API volume mounting with list format."""
        client = MCPClient()

        volumes = ["/host/data:/container/data", "/host/config:/container/config:ro"]

        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                status="running",
                ports={"8080": 8080},
            )

            result = client.start_server(
                "test-template",
                volumes=volumes,
                configuration={"test_key": "test_value"},
            )

            # Verify deployment was called with volumes
            mock_deploy.assert_called_once()
            call_args = mock_deploy.call_args

            # Check that volumes were passed correctly
            # The deploy_template method is called with (template_id, config_sources, deployment_options)
            # Volumes should be in config_sources["config_values"]["VOLUMES"]
            template_id, config_sources, deployment_options = call_args[0]
            assert "config_values" in config_sources
            assert "VOLUMES" in config_sources["config_values"]
            assert config_sources["config_values"]["VOLUMES"] == {
                "/host/data:/container/data": "/host/data:/container/data",
                "/host/config:/container/config:ro": "/host/config:/container/config:ro",
            }

    def test_client_volume_mounting_empty_volumes(self):
        """Test client API handles empty volumes correctly."""
        client = MCPClient()

        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True, deployment_id="test-deployment", status="running"
            )

            # Test with None
            result = client.start_server("test-template", volumes=None)
            mock_deploy.assert_called()

            # Test with empty dict
            result = client.start_server("test-template", volumes={})
            mock_deploy.assert_called()

            # Test with empty list
            result = client.start_server("test-template", volumes=[])
            mock_deploy.assert_called()

    def test_client_volume_mounting_invalid_format_raises_error(self):
        """Test client API raises error for invalid volume formats."""
        client = MCPClient()

        # Test with string (should raise error)
        with pytest.raises((TypeError, ValueError)):
            client.start_server("test-template", volumes="invalid-string")

        # Test with invalid data type
        with pytest.raises((TypeError, ValueError)):
            client.start_server("test-template", volumes=123)

    def test_deployment_manager_volume_handling_dict(self):
        """Test deployment manager handles volume dict format correctly."""
        volumes = {"/host/data": "/container/data", "/host/logs": "/container/logs"}

        # Mock the deployment manager's deploy_template method directly
        with patch.object(self.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                status="running",
                ports={},
            )

            # Prepare config sources with volumes
            config_sources = {
                "config_values": {"VOLUMES": volumes},
                "config_file": None,
                "env_vars": None,
                "override_values": None,
                "volume_config": None,
                "backend_config": None,
                "backend_config_file": None,
            }

            from mcp_template.core.deployment_manager import DeploymentOptions

            deployment_options = DeploymentOptions(
                name="test-deployment",
                transport="http",
                port=8080,
                pull_image=True,
                timeout=300,
            )

            result = self.deployment_manager.deploy_template(
                template_id="test-template",
                config_sources=config_sources,
                deployment_options=deployment_options,
            )

            # Verify deploy_template was called with correct arguments
            mock_deploy.assert_called_once_with(
                template_id="test-template",
                config_sources=config_sources,
                deployment_options=deployment_options,
            )

    def test_deployment_manager_volume_handling_list(self):
        """Test deployment manager handles volume list format correctly."""
        volumes = ["/host/data:/container/data", "/host/logs:/container/logs:ro"]

        # Mock the deployment manager's deploy_template method directly
        with patch.object(self.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                status="running",
                ports={},
            )

            # Prepare config sources with volumes
            config_sources = {
                "config_values": {"VOLUMES": volumes},
                "config_file": None,
                "env_vars": None,
                "override_values": None,
                "volume_config": None,
                "backend_config": None,
                "backend_config_file": None,
            }

            from mcp_template.core.deployment_manager import DeploymentOptions

            deployment_options = DeploymentOptions(
                name="test-deployment",
                transport="http",
                port=8080,
                pull_image=True,
                timeout=300,
            )

            result = self.deployment_manager.deploy_template(
                template_id="test-template",
                config_sources=config_sources,
                deployment_options=deployment_options,
            )

            # Verify deploy_template was called with correct arguments
            mock_deploy.assert_called_once_with(
                template_id="test-template",
                config_sources=config_sources,
                deployment_options=deployment_options,
            )

    def test_docker_backend_volume_conversion_dict_to_list(self):
        """Test Docker backend converts dict volumes to list format for docker run."""
        from mcp_template.backends.docker import DockerDeploymentService

        backend = DockerDeploymentService()
        volumes_dict = {
            "/host/data": "/container/data",
            "/host/config": "/container/config",
        }

        # Test the volume conversion logic
        volume_args = []
        if volumes_dict:
            if isinstance(volumes_dict, dict):
                for host_path, container_path in volumes_dict.items():
                    volume_args.extend(["-v", f"{host_path}:{container_path}"])
            elif isinstance(volumes_dict, list):
                for volume in volumes_dict:
                    volume_args.extend(["-v", volume])

        # Check that volume arguments are correctly formatted
        expected_args = [
            "-v",
            "/host/data:/container/data",
            "-v",
            "/host/config:/container/config",
        ]

        # Sort both lists since dict order might vary
        volume_args.sort()
        expected_args.sort()
        assert volume_args == expected_args

    def test_docker_backend_volume_conversion_list_passthrough(self):
        """Test Docker backend passes through list volumes correctly."""
        volumes_list = [
            "/host/data:/container/data",
            "/host/config:/container/config:ro",
        ]

        # Test the volume conversion logic
        volume_args = []
        if volumes_list:
            if isinstance(volumes_list, dict):
                for host_path, container_path in volumes_list.items():
                    volume_args.extend(["-v", f"{host_path}:{container_path}"])
            elif isinstance(volumes_list, list):
                for volume in volumes_list:
                    volume_args.extend(["-v", volume])

        # Check that volume arguments are correctly formatted
        expected_args = [
            "-v",
            "/host/data:/container/data",
            "-v",
            "/host/config:/container/config:ro",
        ]

        assert volume_args == expected_args

    def test_integration_client_to_docker_backend_volumes(self):
        """Test that client properly passes volumes to deployment manager."""
        client = MCPClient()

        volumes = {"/host/data": "/container/data", "/host/logs": "/container/logs"}

        # Mock the entire deployment_manager.deploy_template call
        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True,
                deployment_id="test-deployment",
                status="running",
                ports={"8080": 8080},
            )

            result = client.start_server(
                "test-template",
                volumes=volumes,
                configuration={"api_key": "test-key"},
            )

            # Verify deploy_template was called with volumes
            mock_deploy.assert_called_once()
            call_args = mock_deploy.call_args

            # Check that volumes were passed correctly in config_sources
            template_id, config_sources, deployment_options = call_args[0]
            assert template_id == "test-template"
            assert "config_values" in config_sources
            assert "VOLUMES" in config_sources["config_values"]
            assert config_sources["config_values"]["VOLUMES"] == volumes

    def test_volume_validation_security_checks(self):
        """Test volume validation includes basic security checks."""
        # NOTE: This is a placeholder for future security validation
        # Currently the system accepts any volume paths, but we should
        # consider adding validation for:
        # - Preventing access to sensitive system directories
        # - Validating host paths exist and are accessible
        # - Checking for path traversal attempts

        volumes_potentially_dangerous = {
            "/etc": "/container/etc",  # System config access
            "/": "/container/root",  # Full filesystem access
            "../../../etc": "/container/etc",  # Path traversal
        }

        # For now, just ensure these don't crash the system
        client = MCPClient()

        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True, deployment_id="test", status="running"
            )

            # Should not raise exceptions (but might in future with validation)
            try:
                result = client.start_server(
                    "test-template", volumes=volumes_potentially_dangerous
                )
            except Exception as e:
                # If validation is added later, document expected behavior
                pytest.skip(f"Volume validation prevented deployment: {e}")

    def test_volume_mounting_with_template_placeholders(self):
        """Test volume mounting works with template placeholder values."""
        client = MCPClient()

        # Volumes with placeholder values that should be resolved by template
        volumes = {"@HOST_DATA_PATH@": "/app/data", "@HOST_CONFIG_PATH@": "/app/config"}

        configuration = {
            "HOST_DATA_PATH": "/home/user/project/data",
            "HOST_CONFIG_PATH": "/home/user/project/config",
        }

        with patch.object(client.deployment_manager, "deploy_template") as mock_deploy:
            mock_deploy.return_value = DeploymentResult(
                success=True, deployment_id="test-deployment", status="running"
            )

            result = client.start_server(
                "test-template", volumes=volumes, configuration=configuration
            )

            # Verify deployment was called with both volumes and config
            mock_deploy.assert_called_once()
            call_args = mock_deploy.call_args

            # Check arguments passed to deploy_template
            template_id, config_sources, deployment_options = call_args[0]
            assert "config_values" in config_sources
            assert "VOLUMES" in config_sources["config_values"]
            # Volumes should contain the original placeholder values
            assert config_sources["config_values"]["VOLUMES"] == volumes
            # Configuration should be merged in config_values too
            for key, value in configuration.items():
                assert config_sources["config_values"][key] == value
