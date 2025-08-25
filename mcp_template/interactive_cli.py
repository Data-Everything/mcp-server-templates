"""
Enhanced Interactive CLI using Typer for MCP Template management.

This module provides a modern interactive command-line interface built with Typer
that replaces the cmd2-based interactive CLI with:
- Dynamic argument handling using Typer
- Client-based operations for consistency with main CLI
- Better error handling and validation
- Rich formatting and user-friendly responses
- Session state management
- Command history with up/down arrow keys
- Tab completion for commands and template names
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional, Union

try:
    import readline

    READLINE_AVAILABLE = True
except ImportError:
    READLINE_AVAILABLE = False

import shlex

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from mcp_template.client import MCPClient
from mcp_template.core.cache import CacheManager
from mcp_template.core.response_formatter import ResponseFormatter

console = Console()
logger = logging.getLogger(__name__)

# Command completion setup
COMMANDS = [
    "help",
    "templates",
    "select",
    "unselect",
    "tools",
    "call",
    "config",
    "servers",
    "deploy",
    "logs",
    "stop",
    "status",
    "remove",
    "cleanup",
    "exit",
    "quit",
]


def setup_completion():
    """Setup readline completion if available."""
    if not READLINE_AVAILABLE:
        return

    def completer(text, state):
        """Custom completer for interactive CLI."""
        try:
            # Get available options
            options = []

            # Get current line and split into parts
            line = readline.get_line_buffer()
            parts = line.split()

            if not parts or (len(parts) == 1 and not line.endswith(" ")):
                # Completing command
                options = [cmd for cmd in COMMANDS if cmd.startswith(text)]
            elif len(parts) >= 1:
                cmd = parts[0]
                if cmd in [
                    "select",
                    "tools",
                    "call",
                    "deploy",
                    "logs",
                    "stop",
                    "status",
                    "remove",
                ]:
                    # Try to complete template names
                    try:
                        session = get_session()
                        templates = session.client.list_templates()
                        options = [t for t in templates if t.startswith(text)]
                    except:
                        options = []
                elif cmd == "config":
                    # Basic config key completion
                    config_keys = ["backend", "timeout", "port", "host"]
                    options = [k for k in config_keys if k.startswith(text)]

            # Return the state-th option
            return options[state] if state < len(options) else None

        except (IndexError, AttributeError):
            return None

    # Setup readline
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    # Enable history
    readline.parse_and_bind("set show-all-if-ambiguous on")

    # Try to load history from file
    history_file = os.path.expanduser("~/.mcp/.mcpt_history")
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass  # No history file yet

    # Set history length
    readline.set_history_length(1000)

    return history_file


class InteractiveSession:
    """Manages interactive session state and configuration."""

    def __init__(self, backend_type: str = "docker"):
        self.backend_type = backend_type
        self.client = MCPClient(backend_type=backend_type)
        self.cache = CacheManager()
        self.formatter = ResponseFormatter()

        # Session configuration storage
        self.session_configs: Dict[str, Dict[str, Any]] = {}

        # Template selection state
        self.selected_template: Optional[str] = None

        # Load cached configurations
        self._load_cached_configs()

    def _load_cached_configs(self):
        """Load previously cached template configurations."""
        try:
            cached_configs = self.cache.get("interactive_session_configs", {})
            self.session_configs.update(cached_configs)
        except Exception:
            # Cache errors are non-fatal
            pass

    def _save_cached_configs(self):
        """Save current configurations to cache."""
        try:
            self.cache.set("interactive_session_configs", self.session_configs)
        except Exception:
            # Cache errors are non-fatal
            pass

    def get_template_config(self, template_name: str) -> Dict[str, Any]:
        """Get configuration for a template."""
        return self.session_configs.get(template_name, {})

    def update_template_config(self, template_name: str, config: Dict[str, Any]):
        """Update configuration for a template."""
        if template_name not in self.session_configs:
            self.session_configs[template_name] = {}
        self.session_configs[template_name].update(config)
        self._save_cached_configs()

    def clear_template_config(self, template_name: str):
        """Clear configuration for a template."""
        if template_name in self.session_configs:
            del self.session_configs[template_name]
            self._save_cached_configs()

    def select_template(self, template_name: str) -> bool:
        """Select a template for the session."""
        try:
            templates = self.client.list_templates()
            if template_name in templates:
                self.selected_template = template_name
                console.print(f"[green]✅ Selected template: {template_name}[/green]")
                return True
            else:
                console.print(f"[red]❌ Template '{template_name}' not found[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error selecting template: {e}[/red]")
            return False

    def unselect_template(self):
        """Unselect the current template."""
        if self.selected_template:
            console.print(
                f"[yellow]📤 Unselected template: {self.selected_template}[/yellow]"
            )
            self.selected_template = None
        else:
            console.print("[yellow]⚠️ No template currently selected[/yellow]")

    def get_selected_template(self) -> Optional[str]:
        """Get the currently selected template."""
        return self.selected_template

    def get_prompt(self) -> str:
        """Get the interactive prompt based on current state."""
        if self.selected_template:
            return f"mcpt({self.selected_template})> "
        return "mcpt> "


# Global session instance
session = None


def get_session() -> InteractiveSession:
    """Get or create the interactive session."""
    global session
    if session is None:
        backend = os.getenv("MCP_BACKEND", "docker")
        session = InteractiveSession(backend_type=backend)
    return session


# Create Typer app for interactive commands
app = typer.Typer(
    name="mcpt-interactive",
    help="MCP Interactive CLI - Enhanced shell for MCP operations",
    rich_markup_mode="rich",
    add_completion=False,  # Disable completion in interactive mode
)


@app.callback()
def main(
    backend: Annotated[
        str, typer.Option("--backend", help="Backend type to use")
    ] = "docker",
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
):
    """Interactive MCP CLI with dynamic command handling."""
    global session
    session = InteractiveSession(backend_type=backend)

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        console.print(f"[dim]Using backend: {backend}[/dim]")


@app.command(name="templates")
def list_templates(
    include_status: Annotated[
        bool, typer.Option("--status", help="Include deployment status")
    ] = False,
    all_backends: Annotated[
        bool, typer.Option("--all-backends", help="Check all backends")
    ] = False,
):
    """List available MCP server templates."""
    try:
        # Import and use the main CLI function to avoid duplication
        from mcp_template.cli import list as cli_list

        # Call the main CLI function with the same parameters
        # Convert to the format the main CLI expects
        deployed_only = include_status
        backend = None if all_backends else os.getenv("MCP_BACKEND", "docker")
        output_format = "table"

        cli_list(
            deployed_only=deployed_only, backend=backend, output_format=output_format
        )

    except Exception as e:
        console.print(f"[red]❌ Error listing templates: {e}[/red]")


@app.command(name="tools")
def list_tools(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template name (optional if template is selected)"),
    ] = None,
    force_refresh: Annotated[
        bool, typer.Option("--force-refresh", help="Force refresh cache")
    ] = False,
    show_help: Annotated[
        bool, typer.Option("--help-info", help="Show detailed help for tools")
    ] = False,
):
    """List available tools for a template."""
    try:
        session = get_session()

        # Use selected template if no template argument provided
        if template is None:
            template = session.get_selected_template()
            if template is None:
                console.print(
                    "[red]❌ No template specified and none selected. Use 'select <template>' first or provide template name.[/red]"
                )
                return
        # Import and use the main CLI function to avoid duplication
        from mcp_template.cli import list_tools as cli_list_tools

        # Call the main CLI function with the same parameters
        backend = os.getenv("MCP_BACKEND", "docker")
        output_format = "table"

        cli_list_tools(
            template=template,
            backend=backend,
            force_refresh=force_refresh,
            static=True,
            dynamic=True,
            output_format=output_format,
        )

        if show_help:
            _show_template_help(template, [])  # Simplified for now

    except Exception as e:
        console.print(f"[red]❌ Error listing tools: {e}[/red]")


@app.command(name="call")
def call_tool(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template name (optional if template is selected)"),
    ] = None,
    tool_name: Annotated[Optional[str], typer.Argument(help="Tool name")] = None,
    args: Annotated[
        Optional[str], typer.Argument(help="JSON arguments for the tool")
    ] = "{}",
    config_file: Annotated[
        Optional[Path], typer.Option("--config-file", "-c", help="Path to config file")
    ] = None,
    env: Annotated[
        Optional[List[str]],
        typer.Option("--env", "-e", help="Environment variables (KEY=VALUE)"),
    ] = None,
    config: Annotated[
        Optional[List[str]],
        typer.Option("--config", "-C", help="Config overrides (KEY=VALUE)"),
    ] = None,
    backend: Annotated[
        Optional[str],
        typer.Option(
            "--backend", "-b", help="Specific backend to use (docker, kubernetes, mock)"
        ),
    ] = None,
    no_pull: Annotated[
        bool, typer.Option("--no-pull", help="Don't pull Docker images")
    ] = False,
    raw: Annotated[
        bool, typer.Option("--raw", "-R", help="Show raw JSON response")
    ] = False,
    force_stdio: Annotated[
        bool, typer.Option("--stdio", help="Force stdio transport")
    ] = False,
):
    """Call a tool from a template."""
    try:
        session = get_session()

        # Handle template selection
        if template is None:
            template = session.get_selected_template()
            if template is None:
                console.print(
                    "[red]❌ No template specified and none selected. Use 'select <template>' first or provide template name.[/red]"
                )
                return

        # Handle tool name requirement
        if tool_name is None:
            console.print(
                "[red]❌ Tool name is required. Usage: call [template] <tool_name> [args][/red]"
            )
            return

        # Validate template exists
        templates = session.client.list_templates()
        if template not in templates:
            console.print(f"[red]❌ Template '{template}' not found[/red]")
            return

        # Parse JSON arguments
        try:
            tool_args = json.loads(args) if args else {}
        except json.JSONDecodeError as e:
            console.print(f"[red]❌ Invalid JSON arguments: {e}[/red]")
            return

        # Parse environment variables
        env_vars = {}
        if env:
            for env_var in env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_vars[key] = value
                else:
                    console.print(
                        f"[yellow]⚠️  Ignoring invalid env var: {env_var}[/yellow]"
                    )

        # Parse config overrides
        config_overrides = {}
        if config:
            for config_var in config:
                if "=" in config_var:
                    key, value = config_var.split("=", 1)
                    config_overrides[key] = value
                else:
                    console.print(
                        f"[yellow]⚠️  Ignoring invalid config: {config_var}[/yellow]"
                    )

        # Merge with session config
        session_config = session.get_template_config(template)
        final_config = {**session_config, **config_overrides}

        console.print(
            f"\n[cyan]🚀 Calling tool '{tool_name}' from template '{template}'[/cyan]"
        )

        # Check for missing required configuration
        template_info = session.client.get_template_info(template)
        if template_info:
            missing_config = _check_missing_config(
                template_info, final_config, env_vars
            )
            if missing_config:
                console.print(
                    f"[yellow]⚠️  Missing required configuration: {', '.join(missing_config)}[/yellow]"
                )

                if Confirm.ask("Would you like to set the missing configuration now?"):
                    new_config = _prompt_for_config(template_info, missing_config)
                    final_config.update(new_config)
                    session.update_template_config(template, new_config)
                else:
                    console.print(
                        "[yellow]Cannot proceed without required configuration[/yellow]"
                    )
                    return

        # Call the tool
        result = session.client.call_tool_with_config(
            template_id=template,
            tool_name=tool_name,
            arguments=tool_args,
            config_file=str(config_file) if config_file else None,
            env_vars=env_vars,
            config_values=final_config,
            all_backends=not backend,
            pull_image=not no_pull,
            force_stdio=force_stdio,
        )

        # Display result
        if result and result.get("success"):
            if raw:
                console.print(json.dumps(result, indent=2))
            else:
                _display_tool_result(result.get("result"), tool_name, raw=False)

                # Show additional info if available
                if result.get("backend_type"):
                    console.print(
                        f"[dim]Used backend: {result.get('backend_type')}[/dim]"
                    )
                if result.get("deployment_id"):
                    console.print(
                        f"[dim]Used deployment: {result.get('deployment_id')}[/dim]"
                    )
        else:
            error_msg = (
                result.get("error", "Tool execution failed")
                if result
                else "Tool execution failed"
            )
            console.print(f"[red]❌ Tool execution failed: {error_msg}[/red]")

            # Show helpful deploy command if template is not deployed and doesn't support stdio
            if result and not result.get("template_supports_stdio", True):
                deploy_cmd = result.get("deploy_command")
                if deploy_cmd:
                    console.print(
                        f"[yellow]💡 Try deploying first: {deploy_cmd}[/yellow]"
                    )

            # Show backend info if available
            if result and result.get("backend_type"):
                console.print(f"[dim]Backend used: {result.get('backend_type')}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Failed to execute tool: {e}[/red]")


@app.command(name="config")
def configure_template(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template name (optional if template is selected)"),
    ] = None,
    config_pairs: Annotated[
        Optional[List[str]], typer.Argument(help="Configuration KEY=VALUE pairs")
    ] = None,
):
    """Configure a template with key=value pairs."""
    try:
        session = get_session()

        # Handle template selection
        if template is None:
            template = session.get_selected_template()
            if template is None:
                console.print(
                    "[red]❌ No template specified and none selected. Use 'select <template>' first or provide template name.[/red]"
                )
                return

        # Handle config pairs requirement
        if not config_pairs:
            console.print(
                "[red]❌ Configuration KEY=VALUE pairs are required. Usage: config [template] key=value ...[/red]"
            )
            return

        # Validate template exists
        templates = session.client.list_templates()
        if template not in templates:
            console.print(f"[red]❌ Template '{template}' not found[/red]")
            return

        # Parse config pairs
        config_values = {}
        for pair in config_pairs:
            if "=" in pair:
                key, value = pair.split("=", 1)
                config_values[key] = value
            else:
                console.print(
                    f"[yellow]⚠️  Ignoring invalid config pair: {pair}[/yellow]"
                )

        if not config_values:
            console.print("[red]❌ No valid configuration pairs provided[/red]")
            return

        # Update session config
        session.update_template_config(template, config_values)

        console.print(
            f"[green]✅ Configuration saved for template '{template}'[/green]"
        )

        # Display current config
        show_config(template)

    except Exception as e:
        console.print(f"[red]❌ Error configuring template: {e}[/red]")


@app.command(name="show-config")
def show_config(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template name (optional if template is selected)"),
    ] = None,
):
    """Show current configuration for a template."""
    try:
        session = get_session()

        # Handle template selection
        if template is None:
            template = session.get_selected_template()
            if template is None:
                console.print(
                    "[red]❌ No template specified and none selected. Use 'select <template>' first or provide template name.[/red]"
                )
                return

        config = session.get_template_config(template)

        if not config:
            console.print(
                f"[yellow]No configuration found for template '{template}'[/yellow]"
            )
            return

        table = Table(title=f"Configuration for {template}")
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
                else str(value)
            )
            table.add_row(key, display_value)

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error showing config: {e}[/red]")


@app.command(name="clear-config")
def clear_config(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template name (optional if template is selected)"),
    ] = None,
):
    """Clear configuration for a template."""
    try:
        session = get_session()

        # Handle template selection
        if template is None:
            template = session.get_selected_template()
            if template is None:
                console.print(
                    "[red]❌ No template specified and none selected. Use 'select <template>' first or provide template name.[/red]"
                )
                return

        session.clear_template_config(template)
        console.print(
            f"[green]✅ Configuration cleared for template '{template}'[/green]"
        )

    except Exception as e:
        console.print(f"[red]❌ Error clearing config: {e}[/red]")


@app.command(name="servers")
def list_servers(
    template: Annotated[
        Optional[str], typer.Option("--template", help="Filter by template")
    ] = None,
    all_backends: Annotated[
        bool, typer.Option("--all-backends", help="Check all backends")
    ] = False,
):
    """List deployed MCP servers."""
    try:
        # Import and use the main CLI function to avoid duplication
        from mcp_template.cli import list_deployments

        # Call the main CLI function with the same parameters
        backend = None if all_backends else os.getenv("MCP_BACKEND", "docker")
        output_format = "table"

        list_deployments(
            template=template,
            backend=backend,
            status="running",
            output_format=output_format,
            all_statuses=False,
        )

    except Exception as e:
        console.print(f"[red]❌ Error listing servers: {e}[/red]")


@app.command(name="deploy")
def deploy_template(
    template: Annotated[str, typer.Argument(help="Template name")],
    config_file: Annotated[
        Optional[Path], typer.Option("--config-file", "-c", help="Path to config file")
    ] = None,
    env: Annotated[
        Optional[List[str]],
        typer.Option("--env", "-e", help="Environment variables (KEY=VALUE)"),
    ] = None,
    config: Annotated[
        Optional[List[str]],
        typer.Option("--config", "-C", help="Config overrides (KEY=VALUE)"),
    ] = None,
    transport: Annotated[
        Optional[str], typer.Option("--transport", "-t", help="Transport protocol")
    ] = "http",
    port: Annotated[
        Optional[int], typer.Option("--port", "-p", help="Port for HTTP transport")
    ] = None,
    no_pull: Annotated[
        bool, typer.Option("--no-pull", help="Don't pull Docker images")
    ] = False,
):
    """Deploy a template as a server."""
    try:
        # Import and use the main CLI function to avoid duplication
        from mcp_template.cli import deploy

        # Get session config for this template
        session = get_session()
        session_config = session.get_template_config(template)

        # Merge session config with CLI config parameters
        merged_config = list(config) if config else []
        for key, value in session_config.items():
            merged_config.append(f"{key}={value}")

        # Call the main CLI deploy function
        deploy(
            template=template,
            config_file=config_file,
            config=merged_config if merged_config else None,
            env=env,
            override=None,  # Not used in interactive mode
            backend_config=None,
            backend_config_file=None,
            volumes=None,
            host="0.0.0.0",
            transport=transport,
            port=port,
            no_pull=no_pull,
            dry_run=False,
        )

    except Exception as e:
        console.print(f"[red]❌ Error deploying template: {e}[/red]")


@app.command(name="select")
def select_template(
    template: Annotated[str, typer.Argument(help="Template name to select")],
):
    """Select a template for the session to avoid repeating template name in commands."""
    try:
        session = get_session()
        session.select_template(template)

    except Exception as e:
        console.print(f"[red]❌ Error selecting template: {e}[/red]")


@app.command(name="unselect")
def unselect_template():
    """Unselect the currently selected template."""
    try:
        session = get_session()
        session.unselect_template()

    except Exception as e:
        console.print(f"[red]❌ Error unselecting template: {e}[/red]")


@app.command(name="help")
def show_help(
    command: Annotated[
        Optional[str], typer.Argument(help="Show help for specific command")
    ] = None,
):
    """Show help information."""
    if command:
        # Show help for specific command
        try:
            ctx = typer.Context(app)
            ctx.invoke(app.get_command(ctx, command), "--help")
        except Exception:
            console.print(f"[red]Unknown command: {command}[/red]")
    else:
        # Show general help
        console.print(
            Panel(
                """
