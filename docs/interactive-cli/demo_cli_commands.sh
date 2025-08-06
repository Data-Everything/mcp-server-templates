#!/bin/bash
# Demo script to run MCP Interactive CLI commands for documentation and output samples
# Uses 'demo' template and MCP_TRANSPORT=http for HTTP output examples


set -e

# Set environment variable for HTTP transport
export MCP_TRANSPORT=http

# Run all commands in a single interactive CLI session using a here-document
# Replace 'mcp-interactive-cli' with the actual CLI entrypoint if different

mcp-template i <<EOF | tee demo_cli_session.out
list_servers
templates
tools demo
show_config demo
config demo api_key=demo123 endpoint=https://demo.example.com
call demo tool1 '{"input": "value"}'
clear_config demo
help
quit
EOF

# Optionally split outputs for documentation
awk '/^list_servers$/{flag="list_servers";next}/^templates$/{flag="templates";next}/^tools demo$/{flag="tools";next}/^show_config demo$/{flag="show_config";next}/^config demo/{flag="config";next}/^call demo/{flag="call";next}/^clear_config demo$/{flag="clear_config";next}/^help$/{flag="help";next}/^quit$/{flag="quit";next} flag{print > ("demo_" flag ".out")}' demo_cli_session.out

# Print sample outputs for documentation
for f in demo_*.out; do
  echo "\n===== Output: $f ====="
  cat "$f"
done
