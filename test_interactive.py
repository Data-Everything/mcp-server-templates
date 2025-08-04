#!/usr/bin/env python3

import sys
print("Starting test...", file=sys.stderr)

try:
    from mcp_template.interactive_cli import InteractiveCLI
    print("InteractiveCLI imported successfully", file=sys.stderr)
    
    # Test basic functionality
    cli = InteractiveCLI()
    print("InteractiveCLI instantiated", file=sys.stderr)
    
    # Test help command
    cli.onecmd("help")
    print("Help command executed", file=sys.stderr)
    
    # Test exit
    cli.onecmd("quit")
    print("Quit command executed", file=sys.stderr)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)

print("Test completed", file=sys.stderr)