[cyan]Available Commands:[/cyan]

[yellow]Template Selection:[/yellow]
  • [bold]select[/bold] TEMPLATE  - Select a template for session (avoids repeating template name)
  • [bold]unselect[/bold]  - Unselect current template

[yellow]Template & Server Management:[/yellow]
  • [bold]templates[/bold] [--status] [--all-backends]  - List available templates
  • [bold]servers[/bold] [--template NAME] [--all-backends]  - List deployed servers
  • [bold]deploy[/bold] [TEMPLATE] [options]  - Deploy a template as server

[yellow]Tool Operations:[/yellow]
  • [bold]tools[/bold] [TEMPLATE] [--force-refresh] [--help-info]  - List tools for template
  • [bold]call[/bold] [TEMPLATE] TOOL [JSON_ARGS] [options]  - Call a tool
    [dim]Options: --config-file, --env KEY=VALUE, --config KEY=VALUE, --raw, --stdio[/dim]

[yellow]Configuration Management:[/yellow]
  • [bold]config[/bold] [TEMPLATE] KEY=VALUE [KEY2=VALUE2...]  - Set configuration
  • [bold]show-config[/bold] [TEMPLATE]  - Show current configuration
  • [bold]clear-config[/bold] [TEMPLATE]  - Clear configuration

