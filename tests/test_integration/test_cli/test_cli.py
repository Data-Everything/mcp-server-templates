"""
Integration tests for the main CLI module (mcp_template.cli.cli).

These tests focus on realistic CLI workflows and end-to-end functionality,
using mock backends where possible to avoid external dependencies.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from mcp_template.cli.cli import app

pytestmark = pytest.mark.integration


class TestCLIWorkflows:
    """Test end-to-end CLI workflows."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_full_deployment_workflow(self, mock_client_class):
        """Test complete deployment workflow: deploy -> list -> logs -> stop."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock successful deployment
        mock_deploy_result = Mock()
        mock_deploy_result.success = True
        mock_deploy_result.deployment_id = "demo-integration-test"
        mock_deploy_result.status = "running"
        mock_deploy_result.to_dict.return_value = {
            "deployment_id": "demo-integration-test",
            "status": "running",
            "success": True,
            "ports": {"8080": 8080},
        }
        mock_client.start_server.return_value = mock_deploy_result
        mock_client.deploy_template.return_value = mock_deploy_result

        # Mock template info
        mock_client.get_template_info.return_value = {
            "name": "Demo Template",
            "transport": {"default": "http", "supported": ["http", "stdio"]},
            "config_schema": {},
        }

        # Mock template listing (needed by logs command)
        mock_client.list_templates.return_value = {
            "demo": {
                "name": "Demo Template",
                "description": "Simple demonstration MCP server",
                "image": "unknown",
                "config_schema": {},
            }
        }

        # Mock listing deployments
        mock_client.list_servers.return_value = [
            {
                "id": "demo-integration-test",
                "template": "demo",
                "status": "running",
                "backend": "mock",
            }
        ]

        # Mock logs
        mock_client.get_server_logs.return_value = [
            "2024-01-01 10:00:00 INFO: Server started",
            "2024-01-01 10:00:01 INFO: Listening on port 8080",
            "2024-01-01 10:00:02 INFO: Ready to serve requests",
        ]

        # Mock stop
        mock_client.stop_server.return_value = {"success": True}

        # Mock _multi_manager for backend availability check in list-deployments
        mock_client._multi_manager = Mock()
        mock_client._multi_manager.get_available_backends.return_value = ["mock"]

        # Step 1: Deploy
        result = self.runner.invoke(app, ["--backend", "mock", "deploy", "demo"])
        assert result.exit_code == 0
        mock_client.deploy_template.assert_called()

        # Step 2: List deployments
        result = self.runner.invoke(app, ["list-deployments"])
        assert result.exit_code == 0
        mock_client.list_servers.assert_called()

        # Step 3: Get logs
        result = self.runner.invoke(
            app, ["--backend", "mock", "logs", "demo-integration-test"]
        )
        assert result.exit_code == 0
        mock_client.get_server_logs.assert_called()

        # Step 4: Stop deployment
        result = self.runner.invoke(
            app, ["--backend", "mock", "stop", "demo-integration-test"]
        )
        assert result.exit_code == 0

    @patch("mcp_template.backends.available_valid_backends")
    @patch("mcp_template.cli.cli.MCPClient")
    def test_template_discovery_workflow(
        self, mock_client_class, mock_available_backends
    ):
        """Test template discovery and information workflow."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_available_backends.return_value = {"mock": {}, "docker": {}}

        # Mock template listing
        mock_client.list_templates.return_value = {
            "demo": {
                "name": "Demo Template",
                "description": "Simple demonstration MCP server",
                "docker_image": "dataeverything/mcp-demo",
                "transport": ["stdio", "http"],
                "config_schema": {
                    "type": "object",
                    "properties": {"greeting": {"type": "string", "default": "Hello"}},
                },
            },
            "github": {
                "name": "GitHub Template",
                "description": "GitHub API integration",
                "docker_image": "dataeverything/mcp-github",
                "transport": ["stdio"],
                "config_schema": {
                    "type": "object",
                    "properties": {"GITHUB_PERSONAL_ACCESS_TOKEN": {"type": "string"}},
                },
            },
        }

        # Mock tools listing
        mock_client.list_tools.return_value = {
            "tools": [
                {
                    "name": "search_repositories",
                    "description": "Search GitHub repositories",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "sort": {
                                "type": "string",
                                "enum": ["stars", "forks", "updated"],
                            },
                        },
                    },
                },
                {
                    "name": "create_issue",
                    "description": "Create a new GitHub issue",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                },
            ],
            "discovery_method": "docker",
            "source": "test",
        }

        # Step 1: List available templates
        result = self.runner.invoke(app, ["list-templates"])
        assert result.exit_code == 0
        assert "demo" in result.output
        assert "github" in result.output

        # Step 2: List tools for a specific template
        result = self.runner.invoke(app, ["list-tools", "github"])
        assert result.exit_code == 0
        mock_client.list_tools.assert_called_with(
            "github",
            static=True,
            dynamic=True,
            force_refresh=False,
            include_metadata=True,
        )

        # Step 3: Use generic list command
        result = self.runner.invoke(app, ["list-templates"])
        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_multi_backend_management(self, mock_client_class):
        """Test managing deployments across multiple backends."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock multi-backend deployments
        mock_client.list_servers.return_value = [
            {
                "id": "demo-docker",
                "template": "demo",
                "status": "running",
                "backend": "docker",
            },
            {
                "id": "github-k8s",
                "template": "github",
                "status": "running",
                "backend": "kubernetes",
            },
            {
                "id": "demo-mock",
                "template": "demo",
                "status": "stopped",
                "backend": "mock",
            },
        ]

        # Mock backend health
        mock_multi_manager = Mock()
        mock_client.multi_manager = mock_multi_manager
        mock_multi_manager.get_backend_health.return_value = {
            "docker": {"status": "healthy", "containers": 2},
            "kubernetes": {"status": "healthy", "pods": 1},
            "mock": {"status": "healthy", "deployments": 1},
        }
        mock_multi_manager.get_all_deployments.return_value = (
            mock_client.list_servers.return_value
        )

        # Test status across backends
        result = self.runner.invoke(app, ["status"])
        assert result.exit_code == 0

        # Test listing with backend filter
        result = self.runner.invoke(app, ["list_deployments", "--backend", "docker"])
        assert result.exit_code == 0

        # Test stopping all deployments
        mock_client.stop_all_servers.return_value = {
            "demo-docker": {"success": True},
            "github-k8s": {"success": True},
            "demo-mock": {"success": False, "error": "Already stopped"},
        }

        result = self.runner.invoke(
            app, ["--backend", "mock", "stop", "--all", "--force"]
        )
        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_configuration_management_workflow(self, mock_client_class):
        """Test configuration file and environment variable handling."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_result = Mock()
        mock_result.success = True
        mock_result.to_dict.return_value = {
            "success": True,
            "deployment_id": "test-config",
        }
        mock_client.start_server.return_value = mock_result

        # Create temporary config files
        config_json = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token_123",
            "GITHUB_TOOLSET": "all",
            "DEBUG_MODE": True,
        }

        config_yaml = {
            "greeting": "Hello Integration Test",
            "port": 8080,
            "debug": False,
        }

        # Test with JSON config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_json, f)
            json_config_file = f.name

        try:
            result = self.runner.invoke(
                app,
                [
                    "deploy",
                    "github",
                    "--config-file",
                    json_config_file,
                    "--backend",
                    "mock",
                ],
            )
            assert result.exit_code == 0
        finally:
            Path(json_config_file).unlink()

        # Test with YAML config file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            import yaml

            yaml.dump(config_yaml, f)
            yaml_config_file = f.name

        try:
            result = self.runner.invoke(
                app,
                [
                    "deploy",
                    "demo",
                    "--config-file",
                    yaml_config_file,
                    "--backend",
                    "mock",
                ],
            )
            assert result.exit_code == 0
        finally:
            Path(yaml_config_file).unlink()

        # Test with inline configuration
        result = self.runner.invoke(
            app,
            [
                "deploy",
                "demo",
                "--config",
                "greeting=Hello CLI",
                "--config",
                "port=9090",
                "--backend",
                "mock",
            ],
        )
        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_error_recovery_workflow(self, mock_client_class):
        """Test CLI behavior during error conditions and recovery."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Test deployment failure and retry
        mock_result_fail = Mock()
        mock_result_fail.success = False
        mock_result_fail.error = "Port 8080 already in use"
        mock_result_fail.to_dict.return_value = {
            "success": False,
            "error": "Port 8080 already in use",
        }

        mock_result_success = Mock()
        mock_result_success.success = True
        mock_result_success.deployment_id = "demo-retry"
        mock_result_success.to_dict.return_value = {
            "success": True,
            "deployment_id": "demo-retry",
        }

        # First attempt fails, second succeeds
        mock_client.start_server.side_effect = [mock_result_fail, mock_result_success]

        # First deployment attempt - should fail
        result = self.runner.invoke(
            app, ["--backend", "mock", "deploy", "demo", "--backend", "mock"]
        )
        assert result.exit_code != 0

        # Retry with different port - should succeed
        result = self.runner.invoke(
            app,
            [
                "--backend",
                "mock",
                "deploy",
                "demo",
                "--config",
                "port=8081",
                "--backend",
                "mock",
            ],
        )
        assert result.exit_code == 0

        # Test handling of backend unavailable
        mock_client.list_servers.side_effect = Exception("Backend unavailable")

        result = self.runner.invoke(app, ["list-deployments"])
        assert result.exit_code != 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_logs_and_monitoring_workflow(self, mock_client_class):
        """Test log streaming and monitoring capabilities."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock log output
        mock_logs = [
            "2024-01-01 10:00:00 INFO: Server starting...",
            "2024-01-01 10:00:01 INFO: Loading configuration...",
            "2024-01-01 10:00:02 INFO: Initializing GitHub client...",
            "2024-01-01 10:00:03 INFO: Server ready on port 8080",
            "2024-01-01 10:00:04 DEBUG: Processing request GET /health",
            "2024-01-01 10:00:05 ERROR: Rate limit exceeded for API call",
            "2024-01-01 10:00:06 WARN: Retrying failed request in 60 seconds",
        ]

        mock_client.get_server_logs.return_value = mock_logs

        # Test basic log retrieval
        result = self.runner.invoke(app, ["--backend", "mock", "logs", "github-123"])
        assert result.exit_code == 0
        mock_client.get_server_logs.assert_called()

        # Test log streaming (follow mode)
        result = self.runner.invoke(
            app, ["--backend", "mock", "logs", "github-123", "--follow"]
        )
        assert result.exit_code == 0

        # Test log filtering by lines
        result = self.runner.invoke(
            app, ["--backend", "mock", "logs", "github-123", "--lines", "50"]
        )
        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    @patch("mcp_template.cli.cli.run_interactive_shell")
    def test_interactive_mode_workflow(self, mock_interactive, mock_client_class):
        """Test transitioning to interactive mode."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Test interactive mode entry
        result = self.runner.invoke(app, ["interactive"])
        assert result.exit_code == 0
        mock_interactive.assert_called_once()

        # Test legacy interactive command
        result = self.runner.invoke(app, ["shell"])
        assert result.exit_code == 0

    def test_shell_completion_workflow(self):
        """Test shell completion installation and usage."""
        # Test completion installation
        with patch("mcp_template.cli.cli.install_completion") as mock_install:
            result = self.runner.invoke(app, ["install-completion"])
            assert result.exit_code == 0
            mock_install.assert_called_once()

    @patch("mcp_template.cli.cli.MCPClient")
    def test_dry_run_workflow(self, mock_client_class):
        """Test dry-run mode across different commands."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Test deploy dry-run
        result = self.runner.invoke(
            app,
            ["--backend", "mock", "deploy", "demo", "--dry-run", "--backend", "mock"],
        )
        assert result.exit_code == 0
        # Verify no actual deployment occurred
        mock_client.start_server.assert_not_called()

        # Test stop dry-run
        result = self.runner.invoke(
            app, ["--backend", "mock", "stop", "demo-123", "--dry-run"]
        )
        assert result.exit_code == 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_output_format_workflow(self, mock_client_class):
        """Test different output formats (table, json, yaml)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_client.list_servers.return_value = [
            {"id": "demo-1", "template": "demo", "status": "running"},
            {"id": "github-1", "template": "github", "status": "stopped"},
        ]

        # Test table output (default)
        result = self.runner.invoke(app, ["list-deployments"])
        assert result.exit_code == 0

        # Test JSON output
        result = self.runner.invoke(app, ["list_deployments", "--format", "json"])
        assert result.exit_code == 0

        # Test YAML output
        result = self.runner.invoke(app, ["list_deployments", "--format", "yaml"])
        assert result.exit_code == 0


class TestCLIIntegrationEdgeCases:
    """Test edge cases and error conditions in CLI integration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_invalid_command_handling(self):
        """Test handling of invalid commands and arguments."""
        # Test invalid command
        result = self.runner.invoke(app, ["invalid_command"])
        assert result.exit_code != 0

        # Test invalid arguments
        result = self.runner.invoke(
            app, ["--backend", "mock", "deploy"]
        )  # Missing template name
        assert result.exit_code != 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_network_timeout_handling(self, mock_client_class):
        """Test handling of network timeouts and connection issues."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Simulate network timeout
        import socket

        mock_client.list_servers.side_effect = socket.timeout("Connection timed out")

        result = self.runner.invoke(app, ["list-deployments"])
        assert result.exit_code != 0

    @patch("mcp_template.cli.cli.MCPClient")
    def test_concurrent_operation_handling(self, mock_client_class):
        """Test handling of concurrent operations and conflicts."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Simulate deployment conflict
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = "Deployment name 'demo' already exists"
        mock_result.to_dict.return_value = {
            "success": False,
            "error": "Deployment name 'demo' already exists",
        }
        mock_client.start_server.return_value = mock_result

        result = self.runner.invoke(app, ["--backend", "mock", "deploy", "demo"])
        assert result.exit_code != 0

    def test_config_file_validation(self):
        """Test configuration file validation and error handling."""
        # Test with invalid JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json}')  # Invalid JSON
            invalid_json_file = f.name

        try:
            result = self.runner.invoke(
                app,
                [
                    "--backend",
                    "mock",
                    "deploy",
                    "demo",
                    "--config-file",
                    invalid_json_file,
                ],
            )
            # Should handle invalid JSON gracefully
            assert result.exit_code != 0
        finally:
            Path(invalid_json_file).unlink()

        # Test with non-existent config file
        result = self.runner.invoke(
            app,
            [
                "--backend",
                "mock",
                "deploy",
                "demo",
                "--config-file",
                "/path/that/does/not/exist.json",
            ],
        )
        assert result.exit_code != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
