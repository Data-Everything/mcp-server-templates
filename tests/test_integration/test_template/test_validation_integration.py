"""
Integration tests for template discovery with tool discovery.
"""

import json

import pytest

pytestmark = pytest.mark.integration


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