[yellow]General:[/yellow]
  • [bold]help[/bold] [COMMAND]  - Show this help or help for specific command
  • [bold]exit[/bold] or Ctrl+C  - Exit interactive mode

[green]Examples with Template Selection:[/green]
  • [dim]select demo  # Select demo template[/dim]
  • [dim]tools  # List tools for selected template[/dim]
  • [dim]call say_hello '{"name": "Alice"}'  # Call tool without template name[/dim]
  • [dim]config github_token=ghp_xxxx  # Configure selected template[/dim]
  • [dim]unselect  # Unselect template[/dim]

[green]Traditional Examples:[/green]
  • [dim]templates --status[/dim]
  • [dim]config github github_token=ghp_xxxx[/dim]
  • [dim]tools github --help-info[/dim]
  • [dim]call github search_repositories '{"query": "python"}'[/dim]
  • [dim]call --env API_KEY=xyz demo say_hello '{"name": "Alice"}'[/dim]
  • [dim]deploy demo --transport http --port 8080[/dim]
""",
                title="MCP Interactive CLI Help",
                border_style="blue",
            )
        )


def _check_missing_config(
    template_info: Dict[str, Any], config: Dict[str, Any], env_vars: Dict[str, str]
) -> List[str]:
    """Check for missing required configuration."""
    config_schema = template_info.get("config_schema", {})
    required_props = config_schema.get("required", [])

    missing = []
    for prop in required_props:
        prop_config = config_schema.get("properties", {}).get(prop, {})
        env_mapping = prop_config.get("env_mapping", prop.upper())

        # Check if we have this config value
        if prop not in config and env_mapping not in env_vars:
            missing.append(prop)

    return missing


def _prompt_for_config(
    template_info: Dict[str, Any], missing_props: List[str]
) -> Dict[str, str]:
    """Prompt user for missing configuration values."""
    config_schema = template_info.get("config_schema", {})
    properties = config_schema.get("properties", {})

    new_config = {}
    for prop in missing_props:
        prop_info = properties.get(prop, {})
        description = prop_info.get("description", f"Value for {prop}")

        # Check if it's a sensitive field
        is_sensitive = any(
            sensitive in prop.lower()
            for sensitive in ["token", "key", "secret", "password"]
        )

        if is_sensitive:
            value = Prompt.ask(f"[cyan]{description}[/cyan]", password=True)
        else:
            default = prop_info.get("default")
            value = Prompt.ask(f"[cyan]{description}[/cyan]", default=default)

        if value:
            new_config[prop] = value

    return new_config


def _display_tool_result(result: Any, tool_name: str, raw: bool = False):
    """Display tool result in tabular format or raw JSON."""
    try:
        if raw:
            # Show raw JSON format
            console.print(f"\n[green]✅ Tool Result: {tool_name} (Raw)[/green]")
            console.print(json.dumps(result, indent=2))
        else:
            # Show tabular format
            _display_tool_result_table(result, tool_name)
    except Exception:
        # Fallback to simple display if both methods fail
        console.print(f"[green]✅ Tool '{tool_name}' result:[/green]")
        console.print(result)


def _display_tool_result_table(result: Any, tool_name: str):
    """Display tool result in a user-friendly tabular format."""
    from rich import box

    # Handle different types of results
    if isinstance(result, dict):
        # Check if it's an MCP-style response with content
        if "content" in result and isinstance(result["content"], list):
            _display_mcp_content_table(result["content"], tool_name)
        # Check if it's a structured response with result data
        elif "structuredContent" in result and "result" in result["structuredContent"]:
            _display_simple_result_table(
                result["structuredContent"]["result"], tool_name
            )
        # Check if it's a simple dict that can be displayed as key-value pairs
        else:
            _display_dict_as_table(result, tool_name)
    elif isinstance(result, list):
        _display_list_as_table(result, tool_name)
    else:
        # Single value result
        _display_simple_result_table(result, tool_name)


def _display_mcp_content_table(content_list: list, tool_name: str):
    """Display MCP content array in tabular format."""
    from rich import box

    table = Table(
        title=f"🎯 {tool_name} Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Type", style="yellow", width=12)
    table.add_column("Content", style="white", min_width=40)

    for i, content in enumerate(content_list):
        if isinstance(content, dict):
            content_type = content.get("type", "unknown")
            if content_type == "text":
                text_content = content.get("text", "")
                # Try to parse as JSON for better formatting
                try:
                    parsed = json.loads(text_content)
                    if isinstance(parsed, dict):
                        # Display nested dict in a compact format
                        formatted_content = "\n".join(
                            [f"{k}: {v}" for k, v in parsed.items()]
                        )
                    else:
                        formatted_content = str(parsed)
                except (json.JSONDecodeError, AttributeError):
                    formatted_content = text_content
                table.add_row(content_type, formatted_content)
            else:
                # Handle other content types
                table.add_row(content_type, str(content))
        else:
            table.add_row("unknown", str(content))

    console.print(table)


def _display_simple_result_table(result: Any, tool_name: str):
    """Display a simple result value in a clean format."""
    from rich import box

    table = Table(
        title=f"🎯 {tool_name} Result", box=box.ROUNDED, show_header=False, width=60
    )

    table.add_column("", style="bold green", justify="center")
    table.add_row(str(result))

    console.print(table)


def _display_dict_as_table(data: dict, tool_name: str):
    """Display a dictionary as a key-value table."""
    from rich import box

    table = Table(
        title=f"🎯 {tool_name} Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Property", style="yellow", width=20)
    table.add_column("Value", style="white", min_width=40)

    for key, value in data.items():
        if isinstance(value, (dict, list)):
            # For complex values, show a summary
            if isinstance(value, dict):
                display_value = f"Dict with {len(value)} items"
                if len(value) <= 3:  # Show small dicts inline
                    display_value = ", ".join([f"{k}: {v}" for k, v in value.items()])
            else:  # list
                display_value = f"List with {len(value)} items"
                if len(value) <= 3 and all(
                    not isinstance(item, (dict, list)) for item in value
                ):
                    display_value = ", ".join(str(item) for item in value)
        else:
            display_value = str(value)

        table.add_row(key, display_value)

    console.print(table)


def _display_list_as_table(data: list, tool_name: str):
    """Display a list as a table."""
    from rich import box

    table = Table(
        title=f"🎯 {tool_name} Results",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    if data and isinstance(data[0], dict):
        # List of dicts - use dict keys as columns
        if data:
            keys = list(data[0].keys())
            for key in keys:
                table.add_column(key.title(), style="white")

            for item in data:
                row = []
                for key in keys:
                    value = item.get(key, "")
                    if isinstance(value, (dict, list)):
                        row.append(f"{type(value).__name__}({len(value)})")
                    else:
                        row.append(str(value))
                table.add_row(*row)
    else:
        # Simple list - show as single column
        table.add_column("Item", style="white")
        for i, item in enumerate(data):
            table.add_row(str(item))

    console.print(table)


def _show_template_help(template: str, tools: List[Dict[str, Any]]):
    """Show detailed help for a template and its tools."""
    console.print(f"\n[cyan]📖 Detailed Help for Template: {template}[/cyan]")

    for tool in tools:
        tool_name = tool.get("name", "Unknown")
        description = tool.get("description", "No description available")

        console.print(f"\n[yellow]🔧 {tool_name}[/yellow]")
        console.print(f"[dim]{description}[/dim]")

        # Show parameters if available
        parameters = tool.get("parameters", {})
        input_schema = tool.get("inputSchema", {})

        schema_to_use = parameters if parameters else input_schema
        if schema_to_use and "properties" in schema_to_use:
            props = schema_to_use["properties"]
            required = schema_to_use.get("required", [])

            if props:
                param_table = Table(title=f"Parameters for {tool_name}")
                param_table.add_column("Parameter", style="cyan")
                param_table.add_column("Type", style="yellow")
                param_table.add_column("Required", style="red")
                param_table.add_column("Description", style="white")

                for param, param_info in props.items():
                    param_type = param_info.get("type", "unknown")
                    is_required = "✓" if param in required else "✗"
                    param_desc = param_info.get("description", "No description")

                    param_table.add_row(param, param_type, is_required, param_desc)

                console.print(param_table)


def run_interactive_shell():
    """Run the interactive shell with command processing."""

    # Setup readline completion and history
    history_file = None
    if READLINE_AVAILABLE:
        history_file = setup_completion()
        console.print("[dim]✨ Command history and tab completion enabled[/dim]")
    else:
        console.print(
            "[dim]💡 Install readline for command history and tab completion[/dim]"
        )

    # Show welcome message
    console.print(
        Panel(
            """
