"""
MCP Template Deployment Tool

A unified deployment system that provides:
- Rich CLI interface for standalone users
- Backend abstraction for different deployment targets
- Dynamic template discovery and configuration management
- Zero-configuration deployment experience

The system follows a layered architecture:
1. CLI Layer: Rich interface for user interaction
2. Management Layer: DeploymentManager orchestrates operations
3. Backend Layer: Pluggable deployment services (Docker, Kubernetes, etc.)
4. Discovery Layer: Dynamic template detection and configuration

Key Features:
- Template-driven configuration (no hardcoded template logic)
- Configurable image pulling (supports local development)
- Generic deployment utilities (reusable across templates)
- Comprehensive error handling and logging
"""

import argparse
import logging
import sys

from rich.console import Console

from mcp_template.backends.docker import DockerDeploymentService

# Import enhanced CLI modules
from mcp_template.cli import (
    EnhancedCLI,
    add_enhanced_cli_args,
    handle_enhanced_cli_commands,
)
from mcp_template.deployer import MCPDeployer
from mcp_template.manager import DeploymentManager
from mcp_template.template.creation import TemplateCreator

# Import core classes that are used in CI and the CLI
from mcp_template.template.discovery import TemplateDiscovery

# Export the classes for external use (CI compatibility)
__all__ = [
    "TemplateDiscovery",
    "DockerDeploymentService",
    "DeploymentManager",
    "MCPDeployer",
    "TemplateCreator",
]

# Constants
DEFAULT_CONFIG_PATH = "/config"
CUSTOM_NAME_HELP = "Custom container name"

console = Console()
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the MCP deployer CLI.
    """

    parser = argparse.ArgumentParser(
        description="Deploy MCP server templates with zero configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-template list                    # List available templates
  mcp-template file-server             # Deploy file server with defaults
  mcp-template file-server --name fs   # Deploy with custom name
  mcp-template logs file-server        # View logs
  mcp-template stop file-server        # Stop deployment
  mcp-template shell file-server       # Open shell in container
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List available templates")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new template")
    create_parser.add_argument(
        "template_id", nargs="?", help="Template ID (e.g., 'my-api-server')"
    )
    create_parser.add_argument(
        "--config-file", help="Path to template configuration file"
    )
    create_parser.add_argument(
        "--non-interactive", action="store_true", help="Run in non-interactive mode"
    )

    # Deploy command (default)
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a template")
    deploy_parser.add_argument("template", help="Template name to deploy")
    deploy_parser.add_argument("--name", help=CUSTOM_NAME_HELP)
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
        help="Configuration values (KEY=VALUE) - for config_schema properties",
    )
    deploy_parser.add_argument(
        "--override",
        action="append",
        help="Template data overrides (KEY=VALUE) - supports double underscore notation (e.g., tools__0__custom_field=value)",
    )
    deploy_parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
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
    stop_parser.add_argument("template", help="Template name to stop")
    stop_parser.add_argument("--name", help=CUSTOM_NAME_HELP)

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show template logs")
    logs_parser.add_argument("template", help="Template name")
    logs_parser.add_argument("--name", help=CUSTOM_NAME_HELP)
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs")

    # Shell command
    shell_parser = subparsers.add_parser("shell", help="Open shell in template")
    shell_parser.add_argument("template", help="Template name")
    shell_parser.add_argument("--name", help=CUSTOM_NAME_HELP)

    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        "cleanup", help="Clean up stopped/failed deployments"
    )
    cleanup_parser.add_argument(
        "template", nargs="?", help="Template name to clean up (optional)"
    )
    cleanup_parser.add_argument(
        "--all", action="store_true", help="Clean up all deployments"
    )
    # Add enhanced CLI commands
    add_enhanced_cli_args(subparsers)

    # Parse arguments
    args = parser.parse_args()

    # Initialize deployer again if not already done
    if "deployer" not in locals():
        deployer = MCPDeployer()
        available_templates = deployer.templates.keys()

    # Initialize enhanced CLI
    enhanced_cli = EnhancedCLI()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        # Try enhanced CLI commands first
        if handle_enhanced_cli_commands(args, enhanced_cli):
            return

        if args.command == "list":
            deployer.list_templates()
        elif args.command == "create":
            creator = TemplateCreator()
            success = creator.create_template_interactive(
                template_id=getattr(args, "template_id", None),
                config_file=getattr(args, "config_file", None),
            )
            if not success:
                sys.exit(1)
        elif args.command == "deploy":
            template = args.template if hasattr(args, "template") else args.command

            # Show configuration options if requested
            if hasattr(args, "show_config") and args.show_config:
                deployer._show_config_options(template)
                return

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

            override_values = {}
            if hasattr(args, "override") and args.override:
                for override_var in args.override:
                    key, value = override_var.split("=", 1)
                    override_values[key] = value

            # Deploy using enhanced CLI with transport support
            success = enhanced_cli.deploy_with_transport(
                template_name=template,
                transport=getattr(args, "transport", "http"),
                port=getattr(args, "port", 7071),
                data_dir=getattr(args, "data_dir", None),
                config_dir=getattr(args, "config_dir", None),
                env_vars=env_vars,
                config_file=getattr(args, "config_file", None),
                config_values=config_values,
                override_values=override_values,
                pull_image=not getattr(args, "no_pull", False),
            )
            if not success:
                sys.exit(1)
        elif args.command == "stop":
            deployer.stop(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "logs":
            deployer.logs(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "shell":
            deployer.shell(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "cleanup":
            deployer.cleanup(
                template_name=getattr(args, "template", None),
                all_containers=getattr(args, "all", False),
            )
        else:
            console.print(f"[red]❌ Unknown command: {args.command}[/red]")
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
