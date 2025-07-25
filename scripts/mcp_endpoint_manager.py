#!/usr/bin/env python3
"""
MCP Server Endpoint Manager and Documentation Generator.

Provides consistent endpoints and usage documentation for deployed MCP servers.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()

# Constants
TOOLS_CALL_METHOD = "tools/call"
SRC_SERVER_MODULE = "src.server"
MARKDOWN_CODE_BLOCK_END = "\n```\n\n"
MARKDOWN_JSON_CODE_BLOCK = "```json"


class MCPEndpointManager:
    """Manage MCP server endpoints and generate usage documentation."""

    def __init__(self, deployment_info: Dict[str, Any]):
        self.deployment_info = deployment_info
        self.template_name = deployment_info.get("template_id", "unknown")
        self.container_name = deployment_info.get("deployment_name", "unknown")
        self.base_url = self._generate_base_url()

    def _generate_base_url(self) -> str:
        """Generate consistent base URL for MCP server endpoints."""
        # Use container name as subdomain or path
        container_id = self.container_name.lower().replace("_", "-")
        return f"mcp://{container_id}"

    def generate_endpoint_documentation(self) -> Dict[str, Any]:
        """Generate comprehensive endpoint documentation."""
        doc = {
            "server_info": {
                "name": self.deployment_info.get("template_id", "Unknown Server"),
                "container": self.container_name,
                "base_url": self.base_url,
                "transport": "stdio",
                "protocol": "Model Context Protocol v1.0",
            },
            "endpoints": self._generate_endpoint_list(),
            "client_configurations": self._generate_client_configs(),
            "usage_examples": self._generate_usage_examples(),
            "troubleshooting": self._generate_troubleshooting_guide(),
        }
        return doc

    def _generate_endpoint_list(self) -> List[Dict[str, Any]]:
        """Generate list of available MCP endpoints/tools."""
        # Load template configuration to get capabilities
        template_config = self._load_template_config()
        capabilities = template_config.get("capabilities", [])

        endpoints = []

        # Standard MCP protocol endpoints
        endpoints.extend(
            [
                {
                    "path": "/tools/list",
                    "method": "tools/list",
                    "description": "List all available tools",
                    "type": "protocol",
                    "example": {
                        "request": {"method": "tools/list", "params": {}},
                        "response": {"tools": []},
                    },
                },
                {
                    "path": "/tools/call",
                    "method": TOOLS_CALL_METHOD,
                    "description": "Call a specific tool",
                    "type": "protocol",
                    "example": {
                        "request": {
                            "method": TOOLS_CALL_METHOD,
                            "params": {"name": "tool_name", "arguments": {}},
                        },
                        "response": {"content": []},
                    },
                },
                {
                    "path": "/resources/list",
                    "method": "resources/list",
                    "description": "List available resources",
                    "type": "protocol",
                    "example": {
                        "request": {"method": "resources/list", "params": {}},
                        "response": {"resources": []},
                    },
                },
            ]
        )

        # Template-specific endpoints based on capabilities
        for capability in capabilities:
            endpoint = self._capability_to_endpoint(capability)
            if endpoint:
                endpoints.append(endpoint)

        return endpoints

    def _capability_to_endpoint(self, capability: Dict[str, Any]) -> Dict[str, Any]:
        """Convert capability definition to endpoint documentation."""
        name = capability.get("name", "").lower().replace(" ", "_")

        return {
            "path": f"/tools/{name}",
            "method": TOOLS_CALL_METHOD,
            "description": capability.get("description", ""),
            "type": "tool",
            "capability": capability.get("name", ""),
            "example": {
                "request": {
                    "method": TOOLS_CALL_METHOD,
                    "params": {
                        "name": name,
                        "arguments": capability.get("example_args", {}),
                    },
                },
                "response": {
                    "content": [
                        {
                            "type": "text",
                            "text": capability.get(
                                "example_response", "Operation completed successfully"
                            ),
                        }
                    ]
                },
            },
        }

    def _generate_client_configs(self) -> Dict[str, Any]:
        """Generate client configuration for major MCP frameworks."""
        return {
            "claude_desktop": self._generate_claude_config(),
            "cline_vscode": self._generate_cline_config(),
            "continue_dev": self._generate_continue_config(),
            "openai_custom": self._generate_openai_config(),
            "anthropic_workbench": self._generate_anthropic_config(),
            "mcp_client_python": self._generate_python_client_config(),
            "mcp_client_nodejs": self._generate_nodejs_client_config(),
        }

    def _generate_claude_config(self) -> Dict[str, Any]:
        """Generate Claude Desktop configuration."""
        config = {
            "mcpServers": {
                f"{self.template_name}-server": {
                    "command": "docker",
                    "args": [
                        "exec",
                        "-i",
                        self.container_name,
                        "python",
                        "-m",
                        SRC_SERVER_MODULE,
                    ],
                }
            }
        }

        # Add environment variables if needed
        env_vars = self._extract_required_env_vars()
        if env_vars:
            config["mcpServers"][f"{self.template_name}-server"]["env"] = env_vars

        return {
            "config": config,
            "file_path": "~/Library/Application Support/Claude/claude_desktop_config.json",
            "instructions": [
                "1. Open Claude Desktop settings",
                "2. Navigate to 'Developer' section",
                "3. Add the configuration to 'MCP Servers'",
                "4. Restart Claude Desktop",
                "5. The server tools will be available in new conversations",
            ],
        }

    def _generate_cline_config(self) -> Dict[str, Any]:
        """Generate Cline VS Code extension configuration."""
        return {
            "config": {
                "mcp": {
                    "servers": {
                        f"{self.template_name}": {
                            "command": "docker",
                            "args": [
                                "exec",
                                "-i",
                                self.container_name,
                                "python",
                                "-m",
                                SRC_SERVER_MODULE,
                            ],
                        }
                    }
                }
            },
            "file_path": ".vscode/settings.json or VS Code User Settings",
            "instructions": [
                "1. Open VS Code with Cline extension installed",
                "2. Open Command Palette (Cmd/Ctrl+Shift+P)",
                "3. Run 'Cline: Open Settings'",
                "4. Add MCP server configuration",
                "5. Restart Cline extension",
                "6. Server tools will be available in Cline chat",
            ],
        }

    def _generate_continue_config(self) -> Dict[str, Any]:
        """Generate Continue.dev configuration."""
        return {
            "config": {
                "mcp": {
                    "servers": [
                        {
                            "name": f"{self.template_name}-server",
                            "command": [
                                "docker",
                                "exec",
                                "-i",
                                self.container_name,
                                "python",
                                "-m",
                                SRC_SERVER_MODULE,
                            ],
                        }
                    ]
                }
            },
            "file_path": "~/.continue/config.json",
            "instructions": [
                "1. Install Continue extension in VS Code",
                "2. Open Continue configuration",
                "3. Add MCP server to configuration",
                "4. Reload Continue extension",
                "5. Use @mcp prefix to access server tools",
            ],
        }

    def _generate_openai_config(self) -> Dict[str, Any]:
        """Generate OpenAI-compatible configuration."""
        return {
            "config": {
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": f"mcp_{self.template_name}",
                            "description": f"Access {self.template_name} MCP server tools",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "tool_name": {
                                        "type": "string",
                                        "description": "Name of the MCP tool to call",
                                    },
                                    "arguments": {
                                        "type": "object",
                                        "description": "Arguments for the tool",
                                    },
                                },
                                "required": ["tool_name"],
                            },
                        },
                    }
                ]
            },
            "instructions": [
                "1. Use OpenAI Function Calling API",
                "2. Include the MCP server function in your tools array",
                "3. Implement a proxy function that calls the MCP server",
                "4. Forward tool calls through Docker exec to the container",
            ],
        }

    def _generate_anthropic_config(self) -> Dict[str, Any]:
        """Generate Anthropic Workbench configuration."""
        return {
            "config": {
                "mcp_servers": {
                    f"{self.template_name}": {
                        "transport": {
                            "type": "stdio",
                            "command": "docker",
                            "args": [
                                "exec",
                                "-i",
                                self.container_name,
                                "python",
                                "-m",
                                SRC_SERVER_MODULE,
                            ],
                        }
                    }
                }
            },
            "instructions": [
                "1. Open Anthropic Workbench",
                "2. Navigate to 'MCP Servers' configuration",
                "3. Add new server with the above configuration",
                "4. Test connection and verify tools are available",
            ],
        }

    def _generate_python_client_config(self) -> Dict[str, Any]:
        """Generate Python MCP client configuration."""
        return {
            "code": f'''
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def call_{self.template_name.replace("-", "_")}_server():
    """Connect to {self.template_name} MCP server."""

    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "{self.container_name}", "python", "-m", SRC_SERVER_MODULE]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])

            # Call a tool (example)
            if tools.tools:
                result = await session.call_tool(
                    tools.tools[0].name,
                    arguments={{}}
                )
                print("Tool result:", result)

# Run the client
asyncio.run(call_{self.template_name.replace("-", "_")}_server())
''',
            "requirements": ["mcp>=1.0.0", "docker"],  # Ensure Docker is available
            "instructions": [
                "1. Install MCP Python client: pip install mcp",
                "2. Ensure Docker container is running",
                "3. Run the Python client code above",
                "4. Tools will be available through the MCP protocol",
            ],
        }

    def _generate_nodejs_client_config(self) -> Dict[str, Any]:
        """Generate Node.js MCP client configuration."""
        return {
            "code": f"""
