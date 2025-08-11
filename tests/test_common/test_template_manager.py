"""
Unit tests for TemplateManager in the common module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_template.common.template_manager import TemplateManager
from tests.test_fixtures.sample_data import ERROR_SCENARIOS, SAMPLE_TEMPLATE_DATA


@pytest.mark.unit
class TestTemplateManagerCore:
    """Core functionality tests for TemplateManager."""

    def test_init_default_templates_dir(self):
        """Test initialization with default templates directory."""
        manager = TemplateManager()
        assert manager.template_discovery is not None
        assert manager._templates_cache is None

    def test_init_custom_templates_dir(self):
        """Test initialization with custom templates directory."""
        from pathlib import Path

        custom_dir = Path("/custom/templates")
        manager = TemplateManager(templates_dir=custom_dir)
        assert manager.template_discovery is not None

    @patch("mcp_template.template.utils.discovery.TemplateDiscovery.discover_templates")
    def test_list_templates_success(self, mock_discover):
        """Test successful template listing."""
        # Mock template discovery
        mock_discover.return_value = SAMPLE_TEMPLATE_DATA.copy()

        manager = TemplateManager()
        templates = manager.list_templates()

        assert len(templates) == len(SAMPLE_TEMPLATE_DATA)
        assert all(name in SAMPLE_TEMPLATE_DATA for name in templates.keys())

    @patch("mcp_template.template.utils.discovery.TemplateDiscovery.discover_templates")
    def test_list_templates_empty_directory(self, mock_discover):
        """Test template listing with empty directory."""
        mock_discover.return_value = {}

        manager = TemplateManager()
        templates = manager.list_templates()

        assert templates == {}

    @patch("mcp_template.template.utils.discovery.TemplateDiscovery.discover_templates")
    def test_list_templates_force_refresh(self, mock_discover):
        """Test template listing with force refresh."""
        mock_discover.return_value = SAMPLE_TEMPLATE_DATA.copy()

        manager = TemplateManager()
        # First call should populate cache
        templates1 = manager.list_templates()
        # Second call should use cache (discover_templates called once)
        templates2 = manager.list_templates()
        # Force refresh should call discover_templates again
        templates3 = manager.list_templates(force_refresh=True)

        assert templates1 == templates2 == templates3
        assert mock_discover.call_count == 2  # Initial call + force refresh

    def test_get_template_info_exists(self):
        """Test getting info for existing template."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            info = manager.get_template("demo")

            assert info is not None
            assert info["name"] == "demo"
            assert info["description"] == SAMPLE_TEMPLATE_DATA["demo"]["description"]

    def test_get_template_info_not_found(self):
        """Test getting info for non-existent template."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            info = manager.get_template("non-existent")

            assert info is None

    def test_validate_template_success(self):
        """Test successful template validation."""
        # Create a valid template data structure
        valid_template = {
            "name": "demo",
            "description": "Demo template",
            "image": "demo:latest",
            "config_schema": {"properties": {}},
            "tools": [],
        }

        with patch.object(TemplateManager, "get_template") as mock_get:
            mock_get.return_value = valid_template

            manager = TemplateManager()
            result = manager.validate_template("demo")

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_template_missing_fields(self):
        """Test template validation with missing required fields."""
        # Create template missing required fields
        invalid_template = {
            "description": "Demo template"
            # Missing name, image
        }

        with patch.object(TemplateManager, "get_template") as mock_get:
            mock_get.return_value = invalid_template

            manager = TemplateManager()
            result = manager.validate_template("demo")

            assert result["valid"] is False
            assert len(result["errors"]) > 0
            assert any("Missing required field" in error for error in result["errors"])

    def test_validate_template_not_found(self):
        """Test template validation for non-existent template."""
        with patch.object(TemplateManager, "get_template") as mock_get:
            mock_get.return_value = None

            manager = TemplateManager()
            result = manager.validate_template("non-existent")

            assert result["valid"] is False
            assert any("not found" in error.lower() for error in result["errors"])

    def test_search_templates_by_tag(self):
        """Test template search by tags."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            results = manager.search_templates("demo")

            # Should find templates with "demo" tag
            assert len(results) >= 1
            # Check that results contain templates with matching tags
            for template_id, template_data in results.items():
                tags = template_data.get("tags", [])
                assert (
                    "demo" in tags
                    or "demo" in template_id.lower()
                    or "demo" in template_data.get("description", "").lower()
                )

    def test_search_templates_by_description(self):
        """Test template search by description."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            results = manager.search_templates("development")

            # Should find templates with "development" in description or tags
            assert len(results) >= 1
            for template_id, template_data in results.items():
                found_match = (
                    "development" in template_data.get("description", "").lower()
                    or "development" in template_data.get("tags", [])
                    or "development" in template_id.lower()
                )
                assert found_match

    def test_search_templates_no_results(self):
        """Test template search with no matching results."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            results = manager.search_templates("nonexistent")

            assert len(results) == 0

    def test_search_templates_case_insensitive(self):
        """Test template search is case insensitive."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            results_lower = manager.search_templates("demo")
            results_upper = manager.search_templates("DEMO")
            results_mixed = manager.search_templates("Demo")

            assert len(results_lower) == len(results_upper) == len(results_mixed)


@pytest.mark.unit
class TestTemplateManagerUtilityMethods:
    """Test utility methods of TemplateManager."""

    def test_get_template_categories(self):
        """Test getting templates organized by category."""
        sample_data = SAMPLE_TEMPLATE_DATA.copy()
        # Add category to sample data
        sample_data["demo"]["category"] = "examples"
        sample_data["fastmcp-demo"]["category"] = "fastmcp"
        sample_data["development-tools"]["category"] = "development"

        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = sample_data

            manager = TemplateManager()
            categories = manager.get_template_categories()

            assert "examples" in categories
            assert "fastmcp" in categories
            assert "development" in categories
            assert "demo" in categories["examples"]

    def test_get_template_tags(self):
        """Test getting all unique tags and their templates."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            tags = manager.get_template_tags()

            assert "demo" in tags
            assert "development" in tags
            assert "fastmcp" in tags
            # Check that demo tag maps to correct templates
            assert any("demo" in template_id for template_id in tags["demo"])

    def test_refresh_templates(self):
        """Test refreshing the templates cache."""
        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            manager = TemplateManager()
            # Populate cache
            manager.list_templates()
            assert manager._templates_cache is not None

            # Refresh should clear cache
            manager.refresh_templates()
            assert manager._templates_cache is None

    def test_get_template_stats(self):
        """Test getting template statistics."""
        sample_data = SAMPLE_TEMPLATE_DATA.copy()
        # Add categories to make stats more interesting
        sample_data["demo"]["category"] = "examples"
        sample_data["fastmcp-demo"]["category"] = "fastmcp"

        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = sample_data

            manager = TemplateManager()
            stats = manager.get_template_stats()

            assert "total_templates" in stats
            assert "categories" in stats
            assert "tags" in stats
            assert stats["total_templates"] == len(sample_data)
            assert stats["categories"]["count"] >= 1
            assert stats["tags"]["count"] >= 1

    def test_get_template_path(self):
        """Test getting template path."""
        from pathlib import Path

        expected_path = Path("/templates/demo")

        with patch.object(TemplateManager, "list_templates") as mock_list:
            mock_list.return_value = SAMPLE_TEMPLATE_DATA.copy()

            with patch(
                "mcp_template.template.utils.discovery.TemplateDiscovery.get_template_path"
            ) as mock_path:
                mock_path.return_value = expected_path

                manager = TemplateManager()
                path = manager.get_template_path("demo")

                assert path == expected_path


