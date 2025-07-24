#!/usr/bin/env python3
"""Test tool functionality of the FastMCP file server."""

import asyncio
import sys
import os

# Add src to path so we can import our server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server import mcp

async def test_tools():
    """Test the FastMCP server tools."""
    print("Testing FastMCP File Server Tools")
    print("=" * 40)
    
    try:
        # Test read_file
        print("Testing read_file...")
        result = await mcp._call_tool("read_file", {"path": "/data/test.txt"})
        print(f"Read result: {result}")
        
        # Test list_directory
        print("\nTesting list_directory...")
        result = await mcp._call_tool("list_directory", {"path": "/data"})
        print(f"Directory listing: {result}")
        
        # Test write_file
        print("\nTesting write_file...")
        result = await mcp._call_tool("write_file", {
            "path": "/data/fastmcp_test.txt", 
            "content": "Written by FastMCP file server!"
        })
        print(f"Write result: {result}")
        
        # Test read the file we just wrote
        print("\nReading the file we just wrote...")
        result = await mcp._call_tool("read_file", {"path": "/data/fastmcp_test.txt"})
        print(f"Read result: {result}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
    
    print("\n" + "=" * 40)
    print("Tool test completed!")

if __name__ == "__main__":
    asyncio.run(test_tools())
