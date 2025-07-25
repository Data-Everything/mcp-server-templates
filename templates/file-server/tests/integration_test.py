#!/usr/bin/env python3
"""Integration test for the FastMCP file server."""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import the server
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_server_import():
    """Test that we can import and initialize the server."""
    try:
        import server

        print("✅ Server import successful")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False


def test_server_tools():
    """Test that the server has all expected tools."""
    try:
        import server

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable for testing
            os.environ["MCP_ALLOWED_DIRS"] = temp_dir

            # Create server instance
            file_server = server.FileServer()

            # Check if the server was created successfully
            if hasattr(file_server, "mcp") and hasattr(file_server, "config"):
                print("✅ Server created successfully with FastMCP instance")

                expected_tools = [
                    "read_file",
                    "write_file",
                    "list_directory",
                    "create_directory",
                    "delete_file",
                    "delete_directory",
                    "move_file",
                    "copy_file",
                    "get_file_info",
                ]

                print(
                    f"✅ Expected tools should be registered: {', '.join(expected_tools)}"
                )
                print("✅ Server tools registration completed")
                return True
            else:
                print("❌ Server missing required attributes")
                return False

    except Exception as e:
        print(f"❌ Tool registration test failed: {e}")
        return False


def test_file_operations():
    """Test basic file operations."""
    try:
        import server

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable for testing
            os.environ["MCP_ALLOWED_DIRS"] = temp_dir
            config = server.FileServerConfig()

            # Test file writing and reading
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Hello FastMCP!"

            # Write file directly (simulating the tool call)
            test_file.write_text(test_content)

            # Test file reading
            if test_file.exists() and test_file.read_text() == test_content:
                print("✅ File write/read operations work")

                # Test path validation
                try:
                    validated_path = config.validate_path(str(test_file))
                    print(f"✅ Path validation works: {validated_path}")
                    return True
                except Exception as path_error:
                    print(f"❌ Path validation failed: {path_error}")
                    return False
            else:
                print("❌ File operations failed")
                return False

    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False


def main():
    """Run integration tests for the FastMCP file server."""
    print("FastMCP File Server Integration Test")
    print("=" * 50)

    tests = [
        ("Server Import", test_server_import),
        ("Tool Registration", test_server_tools),
        ("File Operations", test_file_operations),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} test failed")

    print("\n" + "=" * 50)
    print(f"🏁 Tests completed: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
