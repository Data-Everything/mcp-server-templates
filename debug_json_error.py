#!/usr/bin/env python3
"""Debug script to test JSON-RPC error beautification"""

from mcp_template.interactive_cli import ResponseBeautifier
from unittest.mock import Mock, patch

# Create a beautifier
beautifier = ResponseBeautifier()

# Test the exact response from the failing test
response = {
    "status": "completed",
    "stdout": '{"jsonrpc": "2.0", "id": 3, "error": {"code": 404, "message": "Not found"}}',
}

print("Testing JSON-RPC error response...")
print(f"Response: {response}")

with patch.object(beautifier.console, "print") as mock_print:
    beautifier.beautify_tool_response(response)

    print(f"Number of print calls: {mock_print.call_count}")
    for i, call in enumerate(mock_print.call_args_list):
        print(f"Call {i}: {call}")
        if hasattr(call.args[0], "renderable"):
            print(f"  Panel content: {call.args[0].renderable}")
            print(f"  Panel title: {call.args[0].title}")
        elif hasattr(call.args[0], "title"):
            print(f"  Panel title: {call.args[0].title}")

print("Done!")
