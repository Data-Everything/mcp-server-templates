"""
Unit tests for Filesystem template.
"""

import json
from pathlib import Path

import pytest


class TestFilesystemUnit:
    """Unit tests for Filesystem template."""

    def test_template_config_loading(self):
        """Test that template.json can be loaded and has required fields."""
        template_path = Path(__file__).parent.parent / "template.json"
        assert template_path.exists(), "template.json should exist"

        with open(template_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        assert config is not None
        assert "name" in config
        assert "docker_image" in config
        assert config["name"] == "Filesystem"

    def test_template_schema_structure(self):
        """Test that the template config schema is properly structured."""
        template_path = Path(__file__).parent.parent / "template.json"

        with open(template_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Check config schema exists
        assert "config_schema" in config
        config_schema = config["config_schema"]

        # Check required properties
        assert "properties" in config_schema
        properties = config_schema["properties"]

        # Check that allowed_dirs is properly configured for volume mount and command arg
        assert "allowed_dirs" in properties
        allowed_dirs = properties["allowed_dirs"]
        assert allowed_dirs.get("volume_mount") is True
        assert allowed_dirs.get("command_arg") is True
        assert "env_mapping" in allowed_dirs

    def test_template_transport_config(self):
        """Test that transport configuration is correct."""
        template_path = Path(__file__).parent.parent / "template.json"

        with open(template_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Filesystem template should be stdio by default
        assert "transport" in config
        transport = config["transport"]
        assert transport.get("default") == "stdio"
        assert "stdio" in transport.get("supported", [])
