#!/usr/bin/env python3
"""
CLI module for MCP Template deployment.

This module provides CLI functionality using core modules for shared logic.
Consolidates functionality from EnhancedCLI for simplicity.
"""

import json
import logging
import sys
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mcp_template.core import (
    TemplateManager,
    DeploymentManager,
    ConfigManager,
    ToolManager,
    OutputFormatter,
)
from mcp_template.core.deployment_manager import DeploymentOptions

# Module-level console for backward compatibility with tests
console = Console()
logger = logging.getLogger(__name__)


class CLI:
    """
    Unified CLI that uses core modules for shared functionality.

    This CLI focuses on:
    - Argument parsing and validation
    - User interaction and feedback
    - Output formatting and display
    - CLI-specific features like progress indicators
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize the CLI."""
        self.console = Console()
        self.formatter = OutputFormatter(self.console)
        self.template_manager = TemplateManager(backend_type)
        self.deployment_manager = DeploymentManager(backend_type)
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager(backend_type)

    def handle_list_command(self, args) -> None:
        """Handle the list command."""
        try:
            templates = self.template_manager.list_templates(
                include_deployed_status=True,
                filter_deployed_only=getattr(args, "deployed", False),
            )

            if not templates:
                if getattr(args, "deployed", False):
                    self.formatter.print_info("No deployed templates found")
                else:
                    self.formatter.print_info("No templates found")
                return

            # Format and display templates table
            table = self.formatter.format_templates_table(templates, show_deployed=True)

            self.console.print("\n📋 Available Templates:\n")
            self.formatter.print_table(table)

            # Show helpful tips
            self.console.print("\n💡 Use 'mcpt deploy <template>' to deploy a template")
            self.console.print(
                "💡 Use 'mcpt config <template>' to see configuration options"
            )

        except Exception as e:
            self.formatter.print_error(f"Error showing config: {e}")
            sys.exit(1)

    def handle_shell_command(self, args) -> None:
        """Handle shell command to access running container."""
        try:
            template_name = getattr(args, "template", None)
            custom_name = getattr(args, "name", None)

            if not template_name and not custom_name:
                self.formatter.print_error("Template name or custom name is required")
                sys.exit(1)

            if template_name and not custom_name:
                running_deployments = (
                    self.deployment_manager.find_deployments_by_criteria(
                        template_name=template_name, status="running"
                    )
                )
                if not running_deployments:
                    self.formatter.print_error(
                        f"Template {template_name} has no running deployments"
                    )
                    sys.exit(1)
                elif len(running_deployments) > 1:
                    self.formatter.print_error(
                        f"Multiple running deployments found for {template_name}. Please specify --name to select one from {', '.join([running_deployments.get('id', 'unknown') for running_deployments in running_deployments])}"
                    )
                    sys.exit(1)
                else:
                    self.formatter.print_info("Connecting to running deployment...")
                    custom_name = running_deployments[0].get("id", None)

            if custom_name:
                self.deployment_manager.connect_to_deployment(custom_name)
            else:
                self.formatter.print_error(
                    "Failed to connect to deployment. Please create an issue in the project repo"
                )
                sys.exit(1)

            # Use deployment manager to access shell (placeholder)
            self.formatter.print_info(
                f"Shell access for {template_name or custom_name} - functionality pending"
            )

        except Exception as e:
            self.formatter.print_error(f"Error accessing shell: {e}")
            sys.exit(1)

    def handle_cleanup_command(self, args) -> None:
        """Handle cleanup command to remove stopped containers."""
        try:
            template_name = getattr(args, "template", None)
            all_containers = getattr(args, "all", False)

            # Use deployment manager to clean up (placeholder)
            self.formatter.print_info("Cleanup functionality - pending implementation")

        except Exception as e:
            self.formatter.print_error(f"Error during cleanup: {e}")
            sys.exit(1)

    def handle_deploy_command(self, args) -> None:
        """Handle the deploy command."""
        try:
            # Parse CLI arguments into structured config
            config_sources = {
                "config_file": getattr(args, "config_file", None),
                "env_vars": self._parse_key_value_args(
                    getattr(args, "env", None) or []
                ),
                "config_values": self._parse_key_value_args(
                    getattr(args, "config", None) or []
                ),
                "override_values": self._parse_key_value_args(
                    getattr(args, "override", None) or []
                ),
            }

            deployment_options = DeploymentOptions(
                name=getattr(args, "name", None),
                transport=getattr(args, "transport", None),
                port=getattr(args, "port", 7071),
                data_dir=getattr(args, "data_dir", None),
                config_dir=getattr(args, "config_dir", None),
                pull_image=not getattr(args, "no_pull", False),
            )

            # Show config options if requested
            if getattr(args, "show_config", False):
                self._show_config_options(args.template)
                return

            # Deploy with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task(f"Deploying {args.template}...", total=None)

                result = self.deployment_manager.deploy_template(
                    args.template, config_sources, deployment_options
                )

                progress.stop()

            # Display deployment result
            panel = self.formatter.format_deployment_result(result.to_dict())
            self.formatter.print_panel(
                panel.renderable, panel.title, "green" if result.success else "red"
            )

            if not result.success:
                sys.exit(1)

        except Exception as e:
            self.formatter.print_error(f"Deployment failed: {e}")
            sys.exit(1)

    def handle_stop_command(self, args) -> None:
        """Handle the stop command."""
        try:
            # Find target deployments
            targets = []

            if getattr(args, "all", False):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    template_name=getattr(args, "template", None)
                )
            elif getattr(args, "name", None):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    custom_name=args.name
                )
            elif getattr(args, "template", None):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    template_name=args.template
                )

            if not targets:
                self.formatter.print_error("No deployments found matching criteria")
                return

            # Confirm bulk operations
            if len(targets) > 1 and not getattr(args, "all", False):
                self.console.print(
                    f"\n⚠️ Found {len(targets)} deployments matching criteria:"
                )
                for target in targets:
                    self.console.print(f"  • {target.get('id', 'unknown')}")

                if not self._confirm_action("Stop all these deployments?"):
                    self.formatter.print_info("Operation cancelled")
                    return

            # Execute stops
            if len(targets) == 1:
                result = self.deployment_manager.stop_deployment(targets[0]["id"])
                message = self.formatter.format_stop_result(result)
                self.console.print(message)
            else:
                result = self.deployment_manager.stop_deployments_bulk(
                    [t["id"] for t in targets]
                )
                message = self.formatter.format_stop_result(result)
                self.console.print(message)

        except Exception as e:
            self.formatter.print_error(f"Stop operation failed: {e}")
            sys.exit(1)

    def handle_logs_command(self, args) -> None:
        """Handle the logs command."""
        try:
            # Find deployment
            deployment_id = self.deployment_manager.find_deployment_for_logs(
                template_name=getattr(args, "template", None),
                custom_name=getattr(args, "name", None),
            )

            if not deployment_id:
                self.formatter.print_error(f"No deployment found for {args.template}")
                return

            # Get logs
            if getattr(args, "follow", False):
                self._stream_logs_with_display(deployment_id)
            else:
                lines = getattr(args, "lines", 100)
                result = self.deployment_manager.get_deployment_logs(
                    deployment_id, lines=lines
                )

                if result["success"]:
                    self.console.print(
                        f"\n📋 Logs for deployment: {deployment_id} (last {lines} lines)\n"
                    )
                    formatted_logs = self.formatter.format_logs(result["logs"])
                    self.console.print(formatted_logs)

                    self.console.print(
                        f"\n💡 Use 'mcpt logs {args.template} --follow' to stream logs in real-time"
                    )
                    self.console.print(
                        f"💡 Use 'mcpt logs {args.template} --lines 500' to see more history"
                    )
                else:
                    self.formatter.print_error(
                        f"Failed to get logs: {result.get('error', 'Unknown error')}"
                    )

        except Exception as e:
            self.formatter.print_error(f"Logs operation failed: {e}")
            sys.exit(1)

    def _parse_key_value_args(self, args: List[str]) -> Dict[str, str]:
        """Parse key=value arguments into a dictionary."""
        result = {}
        for arg in args:
            if "=" not in arg:
                self.formatter.print_warning(
                    f"Ignoring invalid argument: {arg} (expected key=value format)"
                )
                continue
            key, value = arg.split("=", 1)
            result[key] = value
        return result

    def _show_config_options(self, template_name: str) -> None:
        """Show configuration options for a template."""
        try:
            schema = self.template_manager.get_template_config_schema(template_name)

            if not schema:
                self.formatter.print_info(
                    f"No configuration schema found for {template_name}"
                )
                return

            self.console.print(f"\n🔧 Configuration Options for {template_name}:\n")

            properties = schema.get("properties", {})
            if properties:
                for prop_name, prop_def in properties.items():
                    prop_type = prop_def.get("type", "unknown")
                    description = prop_def.get("description", "No description")
                    default = prop_def.get("default", "No default")

                    self.console.print(f"• [cyan]{prop_name}[/cyan] ({prop_type})")
                    self.console.print(f"  {description}")
                    self.console.print(f"  Default: {default}\n")
            else:
                self.formatter.print_info("No configurable properties found")

        except Exception as e:
            self.formatter.print_error(f"Failed to show config options: {e}")

    def show_config_options(self, template_name: str) -> None:
        """Show configuration options for a template."""
        self._show_config_options(template_name)

    def _confirm_action(self, message: str) -> bool:
        """Ask user for confirmation."""
        try:
            response = input(f"{message} [y/N]: ").strip().lower()
            return response in ["y", "yes"]
        except (KeyboardInterrupt, EOFError):
            return False

    def _stream_logs_with_display(self, deployment_id: str) -> None:
        """Stream logs with rich display."""
        try:
            self.console.print(f"\n📋 Streaming logs for deployment: {deployment_id}\n")
            self.console.print("Press Ctrl+C to stop streaming...\n")

            def log_callback(log_line: str):
                formatted_line = self.formatter.format_logs(log_line)
                self.console.print(formatted_line, end="")

            self.deployment_manager.stream_deployment_logs(deployment_id, log_callback)

        except KeyboardInterrupt:
            self.console.print("\n\n⏹️  Log streaming stopped by user")
        except Exception as e:
            self.formatter.print_error(f"Log streaming failed: {e}")


