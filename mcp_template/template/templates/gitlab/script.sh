#!/bin/bash

# GitLab MCP Server Transport Handler
# Handles multiple transport modes: stdio, sse, streamable-http

# Default values
MCP_TRANSPORT="${MCP_TRANSPORT:-stdio}"
MCP_PORT="${MCP_PORT:-3002}"
HOST="${HOST:-0.0.0.0}"

echo "GitLab MCP Server starting with transport: $MCP_TRANSPORT"

# Set working directory
cd /app

case "$MCP_TRANSPORT" in
    "stdio")
        echo "Starting GitLab MCP Server with stdio transport"
        # For stdio, we don't set SSE or STREAMABLE_HTTP
        export SSE=false
        export STREAMABLE_HTTP=false
        node build/index.js
        ;;
    "sse")
        echo "Starting GitLab MCP Server with SSE transport on port $MCP_PORT"
        export SSE=true
        export STREAMABLE_HTTP=false
        export PORT="$MCP_PORT"
        export HOST="$HOST"
        node build/index.js
        ;;
    "streamable-http"|"http")
        echo "Starting GitLab MCP Server with Streamable HTTP transport on port $MCP_PORT"
        export SSE=false
        export STREAMABLE_HTTP=true
        export PORT="$MCP_PORT"
        export HOST="$HOST"
        node build/index.js
        ;;
    *)
        echo "Error: Unsupported transport mode: $MCP_TRANSPORT"
        echo "Supported modes: stdio, sse, streamable-http, http"
        exit 1
        ;;
esac
