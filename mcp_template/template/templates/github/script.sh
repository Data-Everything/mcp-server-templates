#!/bin/sh

# Check MCP_Transport env variable, default to stdio
MCP_TRANSPORT="${MCP_TRANSPORT:-stdio}"
MCP_PORT="${MCP_PORT:-7071}"

if [ "$MCP_TRANSPORT" = "stdio" ]; then
    echo "Starting MCP server with stdio transport"
    /server/github-mcp-server stdio
else
    echo "Starting MCP server with HTTP transport on port $MCP_PORT"
    /server/github-mcp-server serve --http --port "$MCP_PORT" "$@"
fi
