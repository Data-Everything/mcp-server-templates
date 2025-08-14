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

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import typer
from rich import print as rich_print
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from mcp_template.core import (
    ConfigManager,
    DeploymentManager,
    OutputFormatter,
    TemplateManager,
    ToolManager,
)
from mcp_template.core.deployment_manager import DeploymentOptions

# Create the main Typer app
app = typer.Typer(
    name="mcpt",
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
    "backend_type": "docker",
    "verbose": False,
    "dry_run": False,
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
        Optional[Path], typer.Option("--config", "-c", help="Path to config file")
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
            help="Template data overrides. Override configuration values (key=value). supports double underscore notation for nested fields, e.g., tools__0__custom_field=value",
        ),
    ] = None,
    transport: Annotated[
        Optional[str],
        typer.Option("--transport", help="Transport protocol (http, stdio)"),
    ] = None,
    no_pull: Annotated[
        bool, typer.Option("--no-pull", help="Don't pull latest Docker image")
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run", help="Show what would be deployed without actually deploying"
        ),
    ] = False,
):
    """
    Deploy an MCP server template.

    This command deploys the specified template with the given configuration.
    Use --dry-run to preview what would be deployed.

    Examples:
        mcpt deploy github --config github-config.json
        mcpt deploy filesystem --set allowed_dirs=/tmp --dry-run
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
        config_manager = ConfigManager()

        # Process configuration
        config_dict = {}
        if config_file:
            config_dict.update(config_manager._load_config_file(str(config_file)))

        if env:
            for env_var in env:
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    config_dict[key] = value

        if config_overrides:
            for override_item in config_overrides:
                if "=" in override_item:
                    key, value = override_item.split("=", 1)
                    config_dict[key] = value

        if override:
            for override_item in override:
                if "=" in override_item:
                    key, value = override_item.split("=", 1)
                    # Add OVERRIDE_ prefix to distinguish from regular config
                    config_dict[f"OVERRIDE_{key}"] = value

        if transport:
            config_dict["MCP_TRANSPORT"] = transport

        # Get template info
        template_info = template_manager.get_template_info(template)
        if not template_info:
            console.print(f"[red]❌ Template '{template}' not found[/red]")
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

        if config_dict:
            plan_table.add_row("Config Keys", ", ".join(config_dict.keys()))

        console.print(plan_table)

        if dry_run:
            console.print(
                "\n[yellow]✅ Dry run complete - deployment plan shown above[/yellow]"
            )
            return

        # Actual deployment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Deploying template...", total=None)

            options = DeploymentOptions(
                pull_image=not no_pull,
            )

            result = deployment_manager.deploy_template(template, config_dict, options)

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

    except Exception as e:
        console.print(f"[red]❌ Error during deployment: {e}[/red]")
        if cli_state["verbose"]:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list_tools(
    template: Annotated[str, typer.Argument(help="Template name or deployment ID")],
    discovery_method: Annotated[
        str, typer.Option("--method", help="Discovery method")
    ] = "auto",
    force_refresh: Annotated[
        bool, typer.Option("--force-refresh", help="Force refresh cache")
    ] = False,
    output_format: Annotated[
        str, typer.Option("--format", help="Output format (table, json)")
    ] = "table",
):
    """
    List available tools from a template or deployment.

    This command discovers and displays tools available from MCP servers.
    The discovery method indicates how the tools were found.

    Examples:
        mcpt list-tools github
        mcpt list-tools demo-12345 --force-refresh
        mcpt list-tools filesystem --method static --format json
    """
    try:
        tool_manager = ToolManager(cli_state["backend_type"])

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Discovering tools...", total=None)

            # Get tools with metadata
            result = tool_manager.list_tools(
                template_or_id=template,
                discovery_method=discovery_method,
                force_refresh=force_refresh,
            )

        if output_format == "json":
            console.print(json.dumps(result, indent=2))
        else:
            display_tools_with_metadata(result, template)

    except Exception as e:
        console.print(f"[red]❌ Error listing tools: {e}[/red]")
        if cli_state["verbose"]:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def list(
    deployed_only: Annotated[
        bool, typer.Option("--deployed", help="Show only deployed templates")
    ] = False,
):
    """
    List available MCP server templates with deployment status.

    This command shows all templates that can be deployed, along with their
    current deployment status and running instance count.
    """
    try:
        template_manager = TemplateManager(cli_state["backend_type"])
        deployment_manager = DeploymentManager(cli_state["backend_type"])

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
                running_counts[template_name] = running_counts.get(template_name, 0) + 1

        # Filter if deployed_only is requested
        if deployed_only:
            templates = {k: v for k, v in templates.items() if k in running_counts}
            if not templates:
                console.print("[yellow]No deployed templates found[/yellow]")
                return

        table = Table(
            title="Available MCP Server Templates",
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
def list_deployments():
    """
    List running MCP server deployments.

    This command shows all currently running MCP servers.
    """
    try:
        deployment_manager = DeploymentManager(cli_state["backend_type"])
        all_deployments = deployment_manager.list_deployments()

        # Filter to only show running deployments
        deployments = [d for d in all_deployments if d.get("status") == "running"]

        if not deployments:
            console.print("[yellow]No running deployments found[/yellow]")
            return

        table = Table(
            title="Running MCP Server Deployments",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Template", style="white")
        table.add_column("Status", style="green")
        table.add_column("Endpoint", style="dim")

        for deployment in deployments:
            table.add_row(
                deployment.get("id", "unknown"),
                deployment.get("template", "unknown"),
                f"[green]{deployment.get('status', 'unknown')}[/green]",
                deployment.get("endpoint", "N/A"),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Error listing deployments: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stop(
    deployment_id: Annotated[str, typer.Argument(help="Deployment ID to stop")],
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be stopped")
    ] = False,
):
    """
    Stop a running MCP server deployment.

    This command stops and removes the specified deployment.
    Use --dry-run to preview what would be stopped.
    """
    if dry_run:
        console.print(
            "[yellow]🔍 DRY RUN MODE - No actual stopping will occur[/yellow]"
        )
        console.print(f"Would stop deployment: {deployment_id}")
        return

    try:
        deployment_manager = DeploymentManager(cli_state["backend_type"])

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Stopping deployment...", total=None)

            result = deployment_manager.stop_deployment(deployment_id)

            if result.get("success"):
                console.print(
                    f"[green]✅ Successfully stopped deployment '{deployment_id}'[/green]"
                )
            else:
                error = result.get("error", "Unknown error")
                console.print(f"[red]❌ Failed to stop deployment: {error}[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error stopping deployment: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def cleanup(
    template: Annotated[
        Optional[str],
        typer.Argument(help="Template to cleanup (or all if not specified)"),
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would be cleaned up")
    ] = False,
    force: Annotated[
        bool, typer.Option("--force", help="Force cleanup without confirmation")
    ] = False,
):
    """
    Clean up stopped containers and unused resources.

    This command removes stopped containers and cleans up resources.
    Use --dry-run to preview what would be cleaned up.
    """
    if dry_run:
        console.print("[yellow]🔍 DRY RUN MODE - No actual cleanup will occur[/yellow]")

    try:
        deployment_manager = DeploymentManager(cli_state["backend_type"])

        # List what would be cleaned up
        deployments = deployment_manager.list_deployments()
        stopped_deployments = [d for d in deployments if d.get("status") != "running"]

        if template:
            stopped_deployments = [
                d for d in stopped_deployments if d.get("template") == template
            ]

        if not stopped_deployments:
            console.print("[green]✅ No stopped deployments to clean up[/green]")
            return

        # Show cleanup plan
        table = Table(
            title="Cleanup Plan", show_header=True, header_style="bold yellow"
        )
        table.add_column("ID", style="cyan")
        table.add_column("Template", style="white")
        table.add_column("Status", style="red")

        for deployment in stopped_deployments:
            table.add_row(
                deployment.get("id", "unknown"),
                deployment.get("template", "unknown"),
                deployment.get("status", "unknown"),
            )

        console.print(table)

        if dry_run:
            console.print(
                "\n[yellow]✅ Dry run complete - cleanup plan shown above[/yellow]"
            )
            return

        # Confirm cleanup
        if not force:
            confirmed = typer.confirm(
                f"Clean up {len(stopped_deployments)} stopped deployment(s)?"
            )
            if not confirmed:
                console.print("[yellow]Cleanup cancelled[/yellow]")
                return

        # Perform cleanup
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Cleaning up deployments...", total=None)

            result = deployment_manager.cleanup_deployments(template)

            if result.get("success"):
                cleaned = result.get("cleaned_count", 0)
                console.print(
                    f"[green]✅ Successfully cleaned up {cleaned} deployment(s)[/green]"
                )
            else:
                error = result.get("error", "Unknown error")
                console.print(f"[red]❌ Cleanup failed: {error}[/red]")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]❌ Error during cleanup: {e}[/red]")
        raise typer.Exit(1)


@app.command()
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


@app.command(name="install-completion")
def install_completion_command():
    """Install shell completion for the CLI."""
    install_completion()


if __name__ == "__main__":
    app()
