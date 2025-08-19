#!/usr/bin/env python3
"""
Enhanced CLI using Typer with autocomplete, dynamic help, and dry-run support.

This module replaces the old argparse-based CLI with a modern Typer implementation
that provides:
- Shell autocomplete for Bash, Zsh, Fish, PowerShell
- Dynamic help generation from docstrings
- Dry-run support for relevant commands
- Rich formatting and consistent output
"""

import builtins
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_template.core import DeploymentManager, TemplateManager, ToolManager
from mcp_template.core.deployment_manager import DeploymentOptions
from mcp_template.core.multi_backend_manager import MultiBackendManager
from mcp_template.core.response_formatter import (
    console,
    format_deployment_summary,
    get_backend_indicator,
    render_backend_health_status,
    render_deployments_grouped_by_backend,
    render_deployments_unified_table,
    render_tools_with_sources,
)


class AliasGroup(typer.core.TyperGroup):

    _CMD_SPLIT_P = re.compile(r"[,/] ?")

    def get_command(self, ctx, cmd_name):
        cmd_name = self._group_cmd_name(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _group_cmd_name(self, default_name):
        for cmd in self.commands.values():
            if cmd.name and default_name in self._CMD_SPLIT_P.split(cmd.name):
                return cmd.name
        return default_name


# Create the main Typer app
app = typer.Typer(
    name="mcpt",
    cls=AliasGroup,
    help="MCP Template CLI - Deploy and manage Model Context Protocol servers",
    epilog="Run 'mcpt COMMAND --help' for more information on a command.",
    rich_markup_mode="rich",
    add_completion=True,
)

# Console for rich output
console = Console()
logger = logging.getLogger(__name__)

# Global CLI state
cli_state = {
    "backend_type": os.getenv("MCP_BACKEND", "docker"),
    "verbose": os.getenv("MCP_VERBOSE", "false").lower() == "true",
    "dry_run": os.getenv("MCP_DRY_RUN", "false").lower() == "true",
}


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def format_discovery_hint(discovery_method: str) -> str:
    """Generate helpful hints based on discovery method."""
    hints = {
        "cache": "💡 [dim]This data was cached. Use --force-refresh to get latest tools.[/dim]",
        "static": "💡 [dim]Tools discovered from template files. Use --force-refresh to check running servers.[/dim]",
        "stdio": "ℹ️  [dim]Tools discovered from stdio interface.[/dim]",
        "http": "ℹ️  [dim]Tools discovered from running HTTP server.[/dim]",
        "error": "❌ [dim]Error occurred during discovery.[/dim]",
    }
    return hints.get(discovery_method, "")


def display_tools_with_metadata(tools_result: Dict[str, Any], template_name: str):
    """Display tools with discovery method metadata and hints."""
    tools = tools_result.get("tools", [])
    discovery_method = tools_result.get("discovery_method", "unknown")
    metadata = tools_result.get("metadata", {})

    if not tools:
        console.print(f"[yellow]No tools found for template '{template_name}'[/yellow]")
        return

    # Deduplicate tools by name (keep the first occurrence)
    seen_tools = set()
    unique_tools = []
    for tool in tools:
        tool_name = tool.get("name", "Unknown")
        if tool_name not in seen_tools:
            seen_tools.add(tool_name)
            unique_tools.append(tool)

    # Create title with discovery method
    title = f"Tools from template '{template_name}' (discovery: {discovery_method})"

    # Create table
    table = Table(title=title, show_header=True, header_style="bold blue")
    table.add_column("Tool Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Input Schema", style="dim")

    for tool in unique_tools:
        name = tool.get("name", "Unknown")
        description = tool.get("description", "No description")
        input_schema = tool.get("inputSchema", {})

        # Format input schema with better parameter detection
        if isinstance(input_schema, dict):
            properties = input_schema.get("properties", {})
            if properties:
                params = list(properties.keys())
                if len(params) <= 3:
                    schema_text = f"({', '.join(params)})"
                else:
                    schema_text = f"({', '.join(params[:3])}...)"
            else:
                # Check if there are any parameters in the tool definition
                parameters = tool.get("parameters", [])
                if parameters:
                    param_names = [p.get("name", "param") for p in parameters[:3]]
                    schema_text = f"({', '.join(param_names)})"
                else:
                    schema_text = "(no params)"
        else:
            schema_text = "(no params)" if not input_schema else "(schema available)"

        table.add_row(name, description, schema_text)

    console.print(table)

    # Show discovery hint
    hint = format_discovery_hint(discovery_method)
    if hint:
        console.print(hint)

    # Show metadata if verbose
    if cli_state.get("verbose") and metadata:
        metadata_text = f"Cached: {metadata.get('cached', False)} | "
        metadata_text += f"Timestamp: {time.ctime(metadata.get('timestamp', 0))}"
        console.print(f"[dim]{metadata_text}[/dim]")


@app.callback()
def main(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
    backend: Annotated[
        str, typer.Option("--backend", help="Backend type to use")
    ] = "docker",
):
    """
    MCP Template CLI - Deploy and manage Model Context Protocol servers.

    This tool helps you easily deploy, manage, and interact with MCP servers
    using Docker or other container backends.
    """
    cli_state["verbose"] = verbose
    cli_state["backend_type"] = backend
    setup_logging(verbose)

    if verbose:
        console.print(f"[dim]Using backend: {backend}[/dim]")


@app.command()
def deploy(
    template: Annotated[str, typer.Argument(help="Template name to deploy")],
    config_file: Annotated[
        Optional[Path], typer.Option("--config-file", "-f", help="Path to config file")
    ] = None,
    config: Annotated[
        Optional[List[str]],
        typer.Option("--config", "-c", help="Configuration key=value pairs"),
    ] = None,
    env: Annotated[
        Optional[List[str]],
        typer.Option("--env", "-e", help="Environment variables (KEY=VALUE)"),
    ] = None,
    config_overrides: Annotated[
        Optional[List[str]], typer.Option("--set", help="Config overrides (key=value)")
    ] = None,
    override: Annotated[
        Optional[List[str]],
        typer.Option(
            "--override",
            "-o",
            help="Template data overrides. Override configuration values (key=value). supports double underscore notation for nested fields, e.g., tools__0__custom_field=value",
        ),
    ] = None,
    backend_config: Annotated[
        Optional[List[str]],
        typer.Option(
            "--backend-config", "-bc", help="Backend-specific configuration (KEY=VALUE)"
        ),
    ] = None,
    volumes: Annotated[
        Optional[str],
        typer.Option("--volumes", "-v", help="Volume mounts (JSON object or array)"),
    ] = None,
    transport: Annotated[
        Optional[str],
        typer.Option("--transport", "-t", help="Transport protocol (http, stdio)"),
    ] = None,
    port: Annotated[
        Optional[int],
        typer.Option("--port", "-p", help="Desired port to run http server on"),
    ] = None,
    no_pull: Annotated[
        bool, typer.Option("--no-pull", "-np", help="Don't pull latest Docker image")
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-x",
            help="Show what would be deployed without actually deploying",
        ),
    ] = False,
):
    """
    Deploy an MCP server template.

    This command deploys the specified template with the given configuration.
    Use --dry-run to preview what would be deployed.

    Examples:
        mcpt deploy github --config-file github-config.json
        mcpt deploy filesystem --config allowed_dirs=/tmp --dry-run
        mcpt deploy demo --config hello_from="Custom Server" --volumes '{"./data": "/app/data"}'
    """

    cli_state["dry_run"] = dry_run

    if dry_run:
        console.print(
            "[yellow]🔍 DRY RUN MODE - No actual deployment will occur[/yellow]"
        )

    try:
        # Initialize managers
        template_manager = TemplateManager(cli_state["backend_type"])
        deployment_manager = DeploymentManager(cli_state["backend_type"])

        # Process configuration with correct precedence order
        # Separate different config sources for proper merging
        config_file_path = None
        env_vars = {}
        config_values = {}
        override_values = {}
        volume_config = None
        backend_config_values = {}

        # 1. Config file (will be handled by deployment manager)
        if config_file:
            config_file_path = str(config_file)

        # 2. CLI config key=value pairs
        if config:
            for config_item in config:
                if "=" in config_item:
                    key, value = config_item.split("=", 1)
                    config_values[key] = value

        # 3. Environment variables
        if env:
            for env_var in env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_vars[key] = value

        # 4. Config overrides (--set)
        if config_overrides:
            for override_item in config_overrides:
                if "=" in override_item:
                    key, value = override_item.split("=", 1)
                    config_values[key] = value

        # 5. Template overrides (--override)
        if override:
            for override_item in override:
                if "=" in override_item:
                    key, value = override_item.split("=", 1)
                    override_values[key] = value

        if backend_config:
            for backend_item in backend_config:
                if "=" in backend_item:
                    key, value = backend_item.split("=", 1)
                    backend_config_values[key] = value

        # Handle transport
        if transport:
            config_values["MCP_TRANSPORT"] = transport

        if port:
            config_values["MCP_PORT"] = str(port)

        # Process volumes and add to config_values
        if volumes:
            try:
                volume_data = json.loads(volumes)
                if isinstance(volume_data, dict):
                    # JSON object format: {"host_path": "container_path"}
                    volume_config = volume_data
                elif isinstance(volume_data, builtins.list):
                    # JSON array format: ["/host/path1", "/host/path2"]
                    # Convert to dict with same host and container paths
                    volume_config = {path: path for path in volume_data}
                else:
                    console.print(
                        "[red]❌ Invalid volume format. Volume mounts must be a JSON object or array[/red]"
                    )
                    raise typer.Exit(1)

            except json.JSONDecodeError as e:
                console.print(f"[red]❌ Invalid JSON format in volumes: {e}[/red]")
                raise typer.Exit(1)

        # Structure config sources for deployment manager
        config_sources = {
            "config_file": config_file_path,
            "env_vars": env_vars if env_vars else None,
            "config_values": config_values if config_values else None,
            "override_values": override_values if override_values else None,
            "volume_config": volume_config,
            "backend_config": backend_config_values if backend_config_values else None,
        }

        # Get template info
        template_info = template_manager.get_template_info(template)
        if not template_info:
            console.print(f"[red]❌ Template '{template}' not found[/red]")
            raise typer.Exit(1)

        # Check if this is a stdio template
        transport_info = template_info.get("transport", {})
        default_transport = transport_info.get("default", "http")
        supported_transports = transport_info.get("supported", ["http"])

        # If transport is explicitly set via CLI, use that
        actual_transport = transport or default_transport

        # Handle stdio template deployment validation
        if actual_transport == "stdio":
            console.print("[red]❌ Cannot deploy stdio transport MCP servers[/red]")
            console.print(
                f"\nThe template '{template}' uses stdio transport, which doesn't require deployment."
            )
            console.print(
                "Stdio MCP servers run interactively and cannot be deployed as persistent containers."
            )

            if config_values or env_vars or override_values:
                console.print("\n[cyan]✅ Configuration validated successfully:[/cyan]")
                all_config = {**config_values, **env_vars, **override_values}
                for key, value in all_config.items():
                    # Mask sensitive values
                    display_value = (
                        "***"
                        if any(
                            sensitive in key.lower()
                            for sensitive in ["token", "key", "secret", "password"]
                        )
                        else value
                    )
                    console.print(f"  {key}: {display_value}")

            console.print("\nTo use this template, run tools directly:")
            console.print(f"  mcpt list-tools {template}     # List available tools")
            console.print("  mcpt interactive               # Start interactive shell")
            raise typer.Exit(1)
        elif actual_transport not in supported_transports:
            console.print(
                f"[red]❌ Unsupported transport '{actual_transport}' for template '{template}'[/red]"
            )
            console.print(f"Supported transports: {', '.join(supported_transports)}")
            raise typer.Exit(1)

        # Show deployment plan
        console.print(f"[cyan]📋 Deployment Plan for '{template}'[/cyan]")

        plan_table = Table(show_header=False, box=None)
        plan_table.add_column("Key", style="bold")
        plan_table.add_column("Value")

        plan_table.add_row("Template", template)
        plan_table.add_row("Backend", cli_state["backend_type"])
        plan_table.add_row("Image", template_info.get("docker_image", "unknown"))
        plan_table.add_row("Pull Image", "No" if no_pull else "Yes")

        if config_values or env_vars or override_values:
            all_config = {**config_values, **env_vars, **override_values}
            plan_table.add_row("Config Keys", ", ".join(all_config.keys()))

        console.print(plan_table)

        # Actual deployment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deploying template...", total=None)

            options = DeploymentOptions(pull_image=not no_pull, dry_run=dry_run)
            result = deployment_manager.deploy_template(
                template, config_sources, options
            )

            if result.success:
                deployment_id = result.deployment_id
                endpoint = result.endpoint

                console.print(f"[green]✅ Successfully deployed '{template}'[/green]")
                console.print(f"[cyan]Deployment ID: {deployment_id}[/cyan]")
                if endpoint:
                    console.print(f"[cyan]Endpoint: {endpoint}[/cyan]")
            else:
                error = result.error or "Unknown error"
                console.print(f"[red]❌ Deployment failed: {error}[/red]")
                raise typer.Exit(1)

        if dry_run:
            console.print(
                "\n[yellow]✅ Dry run complete - deployment plan shown above[/yellow]"
            )
            return

    except Exception as e:
        console.print(f"[red]❌ Error during deployment: {e}[/red]")
        if cli_state["verbose"]:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list_tools(
    template: Annotated[
        Optional[str],
        typer.Argument(
            help="Template name or deployment ID (optional for multi-backend view)"
        ),
    ] = None,
    backend: Annotated[
        Optional[str], typer.Option("--backend", help="Show specific backend only")
    ] = None,
    discovery_method: Annotated[
        str, typer.Option("--method", help="Discovery method")
    ] = "auto",
    force_refresh: Annotated[
        bool, typer.Option("--force-refresh", help="Force refresh cache")
    ] = False,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format (table, json)")
    ] = "table",
    include_static: Annotated[
        bool, typer.Option("--static/--no-static", help="Include static template tools")
    ] = True,
    include_dynamic: Annotated[
        bool,
        typer.Option(
            "--dynamic/--no-dynamic", help="Include tools from running deployments"
        ),
    ] = True,
):
    """
    List available tools from templates and deployments across all backends.

    Without arguments, shows all tools from all templates and running deployments.
    Specify a template name to filter to that template across all backends.
    Use --backend to limit to a specific backend.

    Examples:
        mcpt list-tools                    # All tools from all backends
        mcpt list-tools github             # GitHub template tools from all backends
        mcpt list-tools --backend docker   # All tools from docker backend only
        mcpt list-tools demo-12345         # Tools from specific deployment
    """
    try:
        # Single backend mode
        if backend or (
            template and len(template) > 20
        ):  # Deployment IDs are typically longer
            backend_type = backend or cli_state["backend_type"]
            tool_manager = ToolManager(backend_type)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Discovering tools...", total=None)

                # Adjust discovery method based on include flags
                actual_discovery_method = discovery_method
                if not include_static and include_dynamic:
                    # Force dynamic discovery when --no-static is used
                    actual_discovery_method = "auto"  # Will try dynamic methods first
                elif include_static and not include_dynamic:
                    # Force static discovery when --no-dynamic is used
                    actual_discovery_method = "static"

                # Get tools with metadata
                result = tool_manager.list_tools(
                    template_or_id=template or "",
                    discovery_method=actual_discovery_method,
                    force_refresh=force_refresh,
                )

            # Filter results based on include flags
            if result.get("tools"):
                discovery_used = result.get("discovery_method", "unknown")
                tools = result.get("tools", [])

                # Filter tools based on flags
                if not include_static and discovery_used == "static":
                    # If --no-static and result is static, show empty
                    result["tools"] = []
                elif not include_dynamic and discovery_used in [
                    "stdio",
                    "http",
                    "dynamic",
                ]:
                    # If --no-dynamic and result is dynamic, show empty
                    result["tools"] = []

            if output_format == "json":
                console.print(json.dumps(result, indent=2))
            else:
                display_tools_with_metadata(result, template or "")
            return

        # Multi-backend mode
        multi_manager = MultiBackendManager()
        available_backends = multi_manager.get_available_backends()

        if not available_backends:
            console.print("[red]❌ No backends available[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering tools across backends...", total=None)

            # Get all tools from all sources
            all_tools = multi_manager.get_all_tools(
                template_name=template,
                discovery_method=discovery_method,
                force_refresh=force_refresh,
                include_static=include_static,
                include_dynamic=include_dynamic,
            )

        if output_format == "json":
            console.print(json.dumps(all_tools, indent=2))
        else:
            render_tools_with_sources(all_tools)

        # Show discovery hints
        template_filter = f" for template '{template}'" if template else ""
        static_text = "static" if include_static else ""
        dynamic_text = "dynamic" if include_dynamic else ""
        sources = [s for s in [static_text, dynamic_text] if s]
        sources_text = (
            " and ".join(sources)
            if len(sources) > 1
            else (sources[0] if sources else "no")
        )

        console.print(f"\n💡 [dim]Showing {sources_text} tools{template_filter}[/dim]")
        if template:
            console.print(
                "💡 [dim]Use 'mcpt list-tools' without arguments to see all tools[/dim]"
            )
        console.print("💡 [dim]Use --backend <name> for single-backend discovery[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error listing tools: {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list(
    deployed_only: Annotated[
        bool, typer.Option("--deployed", help="Show only deployed templates")
    ] = False,
    backend: Annotated[
        Optional[str], typer.Option("--backend", help="Show specific backend only")
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, yaml")
    ] = "table",
    unified: Annotated[
        bool, typer.Option("--unified", help="Show all backends in single table")
    ] = False,
):
    """
    List available MCP server templates with deployment status across all backends.

    By default, shows templates and their deployment status across all available backends.
    Use --backend to limit to a specific backend, or --unified for a single table view.
    """
    try:
        # Single backend mode (backward compatibility)
        if backend:
            template_manager = TemplateManager(backend)
            deployment_manager = DeploymentManager(backend)

            # Get templates with deployment status
            templates = template_manager.list_templates()
            deployments = deployment_manager.list_deployments()

            if not templates:
                console.print("[yellow]No templates found[/yellow]")
                return

            # Count running instances per template
            running_counts = {}
            for deployment in deployments:
                if deployment.get("status") == "running":
                    template_name = deployment.get("template", "unknown")
                    running_counts[template_name] = (
                        running_counts.get(template_name, 0) + 1
                    )

            # Filter if deployed_only is requested
            if deployed_only:
                templates = {k: v for k, v in templates.items() if k in running_counts}
                if not templates:
                    console.print("[yellow]No deployed templates found[/yellow]")
                    return

            table = Table(
                title=f"Available MCP Server Templates ({backend})",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            table.add_column("Version", style="green")
            table.add_column("Running", style="yellow", justify="center")
            table.add_column("Image", style="dim")

            for name, info in templates.items():
                running_count = running_counts.get(name, 0)
                running_text = str(running_count) if running_count > 0 else "-"

                table.add_row(
                    name,
                    info.get("description", "No description"),
                    info.get("version", "latest"),
                    running_text,
                    info.get("docker_image", "N/A"),
                )

            console.print(table)
            console.print(
                "\n💡 [dim]Use 'mcpt deploy <template>' to deploy a template[/dim]"
            )
            return

        # Multi-backend mode
        multi_manager = MultiBackendManager()
        available_backends = multi_manager.get_available_backends()

        if not available_backends:
            console.print("[red]❌ No backends available[/red]")
            return

        # Get templates (backend-agnostic)
        template_manager = TemplateManager(
            available_backends[0]
        )  # Use any backend for template listing
        templates = template_manager.list_templates()

        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return

        # Get all deployments across backends
        all_deployments = multi_manager.get_all_deployments()

        # Count running instances per template per backend
        running_counts = {}
        for deployment in all_deployments:
            if deployment.get("status") == "running":
                template_name = deployment.get("template", "unknown")
                backend_type = deployment.get("backend_type", "unknown")

                if template_name not in running_counts:
                    running_counts[template_name] = {}
                running_counts[template_name][backend_type] = (
                    running_counts[template_name].get(backend_type, 0) + 1
                )

        # Filter if deployed_only is requested
        if deployed_only:
            templates = {k: v for k, v in templates.items() if k in running_counts}
            if not templates:
                console.print("[yellow]No deployed templates found[/yellow]")
                return

        # Output format handling
        if output_format == "json":
            output_data = {
                "templates": templates,
                "deployments": all_deployments,
                "running_counts": running_counts,
                "available_backends": available_backends,
            }
            console.print(json.dumps(output_data, indent=2))
            return
        elif output_format == "yaml":
            import yaml

            output_data = {
                "templates": templates,
                "deployments": all_deployments,
                "running_counts": running_counts,
                "available_backends": available_backends,
            }
            console.print(yaml.dump(output_data, default_flow_style=False))
            return

        # Table output with multi-backend view
        table = Table(
            title="Available MCP Server Templates (All Backends)",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Version", style="green")

        # Add columns for each available backend
        for backend_type in available_backends:
            backend_header = get_backend_indicator(backend_type, include_icon=False)
            table.add_column(backend_header, style="yellow", justify="center")

        table.add_column("Image", style="dim")

        for name, info in templates.items():
            row_data = [
                name,
                info.get("description", "No description"),
                info.get("version", "latest"),
            ]

            # Add running counts for each backend
            template_counts = running_counts.get(name, {})
            for backend_type in available_backends:
                count = template_counts.get(backend_type, 0)
                row_data.append(str(count) if count > 0 else "-")

            row_data.append(info.get("docker_image", "N/A"))
            table.add_row(*row_data)

        console.print(table)

        # Show backend summary
        total_running = sum(
            sum(backend_counts.values()) for backend_counts in running_counts.values()
        )
        backend_summary = ", ".join(available_backends)
        console.print(
            f"\n📊 [dim]Backends: {backend_summary} | Total running: {total_running}[/dim]"
        )
        console.print("💡 [dim]Use 'mcpt deploy <template>' to deploy a template[/dim]")
        console.print(
            "💡 [dim]Use 'mcpt list --backend <name>' for single-backend view[/dim]"
        )

    except Exception as e:
        console.print(f"[red]❌ Error listing templates: {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error listing templates: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_templates():
    """
    List available MCP server templates.

    This command shows all templates that can be deployed.
    """
    try:
        template_manager = TemplateManager(cli_state["backend_type"])
        templates = template_manager.list_templates()

        if not templates:
            console.print("[yellow]No templates found[/yellow]")
            return

        table = Table(
            title="Available MCP Server Templates",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Version", style="green")
        table.add_column("Image", style="dim")

        for name, info in templates.items():
            table.add_row(
                name,
                info.get("description", "No description"),
                info.get("version", "latest"),
                info.get("docker_image", "N/A"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error listing templates: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_deployments(
    template: Annotated[
        Optional[str], typer.Option("--template", help="Filter by template name")
    ] = None,
    backend: Annotated[
        Optional[str], typer.Option("--backend", help="Show specific backend only")
    ] = None,
    status: Annotated[
        Optional[str],
        typer.Option("--status", help="Filter by status (running, stopped, etc.)"),
    ] = None,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, grouped, json, yaml")
    ] = "grouped",
    all_statuses: Annotated[
        bool, typer.Option("--all", help="Show deployments with all statuses")
    ] = False,
):
    """
    List MCP server deployments across all backends.

    By default, shows running deployments grouped by backend. Use --backend to limit
    to a specific backend, or --all to include deployments with all statuses.
    """
    try:
        # Single backend mode (backward compatibility)
        if backend:
            deployment_manager = DeploymentManager(backend)
            all_deployments = deployment_manager.list_deployments()

            # Apply filters
            deployments = all_deployments
            if not all_statuses:
                deployments = [d for d in deployments if d.get("status") == "running"]
            if status:
                deployments = [d for d in deployments if d.get("status") == status]
            if template:
                deployments = [d for d in deployments if d.get("template") == template]

            if not deployments:
                status_text = f" with status '{status}'" if status else ""
                template_text = f" for template '{template}'" if template else ""
                console.print(
                    f"[yellow]No deployments found{status_text}{template_text}[/yellow]"
                )
                return

            table = Table(
                title=f"MCP Server Deployments ({backend})",
                show_header=True,
                header_style="bold blue",
            )
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Template", style="white")
            table.add_column("Status", style="green")
            table.add_column("Created", style="dim")
            table.add_column("Endpoint", style="dim")

            for deployment in deployments:
                status_val = deployment.get("status", "unknown")
                status_color = (
                    "green"
                    if status_val == "running"
                    else "red" if status_val == "stopped" else "yellow"
                )

                table.add_row(
                    deployment.get("id", "unknown")[:12],
                    deployment.get("template", "unknown"),
                    f"[{status_color}]{status_val}[/]",
                    (
                        deployment.get("created_at", "N/A")[:19]
                        if deployment.get("created_at")
                        else "N/A"
                    ),
                    deployment.get("endpoint", "N/A"),
                )

            console.print(table)
            return

        # Multi-backend mode
        multi_manager = MultiBackendManager()
        available_backends = multi_manager.get_available_backends()

        if not available_backends:
            console.print("[red]❌ No backends available[/red]")
            return

        # Get all deployments across backends
        all_deployments = multi_manager.get_all_deployments(template_name=template)

        # Apply filters
        deployments = all_deployments
        if not all_statuses:
            deployments = [d for d in deployments if d.get("status") == "running"]
        if status:
            deployments = [d for d in deployments if d.get("status") == status]

        if not deployments:
            filter_parts = []
            if status:
                filter_parts.append(f"status '{status}'")
            elif not all_statuses:
                filter_parts.append("status 'running'")
            if template:
                filter_parts.append(f"template '{template}'")

            filter_text = f" with {' and '.join(filter_parts)}" if filter_parts else ""
            console.print(f"[yellow]No deployments found{filter_text}[/yellow]")
            return

        # Output format handling
        if output_format == "json":
            console.print(json.dumps(deployments, indent=2))
            return
        elif output_format == "yaml":
            import yaml

            console.print(yaml.dump(deployments, default_flow_style=False))
            return

        # Group deployments by backend for visual organization
        grouped_deployments = {}
        for deployment in deployments:
            backend_type = deployment.get("backend_type", "unknown")
            if backend_type not in grouped_deployments:
                grouped_deployments[backend_type] = []
            grouped_deployments[backend_type].append(deployment)

        if output_format == "table":
            # Single unified table
            render_deployments_unified_table(deployments)
        else:
            # Grouped by backend (default)
            render_deployments_grouped_by_backend(grouped_deployments, show_empty=True)

        # Show summary
        summary = format_deployment_summary(deployments)
        console.print(f"\n📊 [dim]{summary}[/dim]")

        if not all_statuses:
            console.print(
                "💡 [dim]Use --all to show deployments with all statuses[/dim]"
            )
        console.print("💡 [dim]Use --backend <name> for single-backend view[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Error listing deployments: {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def stop(
    target: Annotated[
        Optional[str],
        typer.Argument(
            help="Deployment ID, template name, or 'all' to stop deployments"
        ),
    ] = None,
    backend: Annotated[
        Optional[str],
        typer.Option("--backend", help="Specify backend if auto-detection fails"),
    ] = None,
    all: Annotated[
        bool, typer.Option("--all", help="Stop all running deployments")
    ] = False,
    template: Annotated[
        Optional[str],
        typer.Option("--template", help="Stop all deployments for a specific template"),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be stopped")
    ] = False,
    timeout: Annotated[
        int, typer.Option("--timeout", help="Stop timeout in seconds")
    ] = 30,
    force: Annotated[
        bool, typer.Option("--force", help="Force stop without confirmation")
    ] = False,
):
    """
    Stop MCP server deployments.

    This command can stop deployments in several ways:
    1. Stop specific deployment by ID: mcpt stop <deployment-id>
    2. Stop all deployments: mcpt stop --all
    3. Stop all deployments for a template: mcpt stop --template <template-name>
    4. Stop with positional argument: mcpt stop all, mcpt stop <template-name>

    Use --backend to limit operations to a specific backend.
    Use --dry-run to preview what would be stopped.
    """

    template_manager = TemplateManager(
        backend or cli_state.get("backend_type", "docker")
    )
    all_templates = [key for key in template_manager.list_templates().keys()]
    # Validate arguments
    targets_specified = sum([bool(target), all, bool(template)])
    if targets_specified == 0:
        console.print(
            "[red]❌ Please specify what to stop: deployment ID, --all, or --template <name>[/red]"
        )
        console.print("Examples:")
        console.print("  mcpt stop <deployment-id>")
        console.print("  mcpt stop --all")
        console.print("  mcpt stop --template demo")
        console.print("  mcpt stop all")
        raise typer.Exit(1)

    if targets_specified > 1:
        console.print(
            "[red]❌ Please specify only one target: deployment ID, --all, or --template[/red]"
        )
        raise typer.Exit(1)

    # Handle positional argument shortcuts
    if target:
        if target.lower() == "all":
            all = True
            target = None
        elif target in all_templates:
            template = target
            target = None

    if dry_run:
        console.print(
            "[yellow]🔍 DRY RUN MODE - No actual stopping will occur[/yellow]"
        )

    try:
        # Handle different stop scenarios
        if all:
            # Stop all deployments
            if dry_run:
                console.print("Would stop all running deployments")
                if backend:
                    console.print(f"Limited to backend: {backend}")
                else:
                    console.print("Across all backends")
                return

            _stop_all_deployments(backend, timeout, force)

        elif template:
            # Stop all deployments for a specific template
            if dry_run:
                console.print(f"Would stop all deployments for template: {template}")
                if backend:
                    console.print(f"Limited to backend: {backend}")
                else:
                    console.print("Across all backends")
                return

            _stop_template_deployments(template, backend, timeout, force)

        else:
            # Stop specific deployment by ID
            deployment_id = target
            if dry_run:
                console.print(f"Would stop deployment: {deployment_id}")

                # Show backend detection in dry-run mode
                if not backend:
                    try:
                        multi_manager = MultiBackendManager()
                        detected_backend = multi_manager.detect_backend_for_deployment(
                            deployment_id
                        )
                        if detected_backend:
                            console.print(f"Auto-detected backend: {detected_backend}")
                        else:
                            console.print(
                                "Backend auto-detection would fail - use --backend"
                            )
                    except Exception as e:
                        console.print(f"Backend detection error: {e}")
                else:
                    console.print(f"Using specified backend: {backend}")
                return

            _stop_single_deployment(deployment_id, backend, timeout)

    except Exception as e:
        console.print(f"[red]❌ Error stopping deployment(s): {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)


def _stop_single_deployment(deployment_id: str, backend: Optional[str], timeout: int):
    """Stop a single deployment by ID."""
    # Use multi-backend manager for auto-detection or single backend
    if backend:
        # Single backend mode
        deployment_manager = DeploymentManager(backend)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Stopping deployment on {backend}...", total=None)
            result = deployment_manager.stop_deployment(deployment_id, timeout)

        if result.get("success"):
            console.print(
                f"[green]✅ Successfully stopped deployment '{deployment_id}' on {backend}[/green]"
            )
        else:
            error = result.get("error", "Unknown error")
            console.print(f"[red]❌ Failed to stop deployment: {error}[/red]")
            raise typer.Exit(1)
    else:
        # Multi-backend auto-detection mode
        multi_manager = MultiBackendManager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Auto-detecting backend and stopping deployment...", total=None
            )
            result = multi_manager.stop_deployment(deployment_id, timeout)

        if result.get("success"):
            backend_type = result.get("backend_type", "unknown")
            backend_indicator = get_backend_indicator(backend_type)
            console.print(
                f"[green]✅ Successfully stopped deployment '{deployment_id}' on {backend_indicator}[/green]"
            )
        else:
            error = result.get("error", "Unknown error")
            console.print(f"[red]❌ Failed to stop deployment: {error}[/red]")

            # Suggest using --backend flag if auto-detection failed
            if "not found" in error.lower():
                console.print(
                    "💡 [dim]Try using --backend <name> to specify the backend explicitly[/dim]"
                )
            raise typer.Exit(1)


def _stop_all_deployments(backend: Optional[str], timeout: int, force: bool):
    """Stop all running deployments."""
    if backend:
        # Single backend mode
        deployment_manager = DeploymentManager(backend)
        deployments = deployment_manager.list_deployments()
        running_deployments = [d for d in deployments if d.get("status") == "running"]

        if not running_deployments:
            console.print(
                f"[green]✅ No running deployments found on {backend}[/green]"
            )
            return

        # Show what will be stopped
        _show_stop_plan(running_deployments, f"Running deployments on {backend}")

        # Confirm if not forced
        if not force:
            confirmed = typer.confirm(
                f"Stop {len(running_deployments)} running deployment(s) on {backend}?"
            )
            if not confirmed:
                console.print("[yellow]Stop cancelled[/yellow]")
                return

        # Stop deployments
        stopped_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Stopping deployments on {backend}...", total=None
            )

            for deployment in running_deployments:
                deployment_id = deployment.get("id", "unknown")
                try:
                    result = deployment_manager.stop_deployment(deployment_id, timeout)
                    if result.get("success"):
                        stopped_count += 1
                    else:
                        failed_count += 1
                        console.print(
                            f"[yellow]⚠️ Failed to stop {deployment_id}: {result.get('error', 'Unknown error')}[/yellow]"
                        )
                except Exception as e:
                    failed_count += 1
                    console.print(
                        f"[yellow]⚠️ Failed to stop {deployment_id}: {e}[/yellow]"
                    )

        console.print(
            f"[green]✅ Stopped {stopped_count} deployment(s) on {backend}[/green]"
        )
        if failed_count > 0:
            console.print(
                f"[yellow]⚠️ Failed to stop {failed_count} deployment(s)[/yellow]"
            )

    else:
        # Multi-backend mode
        multi_manager = MultiBackendManager()
        available_backends = multi_manager.get_available_backends()

        if not available_backends:
            console.print("[red]❌ No backends available[/red]")
            return

        # Get all running deployments across backends
        all_deployments = multi_manager.get_all_deployments()
        running_deployments = [
            d for d in all_deployments if d.get("status") == "running"
        ]

        if not running_deployments:
            console.print(
                "[green]✅ No running deployments found across all backends[/green]"
            )
            return

        # Show what will be stopped
        _show_stop_plan(running_deployments, "Running deployments across all backends")

        # Confirm if not forced
        if not force:
            confirmed = typer.confirm(
                f"Stop {len(running_deployments)} running deployment(s) across all backends?"
            )
            if not confirmed:
                console.print("[yellow]Stop cancelled[/yellow]")
                return

        # Stop deployments using multi-backend manager
        stopped_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Stopping deployments across backends...", total=None
            )

            for deployment in running_deployments:
                deployment_id = deployment.get("id", "unknown")
                try:
                    result = multi_manager.stop_deployment(deployment_id, timeout)
                    if result.get("success"):
                        stopped_count += 1
                    else:
                        failed_count += 1
                        console.print(
                            f"[yellow]⚠️ Failed to stop {deployment_id}: {result.get('error', 'Unknown error')}[/yellow]"
                        )
                except Exception as e:
                    failed_count += 1
                    console.print(
                        f"[yellow]⚠️ Failed to stop {deployment_id}: {e}[/yellow]"
                    )

        console.print(
            f"[green]✅ Stopped {stopped_count} deployment(s) across all backends[/green]"
        )
        if failed_count > 0:
            console.print(
                f"[yellow]⚠️ Failed to stop {failed_count} deployment(s)[/yellow]"
            )


def _stop_template_deployments(
    template_name: str, backend: Optional[str], timeout: int, force: bool
):
    """Stop all deployments for a specific template."""
    if backend:
        # Single backend mode
        deployment_manager = DeploymentManager(backend)
        deployments = deployment_manager.list_deployments()
        template_deployments = [
            d
            for d in deployments
            if d.get("status") == "running" and d.get("template") == template_name
        ]

        if not template_deployments:
            console.print(
                f"[green]✅ No running deployments found for template '{template_name}' on {backend}[/green]"
            )
            return

        # Show what will be stopped
        _show_stop_plan(
            template_deployments,
            f"Running deployments for template '{template_name}' on {backend}",
        )

        # Confirm if not forced
        if not force:
            confirmed = typer.confirm(
                f"Stop {len(template_deployments)} running deployment(s) for template '{template_name}' on {backend}?"
            )
            if not confirmed:
                console.print("[yellow]Stop cancelled[/yellow]")
                return

        # Stop deployments
        stopped_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Stopping {template_name} deployments on {backend}...", total=None
            )

            for deployment in template_deployments:
                deployment_id = deployment.get("id", "unknown")
                try:
                    result = deployment_manager.stop_deployment(deployment_id, timeout)
                    if result.get("success"):
                        stopped_count += 1
                    else:
                        failed_count += 1
                        console.print(
                            f"[yellow]⚠️ Failed to stop {deployment_id}: {result.get('error', 'Unknown error')}[/yellow]"
                        )
                except Exception as e:
                    failed_count += 1
                    console.print(
                        f"[yellow]⚠️ Failed to stop {deployment_id}: {e}[/yellow]"
                    )

        console.print(
            f"[green]✅ Stopped {stopped_count} '{template_name}' deployment(s) on {backend}[/green]"
        )
        if failed_count > 0:
            console.print(
                f"[yellow]⚠️ Failed to stop {failed_count} deployment(s)[/yellow]"
            )

    else:
        # Multi-backend mode
        multi_manager = MultiBackendManager()
        available_backends = multi_manager.get_available_backends()

        if not available_backends:
            console.print("[red]❌ No backends available[/red]")
            return

        # Get all running deployments for the template across backends
        all_deployments = multi_manager.get_all_deployments(template_name=template_name)
        template_deployments = [
            d for d in all_deployments if d.get("status") == "running"
        ]

        if not template_deployments:
            console.print(
                f"[green]✅ No running deployments found for template '{template_name}' across all backends[/green]"
            )
            return

        # Show what will be stopped
        _show_stop_plan(
            template_deployments,
            f"Running deployments for template '{template_name}' across all backends",
        )

        # Confirm if not forced
        if not force:
            confirmed = typer.confirm(
                f"Stop {len(template_deployments)} running deployment(s) for template '{template_name}' across all backends?"
            )
            if not confirmed:
                console.print("[yellow]Stop cancelled[/yellow]")
                return

        # Stop deployments using multi-backend manager
        stopped_count = 0
        failed_count = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Stopping {template_name} deployments across backends...", total=None
            )

            for deployment in template_deployments:
                deployment_id = deployment.get("id", "unknown")
                try:
                    result = multi_manager.stop_deployment(deployment_id, timeout)
                    if result.get("success"):
                        stopped_count += 1
                    else:
                        failed_count += 1
                        console.print(
                            f"[yellow]⚠️ Failed to stop {deployment_id}: {result.get('error', 'Unknown error')}[/yellow]"
                        )
                except Exception as e:
                    failed_count += 1
                    console.print(
                        f"[yellow]⚠️ Failed to stop {deployment_id}: {e}[/yellow]"
                    )

        console.print(
            f"[green]✅ Stopped {stopped_count} '{template_name}' deployment(s) across all backends[/green]"
        )
        if failed_count > 0:
            console.print(
                f"[yellow]⚠️ Failed to stop {failed_count} deployment(s)[/yellow]"
            )


def _show_stop_plan(deployments: List[Dict[str, Any]], title: str):
    """Show a table of deployments that will be stopped."""
    table = Table(title=title, show_header=True, header_style="bold yellow")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Template", style="white")
    table.add_column("Backend", style="green")
    table.add_column("Status", style="yellow")

    for deployment in deployments:
        backend_type = deployment.get("backend_type", "unknown")
        backend_indicator = get_backend_indicator(backend_type, include_icon=False)

        table.add_row(
            deployment.get("id", "unknown")[:12],
            deployment.get("template", "unknown"),
            backend_indicator,
            deployment.get("status", "unknown"),
        )

    console.print(table)


@app.command(
    "interactive/i",
    help="Start the intreactive shell for intraction with MCP servers",
)
def interactive():
    """
    Start the interactive CLI mode.

    This command launches an interactive shell for MCP server management.
    """
    try:
        console.print("[cyan]🚀 Starting interactive CLI mode...[/cyan]")
        console.print("[dim]Type 'help' for available commands, 'quit' to exit[/dim]")

        # Import and start the interactive CLI
        from mcp_template.interactive_cli import InteractiveCLI

        interactive_cli = InteractiveCLI()
        interactive_cli.cmdloop()

    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive mode interrupted[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error in interactive mode: {e}[/red]")
        raise typer.Exit(1)


def install_completion():
    """Install shell completion for the CLI."""
    # Get the shell
    shell = os.environ.get("SHELL", "").split("/")[-1]

    try:
        if shell == "zsh":
            console.print("[cyan]Installing Zsh completion...[/cyan]")
            console.print("[yellow]Run this command to install completion:[/yellow]")
            console.print("[bold]python -m mcp_template --install-completion[/bold]")
            console.print("\n[yellow]Then add this to your ~/.zshrc:[/yellow]")
            console.print(
                '[bold]eval "$(_MCPT_COMPLETE=zsh_source python -m mcp_template)"[/bold]'
            )

        elif shell == "bash":
            console.print("[cyan]Installing Bash completion...[/cyan]")
            console.print("[yellow]Run this command to install completion:[/yellow]")
            console.print("[bold]python -m mcp_template --install-completion[/bold]")
            console.print("\n[yellow]Then add this to your ~/.bashrc:[/yellow]")
            console.print(
                '[bold]eval "$(_MCPT_COMPLETE=bash_source python -m mcp_template)"[/bold]'
            )

        elif shell == "fish":
            console.print("[cyan]Installing Fish completion...[/cyan]")
            console.print("[yellow]Run this command to install completion:[/yellow]")
            console.print("[bold]python -m mcp_template --install-completion[/bold]")
            console.print("\n[yellow]Then add this to your config.fish:[/yellow]")
            console.print(
                "[bold]eval (env _MCPT_COMPLETE=fish_source python -m mcp_template)[/bold]"
            )

        else:
            console.print(f"[yellow]Shell '{shell}' detected. Manual setup:[/yellow]")
            console.print(
                'For zsh: eval "$(_MCPT_COMPLETE=zsh_source python -m mcp_template)"'
            )
            console.print(
                'For bash: eval "$(_MCPT_COMPLETE=bash_source python -m mcp_template)"'
            )
            console.print(
                "For fish: eval (env _MCPT_COMPLETE=fish_source python -m mcp_template)"
            )

        console.print(
            f"\n[green]✅ Completion setup instructions provided for {shell}![/green]"
        )
        console.print(
            "[dim]Note: Restart your terminal after adding the completion line[/dim]"
        )

    except Exception as e:
        console.print(f"[red]Error setting up completion: {e}[/red]")


@app.command()
def logs(
    deployment_id: Annotated[
        str, typer.Argument(help="Deployment ID to get logs from")
    ],
    backend: Annotated[
        Optional[str],
        typer.Option("--backend", help="Specify backend if auto-detection fails"),
    ] = None,
    lines: Annotated[
        int, typer.Option("--lines", "-n", help="Number of log lines to retrieve")
    ] = 100,
    follow: Annotated[
        bool, typer.Option("--follow", "-f", help="Follow log output")
    ] = False,
):
    """
    Get logs from a running MCP server deployment.

    This command auto-detects the backend for the deployment and retrieves logs.
    Use --backend to specify the backend if auto-detection fails.
    Use --follow to stream logs in real-time.
    """
    try:
        # Use multi-backend manager for auto-detection or single backend
        if backend:
            # Single backend mode
            deployment_manager = DeploymentManager(backend)

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Getting logs from {backend}...", total=None)
                result = deployment_manager.get_deployment_logs(
                    deployment_id, lines=lines, follow=follow
                )

            if result.get("success"):
                logs = result.get("logs", "No logs available")
                console.print(
                    f"[bold]Logs for deployment '{deployment_id}' on {backend}:[/bold]\n"
                )
                console.print(logs)
            else:
                error = result.get("error", "Unknown error")
                console.print(f"[red]❌ Failed to get logs: {error}[/red]")
                raise typer.Exit(1)
        else:
            # Multi-backend auto-detection mode
            multi_manager = MultiBackendManager()

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    "Auto-detecting backend and getting logs...", total=None
                )
                result = multi_manager.get_deployment_logs(
                    deployment_id, lines=lines, follow=follow
                )

            if result.get("success"):
                backend_type = result.get("backend_type", "unknown")
                logs = result.get("logs", "No logs available")

                backend_indicator = get_backend_indicator(backend_type)

                console.print(
                    f"[bold]Logs for deployment '{deployment_id}' on {backend_indicator}:[/bold]\n"
                )
                console.print(logs)
            else:
                error = result.get("error", "Unknown error")
                console.print(f"[red]❌ Failed to get logs: {error}[/red]")

                # Suggest using --backend flag if auto-detection failed
                if "not found" in error.lower():
                    console.print(
                        "💡 [dim]Try using --backend <name> to specify the backend explicitly[/dim]"
                    )
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error getting logs: {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def status(
    output_format: Annotated[
        str, typer.Option("--format", help="Output format: table, json, yaml")
    ] = "table",
):
    """
    Show backend health status and deployment summary.

    This command shows the health status of all available backends
    along with a summary of deployments on each backend.
    """
    try:
        multi_manager = MultiBackendManager()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Checking backend health...", total=None)

            health_data = multi_manager.get_backend_health()
            all_deployments = multi_manager.get_all_deployments()

        if output_format == "json":
            output_data = {
                "backend_health": health_data,
                "deployments": all_deployments,
                "summary": {
                    "total_backends": len(health_data),
                    "healthy_backends": sum(
                        1 for h in health_data.values() if h.get("status") == "healthy"
                    ),
                    "total_deployments": len(all_deployments),
                    "running_deployments": len(
                        [d for d in all_deployments if d.get("status") == "running"]
                    ),
                },
            }
            console.print(json.dumps(output_data, indent=2))
            return
        elif output_format == "yaml":
            import yaml

            output_data = {
                "backend_health": health_data,
                "deployments": all_deployments,
                "summary": {
                    "total_backends": len(health_data),
                    "healthy_backends": sum(
                        1 for h in health_data.values() if h.get("status") == "healthy"
                    ),
                    "total_deployments": len(all_deployments),
                    "running_deployments": len(
                        [d for d in all_deployments if d.get("status") == "running"]
                    ),
                },
            }
            console.print(yaml.dump(output_data, default_flow_style=False))
            return

        # Table format
        render_backend_health_status(health_data)

        # Show deployment summary
        total_deployments = len(all_deployments)
        running_deployments = len(
            [d for d in all_deployments if d.get("status") == "running"]
        )

        console.print("\n📊 [bold]Deployment Summary[/bold]")
        console.print(f"Total deployments: {total_deployments}")
        console.print(f"Running deployments: {running_deployments}")

        if total_deployments > 0:
            # Group by backend for summary
            backend_counts = {}
            for deployment in all_deployments:
                backend_type = deployment.get("backend_type", "unknown")
                status = deployment.get("status", "unknown")

                if backend_type not in backend_counts:
                    backend_counts[backend_type] = {}
                backend_counts[backend_type][status] = (
                    backend_counts[backend_type].get(status, 0) + 1
                )

            console.print("\nPer-backend breakdown:")
            for backend_type, status_counts in backend_counts.items():
                backend_indicator = get_backend_indicator(backend_type)
                total = sum(status_counts.values())
                running = status_counts.get("running", 0)
                console.print(f"  {backend_indicator}: {running}/{total} running")

        console.print(
            "\n💡 [dim]Use 'mcpt list-deployments' for detailed deployment information[/dim]"
        )

    except Exception as e:
        console.print(f"[red]❌ Error checking status: {e}[/red]")
        if cli_state.get("verbose"):
            console.print_exception()
        raise typer.Exit(1)


@app.command(name="install-completion")
def install_completion_command():
    """Install shell completion for the CLI."""
    install_completion()


if __name__ == "__main__":
    app()