# Legacy compatibility - some methods from the old EnhancedCLI for backward compatibility
class EnhancedCLI(CLI):
    """Legacy alias for backward compatibility."""

    def __init__(self):
        super().__init__()
        # Keep some CLI-specific properties for compatibility
        self.verbose = False
        self.beautifier = None

    def show_config_options(self, template_name: str) -> None:
        """Show configuration options for a template."""
        self._show_config_options(template_name)

    def list_tools(
        self,
        template_name: Optional[str] = None,
        image_name: Optional[str] = None,
        static_discovery: bool = False,
        output_format: str = "table",
        connect_timeout: int = 30,
    ) -> None:
        """List available tools from various sources."""
        try:
            if template_name:
                tools = self.tool_manager.list_tools(template_name)
            elif image_name:
                tools = self.tool_manager.discover_tools_from_image(
                    image_name, connect_timeout
                )
            else:
                # For listing all tools, we could list from all templates, but that's complex
                # For now, just show a message
                self.console.print(
                    "[yellow]Please specify a template_name or image_name[/yellow]"
                )
                return

            # Use formatter to display tools
            if tools:
                self.formatter.format_tools_table(tools)
            else:
                self.console.print("[yellow]No tools found[/yellow]")
        except Exception as e:
            self.console.print(f"[red]❌ Error listing tools: {e}[/red]")

    # Additional methods for backward compatibility
    def deploy_with_transport(
        self,
        template_name: str,
        transport: Optional[str] = None,
        port: int = 7071,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
        config_values: Optional[Dict[str, str]] = None,
        override_values: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
    ) -> bool:
        """Deploy a template with transport configuration."""
        try:
            config_sources = {
                "config_file": config_file,
                "env_vars": env_vars or {},
                "config_values": config_values or {},
                "override_values": override_values or {},
            }

            deployment_options = DeploymentOptions(
                name=None,
                transport=transport,
                port=port,
                data_dir=data_dir,
                config_dir=config_dir,
                pull_image=pull_image,
            )

            result = self.deployment_manager.deploy_template(
                template_name, config_sources, deployment_options
            )
            return result.success
        except Exception as e:
            self.console.print(f"[red]❌ Error deploying template: {e}[/red]")
            return False

    def setup_docker_network(self) -> bool:
        """Set up Docker network for MCP platform."""
        try:
            return self.deployment_manager.setup_infrastructure()
        except Exception as e:
            self.console.print(f"[red]❌ Error setting up Docker network: {e}[/red]")
            return False

    def run_stdio_tool(
        self, template_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> None:
        """Run a tool via stdio transport."""
        try:
            result = self.tool_manager.call_tool(template_name, tool_name, arguments)
            if result:
                self.console.print("[green]✅ Tool executed successfully[/green]")
                self.console.print(json.dumps(result, indent=2))
            else:
                self.console.print("[red]❌ Tool execution failed[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Error running tool: {e}[/red]")


def add_enhanced_cli_args(subparsers) -> None:
    """Add enhanced CLI arguments to subparsers for backward compatibility."""
    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Show configuration options for a template"
    )
    config_parser.add_argument("template", help="Template name")

    # Tools command
    tools_parser = subparsers.add_parser(
        "tools",
        help="List available tools [Deprecated - Use mcpt interactive shell in-stead]",
    )
    tools_parser.add_argument("template", nargs="?", help="Template name (optional)")
    tools_parser.add_argument("--image", help="Docker image name")
    tools_parser.add_argument(
        "--static", action="store_true", help="Use static discovery"
    )
    tools_parser.add_argument("--format", default="table", help="Output format")

    # Discover tools command
    discover_parser = subparsers.add_parser(
        "discover-tools",
        help="Discover tools from Docker image  [Deprecated - Use mcpt interactive shell in-stead]",
    )
    discover_parser.add_argument("image", help="Docker image name")
    discover_parser.add_argument("--format", default="table", help="Output format")

    # Integration examples command
    examples_parser = subparsers.add_parser(
        "examples", help="Show integration examples"
    )
    examples_parser.add_argument("template", help="Template name")

    # Run tool command
    run_tool_parser = subparsers.add_parser(
        "run-tool",
        help="Run a specific tool [Deprecated - Use mcpt interactive shell in-stead]",
    )
    run_tool_parser.add_argument("template", help="Template name")
    run_tool_parser.add_argument("tool", help="Tool name")
    run_tool_parser.add_argument("--args", help="Tool arguments as JSON")

    # Interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Start interactive CLI"
    )


