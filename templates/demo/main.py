#!/usr/bin/env python3
"""
Main entry point for the Demo Hello MCP Server.

This avoids the module import warnings by providing a clean entry point.
"""

import os
import sys

# Clean way to import without sys.modules conflicts
if __name__ == "__main__":
    # Add src to path cleanly
    src_path = os.path.join(os.path.dirname(__file__), "src")
    sys.path.insert(0, src_path)

    # Import and run directly
    import server

    server.main()
