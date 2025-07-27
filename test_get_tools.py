#!/usr/bin/env python3
"""
Test script to explore FastMCP get_tools method
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

    # Test get_tools method
    print("Testing mcp.get_tools():")
    tools = await mcp.get_tools()
    print(f"Type: {type(tools)}")
    print(f"Tools: {tools}")

    # Inspect tool objects
    print("\nTool details:")
    for tool_name, tool_obj in tools.items():
        print(f"  Tool Name: {tool_name}")
        print(f"  Tool Object: {tool_obj}")
        print(f"  Tool Type: {type(tool_obj)}")
        print(
            f"  Tool Attributes: {[attr for attr in dir(tool_obj) if not attr.startswith('_')]}"
        )
        if hasattr(tool_obj, "name"):
            print(f"    Name: {tool_obj.name}")
        if hasattr(tool_obj, "description"):
            print(f"    Description: {tool_obj.description}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
