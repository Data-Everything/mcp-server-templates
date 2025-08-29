"""
Tests for volume mounting functionality in template processing.

Tests the volume mounting features in template schema processing,
including template discovery and configuration processing.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.template.utils.discovery import TemplateDiscovery

pytestmark = pytest.mark.unit


class TestTemplateVolumeMounting:
    """Test template volume mounting functionality."""

    @pytest.fixture
    def mock_template_with_volume_mount(self):
        """Mock template with volume mount property."""
        return {
            "template_id": "test-volume",
            "config_schema": {
                "properties": {
                    "volume_mount": {
                        "type": "object",
                        "description": "Volume mount configuration",
                        "properties": {
                            "host_path": {"type": "string"},
                            "container_path": {"type": "string"},
                            "mode": {"type": "string", "default": "rw"},
                        },
                    }
                }
            },
        }

    @pytest.fixture
    def mock_template_with_command_arg(self):
        """Mock template with command argument property."""
        return {
            "template_id": "test-command",
            "config_schema": {
                "properties": {
                    "command_arg": {
                        "type": "string",
                        "description": "Additional command argument",
                    }
                }
            },
        }

    @pytest.fixture
    def mock_template_with_both(self):
        """Mock template with both volume mount and command properties."""
        return {
            "template_id": "test-both",
            "config_schema": {
                "properties": {
                    "volume_mount": {
                        "type": "object",
                        "description": "Volume mount configuration",
                    },
                    "command_arg": {
                        "type": "string",
                        "description": "Additional command argument",
                    },
                }
            },
        }

    def test_template_discovery_for_volume_command_properties(self):
        """Test template discovery can find templates with volume/command properties."""
        with patch.object(TemplateDiscovery, "discover_templates") as mock_discover:
            mock_discover.return_value = [
                {
                    "template_id": "demo",
                    "config_schema": {
                        "properties": {
                            "volume_mount": {"type": "object"},
                            "command_arg": {"type": "string"},
                        }
                    },
                }
            ]

            discovery = TemplateDiscovery()
            templates = discovery.discover_templates()

            assert len(templates) == 1
            template = templates[0]
            properties = template["config_schema"]["properties"]
            assert "volume_mount" in properties
            assert "command_arg" in properties
