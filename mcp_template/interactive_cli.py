"""
Interactive CLI module for MCP Template management.

This module provides an interactive command-line interface for managing MCP servers,
tools, and configurations with persistent session state and beautified responses.
"""

import argparse
import json
import logging
import os
import shlex
import sys
import traceback
from typing import Any, Dict, List, Union

import cmd2
from cmd2 import with_argparser
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from mcp_template.core import (
    TemplateManager,
    DeploymentManager,
    ToolManager,
    OutputFormatter,
)
from mcp_template.tools.cache import CacheManager
from mcp_template.core.tool_caller import ToolCaller
from mcp_template.utils.config_processor import ConfigProcessor

console = Console()
logger = logging.getLogger(__name__)

# Argparse parser for `call` command flags: --config-file, --env, --config
call_parser = argparse.ArgumentParser(prog="call", exit_on_error=False)
call_parser.add_argument(
    "-c", "--config-file", dest="config_file", help="Path to JSON config file"
)
call_parser.add_argument(
    "-e", "--env", dest="env", action="append", help="Environment var KEY=VALUE"
)
call_parser.add_argument(
    "-C",
    "--config",
    dest="config",
    action="append",
    help="Temporary config KEY=VALUE pairs",
)
call_parser.add_argument(
    "-NP",
    "--no-pull",
    dest="no_pull",
    action="store_true",
    help="Do not pull the Docker image",
)
call_parser.add_argument(
    "-R",
    "--raw",
    dest="raw",
    action="store_true",
    help="Show raw JSON response instead of formatted table",
)
call_parser.add_argument("template_name", help="Template name to call")
call_parser.add_argument("tool_name", help="Tool name to execute")
call_parser.add_argument(
    "json_args", nargs="*", default=[], help="JSON string arguments (use quotes for JSON with spaces)"
)


