#!/usr/bin/env python3
"""
Enhanced CLI module for MCP Template deployment.

This module provides CLI functionality using common modules for shared logic.
Simplified implementation that delegates to RefactoredCLI for core functionality.
"""

import datetime
import json
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
logger = logging.getLogger(__name__)


class EnhancedCLI:
    """Enhanced CLI using common modules for shared functionality."""

    def __init__(self):
        """Initialize the enhanced CLI with RefactoredCLI delegation."""
        # Use our core implementation for core functionality
        from mcp_template.core.core_cli import CoreCLI
        self._core_cli = CoreCLI()
        
        # Keep some CLI-specific properties for compatibility
        self.verbose = False
        self.beautifier = None

    def show_config_options(self, template_name: str) -> None:
        """Show configuration options for a template."""
        template_info = self._core_cli.template_manager.get_template_info(template_name)
        if not template_info:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return
            
        # Use formatter to display config options
        config_schema = template_info.get('config_schema', {})
        if hasattr(self._core_cli.formatter, 'format_config_schema'):
            self._core_cli.formatter.format_config_schema(template_name, config_schema)
        else:
            # Fallback display
            console.print(f"[blue]Configuration for {template_name}:[/blue]")
            console.print(json.dumps(config_schema, indent=2))

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
                tools = self._core_cli.tool_manager.list_tools_for_template(template_name)
            elif image_name:
                tools = self._core_cli.tool_manager.discover_tools_from_image(image_name)
            else:
                tools = self._core_cli.tool_manager.list_all_tools()
                
            # Use formatter to display tools
            if tools:
                self._core_cli.formatter.format_tools_table(tools)
            else:
                console.print("[yellow]No tools found[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Error listing tools: {e}[/red]")

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
            from mcp_template.core.deployment_manager import DeploymentOptions
            
            options = DeploymentOptions(
                template_name=template_name,
                transport=transport,
                port=port,
                data_dir=data_dir,
                config_dir=config_dir,
                env_vars=env_vars or {},
                config_file=config_file,
                config_values=config_values or {},
                override_values=override_values or {},
                pull_image=pull_image
            )
            
            result = self._core_cli.deployment_manager.deploy_template(options)
            return result.success
        except Exception as e:
            console.print(f"[red]❌ Error deploying template: {e}[/red]")
            return False

    def discover_tools_from_image(
        self, image_name: str, output_format: str = "table"
    ) -> None:
        """Discover tools from a Docker image."""
        try:
            tools = self._core_cli.tool_manager.discover_tools_from_image(image_name)
            
            if tools:
                self._core_cli.formatter.format_tools_table(tools)
                console.print(f"[green]✅ Found {len(tools)} tools in {image_name}[/green]")
            else:
                console.print(f"[yellow]No tools found in {image_name}[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Error discovering tools: {e}[/red]")

    def setup_docker_network(self) -> bool:
        """Set up Docker network for MCP platform."""
        try:
            return self._core_cli.deployment_manager.setup_infrastructure()
        except Exception as e:
            console.print(f"[red]❌ Error setting up Docker network: {e}[/red]")
            return False

    def show_integration_examples(self, template_name: str) -> None:
        """Show integration examples for a template."""
        try:
            template_info = self._core_cli.template_manager.get_template_info(template_name)
            if not template_info:
                console.print(f"[red]❌ Template '{template_name}' not found[/red]")
                return
                
            # Basic integration examples
            console.print(f"[blue]Integration examples for {template_name}:[/blue]")
            console.print(f"• Connect to running server: mcpt connect {template_name}")
            console.print(f"• List tools: mcpt tools {template_name}")
            console.print(f"• View logs: mcpt logs {template_name}")
        except Exception as e:
            console.print(f"[red]❌ Error showing integration examples: {e}[/red]")

    def run_stdio_tool(self, template_name: str, tool_name: str, arguments: Dict[str, Any]) -> None:
        """Run a tool via stdio transport."""
        try:
            result = self._core_cli.tool_manager.call_tool(template_name, tool_name, arguments)
            if result:
                console.print("[green]✅ Tool executed successfully[/green]")
                console.print(json.dumps(result, indent=2))
            else:
                console.print("[red]❌ Tool execution failed[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error running tool: {e}[/red]")


def add_enhanced_cli_args(subparsers) -> None:
    """Add enhanced CLI arguments to subparsers."""
    # Config command
    config_parser = subparsers.add_parser(
        "config", help="Show configuration options for a template"
    )
    config_parser.add_argument("template", help="Template name")

    # Tools command
    tools_parser = subparsers.add_parser("tools", help="List available tools")
    tools_parser.add_argument("template", nargs="?", help="Template name (optional)")
    tools_parser.add_argument("--image", help="Docker image name")
    tools_parser.add_argument("--static", action="store_true", help="Use static discovery")
    tools_parser.add_argument("--format", default="table", help="Output format")

    # Discover tools command
    discover_parser = subparsers.add_parser(
        "discover-tools", help="Discover tools from Docker image"
    )
    discover_parser.add_argument("image", help="Docker image name")
    discover_parser.add_argument("--format", default="table", help="Output format")

    # Integration examples command
    examples_parser = subparsers.add_parser(
        "examples", help="Show integration examples"
    )
    examples_parser.add_argument("template", help="Template name")

    # Run tool command
    run_tool_parser = subparsers.add_parser("run-tool", help="Run a specific tool")
    run_tool_parser.add_argument("template", help="Template name")
    run_tool_parser.add_argument("tool", help="Tool name")
    run_tool_parser.add_argument("--args", help="Tool arguments as JSON")


def handle_enhanced_cli_commands(args) -> bool:
    """Handle enhanced CLI commands."""
    cli = EnhancedCLI()
    
    if args.command == "config":
        cli.show_config_options(args.template)
        return True
    elif args.command == "tools":
        cli.list_tools(
            template_name=getattr(args, "template", None),
            image_name=getattr(args, "image", None),
            static_discovery=getattr(args, "static", False),
            output_format=getattr(args, "format", "table"),
        )
        return True
    elif args.command == "discover-tools":
        cli.discover_tools_from_image(
            args.image, output_format=getattr(args, "format", "table")
        )
        return True
    elif args.command == "examples":
        cli.show_integration_examples(args.template)
        return True
    elif args.command == "run-tool":
        import json
        arguments = {}
        if hasattr(args, "args") and args.args:
            arguments = json.loads(args.args)
        cli.run_stdio_tool(args.template, args.tool, arguments)
        return True
    
    return False


def get_enhanced_cli() -> EnhancedCLI:
    """Get a shared EnhancedCLI instance."""
    if not hasattr(get_enhanced_cli, '_instance'):
        get_enhanced_cli._instance = EnhancedCLI()
    return get_enhanced_cli._instance