const {{ Client }} = require('@modelcontextprotocol/sdk/client/index.js');
const {{ StdioClientTransport }} = require('@modelcontextprotocol/sdk/client/stdio.js');
const {{ spawn }} = require('child_process');

async function connect{self.template_name.replace("-", "").title()}Server() {{
    // Start the MCP server process
    const serverProcess = spawn('docker', [
        'exec', '-i', '{self.container_name}',
        'python', '-m', SRC_SERVER_MODULE
    ]);

    // Create client with stdio transport
    const transport = new StdioClientTransport({{
        command: 'docker',
        args: ['exec', '-i', '{self.container_name}', 'python', '-m', SRC_SERVER_MODULE]
    }});

    const client = new Client({{
        name: "{self.template_name}-client",
        version: "1.0.0"
    }}, {{
        capabilities: {{}}
    }});

    // Connect to server
    await client.connect(transport);

    // List available tools
    const tools = await client.listTools();
    console.log('Available tools:', tools.tools.map(t => t.name));

    // Call a tool (example)
    if (tools.tools.length > 0) {{
        const result = await client.callTool({{
            name: tools.tools[0].name,
            arguments: {{}}
        }});
        console.log('Tool result:', result);
    }}

    await client.close();
}}

connect{self.template_name.replace("-", "").title()}Server().catch(console.error);
""",
            "dependencies": {"@modelcontextprotocol/sdk": "^1.0.0"},
            "instructions": [
                "1. Install MCP SDK: npm install @modelcontextprotocol/sdk",
                "2. Ensure Docker container is running",
                "3. Run the Node.js client code above",
                "4. Tools will be available through the MCP protocol",
            ],
        }

    def _generate_usage_examples(self) -> List[Dict[str, Any]]:
        """Generate practical usage examples."""
        examples = []

        # Load template configuration
        template_config = self._load_template_config()
        capabilities = template_config.get("capabilities", [])

        # Generate example for each capability
        for capability in capabilities:
            example = {
                "title": f"Using {capability.get('name', 'Tool')}",
                "description": capability.get("description", ""),
                "scenario": capability.get("example", "Basic usage example"),
                "code_examples": {
                    "claude_desktop": self._generate_claude_example(capability),
                    "python_client": self._generate_python_example(capability),
                    "curl_equivalent": self._generate_curl_example(capability),
                },
            }
            examples.append(example)

        # Add general examples
        examples.extend(
            [
                {
                    "title": "Health Check and Server Status",
                    "description": "Verify the MCP server is running and accessible",
                    "scenario": "Check if server is responding and list available capabilities",
                    "code_examples": {
                        "docker_logs": f"docker logs {self.container_name}",
                        "docker_exec": f"docker exec {self.container_name} python -c \"print('Server is running')\"",
                        "connection_test": "Test MCP protocol connection and tool listing",
                    },
                },
                {
                    "title": "Configuration Management",
                    "description": "Update server configuration and restart if needed",
                    "scenario": "Change server settings or update environment variables",
                    "code_examples": {
                        "update_env": f"docker exec {self.container_name} env",
                        "restart_container": f"docker restart {self.container_name}",
                        "check_config": "Verify configuration changes took effect",
                    },
                },
            ]
        )

        return examples

    def _generate_claude_example(self, capability: Dict[str, Any]) -> str:
        """Generate Claude Desktop usage example."""
        tool_name = capability.get("name", "tool").lower().replace(" ", "_")
        return f"""
