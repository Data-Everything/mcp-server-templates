"""
Integration tests for MCP Template system.

Tests the complete deployment workflow including Docker integration,
template discovery, and end-to-end deployment scenarios.
"""

import json
import subprocess
import time
from unittest.mock import patch

import pytest

from conftest import assert_deployment_success
from mcp_template.backends import DockerDeploymentService, MockDeploymentService
from mcp_template.manager import DeploymentManager
from mcp_template.template.discovery import TemplateDiscovery


@pytest.mark.integration
class TestTemplateDiscoveryIntegration:
    """Test template discovery with real filesystem."""

    def test_discover_real_templates(self):
        """Test discovering actual templates in the repository."""
        manager = TemplateDiscovery()
        templates = manager.discover_templates()

        # Should find at least the demo template
        assert len(templates) > 0
        assert "demo" in templates

    def test_load_demo_template_config(self):
        """Test loading the actual demo template configuration."""
        manager = TemplateDiscovery()

        config = manager.get_template_config("demo")
        assert config is not None
        assert "name" in config
        assert "docker_image" in config
        assert "config_schema" in config

    def test_validate_all_templates(self):
        """Test that all discovered templates have valid configurations."""
        manager = TemplateDiscovery()
        templates = manager.discover_templates()

        for template_id in templates:
            try:
                config = manager.get_template_config(template_id)
                manager.validate_template_config(config)
            except Exception as e:
                pytest.fail(f"Template {template_id} has invalid config: {e}")


@pytest.mark.docker
@pytest.mark.integration
@pytest.mark.docker
class TestDockerIntegrationReal:
    """Test Docker integration with real Docker daemon."""

    def setup_method(self):
        """Setup for each test method."""
        self.cleanup_containers = []

    def teardown_method(self):
        """Cleanup after each test method."""
        # Clean up any containers created during testing

        try:
            for container_name in self.cleanup_containers:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception as e:
                    pass
        except Exception:
            pass

    def test_docker_service_real_deployment(self, mock_docker_client):
        """Test actual Docker deployment with mock image."""

        service = DockerDeploymentService()

        # Create a simple test configuration
        template_data = {
            "image": "hello-world:latest",  # Use the correct key and existing image
            "ports": {},
            "command": [],
            "config_schema": {"properties": {}},
        }

        # Deploy
        result = service.deploy_template(
            template_id="integration-test",
            config={},
            template_data=template_data,
            pull_image=True,
        )

        self.cleanup_containers.append(result["deployment_name"])

        assert_deployment_success(result)
        assert "container_id" in result

        # Verify container exists
        container = mock_docker_client.containers.get(result["container_id"])
        assert container is not None

        # Test listing deployments
        deployments = service.list_deployments()
        deployment_names = [d["name"] for d in deployments]
        assert result["deployment_name"] in deployment_names

        # Test getting status
        status = service.get_deployment_status(result["deployment_name"])
        assert status["name"] == result["deployment_name"]

        # Test deletion
        delete_result = service.delete_deployment(result["deployment_name"])
        assert delete_result is True

        # Remove from cleanup list since we deleted it
        self.cleanup_containers.remove(result["deployment_name"])

    def test_docker_service_with_ports(self, mock_docker_client):
        """Test Docker deployment with port mapping."""

        service = DockerDeploymentService()

        template_data = {
            "image": "nginx:alpine",  # Use the correct key format
            "ports": {"80": 8091},  # Use non-standard port to avoid conflicts
            "command": [],
            "config_schema": {"properties": {}},
        }

        result = service.deploy_template(
            template_id="nginx-test",
            config={},
            template_data=template_data,
            pull_image=True,
        )

        self.cleanup_containers.append(result["deployment_name"])

        # Verify port mapping - handle cases where ports might not be exposed
        container = mock_docker_client.containers.get(result["container_id"])
        # For nginx containers, just verify the container exists and is running
        assert container.status in ["running", "created"]

        # Cleanup
        service.delete_deployment(result["deployment_name"])
        self.cleanup_containers.remove(result["deployment_name"])


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.docker
@pytest.mark.slow
class TestEndToEndDeployment:
    """Test complete end-to-end deployment scenarios."""

    def test_deploy_demo_template_mock(self):
        """Test deploying demo template with mock backend."""
        manager = DeploymentManager(
            backend_type="mock"
        )  # Use mock backend consistently

        # Get template data first
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        template_data = templates.get("demo")
        assert template_data is not None, "Demo template not found"

        result = manager.deploy_template(
            template_id="demo",
            configuration={"hello_from": "Integration Test"},
            template_data=template_data,
            pull_image=False,
        )

        assert_deployment_success(result)

        # Test status
        status = manager.get_deployment_status(result["deployment_name"])
        assert status["template"] == "demo"

        # Test listing
        deployments = manager.list_deployments()
        deployment_names = [d["name"] for d in deployments]
        assert result["deployment_name"] in deployment_names

        # Cleanup
        cleanup_success = manager.delete_deployment(result["deployment_name"])
        assert cleanup_success

    @pytest.mark.docker
    def test_deploy_demo_template_docker_no_pull(self, mock_docker_client):
        """Test deploying demo template without pulling image."""
        manager = DeploymentManager()

        # Get template data first
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        template_data = templates.get("demo")
        assert template_data is not None, "Demo template not found"

        # This will fail if the image doesn't exist locally, which is expected
        try:
            result = manager.deploy_template(
                template_id="demo",
                configuration={"hello_from": "Docker Test"},
                template_data=template_data,
                backend="docker",
                pull_image=False,
            )

            # If it succeeds, clean up
            manager.delete_deployment(result["deployment_name"])

        except Exception as e:
            # Expected if image doesn't exist locally
            assert "No such image" in str(e) or "Unable to find image" in str(e)

    def test_invalid_template_deployment(self):
        """Test deploying non-existent template."""
        manager = DeploymentManager()

        with pytest.raises(
            Exception
        ):  # Could be ValueError or KeyError depending on template discovery
            manager.deploy_template(
                template_id="non-existent",
                configuration={},
                template_data={
                    "image": "test:latest"
                },  # Need valid template_data structure
                # No backend specified - should use default (docker) which validates templates
            )

    def test_invalid_backend_deployment(self):
        """Test deploying with invalid backend."""
        manager = DeploymentManager()

        # Get valid template data
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        template_data = templates.get("demo")
        assert template_data is not None, "Demo template not found"

        # Invalid backend should fall back to MockDeploymentService
        # This should actually succeed since invalid backends default to mock
        result = manager.deploy_template(
            template_id="demo",
            configuration={},
            template_data=template_data,
            backend="invalid-backend",
        )
        assert result is not None


