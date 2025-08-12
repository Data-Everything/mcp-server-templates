"""
Unit tests for TemplateManager.

Tests the template discovery, validation, and metadata operations
provided by the TemplateManager common module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from mcp_template.core.template_manager import TemplateManager


@pytest.mark.unit
class TestTemplateManager:
    """Unit tests for TemplateManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template_manager = TemplateManager(backend_type="mock")

    def test_list_templates_basic(self):
        """Test basic template listing."""
        # Mock the template discovery
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "version": "1.0.0",
                "description": "Demo MCP server",
                "docker_image": "demo:latest",
            },
            "filesystem": {
                "name": "Filesystem Template",
                "version": "1.2.0",
                "description": "File operations server",
                "docker_image": "filesystem:latest",
            },
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            templates = self.template_manager.list_templates()

        assert len(templates) == 2
        assert "demo" in templates
        assert "filesystem" in templates
        assert templates["demo"]["name"] == "Demo Template"

    def test_list_templates_with_deployment_status(self):
        """Test template listing with deployment status."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "version": "1.0.0",
                "description": "Demo MCP server",
                "docker_image": "demo:latest",
            }
        }

        mock_deployments = [{"id": "demo-123", "template": "demo", "status": "running"}]

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            with patch.object(
                self.template_manager.backend,
                "list_deployments",
                return_value=mock_deployments,
            ):
                templates = self.template_manager.list_templates(
                    include_deployed_status=True
                )

        assert templates["demo"]["deployed"] is True
        assert templates["demo"]["deployment_count"] == 1
        assert len(templates["demo"]["deployments"]) == 1

    def test_list_templates_filter_deployed_only(self):
        """Test template listing filtered to deployed only."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "version": "1.0.0",
                "description": "Demo MCP server",
                "docker_image": "demo:latest",
            },
            "filesystem": {
                "name": "Filesystem Template",
                "version": "1.2.0",
                "description": "File operations server",
                "docker_image": "filesystem:latest",
            },
        }

        # Mock backend to return deployments only for demo
        def mock_list_deployments(template_name):
            if template_name == "demo":
                return [{"id": "demo-123", "template": "demo"}]
            return []

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            with patch.object(
                self.template_manager.backend,
                "list_deployments",
                side_effect=mock_list_deployments,
            ):
                templates = self.template_manager.list_templates(
                    include_deployed_status=True, filter_deployed_only=True
                )

        assert len(templates) == 1
        assert "demo" in templates
        assert "filesystem" not in templates

    def test_get_template_info_existing(self):
        """Test getting info for existing template."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "version": "1.0.0",
                "description": "Demo MCP server",
                "docker_image": "demo:latest",
            }
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            info = self.template_manager.get_template_info("demo")

        assert info is not None
        assert info["name"] == "Demo Template"
        assert info["version"] == "1.0.0"

    def test_get_template_info_nonexistent(self):
        """Test getting info for non-existent template."""
        mock_templates = {}

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            info = self.template_manager.get_template_info("nonexistent")

        assert info is None

    def test_validate_template_valid(self):
        """Test validation of valid template."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "version": "1.0.0",
                "description": "Demo MCP server",
                "docker_image": "demo:latest",
            }
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            is_valid = self.template_manager.validate_template("demo")

        assert is_valid is True

    def test_validate_template_invalid(self):
        """Test validation of invalid template."""
        mock_templates = {
            "incomplete": {
                "name": "Incomplete Template"
                # Missing required docker_image field
            }
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            is_valid = self.template_manager.validate_template("incomplete")

        assert is_valid is False

    def test_validate_template_nonexistent(self):
        """Test validation of non-existent template."""
        mock_templates = {}

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            is_valid = self.template_manager.validate_template("nonexistent")

        assert is_valid is False

    def test_search_templates(self):
        """Test template search functionality."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "description": "Demo MCP server for testing",
                "tags": ["demo", "example"],
            },
            "filesystem": {
                "name": "Filesystem Template",
                "description": "File operations server",
                "tags": ["filesystem", "files"],
            },
            "database": {
                "name": "Database Template",
                "description": "Database access server",
                "tags": ["database", "sql"],
            },
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            # Search by name
            results = self.template_manager.search_templates("demo")
            assert len(results) == 1
            assert "demo" in results

            # Search by description
            results = self.template_manager.search_templates("file")
            assert len(results) == 1
            assert "filesystem" in results

            # Search by tag
            results = self.template_manager.search_templates("sql")
            assert len(results) == 1
            assert "database" in results

    def test_get_template_config_schema(self):
        """Test getting template configuration schema."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "docker_image": "demo:latest",
                "config_schema": {
                    "type": "object",
                    "properties": {"greeting": {"type": "string", "default": "Hello"}},
                },
            }
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            schema = self.template_manager.get_template_config_schema("demo")

        assert schema is not None
        assert schema["type"] == "object"
        assert "greeting" in schema["properties"]

    def test_get_template_tools(self):
        """Test getting template tools."""
        mock_templates = {
            "demo": {
                "name": "Demo Template",
                "docker_image": "demo:latest",
                "tools": [
                    {
                        "name": "say_hello",
                        "description": "Say hello",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        },
                    }
                ],
            }
        }

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            tools = self.template_manager.get_template_tools("demo")

        assert len(tools) == 1
        assert tools[0]["name"] == "say_hello"

    def test_refresh_cache(self):
        """Test cache refresh functionality."""
        # Initial call should populate cache
        mock_templates = {"demo": {"name": "Demo Template"}}

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            templates1 = self.template_manager.list_templates()

        # Second call should use cache
        with patch.object(
            self.template_manager.template_discovery, "discover_templates"
        ) as mock_discover:
            templates2 = self.template_manager.list_templates()
            # discover_templates should not be called again due to cache
            mock_discover.assert_not_called()

        # After refresh, cache should be cleared
        self.template_manager.refresh_cache()

        with patch.object(
            self.template_manager.template_discovery,
            "discover_templates",
            return_value=mock_templates,
        ):
            templates3 = self.template_manager.list_templates()

        assert templates1 == templates2 == templates3

    def test_get_template_path(self):
        """Test getting template file system path."""
        mock_path = Path("/templates/demo")

        with patch.object(
            self.template_manager.template_discovery, "templates_dir", "/templates"
        ):
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "is_dir", return_value=True):
                    path = self.template_manager.get_template_path("demo")

        assert path is not None
        assert str(path).endswith("demo")

    def test_load_template_config(self):
        """Test loading template configuration from file."""
        mock_config = {
            "name": "Demo Template",
            "version": "1.0.0",
            "docker_image": "demo:latest",
        }

        mock_path = Path("/templates/demo")

        with patch.object(
            self.template_manager, "get_template_path", return_value=mock_path
        ):
            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open_read_json(mock_config)):
                    config = self.template_manager.load_template_config("demo")

        assert config == mock_config


@pytest.mark.integration
class TestTemplateManagerIntegration:
    """Integration tests for TemplateManager."""

    def test_template_manager_with_real_templates(self):
        """Test template manager with real template discovery."""
        # This would test with actual template files
        template_manager = TemplateManager(backend_type="mock")
        templates = template_manager.list_templates()

        # Should discover real templates in the system
        assert isinstance(templates, dict)

    def test_template_manager_with_mock_backend(self):
        """Test template manager with mock backend."""
        template_manager = TemplateManager(backend_type="mock")

        # Should be able to list templates without errors
        templates = template_manager.list_templates(include_deployed_status=True)
        assert isinstance(templates, dict)


def mock_open_read_json(json_data):
    """Helper to mock opening and reading JSON files."""
    import json
    from unittest.mock import mock_open

    return mock_open(read_data=json.dumps(json_data))