def handle_enhanced_cli_commands(args) -> bool:
    """Handle enhanced CLI commands for backward compatibility."""
    from rich.console import Console

    console = Console()

    if args.command == "config":
        # Config is still supported
        cli = EnhancedCLI()
        cli.show_config_options(args.template)
        return True
    elif args.command == "interactive":
        # Start interactive CLI
        from mcp_template.interactive_cli import start_interactive_cli

        start_interactive_cli()
        return True
    elif args.command == "tools":
        # Tools command is deprecated
        console.print("[yellow]⚠️  The 'tools' command has been deprecated.[/yellow]")
        console.print(
            "[blue]💡 Use 'mcpt interactive' to access tool management features.[/blue]"
        )
        sys.exit(2)
    elif args.command == "discover-tools":
        # Discover tools command is deprecated
        console.print(
            "[yellow]⚠️  The 'discover-tools' command has been deprecated.[/yellow]"
        )
        console.print(
            "[blue]💡 Use 'mcpt interactive' to access tool discovery features.[/blue]"
        )
        sys.exit(2)
    elif args.command == "run-tool":
        # Run tool command is deprecated
        console.print("[yellow]⚠️  The 'run-tool' command has been deprecated.[/yellow]")
        console.print("[blue]💡 Use 'mcpt interactive' to run tools.[/blue]")
        sys.exit(2)
    elif args.command == "examples":
        # Examples might still be supported, or also deprecated
        cli = EnhancedCLI()
        template_info = cli.template_manager.get_template_info(args.template)
        if template_info:
            cli.console.print(f"[blue]Integration examples for {args.template}:[/blue]")
            cli.console.print(
                f"• Connect to running server: mcpt connect {args.template}"
            )
            cli.console.print("• List tools: mcpt interactive")
            cli.console.print(f"• View logs: mcpt logs {args.template}")
        else:
            cli.console.print(f"[red]❌ Template '{args.template}' not found[/red]")
        return True

    return False


def get_enhanced_cli() -> "CLI":
    """Get a shared CLI instance for backward compatibility."""
    if not hasattr(get_enhanced_cli, "_instance"):
        get_enhanced_cli._instance = CLI()
    return get_enhanced_cli._instance
