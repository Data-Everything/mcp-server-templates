"""
Template management functionality shared between CLI and MCPClient.

This module provides centralized template discovery, loading, validation,
and management operations that can be used by both the CLI interface
and the programmatic MCPClient API.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Centralized template management for CLI and MCPClient.

    Provides common functionality for template discovery, loading,
    validation, and management operations.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            templates_dir: Optional custom templates directory path
        """
        self.template_discovery = TemplateDiscovery(templates_dir)
        self._templates_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def list_templates(
        self,
        force_refresh: bool = False,
        include_deployment_status: bool = False,
        deployed_only: bool = False,
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all available MCP server templates.

        Args:
            force_refresh: Whether to force refresh the template cache
            include_deployment_status: Whether to include deployment status info
            deployed_only: Whether to only return deployed templates

        Returns:
            Dictionary mapping template_id to template information
        """
        if force_refresh or self._templates_cache is None:
            self._templates_cache = self.template_discovery.discover_templates()

        templates = self._templates_cache.copy()

        if include_deployment_status:
            # This would need deployment manager integration
            # For now, we'll add a placeholder
            for _, template_data in templates.items():
                template_data["deployment_status"] = "unknown"
                template_data["running_instances"] = []

        if deployed_only:
            # Filter to only deployed templates
            # This would need deployment manager integration
            # For now, return empty dict as placeholder
            return {}

        return templates

    def get_template(
        self, template_id: str, force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific template.

        Args:
            template_id: ID of the template to retrieve
            force_refresh: Whether to force refresh the template cache

        Returns:
            Template information or None if not found
        """
        templates = self.list_templates(force_refresh=force_refresh)
        return templates.get(template_id)

    def get_template_path(self, template_id: str) -> Optional[Path]:
        """
        Get the filesystem path to a specific template.

        Args:
            template_id: ID of the template

        Returns:
            Path to the template directory or None if not found
        """
        return self.template_discovery.get_template_path(template_id)

    def validate_template(self, template_id: str) -> Dict[str, Any]:
        """
        Validate a template configuration.

        Args:
            template_id: ID of the template to validate

        Returns:
            Dictionary with validation results:
            - valid: bool - Whether template is valid
            - errors: List[str] - List of validation errors
            - warnings: List[str] - List of validation warnings
        """
        result = {"valid": False, "errors": [], "warnings": []}

        # Check if template exists
        template_data = self.get_template(template_id)
        if not template_data:
            result["errors"].append(f"Template '{template_id}' not found")
            return result

        # Check for required fields
        required_fields = ["name", "description", "image"]
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                result["errors"].append(f"Missing required field: {field}")

        # Check Docker image format
        image = template_data.get("image", "")
        if image and ":" not in image:
            result["warnings"].append(
                "Docker image should include a tag (e.g., ':latest')"
            )

        # Check config schema validity
        config_schema = template_data.get("config_schema", {})
        if config_schema:
            try:
                # Basic JSON schema validation
                if "properties" not in config_schema:
                    result["warnings"].append(
                        "Config schema missing 'properties' field"
                    )
            except (ValueError, TypeError, KeyError) as e:
                result["errors"].append(f"Invalid config schema: {str(e)}")

        # Check tools configuration
        tools = template_data.get("tools", [])
        if tools and not isinstance(tools, list):
            result["errors"].append("Tools configuration must be a list")

        # Set valid status based on errors
        result["valid"] = len(result["errors"]) == 0

        return result

    def search_templates(
        self, query: str, search_fields: Optional[List[str]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Search templates by query string.

        Args:
            query: Search query string
            search_fields: List of fields to search in (default: name, description, tags)

        Returns:
            Dictionary of matching templates
        """
        if search_fields is None:
            search_fields = ["name", "description", "tags", "category"]

        templates = self.list_templates()
        matching_templates = {}
        query_lower = query.lower()

        for template_id, template_data in templates.items():
            if self._template_matches_query(
                template_id, template_data, query_lower, search_fields
            ):
                matching_templates[template_id] = template_data

        return matching_templates

    def _template_matches_query(
        self,
        template_id: str,
        template_data: Dict[str, Any],
        query_lower: str,
        search_fields: List[str],
    ) -> bool:
        """Check if template matches the search query."""
        # Search in template ID
        if query_lower in template_id.lower():
            return True

        # Search in specified fields
        for field in search_fields:
            if self._field_matches_query(template_data, field, query_lower):
                return True

        return False

    def _field_matches_query(
        self, template_data: Dict[str, Any], field: str, query_lower: str
    ) -> bool:
        """Check if a specific field matches the search query."""
        if field not in template_data:
            return False

        field_value = template_data[field]

        if isinstance(field_value, str):
            return query_lower in field_value.lower()
        elif isinstance(field_value, list):
            # Search in list items (like tags)
            return any(
                isinstance(item, str) and query_lower in item.lower()
                for item in field_value
            )

        return False

    def get_template_categories(self) -> Dict[str, List[str]]:
        """
        Get templates organized by category.

        Returns:
            Dictionary mapping category names to lists of template IDs
        """
        templates = self.list_templates()
        categories = {}

        for template_id, template_data in templates.items():
            category = template_data.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append(template_id)

        return categories

    def get_template_tags(self) -> Dict[str, List[str]]:
        """
        Get all unique tags and the templates that use them.

        Returns:
            Dictionary mapping tag names to lists of template IDs
        """
        templates = self.list_templates()
        tags_map = {}

        for template_id, template_data in templates.items():
            tags = template_data.get("tags", [])
            for tag in tags:
                if tag not in tags_map:
                    tags_map[tag] = []
                tags_map[tag].append(template_id)

        return tags_map

    def refresh_templates(self) -> None:
        """Refresh the templates cache by forcing a rediscovery."""
        self._templates_cache = None
        logger.info("Template cache refreshed")

    def get_template_stats(self) -> Dict[str, Any]:
        """
        Get statistics about available templates.

        Returns:
            Dictionary with template statistics
        """
        templates = self.list_templates()
        categories = self.get_template_categories()
        tags = self.get_template_tags()

        return {
            "total_templates": len(templates),
            "categories": {"count": len(categories), "list": list(categories.keys())},
            "tags": {"count": len(tags), "list": list(tags.keys())},
            "templates_by_category": {
                category: len(template_list)
                for category, template_list in categories.items()
            },
        }
