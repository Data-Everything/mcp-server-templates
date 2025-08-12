"""
Output Formatter - Centralized output formatting utilities.

This module provides utilities for formatting output for CLI display,
consolidating formatting logic that can be shared across different commands.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

logger = logging.getLogger(__name__)


class OutputFormatter:
    """
    Centralized output formatting utilities.

    Provides utilities for consistent formatting across CLI commands.
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize the output formatter."""
        self.console = console or Console()

    def format_templates_table(
        self, templates: Dict[str, Dict], show_deployed: bool = False
    ) -> Table:
        """
        Format templates as a rich table.

        Args:
            templates: Dictionary of template information
            show_deployed: Whether to show deployment status

        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Template", style="cyan", no_wrap=True)
        table.add_column("Version", style="magenta")
        table.add_column("Description", style="white")
        table.add_column("Docker Image", style="yellow")

        if show_deployed:
            table.add_column("Status", style="green")
            table.add_column("Deployments", style="blue")

        for name, info in templates.items():
            row = [
                name,
                info.get("version", "unknown"),
                info.get("description", "No description"),
                info.get("docker_image", "unknown"),
            ]

            if show_deployed:
                deployed = info.get("deployed", False)
                deployment_count = info.get("deployment_count", 0)

                status = "✅ Running" if deployed else "⏹️  Stopped"
                deployments = str(deployment_count) if deployment_count > 0 else "-"

                row.extend([status, deployments])

            table.add_row(*row)

        return table

    def format_tools_table(self, tools: List[Dict]) -> Table:
        """
        Format tools as a rich table.

        Args:
            tools: List of tool definitions

        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Tool Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Parameters", style="yellow")
        table.add_column("Source", style="magenta")

        for tool in tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            source = tool.get("source", "unknown")

            # Format parameters
            parameters = tool.get("parameters", [])
            if parameters:
                param_strs = []
                for param in parameters:
                    param_str = param.get("name", "unknown")
                    if not param.get("required", True):
                        param_str += " (optional)"
                    param_strs.append(param_str)
                param_text = ", ".join(param_strs)
            else:
                param_text = "None"

            table.add_row(name, description, param_text, source)

        return table

    def format_deployment_result(self, result: Dict[str, Any]) -> Panel:
        """
        Format deployment result as a rich panel.

        Args:
            result: Deployment result dictionary

        Returns:
            Rich Panel object
        """
        if result.get("success", False):
            title = "🎉 Deployment Complete"
            content = []

            content.append(
                f"✅ Successfully deployed {result.get('template', 'template')}!"
            )
            content.append("")
            content.append("📋 Details:")

            if result.get("deployment_id"):
                content.append(f"• Deployment: {result['deployment_id']}")
            if result.get("container_id"):
                content.append(f"• Container: {result['container_id']}")
            if result.get("image"):
                content.append(f"• Image: {result['image']}")
            if result.get("status"):
                content.append(f"• Status: {result['status']}")

            if result.get("endpoint"):
                content.append("")
                content.append("🔧 MCP Configuration:")
                content.append(f"• Endpoint: {result['endpoint']}")
                content.append(f"• Transport: {result.get('transport', 'http')}")

            if result.get("mcp_config_path"):
                content.append(f"• Config saved to: {result['mcp_config_path']}")

            content.append("")
            content.append("💡 Management:")
            template = result.get("template", "template")
            content.append(f"• View logs: mcpt logs {template}")
            content.append(f"• Stop: mcpt stop {template}")
            content.append(f"• Shell: mcpt shell {template}")

            panel_content = "\n".join(content)
            style = "green"
        else:
            title = "❌ Deployment Failed"
            error = result.get("error", "Unknown error occurred")
            panel_content = f"Error: {error}"
            style = "red"

        return Panel(panel_content, title=title, border_style=style)

    def format_logs(self, logs: str, colorize: bool = True) -> str:
        """
        Format logs for display with optional colorization.

        Args:
            logs: Raw log content
            colorize: Whether to apply color highlighting

        Returns:
            Formatted log string
        """
        if not logs:
            return "No logs available"

        if not colorize:
            return logs

        # Simple log level colorization
        lines = logs.split("\n")
        formatted_lines = []

        for line in lines:
            if "[ERROR]" in line or "[CRITICAL]" in line:
                formatted_lines.append(f"[red]{line}[/red]")
            elif "[WARNING]" in line or "[WARN]" in line:
                formatted_lines.append(f"[yellow]{line}[/yellow]")
            elif "[INFO]" in line:
                formatted_lines.append(f"[blue]{line}[/blue]")
            elif "[DEBUG]" in line:
                formatted_lines.append(f"[dim]{line}[/dim]")
            else:
                formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def format_stop_result(self, result: Dict[str, Any]) -> str:
        """
        Format stop operation result.

        Args:
            result: Stop operation result

        Returns:
            Formatted message string
        """
        if result.get("success", False):
            stopped = result.get("stopped_deployments", [])
            if len(stopped) == 1:
                return f"✅ Deployment stopped successfully!\n• Stopped: {stopped[0]}\n• Duration: {result.get('duration', 0):.1f} seconds"
            elif len(stopped) > 1:
                stops_list = "\n".join(f"  • {dep}" for dep in stopped)
                return f"✅ {len(stopped)} deployments stopped successfully!\n{stops_list}\n• Duration: {result.get('duration', 0):.1f} seconds"
            else:
                return "ℹ️ No deployments were stopped"
        else:
            error = result.get("error", "Unknown error")
            return f"❌ Failed to stop deployment: {error}"

    def format_config_overview(self, configurations: Dict[str, Any]) -> Table:
        """
        Format configuration overview as a table.

        Args:
            configurations: Dictionary of configuration data

        Returns:
            Rich Table object
        """
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Config File", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="green")
        table.add_column("Size", style="yellow")

        for config_name, config_data in configurations.items():
            config_type = self._guess_config_type(config_name, config_data)
            status = "✅ Valid" if isinstance(config_data, dict) else "❌ Invalid"

            if isinstance(config_data, dict):
                size = f"{len(config_data)} properties"
            elif isinstance(config_data, list):
                size = f"{len(config_data)} items"
            else:
                size = "unknown"

            table.add_row(config_name, config_type, status, size)

        return table

    def format_validation_results(self, validation: Dict[str, Any]) -> Panel:
        """
        Format configuration validation results.

        Args:
            validation: Validation result dictionary

        Returns:
            Rich Panel object
        """
        if validation.get("valid", False):
            title = "✅ Configuration Valid"
            content = "All configurations passed validation."

            warnings = validation.get("warnings", [])
            if warnings:
                content += "\n\n⚠️ Warnings:"
                for warning in warnings:
                    content += f"\n• {warning}"

            style = "green"
        else:
            title = "❌ Configuration Invalid"
            content = "Configuration validation failed."

            errors = validation.get("errors", [])
            if errors:
                content += "\n\nErrors:"
                for error in errors:
                    content += f"\n• {error}"

            warnings = validation.get("warnings", [])
            if warnings:
                content += "\n\nWarnings:"
                for warning in warnings:
                    content += f"\n• {warning}"

            style = "red"

        return Panel(content, title=title, border_style=style)

    def format_json(self, data: Any, indent: int = 2) -> str:
        """
        Format data as pretty JSON.

        Args:
            data: Data to format
            indent: JSON indentation level

        Returns:
            Pretty-formatted JSON string
        """
        try:
            return json.dumps(data, indent=indent, default=str)
        except Exception as e:
            logger.error(f"Failed to format JSON: {e}")
            return str(data)

    def print_panel(self, content: str, title: str = "", style: str = "blue"):
        """
        Print content in a rich panel.

        Args:
            content: Panel content
            title: Panel title
            style: Panel border style
        """
        panel = Panel(content, title=title, border_style=style)
        self.console.print(panel)

    def print_table(self, table: Table):
        """
        Print a rich table.

        Args:
            table: Table to print
        """
        self.console.print(table)

    def print_success(self, message: str):
        """Print a success message."""
        self.console.print(f"[green]✅ {message}[/green]")

    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(f"[red]❌ {message}[/red]")

    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(f"[yellow]⚠️ {message}[/yellow]")

    def print_info(self, message: str):
        """Print an info message."""
        self.console.print(f"[blue]ℹ️ {message}[/blue]")

    def _guess_config_type(self, config_name: str, config_data: Any) -> str:
        """Guess the type of configuration based on name and content."""
        if config_name == "template":
            return "Template"
        elif "server" in config_name.lower():
            return "Server"
        elif "client" in config_name.lower():
            return "Client"
        elif "deploy" in config_name.lower():
            return "Deployment"
        elif config_name.endswith(".env"):
            return "Environment"
        else:
            return "Unknown"
