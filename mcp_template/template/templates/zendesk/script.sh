#!/bin/bash

# Zendesk MCP Server Transport Handler
# Supports stdio, http, sse, and streamable-http transports

set -euo pipefail

# Get transport from environment variable or default to http
TRANSPORT=${MCP_TRANSPORT:-http}
PORT=${MCP_PORT:-7072}

echo "Starting Zendesk MCP Server with transport: $TRANSPORT"

case "$TRANSPORT" in
    "stdio")
        echo "Using stdio transport"
        exec python server.py
        ;;
    "http")
        echo "Using HTTP transport on port $PORT"
        exec python server.py
        ;;
    "sse")
        echo "Using Server-Sent Events transport on port $PORT"
        export MCP_TRANSPORT=sse
        exec python server.py
        ;;
    "streamable-http")
        echo "Using Streamable HTTP transport on port $PORT"
        export MCP_TRANSPORT=streamable-http
        exec python server.py
        ;;
    *)
        echo "Error: Unsupported transport '$TRANSPORT'"
        echo "Supported transports: stdio, http, sse, streamable-http"
        exit 1
        ;;
esac
