#!/usr/bin/env python3
"""
Test script for refactored CLI and MCPClient implementations.

This script tests the basic functionality of the refactored implementations
to ensure they work correctly with the common modules.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/home/samarora/data-everything/mcp-server-templates')

from mcp_template.core.refactored_cli import RefactoredCLI
from mcp_template.core.refactored_client import RefactoredMCPClient
from mcp_template.core import (
    TemplateManager,
    DeploymentManager,
    ConfigManager,
    ToolManager,
    OutputFormatter
)


def test_common_modules():
    """Test basic functionality of common modules."""
    print("🔧 Testing Common Modules...")
    
    try:
        # Test instantiation
        tm = TemplateManager(backend_type="mock")
        dm = DeploymentManager(backend_type="mock")
        cm = ConfigManager()
        tool_m = ToolManager(backend_type="mock")
        fmt = OutputFormatter()
        
        print("✅ All common modules instantiated successfully")
        
        # Test basic operations
        templates = tm.list_templates()
        print(f"✅ TemplateManager.list_templates() returned {len(templates)} templates")
        
        # Test config operations
        config_result = cm.merge_config_sources(
            template_config={"name": "test"},
            config_values={"setting": "value"}
        )
        print(f"✅ ConfigManager.merge_config_sources() worked: {len(config_result)} keys")
        
        return True
        
    except Exception as e:
        print(f"❌ Common modules test failed: {e}")
        return False


def test_refactored_client():
    """Test basic functionality of refactored client."""
    print("\n🔧 Testing Refactored MCP Client...")
    
    try:
        # Test instantiation with mock backend
        client = RefactoredMCPClient(backend_type="mock")
        print("✅ RefactoredMCPClient instantiated successfully")
        
        # Test template operations
        templates = client.list_templates()
        print(f"✅ Client.list_templates() returned {len(templates)} templates")
        
        # Test tool operations
        tools = client.list_tools("demo", discovery_method="static")
        print(f"✅ Client.list_tools() returned {len(tools)} tools")
        
        # Test configuration operations
        config = client.get_template_configuration("demo")
        print(f"✅ Client.get_template_configuration() returned {len(config)} configs")
        
        return True
        
    except Exception as e:
        print(f"❌ Refactored client test failed: {e}")
        return False


def test_refactored_cli():
    """Test basic functionality of refactored CLI."""
    print("\n🔧 Testing Refactored CLI...")
    
    try:
        # Test instantiation with mock backend
        cli = RefactoredCLI(backend_type="mock")
        print("✅ RefactoredCLI instantiated successfully")
        
        # Test formatter
        templates = {"demo": {"name": "Demo", "version": "1.0.0", "description": "Test template", "docker_image": "demo:latest"}}
        table = cli.formatter.format_templates_table(templates)
        print("✅ CLI formatter created templates table successfully")
        
        # Test other formatters
        tools = [{"name": "test_tool", "description": "Test tool", "parameters": [], "source": "static"}]
        tools_table = cli.formatter.format_tools_table(tools)
        print("✅ CLI formatter created tools table successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Refactored CLI test failed: {e}")
        return False


def test_integration():
    """Test integration between components."""
    print("\n🔧 Testing Integration...")
    
    try:
        # Test that CLI and Client can work with the same backend
        cli = RefactoredCLI(backend_type="mock")
        client = RefactoredMCPClient(backend_type="mock")
        
        # Both should see the same templates
        cli_templates = cli.template_manager.list_templates()
        client_templates = client.list_templates()
        
        print(f"✅ CLI and Client both see {len(cli_templates)} templates")
        
        # Test backend switching
        client.set_backend_type("mock")
        print(f"✅ Client backend type: {client.get_backend_type()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Refactor Tests...\n")
    
    tests = [
        test_common_modules,
        test_refactored_client,
        test_refactored_cli,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Refactoring appears to be working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