In Claude Desktop, you can use this tool by simply asking:

"Please use the {capability.get("name", "tool")} to {capability.get("description", "perform the operation")}"

Claude will automatically:
1. Recognize the available MCP tool
2. Call the {tool_name} function
3. Display the results in the conversation

Example conversation:
User: "Can you {capability.get("example", "help me with this task")}?"
Claude: "I'll use the {capability.get("name", "tool")} to help you with that."
[Tool execution happens automatically]
Claude: [Shows results and explains what was done]
"""

    def _generate_python_example(self, capability: Dict[str, Any]) -> str:
        """Generate Python client usage example."""
        tool_name = capability.get("name", "tool").lower().replace(" ", "_")
        return f"""
# Call the {capability.get("name", "tool")} tool
result = await session.call_tool(
    "{tool_name}",
    arguments={capability.get("example_args", "{}")}
)

print(f"Result: {{result.content[0].text}}")

# Example with error handling
try:
    result = await session.call_tool(
        "{tool_name}",
        arguments={capability.get("example_args", "{}")}
    )
    if result.isError:
        print(f"Error: {{result.content[0].text}}")
    else:
        print(f"Success: {{result.content[0].text}}")
except Exception as e:
    print(f"Failed to call tool: {{e}}")
"""

    def _generate_curl_example(self, capability: Dict[str, Any]) -> str:
        """Generate curl equivalent for debugging."""
        tool_name = capability.get("name", "tool").lower().replace(" ", "_")
        return f"""
