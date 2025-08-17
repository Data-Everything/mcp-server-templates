"""
Rich-based help formatter for beautiful CLI help output.
"""

import argparse
from typing import Any, Dict, List

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class RichHelpFormatter:
    """Rich-based help formatter for beautiful CLI output."""

    def __init__(self, console: Console = None):
        self.console = console or Console()

    def format_help(self, parser: argparse.ArgumentParser) -> None:
        """Format and display beautiful help using Rich."""

        # Main title
        title = Text("🚀 MCP Template Deployment Tool", style="bold blue")
        subtitle = Text(
            "Deploy MCP server templates with zero configuration", style="italic"
        )

        # Create main panel
        self.console.print("\n")
        self.console.print(Panel.fit(f"{title}\n{subtitle}", border_style="blue"))

        # Commands tree
        self._print_commands_tree(parser)

        # Global options
        self._print_global_options(parser)

        # Examples section
        self._print_examples()

        self.console.print("\n")

    def _print_commands_tree(self, parser: argparse.ArgumentParser) -> None:
        """Print commands in a beautiful tree structure."""

        tree = Tree("📋 [bold cyan]Available Commands[/bold cyan]")

        # Extract subparsers
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        if not subparsers_actions:
            return

        subparsers = subparsers_actions[0]

        # Commands with descriptions
        commands_info = {
            "list": "List available templates",
            "deploy": "Deploy a template",
            "create": "Create a new template",
            "stop": "Stop deployments or cleanup stopped containers",
            "config": "Show configuration options for a template",
            "tools": "List available tools [Deprecated - Use mcpt interactive shell instead]",
            "discover-tools": "Discover tools from Docker image [Deprecated - Use mcpt interactive shell instead]",
            "examples": "Show integration examples",
            "run-tool": "Run a specific tool [Deprecated - Use mcpt interactive shell instead]",
            "interactive": "Start interactive CLI",
        }

        categories = {
            "🏗️  Template Management": ["list", "deploy", "create"],
            "🔧 Server Operations": ["stop", "logs", "shell"],
            "⚙️  Configuration & Tools": [
                "config",
                "tools",
                "discover-tools",
                "examples",
                "run-tool",
            ],
            "🎯 Interactive": ["interactive"],
        }

        for category, command_names in categories.items():
            category_branch = tree.add(f"[bold yellow]{category}[/bold yellow]")

            for command_name in command_names:
                if command_name in subparsers.choices and command_name in commands_info:
                    help_text = commands_info[command_name]

                    # Add deprecation warning for deprecated commands
                    if "Deprecated" in help_text:
                        command_branch = category_branch.add(
                            f"[dim]{command_name}[/dim] - [yellow]{help_text}[/yellow]"
                        )
                    else:
                        command_branch = category_branch.add(
                            f"[green]{command_name}[/green] - {help_text}"
                        )

        self.console.print(tree)
        self.console.print()

    def _print_global_options(self, parser: argparse.ArgumentParser) -> None:
        """Print global options in a table."""

        table = Table(title="🔧 Global Options", border_style="cyan")
        table.add_column("Option", style="green", min_width=15)
        table.add_column("Description", style="white")

        for action in parser._actions:
            if action.option_strings and not isinstance(
                action, argparse._SubParsersAction
            ):
                option_str = ", ".join(action.option_strings)
                help_text = action.help or ""
                table.add_row(option_str, help_text)

        self.console.print(table)
        self.console.print()

    def _print_examples(self) -> None:
        """Print usage examples in panels."""

        examples = [
            (
                "📚 Basic Usage",
                [
                    "mcpt list                     # List available templates",
                    "mcpt deploy demo              # Deploy demo template",
                    "mcpt logs demo                # View logs",
                    "mcpt stop demo                # Stop deployment",
                ],
            ),
            (
                "🎯 Interactive Mode",
                [
                    "mcpt interactive                                  # Start interactive CLI",
                    "mcpt> tools demo                                  # Deploy in interactive mode",
                    'mcpt> call demo say_hello \'{"name": "MCP"}\'   # Deploy with custom name',
                ],
            ),
            (
                "⚙️  Advanced Configuration",
                [
                    "mcpt deploy demo --config-file config.json",
                    "mcpt deploy demo --env KEY=VALUE --port 8080",
                    "mcpt shell demo --name my-server",
                ],
            ),
        ]

        panels = []
        for title, commands in examples:
            content = "\n".join(f"[cyan]${command}[/cyan]" for command in commands)
            panel = Panel(content, title=title, border_style="green", padding=(1, 2))
            panels.append(panel)

        self.console.print(
            Panel.fit(
                Columns(panels, equal=True, expand=True),
                title="💡 Examples",
                border_style="blue",
            )
        )


def show_beautiful_help(parser: argparse.ArgumentParser) -> None:
    """Show beautiful help using Rich."""
    formatter = RichHelpFormatter()
    formatter.format_help(parser)


def create_rich_argument_parser() -> argparse.ArgumentParser:
    """Create an ArgumentParser that uses Rich for help formatting."""

    class RichArgumentParser(argparse.ArgumentParser):
        def print_help(self, file=None):
            """Override to use Rich help instead of default."""
            show_beautiful_help(self)

        def format_help(self):
            """Override to prevent default help formatting."""
            return ""  # Rich handles the formatting

    return RichArgumentParser
