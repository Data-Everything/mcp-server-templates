#!/usr/bin/env python3
"""
Test the demo server using the FastMCP client
"""

import asyncio

from fastmcp import Client


async def test_demo_server():
    """Test the demo server using FastMCP client."""

    # Create a client that connects to our running server via script
    client = Client("templates/demo/main.py")

    try:
        async with client:
            print("🧪 Testing demo server with FastMCP client...")

            # Test basic connection
            await client.ping()
            print("✅ Server ping successful!")

            # List available tools
            tools = await client.list_tools()
            print(f"🔧 Found {len(tools)} tools:")
            for tool in tools:
                print(f"  • {tool.name}: {tool.description}")

            # Test say_hello tool
            if any(tool.name == "say_hello" for tool in tools):
                print("\n📤 Testing say_hello tool...")
                result = await client.call_tool("say_hello", {"name": "FastMCP Tester"})
                print(f"✅ Tool result: {result}")

                print("\n📤 Testing say_hello without name...")
                result2 = await client.call_tool("say_hello", {})
                print(f"✅ Tool result: {result2}")

            # Test get_server_info tool
            if any(tool.name == "get_server_info" for tool in tools):
                print("\n📤 Testing get_server_info tool...")
                result = await client.call_tool("get_server_info", {})
                print(f"✅ Server info: {result}")

            print("\n🎉 All tests passed! Demo server is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_demo_server())
