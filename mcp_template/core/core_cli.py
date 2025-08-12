"""
Core CLI module using common modules.

This module provides the CLI interface that uses the common modules for
shared functionality, keeping CLI-specific logic focused on user interaction
and output formatting.
"""

import argparse
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

logger = logging.getLogger(__name__)


class CoreCLI:
    """
    Core CLI that uses common modules for shared functionality.
    
    This CLI focuses on:
    - Argument parsing and validation
    - User interaction and feedback
    - Output formatting and display
    - CLI-specific features like progress indicators
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize the refactored CLI."""
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
                filter_deployed_only=getattr(args, 'deployed', False)
            )
            
            if not templates:
                if getattr(args, 'deployed', False):
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
            self.console.print("💡 Use 'mcpt config <template>' to see configuration options")
            
        except Exception as e:
            self.formatter.print_error(f"Error showing config: {e}")
            sys.exit(1)

    def handle_shell_command(self, args) -> None:
        """Handle shell command to access running container."""
        try:
            template_name = getattr(args, 'template', None)
            custom_name = getattr(args, 'name', None)
            
            if not template_name and not custom_name:
                self.formatter.print_error("Template name or custom name is required")
                sys.exit(1)
                
            # Use deployment manager to access shell (placeholder)
            self.formatter.print_info(f"Shell access for {template_name or custom_name} - functionality pending")
                
        except Exception as e:
            self.formatter.print_error(f"Error accessing shell: {e}")
            sys.exit(1)

    def handle_cleanup_command(self, args) -> None:
        """Handle cleanup command to remove stopped containers."""
        try:
            template_name = getattr(args, 'template', None)
            all_containers = getattr(args, 'all', False)
            
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
                'config_file': getattr(args, 'config_file', None),
                'env_vars': self._parse_key_value_args(getattr(args, 'env', [])),
                'config_values': self._parse_key_value_args(getattr(args, 'config', [])),
                'override_values': self._parse_key_value_args(getattr(args, 'override', []))
            }

            deployment_options = DeploymentOptions(
                name=getattr(args, 'name', None),
                transport=getattr(args, 'transport', None),
                port=getattr(args, 'port', 7071),
                data_dir=getattr(args, 'data_dir', None),
                config_dir=getattr(args, 'config_dir', None),
                pull_image=not getattr(args, 'no_pull', False)
            )

            # Show config options if requested
            if getattr(args, 'show_config', False):
                self._show_config_options(args.template)
                return

            # Deploy with progress indicator
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Deploying {args.template}...", total=None)
                
                result = self.deployment_manager.deploy_template(
                    args.template, config_sources, deployment_options
                )
                
                progress.stop()

            # Display deployment result
            panel = self.formatter.format_deployment_result(result.to_dict())
            self.formatter.print_panel(panel.renderable, panel.title, 
                                     "green" if result.success else "red")
            
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
            
            if getattr(args, 'all', False):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    template_name=getattr(args, 'template', None)
                )
            elif getattr(args, 'name', None):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    custom_name=args.name
                )
            elif getattr(args, 'template', None):
                targets = self.deployment_manager.find_deployments_by_criteria(
                    template_name=args.template
                )

            if not targets:
                self.formatter.print_error("No deployments found matching criteria")
                return

            # Confirm bulk operations
            if len(targets) > 1 and not getattr(args, 'all', False):
                self.console.print(f"\n⚠️ Found {len(targets)} deployments matching criteria:")
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
                template_name=getattr(args, 'template', None),
                custom_name=getattr(args, 'name', None)
            )

            if not deployment_id:
                self.formatter.print_error(f"No deployment found for {args.template}")
                return

            # Get logs
            if getattr(args, 'follow', False):
                self._stream_logs_with_display(deployment_id)
            else:
                lines = getattr(args, 'lines', 100)
                result = self.deployment_manager.get_deployment_logs(deployment_id, lines=lines)
                
                if result["success"]:
                    self.console.print(f"\n📋 Logs for deployment: {deployment_id} (last {lines} lines)\n")
                    formatted_logs = self.formatter.format_logs(result["logs"])
                    self.console.print(formatted_logs)
                    
                    self.console.print(f"\n💡 Use 'mcpt logs {args.template} --follow' to stream logs in real-time")
                    self.console.print(f"💡 Use 'mcpt logs {args.template} --lines 500' to see more history")
                else:
                    self.formatter.print_error(f"Failed to get logs: {result.get('error', 'Unknown error')}")

        except Exception as e:
            self.formatter.print_error(f"Logs operation failed: {e}")
            sys.exit(1)

    def handle_tools_command(self, args) -> None:
        """Handle the tools/list_tools command."""
        try:
            discovery_method = getattr(args, 'method', 'auto')
            force_refresh = getattr(args, 'refresh', False)
            
            tools = self.tool_manager.list_tools(
                args.template,
                discovery_method=discovery_method,
                force_refresh=force_refresh
            )

            if not tools:
                self.formatter.print_info(f"No tools found for {args.template}")
                return

            # Format and display tools table
            table = self.formatter.format_tools_table(tools)
            
            self.console.print(f"\n🔧 Available Tools for {args.template}:\n")
            self.formatter.print_table(table)
            
            # Show helpful tips
            self.console.print(f"\n💡 Use 'call say_hello name=\"World\"' to call a tool")
            self.console.print(f"💡 Use 'call say_hello --help' for detailed parameter information")

        except Exception as e:
            self.formatter.print_error(f"Failed to list tools: {e}")
            sys.exit(1)

    def handle_config_command(self, args) -> None:
        """Handle the config command."""
        try:
            if getattr(args, 'validate', False):
                result = self.config_manager.validate_template_configuration(args.template)
                panel = self.formatter.format_validation_results(result)
                self.console.print(panel)
                
                if not result["valid"]:
                    sys.exit(1)
            else:
                configs = self.config_manager.load_configuration_for_template(args.template)
                
                if not configs:
                    self.formatter.print_info(f"No configurations found for template {args.template}")
                    return
                
                self.console.print(f"\n🔧 Configuration Management for Template: {args.template}\n")
                
                table = self.formatter.format_config_overview(configs)
                self.formatter.print_table(table)
                
                self.console.print(f"\n💡 Use 'mcpt config {args.template} --validate' to check all configurations")

        except Exception as e:
            self.formatter.print_error(f"Config operation failed: {e}")
            sys.exit(1)

    def _parse_key_value_args(self, args: List[str]) -> Dict[str, str]:
        """Parse key=value arguments into a dictionary."""
        result = {}
        for arg in args:
            if '=' not in arg:
                self.formatter.print_warning(f"Ignoring invalid argument: {arg} (expected key=value format)")
                continue
            key, value = arg.split('=', 1)
            result[key] = value
        return result

    def _show_config_options(self, template_name: str) -> None:
        """Show configuration options for a template."""
        try:
            schema = self.template_manager.get_template_config_schema(template_name)
            
            if not schema:
                self.formatter.print_info(f"No configuration schema found for {template_name}")
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

    def _confirm_action(self, message: str) -> bool:
        """Ask user for confirmation."""
        try:
            response = input(f"{message} [y/N]: ").strip().lower()
            return response in ['y', 'yes']
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