# Note: MCP uses stdio transport, not HTTP.
# This is a conceptual HTTP equivalent for understanding:

# List tools (conceptual)
curl -X POST "http://localhost:8000/mcp/rpc" \\
  -H "Content-Type: application/json" \\
  -d '{{"method": "tools/list", "params": {{}}}}'

# Call tool (conceptual)
curl -X POST "http://localhost:8000/mcp/rpc" \\
  -H "Content-Type: application/json" \\
  -d '{{"method": "tools/call", "params": {{"name": "{tool_name}", "arguments": {capability.get("example_args", "{}")}}}}}'

# Actual usage requires MCP-compatible client over stdio transport
"""

    def _generate_troubleshooting_guide(self) -> Dict[str, Any]:
        """Generate troubleshooting guide."""
        return {
            "common_issues": [
                {
                    "issue": "Container not responding",
                    "symptoms": [
                        "Connection timeouts",
                        "No tool responses",
                        "Server appears offline",
                    ],
                    "solutions": [
                        f"Check container status: docker ps | grep {self.container_name}",
                        f"View container logs: docker logs {self.container_name}",
                        f"Restart container: docker restart {self.container_name}",
                        "Verify Docker daemon is running",
                    ],
                },
                {
                    "issue": "Tools not available in client",
                    "symptoms": [
                        "Empty tools list",
                        "Tool call errors",
                        "MCP client can't connect",
                    ],
                    "solutions": [
                        "Verify MCP client configuration is correct",
                        "Check that container name matches configuration",
                        "Ensure stdio transport is properly configured",
                        "Test connection with simple MCP client first",
                    ],
                },
                {
                    "issue": "Permission or access errors",
                    "symptoms": [
                        "Access denied",
                        "File permission errors",
                        "Docker exec failures",
                    ],
                    "solutions": [
                        "Check Docker container permissions",
                        "Verify environment variables are set correctly",
                        "Ensure required volumes are mounted",
                        "Check file/directory ownership in container",
                    ],
                },
                {
                    "issue": "Performance or timeout issues",
                    "symptoms": [
                        "Slow responses",
                        "Operation timeouts",
                        "High resource usage",
                    ],
                    "solutions": [
                        "Check container resource limits",
                        "Monitor Docker container stats",
                        "Review configuration for performance settings",
                        "Scale container resources if needed",
                    ],
                },
            ],
            "diagnostic_commands": [
                {
                    "purpose": "Check container health",
                    "command": f"docker exec {self.container_name} python -c \"import sys; print('Python version:', sys.version)\"",
                },
                {
                    "purpose": "Test MCP server import",
                    "command": f"docker exec {self.container_name} python -c \"from {SRC_SERVER_MODULE} import app; print('Server imported successfully')\"",
                },
                {
                    "purpose": "Check environment variables",
                    "command": f"docker exec {self.container_name} env | grep MCP",
                },
                {
                    "purpose": "View recent logs",
                    "command": f"docker logs --tail 50 {self.container_name}",
                },
            ],
            "support_resources": [
                "MCP Protocol Documentation: https://modelcontextprotocol.io/docs",
                "Template Issues: https://github.com/data-everything/mcp-server-templates/issues",
                "Docker Documentation: https://docs.docker.com/",
                "FastMCP Documentation: https://fastmcp.com/",
            ],
        }

    def _load_template_config(self) -> Dict[str, Any]:
        """Load template configuration."""
        try:
            template_dir = (
                Path(__file__).parent.parent / "templates" / self.template_name
            )
            template_json = template_dir / "template.json"

            if template_json.exists():
                with open(template_json, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        return {}

    def _extract_required_env_vars(self) -> Dict[str, str]:
        """Extract required environment variables with example values."""
        template_config = self._load_template_config()
        config_schema = template_config.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        env_vars = {}
        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            env_mapping = prop_config.get("env_mapping")
            if env_mapping:
                # Use default value or placeholder
                example_value = prop_config.get("default", f"YOUR_{env_mapping}")
                env_vars[env_mapping] = str(example_value)

        return env_vars

    def save_documentation(self, output_dir: Path):
        """Save comprehensive documentation to files."""
        output_dir.mkdir(exist_ok=True)

        doc = self.generate_endpoint_documentation()

        # Save as JSON
        with open(
            output_dir / f"{self.template_name}_endpoints.json", "w", encoding="utf-8"
        ) as f:
            json.dump(doc, f, indent=2)

        # Save as YAML
        with open(
            output_dir / f"{self.template_name}_endpoints.yaml", "w", encoding="utf-8"
        ) as f:
            yaml.dump(doc, f, default_flow_style=False)

        # Generate markdown documentation
        self._generate_markdown_docs(doc, output_dir)

        console.print(f"✅ Documentation saved to {output_dir}")

    def _generate_markdown_docs(self, doc: Dict[str, Any], output_dir: Path):
        """Generate comprehensive markdown documentation."""
        md_content = self._render_markdown_template(doc)

        with open(
            output_dir / f"{self.template_name}_usage_guide.md", "w", encoding="utf-8"
        ) as f:
            f.write(md_content)

    def _render_markdown_template(self, doc: Dict[str, Any]) -> str:
        """Render markdown documentation template."""
        md_parts = []

        # Add header section
        md_parts.append(self._render_header_section(doc["server_info"]))

        # Add endpoints section
        md_parts.append(self._render_endpoints_section(doc["endpoints"]))

        # Add client configurations section
        md_parts.append(
            self._render_client_configs_section(doc["client_configurations"])
        )

        # Add usage examples section
        md_parts.append(self._render_usage_examples_section(doc["usage_examples"]))

        # Add troubleshooting section
        md_parts.append(self._render_troubleshooting_section(doc["troubleshooting"]))

        return "\n".join(md_parts)

    def _render_header_section(self, server_info: Dict[str, Any]) -> str:
        """Render header section of markdown."""
        return f"""# {server_info["name"]} - Usage Guide