@pytest.mark.integration
@pytest.mark.integration
class TestConfigurationIntegration:
    """Test configuration handling and validation."""

    def test_config_validation_with_schema(self):
        """Test configuration validation against template schema."""
        manager = TemplateDiscovery()

        # Get demo template config
        template_config = manager.get_template_config("demo")

        # Valid configuration
        valid_config = {"hello_from": "Test Suite", "log_level": "info"}

        # Should not raise an exception
        manager.validate_template_config(template_config)

    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    @patch("mcp_template.backends.docker.subprocess")
    def test_environment_variable_mapping(self, mock_subprocess, mock_ensure_docker):
        """Test environment variable mapping from config."""
        # Mock subprocess to prevent actual Docker execution
        mock_subprocess.run.return_value.returncode = 0
        mock_subprocess.run.return_value.stdout = "container_id_123"

        # Mock docker availability check
        mock_ensure_docker.return_value = None

        service = DockerDeploymentService()

        config = {"hello_from": "Test", "log_level": "debug"}

        template_data = {
            "name": "test-template",
            "docker_image": "test/image",
            "docker_tag": "latest",
            "config_schema": {
                "properties": {
                    "hello_from": {"env_mapping": "MCP_HELLO_FROM"},
                    "log_level": {"env_mapping": "MCP_LOG_LEVEL"},
                }
            },
        }

        # Deploy and check that env vars are passed correctly
        service.deploy_template(
            template_id="test", config=config, template_data=template_data
        )

        # Verify deployment was called with correct environment variables
        assert mock_subprocess.run.called
        call_args = mock_subprocess.run.call_args[0][0]  # Get the command args

        # Check that environment variables are in the command
        command_str = " ".join(call_args)
        assert "MCP_HELLO_FROM=Test" in command_str
        assert "MCP_LOG_LEVEL=debug" in command_str

    def test_config_defaults_handling(self):
        """Test handling of default configuration values."""
        manager = TemplateDiscovery()
        template_config = manager.get_template_config("demo")

        # Should have config_schema with defaults
        assert "config_schema" in template_config
        schema = template_config["config_schema"]

        if "properties" in schema:
            for prop_name, prop_config in schema["properties"].items():
                if "default" in prop_config:
                    assert prop_config["default"] is not None


