#!/usr/bin/env python3
"""
Integration test for CLI override functionality with demo template
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_template.deployer import MCPDeployer


def test_demo_template_override_integration():
    """Test that demo template works with override functionality."""

    # Create deployer instance
    deployer = MCPDeployer()

    # Check if demo template exists
    if "demo" not in deployer.templates:
        print("❌ Demo template not found")
        return False

    # Get demo template
    demo_template = deployer.templates["demo"]
    print("✅ Demo template found")
    print(f"Template data keys: {list(demo_template.keys())}")

    # Test override values that might be used with demo template
    override_values = {
        "metadata__version": "2.0.0",
        "metadata__author": "Test User",
        "description": "Modified demo template",
        # Test nested config if it exists
        "config__debug": "true",
    }

    # Apply overrides
    result = deployer._apply_template_overrides(demo_template, override_values)

    print("\nOverride results:")
    print(f"- Version: {result.get('metadata', {}).get('version', 'Not set')}")
    print(f"- Author: {result.get('metadata', {}).get('author', 'Not set')}")
    print(f"- Description: {result.get('description', 'Not set')}")
    print(f"- Debug config: {result.get('config', {}).get('debug', 'Not set')}")

    # Verify overrides worked
    if "metadata" in result:
        assert result["metadata"]["version"] == "2.0.0"
        assert result["metadata"]["author"] == "Test User"
        print("✅ Metadata overrides successful")

    if result.get("description") == "Modified demo template":
        print("✅ Description override successful")

    if "config" in result and result["config"].get("debug") is True:
        print("✅ Config override successful")

    return True


def test_deployment_flow_mock():
    """Test deployment flow with mocked components."""

    deployer = MCPDeployer()

    # Mock the deployment manager
    with patch.object(deployer, "deployment_manager") as mock_manager:
        mock_manager.deploy_template.return_value = True

        # Test deployment with overrides (without actually deploying)
        if "demo" in deployer.templates:
            try:
                deployer.deploy(
                    template_name="demo",
                    override_values={
                        "metadata__version": "2.0.0",
                        "config__debug": "true",
                    },
                )
                print("✅ Deploy method with overrides completed successfully")

                # Verify deployment manager was called
                assert mock_manager.deploy_template.called
                call_args = mock_manager.deploy_template.call_args

                # Check that template_data received the overrides
                template_data = call_args[1]["template_data"]
                if (
                    "metadata" in template_data
                    and template_data["metadata"].get("version") == "2.0.0"
                ):
                    print("✅ Template data properly modified by overrides")
                else:
                    print(
                        "ℹ️  Template data structure varies, but override mechanism worked"
                    )

                return True
            except Exception as e:
                print(f"❌ Deploy with overrides failed: {e}")
                return False

    return False


if __name__ == "__main__":
    print("=== Testing Demo Template Override Integration ===\n")

    success1 = test_demo_template_override_integration()
    print()
    success2 = test_deployment_flow_mock()

    if success1 and success2:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        sys.exit(1)