def merge_config_sources(
    session_config: Dict[str, Any],
    config_file: str = None,
    env_vars: List[str] = None,
    inline_config: List[str] = None,
    template: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Utility to merge configuration from multiple sources using ConfigProcessor.

    This is a wrapper around ConfigProcessor.prepare_configuration to maintain
    backward compatibility with the interactive CLI interface.

    Priority order (highest to lowest):
    1. Inline config (--config)
    2. Environment variables (--env)
    3. Config file (--config-file)
    4. Session config

    Args:
        session_config: Base configuration from interactive session
        config_file: Path to JSON config file
        env_vars: List of KEY=VALUE environment variable pairs
        inline_config: List of KEY=VALUE inline config pairs
        template: Template configuration for proper type conversion

    Returns:
        Merged configuration dictionary
    """
    # For backward compatibility with existing tests, we need to handle the case
    # where no template is provided (older API)
    if template is None:
        # Fall back to simple merging for backward compatibility
        config_values = session_config.copy()

        # Load config file if provided (lower priority)
        if config_file:
            try:
                with open(config_file, "r") as f:
                    file_cfg = json.load(f)
                    config_values.update(file_cfg)
                    console.print(f"[dim]✓ Loaded config from {config_file}[/dim]")
            except Exception as e:
                console.print(f"[red]❌ Failed to load config file: {e}[/red]")
                raise

        # Apply environment overrides (medium priority)
        if env_vars:
            for pair in env_vars:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    config_values[k] = v
                    console.print(f"[dim]✓ Set env var: {k}=***[/dim]")

        # Apply inline config overrides (highest priority)
        if inline_config:
            for pair in inline_config:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    config_values[k] = v
                    console.print(f"[dim]✓ Set inline config: {k}=***[/dim]")

        return config_values

    # Use the unified config processor when template is provided
    config_processor = ConfigProcessor()

    try:
        # Convert list inputs to dict format for the config processor
        config_values = {}
        env_dict = {}

        # Process inline config into dict (highest priority)
        if inline_config:
            for pair in inline_config:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    config_values[k] = v
                    console.print(f"[dim]✓ Set inline config: {k}=***[/dim]")

        # Process env vars into dict (medium priority)
        if env_vars:
            for pair in env_vars:
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    env_dict[k] = v
                    console.print(f"[dim]✓ Set env var: {k}=***[/dim]")

        return config_processor.prepare_configuration(
            template=template,
            session_config=session_config,
            config_file=config_file,
            config_values=config_values,
            env_vars=env_dict,
        )
    except Exception as e:
        console.print(f"[red]❌ Failed to merge config sources: {e}[/red]")
        raise


class ResponseBeautifier:
    """Class for beautifying and formatting MCP responses."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the response beautifier.

        Args:
            verbose: Whether to enable verbose output for debugging
        """
        self.console = Console()
        self.verbose = verbose

    def _is_actual_error(self, stderr_text: str) -> bool:
        """Check if stderr contains actual errors vs informational messages."""
        if not stderr_text:
            return False

        stderr_lower = stderr_text.lower().strip()

        # These are actual error indicators
        error_indicators = [
            "error:",
            "exception:",
            "traceback",
            "failed:",
            "fatal:",
            "cannot",
            "unable to",
            "permission denied",
            "not found",
            "invalid",
            "syntax error",
            "connection refused",
            "timeout",
        ]

        # These are informational messages that should not be treated as errors
        info_indicators = [
            "running on stdio",
            "server started",
            "listening on",
            "connected to",
            "initialized",
            "ready",
            "starting",
            "loading",
            "loaded",
            "using",
            "found",
        ]

        # Check for actual errors first
        for indicator in error_indicators:
            if indicator in stderr_lower:
                return True

        # If it contains info indicators, it's likely not an error
        for indicator in info_indicators:
            if indicator in stderr_lower:
                return False

        # If stderr is very short and doesn't contain error words, likely not an error
        if len(stderr_text.strip()) < 100 and not any(
            word in stderr_lower for word in ["error", "fail", "exception"]
        ):
            return False

        # Default to showing it if we're unsure
        return True

    def _analyze_data_types(self, data: Any) -> Dict[str, Any]:
        """Analyze data structure and return metadata about its composition."""
        analysis = {
            "primary_type": type(data).__name__,
            "is_homogeneous": True,
            "element_types": {},
            "structure_hints": [],
            "complexity": "simple",
            "best_display": "raw",
        }

        if isinstance(data, dict):
            analysis["size"] = len(data)
            analysis["element_types"] = {k: type(v).__name__ for k, v in data.items()}

            # Analyze value types for homogeneity
            value_types = set(type(v).__name__ for v in data.values())
            analysis["is_homogeneous"] = len(value_types) == 1
            analysis["value_types"] = list(value_types)

            # Determine complexity and structure hints
            if len(data) <= 6 and all(
                isinstance(v, (str, int, float, bool, type(None)))
                for v in data.values()
            ):
                analysis["complexity"] = "simple"
                analysis["best_display"] = "key_value"
                analysis["structure_hints"].append("simple_mapping")
            elif self._is_tabular_dict(data):
                analysis["complexity"] = "tabular"
                analysis["best_display"] = "table"
                analysis["structure_hints"].append("column_oriented")
            elif any(isinstance(v, (list, dict)) for v in data.values()):
                analysis["complexity"] = "nested"
                analysis["best_display"] = "tree" if len(data) <= 10 else "json"
                analysis["structure_hints"].append("hierarchical")
            else:
                analysis["complexity"] = "medium"
                analysis["best_display"] = "key_value" if len(data) <= 15 else "json"

        elif isinstance(data, list):
            analysis["size"] = len(data)
            if data:
                element_types = [type(item).__name__ for item in data]
                analysis["element_types"] = dict(
                    zip(range(len(element_types)), element_types)
                )
                analysis["is_homogeneous"] = len(set(element_types)) == 1
                analysis["item_type"] = (
                    element_types[0] if analysis["is_homogeneous"] else "mixed"
                )

                if analysis["is_homogeneous"]:
                    if isinstance(data[0], dict) and self._has_consistent_keys(data):
                        analysis["complexity"] = "tabular"
                        analysis["best_display"] = "table"
                        analysis["structure_hints"].append("record_list")
                    elif isinstance(data[0], (str, int, float)):
                        analysis["complexity"] = "simple"
                        analysis["best_display"] = "list"
                        analysis["structure_hints"].append("value_list")
                    else:
                        analysis["complexity"] = "nested"
                        analysis["best_display"] = "json"
                        analysis["structure_hints"].append("complex_list")
                else:
                    analysis["complexity"] = "heterogeneous"
                    analysis["best_display"] = "json"
                    analysis["structure_hints"].append("mixed_types")
            else:
                analysis["best_display"] = "empty"

        elif isinstance(data, str):
            try:
                parsed = json.loads(data)
                nested_analysis = self._analyze_data_types(parsed)
                analysis.update(nested_analysis)
                analysis["structure_hints"].append("json_string")
            except json.JSONDecodeError:
                analysis["best_display"] = "text"
                analysis["structure_hints"].append("plain_text")
        else:
            analysis["best_display"] = "simple"

        return analysis

    def _detect_data_structure(self, data: Any) -> str:
        """Detect the type of data structure to apply appropriate formatting."""
        analysis = self._analyze_data_types(data)
        return analysis["best_display"]

    def _is_tabular_dict(self, data: dict) -> bool:
        """Check if dictionary contains tabular data."""
        # Look for patterns like {key1: [values], key2: [values]}
        if len(data) >= 2:
            values = list(data.values())
            if all(isinstance(v, list) and len(v) > 0 for v in values):
                # Check if all lists have same length
                lengths = [len(v) for v in values]
                return len(set(lengths)) == 1
        return False

    def _has_consistent_keys(self, data: List[dict]) -> bool:
        """Check if list of dicts has consistent keys for table display."""
        if not data or not isinstance(data[0], dict):
            return False

        first_keys = set(data[0].keys())
        return all(
            set(item.keys()) == first_keys for item in data[:5]
        )  # Check first 5 items

    def _create_key_value_table(self, data: dict, title: str = "Data") -> Table:
        """Create a key-value table for simple dictionaries with intelligent formatting."""
        analysis = self._analyze_data_types(data)

        table = Table(
            title=f"{title} ({len(data)} properties)",
            show_header=True,
            header_style="cyan",
        )
        table.add_column("Property", style="cyan", width=25)
        table.add_column("Value", style="white", width=55)
        table.add_column("Type", style="yellow", width=10)

        for key, value in data.items():
            value_type = type(value).__name__

            # Format value based on type with intelligent truncation
            if isinstance(value, (dict, list)):
                if isinstance(value, dict):
                    size_info = (
                        f" ({len(value)} keys)" if len(value) > 0 else " (empty)"
                    )
                    preview = (
                        "{"
                        + ", ".join(f"{k}: ..." for k in list(value.keys())[:3])
                        + "}"
                    )
                    if len(value) > 3:
                        preview += "..."
                    preview += size_info
                else:  # list
                    size_info = (
                        f" ({len(value)} items)" if len(value) > 0 else " (empty)"
                    )
                    if len(value) > 0:
                        preview = (
                            "["
                            + ", ".join(
                                str(item)[:10] + ("..." if len(str(item)) > 10 else "")
                                for item in value[:3]
                            )
                            + "]"
                        )
                        if len(value) > 3:
                            preview += "..."
                    else:
                        preview = "[]"
                    preview += size_info
                value_str = preview
            elif isinstance(value, bool):
                value_str = "[green]✓[/green]" if value else "[red]✗[/red]"
            elif isinstance(value, str):
                if len(value) > 50:
                    value_str = value[:47] + "..."
                elif value.startswith(("http://", "https://")):
                    value_str = f"[link]{value}[/link]"
                elif value.lower() in ["true", "false"]:
                    value_str = f"[cyan]{value}[/cyan]"
                else:
                    value_str = value
            elif isinstance(value, (int, float)):
                if isinstance(value, float):
                    value_str = f"{value:.3f}" if abs(value) < 1000 else f"{value:.2e}"
                else:
                    value_str = f"{value:,}" if abs(value) > 1000 else str(value)
            elif value is None:
                value_str = "[dim]null[/dim]"
            else:
                value_str = str(value)

            table.add_row(str(key), value_str, value_type)

        return table

    def _create_data_table(
        self, data: Union[List[dict], dict], title: str = "Data"
    ) -> Table:
        """Create a dynamic table from list of dictionaries or tabular dict with intelligent column formatting."""
        if isinstance(data, dict) and self._is_tabular_dict(data):
            # Convert tabular dict to list of dicts
            keys = list(data.keys())
            values = list(data.values())
            rows = []
            for i in range(len(values[0])):
                row = {key: values[j][i] for j, key in enumerate(keys)}
                rows.append(row)
            data = rows

        if not isinstance(data, list) or not data:
            return None

        # Get column headers from first item
        first_item = data[0]
        if not isinstance(first_item, dict):
            return None

        headers = list(first_item.keys())

        # Analyze column types and content for intelligent formatting
        column_analysis = {}
        for header in headers:
            values = [item.get(header) for item in data[:10]]  # Sample first 10 rows
            non_null_values = [v for v in values if v is not None]

            if not non_null_values:
                column_analysis[header] = {"type": "null", "width": 10, "style": "dim"}
                continue

            # Determine predominant type
            types = [type(v).__name__ for v in non_null_values]
            most_common_type = max(set(types), key=types.count)

            # Analyze content for formatting hints
            analysis = {
                "type": most_common_type,
                "max_length": max(len(str(v)) for v in non_null_values),
                "has_urls": any(
                    isinstance(v, str) and v.startswith(("http://", "https://"))
                    for v in non_null_values
                ),
                "is_boolean_like": all(
                    isinstance(v, bool)
                    or (
                        isinstance(v, str)
                        and v.lower() in ["true", "false", "yes", "no"]
                    )
                    for v in non_null_values
                ),
                "is_numeric": most_common_type in ["int", "float"],
                "is_id_like": header.lower() in ["id", "name", "title", "key"]
                or header.lower().endswith("_id"),
            }

            # Determine display properties
            if analysis["is_id_like"]:
                analysis["style"] = "cyan"
                analysis["width"] = min(20, max(10, analysis["max_length"] + 2))
            elif analysis["is_boolean_like"]:
                analysis["style"] = "green"
                analysis["width"] = 8
            elif analysis["is_numeric"]:
                analysis["style"] = "yellow"
                analysis["width"] = min(15, max(8, analysis["max_length"] + 2))
            elif analysis["has_urls"]:
                analysis["style"] = "blue"
                analysis["width"] = 30
            elif header.lower() in ["description", "content", "message", "text"]:
                analysis["style"] = "white"
                analysis["width"] = 40
            else:
                analysis["style"] = "white"
                analysis["width"] = min(25, max(12, analysis["max_length"] + 2))

            column_analysis[header] = analysis

        # Create table with intelligent column formatting
        table = Table(
            title=f"{title} ({len(data)} rows)", show_header=True, header_style="cyan"
        )

        for header in headers:
            col_info = column_analysis[header]
            table.add_column(
                str(header).title(),
                style=col_info["style"],
                width=col_info["width"],
                overflow="ellipsis",
            )

        # Add rows with intelligent value formatting
        max_rows = 25  # Increased slightly for better data display
        for i, item in enumerate(data[:max_rows]):
            if not isinstance(item, dict):
                continue

            row = []
            for header in headers:
                value = item.get(header, "")
                col_info = column_analysis[header]

                # Format different data types intelligently
                if value is None:
                    formatted = "[dim]null[/dim]"
                elif isinstance(value, bool):
                    formatted = "[green]✓[/green]" if value else "[red]✗[/red]"
                elif col_info["is_boolean_like"] and isinstance(value, str):
                    if value.lower() in ["true", "yes", "1"]:
                        formatted = "[green]✓[/green]"
                    elif value.lower() in ["false", "no", "0"]:
                        formatted = "[red]✗[/red]"
                    else:
                        formatted = value
                elif isinstance(value, (int, float)):
                    if isinstance(value, float):
                        formatted = (
                            f"{value:.3f}" if abs(value) < 1000 else f"{value:.2e}"
                        )
                    else:
                        formatted = f"{value:,}" if abs(value) > 1000 else str(value)
                elif isinstance(value, str):
                    if col_info["has_urls"]:
                        formatted = (
                            f"[link]{value}[/link]"
                            if len(value) < 35
                            else f"[link]{value[:32]}...[/link]"
                        )
                    elif len(value) > col_info["width"] - 3:
                        formatted = value[: col_info["width"] - 6] + "..."
                    else:
                        formatted = value
                elif isinstance(value, (dict, list)):
                    if isinstance(value, list):
                        formatted = f"[{len(value)} items]"
                    else:
                        formatted = f"{{{len(value)} keys}}"
                else:
                    formatted = (
                        str(value)
                        if len(str(value)) < col_info["width"]
                        else str(value)[: col_info["width"] - 3] + "..."
                    )

                row.append(formatted)

            table.add_row(*row)

        # Add info if truncated
        if len(data) > max_rows:
            table.caption = f"Showing {max_rows} of {len(data)} rows"

        return table

    def _create_list_display(
        self, data: list, title: str = "Items"
    ) -> Union[Table, Panel]:
        """Create display for simple lists."""
        if len(data) <= 10 and all(
            isinstance(item, (str, int, float)) for item in data
        ):
            # Small list of simple values - use columns
            items = [str(item) for item in data]
            return Columns(items, equal=True, expand=True, title=title)
        else:
            # Larger or complex list - use panel
            content = "\n".join(f"• {item}" for item in data[:20])
            if len(data) > 20:
                content += f"\n... and {len(data) - 20} more items"
            return Panel(
                content, title=f"{title} ({len(data)} items)", border_style="blue"
            )

    def beautify_json(self, data: Any, title: str = "Response") -> None:
        """Display JSON data in a beautified format with intelligent formatting."""
        # Analyze data structure for intelligent display
        analysis = self._analyze_data_types(data)
        structure_type = analysis["best_display"]

        # Check for special cases first (before generic structure-based routing)
        if (
            isinstance(data, dict)
            and "tools" in data
            and isinstance(data["tools"], list)
        ):
            # Special case: handle tools lists (MCP-specific but common pattern)
            tools = data["tools"]
            if tools and isinstance(tools[0], dict) and "name" in tools[0]:
                self.beautify_tools_list(tools, "MCP Server Tools")
                return
            # Tools is just names or other simple data - fall through to generic display

        # Route to appropriate display method based on analysis
        if structure_type == "key_value" and isinstance(data, dict):
            table = self._create_key_value_table(data, title)
            self.console.print(table)

        elif structure_type == "table":
            table = self._create_data_table(data, title)
            if table:
                self.console.print(table)
            else:
                # Fallback to JSON
                self._display_json_syntax(data, title)

        elif structure_type == "list" and isinstance(data, list):
            display = self._create_list_display(data, title)
            self.console.print(display)

        elif structure_type == "tree" and isinstance(data, dict):
            # Use tree display for hierarchical data
            self._display_tree_structure(data, title)

        elif structure_type == "empty":
            self.console.print(f"[dim]{title}: Empty collection[/dim]")

        elif structure_type == "text":
            self.console.print(Panel(str(data), title=title, border_style="blue"))

        else:
            # Default to syntax-highlighted JSON with analysis hints
            self._display_json_syntax(data, title, analysis)

    def _display_tree_structure(self, data: dict, title: str = "Data") -> None:
        """Display hierarchical data as a tree structure."""
        tree = Tree(f"[bold cyan]{title}[/bold cyan]")

        def add_to_tree(node, key, value, max_depth=3, current_depth=0):
            if current_depth >= max_depth:
                node.add(f"[dim]{key}: ... (truncated)[/dim]")
                return

            if isinstance(value, dict):
                if len(value) > 10:  # Large dicts get summary
                    branch = node.add(f"[yellow]{key}[/yellow] ({len(value)} items)")
                    # Show first few items
                    for i, (k, v) in enumerate(list(value.items())[:3]):
                        add_to_tree(branch, k, v, max_depth, current_depth + 1)
                    if len(value) > 3:
                        branch.add("[dim]... more items[/dim]")
                else:
                    branch = node.add(f"[yellow]{key}[/yellow]")
                    for k, v in value.items():
                        add_to_tree(branch, k, v, max_depth, current_depth + 1)
            elif isinstance(value, list):
                if len(value) > 5:  # Large lists get summary
                    branch = node.add(f"[magenta]{key}[/magenta] [{len(value)} items]")
                    for i, item in enumerate(value[:3]):
                        add_to_tree(
                            branch, f"[{i}]", item, max_depth, current_depth + 1
                        )
                    if len(value) > 3:
                        branch.add("[dim]... more items[/dim]")
                else:
                    branch = node.add(f"[magenta]{key}[/magenta]")
                    for i, item in enumerate(value):
                        add_to_tree(
                            branch, f"[{i}]", item, max_depth, current_depth + 1
                        )
            else:
                # Format leaf values
                if isinstance(value, bool):
                    display_value = "✓" if value else "✗"
                elif isinstance(value, str) and len(value) > 50:
                    display_value = f"{value[:47]}..."
                else:
                    display_value = str(value)

                node.add(f"[white]{key}[/white]: [green]{display_value}[/green]")

        for key, value in data.items():
            add_to_tree(tree, key, value)

        self.console.print(tree)

    def _display_json_syntax(
        self, data: Any, title: str, analysis: Dict[str, Any] = None
    ) -> None:
        """Display data as syntax-highlighted JSON with optional analysis hints."""
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                # If it's not valid JSON, display as text
                self.console.print(Panel(data, title=title, border_style="blue"))
                return

        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)

        # Add analysis hints as caption if provided
        caption = None
        if analysis:
            hints = []
            if analysis.get("complexity"):
                hints.append(f"Complexity: {analysis['complexity']}")
            if analysis.get("size"):
                hints.append(f"Size: {analysis['size']} items")
            if analysis.get("structure_hints"):
                hints.append(f"Structure: {', '.join(analysis['structure_hints'])}")
            if hints:
                caption = " | ".join(hints)

        panel = Panel(syntax, title=title, border_style="green")
        if caption:
            panel.subtitle = f"[dim]{caption}[/dim]"

        self.console.print(panel)

    def beautify_tool_response(self, response: Dict[str, Any]) -> None:
        """Beautify tool execution response with enhanced formatting."""
        if response.get("status") == "completed":
            stdout = response.get("stdout", "")
            stderr = response.get("stderr", "")

            # Try to parse stdout as JSON-RPC response
            try:
                lines = stdout.strip().split("\n")
                json_responses = []

                for line in lines:
                    line = line.strip()
                    if (
                        line.startswith('{"jsonrpc"')
                        or line.startswith('{"result"')
                        or line.startswith('{"error"')
                    ):
                        try:
                            json_response = json.loads(line)
                            json_responses.append(json_response)
                        except json.JSONDecodeError:
                            continue

                # Find tool response
                tool_response = None
                for resp in json_responses:
                    if resp.get("id") == 3:  # Tool call response
                        tool_response = resp
                        break

                if not tool_response and json_responses:
                    tool_response = json_responses[-1]

                if tool_response:
                    if "result" in tool_response:
                        result_data = tool_response["result"]

                        # Handle MCP content format - prioritize structuredContent
                        if (
                            isinstance(result_data, dict)
                            and "structuredContent" in result_data
                        ):
                            # Use structuredContent when available (already parsed JSON)
                            structured_data = result_data["structuredContent"]
                            self.beautify_json(structured_data, "Tool Result")

                        elif isinstance(result_data, dict) and "content" in result_data:
                            content_items = result_data["content"]
                            if isinstance(content_items, list) and content_items:
                                for i, content in enumerate(content_items):
                                    if isinstance(content, dict) and "text" in content:
                                        # Try to beautify the text content if it's structured data
                                        text_content = content["text"]
                                        try:
                                            # Try to parse as JSON for better formatting
                                            parsed_content = json.loads(text_content)
                                            self.beautify_json(
                                                parsed_content, f"Tool Result {i+1}"
                                            )
                                        except json.JSONDecodeError:
                                            # Display as text if not JSON
                                            self.console.print(
                                                Panel(
                                                    text_content,
                                                    title=f"Tool Result {i+1}",
                                                    border_style="green",
                                                )
                                            )
                                    else:
                                        self.beautify_json(content, f"Content {i+1}")
                            else:
                                self.beautify_json(result_data, "Tool Result")
                        else:
                            self.beautify_json(result_data, "Tool Result")

                    elif "error" in tool_response:
                        error_info = tool_response["error"]
                        self.console.print(
                            Panel(
                                f"Error {error_info.get('code', 'unknown')}: {error_info.get('message', 'Unknown error')}",
                                title="Tool Error",
                                border_style="red",
                            )
                        )
                    else:
                        self.beautify_json(tool_response, "MCP Response")
                else:
                    # No JSON response found, show raw output
                    self.console.print(
                        Panel(stdout, title="Raw Output", border_style="blue")
                    )

            except Exception as e:
                # Debug the exception and fallback to raw output

                self.console.print(f"[yellow]⚠️  Beautifier parsing error: {e}[/yellow]")
                self.console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")
                # Fallback to raw output
                self.console.print(
                    Panel(stdout, title="Tool Output", border_style="blue")
                )

            # Show stderr if present and contains actual errors
            if stderr and self._is_actual_error(stderr):
                self.console.print(
                    Panel(stderr, title="Standard Error", border_style="yellow")
                )
            elif stderr and not self._is_actual_error(stderr):
                # Show non-error stderr as debug info only if verbose
                if hasattr(self, "verbose") and self.verbose:
                    self.console.print(
                        Panel(stderr, title="Debug Info", border_style="dim")
                    )

        else:
            # Failed execution
            error_msg = response.get("error", "Unknown error")
            stderr = response.get("stderr", "")

            self.console.print(
                Panel(
                    f"Execution failed: {error_msg}",
                    title="Execution Error",
                    border_style="red",
                )
            )

            if stderr:
                self.console.print(
                    Panel(stderr, title="Error Details", border_style="red")
                )

    def beautify_tools_list(
        self, tools: List[Dict[str, Any]], source: str = "Template"
    ) -> None:
        """Beautify tools list display."""
        if not tools:
            self.console.print("[yellow]⚠️  No tools found[/yellow]")
            return

        # Create tools table
        table = Table(title=f"Available Tools ({len(tools)} found)")
        table.add_column("Tool Name", style="cyan", width=20)
        table.add_column("Description", style="white", width=50)
        table.add_column("Parameters", style="yellow", width=50)
        table.add_column("Category", style="green", width=15)

        for tool in tools:
            name = tool.get("name", "Unknown")
            description = tool.get("description", "No description")

            # Handle parameters
            parameters = tool.get("parameters", {})
            input_schema = tool.get("inputSchema", {})

            # Check both formats - MCP tools/call format and discovery format
            if isinstance(parameters, dict) and "properties" in parameters:
                properties = parameters.get("properties", {})
                param_count = len(properties)
                param_text = f"{param_count} params"
                param_names = ", ".join(properties.keys())
            elif isinstance(input_schema, dict) and "properties" in input_schema:
                properties = input_schema.get("properties", {})
                param_count = len(properties)
                param_text = f"{param_count} params"
                param_names = ", ".join(properties.keys())
            elif isinstance(parameters, list):
                param_count = len(parameters)
                param_text = f"{param_count} params"
                param_names = ", ".join([p.get("name", "Unknown") for p in parameters])
            elif parameters or input_schema:
                param_text = "Schema defined"
                param_names = ""
            else:
                param_text = "0 params"
                param_names = ""

            category = tool.get("category", "general")

            table.add_row(
                name,
                description,
                param_text + " (" + param_names + ")" if param_names else "",
                category,
            )

        self.console.print(table)
        self.console.print(f"[dim]Source: {source}[/dim]")

    def beautify_deployed_servers(self, servers: List[Dict[str, Any]]) -> None:
        """Beautify deployed servers list."""
        if not servers:
            self.console.print("[yellow]⚠️  No deployed servers found[/yellow]")
            return

        table = Table(title=f"Deployed MCP Servers ({len(servers)} active)")
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Transport", style="yellow", width=12)
        table.add_column("Status", style="green", width=10)
        table.add_column("Endpoint", style="blue", width=30)
        table.add_column("Ports", style="blue", width=20)
        table.add_column("Since", style="blue", width=25)
        table.add_column("Tools", style="magenta", width=10)

        for server in servers:
            id = server.get("id", "N/A")
            template_name = server.get("name", "Unknown")
            transport = server.get("transport", "unknown")
            status = server.get("status", "unknown")
            endpoint = server.get("endpoint", "N/A")
            ports = server.get("ports", "N/A")
            since = server.get("since", "N/A")
            tool_count = len(server.get("tools", []))

            # Color status
            if status == "running":
                status_text = f"[green]{status}[/green]"
            elif status == "failed":
                status_text = f"[red]{status}[/red]"
            else:
                status_text = f"[yellow]{status}[/yellow]"

            table.add_row(
                id,
                template_name,
                transport,
                status_text,
                endpoint,
                ports,
                since,
                str(tool_count),
            )

        self.console.print(table)


class InteractiveCLI(cmd2.Cmd):
    """Interactive command-line interface for MCP Template management."""

    intro = None  # Set to None to prevent automatic intro display

    prompt = "mcpt> "

    def __init__(self):
        super().__init__()
        # Use core modules for all business logic
        self.template_manager = TemplateManager()
        self.deployment_manager = DeploymentManager()
        self.tool_manager = ToolManager()
        self.formatter = OutputFormatter()

        # Keep utility components
        self.cache = CacheManager()
        self.beautifier = ResponseBeautifier()
        self.tool_caller = ToolCaller(backend_type="docker", caller_type="cli")

        # Session state
        self.session_configs = {}  # Template name -> config
        self.deployed_servers = []  # List of deployed servers info

    def cmdloop(self, intro=None):
        """Override cmdloop to handle KeyboardInterrupt gracefully and show help."""
        try:
            # Show intro and help automatically on start
            if intro is None:
                # Custom intro display
                intro_text = """
╔══════════════════════════════════════════════════════════════╗
║                    MCP Interactive CLI                       ║
╠══════════════════════════════════════════════════════════════╣
║  Welcome to the MCP Template Interactive CLI!               ║
║  Type 'help' for available commands or 'quit' to exit.      ║
╚══════════════════════════════════════════════════════════════╝
"""
                console.print(intro_text)
                # Show help directly instead of calling do_help to avoid empty command issue
                console.print(
                    Panel(
                        """
[cyan]Available Commands:[/cyan]

[yellow]Server Management:[/yellow]
  • list_servers          - List all deployed MCP servers
  • templates             - List all available templates

[yellow]Tool Operations:[/yellow]
  • tools <template>      - List available tools for a template
  • call <template> <tool> [args] - Call a tool (stdio or HTTP)
    [dim]Options: --config-file, --env KEY=VALUE, --config KEY=VALUE[/dim]

[yellow]Configuration (Multiple Ways):[/yellow]
  • config <template> key=value   - Set configuration interactively
  • show_config <template>        - Show current template configuration
  • clear_config <template>       - Clear template configuration

[yellow]General:[/yellow]
  • help [command]        - Show this help or help for specific command
  • quit / exit           - Exit the interactive CLI

[green]Examples:[/green]
  • templates
  • config github github_token=your_token_here
  • tools github
  • call github search_repositories {"query": "python"}
  • call --config-file config.json demo say_hello
  • call --env API_KEY=xyz --config timeout=30 github search_repositories '{"query": "python"}'
  • call demo say_hello (no config needed)
  [dim]For stdio templates: config is prompted if missing mandatory properties[/dim]
  [dim]For HTTP templates: server deployment is prompted if not running[/dim]
""",
                        title="MCP Interactive CLI Help",
                        border_style="blue",
                    )
                )
            # Don't pass any intro to super() to prevent duplicate display
            super().cmdloop(None)
        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            return

    def do_list_servers(self, arg):
        """List all deployed MCP servers.
        Usage: list_servers
        """
        console.print("\n[cyan]🔍 Discovering deployed MCP servers...[/cyan]")

        # Get deployed servers from deployer
        try:
            all_servers = self.deployment_manager.list_deployments()
            # Filter to only show running servers
            active_servers = [s for s in all_servers if s.get("status") == "running"]
            self.deployed_servers = active_servers
            self.beautifier.beautify_deployed_servers(active_servers)
        except Exception as e:
            console.print(f"[red]❌ Failed to list servers: {e}[/red]")

    def do_tools(self, args):
        """List available tools for a template.
        Usage: tools <template_name> [--force-server] [--help]

        Options:
            --force-server    Force server discovery (MCP probe only, no static fallback)
            --help           Show detailed help for the template and its tools
        """
        if not args.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            console.print("Usage: tools <template_name> [--force-server] [--help]")
            return

        # Parse arguments
        parts = args.strip().split()
        template_name = parts[0]
        force_server_discovery = "--force-server" in parts
        show_help = "--help" in parts

        # Handle help request
        if show_help:
            self._show_template_help(template_name)
            return

        if force_server_discovery:
            console.print(
                "[yellow]🔍 Force server discovery mode - MCP probe only (no static fallback)[/yellow]"
            )

        # Get environment variables for the template
        config_values = self.session_configs.get(template_name, {})

        # Add environment variables to config_values if available and not already set
        template_info = self.template_manager.get_template_info(template_name)
        if template_info:
            config_schema = template_info.get("config_schema", {})
            properties = config_schema.get("properties", {})

            for prop_name, prop_config in properties.items():
                env_mapping = prop_config.get("env_mapping")
                if (
                    env_mapping
                    and env_mapping in os.environ
                    and prop_name not in config_values
                ):
                    config_values[prop_name] = os.environ[env_mapping]

        # Use the shared CLI method - this handles all the logic correctly
        try:
            tools = self.tool_manager.list_tools(
                template_or_id=template_name,
                discovery_method="auto",
                force_refresh=force_server_discovery,
                config_values=config_values,
            )
            
            # Display the tools if we got any
            if tools:
                self.beautifier.beautify_tools_list(tools, f"Template: {template_name}")
            else:
                console.print(f"[yellow]⚠️  No tools found for template '{template_name}'[/yellow]")
                
        except Exception as e:
            console.print(f"[red]❌ Exception during tool discovery for template '{template_name}': {e}[/red]")
            return

    def _show_template_help(self, template_name: str):
        """Show detailed help for a template including configuration and tools."""
        template_info = self.template_manager.get_template_info(template_name)
        if not template_info:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            available_templates = self.template_manager.list_templates()
            console.print(
                f"[dim]Available templates: {', '.join(available_templates.keys())}[/dim]"
            )
            return

        template = template_info

        # Template overview
        console.print(
            Panel(
                f"[cyan]Template: {template_name}[/cyan]\n"
                f"Description: {template.get('description', 'No description available')}\n"
                f"Transport: {template.get('transport', {}).get('default', 'http')}\n"
                f"Supported: {', '.join(template.get('transport', {}).get('supported', ['http']))}",
                title="Template Overview",
                border_style="blue",
            )
        )

        # Configuration Schema
        config_schema = template.get("config_schema", {})
        if config_schema:
            properties = config_schema.get("properties", {})
            required = config_schema.get("required", [])

            if properties:
                table = Table(title="Configuration Parameters")
                table.add_column("Parameter", style="cyan", width=20)
                table.add_column("Type", style="yellow", width=12)
                table.add_column("Required", style="red", width=8)
                table.add_column("Environment", style="green", width=20)
                table.add_column("Description", style="white", width=40)

                for prop_name, prop_config in properties.items():
                    prop_type = prop_config.get("type", "string")
                    is_required = "✓" if prop_name in required else "✗"
                    env_var = prop_config.get("env_mapping", f"{prop_name.upper()}")
                    description = prop_config.get("description", "No description")

                    table.add_row(
                        prop_name, prop_type, is_required, env_var, description
                    )

                console.print(table)

        # Get and show tools
        console.print("\n[cyan]📋 Available Tools:[/cyan]")

        # Try to get tools using current session config
        config_values = self.session_configs.get(template_name, {})

        # Add environment variables to config_values if available and not already set
        if config_schema:
            properties = config_schema.get("properties", {})
            for prop_name, prop_config in properties.items():
                env_mapping = prop_config.get("env_mapping")
                if (
                    env_mapping
                    and env_mapping in os.environ
                    and prop_name not in config_values
                ):
                    config_values[prop_name] = os.environ[env_mapping]

        try:
            # Get tools using tool discovery
            tools = self.tool_manager.discover_tools_static(template_name)

            if tools:
                # Show detailed tool information
                for tool in tools:
                    tool_name = tool.get("name", "Unknown")
                    tool_desc = tool.get("description", "No description")

                    # Handle parameters from both formats
                    parameters = tool.get("parameters", {})
                    input_schema = tool.get("inputSchema", {})

                    param_info = []
                    if isinstance(parameters, dict) and "properties" in parameters:
                        properties = parameters.get("properties", {})
                        required_params = parameters.get("required", [])
                        for param_name, param_config in properties.items():
                            param_type = param_config.get("type", "any")
                            is_req = (
                                " (required)" if param_name in required_params else ""
                            )
                            param_desc = param_config.get("description", "")
                            param_info.append(
                                f"  • {param_name}: {param_type}{is_req} - {param_desc}"
                            )
                    elif (
                        isinstance(input_schema, dict) and "properties" in input_schema
                    ):
                        properties = input_schema.get("properties", {})
                        required_params = input_schema.get("required", [])
                        for param_name, param_config in properties.items():
                            param_type = param_config.get("type", "any")
                            is_req = (
                                " (required)" if param_name in required_params else ""
                            )
                            param_desc = param_config.get("description", "")
                            param_info.append(
                                f"  • {param_name}: {param_type}{is_req} - {param_desc}"
                            )

                    tool_text = f"[bold]{tool_name}[/bold]: {tool_desc}"
                    if param_info:
                        tool_text += "\n[dim]Parameters:[/dim]\n" + "\n".join(
                            param_info
                        )
                    else:
                        tool_text += "\n[dim]No parameters required[/dim]"

                    console.print(
                        Panel(tool_text, border_style="green", padding=(1, 2))
                    )
            else:
                console.print(
                    "[yellow]⚠️  No tools found. Try configuring the template first.[/yellow]"
                )

        except Exception as e:
            console.print(f"[red]❌ Failed to discover tools: {e}[/red]")
            console.print(
                "[dim]This may be due to missing configuration or connectivity issues.[/dim]"
            )

        # Usage examples
        examples_text = f"""[cyan]Usage Examples:[/cyan]

[yellow]Configuration:[/yellow]
  config {template_name} param=value

[yellow]List Tools:[/yellow]
  tools {template_name}
  tools {template_name} --force-server

[yellow]Call Tools:[/yellow]
  call {template_name} tool_name
  call {template_name} tool_name {{"param": "value"}}

[yellow]Environment Variables:[/yellow]"""

        if config_schema and config_schema.get("properties"):
            for prop_name, prop_config in config_schema.get("properties", {}).items():
                env_var = prop_config.get("env_mapping", f"{prop_name.upper()}")
                examples_text += f"\n  export {env_var}=your_value"

        console.print(
            Panel(examples_text, title="Usage Examples", border_style="yellow")
        )

    def do_config(self, args):
        """Set configuration for a template.
        Usage: config <template_name> <key>=<value> [<key2>=<value2> ...]
        """
        if not args.strip():
            console.print(
                "[red]❌ Please provide template name and configuration[/red]"
            )
            console.print(
                "Usage: config <template_name> <key>=<value> [<key2>=<value2> ...]"
            )
            return

        parts = args.strip().split()
        if len(parts) < 2:
            console.print(
                "[red]❌ Please provide template name and at least one config value[/red]"
            )
            return

        template_name = parts[0]
        config_pairs = parts[1:]

        # Parse config values
        config_values = {}
        for pair in config_pairs:
            if "=" not in pair:
                console.print(
                    f"[red]❌ Invalid config format: {pair}. Use KEY=VALUE[/red]"
                )
                return
            key, value = pair.split("=", 1)
            config_values[key] = value

        # Store in session
        if template_name not in self.session_configs:
            self.session_configs[template_name] = {}
        self.session_configs[template_name].update(config_values)

        # Cache configuration
        cache_key = f"interactive_config_{template_name}"
        self.cache.set(cache_key, self.session_configs[template_name])

        console.print(
            f"[green]✅ Configuration saved for template '{template_name}'[/green]"
        )

        # Display current config
        current_config = self.session_configs[template_name]
        table = Table(title=f"Configuration for {template_name}")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in current_config.items():
            # Mask sensitive values
            display_value = (
                "***"
                if any(
                    sensitive in key.lower()
                    for sensitive in ["token", "key", "secret", "password"]
                )
                else value
            )
            table.add_row(key, display_value)

        console.print(table)

    def _validate_and_get_tool_parameters(
        self,
        template_name: str,
        tool_name: str,
        tool_args: str,
        config_values: Dict[str, Any],
    ) -> Union[str, None]:
        """Validate tool parameters and prompt for missing required ones.

        Args:
            template_name: Name of the template
            tool_name: Name of the tool
            tool_args: JSON string arguments provided by user
            config_values: Current configuration values

        Returns:
            Updated JSON arguments string, or None if validation failed
        """
        try:
            # Parse existing arguments
            current_args = {}
            if tool_args and tool_args.strip() != "{}":
                try:
                    current_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    console.print(
                        f"[red]❌ Invalid JSON in tool arguments: {tool_args}[/red]"
                    )
                    return None

            # Get tool information using tool discovery
            try:
                tools = self.tool_manager.discover_tools_static(template_name)
            except Exception as e:
                console.print(
                    f"[yellow]⚠️  Could not discover tools for validation: {e}[/yellow]"
                )
                # Continue with original args if tool discovery fails
                return tool_args

            # Validate that tools is a list and contains dictionaries
            if not isinstance(tools, list):
                console.print(
                    "[yellow]⚠️  Tool discovery returned unexpected format[/yellow]"
                )
                return tool_args

            # Find the specific tool
            target_tool = None
            for tool in tools:
                if not isinstance(tool, dict):
                    continue  # Skip non-dictionary entries
                if tool.get("name") == tool_name:
                    target_tool = tool
                    break

            if not target_tool:
                console.print(
                    f"[yellow]⚠️  Tool '{tool_name}' not found for validation[/yellow]"
                )
                return tool_args

            # Check tool parameters
            parameters = target_tool.get("parameters", {})
            input_schema = target_tool.get("inputSchema", {})

            # Use the appropriate schema format
            schema_to_use = None
            if isinstance(parameters, dict) and "properties" in parameters:
                schema_to_use = parameters
            elif isinstance(input_schema, dict) and "properties" in input_schema:
                schema_to_use = input_schema

            if not schema_to_use:
                # No schema to validate against
                return tool_args

            properties = schema_to_use.get("properties", {})
            required_params = schema_to_use.get("required", [])

            # Check for missing required parameters
            missing_required = []
            for param_name in required_params:
                if param_name not in current_args:
                    missing_required.append(param_name)

            if missing_required:
                console.print(
                    f"[yellow]⚠️  Missing required parameters for tool '{tool_name}': {', '.join(missing_required)}[/yellow]"
                )

                if Confirm.ask("Would you like to provide the missing parameters?"):
                    console.print(
                        f"[cyan]Providing parameters for tool '{tool_name}'...[/cyan]"
                    )

                    for param_name in missing_required:
                        param_config = properties.get(param_name, {})
                        param_type = param_config.get("type", "string")
                        param_desc = param_config.get(
                            "description", f"Value for {param_name}"
                        )

                        value = Prompt.ask(
                            f"Enter {param_name} ({param_type}) - {param_desc}"
                        )
                        if value:
                            # Convert value based on type
                            if param_type == "integer":
                                try:
                                    current_args[param_name] = int(value)
                                except ValueError:
                                    current_args[param_name] = value
                            elif param_type == "number":
                                try:
                                    current_args[param_name] = float(value)
                                except ValueError:
                                    current_args[param_name] = value
                            elif param_type == "boolean":
                                current_args[param_name] = value.lower() in (
                                    "true",
                                    "1",
                                    "yes",
                                    "on",
                                )
                            else:
                                current_args[param_name] = value

                    # Return updated JSON arguments
                    return json.dumps(current_args)
                else:
                    console.print(
                        "[yellow]⚠️  Cannot proceed without required parameters[/yellow]"
                    )
                    return None

            # All required parameters are present
            return tool_args

        except Exception as e:
            console.print(f"[yellow]⚠️  Parameter validation error: {e}[/yellow]")
            # Continue with original args if validation fails
            return tool_args

    def do_call(self, line):
        """Call a tool from a template using argparse flags.

        Usage:
          call <template_name> <tool_name> [json_args]
          call --config-file config.json <template_name> <tool_name> [json_args]
          call --env API_KEY=value --config timeout=30 <template_name> <tool_name> [json_args]
          call --raw <template_name> <tool_name> [json_args]  # Show raw JSON output
        """
        try:
            # Handle JSON arguments specially - find JSON-like content and preserve it
            line = line.strip()
            if not line:
                argv = []
            else:
                # Look for JSON-like content (starts with { and ends with })
                json_start = line.find('{')
                json_end = line.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    # Split the line into non-JSON part and JSON part
                    before_json = line[:json_start].strip()
                    json_part = line[json_start:json_end + 1].strip()
                    after_json = line[json_end + 1:].strip()
                    
                    # Use shlex for the non-JSON parts
                    argv = shlex.split(before_json) if before_json else []
                    if json_part:
                        argv.append(json_part)
                    if after_json:
                        argv.extend(shlex.split(after_json))
                else:
                    # No JSON detected, use normal shlex splitting
                    argv = shlex.split(line)

            # Parse arguments using the call_parser
            args = call_parser.parse_args(argv)

        except (ValueError, SystemExit) as e:
            console.print(f"[red]❌ Error parsing command line: {e}[/red]")
            console.print("[dim]Use: call <template> <tool> [json_args][/dim]")
            return
        # Merge configuration from all sources
        template_name = args.template_name

        # Get template info for proper config processing
        available_templates = self.template_manager.list_templates()
        if template_name not in available_templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.template_manager.get_template_info(template_name)

        try:
            config_values = merge_config_sources(
                session_config=self.session_configs.get(template_name, {}),
                config_file=args.config_file,
                env_vars=args.env,
                inline_config=args.config,
                template=template,
            )
        except Exception:
            return  # Error already printed in merge_config_sources

        tool_name = args.tool_name
        
        # Handle json_args - join multiple parts back together and default to empty dict
        if isinstance(args.json_args, list):
            if not args.json_args:
                tool_args = "{}"
            else:
                tool_args = " ".join(args.json_args)
        else:
            tool_args = args.json_args or "{}"
            
        no_pull = args.no_pull

        console.print(
            f"\n[cyan]🚀 Calling tool '{tool_name}' from template '{template_name}'[/cyan]"
        )
        # Check if template exists
        available_templates = self.template_manager.list_templates()
        if template_name not in available_templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.template_manager.get_template_info(template_name)
        transport_config = template.get("transport", {})
        default_transport = transport_config.get("default", "http")
        supported_transports = transport_config.get("supported", ["http"])

        # Check for mandatory properties for stdio transport
        if "stdio" in supported_transports or default_transport == "stdio":
            # Check if template has required configuration
            config_schema = template.get("config_schema", {})
            required_props = config_schema.get("required", [])

            if required_props:
                missing_props = []
                for prop in required_props:
                    prop_config = config_schema.get("properties", {}).get(prop, {})
                    env_mapping = prop_config.get("env_mapping", prop.upper())

                    # Check if we have this config value
                    if prop not in config_values and env_mapping not in config_values:
                        missing_props.append(prop)

                if missing_props:
                    console.print(
                        f"[yellow]⚠️  Missing required configuration for '{template_name}': {', '.join(missing_props)}[/yellow]"
                    )
                    console.print("[dim]Please set configuration using:[/dim]")
                    console.print(
                        "[dim]• call --config key=value <template> <tool>[/dim]"
                    )
                    console.print(
                        "[dim]• call --config-file path.json <template> <tool>[/dim]"
                    )
                    console.print("[dim]• call --env KEY=VALUE <template> <tool>[/dim]")
                    console.print("[dim]• config <template> key=value[/dim]")

                    if Confirm.ask("Would you like to set configuration now?"):
                        console.print(
                            f"[cyan]Setting configuration for {template_name}...[/cyan]"
                        )
                        for prop in missing_props:
                            prop_config = config_schema.get("properties", {}).get(
                                prop, {}
                            )
                            description = prop_config.get(
                                "description", f"Value for {prop}"
                            )
                            value = Prompt.ask(f"Enter {prop} ({description})")
                            if value:
                                config_values[prop] = value

                        # Save the config
                        self.session_configs[template_name] = config_values
                        cache_key = f"interactive_config_{template_name}"
                        self.cache.set(cache_key, config_values)
                        console.print("[green]✅ Configuration saved[/green]")
                    else:
                        console.print(
                            "[yellow]⚠️  Cannot proceed without required configuration[/yellow]"
                        )
                        return

        # Use the enhanced tool manager call_tool method that implements HTTP-first logic
        console.print(
            "[dim]Checking for running server (HTTP first, stdio fallback)...[/dim]"
        )

        try:
            # Ensure tool_args is parsed as JSON if it's a string
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    console.print(f"[red]❌ Invalid JSON arguments: {tool_args}[/red]")
                    return

            result = self.tool_manager.call_tool(
                template_name,
                tool_name,
                tool_args,
                config_values,
                pull_image=not no_pull,
            )

            if result and result.get("success"):
                # Display successful result
                if result.get("result"):
                    self._display_tool_result(result["result"], tool_name, args.raw)
                else:
                    console.print(
                        "[green]✅ Tool executed successfully (no output)[/green]"
                    )
            else:
                error_msg = (
                    result.get("error", "Tool execution failed")
                    if result
                    else "Tool execution failed"
                )
                console.print(f"[red]❌ Tool execution failed: {error_msg}[/red]")

        except Exception as e:
            console.print(f"[red]❌ Failed to execute tool: {e}[/red]")

    def _display_tool_result(self, result: Any, tool_name: str, raw: bool = False):
        """Display tool result in tabular format or raw JSON."""
        try:
            if raw:
                # Show raw JSON format
                self.beautifier.beautify_json(result, f"Tool Result: {tool_name}")
            else:
                # Show tabular format
                self._display_tool_result_table(result, tool_name)
        except Exception:
            # Fallback to simple display if both methods fail
            console.print(f"[green]✅ Tool '{tool_name}' result:[/green]")
            console.print(result)

    def _display_tool_result_table(self, result: Any, tool_name: str):
        """Display tool result in a user-friendly tabular format."""
        from rich.table import Table
        from rich import box
        
        # Handle different types of results
        if isinstance(result, dict):
            # Check if it's an MCP-style response with content
            if "content" in result and isinstance(result["content"], list):
                self._display_mcp_content_table(result["content"], tool_name)
            # Check if it's a structured response with result data
            elif "structuredContent" in result and "result" in result["structuredContent"]:
                self._display_simple_result_table(result["structuredContent"]["result"], tool_name)
            # Check if it's a simple dict that can be displayed as key-value pairs
            else:
                self._display_dict_as_table(result, tool_name)
        elif isinstance(result, list):
            self._display_list_as_table(result, tool_name)
        else:
            # Single value result
            self._display_simple_result_table(result, tool_name)
    
    def _display_mcp_content_table(self, content_list: list, tool_name: str):
        """Display MCP content array in tabular format."""
        from rich.table import Table
        from rich import box
        
        table = Table(
            title=f"🎯 {tool_name} Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Content", style="white", min_width=40)
        
        for i, content in enumerate(content_list):
            if isinstance(content, dict):
                content_type = content.get("type", "unknown")
                if content_type == "text":
                    text_content = content.get("text", "")
                    # Try to parse as JSON for better formatting
                    try:
                        import json
                        parsed = json.loads(text_content)
                        if isinstance(parsed, dict):
                            # Display nested dict in a compact format
                            formatted_content = "\n".join([f"{k}: {v}" for k, v in parsed.items()])
                        else:
                            formatted_content = str(parsed)
                    except (json.JSONDecodeError, AttributeError):
                        formatted_content = text_content
                    table.add_row(content_type, formatted_content)
                else:
                    # Handle other content types
                    table.add_row(content_type, str(content))
            else:
                table.add_row("unknown", str(content))
        
        console.print(table)
        
        # Also check for structured content if available
        if hasattr(self, '_current_result') and "structuredContent" in getattr(self, '_current_result', {}):
            structured = getattr(self, '_current_result')["structuredContent"]
            if "result" in structured:
                console.print(f"\n[green]✅ Result:[/green] {structured['result']}")
    
    def _display_simple_result_table(self, result: Any, tool_name: str):
        """Display a simple result value in a clean format."""
        from rich.table import Table
        from rich import box
        
        table = Table(
            title=f"🎯 {tool_name} Result",
            box=box.ROUNDED,
            show_header=False,
            width=60
        )
        
        table.add_column("", style="bold green", justify="center")
        table.add_row(str(result))
        
        console.print(table)
    
    def _display_dict_as_table(self, data: dict, tool_name: str):
        """Display a dictionary as a key-value table."""
        from rich.table import Table
        from rich import box
        
        table = Table(
            title=f"🎯 {tool_name} Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        table.add_column("Property", style="yellow", width=20)
        table.add_column("Value", style="white", min_width=40)
        
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                # For complex values, show a summary
                if isinstance(value, dict):
                    display_value = f"Dict with {len(value)} items"
                    if len(value) <= 3:  # Show small dicts inline
                        display_value = ", ".join([f"{k}: {v}" for k, v in value.items()])
                else:  # list
                    display_value = f"List with {len(value)} items"
                    if len(value) <= 3 and all(not isinstance(item, (dict, list)) for item in value):
                        display_value = ", ".join(str(item) for item in value)
            else:
                display_value = str(value)
            
            table.add_row(key, display_value)
        
        console.print(table)
    
    def _display_list_as_table(self, data: list, tool_name: str):
        """Display a list as a table."""
        from rich.table import Table
        from rich import box
        
        table = Table(
            title=f"🎯 {tool_name} Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan"
        )
        
        if data and isinstance(data[0], dict):
            # List of dicts - use dict keys as columns
            if data:
                keys = list(data[0].keys())
                for key in keys:
                    table.add_column(key.title(), style="white")
                
                for item in data:
                    row = []
                    for key in keys:
                        value = item.get(key, "")
                        if isinstance(value, (dict, list)):
                            row.append(f"{type(value).__name__}({len(value)})")
                        else:
                            row.append(str(value))
                    table.add_row(*row)
        else:
            # Simple list - show as single column
            table.add_column("Item", style="white")
            for i, item in enumerate(data):
                table.add_row(str(item))
        
        console.print(table)

    def do_show_config(self, template_name):
        """Show current configuration for a template.
        Usage: show_config <template_name>
        """
        if not template_name.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            return

        template_name = template_name.strip()

        if template_name not in self.session_configs:
            console.print(
                f"[yellow]⚠️  No configuration found for '{template_name}'[/yellow]"
            )
            return

        config = self.session_configs[template_name]
        table = Table(title=f"Configuration for {template_name}")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="yellow")

        for key, value in config.items():
            # Mask sensitive values
            display_value = (
                "***"
                if any(
                    sensitive in key.lower()
                    for sensitive in ["token", "key", "secret", "password"]
                )
                else value
            )
            table.add_row(key, display_value)

        console.print(table)

    def do_clear_config(self, template_name):
        """Clear configuration for a template.
        Usage: clear_config <template_name>
        """
        if not template_name.strip():
            console.print("[red]❌ Please provide a template name[/red]")
            return

        template_name = template_name.strip()

        if template_name in self.session_configs:
            del self.session_configs[template_name]

            # Clear from cache
            cache_key = f"interactive_config_{template_name}"
            self.cache.remove(cache_key)

            console.print(
                f"[green]✅ Configuration cleared for '{template_name}'[/green]"
            )
        else:
            console.print(
                f"[yellow]⚠️  No configuration found for '{template_name}'[/yellow]"
            )

    def do_templates(self, arg):
        """List all available templates.
        Usage: templates
        """
        templates = self.template_manager.list_templates()

        if not templates:
            console.print("[yellow]⚠️  No templates found[/yellow]")
            return

        table = Table(title=f"Available Templates ({len(templates)} found)")
        table.add_column("Template", style="cyan", width=20)
        table.add_column("Transport", style="yellow", width=15)
        table.add_column("Default Port", style="green", width=12)
        table.add_column("Tools", style="magenta", width=10)
        table.add_column("Description", style="white", width=40)

        for name, template in templates.items():
            transport_config = template.get("transport", {})
            default_transport = transport_config.get("default", "http")
            port = transport_config.get("port", "N/A")
            tools = template.get("tools", [])
            tool_count = len(tools) if tools else "Unknown"
            description = template.get("description", "No description")

            table.add_row(
                name, default_transport, str(port), str(tool_count), description
            )

        console.print(table)
        console.print(
            "\n[green]💡 Use 'tools <template_name>' to see available tools[/green]"
        )
        console.print(
            "[green]💡 Use 'config <template_name> key=value' to set configuration[/green]"
        )

    def do_quit(self, arg):
        """Exit the interactive CLI.
        Usage: quit
        """
        console.print(
            "\n[green]👋 Goodbye! Thanks for using MCP Interactive CLI![/green]"
        )
        return True

    def do_exit(self, arg):
        """Exit the interactive CLI.
        Usage: exit
        """
        return self.do_quit(arg)

    def do_help(self, arg):
        """Show help information.
        Usage: help [command]
        """
        if arg:
            super().do_help(arg)
        else:
            console.print(
                Panel(
                    """
[cyan]Available Commands:[/cyan]

[yellow]Server Management:[/yellow]
  • list_servers          - List all deployed MCP servers
  • templates             - List all available templates

[yellow]Tool Operations:[/yellow]
  • tools <template>      - List available tools for a template
  • call <template> <tool> [args] - Call a tool (stdio or HTTP)
    [dim]Options: --config-file, --env KEY=VALUE, --config KEY=VALUE[/dim]

[yellow]Configuration (Multiple Ways):[/yellow]
  • config <template> key=value   - Set configuration interactively
  • show_config <template>        - Show current template configuration
  • clear_config <template>       - Clear template configuration

[yellow]General:[/yellow]
  • help [command]        - Show this help or help for specific command
  • quit / exit           - Exit the interactive CLI

[green]Examples:[/green]
  • templates
  • config github github_token=your_token_here
  • tools github
  • call github search_repositories {"query": "python"}
  • call --config-file config.json demo say_hello
  • call --env API_KEY=xyz --config timeout=30 github search_repositories '{"query": "python"}'
  • call demo say_hello (no config needed)
  [dim]For stdio templates: config is prompted if missing mandatory properties[/dim]
  [dim]For HTTP templates: server deployment is prompted if not running[/dim]
""",
                    title="MCP Interactive CLI Help",
                    border_style="blue",
                )
            )

    def emptyline(self):
        """Override to do nothing on empty line."""
        pass

    def default(self, line):
        """Handle unknown commands."""
        # Debug: Let's see what's causing the empty command
        if not line or line.strip() == "":
            # Skip empty lines/commands without error
            return
        console.print(f"[red]❌ Unknown command: {line}[/red]")
        console.print("[dim]Type 'help' for available commands[/dim]")


def start_interactive_cli():
    """Start the interactive CLI session."""
    console.print("[green]🚀 Starting MCP Interactive CLI...[/green]")

    try:
        cli = InteractiveCLI()
        cli.cmdloop()
    except Exception as e:
        console.print(f"[red]❌ Failed to start interactive CLI: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    start_interactive_cli()
