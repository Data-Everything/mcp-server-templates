#!/usr/bin/env python3
"""
Test script to validate that name override works correctly.
"""

import os
import sys
from pathlib import Path

# Add templates directory to Python path
templates_path = Path(__file__).parent / "templates" / "demo"
sys.path.insert(0, str(templates_path))

from config import DemoServerConfig


def test_name_override():
    """Test that MCP_OVERRIDE_NAME environment variable overrides the template name."""

    # Set the override environment variable
    os.environ["MCP_OVERRIDE_NAME"] = "Test Function"

    try:
        # Create config instance
        config = DemoServerConfig()

        # Get template data (should include the override)
        template_data = config.get_template_data()

        print(f"Template name: {template_data.get('name')}")

        # Verify the override worked
        assert (
            template_data.get("name") == "Test Function"
        ), f"Expected 'Test Function', got '{template_data.get('name')}'"

        print("✅ Name override test PASSED!")

    finally:
        # Clean up environment variable
        if "MCP_OVERRIDE_NAME" in os.environ:
            del os.environ["MCP_OVERRIDE_NAME"]


def test_name_override_case_insensitive():
    """Test that name override works with different case variations."""

    # Test with lowercase override key
    os.environ["MCP_OVERRIDE_name"] = "Lowercase Test"

    try:
        config = DemoServerConfig()
        template_data = config.get_template_data()

        print(f"Template name (lowercase key): {template_data.get('name')}")
        assert (
            template_data.get("name") == "Lowercase Test"
        ), f"Expected 'Lowercase Test', got '{template_data.get('name')}'"

        print("✅ Lowercase name override test PASSED!")

    finally:
        if "MCP_OVERRIDE_name" in os.environ:
            del os.environ["MCP_OVERRIDE_name"]


if __name__ == "__main__":
    test_name_override()
    test_name_override_case_insensitive()
    print("All tests passed!")
