"""
Unified Response Formatter and Visual Design System.

This module combines the ResponseBeautifier functionality from interactive_cli.py
with the multi-backend visual formatting from utils/visual_formatting.py to provide
a comprehensive formatting solution.
"""

import datetime
import json
import logging
import traceback
from typing import Any, Dict, List, Union

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from mcp_template.backends import VALID_BACKENDS

logger = logging.getLogger(__name__)

# Backend visual configuration
BACKEND_COLORS = {
    "docker": "blue",
    "kubernetes": "green",
    "mock": "yellow",
    "unknown": "dim",
}

BACKEND_ICONS = {"docker": "🐳", "kubernetes": "☸️", "mock": "🔧", "unknown": "❓"}

STATUS_COLORS = {
    "running": "green",
    "stopped": "red",
    "starting": "yellow",
    "error": "bright_red",
    "unknown": "dim",
    "pending": "blue",
    "terminating": "orange1",
}

console = Console()


def get_backend_color(backend_type: str) -> str:
    """Get color for backend type."""
    return BACKEND_COLORS.get(backend_type, "dim")


def get_backend_icon(backend_type: str) -> str:
    """Get icon for backend type."""
    return BACKEND_ICONS.get(backend_type, "❓")


def get_status_color(status: str) -> str:
    """Get color for deployment status."""
    return STATUS_COLORS.get(status.lower() if status else "unknown", "dim")


def get_backend_indicator(backend_type: str, include_icon: bool = True) -> str:
    """
    Get visual indicator for backend type.

    Args:
        backend_type: Backend type string
        include_icon: Whether to include emoji icon

    Returns:
        Formatted backend indicator string
    """
    icon = get_backend_icon(backend_type) if include_icon else ""
    color = get_backend_color(backend_type)
    name = backend_type.upper()

    if include_icon:
        return f"[{color}]{icon} {name}[/]"
    else:
        return f"[{color}]{name}[/]"


