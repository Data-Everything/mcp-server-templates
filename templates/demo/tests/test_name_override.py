#!/usr/bin/env python3
"""
Test for name override functionality in demo config.
"""

import os
import unittest

import pytest

from templates.demo.config import DemoServerConfig


@pytest.mark.unit
class TestNameOverride(unittest.TestCase):
    """Test that name overrides work correctly in demo config."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original environment
        self.original_env = dict(os.environ)

    def tearDown(self):
        """Clean up after test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_mcp_override_name_env_var(self):
        """Test that MCP_OVERRIDE_NAME environment variable overrides template name."""
        # Set the override environment variable
        os.environ["MCP_OVERRIDE_NAME"] = "Test Function"

        # Create config instance
        config = DemoServerConfig()

        # Get template data (should include the override)
        template_data = config.get_template_data()

        # Verify the override worked
        self.assertEqual(
            template_data.get("name"),
            "Test Function",
            f"Expected 'Test Function', got '{template_data.get('name')}'",
        )

    def test_override_name_env_var(self):
        """Test that OVERRIDE_NAME environment variable overrides template name."""
        # Set the override environment variable
        os.environ["OVERRIDE_NAME"] = "Simple Override"

        # Create config instance
        config = DemoServerConfig()

        # Get template data (should include the override)
        template_data = config.get_template_data()

        # Verify the override worked
        self.assertEqual(
            template_data.get("name"),
            "Simple Override",
            f"Expected 'Simple Override', got '{template_data.get('name')}'",
        )

    def test_config_dict_name_override(self):
        """Test that name override works via config_dict parameter."""
        # Create config instance with override in config_dict
        config = DemoServerConfig(config_dict={"NAME": "Config Dict Override"})

        # Get template data (should include the override)
        template_data = config.get_template_data()

        # Verify the override worked
        self.assertEqual(
            template_data.get("name"),
            "Config Dict Override",
            f"Expected 'Config Dict Override', got '{template_data.get('name')}'",
        )

    def test_direct_name_override(self):
        """Test that direct name override works via config_dict parameter."""
        # Create config instance with direct name override
        config = DemoServerConfig(config_dict={"name": "Direct Override"})

        # Get template data (should include the override)
        template_data = config.get_template_data()

        # Verify the override worked
        self.assertEqual(
            template_data.get("name"),
            "Direct Override",
            f"Expected 'Direct Override', got '{template_data.get('name')}'",
        )

    def test_description_override(self):
        """Test that description override also works."""
        # Set the override environment variable
        os.environ["MCP_OVERRIDE_DESCRIPTION"] = "Custom Description"

        # Create config instance
        config = DemoServerConfig()

        # Get template data (should include the override)
        template_data = config.get_template_data()

        # Verify the override worked
        self.assertEqual(
            template_data.get("description"),
            "Custom Description",
            f"Expected 'Custom Description', got '{template_data.get('description')}'",
        )

    def test_no_override_uses_default(self):
        """Test that without override, default name is used."""
        # Create config instance without any overrides
        config = DemoServerConfig()

        # Get template data (should use default)
        template_data = config.get_template_data()

        # Should use the default from template.json
        # (We don't check the exact value since it might change, just that it exists)
        self.assertIsNotNone(template_data.get("name"))
        self.assertNotEqual(template_data.get("name"), "")


if __name__ == "__main__":
    unittest.main()
