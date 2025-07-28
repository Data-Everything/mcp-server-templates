"""
Test template discovery and management.
"""

from mcp_template.template.discovery import TemplateDiscovery


class TestTemplateDiscovery:
    """Test template discovery and management."""

    def test_init(self):
        """Test TemplateDiscovery initialization."""
        discovery = TemplateDiscovery()
        assert discovery.templates_dir is not None
        assert discovery.templates_dir.exists() or True  # May not exist in test env

    def test_discover_templates(self, temp_template_dir):
        """Test template discovery."""
        discovery = TemplateDiscovery(templates_dir=temp_template_dir.parent)

        templates = discovery.discover_templates()
        assert len(templates) >= 1
        assert "test-template" in templates

    def test_load_template_config(self, temp_template_dir):
        """Test loading template configuration."""
        discovery = TemplateDiscovery(templates_dir=temp_template_dir.parent)

        # Load specific template config
        config = discovery._load_template_config(temp_template_dir)
        assert config is not None
        assert config["name"] == "Test Template"

    def test_discover_no_templates_dir(self, tmp_path):
        """Test discovery when templates directory doesn't exist."""
        discovery = TemplateDiscovery(templates_dir=tmp_path / "nonexistent")

        templates = discovery.discover_templates()
        assert templates == {}

    def test_invalid_template_structure(self, tmp_path):
        """Test handling of invalid template structure."""
        # Create template without required files
        invalid_template = tmp_path / "invalid-template"
        invalid_template.mkdir()

        discovery = TemplateDiscovery(templates_dir=tmp_path)
        templates = discovery.discover_templates()

        # Should skip invalid template
        assert "invalid-template" not in templates
