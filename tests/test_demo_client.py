#!/usr/bin/env python3
"""
Simple MCP client to test the demo server functionality.
"""
import asyncio
import json
import subprocess
import sys
from typing import Any, Dict

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("MCP client library not found. Install with:")
    print("pip install mcp")
    sys.exit(1)


class MCPTestClient:
    """Simple MCP client for testing servers."""

    def __init__(self, container_name: str):
        self.container_name = container_name
        self.server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", container_name, "python", "-m", "src.server"],
        )

    async def test_server(self):
        """Test the MCP server functionality."""
        print(f"🧪 Testing MCP server in container: {self.container_name}")
        print("-" * 60)

        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    print("✅ Server connection established")

                    # List available tools
                    tools = await session.list_tools()
                    print(f"\n🔧 Available tools ({len(tools.tools)}):")
                    for tool in tools.tools:
                        print(f"  • {tool.name}: {tool.description}")

                    # Test each tool
                    print("\n🚀 Testing tools:")

                    # Test say_hello without name
                    print("\n1. Testing say_hello() without name:")
                    result = await session.call_tool("say_hello", {})
                    print(f"   Result: {result.content[0].text}")

                    # Test say_hello with name
                    print("\n2. Testing say_hello() with name 'Alice':")
                    result = await session.call_tool("say_hello", {"name": "Alice"})
                    print(f"   Result: {result.content[0].text}")

                    # Test get_server_info
                    print("\n3. Testing get_server_info():")
                    result = await session.call_tool("get_server_info", {})
                    info = json.loads(result.content[0].text)
                    print("   Server Info:")
                    for key, value in info.items():
                        if isinstance(value, list):
                            print(f"     {key}:")
                            for item in value:
                                print(f"       - {item}")
                        else:
                            print(f"     {key}: {value}")

                    print("\n✅ All tests completed successfully!")

        except Exception as e:
            print(f"❌ Error testing server: {e}")
            return False

        return True


async def main():
    """Main function to test the demo server."""
    # Find running demo containers
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "ancestor=dataeverything/mcp-demo:latest",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        containers = result.stdout.strip().split("\n")
        containers = [c for c in containers if c]  # Remove empty strings

        if not containers:
            print("❌ No demo containers found. Please deploy the demo server first:")
            print("   python -m mcp_template deploy demo --config hello_from=YourName")
            return

        # Use the most recent container
        container_name = containers[0]
        print(f"📦 Found demo container: {container_name}")

        # Test the server
        client = MCPTestClient(container_name)
        success = await client.test_server()

        if success:
            print("\n🎉 Demo server test completed successfully!")
            print("\n📋 Next steps:")
            print(
                "   1. Add to Claude Desktop: see docs/guides/claude-desktop-setup.md"
            )
            print("   2. Add to VS Code: see docs/guides/vscode-setup.md")
            print("   3. Use with Python: see docs/guides/python-integration.md")
            print(f"   4. Container name for config: {container_name}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking containers: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
