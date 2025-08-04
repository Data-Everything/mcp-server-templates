"""
Interactive CLI module for MCP Template management.

This module provides an interactive command-line interface for managing MCP servers,
tools, and configurations with persistent session state and beautified responses.
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any
from pathlib import Path
import cmd
import logging

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.tree import Tree

from mcp_template.cli import EnhancedCLI
from mcp_template.tools.cache import CacheManager
from mcp_template.deployer import MCPDeployer

console = Console()
logger = logging.getLogger(__name__)


class ResponseBeautifier:
    """Class for beautifying and formatting MCP responses."""

    def __init__(self):
        self.console = Console()

    def beautify_json(self, data: Any, title: str = "Response") -> None:
        """Display JSON data in a beautified format."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If it's not valid JSON, display as text
                self.console.print(Panel(data, title=title, border_style="blue"))
                return

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
        self.console.print(Panel(syntax, title=title, border_style="green"))

    def beautify_tool_response(self, response: Dict[str, Any]) -> None:
        """Beautify tool execution response."""
        if response.get("status") == "completed":
            stdout = response.get("stdout", "")
            stderr = response.get("stderr", "")

            # Try to parse stdout as JSON-RPC response
            try:
                lines = stdout.strip().split("\\n")
                json_responses = []

                for line in lines:
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

                # Find tool response
                tool_response = None
                for resp in json_responses:
                    if resp.get("id") == 3:  # Tool call response
                        tool_response = resp
                        break

                if not tool_response and json_responses:
                    tool_response = json_responses[-1]

                if tool_response:
                    if "result" in tool_response:
                        result_data = tool_response["result"]

                        # Handle MCP content format
                        if isinstance(result_data, dict) and "content" in result_data:
                            content_items = result_data["content"]
                            if isinstance(content_items, list) and content_items:
                                for i, content in enumerate(content_items):
                                    if isinstance(content, dict) and "text" in content:
                                        self.console.print(
                                            Panel(
                                                content["text"],
                                                title=f"Tool Result {i+1}",
                                                border_style="green",
                                            )
                                        )
                                    else:
                                        self.beautify_json(content, f"Content {i+1}")
                            else:
                                self.beautify_json(result_data, "Tool Result")
                        else:
                            self.beautify_json(result_data, "Tool Result")

                    elif "error" in tool_response:
                        error_info = tool_response["error"]
                        self.console.print(
                            Panel(
                                f"Error {error_info.get('code', 'unknown')}: {error_info.get('message', 'Unknown error')}",
                                title="Tool Error",
                                border_style="red",
                            )
                        )
                    else:
                        self.beautify_json(tool_response, "MCP Response")
                else:
                    # No JSON response found, show raw output
                    self.console.print(
                        Panel(stdout, title="Raw Output", border_style="blue")
                    )

            except Exception as e:
                # Fallback to raw output
                self.console.print(
                    Panel(stdout, title="Tool Output", border_style="blue")
                )

            # Show stderr if present
            if stderr:
                self.console.print(
                    Panel(stderr, title="Standard Error", border_style="yellow")
                )

        else:
            # Failed execution
            error_msg = response.get("error", "Unknown error")
            stderr = response.get("stderr", "")

            self.console.print(
                Panel(
                    f"Execution failed: {error_msg}",
                    title="Execution Error",
                    border_style="red",
                )
            )

            if stderr:
                self.console.print(
                    Panel(stderr, title="Error Details", border_style="red")
                )

    def beautify_tools_list(
        self, tools: List[Dict[str, Any]], source: str = "Template"
    ) -> None:
        """Beautify tools list display."""
        if not tools:
            self.console.print("[yellow]⚠️  No tools found[/yellow]")
            return

        # Create tools table
        table = Table(title=f"Available Tools ({len(tools)} found)")
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Parameters", style="yellow", width=15)
        table.add_column("Category", style="green", width=15)

        for tool in tools:
            name = tool.get("name", "Unknown")
            description = tool.get("description", "No description")

            # Handle parameters
            input_schema = tool.get("inputSchema", {})
            if isinstance(input_schema, dict):
                properties = input_schema.get("properties", {})
                param_count = len(properties) if properties else 0
                param_text = f"{param_count} params"
            else:
                param_text = "Schema defined"

            category = tool.get("category", "general")

            table.add_row(name, description, param_text, category)

        self.console.print(table)
        self.console.print(f"[dim]Source: {source}[/dim]")

    def beautify_deployed_servers(self, servers: List[Dict[str, Any]]) -> None:
        """Beautify deployed servers list."""
        if not servers:
            self.console.print("[yellow]⚠️  No deployed servers found[/yellow]")
            return

        table = Table(title=f"Deployed MCP Servers ({len(servers)} active)")
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Transport", style="yellow", width=12)
        table.add_column("Status", style="green", width=10)
        table.add_column("Endpoint", style="blue", width=30)
        table.add_column("Tools", style="magenta", width=10)

        for server in servers:
            template_name = server.get("template_name", "Unknown")
            transport = server.get("transport", "unknown")
            status = server.get("status", "unknown")
            endpoint = server.get("endpoint", "N/A")
            tool_count = len(server.get("tools", []))

            # Color status
            if status == "running":
                status_text = f"[green]{status}[/green]"
            elif status == "failed":
                status_text = f"[red]{status}[/red]"
            else:
                status_text = f"[yellow]{status}[/yellow]"

            table.add_row(
                template_name, transport, status_text, endpoint, str(tool_count)
            )

        self.console.print(table)


