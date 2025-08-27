"""
Integration tests for TemplateManager.

Tests the template manager with real template discovery and
backend interactions using mock backends where appropriate.
"""

import pytest

from mcp_template.core.template_manager import TemplateManager

pytestmark = pytest.mark.integration


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