## Server Information

- **Container**: `{server_info["container"]}`
- **Base URL**: `{server_info["base_url"]}`
- **Transport**: {server_info["transport"]}
- **Protocol**: {server_info["protocol"]}

## Available Endpoints

"""

    def _render_endpoints_section(self, endpoints: List[Dict[str, Any]]) -> str:
        """Render endpoints section of markdown."""
        md_parts = []

        for endpoint in endpoints:
            capability_name = endpoint.get("capability", endpoint["method"])
            md_parts.append(f"### {capability_name}")
            md_parts.append(f"- **Method**: `{endpoint['method']}`")
            md_parts.append(f"- **Type**: {endpoint['type']}")
            md_parts.append(f"- **Description**: {endpoint['description']}")
            md_parts.append("")
            md_parts.append("**Example Request:**")
            md_parts.append(MARKDOWN_JSON_CODE_BLOCK)
            md_parts.append(json.dumps(endpoint["example"]["request"], indent=2))
            md_parts.append("```")
            md_parts.append("")
            md_parts.append("**Example Response:**")
            md_parts.append(MARKDOWN_JSON_CODE_BLOCK)
            md_parts.append(json.dumps(endpoint["example"]["response"], indent=2))
            md_parts.append("```")
            md_parts.append("")

        return "\n".join(md_parts)

    def _render_client_configs_section(self, clients: Dict[str, Any]) -> str:
        """Render client configurations section of markdown."""
        md_parts = ["## Client Configurations\n"]

        for client_name, client_config in clients.items():
            client_title = client_name.replace("_", " ").title()
            md_parts.append(f"### {client_title}\n")

            if "config" in client_config:
                md_parts.append("**Configuration:**")
                md_parts.append(MARKDOWN_JSON_CODE_BLOCK)
                md_parts.append(json.dumps(client_config["config"], indent=2))
                md_parts.append("```\n")

            if "code" in client_config:
                md_parts.append("**Code Example:**")
                md_parts.append("```python")
                md_parts.append(client_config["code"])
                md_parts.append("```\n")

            if "instructions" in client_config:
                md_parts.append("**Setup Instructions:**")
                for i, instruction in enumerate(client_config["instructions"], 1):
                    md_parts.append(f"{i}. {instruction}")
                md_parts.append("")

        return "\n".join(md_parts)

    def _render_usage_examples_section(self, examples: List[Dict[str, Any]]) -> str:
        """Render usage examples section of markdown."""
        md_parts = ["## Usage Examples\n"]

        for example in examples:
            md_parts.append(f"### {example['title']}\n")
            md_parts.append(f"{example['description']}\n")
            md_parts.append(f"**Scenario**: {example['scenario']}\n")

            for example_type, code in example["code_examples"].items():
                example_title = example_type.replace("_", " ").title()
                md_parts.append(f"**{example_title}:**")

                # Determine code block language
                if example_type == "curl_equivalent":
                    lang = "bash"
                elif example_type == "python_client":
                    lang = "python"
                else:
                    lang = ""

                md_parts.append(f"```{lang}")
                md_parts.append(code)
                md_parts.append("```\n")

        return "\n".join(md_parts)

    def _render_troubleshooting_section(self, troubleshooting: Dict[str, Any]) -> str:
        """Render troubleshooting section of markdown."""
        md_parts = ["## Troubleshooting\n", "### Common Issues\n"]

        # Add common issues
        for issue in troubleshooting["common_issues"]:
            md_parts.append(f"#### {issue['issue']}\n")
            md_parts.append("**Symptoms:**")
            for symptom in issue["symptoms"]:
                md_parts.append(f"- {symptom}")
            md_parts.append("\n**Solutions:**")
            for solution in issue["solutions"]:
                md_parts.append(f"- {solution}")
            md_parts.append("")

        # Add diagnostic commands
        md_parts.append("### Diagnostic Commands\n")
        for diag in troubleshooting["diagnostic_commands"]:
            md_parts.append(f"**{diag['purpose']}:**")
            md_parts.append("```bash")
            md_parts.append(diag["command"])
            md_parts.append("```\n")

        # Add support resources
        md_parts.append("### Support Resources\n")
        for resource in troubleshooting["support_resources"]:
            md_parts.append(f"- {resource}")

        return "\n".join(md_parts)

    def display_quick_start(self):
        """Display quick start guide in console."""
        doc = self.generate_endpoint_documentation()
        server_info = doc["server_info"]

        # Server info panel
        console.print(
            Panel(
                f"[cyan]Container:[/cyan] {server_info['container']}\n"
                f"[cyan]Base URL:[/cyan] {server_info['base_url']}\n"
                f"[cyan]Transport:[/cyan] {server_info['transport']}\n"
                f"[cyan]Protocol:[/cyan] {server_info['protocol']}",
                title=f"🚀 {server_info['name']} - Quick Start",
                border_style="green",
            )
        )

        # Available tools
        endpoints = [e for e in doc["endpoints"] if e["type"] == "tool"]
        if endpoints:
            table = Table(title="Available Tools")
            table.add_column("Tool", style="cyan")
            table.add_column("Description", style="white")

            for endpoint in endpoints:
                table.add_row(
                    endpoint.get("capability", endpoint["method"]),
                    endpoint["description"],
                )

            console.print(table)

        # Quick setup for Claude Desktop
        claude_config = doc["client_configurations"]["claude_desktop"]
        console.print(
            Panel(
                "[yellow]Add this to your Claude Desktop configuration:[/yellow]\n\n"
                + json.dumps(claude_config["config"], indent=2),
                title="🤖 Claude Desktop Setup",
                border_style="blue",
            )
        )

        # Health check command
        console.print(
            Panel(
                f"[green]docker logs {server_info['container']}[/green]\n\n"
                f"[yellow]Check if your server is running properly[/yellow]",
                title="🏥 Health Check",
                border_style="yellow",
            )
        )


def main():
    """Generate endpoint documentation for a deployed MCP server."""
    if len(sys.argv) < 2:
        console.print(
            "[red]Usage: python mcp_endpoint_manager.py <container_name> [template_name][/red]"
        )
        sys.exit(1)

    container_name = sys.argv[1]

    # Extract template name with proper conditional handling
    if len(sys.argv) > 2:
        template_name = sys.argv[2]
    elif "-" in container_name:
        template_name = container_name.split("-")[1]
    else:
        template_name = "unknown"

    # Mock deployment info (in real usage, this would come from deployment system)
    deployment_info = {
        "template_id": template_name,
        "deployment_name": container_name,
        "status": "deployed",
        "created_at": "2024-01-01T00:00:00Z",
    }

    manager = MCPEndpointManager(deployment_info)

    # Display quick start guide
    manager.display_quick_start()

    # Save comprehensive documentation
    output_dir = Path.cwd() / "mcp_docs" / container_name
    manager.save_documentation(output_dir)

    console.print(f"\n[green]✅ Complete documentation saved to:[/green] {output_dir}")
    console.print(
        f"[cyan]📖 View usage guide:[/cyan] {output_dir / f'{template_name}_usage_guide.md'}"
    )


if __name__ == "__main__":
    main()
