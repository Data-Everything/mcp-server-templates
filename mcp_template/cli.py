#!/usr/bin/env python3
"""
Enhanced CLI module for MCP Template deployment with FastMCP integration.

This module extends the existing CLI with new commands for:
- Config discovery with double-underscore notation
- Tool listing using FastMCP client
- Integration examples for various LLMs and frameworks
- Docker networking support
- HTTP-first transport with stdio fallback
"""

import datetime
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_template.backends.docker import DockerDeploymentService
from mcp_template.deployer import MCPDeployer
from mcp_template.template.utils.discovery import TemplateDiscovery
from mcp_template.tools import DockerProbe, ToolDiscovery
from mcp_template.utils import TEMPLATES_DIR

console = Console()
logger = logging.getLogger(__name__)


class EnhancedCLI:
    """Enhanced CLI with FastMCP integration and new features."""

    def __init__(self):
        """Initialize the enhanced CLI."""
        # Import at runtime to avoid circular imports

        self.deployer = MCPDeployer()
        self.template_discovery = TemplateDiscovery()
        self.templates = self.template_discovery.discover_templates()
        self.tool_discovery = ToolDiscovery()
        self.docker_probe = DockerProbe()
        self.docker_service = DockerDeploymentService()

        # Initialize response beautifier
        try:
            from mcp_template.interactive_cli import ResponseBeautifier

            self.beautifier = ResponseBeautifier()
        except ImportError:
            # Fallback if interactive CLI not available
            self.beautifier = None

    def _is_actual_error(self, stderr_text: str) -> bool:
        """Check if stderr contains actual errors vs informational messages."""
        if not stderr_text:
            return False

        stderr_lower = stderr_text.lower().strip()

        # These are actual error indicators
        error_indicators = [
            "error:",
            "exception:",
            "traceback",
            "failed:",
            "fatal:",
            "cannot",
            "unable to",
            "permission denied",
            "not found",
            "invalid",
            "syntax error",
            "connection refused",
            "timeout",
        ]

        # These are informational messages that should not be treated as errors
        info_indicators = [
            "running on stdio",
            "server started",
            "listening on",
            "connected to",
            "initialized",
            "ready",
            "starting",
            "loading",
            "loaded",
            "using",
            "found",
        ]

        # Check for actual errors first
        for indicator in error_indicators:
            if indicator in stderr_lower:
                return True

        # If it contains info indicators, it's likely not an error
        for indicator in info_indicators:
            if indicator in stderr_lower:
                return False

        # If stderr is very short and doesn't contain error words, likely not an error
        if len(stderr_text.strip()) < 100 and not any(
            word in stderr_lower for word in ["error", "fail", "exception"]
        ):
            return False

        # Default to showing it if we're unsure
        return True

    def show_config_options(self, template_name: str) -> None:
        """Show all configuration options including double-underscore notation."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.templates[template_name]
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        if not properties:
            console.print(
                f"[yellow]⚠️  No configuration options available for {template_name}[/yellow]"
            )
            return

        console.print(
            Panel(
                f"Configuration Options for [cyan]{template_name}[/cyan]",
                title="📋 Template Configuration",
                border_style="blue",
            )
        )

        table = Table()
        table.add_column("Property", style="cyan", width=20)
        table.add_column("Type", style="yellow", width=12)
        table.add_column("CLI Options", style="green", width=40)
        table.add_column("Environment Variable", style="magenta", width=20)
        table.add_column("Default", style="blue", width=15)
        table.add_column("Required", style="red", width=8)

        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get("type", "string")
            env_mapping = prop_config.get("env_mapping", "")
            default = str(prop_config.get("default", ""))
            is_required = "✓" if prop_name in required else ""

            # Generate CLI options including double-underscore notation
            cli_options = []
            cli_options.append(f"--config {prop_name}=value")
            if env_mapping:
                cli_options.append(f"--env {env_mapping}=value")
            # Add double-underscore notation for nested configs
            cli_options.append(f"--config {template_name}__{prop_name}=value")

            cli_options_text = "\n".join(cli_options)

            table.add_row(
                prop_name,
                prop_type,
                cli_options_text,
                env_mapping,
                default,
                is_required,
            )

        console.print(table)

        # Show usage examples
        console.print("\n[cyan]💡 Usage Examples:[/cyan]")

        example_configs = []
        for prop_name, prop_config in list(properties.items())[:2]:
            default_value = prop_config.get("default")
            if default_value is not None:
                example_configs.append(f"{prop_name}={default_value}")

        if example_configs:
            config_str = " ".join([f"--config {c}" for c in example_configs])
            console.print(
                f"  python -m mcp_template deploy {template_name} {config_str}"
            )

        # Show double-underscore notation example
        first_prop = list(properties.keys())[0] if properties else "property"
        console.print(
            f"  python -m mcp_template deploy {template_name} --config {template_name}__{first_prop}=value"
        )

        # Show config file example
        console.print(
            f"  python -m mcp_template deploy {template_name} --config-file config.json"
        )

    def list_tools(
        self,
        template_name: str,
        no_cache: bool = False,
        refresh: bool = False,
        config_values: Optional[Dict[str, str]] = None,
        force_server_discovery: bool = False,
    ) -> None:
        """List available tools for a template using enhanced tool discovery.

        Args:
            template_name: Name of the template
            no_cache: Ignore cached results
            refresh: Force refresh cached results
            config_values: Configuration values for dynamic discovery
            force_server_discovery: Force server discovery (MCP probe only, no static fallback)
        """
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            console.print(
                f"[dim]Available templates: {', '.join(self.templates.keys())}[/dim]"
            )
            return

        template = self.templates[template_name]
        template_dir = TEMPLATES_DIR / template_name

        console.print(
            Panel(
                f"Discovering Tools for Template: [cyan]{template_name}[/cyan]",
                title="🔧 Tool Discovery",
                border_style="blue",
            )
        )

        # Use the enhanced tool discovery system
        # Merge config_values into template config for dynamic discovery
        template_with_config = template.copy()
        if config_values:
            # Add config values as environment variables for Docker discovery
            existing_env_vars = template_with_config.get("env_vars", {})
            existing_env_vars.update(config_values)
            template_with_config["env_vars"] = existing_env_vars

        # For tool discovery, automatically add dummy credentials if none provided
        # This allows users to discover tools without needing real credentials
        template_with_config = self._add_dummy_credentials_for_discovery(
            template_name, template_with_config
        )

        discovery_result = self.tool_discovery.discover_tools(
            template_name=template_name,
            template_dir=template_dir,
            template_config=template_with_config,
            use_cache=not no_cache,
            force_refresh=refresh,
            force_server_discovery=force_server_discovery,
        )
        tools = discovery_result.get("tools", [])
        discovery_method = discovery_result.get("discovery_method", "unknown")
        source = (
            discovery_result.get("source_file")
            or discovery_result.get("source_endpoint")
            or "template.json"
        )

        # Check if we need to fallback to Docker image discovery
        if (not tools or discovery_method == "unknown") and template.get(
            "tool_discovery"
        ) == "dynamic":
            console.print(
                "[yellow]⚠️  Standard discovery failed, attempting Docker image discovery...[/yellow]"
            )

            # Extract Docker image information from template
            docker_image = template.get("docker_image")
            docker_tag = template.get("docker_tag", "latest")

            if docker_image:
                full_image_name = f"{docker_image}:{docker_tag}"
                console.print(f"[dim]Using Docker image: {full_image_name}[/dim]")

                # Prepare server arguments from config values if provided
                server_args = []
                if config_values:
                    # Convert config values to environment variables or command line args
                    # based on template's config schema
                    config_schema = template.get("config_schema", {})
                    properties = config_schema.get("properties", {})

                    for key, value in config_values.items():
                        if key in properties:
                            env_mapping = properties[key].get("env_mapping")
                            if env_mapping:
                                server_args.extend(["--env", f"{env_mapping}={value}"])

                # Attempt Docker discovery
                docker_result = self.docker_probe.discover_tools_from_image(
                    full_image_name, server_args if server_args else None
                )

                if docker_result and docker_result.get("tools"):
                    tools = docker_result["tools"]
                    discovery_method = docker_result.get("discovery_method", "docker")
                    source = f"Docker image: {full_image_name}"
                    console.print(
                        "[green]✅ Successfully discovered tools from Docker image[/green]"
                    )
                else:
                    console.print("[red]❌ Docker image discovery also failed[/red]")
            else:
                console.print(
                    "[yellow]⚠️  No Docker image specified in template config[/yellow]"
                )

        # Show discovery info
        console.print(f"[dim]Discovery method: {discovery_method}[/dim]")
        console.print(f"[dim]Source: {source}[/dim]")

        if "timestamp" in discovery_result:
            timestamp = datetime.datetime.fromtimestamp(discovery_result["timestamp"])
            console.print(
                f"[dim]Last updated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]"
            )

        if not tools:
            console.print("[yellow]⚠️  No tools found for this template[/yellow]")
            if "warnings" in discovery_result:
                for warning in discovery_result["warnings"]:
                    console.print(f"[yellow]⚠️  {warning}[/yellow]")
            return
        # Display tools in a table
        if self.beautifier:
            self.beautifier.beautify_tools_list(tools, f"{discovery_method} ({source})")
        else:
            self._display_tools_table(tools)

        # Show usage examples
        self._show_tool_usage_examples(template_name, template, tools)
        return True

    def _display_tools_table(self, tools):
        """Display tools in a formatted table."""
        table = Table()
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Category", style="green", width=15)
        table.add_column("Parameters", style="yellow", width=25)

        for tool in tools:
            tool_name = tool.get("name", "Unknown")
            description = tool.get("description", "No description")
            category = tool.get("category", "general")

            # Format parameters
            parameters = tool.get("parameters", [])
            if isinstance(parameters, list) and parameters:
                param_count = len(parameters)
                param_text = f"{param_count} parameter{'s' if param_count != 1 else ''}"
            elif isinstance(parameters, dict):
                param_text = "Schema defined"
            else:
                param_text = "No parameters"

            table.add_row(tool_name, description, category, param_text)

        console.print(table)

    def _show_tool_usage_examples(
        self, template_name: str, template: dict, tools: list
    ):
        """Show usage examples for the discovered tools."""
        console.print("\n[cyan]💡 Tool Usage Examples:[/cyan]")

        # Get transport info
        transport_info = template.get("transport", {})
        default_transport = transport_info.get("default", "http")
        port = transport_info.get("port", 7071)

        if default_transport == "http":
            console.print(f"  # HTTP endpoint: http://localhost:{port}")
            console.print("  # FastMCP client example:")
            console.print("  from fastmcp.client import FastMCPClient")
            console.print(
                f'  client = FastMCPClient(endpoint="http://localhost:{port}")'
            )

            # Show example tool calls for first 2 tools
            for tool in tools[:2]:
                tool_name = tool.get("name")
                if tool_name:
                    console.print(f'  result = client.call_tool("{tool_name}", {{}})')

        console.print(f"\n  # Deploy template: mcp-template deploy {template_name}")
        console.print(f"  # View logs: mcp-template logs {template_name}")

    def discover_tools_from_image(
        self,
        image_name: str,
        server_args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Discover tools from a Docker image."""
        console.print(
            Panel(
                f"Discovering Tools from Docker Image: [cyan]{image_name}[/cyan]",
                title="🐳 Docker Tool Discovery",
                border_style="blue",
            )
        )
        # Use Docker probe to discover tools
        result = self.docker_probe.discover_tools_from_image(
            image_name, server_args, env_vars
        )
        if result:
            tools = result.get("tools", [])
            discovery_method = result.get("discovery_method", "unknown")
            console.print(
                f"[green]✅ Discovered {len(tools)} tools via {discovery_method}[green]"
            )
            if tools:
                self._display_tools_table(tools)
                # Show MCP client usage example
                console.print("\n[cyan]💡 Usage Example:[/cyan]")
                console.print("  # Using MCP client directly:")
                console.print(
                    "  from mcp_template.tools.mcp_client_probe import MCPClientProbe"
                )
                console.print("  client = MCPClientProbe()")
                args_str = str(server_args) if server_args else "[]"
                console.print(
                    f"  result = client.discover_tools_from_docker_sync('{image_name}', {args_str})"
                )
            else:
                console.print("[yellow]⚠️  No tools found in the image[yellow]")
            return True
        else:
            console.print("[red]❌ Failed to discover tools from image[red]")
            return False

    def show_integration_examples(
        self, template_name: str, llm: Optional[str] = None
    ) -> None:
        """Show integration examples for various LLMs and frameworks."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.templates[template_name]
        transport_info = template.get("transport", {})
        port = transport_info.get("port", 7071)

        console.print(
            Panel(
                f"Integration Examples for [cyan]{template_name}[/cyan]",
                title="🔗 LLM Integration",
                border_style="blue",
            )
        )

        # Get example tools for demonstrations
        tools = template.get("tools", [])
        example_tool = tools[0] if tools else {"name": "example_tool", "parameters": []}

        integrations = {
            "fastmcp": {
                "title": "FastMCP Client",
                "code": f"""from fastmcp.client import FastMCPClient

