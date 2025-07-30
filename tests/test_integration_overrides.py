#!/usr/bin/env python3
"""
Integration tests for template config overrides in the deployment flow.

Tests that override values are correctly passed through the CLI via
deploy_with_transport(), deployer.deploy(), to Docker run commands.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.cli import EnhancedCLI
from mcp_template.deployer import MCPDeployer
from mcp_template.manager import DeploymentManager


@pytest.mark.integration
@pytest.mark.docker
class TestDeploymentIntegration:
    """Test full deployment integration with overrides."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.enhanced_cli = EnhancedCLI()
        self.deployer = MCPDeployer()

        # Mock template data
        self.mock_template = {
            "name": "Demo Server",
            "version": "1.0.0",
            "image": "dataeverything/mcp-demo:latest",
            "docker_image": "test/demo",
            "docker_tag": "latest",
            "ports": {"7071": 7071},
            "config_schema": {
                "properties": {
                    "hello_from": {
                        "type": "string",
                        "default": "MCP Platform",
                        "env_mapping": "MCP_HELLO_FROM",
                    },
                    "debug_mode": {
                        "type": "boolean",
                        "default": False,
                        "env_mapping": "MCP_DEBUG_MODE",
                    },
                    "max_connections": {
                        "type": "integer",
                        "default": 10,
                        "env_mapping": "MCP_MAX_CONNECTIONS",
                    },
                }
            },
            "tools": [
                {"name": "say_hello", "description": "Say hello", "enabled": True}
            ],
            "metadata": {"author": "Original Author"},
        }

    @patch("mcp_template.manager.DeploymentManager")
    @patch("mcp_template.template.discovery.TemplateDiscovery.discover_templates")
    def test_config_overrides_reach_deployment(
        self, mock_discover, mock_deployment_manager_class
    ):
        """Test that config overrides reach the deployment backend."""
        # Setup mocks
        mock_discover.return_value = {"demo": self.mock_template}
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager
        mock_deployment_manager.deploy_template.return_value = {
            "deployment_name": "test-deployment",
            "status": "deployed",
            "image": "test:latest",
        }

        # Deploy with config overrides
        override_values = {
            "hello_from": "Custom Server",
            "debug_mode": "true",
            "max_connections": "25",
        }

        # Create a new deployer instance to use the mocked manager
        deployer = MCPDeployer()
        deployer.templates = {"demo": self.mock_template}
        deployer.deployment_manager = mock_deployment_manager

        with patch.object(deployer, "_generate_mcp_config"):
            result = deployer.deploy(
                template_name="demo", override_values=override_values
            )

        # Verify deployment was called
        assert result is True
        mock_deployment_manager.deploy_template.assert_called_once()

        # Extract the actual call arguments
        call_args = mock_deployment_manager.deploy_template.call_args
        configuration = call_args[1]["configuration"]

        # Verify config overrides were converted to OVERRIDE_ environment variables
        assert "OVERRIDE_hello_from" in configuration
        assert "OVERRIDE_debug_mode" in configuration
        assert "OVERRIDE_max_connections" in configuration

    @patch("mcp_template.manager.DeploymentManager")
    @patch("mcp_template.template.discovery.TemplateDiscovery.discover_templates")
    def test_template_overrides_modify_template_data(
        self, mock_discover, mock_deployment_manager_class
    ):
        """Test that template overrides modify the template_data passed to backend."""
        # Setup mocks
        mock_discover.return_value = {"demo": self.mock_template}
        mock_deployment_manager = Mock()
        mock_deployment_manager_class.return_value = mock_deployment_manager
        mock_deployment_manager.deploy_template.return_value = {
            "deployment_name": "test-deployment",
            "status": "deployed",
            "image": "test:latest",
        }

        # Deploy with template structure overrides
        override_values = {
            "tools__0__name": "custom_hello",
            "tools__0__enabled": "false",
            "metadata__author": "New Author",
            "metadata__version": "2.0.0",
        }

        # Create a new deployer instance to use the mocked manager
        deployer = MCPDeployer()
        deployer.templates = {"demo": self.mock_template}
        deployer.deployment_manager = mock_deployment_manager

        with patch.object(deployer, "_generate_mcp_config"):
            result = deployer.deploy(
                template_name="demo", override_values=override_values
            )

        # Verify deployment was called
        assert result is True
        mock_deployment_manager.deploy_template.assert_called_once()

        # Extract the call arguments
        call_args = mock_deployment_manager.deploy_template.call_args
        configuration = call_args[1]["configuration"]

        # Verify template overrides were converted to OVERRIDE_ environment variables
        assert "OVERRIDE_tools__0__name" in configuration
        assert configuration["OVERRIDE_tools__0__name"] == "custom_hello"
        assert "OVERRIDE_tools__0__enabled" in configuration
        assert configuration["OVERRIDE_tools__0__enabled"] == "false"
        assert "OVERRIDE_metadata__author" in configuration
        assert configuration["OVERRIDE_metadata__author"] == "New Author"
        assert "OVERRIDE_metadata__version" in configuration
        assert configuration["OVERRIDE_metadata__version"] == "2.0.0"

    @patch("mcp_template.template.discovery.TemplateDiscovery.discover_templates")
    def test_mixed_config_and_template_overrides(self, mock_discover):
        """Test mixing config overrides and template overrides."""
        # Setup mocks
        mock_discover.return_value = {"demo": self.mock_template}

        deployer = MCPDeployer()
        deployer.templates = {"demo": self.mock_template}

        with patch.object(deployer, "deployment_manager") as mock_manager, patch.object(
            deployer, "_generate_mcp_config"
        ):
            mock_manager.deploy_template.return_value = {
                "deployment_name": "test-deployment",
                "status": "deployed",
                "image": "test:latest",
            }

            # Deploy with mixed overrides
            override_values = {
                # Config overrides (have env_mapping)
                "hello_from": "Mixed Server",
                "debug_mode": "true",
                # Template overrides (no env_mapping)
                "tools__0__description": "Custom description",
                "metadata__custom__field": "custom_value",
            }

            result = deployer.deploy(
                template_name="demo", override_values=override_values
            )

            assert result is True
            call_args = mock_manager.deploy_template.call_args

            # Check configuration (for env vars) - overrides are converted to OVERRIDE_ prefixed env vars
            configuration = call_args.kwargs["configuration"]
            assert "OVERRIDE_hello_from" in configuration
            assert "OVERRIDE_debug_mode" in configuration
            assert "OVERRIDE_tools__0__description" in configuration
            assert "OVERRIDE_metadata__custom__field" in configuration

    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    def test_env_vars_reach_docker_command(self, mock_ensure_docker, mock_run_command):
        """Test that config overrides become environment variables in Docker command."""
        # Setup mocks
        mock_run_command.side_effect = [
            Mock(stdout="pulled", stderr=""),  # docker pull
            Mock(stdout="container123", stderr=""),  # docker run
        ]

        # Create a deployment manager with Docker backend
        manager = DeploymentManager(backend_type="docker")

        # Test config with overrides
        config = {
            "hello_from": "Docker Test",
            "debug_mode": "true",
            "max_connections": "15",
        }

        template_data = self.mock_template.copy()

        # Deploy
        manager.deploy_template(
            template_id="demo", configuration=config, template_data=template_data
        )  # Verify Docker run was called
        assert mock_run_command.call_count == 2
        docker_run_call = mock_run_command.call_args_list[1]
        docker_command = docker_run_call[0][0]

        # Verify environment variables are in the command
        env_vars = []
        for i, arg in enumerate(docker_command):
            if arg == "--env" and i + 1 < len(docker_command):
                env_vars.append(docker_command[i + 1])

        # Check that our config overrides became env vars
        assert any("MCP_HELLO_FROM=Docker Test" in env_var for env_var in env_vars)
        assert any("MCP_DEBUG_MODE=true" in env_var for env_var in env_vars)
        assert any("MCP_MAX_CONNECTIONS=15" in env_var for env_var in env_vars)

    @patch("mcp_template.backends.docker.DockerDeploymentService._run_command")
    @patch(
        "mcp_template.backends.docker.DockerDeploymentService._ensure_docker_available"
    )
    def test_no_env_var_duplication(self, mock_ensure_docker, mock_run_command):
        """Test that environment variables are not duplicated in Docker command."""
        # Setup mocks
        mock_run_command.side_effect = [
            Mock(stdout="pulled", stderr=""),  # docker pull
            Mock(stdout="container123", stderr=""),  # docker run
        ]

        manager = DeploymentManager(backend_type="docker")

        # Config with potential duplicates
        config = {
            "hello_from": "No Duplicate Test",
            "MCP_HELLO_FROM": "Another Value",  # This could cause duplication
        }

        template_data = {
            **self.mock_template,
            "env_vars": {
                "MCP_HELLO_FROM": "Template Default"  # Another potential duplicate
            },
        }

        # Deploy
        manager.deploy_template(
            template_id="demo", configuration=config, template_data=template_data
        )

        # Get the Docker run command
        docker_run_call = mock_run_command.call_args_list[1]
        docker_command = docker_run_call[0][0]

        # Count MCP_HELLO_FROM occurrences
        hello_from_count = 0
        for i, arg in enumerate(docker_command):
            if arg == "--env" and i + 1 < len(docker_command):
                env_var = docker_command[i + 1]
                if "MCP_HELLO_FROM=" in env_var:
                    hello_from_count += 1

        # Should only appear once (no duplication)
        assert hello_from_count == 1


