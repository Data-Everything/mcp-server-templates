#!/usr/bin/env python3
"""
Integration test to verify that the name override works in deployment scenario.
"""

import os
import unittest
from unittest.mock import patch

import pytest


@pytest.mark.integration
class TestNameOverrideIntegration(unittest.TestCase):
    """Test name override in full deployment integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.original_env = dict(os.environ)

    def tearDown(self):
        """Clean up after test."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_demo_server_receives_name_override(self):
        """Test that the demo server config correctly processes the name override."""

        # Set up environment like the deployer would
        os.environ["MCP_OVERRIDE_NAME"] = "Test Function"

        # Import and test the demo config directly
        from templates.demo.config import DemoServerConfig

        config = DemoServerConfig()
        template_data = config.get_template_data()

        # Verify the name was overridden
        self.assertEqual(template_data.get("name"), "Test Function")

        print(f"✅ Demo config received name override: {template_data.get('name')}")

        # Verify server would use the overridden name
        from templates.demo.server import DemoMCPServer

        # Create server instance (without actually running FastMCP)
        with patch("templates.demo.server.FastMCP") as mock_fastmcp:
            DemoMCPServer()

            # Verify FastMCP was initialized with the correct name
            mock_fastmcp.assert_called_once()
            call_kwargs = mock_fastmcp.call_args[1]
            self.assertEqual(call_kwargs["name"], "Test Function")

            print(f"✅ Server initialized with correct name: {call_kwargs['name']}")


if __name__ == "__main__":
    unittest.main()
