"""Integration tests for the demo server."""

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Add the src directory to the path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestDemoServerIntegration:
    """Integration tests for the demo server."""

    def test_server_imports(self):
        """Test that the server module can be imported."""
        try:
            from server import DemoServer, DemoServerConfig, main

            assert DemoServer is not None
            assert DemoServerConfig is not None
            assert main is not None
        except ImportError as e:
            pytest.fail(f"Failed to import server modules: {e}")

    def test_fastmcp_dependency(self):
        """Test that FastMCP dependency is available."""
        try:
            from fastmcp import FastMCP

            assert FastMCP is not None
        except ImportError:
            pytest.skip("FastMCP not available - this is expected in CI")

    def test_server_configuration_loading(self, mock_env_vars):
        """Test that server loads configuration correctly."""
        try:
            from server import DemoServerConfig

            config = DemoServerConfig()
            assert config.hello_from == "Test Server"
            assert hasattr(config, "logger")
        except ImportError:
            pytest.skip("Server module not available")

    def test_template_json_validity(self):
        """Test that template.json is valid."""
        template_path = Path(__file__).parent.parent / "template.json"

        assert template_path.exists(), "template.json should exist"

        with open(template_path, "r") as f:
            template_data = json.load(f)

        # Verify required fields
        assert "name" in template_data
        assert "description" in template_data
        assert "config_schema" in template_data

        # Verify config schema structure
        schema = template_data["config_schema"]
        assert "properties" in schema
        assert "hello_from" in schema["properties"]

        # Verify hello_from configuration
        hello_from_config = schema["properties"]["hello_from"]
        assert hello_from_config["env_mapping"] == "MCP_HELLO_FROM"
        assert hello_from_config["default"] == "MCP Platform"

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and has basic structure."""
        dockerfile_path = Path(__file__).parent.parent / "Dockerfile"

        assert dockerfile_path.exists(), "Dockerfile should exist"

        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Check for basic Dockerfile components
        assert "FROM python:" in content
        assert "COPY requirements.txt" in content
        assert "RUN pip install" in content
        assert "CMD" in content

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists and contains FastMCP."""
        requirements_path = Path(__file__).parent.parent / "requirements.txt"

        assert requirements_path.exists(), "requirements.txt should exist"

        with open(requirements_path, "r") as f:
            content = f.read()

        assert "fastmcp" in content.lower()

    def test_readme_completeness(self):
        """Test that README.md is comprehensive."""
        readme_path = Path(__file__).parent.parent / "README.md"

        assert readme_path.exists(), "README.md should exist"

        with open(readme_path, "r") as f:
            content = f.read()

        # Check for essential documentation sections
        required_sections = [
            "# Demo Hello MCP Server",
            "## Features",
            "## Configuration",
            "## Available Tools",
            "## Usage Examples",
            "say_hello",
            "get_server_info",
        ]

        for section in required_sections:
            assert section in content, f"README should contain '{section}'"

    def test_module_structure(self):
        """Test that the module has proper structure."""
        src_path = Path(__file__).parent.parent / "src"

        assert src_path.exists(), "src directory should exist"
        assert (src_path / "__init__.py").exists(), "__init__.py should exist in src"
        assert (src_path / "server.py").exists(), "server.py should exist in src"
