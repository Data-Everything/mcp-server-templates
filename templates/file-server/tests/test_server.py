#!/usr/bin/env python3
"""Test script for the FastMCP file server."""

import asyncio
import sys
import os

# Add src to path so we can import our server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server import mcp

async def test_server():
    """Test the FastMCP server setup."""
    print("FastMCP File Server Test")
    print("=" * 40)
    
    # List all registered tools
    tools = await mcp.get_tools()
    print(f"Registered {len(tools)} tools:")
    for tool in tools:
        print(f"- {tool}")
    
    print("\n" + "=" * 40)
    print("Server test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_server())
