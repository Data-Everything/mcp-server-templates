#!/usr/bin/env python3
"""
Test script for CLI override functionality
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_template.deployer import MCPDeployer


def test_template_overrides():
    """Test template data override functionality"""

    # Create a mock template structure
    template_data = {
        "name": "test-template",
        "tools": [
            {"name": "tool1", "type": "function"},
            {"name": "tool2", "type": "resource"},
        ],
        "metadata": {"version": "1.0.0", "description": "Test template"},
        "config": {"debug": False, "port": 8080},
    }

    # Test override values with double underscore notation
    override_values = {
        "metadata__version": "2.0.0",
        "metadata__author": "Test Author",
        "config__debug": "true",
        "config__port": "9090",
        "tools__0__enabled": "false",
        "new_field": "test_value",
    }

    # Create deployer instance
    deployer = MCPDeployer()

    # Apply overrides
    result = deployer._apply_template_overrides(template_data, override_values)

    # Verify results
    print("Original template:")
    print(json.dumps(template_data, indent=2))
    print("\nOverride values:")
    print(json.dumps(override_values, indent=2))
    print("\nResult after overrides:")
    print(json.dumps(result, indent=2))

    # Assertions
    assert result["metadata"]["version"] == "2.0.0"
    assert result["metadata"]["author"] == "Test Author"
    assert result["config"]["debug"] is True  # Should be converted to boolean
    assert result["config"]["port"] == 9090  # Should be converted to int
    assert result["tools"][0]["enabled"] is False  # Should be converted to boolean
    assert result["new_field"] == "test_value"

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_template_overrides()