@pytest.mark.integration
@pytest.mark.docker
class TestCLIIntegration:
    """Test CLI integration with enhanced deploy_with_transport."""

    @patch("mcp_template.cli.MCPDeployer")
    def test_deploy_with_transport_passes_overrides(self, mock_deployer_class):
        """Test that deploy_with_transport passes override values correctly."""
        mock_deployer = Mock()
        mock_deployer.deploy.return_value = True
        mock_deployer_class.return_value = mock_deployer

        # Create CLI instance after patching MCPDeployer
        enhanced_cli = EnhancedCLI()

        # Mock templates
        enhanced_cli.templates = {
            "demo": {"transport": {"supported": ["http", "stdio"], "default": "http"}}
        }

        # Test with override values
        override_values = {"metadata__version": "2.0.0", "tools__0__enabled": "false"}

        result = enhanced_cli.deploy_with_transport(
            template_name="demo",
            transport="http",
            port=7071,
            override_values=override_values,
        )

        assert result is True

        # Verify deploy was called with override values
        mock_deployer.deploy.assert_called_once()
        call_kwargs = mock_deployer.deploy.call_args[1]

        assert "override_values" in call_kwargs
        assert call_kwargs["override_values"] == override_values

    @patch("mcp_template.cli.MCPDeployer")
    def test_transport_config_and_overrides_combined(self, mock_deployer_class):
        """Test that transport config and overrides are properly combined."""
        mock_deployer = Mock()
        mock_deployer.deploy.return_value = True
        mock_deployer_class.return_value = mock_deployer

        # Create CLI instance after patching MCPDeployer
        enhanced_cli = EnhancedCLI()

        # Mock templates
        enhanced_cli.templates = {
            "demo": {"transport": {"supported": ["http"], "default": "http"}}
        }

        # Test with both transport settings and overrides
        override_values = {"metadata__version": "2.0.0"}
        config_values = {"debug_mode": "true"}

        result = enhanced_cli.deploy_with_transport(
            template_name="demo",
            transport="http",
            port=8080,
            config_values=config_values,
            override_values=override_values,
        )

        assert result is True

        call_kwargs = mock_deployer.deploy.call_args[1]

        # Should have transport config
        final_config_values = call_kwargs["config_values"]
        assert final_config_values["transport"] == "http"
        assert final_config_values["port"] == "8080"
        assert final_config_values["debug_mode"] == "true"

        # Should have override values
        assert call_kwargs["override_values"] == override_values