def create_refactored_cli_parser() -> argparse.ArgumentParser:
    """Create argument parser for refactored CLI."""
    parser = argparse.ArgumentParser(
        description="Deploy MCP server templates with zero configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcpt list                    # List available templates
  mcpt deploy demo             # Deploy demo template
  mcpt logs demo               # View logs
  mcpt stop demo               # Stop deployment
  mcpt config demo             # Show configuration
  mcpt tools demo              # List available tools
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser(
        "list",
        help="List available templates",
        description="List all available templates with their metadata.",
    )
    list_parser.add_argument(
        "--deployed",
        action="store_true",
        help="List only deployed templates",
    )

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a template")
    deploy_parser.add_argument("template", help="Template name to deploy")
    deploy_parser.add_argument("--name", help="Custom deployment name")
    deploy_parser.add_argument("--data-dir", help="Custom data directory")
    deploy_parser.add_argument("--config-dir", help="Custom config directory")
    deploy_parser.add_argument(
        "--env", action="append", help="Environment variables (KEY=VALUE)"
    )
    deploy_parser.add_argument(
        "--config-file", help="Path to JSON/YAML configuration file"
    )
    deploy_parser.add_argument(
        "--config",
        action="append",
        help="Configuration values (KEY=VALUE)",
    )
    deploy_parser.add_argument(
        "--override",
        action="append",
        help="Template data overrides (KEY=VALUE) with double underscore notation",
    )
    deploy_parser.add_argument(
        "--transport",
        choices=["http", "stdio", "sse", "streamable-http"],
        default=None,
        help="Transport protocol for MCP communication (default: http)",
    )
    deploy_parser.add_argument(
        "--port", type=int, default=7071, help="Port for HTTP transport (default: 7071)"
    )
    deploy_parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show available configuration options",
    )
    deploy_parser.add_argument(
        "--no-pull",
        action="store_true",
        help="Skip pulling Docker image (use local image)",
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a deployed template")
    stop_parser.add_argument(
        "template",
        nargs="?",
        help="Template name to stop",
    )
    stop_parser.add_argument("--name", help="Custom deployment name")
    stop_parser.add_argument(
        "--all",
        action="store_true",
        help="Stop all deployments",
    )

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show template logs")
    logs_parser.add_argument("template", help="Template name")
    logs_parser.add_argument("--name", help="Custom deployment name")
    logs_parser.add_argument("--lines", type=int, default=100, help="Number of log lines to show")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs")

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="List available tools")
    tools_parser.add_argument("template", help="Template name")
    tools_parser.add_argument("--method", choices=["static", "dynamic", "image", "auto"], 
                             default="auto", help="Tool discovery method")
    tools_parser.add_argument("--refresh", action="store_true", help="Force refresh cache")

    # Config command
    config_parser = subparsers.add_parser("config", help="Manage template configurations")
    config_parser.add_argument("template", help="Template name")
    config_parser.add_argument("--validate", action="store_true", help="Validate configurations")

    return parser