[cyan]🚀 Welcome to MCP Interactive CLI v2[/cyan]

This is an enhanced interactive shell for managing MCP servers and calling tools.
Type [bold]help[/bold] for available commands or [bold]help COMMAND[/bold] for specific help.

[green]Quick Start:[/green]
• [dim]templates  # List available templates[/dim]
• [dim]select demo  # Select demo template for session[/dim]
• [dim]tools  # List tools for selected template[/dim]
• [dim]call say_hello '{"name": "Alice"}'  # Call a tool (no template needed)[/dim]
• [dim]unselect  # Unselect template[/dim]

[green]Template Selection:[/green]
• [dim]select <template>  # Select a template to avoid repeating in commands[/dim]
• [dim]unselect  # Unselect current template[/dim]

[yellow]Note:[/yellow] Use [bold]exit[/bold] or [bold]quit[/bold] to leave the interactive mode.
""",
            title="MCP Interactive CLI",
            border_style="blue",
        )
    )

    # Main interactive loop
    try:
        while True:
            try:
                # Get session for dynamic prompt
                session = get_session()
                prompt_text = session.get_prompt()

                # Use input() with prompt parameter to avoid Rich console conflicts
                if READLINE_AVAILABLE:
                    # With readline, use a simple prompt to avoid display issues
                    command = input(prompt_text).strip()
                else:
                    # Without readline, use Rich formatting
                    console.print(f"[bold blue]{prompt_text}[/bold blue]", end="")
                    command = input().strip()

                if not command:
                    continue

                if command in ["exit", "quit"]:
                    # Save command history before exiting
                    if READLINE_AVAILABLE and history_file:
                        try:
                            readline.write_history_file(history_file)
                        except:
                            pass  # Ignore history save errors
                    console.print("[yellow]Goodbye![/yellow]")
                    break

                # Parse and execute command using direct function calls
                try:
                    # Split command into args, respecting quoted strings
                    args = shlex.split(command)

                    if not args:
                        continue

                    cmd = args[0]
                    cmd_args = args[1:]

                    # Direct command dispatch to preserve session
                    if cmd == "help":
                        if cmd_args:
                            show_help(cmd_args[0])
                        else:
                            show_help()
                    elif cmd == "templates":
                        list_templates()
                    elif cmd == "select":
                        if cmd_args:
                            select_template(cmd_args[0])
                        else:
                            console.print(
                                "[red]❌ Template name required for select command[/red]"
                            )
                    elif cmd == "unselect":
                        unselect_template()
                    elif cmd == "tools":
                        # Parse tools command arguments and flags
                        template_arg = None
                        force_refresh = False
                        show_help_flag = False

                        for arg in cmd_args:
                            if arg == "--force-refresh":
                                force_refresh = True
                            elif arg == "--help-info":
                                show_help_flag = True
                            elif not arg.startswith("-"):
                                template_arg = arg

                        list_tools(
                            template=template_arg,
                            force_refresh=force_refresh,
                            show_help=show_help_flag,
                        )
                    elif cmd == "servers":
                        list_servers()
                    elif cmd == "deploy":
                        if cmd_args:
                            deploy_template(cmd_args[0])
                        else:
                            # Use selected template
                            session = get_session()
                            template = session.get_selected_template()
                            if template:
                                deploy_template(template)
                            else:
                                console.print(
                                    "[red]❌ Template name required for deploy command when none selected[/red]"
                                )
                    elif cmd == "call":
                        # Robust argument parsing for call command
                        session = get_session()
                        available_templates = session.client.list_templates()

                        # Initialize variables
                        template_arg = None
                        tool_name = None
                        tool_args = "{}"
                        config_overrides = []
                        env_vars = []
                        backend_arg = None

                        # Parse command line arguments properly
                        i = 0
                        positional_args = []

                        while i < len(cmd_args):
                            arg = cmd_args[i]

                            if arg in ["-C", "--config"]:
                                # Next argument should be key=value
                                if i + 1 < len(cmd_args):
                                    config_overrides.append(cmd_args[i + 1])
                                    i += 2
                                else:
                                    console.print(
                                        "[red]❌ -C/--config requires a key=value argument[/red]"
                                    )
                                    break
                            elif arg in ["-e", "--env"]:
                                # Next argument should be key=value
                                if i + 1 < len(cmd_args):
                                    env_vars.append(cmd_args[i + 1])
                                    i += 2
                                else:
                                    console.print(
                                        "[red]❌ -e/--env requires a key=value argument[/red]"
                                    )
                                    break
                            elif arg in ["-b", "--backend"]:
                                # Next argument should be backend name
                                if i + 1 < len(cmd_args):
                                    backend_arg = cmd_args[i + 1]
                                    i += 2
                                else:
                                    console.print(
                                        "[red]❌ -b/--backend requires a backend name[/red]"
                                    )
                                    break
                            elif arg.startswith("-"):
                                # Skip unknown flags for now
                                console.print(
                                    f"[yellow]⚠️ Ignoring unknown flag: {arg}[/yellow]"
                                )
                                i += 1
                            else:
                                # This is a positional argument
                                positional_args.append(arg)
                                i += 1

                        # Now determine template, tool_name, and tool_args from positional args
                        if not positional_args:
                            console.print(
                                "[red]❌ Tool name required for call command[/red]"
                            )
                        elif len(positional_args) == 1:
                            # call tool_name (use selected template, no args)
                            tool_name = positional_args[0]
                        elif len(positional_args) == 2:
                            # Could be: call template tool_name OR call tool_name args
                            if positional_args[0] in available_templates:
                                # call template tool_name
                                template_arg = positional_args[0]
                                tool_name = positional_args[1]
                            else:
                                # call tool_name args
                                tool_name = positional_args[0]
                                tool_args = positional_args[1]
                        elif len(positional_args) >= 3:
                            # call template tool_name args
                            if positional_args[0] in available_templates:
                                template_arg = positional_args[0]
                                tool_name = positional_args[1]
                                tool_args = positional_args[2]
                            else:
                                # call tool_name args (with extra args - use last one)
                                tool_name = positional_args[0]
                                tool_args = positional_args[
                                    -1
                                ]  # Use the last argument as JSON

                        if tool_name:
                            call_tool(
                                template=template_arg,
                                tool_name=tool_name,
                                args=tool_args,
                                config=config_overrides if config_overrides else None,
                                env=env_vars if env_vars else None,
                                backend=backend_arg,
                            )
                        else:
                            console.print(
                                "[red]❌ Tool name required for call command[/red]"
                            )
                    elif cmd == "config":
                        # Smart argument parsing for config command
                        if len(cmd_args) >= 2:
                            # Check if first arg is a template name
                            session = get_session()
                            available_templates = session.client.list_templates()

                            if cmd_args[0] in available_templates:
                                # config template key=value...
                                template_arg = cmd_args[0]
                                config_pairs = cmd_args[1:]
                                configure_template(
                                    template=template_arg, config_pairs=config_pairs
                                )
                            else:
                                # config key=value... (with selected template)
                                config_pairs = cmd_args
                                configure_template(
                                    template=None, config_pairs=config_pairs
                                )
                        elif len(cmd_args) >= 1:
                            # config key=value... (with selected template)
                            config_pairs = cmd_args
                            configure_template(template=None, config_pairs=config_pairs)
                        else:
                            console.print(
                                "[red]❌ Configuration pairs required for config command[/red]"
                            )
                    elif cmd == "show-config":
                        template_arg = cmd_args[0] if cmd_args else None
                        show_config(template=template_arg)
                    elif cmd == "clear-config":
                        template_arg = cmd_args[0] if cmd_args else None
                        clear_config(template=template_arg)
                    else:
                        console.print(f"[red]❌ Unknown command: {cmd}[/red]")
                        console.print("[dim]Type 'help' for available commands[/dim]")

                except Exception as e:
                    console.print(f"[red]❌ Error executing command: {e}[/red]")

            except KeyboardInterrupt:
                console.print(
                    "\n[yellow]Use 'exit' or 'quit' to leave the interactive shell[/yellow]"
                )
            except EOFError:
                # Save command history before exiting
                if READLINE_AVAILABLE and history_file:
                    try:
                        readline.write_history_file(history_file)
                    except:
                        pass  # Ignore history save errors
                console.print("\n[yellow]Goodbye![/yellow]")
                break

    except Exception as e:
        console.print(f"[red]❌ Fatal error in interactive shell: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point for standalone execution."""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        console.print("Enhanced MCP Interactive CLI")
        console.print("Usage: python -m mcp_template.interactive_cli_v2")
        console.print("       or: python interactive_cli_v2.py")
        return

    run_interactive_shell()


if __name__ == "__main__":
    main()
