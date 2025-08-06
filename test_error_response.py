#!/usr/bin/env python3
"""
Script to test the beautify_tool_response behavior with error.
"""

import sys
import os

# Add project path
project_path = "/home/samarora/data-everything/mcp-server-templates"
sys.path.insert(0, project_path)

from mcp_template.interactive_cli import ResponseBeautifier
from unittest.mock import patch

# Create a beautifier
beautifier = ResponseBeautifier()

response = {
    "status": "completed",
    "stdout": '{"jsonrpc": "2.0", "id": 3, "error": {"code": 404, "message": "Not found"}}',
}

print("Testing beautify_tool_response with error...")

with patch.object(beautifier.console, "print") as mock_print:
    beautifier.beautify_tool_response(response)

    print(f"Number of print calls: {mock_print.call_count}")
    for i, call in enumerate(mock_print.call_args_list):
        print(f"Call {i}: {call}")

print("Done!")
