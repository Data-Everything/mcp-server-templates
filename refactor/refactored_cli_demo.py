"""
Refactored CLI command handlers using common modules.

This demonstrates how CLI commands will be refactored to use the common
TemplateManager and DeploymentManager modules instead of duplicating
logic between CLI and MCPClient.
"""

from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_template.common.deployment_manager import DeploymentManager
from mcp_template.common.template_manager import TemplateManager

console = Console()


class RefactoredCLICommands:
    """
    Refactored CLI command handlers using common modules.

    This class demonstrates the new pattern where CLI commands are thin wrappers
    around common functionality, focusing only on argument parsing, validation,
    and output formatting.
    """

    def __init__(self, backend_type: str = "docker"):
        """Initialize with common managers."""
        self.template_manager = TemplateManager()
        self.deployment_manager = DeploymentManager(backend_type)

    def list_templates_command(self, deployed_only: bool = False) -> bool:
        """
        Refactored list command using TemplateManager.

        This replaces the original deployer.list_templates() method,
        demonstrating how CLI-specific formatting is separated from
        core template management logic.

        Args:
            deployed_only: Whether to only show deployed templates

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use TemplateManager for core template operations
            templates = self.template_manager.list_templates(
                force_refresh=False,
                include_deployment_status=True,  # We need deployment status for display
                deployed_only=deployed_only,
            )

            if not templates:
                if deployed_only:
                    console.print("[yellow]⚠️  No deployed templates found[/yellow]")
                else:
                    console.print("[yellow]⚠️  No templates available[/yellow]")
                return True

            # Get deployment information for status display
            deployments = self.deployment_manager.list_deployments()
            deployment_counts = {}
            for deployment in deployments:
                template_name = deployment.get("template", "unknown")
                if template_name not in deployment_counts:
                    deployment_counts[template_name] = 0
                deployment_counts[template_name] += 1

            # CLI-specific formatting using Rich
            title = f"{'Available' if not deployed_only else 'Deployed'} MCP Templates"
            table = Table(title=title)
            table.add_column("Template", style="cyan", width=20)
            table.add_column("Description", style="white", width=50)
            table.add_column("Version", style="yellow", width=10)
            table.add_column("Category", style="magenta", width=15)
            table.add_column("Status", style="green", width=20)

            for template_name, template_data in templates.items():
                description = template_data.get("description", "No description")
                version = template_data.get("version", "latest")
                category = template_data.get("category", "general")

                # Determine status from deployment information
                deployment_count = deployment_counts.get(template_name, 0)
                if deployment_count > 0:
                    status = f"✅ Running ({deployment_count})"
                else:
                    status = "⚪ Not deployed"

                # Only add row if it matches our filter
                if deployed_only and deployment_count == 0:
                    continue

                table.add_row(template_name, description, version, category, status)

            console.print(table)

            # Show summary information
            total_templates = len(templates)
            running_count = len(
                [t for t in templates.keys() if deployment_counts.get(t, 0) > 0]
            )

            summary = f"📊 Total: {total_templates} templates"
            if not deployed_only:
                summary += f" | Running: {running_count} | Available: {total_templates - running_count}"

            console.print(f"\n[dim]{summary}[/dim]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to list templates: {e}[/red]")
            return False

    def deploy_template_command(
        self, template_id: str, config_values: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bool:
        """
        Refactored deploy command using DeploymentManager.

        This replaces the original CLI deploy logic, demonstrating how
        deployment orchestration is handled by the common module.

        Args:
            template_id: Template to deploy
            config_values: Configuration values
            **kwargs: Additional deployment parameters

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate template exists using TemplateManager
            template_data = self.template_manager.get_template(template_id)
            if not template_data:
                console.print(f"[red]❌ Template '{template_id}' not found[/red]")
                available_templates = list(
                    self.template_manager.list_templates().keys()
                )
                if available_templates:
                    console.print(
                        f"[dim]Available templates: {', '.join(available_templates)}[/dim]"
                    )
                return False

            # CLI-specific validation and user feedback
            console.print(
                Panel(
                    f"🚀 Deploying template: [cyan]{template_id}[/cyan]\n"
                    f"Description: {template_data.get('description', 'No description')}\n"
                    f"Version: {template_data.get('version', 'latest')}",
                    title="MCP Template Deployment",
                    border_style="blue",
                )
            )

            # Validate configuration before deployment
            validation_result = self.deployment_manager.validate_deployment_config(
                template_id, config_values
            )

            if not validation_result["valid"]:
                console.print("[red]❌ Configuration validation failed:[/red]")
                for error in validation_result["errors"]:
                    console.print(f"  • {error}")

                if validation_result["missing_properties"]:
                    console.print("\n[yellow]Missing required properties:[/yellow]")
                    for prop in validation_result["missing_properties"]:
                        console.print(f"  • {prop}")

                return False

            # Show warnings if any
            if validation_result.get("warnings"):
                console.print("[yellow]⚠️  Validation warnings:[/yellow]")
                for warning in validation_result["warnings"]:
                    console.print(f"  • {warning}")

            # Use DeploymentManager for actual deployment
            result = self.deployment_manager.deploy_template(
                template_id=template_id, configuration=config_values, **kwargs
            )

            if result:
                console.print("[green]✅ Deployment successful![/green]")

                # Display deployment information
                deployment_info = Table(title="Deployment Information")
                deployment_info.add_column("Property", style="cyan")
                deployment_info.add_column("Value", style="white")

                for key, value in result.items():
                    if key not in ["template", "config"]:  # Skip complex objects
                        deployment_info.add_row(
                            key.replace("_", " ").title(), str(value)
                        )

                console.print(deployment_info)

                # Show next steps
                console.print("\n[cyan]💡 Next steps:[/cyan]")
                console.print(f"  • View logs: [bold]mcpt logs {template_id}[/bold]")
                console.print(
                    f"  • Stop deployment: [bold]mcpt stop {template_id}[/bold]"
                )

                return True
            else:
                console.print("[red]❌ Deployment failed[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Deployment failed: {e}[/red]")
            return False

    def stop_deployment_command(self, deployment_id: str) -> bool:
        """
        Refactored stop command using DeploymentManager.

        Args:
            deployment_id: ID of the deployment to stop

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if deployment exists
            status = self.deployment_manager.get_deployment_status(deployment_id)
            if not status:
                console.print(f"[red]❌ Deployment '{deployment_id}' not found[/red]")

                # Show available deployments
                deployments = self.deployment_manager.list_deployments()
                if deployments:
                    console.print("\n[dim]Available deployments:[/dim]")
                    for deployment in deployments:
                        deployment_name = deployment.get("id") or deployment.get("name")
                        template_name = deployment.get("template", "unknown")
                        console.print(f"  • {deployment_name} ({template_name})")

                return False

            # CLI-specific confirmation and feedback
            template_name = status.get("template", "unknown")
            console.print(
                Panel(
                    f"🛑 Stopping deployment: [cyan]{deployment_id}[/cyan]\n"
                    f"Template: {template_name}",
                    title="Stop Deployment",
                    border_style="red",
                )
            )

            # Use DeploymentManager for actual stop operation
            success = self.deployment_manager.stop_deployment(deployment_id)

            if success:
                console.print("[green]✅ Deployment stopped successfully![/green]")
                return True
            else:
                console.print("[red]❌ Failed to stop deployment[/red]")
                return False

        except Exception as e:
            console.print(f"[red]❌ Failed to stop deployment: {e}[/red]")
            return False

    def search_templates_command(self, query: str) -> bool:
        """
        New search command using TemplateManager.

        This demonstrates how new functionality can be easily added
        by leveraging the common modules.

        Args:
            query: Search query string

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use TemplateManager for search functionality
            matching_templates = self.template_manager.search_templates(query)

            if not matching_templates:
                console.print(
                    f"[yellow]⚠️  No templates found matching '{query}'[/yellow]"
                )
                return True

            console.print(
                Panel(
                    f"🔍 Search results for: [cyan]{query}[/cyan]",
                    title="Template Search",
                    border_style="blue",
                )
            )

            table = Table()
            table.add_column("Template", style="cyan", width=20)
            table.add_column("Description", style="white", width=50)
            table.add_column("Category", style="magenta", width=15)
            table.add_column("Tags", style="yellow", width=20)

            for template_name, template_data in matching_templates.items():
                description = template_data.get("description", "No description")
                category = template_data.get("category", "general")
                tags = ", ".join(template_data.get("tags", []))

                table.add_row(template_name, description, category, tags)

            console.print(table)
            console.print(
                f"\n[dim]Found {len(matching_templates)} matching templates[/dim]"
            )
            return True

        except Exception as e:
            console.print(f"[red]❌ Search failed: {e}[/red]")
            return False


