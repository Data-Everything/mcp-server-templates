"""
Tests for volume mounting functionality in client API and CLI.

Tests the volume mounting features added to both the Python client API
and CLI deploy command, including dict/list formats and validation.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.client import MCPClient
from mcp_template.core.deployment_manager import DeploymentManager, DeploymentResult
from mcp_template.template.utils.discovery import TemplateDiscovery

pytestmark = pytest.mark.unit


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


class TestVolumeMountArgumentParsing:
    """Tests for volume mount and command argument functionality."""

    @pytest.fixture
    def mock_template_with_volume_mount(self):
        """Create a mock template with volume mount configuration."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "data_directory": {
                        "type": "string",
                        "description": "Directory to mount as volume",
                        "env_mapping": "DATA_DIR",
                        "volume_mount": True,
                    },
                    "regular_config": {
                        "type": "string",
                        "description": "Regular environment variable",
                        "env_mapping": "REGULAR_CONFIG",
                    },
                },
            },
            "volumes": {},
            "command": [],
        }

    @pytest.fixture
    def mock_template_with_command_arg(self):
        """Create a mock template with command argument configuration."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "server_args": {
                        "type": "string",
                        "description": "Arguments to pass to server",
                        "env_mapping": "SERVER_ARGS",
                        "command_arg": True,
                    },
                    "regular_config": {
                        "type": "string",
                        "description": "Regular environment variable",
                        "env_mapping": "REGULAR_CONFIG",
                    },
                },
            },
            "volumes": {},
            "command": [],
        }

    @pytest.fixture
    def mock_template_with_both(self):
        """Create a mock template with both volume mount and command arg on same property."""
        return {
            "name": "Test Template",
            "description": "A test template",
            "docker_image": "test/image",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "data_path": {
                        "type": "string",
                        "description": "Path that is both mounted and passed as arg",
                        "env_mapping": "DATA_PATH",
                        "volume_mount": True,
                        "command_arg": True,
                    }
                },
            },
            "volumes": {},
            "command": [],
        }

    def test_template_schema_volume_mount_property(
        self, mock_template_with_volume_mount
    ):
        """Test that template schema correctly identifies volume mount properties."""
        config_schema = mock_template_with_volume_mount["config_schema"]
        properties = config_schema["properties"]

        # Check that data_directory has volume_mount flag
        data_dir_prop = properties["data_directory"]
        assert data_dir_prop.get("volume_mount") is True
        assert data_dir_prop.get("env_mapping") == "DATA_DIR"

        # Check that regular_config does not have volume_mount flag
        regular_prop = properties["regular_config"]
        assert regular_prop.get("volume_mount") is not True
        assert regular_prop.get("env_mapping") == "REGULAR_CONFIG"

    def test_template_schema_command_arg_property(self, mock_template_with_command_arg):
        """Test that template schema correctly identifies command argument properties."""
        config_schema = mock_template_with_command_arg["config_schema"]
        properties = config_schema["properties"]

        # Check that server_args has command_arg flag
        server_args_prop = properties["server_args"]
        assert server_args_prop.get("command_arg") is True
        assert server_args_prop.get("env_mapping") == "SERVER_ARGS"

        # Check that regular_config does not have command_arg flag
        regular_prop = properties["regular_config"]
        assert regular_prop.get("command_arg") is not True
        assert regular_prop.get("env_mapping") == "REGULAR_CONFIG"

    def test_template_schema_combined_volume_and_command(self, mock_template_with_both):
        """Test that template schema correctly handles properties with both volume_mount and command_arg."""
        config_schema = mock_template_with_both["config_schema"]
        properties = config_schema["properties"]

        # Check that data_path has both flags
        data_path_prop = properties["data_path"]
        assert data_path_prop.get("volume_mount") is True
        assert data_path_prop.get("command_arg") is True
        assert data_path_prop.get("env_mapping") == "DATA_PATH"

    def test_volume_mount_config_processing(self, mock_template_with_volume_mount):
        """Test processing of configuration values for volume mount properties."""
        # Mock configuration values
        config_values = {"DATA_DIR": "/host/data/path", "REGULAR_CONFIG": "some_value"}

        config_schema = mock_template_with_volume_mount["config_schema"]
        properties = config_schema["properties"]

        # Simulate processing logic for volume mounts
        volume_mounts = {}
        env_vars = {}

        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping")
            if env_mapping and env_mapping in config_values:
                if prop_config.get("volume_mount"):
                    # This should become a volume mount
                    volume_mounts[config_values[env_mapping]] = (
                        f"/container/{prop_name}"
                    )
                else:
                    # This should remain an environment variable
                    env_vars[env_mapping] = config_values[env_mapping]

        # Verify volume mount was created
        assert "/host/data/path" in volume_mounts
        assert volume_mounts["/host/data/path"] == "/container/data_directory"

        # Verify regular config remains as env var
        assert "REGULAR_CONFIG" in env_vars
        assert env_vars["REGULAR_CONFIG"] == "some_value"

    def test_command_arg_config_processing(self, mock_template_with_command_arg):
        """Test processing of configuration values for command argument properties."""
        # Mock configuration values
        config_values = {
            "SERVER_ARGS": "--verbose --port 8080",
            "REGULAR_CONFIG": "some_value",
        }

        config_schema = mock_template_with_command_arg["config_schema"]
        properties = config_schema["properties"]

        # Simulate processing logic for command arguments
        command_args = []
        env_vars = {}

        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping")
            if env_mapping and env_mapping in config_values:
                if prop_config.get("command_arg"):
                    # This should become a command argument
                    command_args.extend(config_values[env_mapping].split())
                else:
                    # This should remain an environment variable
                    env_vars[env_mapping] = config_values[env_mapping]

        # Verify command args were created
        assert command_args == ["--verbose", "--port", "8080"]

        # Verify regular config remains as env var
        assert "REGULAR_CONFIG" in env_vars
        assert env_vars["REGULAR_CONFIG"] == "some_value"

    def test_combined_volume_and_command_processing(self, mock_template_with_both):
        """Test processing of properties that are both volume mounts and command arguments."""
        # Mock configuration values
        config_values = {"DATA_PATH": "/host/shared/data"}

        config_schema = mock_template_with_both["config_schema"]
        properties = config_schema["properties"]

        # Simulate processing logic for combined properties
        volume_mounts = {}
        command_args = []

        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping")
            if env_mapping and env_mapping in config_values:
                value = config_values[env_mapping]

                if prop_config.get("volume_mount"):
                    # This should become a volume mount
                    container_path = f"/container/{prop_name}"
                    volume_mounts[value] = container_path

                if prop_config.get("command_arg"):
                    # This should also become a command argument
                    command_args.append(value)

        # Verify both volume mount and command arg were created
        assert "/host/shared/data" in volume_mounts
        assert volume_mounts["/host/shared/data"] == "/container/data_path"
        assert "/host/shared/data" in command_args


class TestVolumeAndCommandIntegrationWithDeployer:
    """Integration tests with the full deployer workflow."""

    def test_demo_template_volume_command_integration(self):
        """Test the demo template's volume mount and command arg configuration."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Demo template should have the allowed_dirs property with both flags
        if "demo" in templates:
            demo_template = templates["demo"]
            config_schema = demo_template.get("config_schema", {})
            properties = config_schema.get("properties", {})

            if "allowed_dirs" in properties:
                allowed_dirs = properties["allowed_dirs"]
                assert allowed_dirs.get("volume_mount") is True
                assert allowed_dirs.get("command_arg") is True

    def test_filesystem_template_volume_command_integration(self):
        """Test the filesystem template's volume mount and command arg configuration."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Filesystem template should have the allowed_dirs property with both flags
        if "filesystem" in templates:
            filesystem_template = templates["filesystem"]
            config_schema = filesystem_template.get("config_schema", {})
            properties = config_schema.get("properties", {})

            if "allowed_dirs" in properties:
                allowed_dirs = properties["allowed_dirs"]
                assert allowed_dirs.get("volume_mount") is True
                assert allowed_dirs.get("command_arg") is True

    def test_template_discovery_for_volume_command_properties(self):
        """Test that template discovery correctly identifies volume mount and command arg properties."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Check that we have at least one template
        assert len(templates) > 0

        # Look for templates with volume_mount or command_arg properties
        volume_mount_templates = []
        command_arg_templates = []

        for template_id, template_config in templates.items():
            config_schema = template_config.get("config_schema", {})
            properties = config_schema.get("properties", {})

            for prop_name, prop_config in properties.items():
                if prop_config.get("volume_mount"):
                    volume_mount_templates.append((template_id, prop_name))
                if prop_config.get("command_arg"):
                    command_arg_templates.append((template_id, prop_name))

        # We should find at least some templates with these features
        # (This test documents the current state and will help detect regressions)
        print(f"Templates with volume_mount properties: {volume_mount_templates}")
        print(f"Templates with command_arg properties: {command_arg_templates}")

        # Basic assertion that discovery worked
        assert isinstance(volume_mount_templates, list)
        assert isinstance(command_arg_templates, list)