@pytest.mark.unit
class TestTemplateManagerErrorHandling:
    """Test error handling in TemplateManager."""

    def test_handle_file_permission_error(self):
        """Test handling of file permission errors."""
        with patch(
            "pathlib.Path.read_text", side_effect=PermissionError("Permission denied")
        ):
            manager = TemplateManager()
            metadata = manager._load_template_metadata("demo")

            assert metadata is None

    def test_handle_os_error(self):
        """Test handling of OS errors."""
        with patch("pathlib.Path.iterdir", side_effect=OSError("OS error")):
            manager = TemplateManager()
            templates = manager.list_templates()

            assert templates == []

    def test_handle_unicode_decode_error(self):
        """Test handling of unicode decode errors."""
        with patch(
            "pathlib.Path.read_text",
            side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte"),
        ):
            manager = TemplateManager()
            metadata = manager._load_template_metadata("demo")

            assert metadata is None


@pytest.mark.integration
class TestTemplateManagerIntegration:
    """Integration tests for TemplateManager."""

    def test_real_template_discovery(self, temp_workspace):
        """Test template discovery with real file system."""
        templates_dir = temp_workspace / "templates"

        manager = TemplateManager(templates_dir=str(templates_dir))
        templates = manager.list_templates()

        # Should find the templates created in temp_workspace fixture
        assert len(templates) == 0  # Should be empty if no templates created
        for template in templates:
            assert "name" in template
            assert "version" in template

    def test_template_validation_with_real_files(self, temp_workspace):
        """Test template validation with actual template files."""
        templates_dir = temp_workspace / "templates"

        # Find a template to validate
        manager = TemplateManager(templates_dir=str(templates_dir))
        templates = manager.list_templates()

        if templates:
            template_name = templates[0]["name"]
            result = manager.validate_template(template_name)

            assert "valid" in result
            assert "errors" in result
            assert "warnings" in result

    def test_search_functionality_with_real_data(self, temp_workspace):
        """Test search functionality with real template data."""
        templates_dir = temp_workspace / "templates"

        manager = TemplateManager(templates_dir=str(templates_dir))

        # Test search with known terms
        demo_results = manager.search_templates("demo")
        all_results = manager.search_templates("")  # Should return all templates

        assert len(demo_results) <= len(all_results)


@pytest.mark.slow
class TestTemplateManagerPerformance:
    """Performance tests for TemplateManager."""

    def test_large_template_collection_performance(self, large_template_collection):
        """Test performance with large template collections."""
        import time

        manager = TemplateManager(templates_dir=str(large_template_collection))

        # Test list_templates performance
        start_time = time.time()
        templates = manager.list_templates()
        list_time = time.time() - start_time

        assert list_time < 5.0  # Should complete within 5 seconds
        assert len(templates) == 100  # Should find all 100 templates

        # Test search performance
        start_time = time.time()
        results = manager.search_templates("template")
        search_time = time.time() - start_time

        assert search_time < 2.0  # Should complete within 2 seconds
        assert len(results) > 0  # Should find matching templates
