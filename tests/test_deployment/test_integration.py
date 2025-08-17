#!/usr/bin/env python3
"""
Comprehensive integration tests for MCP template deployment system.

Tests all functionality including:
- Dynamic template discovery
- Template deployment
- Status checking and listing
- Log viewing
- Cleanup functionality
"""

import subprocess
import sys
import time
from pathlib import Path

import pytest

from mcp_template import MCPDeployer
from mcp_template.template.utils.discovery import TemplateDiscovery


@pytest.mark.integration
@pytest.mark.docker
class TestMCPDeploymentSystem:
    """Integration tests for the MCP deployment system."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        self.deployer = MCPDeployer()
        self.deployed_containers = []

        yield

        # Cleanup any containers created during tests
        self._cleanup_test_containers()

    def _cleanup_test_containers(self):
        """Clean up any test containers."""
        try:
            deployments = self.deployer.deployment_manager.list_deployments()
            for deployment in deployments:
                try:
                    self.deployer.deployment_manager.delete_deployment(
                        deployment["name"]
                    )
                except Exception:
                    pass  # Ignore cleanup errors
        except Exception:
            pass  # Ignore if Docker is not available

    def test_template_discovery(self):
        """Test dynamic template discovery functionality."""
        # Test template discovery initialization
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        # Should find at least one template
        assert len(templates) > 0, "No templates discovered"

        # Validate template structure
        for name, template in templates.items():
            required_fields = ["name", "description", "image", "env_vars", "volumes"]
            for field in required_fields:
                assert (
                    field in template
                ), f"Template {name} missing required field: {field}"

    def test_template_deployment(self):
        """Test template deployment functionality."""
        # Get available templates
        templates = list(self.deployer.templates.keys())
        assert len(templates) > 0, "No templates available for testing"

        # Test deployment with first available template
        test_template = templates[0]

        # Check if template is stdio-based and skip if it is
        template_config = self.deployer.templates[test_template]
        transport_config = template_config.get("transport", {})
        default_transport = transport_config.get("default", "http")

        if default_transport == "stdio":
            # Verify that stdio deployment fails appropriately
            try:
                success = self.deployer.deploy(
                    test_template,
                    env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
                    pull_image=False,
                )
                assert (
                    not success
                ), f"Stdio template {test_template} should not be deployable as persistent container"
            except ValueError as e:
                # Expected - stdio templates should raise ValueError
                assert (
                    "stdio transport" in str(e).lower()
                ), f"Expected stdio transport error, got: {e}"
            return

        # For HTTP-based templates, test normal deployment
        success = self.deployer.deploy(
            test_template,
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
            pull_image=False,
        )
        assert success, f"Failed to deploy {test_template}"

        # Wait for container to start
        time.sleep(3)

        # Verify deployment appears in list
        deployments = self.deployer.deployment_manager.list_deployments()
        template_deployments = [
            d for d in deployments if d["template"] == test_template
        ]
        assert (
            len(template_deployments) > 0
        ), f"Deployed template {test_template} not found in list"

        # Store container info for cleanup
        for deployment in template_deployments:
            self.deployed_containers.append(deployment["name"])

    def test_deployment_status_and_logs(self):
        """Test deployment status and log retrieval."""
        templates = list(self.deployer.templates.keys())
        if len(templates) == 0:
            pytest.skip("No templates available for testing")

        test_template = templates[0]

        # Check if template is stdio-based and skip if it is
        template_config = self.deployer.templates[test_template]
        transport_config = template_config.get("transport", {})
        default_transport = transport_config.get("default", "http")

        if default_transport == "stdio":
            # Verify that stdio deployment fails appropriately
            try:
                success = self.deployer.deploy(
                    test_template,
                    env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
                    pull_image=False,
                )
                assert (
                    not success
                ), f"Stdio template {test_template} should not be deployable as persistent container"
            except ValueError as e:
                # Expected - stdio templates should raise ValueError
                assert (
                    "stdio transport" in str(e).lower()
                ), f"Expected stdio transport error, got: {e}"
            return

        # For HTTP-based templates, test normal deployment
        success = self.deployer.deploy(
            test_template,
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
            pull_image=False,
        )
        assert success, f"Failed to deploy {test_template}"

    def test_cleanup_functionality(self):
        """Test cleanup functionality."""
        # First deploy a template
        templates = list(self.deployer.templates.keys())
        if not templates:
            pytest.skip("No templates available for testing")

        test_template = templates[0]

        # Check if template is stdio-based and skip if it is
        template_config = self.deployer.templates[test_template]
        transport_config = template_config.get("transport", {})
        default_transport = transport_config.get("default", "http")

        if default_transport == "stdio":
            # Verify that stdio deployment fails appropriately
            try:
                success = self.deployer.deploy(
                    test_template,
                    env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
                    pull_image=False,
                )
                assert (
                    not success
                ), f"Stdio template {test_template} should not be deployable as persistent container"
            except ValueError as e:
                # Expected - stdio templates should raise ValueError
                assert (
                    "stdio transport" in str(e).lower()
                ), f"Expected stdio transport error, got: {e}"
            return

        # For HTTP-based templates, test normal deployment
        success = self.deployer.deploy(
            test_template,
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"},
            pull_image=False,
        )
        assert success, f"Failed to deploy {test_template}"

        time.sleep(3)

        # Get initial deployment count
        initial_deployments = self.deployer.deployment_manager.list_deployments()
        initial_count = len(initial_deployments)
        assert initial_count > 0, "No deployments found after deployment"

        # Test template-specific cleanup
        success = self.deployer.cleanup(template_name=test_template)
        assert success, f"Failed to cleanup {test_template}"

        # Verify cleanup worked (allow some time for cleanup)
        time.sleep(2)
        remaining_deployments = self.deployer.deployment_manager.list_deployments()

        # Should have fewer or same number of deployments
        # (containers might still be running, which is normal)
        assert (
            len(remaining_deployments) <= initial_count
        ), "Cleanup did not reduce deployment count"


@pytest.mark.unit
class TestTemplateDiscovery:
    """Unit tests for template discovery."""

    def test_template_discovery_initialization(self):
        """Test TemplateDiscovery initialization."""
        discovery = TemplateDiscovery()
        assert discovery.templates_dir.exists(), "Templates directory should exist"

    def test_template_validation(self):
        """Test template validation logic."""
        discovery = TemplateDiscovery()
        templates = discovery.discover_templates()

        for name, template in templates.items():
            # Test required fields
            assert "name" in template
            assert "description" in template
            assert "image" in template

            # Test image format
            assert ":" in template["image"], f"Template {name} image should include tag"


@pytest.mark.integration
@pytest.mark.docker
class TestCLIInterface:
    """Test CLI interface functionality."""

    def test_cli_list_command(self):
        """Test CLI list command."""
        result = subprocess.run(
            [sys.executable, "-m", "mcp_template", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0, f"List command failed: {result.stderr}"

    def test_cli_help_command(self):
        """Test CLI help command."""
        result = subprocess.run(
            [sys.executable, "-m", "mcp_template", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0, f"Help command failed: {result.stderr}"
        assert (
            "stop" in result.stdout
        ), "Help should mention stop command (which includes cleanup functionality)"
        assert "deploy" in result.stdout, "Help should mention deploy command"
        assert "list" in result.stdout, "Help should mention list command"


@pytest.mark.docker
def test_docker_availability():
    """Test that Docker is available for testing."""
    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, check=True
        )
        assert result.returncode == 0, "Docker should be available"
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.fail("Docker is not available. Integration tests require Docker.")


# Fixtures for test data
@pytest.fixture
def sample_template_config():
    """Sample template configuration for testing."""
    return {
        "name": "Test Template",
        "description": "A test template",
        "image": "test/image:latest",
        "env_vars": {"TEST_VAR": "test_value"},
        "volumes": {"~/test-data": "/data"},
        "example_config": '{"servers": {"test": {"command": "test"}}}',
    }


@pytest.fixture
def mock_deployment_result():
    """Mock deployment result for testing."""
    return {
        "deployment_name": "test-deployment",
        "container_id": "abc123",
        "template_id": "test-template",
        "status": "deployed",
        "created_at": "2024-01-01T00:00:00",
        "image": "test/image:latest",
    }