# Connect to the server
client = FastMCPClient(endpoint="http://localhost:{port}")

# Call a tool
result = client.call("{example_tool['name']}")
print(result)

# List available tools
tools = client.list_tools()
for tool in tools:
    print(f"Tool: {{tool.name}} - {{tool.description}}")""",
            },
            "claude": {
                "title": "Claude Desktop Integration",
                "code": f"""{{
  "mcpServers": {{
    "{template_name}": {{
      "command": "docker",
      "args": ["exec", "-i", "mcp-{template_name}", "python", "server.py", "--transport", "stdio"]
    }}
  }}
}}

# Add this to your Claude Desktop configuration file:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Windows: %APPDATA%\\Claude\\claude_desktop_config.json""",
            },
            "vscode": {
                "title": "VS Code MCP Integration",
                "code": f"""{{
  "mcp.servers": {{
    "{template_name}": {{
      "command": "python",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/path/to/templates/{template_name}"
    }}
  }}
}}

# Add this to your VS Code settings.json""",
            },
            "curl": {
                "title": "Direct HTTP API Testing",
                "code": f"""# Test tool availability
curl -X GET http://localhost:{port}/tools

# Call a tool
curl -X POST http://localhost:{port}/call \\
  -H "Content-Type: application/json" \\
  -d '{{"method": "{example_tool['name']}", "params": {{}}}}'

# Health check
curl -X GET http://localhost:{port}/health""",
            },
            "python": {
                "title": "Direct Python Integration",
                "code": f"""import requests
import json

# Define the endpoint
endpoint = "http://localhost:{port}"

# Call a tool
response = requests.post(
    f"{{endpoint}}/call",
    json={{
        "method": "{example_tool['name']}",
        "params": {{}}
    }}
)

if response.status_code == 200:
    result = response.json()
    print("Tool result:", result)
else:
    print("Error:", response.text)""",
            },
        }

        if llm and llm in integrations:
            # Show specific integration
            integration = integrations[llm]
            console.print(f"\n[cyan]📋 {integration['title']}:[/cyan]")
            console.print(
                Panel(
                    integration["code"],
                    title=f"{integration['title']} Example",
                    border_style="green",
                )
            )
        else:
            # Show all integrations
            for key, integration in integrations.items():
                console.print(f"\n[cyan]📋 {integration['title']}:[/cyan]")
                console.print(
                    Panel(
                        integration["code"],
                        title=f"{integration['title']} Example",
                        border_style="green",
                    )
                )

    def setup_docker_network(self) -> bool:
        """Setup Docker network for MCP platform."""
        network_name = "mcp-platform"

        try:
            # Check if network already exists
            result = subprocess.run(
                [
                    "docker",
                    "network",
                    "ls",
                    "--filter",
                    f"name={network_name}",
                    "--format",
                    "{{.Name}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if network_name in result.stdout:
                console.print(
                    f"[green]✅ Docker network '{network_name}' already exists[/green]"
                )
                return True

            # Create the network
            subprocess.run(
                ["docker", "network", "create", network_name],
                check=True,
                capture_output=True,
            )

            console.print(f"[green]✅ Created Docker network '{network_name}'[/green]")
            return True

        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ Failed to setup Docker network: {e}[/red]")
            return False
        except FileNotFoundError:
            console.print(
                "[red]❌ Docker not found. Please install Docker first.[/red]"
            )
            return False

    def deploy_with_transport(
        self, template_name: str, transport: str = None, port: int = 7071, **kwargs
    ) -> bool:
        """Deploy template with specified transport options."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return False

        template = self.templates[template_name]

        if not transport:
            # Default to HTTP transport if not specified
            transport = template.get("transport", {}).get("default", "http")

        # Validate transport
        supported_transports = template.get("transport", {}).get("supported", ["http"])
        if transport not in supported_transports:
            console.print(
                f"[red]❌ Transport '{transport}' not supported by {template_name}[/red]"
            )
            console.print(f"Supported transports: {', '.join(supported_transports)}")
            return False

        # Check if this is a stdio deployment - prevent it with helpful message
        if transport == "stdio":
            # Get available tools for this template
            try:
                discovery_result = self.tool_discovery.discover_tools(
                    template_name,
                    template.get("template_dir", ""),
                    template,
                    use_cache=True,
                    force_refresh=False,
                )
                tools = discovery_result.get("tools", [])
                tool_names = [tool.get("name", "unknown") for tool in tools]
            except Exception as e:
                logger.warning("Failed to discover tools for %s: %s", template_name, e)
                tool_names = []

            # Create error message with available tools
            console.line()
            console.print(
                Panel(
                    f"❌ [red]Cannot deploy stdio transport MCP servers[/red]\n\n"
                    f"The template [cyan]{template_name}[/cyan] uses stdio transport, which doesn't require deployment.\n"
                    f"Stdio MCP servers run interactively and cannot be deployed as persistent containers.\n\n"
                    f"[yellow]Available tools in this template:[/yellow]\n"
                    + (
                        f"  • {chr(10).join(f'  • {tool}' for tool in tool_names)}"
                        if tool_names
                        else "  • No tools discovered"
                    )
                    + "\n\n"
                    f"[green]To use this template, run tools directly:[/green]\n"
                    f"  mcp-template tools {template_name}                    # List available tools\n"
                    f"  mcp-template run-tool {template_name} <tool_name>     # Run a specific tool\n"
                    f"  echo '{json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})}' | \\\n"
                    f"    docker run -i --rm {template.get('docker_image', f'mcp-{template_name}:latest')}",
                    title="Stdio Transport Detected",
                    border_style="yellow",
                )
            )
            return False

        console.print(
            Panel(
                f"🚀 Deploying [cyan]{template_name}[/cyan] with [yellow]{transport}[/yellow] transport",
                title="MCP Template Deployment",
                border_style="blue",
            )
        )

        # Setup Docker network if using HTTP transport
        if transport == "http":
            if not self.setup_docker_network():
                console.print(
                    "[yellow]⚠️  Continuing without Docker network setup[/yellow]"
                )

        # Add transport-specific configuration
        config_values = kwargs.get("config_values", {})
        if transport == "http":
            config_values["transport"] = "http"
            config_values["port"] = str(port)
        elif transport == "stdio":
            config_values["transport"] = "stdio"

        kwargs["config_values"] = config_values

        # Deploy using the existing deployer
        return self.deployer.deploy(template_name, **kwargs)

    def run_stdio_tool(
        self,
        template_name: str,
        tool_name: str,
        tool_args: Optional[str] = None,
        config_values: Optional[Dict[str, str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> bool:
        """Run a specific tool from a stdio MCP template."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return False

        template = self.templates[template_name]

        # Check if template supports stdio
        transport = template.get("transport", {})
        default_transport = transport.get("default", "http")
        supported_transports = transport.get("supported", ["http"])

        if "stdio" not in supported_transports and default_transport != "stdio":
            console.print(
                f"[red]❌ Template '{template_name}' does not support stdio transport[/red]"
            )
            console.print(f"Supported transports: {', '.join(supported_transports)}")
            return False

        console.print(
            Panel(
                f"🔧 Running tool [yellow]{tool_name}[/yellow] from template [cyan]{template_name}[/cyan]",
                title="MCP Tool Execution",
                border_style="blue",
            )
        )

        # Prepare configuration
        config = {}
        if config_values:
            config.update(config_values)
        if env_vars:
            config.update(env_vars)

        # Parse tool arguments if provided
        tool_arguments = {}
        if tool_args:
            try:
                tool_arguments = json.loads(tool_args)
            except json.JSONDecodeError:
                console.print(
                    f"[red]❌ Invalid JSON in tool arguments: {tool_args}[/red]"
                )
                return False

        # Create the MCP request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": tool_arguments},
        }

        # Convert to JSON string
        json_input = json.dumps(mcp_request)

        try:
            result = self.docker_service.run_stdio_command(
                template_name,
                config,
                template,
                json_input,
                pull_image=True,
            )

            if result["status"] == "completed":
                console.print("[green]✅ Tool executed successfully[/green]")

                # Use beautifier if available, otherwise fall back to existing logic
                if self.beautifier:
                    logger.debug("Using enhanced beautifier")
                    try:
                        self.beautifier.beautify_tool_response(result)
                        return  True
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Beautifier error: {e}[/yellow]")
                        console.print("[dim]Falling back to legacy output...[/dim]")
                        # Fall through to legacy logic
                else:
                    logger.debug("No beautifier available, using legacy logic")

                stdout_content = result["stdout"]
                stderr_content = result["stderr"]

                # Log for debugging
                logger.debug("Raw stdout: %s", repr(stdout_content))
                logger.debug("Raw stderr: %s", repr(stderr_content))

                # Try to parse and display the response nicely
                # Look for JSON-RPC response in the output
                json_responses = []
                for line in stdout_content.split("\n"):
                    line = line.strip()
                    if (
                        line.startswith('{"jsonrpc"')
                        or line.startswith('{"result"')
                        or line.startswith('{"error"')
                    ):
                        try:
                            json_response = json.loads(line)
                            json_responses.append(json_response)
                        except json.JSONDecodeError:
                            continue

                # Find the tool call response (should be the last response or one with id=3)
                tool_response = None
                for response in json_responses:
                    if response.get("id") == 3:  # Tool call has id=3 in our sequence
                        tool_response = response
                        break

                    # If no id=3 response, use the last response (might be the tool result)
                    if not tool_response and json_responses:
                        tool_response = json_responses[-1]

                    if tool_response:
                        if "result" in tool_response:
                            # Check if result has content (MCP response format)
                            result_data = tool_response["result"]
                            if (
                                isinstance(result_data, dict)
                                and "content" in result_data
                            ):
                                # MCP format with content array
                                content_items = result_data["content"]
                                if isinstance(content_items, list) and content_items:
                                    # Display the first content item
                                    first_content = content_items[0]
                                    if (
                                        isinstance(first_content, dict)
                                        and "text" in first_content
                                    ):
                                        console.print(
                                            Panel(
                                                first_content["text"],
                                                title="Tool Result",
                                                border_style=(
                                                    "green"
                                                    if not result_data.get("isError")
                                                    else "red"
                                                ),
                                            )
                                        )
                                    else:
                                        console.print(
                                            Panel(
                                                json.dumps(content_items, indent=2),
                                                title="Tool Result",
                                                border_style="green",
                                            )
                                        )
                                else:
                                    console.print(
                                        Panel(
                                            json.dumps(result_data, indent=2),
                                            title="Tool Result",
                                            border_style="green",
                                        )
                                    )
                            else:
                                # Simple result
                                console.print(
                                    Panel(
                                        json.dumps(result_data, indent=2),
                                        title="Tool Result",
                                        border_style="green",
                                    )
                                )
                        elif "error" in tool_response:
                            # JSON-RPC error
                            error_info = tool_response["error"]
                            console.print(
                                Panel(
                                    f"Error {error_info.get('code', 'unknown')}: {error_info.get('message', 'Unknown error')}",
                                    title="Tool Error",
                                    border_style="red",
                                )
                            )
                        else:
                            # Raw JSON response
                            console.print(
                                Panel(
                                    json.dumps(tool_response, indent=2),
                                    title="MCP Response",
                                    border_style="blue",
                                )
                            )
                    else:
                        # No tool response found, show raw output
                        console.print(
                            Panel(
                                stdout_content,
                                title="Raw Output",
                                border_style="blue",
                            )
                        )

                    if stderr_content and self._is_actual_error(stderr_content):
                        console.print(
                            Panel(
                                stderr_content,
                                title="Standard Error",
                                border_style="yellow",
                            )
                        )
                    elif stderr_content and not self._is_actual_error(stderr_content):
                        # Show non-error stderr as debug info only if verbose
                        if hasattr(self, "verbose") and self.verbose:
                            console.print(
                                Panel(
                                    stderr_content,
                                    title="Debug Info",
                                    border_style="dim",
                                )
                            )
                return True
            else:
                console.print(
                    f"[red]❌ Tool execution failed: {result.get('error', 'Unknown error')}[/red]"
                )
                if result.get("stderr"):
                    console.print(
                        Panel(
                            result["stderr"],
                            title="Error Output",
                            border_style="red",
                        )
                    )
                return False

        except Exception as e:
            console.print(f"[red]❌ Failed to execute tool: {e}[/red]")
            return False

    def _add_dummy_credentials_for_discovery(
        self, template_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add dummy credentials for tool discovery to avoid prompting users."""
        # Use the same logic as the discovery module
        return self.tool_discovery._add_dummy_credentials(template_name, config)


def add_enhanced_cli_args(subparsers) -> None:
    """Add enhanced CLI arguments to the argument parser."""

    # Interactive CLI command (with 'i' alias)
    interactive_parser = subparsers.add_parser(
        "interactive",
        aliases=["i"],
        help="Start interactive CLI session for MCP management",
    )

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Show configuration options for a template"
    )
    config_parser.add_argument("template", help="Template name")

    # Tools command (unified)
    tools_parser = subparsers.add_parser(
        "tools",
        help="List available tools for a template or discover tools from a Docker image",
    )
    tools_parser.add_argument(
        "template", nargs="?", help="Template name (optional if using --image)"
    )
    tools_parser.add_argument(
        "--image", help="Docker image name to discover tools from"
    )
    tools_parser.add_argument(
        "--no-cache", action="store_true", help="Ignore cached results"
    )
    tools_parser.add_argument(
        "--refresh", action="store_true", help="Force refresh cached results"
    )
    tools_parser.add_argument(
        "--force-server",
        action="store_true",
        help="Force server discovery (MCP probe only, no static fallback)",
    )
    tools_parser.add_argument(
        "--config",
        action="append",
        help="Configuration values for dynamic discovery (KEY=VALUE)",
    )
    tools_parser.add_argument(
        "server_args",
        nargs="*",
        help="Server arguments (when using --image)",
    )

    # Discover tools command (deprecated, for backward compatibility)
    discover_parser = subparsers.add_parser(
        "discover-tools", help="[DEPRECATED] Use 'tools --image' instead"
    )
    discover_parser.add_argument("--image", required=True, help="Docker image name")
    discover_parser.add_argument(
        "server_args", nargs="*", help="Arguments to pass to the MCP server"
    )

    # Connect command
    connect_parser = subparsers.add_parser(
        "connect", help="Show integration examples for LLMs and frameworks"
    )
    connect_parser.add_argument("template", help="Template name")
    connect_parser.add_argument(
        "--llm",
        choices=["fastmcp", "claude", "vscode", "curl", "python"],
        help="Show specific LLM integration example",
    )

    # Run command (alternative to deploy with transport options)
    run_parser = subparsers.add_parser(
        "run", help="Run a template with transport options"
    )
    run_parser.add_argument("template", help="Template name")
    run_parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport type (default: http)",
    )
    run_parser.add_argument(
        "--port", type=int, default=7071, help="Port for HTTP transport (default: 7071)"
    )
    run_parser.add_argument("--data-dir", help="Custom data directory")
    run_parser.add_argument("--config-dir", help="Custom config directory")
    run_parser.add_argument(
        "--env", action="append", help="Environment variables (KEY=VALUE)"
    )
    run_parser.add_argument(
        "--config-file", help="Path to JSON/YAML configuration file"
    )
    run_parser.add_argument(
        "--config", action="append", help="Configuration values (KEY=VALUE)"
    )

    # Run-tool command for stdio MCP servers
    run_tool_parser = subparsers.add_parser(
        "run-tool", help="Run a specific tool from a stdio MCP template"
    )
    run_tool_parser.add_argument("template", help="Template name")
    run_tool_parser.add_argument("tool_name", help="Name of the tool to run")
    run_tool_parser.add_argument(
        "--args", help="JSON arguments to pass to the tool (optional)"
    )
    run_tool_parser.add_argument(
        "--config", action="append", help="Configuration values (KEY=VALUE)"
    )
    run_tool_parser.add_argument(
        "--env", action="append", help="Environment variables (KEY=VALUE)"
    )

def handle_enhanced_cli_commands(args) -> bool:
    """Handle enhanced CLI commands."""
    enhanced_cli = EnhancedCLI()
    if args.command in ["interactive", "i"]:
        # Start interactive CLI session
        from mcp_template.interactive_cli import start_interactive_cli

        start_interactive_cli()
        return True

    elif args.command == "config":
        enhanced_cli.show_config_options(args.template)
        return True

    elif args.command == "tools":
        # Parse config values if provided
        config_values = {}
        if hasattr(args, "config") and args.config:
            for config_var in args.config:
                try:
                    key, value = config_var.split("=", 1)
                    config_values[key] = value
                except ValueError:
                    console.print(
                        f"[red]❌ Invalid config format: {config_var}. Use KEY=VALUE[/red]"
                    )
                    return False

        # Handle unified tools command
        if args.image:
            # Docker image discovery (former discover-tools functionality)
            server_args = args.server_args if hasattr(args, "server_args") else []
            enhanced_cli.discover_tools_from_image(
                args.image, server_args, config_values
            )
        elif hasattr(args, "template") and args.template:
            # Template-based discovery (former tools functionality)
            enhanced_cli.list_tools(
                args.template,
                no_cache=getattr(args, "no_cache", False),
                refresh=getattr(args, "refresh", False),
                config_values=config_values,
                force_server_discovery=getattr(args, "force_server", False),
            )
        else:
            # Error: must provide either template or --image
            console.print(
                "[red]❌ Must provide either a template name or --image parameter[/red]"
            )
            console.print("Examples:")
            console.print("  python -m mcp_template tools demo")
            console.print("  python -m mcp_template tools --image mcp/filesystem /tmp")
            console.print(
                "  python -m mcp_template tools github --config github_token=your_token"
            )
            return False
        return True

    elif args.command == "discover-tools":
        # Legacy command - redirect to unified tools command
        console.print(
            "[yellow]⚠️  The 'discover-tools' command is deprecated. Use 'tools --image' instead.[/yellow]"
        )
        enhanced_cli.discover_tools_from_image(args.image, args.server_args)
        return True

    elif args.command == "connect":
        enhanced_cli.show_integration_examples(
            args.template, llm=getattr(args, "llm", None)
        )
        return True

    elif args.command == "run":
        # Convert args to kwargs for deploy_with_transport
        env_vars = {}
        if hasattr(args, "env") and args.env:
            for env_var in args.env:
                key, value = env_var.split("=", 1)
                env_vars[key] = value

        config_values = {}
        if hasattr(args, "config") and args.config:
            for config_var in args.config:
                key, value = config_var.split("=", 1)
                config_values[key] = value

        enhanced_cli.deploy_with_transport(
            args.template,
            transport=args.transport,
            port=args.port,
            data_dir=getattr(args, "data_dir", None),
            config_dir=getattr(args, "config_dir", None),
            env_vars=env_vars,
            config_file=getattr(args, "config_file", None),
            config_values=config_values,
        )
        return True

    elif args.command == "run-tool":
        # Parse config values if provided
        config_values = {}
        if hasattr(args, "config") and args.config:
            for config_var in args.config:
                try:
                    key, value = config_var.split("=", 1)
                    config_values[key] = value
                except ValueError:
                    console.print(
                        f"[red]❌ Invalid config format: {config_var}. Use KEY=VALUE[/red]"
                    )
                    return False

        # Parse env vars if provided
        env_vars = {}
        if hasattr(args, "env") and args.env:
            for env_var in args.env:
                try:
                    key, value = env_var.split("=", 1)
                    env_vars[key] = value
                except ValueError:
                    console.print(
                        f"[red]❌ Invalid env format: {env_var}. Use KEY=VALUE[/red]"
                    )
                    return False
        # Return the result of run_stdio_tool instead of always True
        return enhanced_cli.run_stdio_tool(
            args.template,
            args.tool_name,
            tool_args=getattr(args, "args", None),
            config_values=config_values,
            env_vars=env_vars,
        )
