"""
Template Manager - Centralized template operations.

This module provides a unified interface for template discovery, validation,
and metadata operations, consolidating functionality from CLI and MCPClient.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp_template.backends import get_backend
from mcp_template.template.utils.discovery import TemplateDiscovery

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Centralized template management operations.

    Provides unified interface for template discovery, validation, and metadata
    operations that can be shared between CLI and MCPClient implementations.
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize the template manager."""
        self.template_discovery = TemplateDiscovery()
        self.backend = get_backend(backend_type)
        self._template_cache = {}
        self._cache_valid = False

    def list_templates(
        self, include_deployed_status: bool = False, filter_deployed_only: bool = False
    ) -> Dict[str, Dict]:
        """
        List all available templates with optional deployment status.

        Args:
            include_deployed_status: Whether to check and include deployment status
            filter_deployed_only: Whether to filter to only deployed templates

        Returns:
            Dictionary mapping template names to template metadata
        """
        try:
            # Get base template information
            if not self._cache_valid:
                self._template_cache = self.template_discovery.discover_templates()
                self._cache_valid = True

            templates = self._template_cache.copy()

            # Add deployment status if requested
            if include_deployed_status:
                try:
                    # Get all deployments and filter by template
                    all_deployments = self.backend.list_deployments()
                    for template_name in templates:
                        try:
                            # Filter deployments for this specific template
                            template_deployments = [
                                d
                                for d in all_deployments
                                if (
                                    d.get("template") == template_name
                                    or d.get("Template") == template_name
                                )
                            ]

                            # Filter to only running deployments for the count and status
                            running_deployments = [
                                d
                                for d in template_deployments
                                if d.get("status") == "running"
                            ]

                            templates[template_name]["deployed"] = (
                                len(running_deployments) > 0
                            )
                            templates[template_name]["deployment_count"] = len(
                                running_deployments
                            )
                            templates[template_name][
                                "deployments"
                            ] = template_deployments
                        except Exception as e:
                            logger.warning(
                                f"Failed to process deployment status for {template_name}: {e}"
                            )
                            templates[template_name]["deployed"] = False
                            templates[template_name]["deployment_count"] = 0
                            templates[template_name]["deployments"] = []
                except Exception as e:
                    logger.warning(f"Failed to get deployment status: {e}")
                    # Set default values for all templates
                    for template_name in templates:
                        templates[template_name]["deployed"] = False
                        templates[template_name]["deployment_count"] = 0
                        templates[template_name]["deployments"] = []

            # Filter to deployed only if requested
            if filter_deployed_only:
                templates = {
                    name: info
                    for name, info in templates.items()
                    if info.get("deployed", False)
                }

            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return {}

    def get_template_info(self, template_id: str) -> Optional[Dict]:
        """
        Get detailed information for a specific template.

        Args:
            template_id: The template identifier

        Returns:
            Template metadata dictionary or None if not found
        """
        try:
            templates = self.list_templates()
            return templates.get(template_id)
        except Exception as e:
            logger.error(f"Failed to get template info for {template_id}: {e}")
            return None

    def validate_template(self, template_id: str) -> bool:
        """
        Validate that a template exists and is properly structured.

        Args:
            template_id: The template identifier

        Returns:
            True if template is valid, False otherwise
        """
        try:
            template_info = self.get_template_info(template_id)
            if not template_info:
                return False

            # Check required fields
            required_fields = ["name", "docker_image"]
            for field in required_fields:
                if field not in template_info:
                    logger.warning(
                        f"Template {template_id} missing required field: {field}"
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to validate template {template_id}: {e}")
            return False

    def search_templates(self, query: str) -> Dict[str, Dict]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query string

        Returns:
            Dictionary of matching templates
        """
        try:
            all_templates = self.list_templates()
            matching_templates = {}

            query_lower = query.lower()

            for name, info in all_templates.items():
                # Search in name
                if query_lower in name.lower():
                    matching_templates[name] = info
                    continue

                # Search in description
                description = info.get("description", "").lower()
                if query_lower in description:
                    matching_templates[name] = info
                    continue

                # Search in tags
                tags = info.get("tags", [])
                if any(query_lower in tag.lower() for tag in tags):
                    matching_templates[name] = info
                    continue

            return matching_templates

        except Exception as e:
            logger.error(f"Failed to search templates: {e}")
            return {}

    def get_template_config_schema(self, template_id: str) -> Optional[Dict]:
        """
        Get the configuration schema for a template.

        Args:
            template_id: The template identifier

        Returns:
            Configuration schema dictionary or None if not found
        """
        try:
            template_info = self.get_template_info(template_id)
            if not template_info:
                return None

            return template_info.get("config_schema", {})

        except Exception as e:
            logger.error(f"Failed to get config schema for {template_id}: {e}")
            return None

    def get_template_tools(self, template_id: str) -> List[Dict]:
        """
        Get the tools defined for a template.

        Args:
            template_id: The template identifier

        Returns:
            List of tool definitions
        """
        try:
            template_info = self.get_template_info(template_id)
            if not template_info:
                return []

            return template_info.get("tools", [])

        except Exception as e:
            logger.error(f"Failed to get tools for {template_id}: {e}")
            return []

    def refresh_cache(self):
        """Force refresh of the template cache."""
        self._cache_valid = False
        self._template_cache = {}

    def get_template_path(self, template_id: str) -> Optional[Path]:
        """
        Get the file system path for a template.

        Args:
            template_id: The template identifier

        Returns:
            Path to template directory or None if not found
        """
        try:
            # Use the template discovery to find the path
            templates_dir = Path(self.template_discovery.templates_dir)
            template_path = templates_dir / template_id

            if template_path.exists() and template_path.is_dir():
                return template_path

            return None

        except Exception as e:
            logger.error(f"Failed to get template path for {template_id}: {e}")
            return None

    def load_template_config(self, template_id: str) -> Dict[str, Any]:
        """
        Load the complete template configuration from template.json.

        Args:
            template_id: The template identifier

        Returns:
            Complete template configuration dictionary
        """
        try:
            template_path = self.get_template_path(template_id)
            if not template_path:
                return {}

            config_file = template_path / "template.json"
            if not config_file.exists():
                return {}

            with open(config_file, "r") as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Failed to load template config for {template_id}: {e}")
            return {}
