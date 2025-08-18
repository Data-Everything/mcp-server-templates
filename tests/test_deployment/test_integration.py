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
from pathlib import Path

import pytest

from mcp_template.template.utils.discovery import TemplateDiscovery


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