class InteractiveCLI(cmd.Cmd):
    """Interactive command-line interface for MCP Template management."""

    intro = """
╔══════════════════════════════════════════════════════════════╗
║                    MCP Interactive CLI                       ║
╠══════════════════════════════════════════════════════════════╣
║  Welcome to the MCP Template Interactive CLI!               ║
║  Type 'help' for available commands or 'quit' to exit.      ║
╚══════════════════════════════════════════════════════════════╝
"""

    prompt = "mcp> "

    def __init__(self):
        super().__init__()
        self.enhanced_cli = EnhancedCLI()
        self.deployer = MCPDeployer()
        self.cache = CacheManager()
        self.beautifier = ResponseBeautifier()

        # Session state
        self.session_configs = {}  # Template name -> config
        self.deployed_servers = []  # List of deployed servers info

    def cmdloop(self, intro=None):
        """Override cmdloop to handle KeyboardInterrupt gracefully."""
        try:
            super().cmdloop(intro)
        except KeyboardInterrupt:
            console.print("\\n[yellow]Session interrupted. Goodbye![/yellow]")
            return

    def do_list_servers(self, arg):
        """List all deployed MCP servers.
        Usage: list_servers
        """
        console.print("\\n[cyan]🔍 Discovering deployed MCP servers...[/cyan]")

        # Get deployed servers from deployer
        try:
            servers = self.deployer.list_active_deployments()
            self.deployed_servers = servers
            self.beautifier.beautify_deployed_servers(servers)
        except Exception as e:
            console.print(f"[red]❌ Failed to list servers: {e}[/red]")

    def do_tools(self, template_name):
        """List available tools for a template.
        Usage: tools <template_name>
        """
        if not template_name.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            console.print("Usage: tools <template_name>")
            return

        template_name = template_name.strip()

        console.print(
            f"\\n[cyan]🔧 Discovering tools for template: {template_name}[/cyan]"
        )

        # Check if we have cached config for this template
        config_values = self.session_configs.get(template_name, {})

        try:
            # Use enhanced CLI to discover tools
            if template_name not in self.enhanced_cli.templates:
                console.print(f"[red]❌ Template '{template_name}' not found[/red]")
                available = list(self.enhanced_cli.templates.keys())
                console.print(f"[dim]Available templates: {', '.join(available)}[/dim]")
                return

            template = self.enhanced_cli.templates[template_name]
            template_dir = self.enhanced_cli.template_discovery.get_template_dir(
                template_name
            )

            # Use enhanced tool discovery with cached config
            template_with_config = template.copy()
            if config_values:
                existing_env_vars = template_with_config.get("env_vars", {})
                existing_env_vars.update(config_values)
                template_with_config["env_vars"] = existing_env_vars

            discovery_result = self.enhanced_cli.tool_discovery.discover_tools(
                template_name=template_name,
                template_dir=template_dir,
                template_config=template_with_config,
                use_cache=True,
                force_refresh=False,
            )

            tools = discovery_result.get("tools", [])
            discovery_method = discovery_result.get("discovery_method", "unknown")
            source = discovery_result.get("source_file") or "template.json"

            self.beautifier.beautify_tools_list(tools, f"{discovery_method} ({source})")

            if tools:
                console.print(
                    f"\\n[green]💡 Use 'call {template_name} <tool_name> [args]' to execute a tool[/green]"
                )

        except Exception as e:
            console.print(f"[red]❌ Failed to discover tools: {e}[/red]")

    def do_config(self, args):
        """Set configuration for a template.
        Usage: config <template_name> <key>=<value> [<key2>=<value2> ...]
        """
        if not args.strip():
            console.print(
                "[red]❌ Please provide template name and configuration[/red]"
            )
            console.print(
                "Usage: config <template_name> <key>=<value> [<key2>=<value2> ...]"
            )
            return

        parts = args.strip().split()
        if len(parts) < 2:
            console.print(
                "[red]❌ Please provide template name and at least one config value[/red]"
            )
            return

        template_name = parts[0]
        config_pairs = parts[1:]

        # Parse config values
        config_values = {}
        for pair in config_pairs:
            if "=" not in pair:
                console.print(
                    f"[red]❌ Invalid config format: {pair}. Use KEY=VALUE[/red]"
                )
                return
            key, value = pair.split("=", 1)
            config_values[key] = value

        # Store in session
        if template_name not in self.session_configs:
            self.session_configs[template_name] = {}
        self.session_configs[template_name].update(config_values)

        # Cache configuration
        cache_key = f"interactive_config_{template_name}"
        self.cache.set(cache_key, self.session_configs[template_name])

        console.print(
            f"[green]✅ Configuration saved for template '{template_name}'[/green]"
        )

        # Display current config
        current_config = self.session_configs[template_name]
        table = Table(title=f"Configuration for {template_name}")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in current_config.items():
            # Mask sensitive values
            display_value = (
                "***"
                if any(
                    sensitive in key.lower()
                    for sensitive in ["token", "key", "secret", "password"]
                )
                else value
            )
            table.add_row(key, display_value)

        console.print(table)

    def do_call(self, args):
        """Call a tool from a template.
        Usage: call <template_name> <tool_name> [json_args]
        """
        if not args.strip():
            console.print("[red]❌ Please provide template name and tool name[/red]")
            console.print("Usage: call <template_name> <tool_name> [json_args]")
            return

        parts = args.strip().split(None, 2)
        if len(parts) < 2:
            console.print(
                "[red]❌ Please provide both template name and tool name[/red]"
            )
            return

        template_name = parts[0]
        tool_name = parts[1]
        tool_args = parts[2] if len(parts) > 2 else "{}"

        console.print(
            f"\\n[cyan]🚀 Calling tool '{tool_name}' from template '{template_name}'[/cyan]"
        )

        # Check if template exists
        if template_name not in self.enhanced_cli.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.enhanced_cli.templates[template_name]
        transport_config = template.get("transport", {})
        default_transport = transport_config.get("default", "http")
        supported_transports = transport_config.get("supported", ["http"])

        # Get cached config
        config_values = self.session_configs.get(template_name, {})

        # Handle different transport protocols
        if "stdio" in supported_transports or default_transport == "stdio":
            # Use stdio approach
            console.print("[dim]Using stdio transport...[/dim]")

            # Prompt for config if not cached
            if not config_values:
                console.print(
                    f"[yellow]⚠️  No configuration found for '{template_name}'[/yellow]"
                )
                if Confirm.ask("Would you like to set configuration now?"):
                    self.do_config(f"{template_name} ")
                    return

            try:
                result = self.enhanced_cli.run_stdio_tool(
                    template_name, tool_name, tool_args, config_values
                )

                # The enhanced CLI already beautifies stdio responses
                if not result:
                    console.print("[red]❌ Tool execution failed[/red]")

            except Exception as e:
                console.print(f"[red]❌ Failed to execute tool: {e}[/red]")

        else:
            # Handle HTTP/SSE transports - check if server is deployed
            console.print("[dim]Checking for deployed server...[/dim]")

            # Find deployed server
            deployed_server = None
            for server in self.deployed_servers:
                if server.get("template_name") == template_name:
                    deployed_server = server
                    break

            if not deployed_server:
                console.print(
                    f"[yellow]⚠️  Template '{template_name}' is not deployed[/yellow]"
                )
                console.print(
                    f"[dim]Supported transports: {', '.join(supported_transports)}[/dim]"
                )

                if Confirm.ask(f"Would you like to deploy '{template_name}' now?"):
                    # TODO: Integrate with deployment logic
                    console.print(
                        "[blue]🚀 Deployment integration coming soon...[/blue]"
                    )
                    return
                else:
                    return

            # Call tool on deployed server
            console.print(
                f"[dim]Calling tool on deployed server at {deployed_server.get('endpoint')}[/dim]"
            )
            # TODO: Implement HTTP tool calling
            console.print(
                "[blue]📡 HTTP tool calling integration coming soon...[/blue]"
            )

    def do_show_config(self, template_name):
        """Show current configuration for a template.
        Usage: show_config <template_name>
        """
        if not template_name.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            return

        template_name = template_name.strip()

        if template_name not in self.session_configs:
            console.print(
                f"[yellow]⚠️  No configuration found for '{template_name}'[/yellow]"
            )
            return

        config = self.session_configs[template_name]
        table = Table(title=f"Configuration for {template_name}")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in config.items():
            # Mask sensitive values
            display_value = (
                "***"
                if any(
                    sensitive in key.lower()
                    for sensitive in ["token", "key", "secret", "password"]
                )
                else value
            )
            table.add_row(key, display_value)

        console.print(table)

    def do_clear_config(self, template_name):
        """Clear configuration for a template.
        Usage: clear_config <template_name>
        """
        if not template_name.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            return

        template_name = template_name.strip()

        if template_name in self.session_configs:
            del self.session_configs[template_name]

            # Clear from cache
            cache_key = f"interactive_config_{template_name}"
            self.cache.remove(cache_key)

            console.print(
                f"[green]✅ Configuration cleared for '{template_name}'[/green]"
            )
        else:
            console.print(
                f"[yellow]⚠️  No configuration found for '{template_name}'[/yellow]"
            )

    def do_templates(self, arg):
        """List all available templates.
        Usage: templates
        """
        templates = self.enhanced_cli.templates

        if not templates:
            console.print("[yellow]⚠️  No templates found[/yellow]")
            return

        table = Table(title=f"Available Templates ({len(templates)} found)")
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Transport", style="yellow", width=15)
        table.add_column("Default Port", style="green", width=12)
        table.add_column("Tools", style="magenta", width=10)
        table.add_column("Description", style="white", width=40)

        for name, template in templates.items():
            transport_config = template.get("transport", {})
            default_transport = transport_config.get("default", "http")
            port = transport_config.get("port", "N/A")
            tools = template.get("tools", [])
            tool_count = len(tools) if tools else "Unknown"
            description = template.get("description", "No description")

            table.add_row(
                name, default_transport, str(port), str(tool_count), description
            )

        console.print(table)
        console.print(
            "\\n[green]💡 Use 'tools <template_name>' to see available tools[/green]"
        )
        console.print(
            "[green]💡 Use 'config <template_name> key=value' to set configuration[/green]"
        )

    def do_quit(self, arg):
        """Exit the interactive CLI.
        Usage: quit
        """
        console.print(
            "\\n[green]👋 Goodbye! Thanks for using MCP Interactive CLI![/green]"
        )
        return True

    def do_exit(self, arg):
        """Exit the interactive CLI.
        Usage: exit
        """
        return self.do_quit(arg)

    def do_help(self, arg):
        """Show help information.
        Usage: help [command]
        """
        if arg:
            super().do_help(arg)
        else:
            console.print(
                Panel(
                    """
[cyan]Available Commands:[/cyan]

[yellow]Server Management:[/yellow]
  • list_servers          - List all deployed MCP servers
  • templates             - List all available templates

[yellow]Tool Operations:[/yellow]
  • tools <template>      - List available tools for a template
  • call <template> <tool> [args] - Call a tool (stdio or HTTP)

[yellow]Configuration:[/yellow]
  • config <template> key=value   - Set configuration for a template
  • show_config <template>        - Show current template configuration
  • clear_config <template>       - Clear template configuration

[yellow]General:[/yellow]
  • help [command]        - Show this help or help for specific command
  • quit / exit           - Exit the interactive CLI

[green]Examples:[/green]
  • templates
  • config github GITHUB_TOKEN=your_token_here
  • tools github
  • call github search_repositories {"query": "python"}
""",
                    title="MCP Interactive CLI Help",
                    border_style="blue",
                )
            )

    def emptyline(self):
        """Override to do nothing on empty line."""
        pass

    def default(self, line):
        """Handle unknown commands."""
        console.print(f"[red]❌ Unknown command: {line}[/red]")
        console.print("[dim]Type 'help' for available commands[/dim]")


def start_interactive_cli():
    """Start the interactive CLI session."""
    console.print("[green]🚀 Starting MCP Interactive CLI...[/green]")

    try:
        cli = InteractiveCLI()
        cli.cmdloop()
    except Exception as e:
        console.print(f"[red]❌ Failed to start interactive CLI: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    start_interactive_cli()
