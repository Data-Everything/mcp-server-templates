#!/usr/bin/env python3
import json
import logging
from pathlib import Path
from mcp_template.tools.discovery import ToolDiscovery

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load github template config
with open('mcp_template/template/templates/github/template.json') as f:
    config = json.load(f)

print("=== Template Config Analysis ===")
print(f"Tool discovery type: {config.get('tool_discovery')}")
print(f"Has 'tools': {'tools' in config}")
print(f"Has 'capabilities': {'capabilities' in config}")

if 'capabilities' in config:
    capabilities = config['capabilities']
    print(f"Number of capabilities: {len(capabilities)}")
    print(f"Capabilities: {capabilities}")

print("\n=== Running Discovery ===")

# Test discovery
discovery = ToolDiscovery()
result = discovery.discover_tools(
    template_name='github',
    template_dir=Path('mcp_template/template/templates/github'),
    template_config=config,
    use_cache=False,
    force_refresh=True
)

print("\n=== Results ===")
print(f"Discovery method: {result.get('discovery_method')}")
print(f"Number of tools: {len(result.get('tools', []))}")
print(f"Tools: {[t.get('name') for t in result.get('tools', [])]}")
print(f"Warnings: {result.get('warnings', [])}")