def format_timestamp(timestamp: Union[str, datetime.datetime, None]) -> str:
    """
    Format timestamp for display.

    Args:
        timestamp: Timestamp to format

    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"

    if isinstance(timestamp, str):
        try:
            # Try parsing ISO format
            dt = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return timestamp[:19] if len(timestamp) > 19 else timestamp
    elif isinstance(timestamp, datetime.datetime):
        dt = timestamp
    else:
        return str(timestamp)

    # Format as relative time if recent, otherwise absolute
    now = datetime.datetime.now(dt.tzinfo) if dt.tzinfo else datetime.datetime.now()
    delta = now - dt

    if delta.days == 0:
        if delta.seconds < 60:
            return "just now"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60}m ago"
        else:
            return f"{delta.seconds // 3600}h ago"
    elif delta.days == 1:
        return "yesterday"
    elif delta.days < 7:
        return f"{delta.days}d ago"
    else:
        return dt.strftime("%Y-%m-%d")


def render_deployments_grouped_by_backend(
    grouped_deployments: Dict[str, List[Dict]], show_empty: bool = False
) -> None:
    """
    Render deployments grouped by backend with visual separation.

    Args:
        grouped_deployments: Dictionary mapping backend_type to deployment list
        show_empty: Whether to show backends with no deployments
    """
    if not grouped_deployments and not show_empty:
        console.print("[dim]No deployments found.[/]")
        return

    for backend_type in VALID_BACKENDS:  # Production backends only
        deployments = grouped_deployments.get(backend_type, [])

        if not deployments and not show_empty:
            continue

        # Backend header
        backend_indicator = get_backend_indicator(backend_type)
        count_text = (
            f"({len(deployments)} deployment{'s' if len(deployments) != 1 else ''})"
        )
        header = f"{backend_indicator} {count_text}"

        console.print(f"\n{header}")

        if not deployments:
            console.print("  No deployments")
            continue

        # Create table for this backend's deployments
        table = Table(show_header=True, header_style="cyan", padding=(0, 1))
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Template", style="white", width=15)
        table.add_column("Status", style="white", width=10)
        table.add_column("Created", style="blue", width=10)
        table.add_column("Transport", style="yellow", width=10)

        for deployment in deployments:
            deployment_id = deployment.get("id", deployment.get("name", "N/A"))[:11]
            template = deployment.get("template", "unknown")
            status = deployment.get("status", "unknown")
            created = format_timestamp(deployment.get("created"))
            transport = deployment.get("transport", "N/A")

            # Colorize status
            status_color = get_status_color(status)
            status_text = f"[{status_color}]● {status}[/]"

            table.add_row(deployment_id, template, status_text, created, transport)

        console.print(table)


def render_deployments_unified_table(
    deployments: List[Dict[str, Any]], title: str = "All Deployments"
) -> None:
    """
    Render all deployments in a single unified table.

    Args:
        deployments: List of deployment dictionaries
        title: Table title
    """
    if not deployments:
        console.print("[dim]No deployments found.[/]")
        return

    table = Table(title=title, show_header=True, header_style="cyan")
    table.add_column("Backend", style="white", width=12)
    table.add_column("ID", style="cyan", width=12)
    table.add_column("Template", style="white", width=15)
    table.add_column("Status", style="white", width=10)
    table.add_column("Created", style="blue", width=10)
    table.add_column("Transport", style="yellow", width=10)

    for deployment in deployments:
        backend_type = deployment.get("backend_type", "unknown")
        backend_indicator = get_backend_indicator(backend_type, include_icon=False)

        deployment_id = deployment.get("id", deployment.get("name", "N/A"))[:11]
        template = deployment.get("template", "unknown")
        status = deployment.get("status", "unknown")
        created = format_timestamp(deployment.get("created"))
        transport = deployment.get("transport", "N/A")

        # Colorize status
        status_color = get_status_color(status)
        status_text = f"[{status_color}]● {status}[/]"

        table.add_row(
            backend_indicator, deployment_id, template, status_text, created, transport
        )

    console.print(table)


def format_deployment_summary(deployments: List[Dict[str, Any]]) -> str:
    """
    Create a summary string for a list of deployments.

    Args:
        deployments: List of deployment dictionaries

    Returns:
        Summary string
    """
    if not deployments:
        return "No deployments"

    # Count by status
    status_counts = {}
    backend_counts = {}

    for deployment in deployments:
        status = deployment.get("status", "unknown")
        backend = deployment.get("backend_type", "unknown")

        status_counts[status] = status_counts.get(status, 0) + 1
        backend_counts[backend] = backend_counts.get(backend, 0) + 1

    # Build summary
    total = len(deployments)
    summary_parts = [f"{total} total"]

    # Add status breakdown if multiple statuses
    if len(status_counts) > 1:
        running = status_counts.get("running", 0)
        if running > 0:
            summary_parts.append(f"{running} running")

    # Add backend breakdown if multiple backends
    if len(backend_counts) > 1:
        backend_parts = []
        for backend, count in backend_counts.items():
            backend_parts.append(f"{count} {backend}")
        summary_parts.append(f"({', '.join(backend_parts)})")

    return ", ".join(summary_parts)


def render_backend_health_status(health_data: Dict[str, Any]) -> None:
    """
    Render health status for all backends.

    Args:
        health_data: Health status data by backend
    """
    console.print("\n[bold]Backend Health Status[/]")

    panels = []
    for backend_type in ["docker", "kubernetes"]:  # Production backends only
        if backend_type not in health_data:
            continue

        health = health_data[backend_type]
        status = health.get("status", "unknown")
        deployment_count = health.get("deployment_count", 0)
        error = health.get("error")

        # Choose colors and icons based on status
        if status == "healthy":
            status_color = "green"
            status_icon = "✅"
        else:
            status_color = "red"
            status_icon = "❌"

        backend_icon = get_backend_icon(backend_type)
        backend_color = get_backend_color(backend_type)

        # Panel content
        content = f"[{status_color}]{status_icon} {status.upper()}[/]\n"
        content += f"Deployments: {deployment_count}"

        if error:
            content += f"\n[red]Error: {error[:40]}[/]"

        panel = Panel(
            content,
            title=f"[{backend_color}]{backend_icon} {backend_type.upper()}[/]",
            border_style=backend_color,
            width=20,
        )
        panels.append(panel)

    if panels:
        console.print(Columns(panels, equal=True))
    else:
        console.print("[dim]No backend health data available.[/]")


class MultiBackendProgressTracker:
    """Track progress of operations across multiple backends."""

    def __init__(self, backends: List[str]):
        self.backends = backends
        self.results = {}
        self.completed = []
        self.progress = None
        self.task = None

    def start(self, description: str = "Processing backends"):
        """Start progress tracking."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        )
        self.task = self.progress.add_task(description, total=len(self.backends))
        self.progress.start()

    def start_backend(self, backend_type: str):
        """Start processing a backend."""
        console.print(
            f"[blue]🔄 Starting {get_backend_indicator(backend_type)}...[/blue]"
        )

    def finish_backend(
        self, backend_type: str, success: bool = True, message: str = ""
    ):
        """Finish processing a backend."""
        self.completed.append(backend_type)
        self.results[backend_type] = {"success": success, "message": message}

        if success:
            console.print(
                f"[green]✅ {get_backend_indicator(backend_type)} completed: {message}[/green]"
            )
        else:
            console.print(
                f"[red]❌ {get_backend_indicator(backend_type)} failed: {message}[/red]"
            )

        if self.progress and self.task:
            self.progress.update(self.task, advance=1)

    def update_backend(
        self, backend_type: str, success: bool = True, result: Any = None
    ):
        """Update progress for a backend (backward compatibility)."""
        self.finish_backend(backend_type, success, str(result) if result else "")

    def stop(self):
        """Stop progress tracking."""
        if self.progress:
            self.progress.stop()

    def get_results(self) -> Dict[str, Any]:
        """Get all results."""
        return self.results

    def get_summary(self) -> str:
        """Get a summary of the progress tracking results."""
        if not self.results:
            return "No backends processed"

        total = len(self.backends)
        successful = sum(
            1 for result in self.results.values() if result.get("success", False)
        )
        failed = total - successful

        if failed == 0:
            return f"All {total} backends completed successfully"
        elif successful == 0:
            return f"All {total} backends failed"
        else:
            return f"{successful}/{total} backends successful, {failed} failed"


