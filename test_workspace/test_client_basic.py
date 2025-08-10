#!/usr/bin/env python3
"""
Test script to verify MCP Client functionality.
This script tests the basic client functionality without Docker dependencies.
"""

import asyncio
import os
import sys

# Add parent directory to path to import mcp_template
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_template.client import MCPClient


async def test_client_basic_functionality():
    """Test basic client functionality with mock backend."""
    print("🧪 Testing MCP Client basic functionality...")

    try:
        # Test with mock backend to avoid Docker dependencies
        async with MCPClient(backend_type="mock") as client:
            print("✅ Client initialization successful")

            # Test template listing
            templates = client.list_templates()
            print(f"📦 Available templates: {list(templates.keys())}")

            # Test server listing (should be empty initially)
            servers = client.list_servers()
            print(f"🖥️  Running servers: {len(servers)}")

            # Test getting template info
            if "demo" in templates:
                demo_info = client.get_template_info("demo")
                print(
                    f"ℹ️  Demo template info: {demo_info['name'] if demo_info else 'Not found'}"
                )

            print("✅ All basic client tests passed!")
            return True

    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False


def test_client_import():
    """Test that client can be imported properly."""
    print("🔍 Testing MCP Client import...")

    try:
        from mcp_template import MCPClient

        print("✅ MCPClient import successful")

        # Test instantiation
        client = MCPClient(backend_type="mock")
        print("✅ MCPClient instantiation successful")

        # Test basic attributes
        assert hasattr(client, "list_templates")
        assert hasattr(client, "list_servers")
        assert hasattr(client, "start_server")
        assert hasattr(client, "stop_server")
        assert hasattr(client, "list_tools")
        assert hasattr(client, "call_tool")
        print("✅ MCPClient has all expected methods")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting MCP Client tests...\n")

    # Test 1: Import and basic instantiation
    import_success = test_client_import()
    print()

    # Test 2: Basic functionality
    functionality_success = await test_client_basic_functionality()
    print()

    if import_success and functionality_success:
        print("🎉 All tests passed! MCP Client is working correctly.")
        return 0
    else:
        print("💥 Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
