"""
Example usage of the refactored MCP Client.

This script demonstrates how to use the MCPClient to connect to MCP servers
and perform common operations programmatically.
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


async def demonstrate_mcp_client():
    """Demonstrate the MCP Client capabilities."""

    print("🚀 MCP Client API Demonstration")
    print("=" * 50)

    # Example 1: Basic usage with context manager
    print("\n📝 Example 1: Basic MCP Client Usage")
    async with MCPClient(timeout=10) as client:
        print(f"✅ Created MCPClient with timeout: {client.timeout}s")

        # Show initial state
        servers = client.list_connected_servers()
        print(f"📊 Connected servers: {len(servers)}")

        # List tools (no connections yet)
        tools = await client.list_tools()
        print(f"🔧 Available tools: {len(tools)}")

    print("✅ Context manager cleanup completed automatically")

    # Example 2: Unified connection interface
    print("\n📝 Example 2: Unified Connection Interface")
    client = MCPClient()

    # Different connection configurations
    stdio_config = {
        "type": "stdio",
        "command": ["python", "-c", "print('Mock MCP Server')"],
        "working_dir": "/tmp",
        "env_vars": {"MCP_MODE": "demo"},
    }

    websocket_config = {
        "type": "websocket",
        "url": "ws://localhost:8080/mcp",
        "headers": {"Authorization": "Bearer token"},
    }

    http_config = {
        "type": "http",
        "url": "http://localhost:8080/mcp",
        "headers": {"Content-Type": "application/json"},
    }

    # Try different connection types
    print("🔌 Testing connection types:")

    for config_name, config in [
        ("stdio", stdio_config),
        ("websocket", websocket_config),
        ("http", http_config),
    ]:
        connection_id = await client.connect(config)
        if connection_id:
            print(f"✅ {config_name}: Connected with ID {connection_id}")
            await client.disconnect(connection_id)
        else:
            print(f"❌ {config_name}: Failed to connect (expected for websocket/http)")

    await client.cleanup()

    # Example 3: Error handling demonstration
    print("\n📝 Example 3: Error Handling")
    client = MCPClient()

    # Test various error scenarios
    print("🚨 Testing error scenarios:")

    # Invalid connection type
    result = await client.connect({"type": "invalid"})
    print(f"❌ Invalid connection type: {result} (expected: None)")

    # Call tool on non-existent connection
    result = await client.call_tool("invalid_id", "test_tool", {})
    print(f"❌ Tool call on invalid connection: {result} (expected: None)")

    # Disconnect non-existent connection
    result = await client.disconnect("invalid_id")
    print(f"❌ Disconnect invalid connection: {result} (expected: False)")

    # Get info for non-existent connection
    info = client.get_connection_info("invalid_id")
    print(f"❌ Get invalid connection info: {info} (expected: None)")

    await client.cleanup()

    # Example 4: Connection management
    print("\n📝 Example 4: Connection Management")
    client = MCPClient()

    print("🔗 Connection management features:")

    # Generate connection IDs
    id1 = client._generate_connection_id("stdio")
    id2 = client._generate_connection_id("websocket")
    print(f"📝 Generated IDs: {id1}, {id2}")

    # List servers (empty)
    servers = client.list_connected_servers()
    print(f"📊 Connected servers: {len(servers)}")

    # Test bulk operations
    await client.disconnect_all()
    print("🧹 Bulk disconnect completed")

    await client.cleanup()

    print("\n🎉 MCP Client demonstration completed!")

    # Example 5: Future connection types (framework in place)
    print("\n📝 Example 5: Future Connection Types")
    client = MCPClient()

    print("🚧 Testing future connection types (infrastructure ready):")

    # WebSocket (framework ready, implementation needed)
    connection_id = await client.connect_websocket("ws://localhost:8080")
    print(
        f"🌐 WebSocket: {connection_id} (infrastructure ready, implementation needed)"
    )

    # HTTP Stream (framework ready, implementation needed)
    connection_id = await client.connect_http_stream("http://localhost:8080")
    print(
        f"🌊 HTTP Stream: {connection_id} (infrastructure ready, implementation needed)"
    )

    await client.cleanup()

    print(
        "\n✨ The MCP Client provides a clean, focused API for MCP server connections!"
    )


async def demonstrate_real_usage():
    """Show how the client would be used in real applications."""

    print("\n" + "=" * 60)
    print("📚 REAL-WORLD USAGE PATTERNS")
    print("=" * 60)

    # Pattern 1: Single connection workflow
    print("\n🔹 Pattern 1: Single Connection Workflow")
    print(
        """
async def connect_and_use_tool():
    async with MCPClient() as client:
        # Connect to MCP server
        connection_id = await client.connect_stdio(["python", "my_server.py"])

        if connection_id:
            # Discover available tools
            tools = await client.list_tools(connection_id)
            print(f"Available: {[t['name'] for t in tools]}")

            # Use a specific tool
            result = await client.call_tool(
                connection_id,
                "process_data",
                {"input": "example_data"}
            )

            return result
    """
    )

    # Pattern 2: Multi-connection management
    print("\n🔹 Pattern 2: Multi-Connection Management")
    print(
        """
async def manage_multiple_servers():
    client = MCPClient()
    connections = {}

    try:
        # Connect to multiple servers
        for server_name, command in server_configs.items():
            conn_id = await client.connect_stdio(command)
            if conn_id:
                connections[server_name] = conn_id

        # Use tools from different servers
        for name, conn_id in connections.items():
            tools = await client.list_tools(conn_id)
            # Process tools...

    finally:
        await client.cleanup()
    """
    )

    # Pattern 3: Error-resilient usage
    print("\n🔹 Pattern 3: Error-Resilient Usage")
    print(
        """
async def resilient_tool_call(client, connection_id, tool_name, args):
    try:
        # Check connection is still valid
        info = client.get_connection_info(connection_id)
        if not info or info["status"] != "connected":
            raise ConnectionError("Server connection lost")

        # Call tool with timeout handling
        result = await client.call_tool(connection_id, tool_name, args)

        if result is None:
            raise RuntimeError("Tool call failed")

        return result

    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        # Implement retry logic, reconnection, etc.
        return None
    """
    )

    print(
        "\n✅ These patterns show how the MCP Client enables robust, production-ready"
    )
    print("   programmatic access to MCP servers with clean error handling.")


if __name__ == "__main__":
    asyncio.run(demonstrate_mcp_client())
    asyncio.run(demonstrate_real_usage())