# Example of how the main CLI would use the refactored commands
def refactored_main_example():
    """
    Example of how the main CLI function would be refactored.

    This shows the pattern where the main function becomes much simpler,
    with all complex logic moved to common modules.
    """
    import argparse

    parser = argparse.ArgumentParser(description="MCP Template CLI (Refactored)")
    subparsers = parser.add_subparsers(dest="command")

    # List command
    list_parser = subparsers.add_parser("list", help="List templates")
    list_parser.add_argument(
        "--deployed", action="store_true", help="Show only deployed templates"
    )

    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy template")
    deploy_parser.add_argument("template", help="Template name")
    deploy_parser.add_argument(
        "--config", action="append", help="Configuration values (KEY=VALUE)"
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop deployment")
    stop_parser.add_argument("deployment_id", help="Deployment ID")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search templates")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize refactored CLI
    cli = RefactoredCLICommands()

    # Handle commands with simple dispatch
    if args.command == "list":
        success = cli.list_templates_command(deployed_only=args.deployed)
    elif args.command == "deploy":
        # Parse config values
        config_values = {}
        if hasattr(args, "config") and args.config:
            for config_pair in args.config:
                if "=" in config_pair:
                    key, value = config_pair.split("=", 1)
                    config_values[key] = value

        success = cli.deploy_template_command(args.template, config_values)
    elif args.command == "stop":
        success = cli.stop_deployment_command(args.deployment_id)
    elif args.command == "search":
        success = cli.search_templates_command(args.query)
    else:
        console.print(f"[red]❌ Unknown command: {args.command}[/red]")
        success = False

    if not success:
        exit(1)


if __name__ == "__main__":
    refactored_main_example()
