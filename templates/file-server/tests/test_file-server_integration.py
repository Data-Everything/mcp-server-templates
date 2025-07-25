#!/usr/bin/env python3
"""
Integration tests for file-server template.

Auto-generated by TemplateTestGenerator.
Tests actual deployment and container functionality.
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_template import MCPDeployer
from tests.utils.mcp_test_utils import build_and_run_template


@pytest.mark.integration
@pytest.mark.docker
class TestFileServerIntegration:
    """Integration tests for file-server template deployment."""

    @pytest.fixture
    def deployer(self):
        """MCPDeployer fixture."""
        return MCPDeployer()

    def test_template_deployment(self, deployer):
        """Test successful template deployment."""
        # Skip if template not available
        if "file-server" not in deployer.templates:
            pytest.skip("file-server template not available")

        # Deploy template
        success = deployer.deploy("file-server")
        assert success, "Template deployment should succeed"

        # Wait for container to start
        time.sleep(3)

        # Verify deployment
        deployments = deployer.deployment_manager.list_deployments()
        template_deployments = [
            d for d in deployments if d["template"] == "file-server"
        ]
        assert len(template_deployments) > 0, "Deployed template should appear in list"

        # Cleanup
        for deployment in template_deployments:
            deployer.deployment_manager.delete_deployment(deployment["name"])

    def test_container_health(self):
        """Test container starts and runs healthily."""
        config = {
            "allowed_directories": ["/data"],
            "read_only_mode": False,
            "enable_symlinks": True,
            "max_file_size": 100,
            "exclude_patterns": ["**/.git/**", "**/node_modules/**", "**/.env*"],
            "log_level": "info",
            "enable_audit": True,
            "max_concurrent_operations": 10,
            "timeout_ms": 30000,
            "cache_enabled": True,
            "metrics_enabled": True,
        }

        with build_and_run_template("file-server", config) as container:
            # Container should start successfully
            assert container.container_id, "Container should have valid ID"

            # Check container logs for health indicators
            logs = container.get_logs()
            health_indicators = [
                "Starting MCP server",
                "Server initialized",
                "FastMCP",
                "transport",
            ]

            found_indicators = [
                indicator for indicator in health_indicators if indicator in logs
            ]
            assert (
                len(found_indicators) > 0
            ), f"Container logs should contain health indicators. Logs: {logs}"

    def test_configuration_mapping(self, deployer):
        """Test configuration mapping works correctly."""
        if "file-server" not in deployer.templates:
            pytest.skip("file-server template not available")

        template = deployer.templates["file-server"]

        # Test file config mapping
        file_config = {
            "allowed_directories": ["/data"],
            "read_only_mode": False,
            "enable_symlinks": True,
            "max_file_size": 100,
            "exclude_patterns": ["**/.git/**", "**/node_modules/**", "**/.env*"],
            "log_level": "info",
            "enable_audit": True,
            "max_concurrent_operations": 10,
            "timeout_ms": 30000,
            "cache_enabled": True,
            "metrics_enabled": True,
        }

        result = deployer._map_file_config_to_env(file_config, template)

        # Should produce environment variables
        assert (
            len(result) > 0
        ), "Configuration mapping should produce environment variables"

        # All values should be strings (for environment variables)
        for key, value in result.items():
            assert isinstance(
                value, str
            ), f"Environment variable {key} should be string, got {type(value)}"

    def test_mcp_endpoints(self):
        """Test MCP server endpoints and tools."""
        config = {
            "allowed_directories": ["/data"],
            "read_only_mode": False,
            "enable_symlinks": True,
            "max_file_size": 100,
            "exclude_patterns": ["**/.git/**", "**/node_modules/**", "**/.env*"],
            "log_level": "info",
            "enable_audit": True,
            "max_concurrent_operations": 10,
            "timeout_ms": 30000,
            "cache_enabled": True,
            "metrics_enabled": True,
        }

        with build_and_run_template("file-server", config) as container:
            # Wait for server to fully initialize
            time.sleep(5)

            # Test that container is providing MCP protocol
            logs = container.get_logs()

            # Should contain MCP-related initialization messages
            mcp_indicators = ["MCP", "FastMCP", "stdio", "transport"]
            found = [indicator for indicator in mcp_indicators if indicator in logs]
            assert (
                len(found) > 0
            ), f"Server should show MCP initialization. Logs: {logs}"
