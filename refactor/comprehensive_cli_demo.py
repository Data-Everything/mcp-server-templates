"""
Comprehensive refactored CLI demonstrating all common modules.

This showcases the complete refactored architecture with all 4 common modules:
- TemplateManager: Template discovery and management
- DeploymentManager: Deployment lifecycle management
- ConfigManager: Configuration processing and validation
- ToolManager: Tool discovery and management
"""

import json
import sys
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_template.common.config_manager import ConfigManager
from mcp_template.common.deployment_manager import DeploymentManager

# Import all common modules
from mcp_template.common.template_manager import TemplateManager
from mcp_template.common.tool_manager import ToolManager

console = Console()


class ComprehensiveRefactoredCLI:
    """
    Comprehensive refactored CLI using all common modules.

    This demonstrates the complete architecture with all shared functionality
    centralized in common modules, making CLI commands thin wrappers that
    focus purely on user interaction and output formatting.
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize with all common managers."""
        self.template_manager = TemplateManager()
        self.deployment_manager = DeploymentManager(backend_type)
        self.config_manager = ConfigManager()
        self.tool_manager = ToolManager(backend_type)

    def list_templates_command(
        self, deployed_only: bool = False, format_type: str = "table"
    ) -> bool:
        """Enhanced list command with multiple output formats."""
        try:
            templates = self.template_manager.list_templates(
                force_refresh=False,
                include_deployment_status=True,
                deployed_only=deployed_only,
            )

            if not templates:
                console.print("[yellow]⚠️  No templates found[/yellow]")
                return True

            if format_type == "json":
                print(json.dumps(templates, indent=2))
                return True

            # Rich table format
            self._display_templates_table(templates, deployed_only)
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to list templates: {e}[/red]")
            return False

    def _display_templates_table(self, templates: Dict[str, Any], deployed_only: bool):
        """Display templates in rich table format."""
        title = f"{'Available' if not deployed_only else 'Deployed'} MCP Templates"
        table = Table(title=title)
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Version", style="yellow", width=10)
        table.add_column("Category", style="magenta", width=15)
        table.add_column("Status", style="green", width=20)

        # Get deployment information
        deployments = self.deployment_manager.list_deployments()
        deployment_counts = {}
        for deployment in deployments:
            template_name = deployment.get("template", "unknown")
            deployment_counts[template_name] = (
                deployment_counts.get(template_name, 0) + 1
            )

        for template_name, template_data in templates.items():
            description = template_data.get("description", "No description")
            version = template_data.get("version", "latest")
            category = template_data.get("category", "general")

            deployment_count = deployment_counts.get(template_name, 0)
            status = (
                f"✅ Running ({deployment_count})"
                if deployment_count > 0
                else "⚪ Not deployed"
            )

            if deployed_only and deployment_count == 0:
                continue

            table.add_row(template_name, description, version, category, status)

        console.print(table)

    def deploy_template_command(
        self,
        template_id: str,
        config_file: Optional[str] = None,
        config_args: Optional[List[str]] = None,
        env_args: Optional[List[str]] = None,
        **kwargs,
    ) -> bool:
        """Enhanced deploy command with comprehensive configuration processing."""
        try:
            # Validate template exists
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                console.print(f"[red]❌ Template '{template_id}' not found[/red]")
                return False

            console.print(
                Panel(
                    f"🚀 Deploying template: [cyan]{template_id}[/cyan]\n"
                    f"Description: {template_data.get('description', 'No description')}",
                    title="MCP Template Deployment",
                    border_style="blue",
                )
            )

            # Process configuration using ConfigManager
            config_values = {}
            env_vars = {}

            if config_file:
                file_config = self.config_manager.load_config_file(config_file)
                config_values.update(file_config)

            if config_args:
                cli_config = self.config_manager.process_command_line_config(
                    config_args
                )
                config_values.update(cli_config)

            if env_args:
                env_vars = self.config_manager.process_environment_variables(env_args)

            # Prepare final configuration
            final_config = self.config_manager.prepare_configuration(
                template=template_data, config_values=config_values, env_vars=env_vars
            )

            # Validate configuration
            validation = self.config_manager.validate_configuration(
                template_data, final_config
            )
            if not validation["valid"]:
                console.print("[red]❌ Configuration validation failed:[/red]")
                for error in validation["errors"]:
                    console.print(f"  • {error}")
                return False

            # Deploy using DeploymentManager
            result = self.deployment_manager.deploy_template(
                template_id=template_id,
                configuration=final_config,
                env_vars=env_vars,
                **kwargs,
            )

            if result:
                console.print("[green]✅ Deployment successful![/green]")
                self._display_deployment_info(result)
                return True
            else:
                console.print("[red]❌ Deployment failed[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Deployment failed: {e}[/red]")
            return False

    def _display_deployment_info(self, result: Dict[str, Any]):
        """Display deployment information."""
        info_table = Table(title="Deployment Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="white")

        for key, value in result.items():
            if key not in ["template", "config"]:
                info_table.add_row(key.replace("_", " ").title(), str(value))

        console.print(info_table)

    def list_tools_command(
        self,
        template_name: str,
        discovery_method: str = "auto",
        force_refresh: bool = False,
    ) -> bool:
        """Enhanced tools command using ToolManager."""
        try:
            # Validate template exists
            template_data = self.template_manager.get_template(template_name)
            if not template_data:
                console.print(f"[red]❌ Template '{template_name}' not found[/red]")
                return False

            console.print(
                Panel(
                    f"🔧 Discovering tools for: [cyan]{template_name}[/cyan]",
                    title="Tool Discovery",
                    border_style="blue",
                )
            )

            # Discover tools using ToolManager
            result = self.tool_manager.discover_tools(
                template_name=template_name,
                template_config=template_data,
                discovery_method=discovery_method,
                force_refresh=force_refresh,
            )

            tools = result.get("tools", [])
            method = result.get("discovery_method", "unknown")
            source = result.get("source", "unknown")

            console.print(f"[dim]Discovery method: {method}[/dim]")
            console.print(f"[dim]Source: {source}[/dim]")

            if not tools:
                console.print("[yellow]⚠️  No tools found[/yellow]")
                if result.get("error"):
                    console.print(f"[red]Error: {result['error']}[/red]")
                return True

            # Display tools table
            self._display_tools_table(tools)

            # Show usage examples
            self._show_tool_usage_examples(template_name, tools)
            return True

        except Exception as e:
            console.print(f"[red]❌ Tool discovery failed: {e}[/red]")
            return False

    def _display_tools_table(self, tools: List[Dict[str, Any]]):
        """Display tools in a rich table."""
        table = Table()
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Parameters", style="yellow", width=25)
        table.add_column("Category", style="green", width=15)

        for tool in tools:
            formatted = self.tool_manager.format_tool_for_display(tool)
            table.add_row(
                formatted["name"],
                formatted["description"],
                formatted["parameters"],
                formatted["category"],
            )

        console.print(table)

    def _show_tool_usage_examples(
        self, template_name: str, tools: List[Dict[str, Any]]
    ):
        """Show tool usage examples."""
        console.print("\n[cyan]💡 Tool Usage Examples:[/cyan]")

        if tools:
            first_tool = tools[0]["name"]
            console.print("  # Call a tool:")
            console.print(f"  mcpt call {template_name} {first_tool}")
            console.print(f"  mcpt call {template_name} {first_tool} --args '{{}}'")

    def validate_config_command(
        self, template_id: str, config_file: Optional[str] = None
    ) -> bool:
        """New command to validate configuration without deploying."""
        try:
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                console.print(f"[red]❌ Template '{template_id}' not found[/red]")
                return False

            console.print(
                Panel(
                    f"🔍 Validating configuration for: [cyan]{template_id}[/cyan]",
                    title="Configuration Validation",
                    border_style="blue",
                )
            )

            config_values = {}
            if config_file:
                config_values = self.config_manager.load_config_file(config_file)

            validation = self.config_manager.validate_configuration(
                template_data, config_values
            )

            if validation["valid"]:
                console.print("[green]✅ Configuration is valid![/green]")
            else:
                console.print("[red]❌ Configuration validation failed:[/red]")
                for error in validation["errors"]:
                    console.print(f"  • {error}")

            if validation["warnings"]:
                console.print("[yellow]⚠️  Warnings:[/yellow]")
                for warning in validation["warnings"]:
                    console.print(f"  • {warning}")

            return validation["valid"]

        except Exception as e:
            console.print(f"[red]❌ Validation failed: {e}[/red]")
            return False

    def generate_config_command(
        self, template_id: str, output_file: Optional[str] = None
    ) -> bool:
        """New command to generate example configuration."""
        try:
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                console.print(f"[red]❌ Template '{template_id}' not found[/red]")
                return False

            console.print(
                Panel(
                    f"📋 Generating configuration for: [cyan]{template_id}[/cyan]",
                    title="Configuration Generation",
                    border_style="green",
                )
            )

            example_config = self.config_manager.generate_example_config(template_data)

            if output_file:
                success = self.config_manager.export_configuration(
                    example_config, output_file, "json"
                )
                if success:
                    console.print(
                        f"[green]✅ Configuration saved to {output_file}[/green]"
                    )
                else:
                    console.print("[red]❌ Failed to save configuration[/red]")
                    return False
            else:
                console.print("\n[cyan]Example Configuration:[/cyan]")
                print(json.dumps(example_config, indent=2))

            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to generate configuration: {e}[/red]")
            return False

    def cleanup_command(
        self, template_filter: Optional[str] = None, force: bool = False
    ) -> bool:
        """Enhanced cleanup command using DeploymentManager."""
        try:
            console.print(
                Panel(
                    "🧹 Cleaning up deployments...",
                    title="Deployment Cleanup",
                    border_style="yellow",
                )
            )

            result = self.deployment_manager.cleanup_deployments(
                template_filter=template_filter, force=force
            )

            # Display results
            if result["cleaned"]:
                console.print(
                    f"[green]✅ Cleaned {len(result['cleaned'])} deployments[/green]"
                )
                for deployment_id in result["cleaned"]:
                    console.print(f"  • {deployment_id}")

            if result["skipped"]:
                console.print(
                    f"[yellow]⚠️  Skipped {len(result['skipped'])} running deployments[/yellow]"
                )
                if not force:
                    console.print("  Use --force to cleanup running deployments")

            if result["failed"]:
                console.print(
                    f"[red]❌ Failed to cleanup {len(result['failed'])} deployments[/red]"
                )
                for deployment_id in result["failed"]:
                    console.print(f"  • {deployment_id}")

            return True

        except Exception as e:
            console.print(f"[red]❌ Cleanup failed: {e}[/red]")
            return False


def main():
    """Enhanced main function demonstrating comprehensive refactored architecture."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP Template CLI (Comprehensively Refactored)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List templates")
    list_parser.add_argument(
        "--deployed", action="store_true", help="Show only deployed templates"
    )
    list_parser.add_argument(
        "--format", choices=["table", "json"], default="table", help="Output format"
    )

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy template")
    deploy_parser.add_argument("template", help="Template name")
    deploy_parser.add_argument("--config-file", help="Configuration file")
    deploy_parser.add_argument(
        "--config", action="append", help="Configuration values (KEY=VALUE)"
    )
    deploy_parser.add_argument(
        "--env", action="append", help="Environment variables (KEY=VALUE)"
    )

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="List tools for template")
    tools_parser.add_argument("template", help="Template name")
    tools_parser.add_argument(
        "--method",
        choices=["auto", "static", "dynamic", "docker"],
        default="auto",
        help="Discovery method",
    )
    tools_parser.add_argument(
        "--refresh", action="store_true", help="Force refresh cache"
    )

    # Search command
    search_parser = subparsers.add_parser("search", help="Search templates")
    search_parser.add_argument("query", help="Search query")

    # Validate config command
    validate_parser = subparsers.add_parser("validate", help="Validate configuration")
    validate_parser.add_argument("template", help="Template name")
    validate_parser.add_argument("--config-file", help="Configuration file to validate")

    # Generate config command
    generate_parser = subparsers.add_parser(
        "generate-config", help="Generate example configuration"
    )
    generate_parser.add_argument("template", help="Template name")
    generate_parser.add_argument("--output", help="Output file path")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup deployments")
    cleanup_parser.add_argument("--template", help="Filter by template")
    cleanup_parser.add_argument(
        "--force", action="store_true", help="Force cleanup running deployments"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize CLI
    cli = ComprehensiveRefactoredCLI()

    # Dispatch commands
    try:
        if args.command == "list":
            success = cli.list_templates_command(
                deployed_only=args.deployed, format_type=args.format
            )
        elif args.command == "deploy":
            success = cli.deploy_template_command(
                template_id=args.template,
                config_file=getattr(args, "config_file", None),
                config_args=getattr(args, "config", None),
                env_args=getattr(args, "env", None),
            )
        elif args.command == "tools":
            success = cli.list_tools_command(
                template_name=args.template,
                discovery_method=args.method,
                force_refresh=args.refresh,
            )
        elif args.command == "search":
            templates = cli.template_manager.search_templates(args.query)
            if templates:
                cli._display_templates_table(templates, False)
                console.print(f"\n[dim]Found {len(templates)} matching templates[/dim]")
            else:
                console.print(
                    f"[yellow]⚠️  No templates found matching '{args.query}'[/yellow]"
                )
            success = True
        elif args.command == "validate":
            success = cli.validate_config_command(
                template_id=args.template,
                config_file=getattr(args, "config_file", None),
            )
        elif args.command == "generate-config":
            success = cli.generate_config_command(
                template_id=args.template, output_file=getattr(args, "output", None)
            )
        elif args.command == "cleanup":
            success = cli.cleanup_command(
                template_filter=getattr(args, "template", None),
                force=getattr(args, "force", False),
            )
        else:
            console.print(f"[red]❌ Unknown command: {args.command}[/red]")
            success = False

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Operation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