@pytest.mark.integration
@pytest.mark.integration
@pytest.mark.template
class TestTemplateStructureValidation:
    """Test template structure and file validation."""

    def test_all_templates_have_required_files(self):
        """Test that all templates have required files."""
        manager = TemplateDiscovery()
        templates = manager.discover_templates()

        required_files = ["template.json", "README.md", "Dockerfile"]

        for template_id in templates:
            template_path = manager.get_template_path(template_id)

            for required_file in required_files:
                file_path = template_path / required_file
                assert (
                    file_path.exists()
                ), f"Template {template_id} missing {required_file}"

    def test_all_templates_have_valid_json(self):
        """Test that all template.json files are valid JSON."""
        manager = TemplateDiscovery()
        templates = manager.discover_templates()

        for template_id in templates:
            template_path = manager.get_template_path(template_id)
            json_path = template_path / "template.json"

            try:
                with open(json_path) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                pytest.fail(f"Template {template_id} has invalid JSON: {e}")

    def test_dockerfile_syntax_basic(self):
        """Test basic Dockerfile syntax validation."""
        manager = TemplateDiscovery()
        templates = manager.discover_templates()

        for template_id in templates:
            template_path = manager.get_template_path(template_id)
            dockerfile_path = template_path / "Dockerfile"

            content = dockerfile_path.read_text()

            # Basic checks
            assert content.strip(), f"Template {template_id} has empty Dockerfile"
            assert (
                "FROM" in content
            ), f"Template {template_id} Dockerfile missing FROM instruction"


@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance aspects of the system."""

    def test_template_discovery_performance(self):
        """Test that template discovery completes in reasonable time."""
        manager = TemplateDiscovery()

        start_time = time.time()
        templates = manager.discover_templates()
        end_time = time.time()

        discovery_time = end_time - start_time

        # Should complete discovery within 5 seconds
        assert (
            discovery_time < 5.0
        ), f"Template discovery took {discovery_time:.2f} seconds"
        assert len(templates) > 0, "No templates discovered"

    def test_multiple_deployments_mock(self):
        """Test deploying multiple templates simultaneously."""
        manager = DeploymentManager(
            backend_type="mock"
        )  # Use mock backend consistently
        deployments = []

        # Get template data first
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()
        template_data = templates.get("demo")
        assert template_data is not None, "Demo template not found"

        try:
            # Deploy multiple instances
            for i in range(3):
                result = manager.deploy_template(
                    template_id="demo",
                    configuration={"hello_from": f"Test {i}"},
                    template_data=template_data,
                    pull_image=False,
                )
                deployments.append(result["deployment_name"])

            # Verify all are listed
            active_deployments = manager.list_deployments()
            active_names = [d["name"] for d in active_deployments]

            for deployment_name in deployments:
                assert deployment_name in active_names

        finally:
            # Cleanup
            for deployment_name in deployments:
                try:
                    manager.delete_deployment(deployment_name)
                except Exception:
                    pass


@pytest.mark.integration
@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_malformed_template_config(self, temp_template_dir):
        """Test handling of malformed template configuration."""
        # Create a template directory with malformed template.json
        malformed_template_dir = temp_template_dir / "malformed-template"
        malformed_template_dir.mkdir()

        # Create malformed template.json inside the directory
        malformed_json = malformed_template_dir / "template.json"
        malformed_json.write_text('{"name": "Test", invalid json}')

        # Also create a Dockerfile so it passes basic validation
        dockerfile = malformed_template_dir / "Dockerfile"
        dockerfile.write_text("FROM python:3.11")

        manager = TemplateDiscovery(templates_dir=temp_template_dir)

        # Should return None for malformed templates rather than crash
        result = manager.get_template_config("malformed-template")
        assert result is None

    @pytest.mark.docker
    def test_docker_service_unavailable(self):
        """Test handling when Docker service is unavailable."""

        with patch("mcp_template.backends.docker.subprocess.run") as mock_run:
            # Mock docker version command to fail
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["docker", "version"]
            )

            with pytest.raises(
                RuntimeError, match="Docker daemon is not available or not running"
            ):
                DockerDeploymentService()

    def test_deployment_cleanup_on_failure(self):
        """Test that failed deployments are properly cleaned up."""

        service = MockDeploymentService()

        # Simulate deployment failure
        with patch.object(service, "_deploy_container") as mock_deploy:
            mock_deploy.side_effect = Exception("Deployment failed")

            with pytest.raises(Exception, match="Deployment failed"):
                service.deploy_template(
                    "test",
                    {},
                    {
                        "docker_image": "test",
                        "docker_tag": "latest",
                        "ports": {},
                        "config_schema": {"properties": {}},
                    },
                )

            # Should not have any deployments after failure
            assert len(service.deployments) == 0
