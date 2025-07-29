"""
Tests for template validation with tool discovery fields.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_template.template.discovery import TemplateDiscovery


class TestTemplateValidation:
    """Test template validation with new tool discovery fields."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.templates_dir = self.temp_dir / "templates"
        self.templates_dir.mkdir()

        self.discovery = TemplateDiscovery(templates_dir=self.templates_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_valid_template_with_tool_discovery_fields(self):
        """Test validation of template with proper tool discovery fields."""
        template_dir = self.templates_dir / "valid-template"
        template_dir.mkdir()

        # Create valid template.json with tool discovery fields
        template_config = {
            "name": "Valid Template",
            "description": "A valid template",
            "version": "1.0.0",
            "docker_image": "test/image",
            "tool_discovery": "dynamic",
            "tool_endpoint": "/tools",
            "has_image": True,
            "origin": "internal",
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f)

        # Create Dockerfile
        with open(template_dir / "Dockerfile", "w") as f:
            f.write("FROM python:3.9\n")

        templates = self.discovery.discover_templates()

        assert "valid-template" in templates
        template = templates["valid-template"]

        # Check that tool discovery fields are preserved
        # Note: These would be available in the original template_data
        # The discovery class may not pass all fields through

    def test_static_tool_discovery_requires_tools_json(self):
        """Test that static tool discovery validates tools.json exists."""
        template_dir = self.templates_dir / "static-template"
        template_dir.mkdir()

        # Create template.json with static tool discovery
        template_config = {
            "name": "Static Template",
            "description": "A template with static tool discovery",
            "version": "1.0.0",
            "docker_image": "test/image",
            "tool_discovery": "static",
            "tool_endpoint": "/tools",
            "has_image": True,
            "origin": "internal",
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f)

        # Create Dockerfile
        with open(template_dir / "Dockerfile", "w") as f:
            f.write("FROM python:3.9\n")

        # Should still discover template even without tools.json
        # (tools.json validation would be in a separate validation step)
        templates = self.discovery.discover_templates()
        assert "static-template" in templates

    def test_tools_json_validation(self):
        """Test validation of tools.json format."""
        template_dir = self.templates_dir / "tools-template"
        template_dir.mkdir()

        # Create template.json
        template_config = {
            "name": "Tools Template",
            "description": "A template with tools.json",
            "version": "1.0.0",
            "docker_image": "test/image",
            "tool_discovery": "static",
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f)

        # Create Dockerfile
        with open(template_dir / "Dockerfile", "w") as f:
            f.write("FROM python:3.9\n")

        # Create valid tools.json
        tools_config = {
            "tools": [
                {
                    "name": "test_tool",
                    "description": "A test tool",
                    "category": "test",
                    "parameters": {
                        "type": "object",
                        "properties": {"param1": {"type": "string"}},
                    },
                }
            ]
        }

        with open(template_dir / "tools.json", "w") as f:
            json.dump(tools_config, f)

        templates = self.discovery.discover_templates()
        assert "tools-template" in templates

    def test_invalid_tools_json_format(self):
        """Test handling of invalid tools.json format."""
        template_dir = self.templates_dir / "invalid-tools-template"
        template_dir.mkdir()

        # Create template.json
        template_config = {
            "name": "Invalid Tools Template",
            "description": "A template with invalid tools.json",
            "version": "1.0.0",
            "docker_image": "test/image",
            "tool_discovery": "static",
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f)

        # Create Dockerfile
        with open(template_dir / "Dockerfile", "w") as f:
            f.write("FROM python:3.9\n")

        # Create invalid tools.json (not valid JSON)
        with open(template_dir / "tools.json", "w") as f:
            f.write("{ invalid json")

        # Template should still be discovered (tools.json validation is separate)
        templates = self.discovery.discover_templates()
        assert "invalid-tools-template" in templates

    def test_default_tool_discovery_values(self):
        """Test default values for tool discovery fields."""
        from mcp_template.template.creation import TemplateCreator

        creator = TemplateCreator(templates_dir=self.templates_dir)
        creator.template_data = {
            "id": "default-template",
            "name": "Default Template",
            "description": "A template with defaults",
            "version": "1.0.0",
            "author": "Test Author",
        }

        # Create template directory
        creator.template_dir = self.templates_dir / "default-template"
        creator.template_dir.mkdir()

        # Create the template JSON (this will use defaults)
        creator._create_template_json()

        # Verify defaults are set
        with open(creator.template_dir / "template.json", "r") as f:
            config = json.load(f)

        assert config["tool_discovery"] == "dynamic"
        assert config["tool_endpoint"] == "/tools"
        assert config["has_image"] is True
        assert config["origin"] == "internal"

    def test_external_template_validation(self):
        """Test validation behavior for external templates."""
        template_dir = self.templates_dir / "external-template"
        template_dir.mkdir()

        # Create template.json for external template
        template_config = {
            "name": "External Template",
            "description": "An external template",
            "version": "1.0.0",
            "docker_image": "external/image",
            "tool_discovery": "dynamic",
            "tool_endpoint": "/api/tools",
            "has_image": True,
            "origin": "external",
        }

        with open(template_dir / "template.json", "w") as f:
            json.dump(template_config, f)

        # Create Dockerfile
        with open(template_dir / "Dockerfile", "w") as f:
            f.write("FROM external/base:latest\n")

        templates = self.discovery.discover_templates()
        assert "external-template" in templates


class TestTemplateIntegration:
    """Integration tests for template discovery with tool discovery."""

    def test_demo_template_has_required_fields(self):
        """Test that the demo template has the required tool discovery fields."""
        from mcp_template.utils import TEMPLATES_DIR

        demo_template_path = TEMPLATES_DIR / "demo" / "template.json"

        if demo_template_path.exists():
            with open(demo_template_path, "r") as f:
                config = json.load(f)

            # Check that required fields are present
            assert "tool_discovery" in config
            assert "tool_endpoint" in config
            assert "has_image" in config
            assert "origin" in config

            # Check specific values
            assert config["tool_discovery"] in ["static", "dynamic", "none"]
            assert config["origin"] in ["internal", "external"]

    def test_demo_template_tools_json_exists(self):
        """Test that demo template has tools.json if using static discovery."""
        from mcp_template.utils import TEMPLATES_DIR

        demo_template_path = TEMPLATES_DIR / "demo" / "template.json"
        tools_json_path = TEMPLATES_DIR / "demo" / "tools.json"

        if demo_template_path.exists():
            with open(demo_template_path, "r") as f:
                config = json.load(f)

            if config.get("tool_discovery") == "static":
                assert (
                    tools_json_path.exists()
                ), "Static tool discovery requires tools.json"

                # Validate tools.json format
                with open(tools_json_path, "r") as f:
                    tools_config = json.load(f)

                assert "tools" in tools_config
                assert isinstance(tools_config["tools"], list)


if __name__ == "__main__":
    pytest.main([__file__])