class ResponseFormatter:
    """Unified response formatter combining MCP response formatting with multi-backend visual formatting."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the response formatter.

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
                self.beautify_toollist(tools, "MCP Server Tools")
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
                if self.verbose:
                    self.console.print(
                        f"[yellow]⚠️  Beautifier parsing error: {e}[/yellow]"
                    )
                    self.console.print(
                        f"[dim]Traceback: {traceback.format_exc()}[/dim]"
                    )
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
                if self.verbose:
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
        self,
        tools: List[Dict[str, Any]],
        source: str = "Template",
        discovery_method: str = "unknown",
        backend: str = "unknown",
        template_name: str = "unknown",
    ) -> None:
        """Beautify tools list display with discovery metadata."""
        if not tools:
            self.console.print("[yellow]⚠️  No tools found[/yellow]")
            return

        # Create discovery metadata display
        discovery_info = (
            f"Backend: {backend} | Method: {discovery_method} | Source: {source}"
        )

        # Create tools table with enhanced title
        table = Table(
            title=f"Tools from '{template_name}' ({len(tools)} found) - {discovery_info}",
            header_style="bold cyan",
            show_lines=True,  # Add lines between rows for spacing
        )
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

        # Show detailed discovery information
        discovery_hints = {
            "stdio": "🔗 Tools discovered via stdio interface (direct container communication)",
            "http": "🌐 Tools discovered via HTTP API (from running server)",
            "static": "📄 Tools discovered from template definition files",
            "cache": "💾 Tools loaded from cache (use --force-refresh for latest)",
            "error": "❌ Error occurred during discovery",
        }

        hint = discovery_hints.get(
            discovery_method, f"ℹ️  Discovery method: {discovery_method}"
        )
        self.console.print(f"[dim]{hint}[/dim]")

        # Show additional metadata
        if backend != "unknown":
            self.console.print(
                f"[dim]💡 Using {backend} backend for container operations[/dim]"
            )
