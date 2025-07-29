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

import logging
import subprocess

# Import existing components
# Note: Import classes directly to avoid circular import
from typing import List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_template.deployer import MCPDeployer
from mcp_template.template.discovery import TemplateDiscovery
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
        self, template_name: str, no_cache: bool = False, refresh: bool = False
    ) -> None:
        """List available tools for a template using enhanced tool discovery."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.templates[template_name]
        template_dir = TEMPLATES_DIR / template_name

        console.print(
            Panel(
                f"Discovering Tools for [cyan]{template_name}[/cyan]",
                title="🔧 Tool Discovery",
                border_style="blue",
            )
        )

        # Use the enhanced tool discovery system
        discovery_result = self.tool_discovery.discover_tools(
            template_name=template_name,
            template_dir=template_dir,
            template_config=template,
            use_cache=not no_cache,
            force_refresh=refresh,
        )

        tools = discovery_result.get("tools", [])
        discovery_method = discovery_result.get("discovery_method", "unknown")
        source = (
            discovery_result.get("source_file")
            or discovery_result.get("source_endpoint")
            or "template.json"
        )

        # Show discovery info
        console.print(f"[dim]Discovery method: {discovery_method}[/dim]")
        console.print(f"[dim]Source: {source}[/dim]")

        if "timestamp" in discovery_result:
            import datetime

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
        self._display_tools_table(tools)

        # Show usage examples
        self._show_tool_usage_examples(template_name, template, tools)

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
        self, image_name: str, server_args: Optional[List[str]] = None
    ) -> None:
        """Discover tools from a Docker image."""
        console.print(
            Panel(
                f"Discovering Tools from Docker Image: [cyan]{image_name}[/cyan]",
                title="🐳 Docker Tool Discovery",
                border_style="blue",
            )
        )

        # Use Docker probe to discover tools
        result = self.docker_probe.discover_tools_from_image(image_name, server_args)

        if result:
            tools = result.get("tools", [])
            discovery_method = result.get("discovery_method", "unknown")
            console.print(
                f"[green]✅ Discovered {len(tools)} tools via {discovery_method}[/green]"
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
                console.print("[yellow]⚠️  No tools found in the image[/yellow]")
        else:
            console.print("[red]❌ Failed to discover tools from image[/red]")

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
        self, template_name: str, transport: str = "http", port: int = 7071, **kwargs
    ) -> bool:
        """Deploy template with specified transport options."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return False

        template = self.templates[template_name]

        # Validate transport
        supported_transports = template.get("transport", {}).get("supported", ["http"])
        if transport not in supported_transports:
            console.print(
                f"[red]❌ Transport '{transport}' not supported by {template_name}[/red]"
            )
            console.print(f"Supported transports: {', '.join(supported_transports)}")
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


def add_enhanced_cli_args(subparsers) -> None:
    """Add enhanced CLI arguments to the argument parser."""

    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Show configuration options for a template"
    )
    config_parser.add_argument("template", help="Template name")

    # Tools command
    tools_parser = subparsers.add_parser(
        "tools", help="List available tools for a template"
    )
    tools_parser.add_argument("template", help="Template name")
    tools_parser.add_argument(
        "--no-cache", action="store_true", help="Ignore cached results"
    )
    tools_parser.add_argument(
        "--refresh", action="store_true", help="Force refresh cached results"
    )

    # Discover tools command for Docker images
    discover_parser = subparsers.add_parser(
        "discover-tools", help="Discover tools from a Docker image"
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


def handle_enhanced_cli_commands(args, enhanced_cli: EnhancedCLI) -> bool:
    """Handle enhanced CLI commands."""

    if args.command == "config":
        enhanced_cli.show_config_options(args.template)
        return True

    elif args.command == "tools":
        enhanced_cli.list_tools(
            args.template,
            no_cache=getattr(args, "no_cache", False),
            refresh=getattr(args, "refresh", False),
        )
        return True

    elif args.command == "discover-tools":
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

    return False
