#!/usr/bin/env python3
"""
Script to test the actual behavior of ResponseBeautifier methods.
"""

import sys
import os

# Add project path
project_path = "/home/samarora/data-everything/mcp-server-templates"
sys.path.insert(0, project_path)

from mcp_template.interactive_cli import ResponseBeautifier

# Create a beautifier
beautifier = ResponseBeautifier()

print("Testing ResponseBeautifier methods...")

# Test _create_key_value_table
print("\n=== Testing _create_key_value_table ===")
data = {"name": "test", "value": 42, "active": True}
try:
    result = beautifier._create_key_value_table(data, "Test")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Test _create_data_table
print("\n=== Testing _create_data_table ===")
data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
try:
    result = beautifier._create_data_table(data, "Users")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Test _create_list_display
print("\n=== Testing _create_list_display ===")
data = ["item1", "item2", "item3"]
try:
    result = beautifier._create_list_display(data, "Items")
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

# Test beautify_tools_list
print("\n=== Testing beautify_tools_list ===")
tools = [
    {"name": "test_tool", "description": "Test tool", "parameters": {"properties": {}}}
]
try:
    result = beautifier.beautify_tools_list(tools, "Test")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error: {e}")

print("\nDone testing!")
