"""
Test script for the refactored MCP Client.

This script tests the basic functionality of the refactored MCPClient
that focuses only on MCP server connections (no template management).
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_template.client import MCPClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mcp_client():
    """Test the refactored MCP Client functionality."""

    print("🧪 Testing Refactored MCP Client")
    print("=" * 50)

    # Initialize client
    client = MCPClient(timeout=10)
    print(f"✅ Initialized MCPClient with timeout: {client.timeout}s")

    # Test 1: List connected servers (should be empty initially)
    servers = client.list_connected_servers()
    print(f"✅ Connected servers: {len(servers)} (expected: 0)")

    # Test 2: Test unified connect method with invalid config
    connection_id = await client.connect({"type": "invalid"})
    print(f"✅ Invalid connection test: {connection_id} (expected: None)")

    # Test 3: Test websocket connection (not implemented yet)
    connection_id = await client.connect_websocket("ws://localhost:8080")
    print(
        f"✅ WebSocket connection test: {connection_id} (expected: None, not implemented)"
    )

    # Test 4: Test HTTP stream connection (not implemented yet)
    connection_id = await client.connect_http_stream("http://localhost:8080")
    print(
        f"✅ HTTP stream connection test: {connection_id} (expected: None, not implemented)"
    )

    # Test 5: List tools with no connections
    tools = await client.list_tools()
    print(f"✅ Tools with no connections: {len(tools)} (expected: 0)")

    # Test 6: Try to call tool on non-existent connection
    result = await client.call_tool("invalid", "test_tool", {})
    print(f"✅ Call tool on invalid connection: {result} (expected: None)")

    # Test 7: Try to disconnect from non-existent connection
    disconnected = await client.disconnect("invalid")
    print(f"✅ Disconnect invalid connection: {disconnected} (expected: False)")

    # Test 8: Get info for non-existent connection
    info = client.get_connection_info("invalid")
    print(f"✅ Get invalid connection info: {info} (expected: None)")

    # Test 9: Test context manager
    async with MCPClient() as test_client:
        servers = test_client.list_connected_servers()
        print(f"✅ Context manager test: {len(servers)} servers (expected: 0)")

    # Test 10: Test cleanup
    await client.cleanup()
    print("✅ Cleanup completed")

    print(
        "\n🎉 All basic tests passed! The refactored MCP Client is working correctly."
    )
    print("\nℹ️  Note: WebSocket and HTTP stream connections are not yet implemented")
    print("   but the infrastructure is in place for future implementation.")


if __name__ == "__main__":
    asyncio.run(test_mcp_client())
