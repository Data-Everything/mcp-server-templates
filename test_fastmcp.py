#!/usr/bin/env python3
"""
Test script to explore FastMCP capabilities
"""

import asyncio

from fastmcp import Client, FastMCP


async def main():
    # Create server
    mcp = FastMCP("test")

    @mcp.tool
    def test_tool(x: int) -> int:
        """Test tool"""
        return x * 2

    @mcp.tool
    def another_tool(msg: str) -> str:
        """Another test tool"""
        return f"Echo: {msg}"

    print("FastMCP object attributes:")
    for attr in sorted(dir(mcp)):
        if not attr.startswith("_"):
            print(f"  {attr}")

    # Test with client
    print("\nTesting with client:")
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print(f"Tools found: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Test calling a tool
        result = await client.call_tool("test_tool", {"x": 5})
        print(f"Tool result: {result.data}")


if __name__ == "__main__":
    asyncio.run(main())
