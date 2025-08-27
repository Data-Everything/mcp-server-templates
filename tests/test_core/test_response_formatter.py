"""
Tests for the ResponseFormatter class.

This module contains comprehensive tests for the ResponseFormatter class that handles
formatting and beautification of various data structures in CLI output.
"""

import datetime
import json
from unittest.mock import Mock, patch

import pytest
from rich.console import Console
from rich.table import Table

from mcp_template.core.response_formatter import (
    ResponseFormatter,
    format_deployment_summary,
    format_timestamp,
    get_backend_color,
    get_backend_icon,
    get_backend_indicator,
    get_status_color,
)

pytestmark = pytest.mark.unit


class TestResponseFormatterCore:
    """Test cases for ResponseFormatter class core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ResponseFormatter()

    def test_init(self):
        """Test ResponseFormatter initialization."""
        assert isinstance(self.formatter.console, Console)
        assert self.formatter.verbose is False

    def test_init_verbose(self):
        """Test ResponseFormatter initialization with verbose flag."""
        formatter = ResponseFormatter(verbose=True)
        assert formatter.verbose is True

    def test_is_actual_error(self):
        """Test error detection in stderr."""
        # Actual errors
        assert self.formatter._is_actual_error("Error: something went wrong")
        assert self.formatter._is_actual_error("Exception: failed to connect")
        assert self.formatter._is_actual_error("Traceback (most recent call last):")
        assert self.formatter._is_actual_error("FATAL: cannot start server")
        assert self.formatter._is_actual_error("Permission denied")

        # Informational messages (not errors)
        assert not self.formatter._is_actual_error("Server started successfully")
        assert not self.formatter._is_actual_error("Running on stdio")
        assert not self.formatter._is_actual_error("Connected to database")
        assert not self.formatter._is_actual_error("Initialized properly")

        # Empty or None
        assert not self.formatter._is_actual_error("")
        assert not self.formatter._is_actual_error(None)


class TestDataTypeAnalysis:
    """Test cases for data type analysis functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ResponseFormatter()

    def test_analyze_data_types_simple_dict(self):
        """Test data type analysis for simple dictionaries."""
        data = {"name": "test", "version": "1.0", "active": True}
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["primary_type"] == "dict"
        assert analysis["best_display"] == "key_value"
        assert analysis["complexity"] == "simple"
        assert "simple_mapping" in analysis["structure_hints"]
        assert analysis["size"] == 3

    def test_analyze_data_types_complex_dict(self):
        """Test data type analysis for complex dictionaries."""
        data = {
            "server": {"name": "test", "port": 8080},
            "tools": ["search", "create"],
            "config": {"timeout": 30},
        }
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["primary_type"] == "dict"
        assert analysis["best_display"] == "tree"
        assert analysis["complexity"] == "nested"
        assert "hierarchical" in analysis["structure_hints"]

    def test_analyze_data_types_tabular_list(self):
        """Test data type analysis for tabular data (list of dicts)."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
            {"id": 3, "name": "Charlie", "active": True},
        ]
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "table"
        assert analysis["complexity"] == "tabular"
        assert "record_list" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is True

    def test_analyze_data_types_simple_list(self):
        """Test data type analysis for simple lists."""
        data = ["apple", "banana", "cherry"]
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "list"
        assert analysis["complexity"] == "simple"
        assert "value_list" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is True

    def test_analyze_data_types_mixed_list(self):
        """Test data type analysis for mixed type lists."""
        data = ["text", 123, {"key": "value"}, True]
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "json"
        assert analysis["complexity"] == "heterogeneous"
        assert "mixed_types" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is False

    def test_analyze_data_types_json_string(self):
        """Test data type analysis for JSON strings."""
        data = '{"name": "test", "value": 42}'
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["best_display"] == "key_value"
        assert "json_string" in analysis["structure_hints"]

    def test_analyze_data_types_plain_text(self):
        """Test data type analysis for plain text."""
        data = "This is just plain text"
        analysis = self.formatter._analyze_data_types(data)

        assert analysis["best_display"] == "text"
        assert "plain_text" in analysis["structure_hints"]

    def test_detect_data_structure(self):
        """Test the detect data structure method."""
        # Simple dict
        assert self.formatter._detect_data_structure({"a": 1, "b": 2}) == "key_value"

        # Complex dict
        complex_data = {"a": {"nested": True}, "b": [1, 2, 3]}
        assert self.formatter._detect_data_structure(complex_data) == "tree"

        # List of dicts
        tabular = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert self.formatter._detect_data_structure(tabular) == "table"

        # Simple list
        assert self.formatter._detect_data_structure([1, 2, 3]) == "list"

    def test_is_tabular_dict(self):
        """Test tabular dictionary detection."""
        # Tabular dict
        tabular = {
            "names": ["Alice", "Bob", "Charlie"],
            "ages": [25, 30, 35],
            "active": [True, False, True],
        }
        assert self.formatter._is_tabular_dict(tabular) is True

        # Non-tabular dict
        non_tabular = {"name": "test", "config": {"port": 8080}}
        assert self.formatter._is_tabular_dict(non_tabular) is False

        # Mixed length lists (not tabular)
        mixed = {"names": ["Alice", "Bob"], "ages": [25, 30, 35]}  # Different length
        assert self.formatter._is_tabular_dict(mixed) is False

    def test_has_consistent_keys(self):
        """Test consistent keys detection for list of dicts."""
        # Consistent keys
        consistent = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 35},
        ]
        assert self.formatter._has_consistent_keys(consistent) is True

        # Inconsistent keys
        inconsistent = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "score": 95},  # Different key
            {"title": "Charlie", "age": 35},  # Different key
        ]
        assert self.formatter._has_consistent_keys(inconsistent) is False

        # Empty list
        assert self.formatter._has_consistent_keys([]) is False

        # Non-dict items
        assert self.formatter._has_consistent_keys(["a", "b", "c"]) is False


class TestDisplayFormatters:
    """Test cases for display formatting methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = ResponseFormatter()

    def test_create_key_value_table(self):
        """Test key-value table creation."""
        data = {
            "name": "test-server",
            "version": "1.0.0",
            "active": True,
            "port": 8080,
            "url": "https://example.com",
            "config": {"timeout": 30},
            "tags": ["python", "mcp"],
            "score": 95.567,
            "nullable": None,
        }

        table = self.formatter._create_key_value_table(data, "Test Data")

        assert isinstance(table, Table)
        assert table.title == "Test Data (9 properties)"
        # Verify table has correct number of columns
        assert len(table.columns) == 3  # Property, Value, Type

    def test_create_data_table_from_list(self):
        """Test data table creation from list of dicts."""
        data = [
            {
                "id": 1,
                "name": "Alice",
                "active": True,
                "score": 95.5,
                "url": "https://alice.example.com",
            },
            {
                "id": 2,
                "name": "Bob",
                "active": False,
                "score": 87.2,
                "url": "https://bob.example.com",
            },
            {
                "id": 3,
                "name": "Charlie",
                "active": True,
                "score": 92.8,
                "url": "https://charlie.example.com",
            },
        ]

        table = self.formatter._create_data_table(data, "User Data")

        assert isinstance(table, Table)
        assert table.title == "User Data (3 rows)"
        # Should have 5 columns: id, name, active, score, url
        assert len(table.columns) == 5

    def test_create_data_table_from_dict(self):
        """Test data table creation from tabular dictionary."""
        data = {
            "names": ["Alice", "Bob", "Charlie"],
            "ages": [25, 30, 35],
            "active": [True, False, True],
        }

        table = self.formatter._create_data_table(data, "User Data")

        assert isinstance(table, Table)
        assert table.title == "User Data (3 rows)"
        assert len(table.columns) == 3

    @patch("mcp_template.core.response_formatter.console")
    def test_beautify_json_key_value(self, mock_console):
        """Test beautify_json with key-value data."""
        data = {"name": "test", "version": "1.0", "active": True}

        # Mock the formatter's instance console as well
        with patch.object(self.formatter, "console") as mock_instance_console:
            self.formatter.beautify_json(data, "Test Data")
            # Either the global console or the instance console should be called
            assert mock_console.print.called or mock_instance_console.print.called

    @patch("mcp_template.core.response_formatter.console")
    def test_beautify_json_table(self, mock_console):
        """Test beautify_json with tabular data."""
        data = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]

        with patch.object(self.formatter, "console") as mock_instance_console:
            self.formatter.beautify_json(data, "User Data")
            assert mock_console.print.called or mock_instance_console.print.called

    @patch("mcp_template.core.response_formatter.console")
    def test_beautify_json_empty(self, mock_console):
        """Test beautify_json with empty collection."""
        data = []

        with patch.object(self.formatter, "console") as mock_instance_console:
            self.formatter.beautify_json(data, "Empty Data")
            assert mock_console.print.called or mock_instance_console.print.called

    @patch("mcp_template.core.response_formatter.console")
    def test_beautify_json_text(self, mock_console):
        """Test beautify_json with plain text."""
        data = "This is plain text"

        with patch.object(self.formatter, "console") as mock_instance_console:
            self.formatter.beautify_json(data, "Text Data")
            assert mock_console.print.called or mock_instance_console.print.called


class TestBackendIndicators:
    """Test backend visual indicator functions."""

    def test_get_backend_color(self):
        """Test backend color mapping."""
        assert get_backend_color("docker") == "blue"
        assert get_backend_color("kubernetes") == "green"
        assert get_backend_color("mock") == "yellow"
        assert get_backend_color("unknown") == "dim"
        assert get_backend_color("invalid") == "dim"

    def test_get_backend_icon(self):
        """Test backend icon mapping."""
        assert get_backend_icon("docker") == "🐳"
        assert get_backend_icon("kubernetes") == "☸️"
        assert get_backend_icon("mock") == "🔧"
        assert get_backend_icon("unknown") == "❓"
        assert get_backend_icon("invalid") == "❓"

    def test_get_status_color(self):
        """Test status color mapping."""
        assert get_status_color("running") == "green"
        assert get_status_color("stopped") == "red"
        assert get_status_color("starting") == "yellow"
        assert get_status_color("error") == "bright_red"
        assert get_status_color("unknown") == "dim"
        assert get_status_color("RUNNING") == "green"  # Case insensitive
        assert get_status_color(None) == "dim"

    def test_get_backend_indicator(self):
        """Test backend indicator formatting."""
        indicator = get_backend_indicator("docker")
        assert "🐳" in indicator
        assert "DOCKER" in indicator
        assert "[blue]" in indicator

        indicator_no_icon = get_backend_indicator("kubernetes", include_icon=False)
        assert "☸️" not in indicator_no_icon
        assert "KUBERNETES" in indicator_no_icon
        assert "[green]" in indicator_no_icon


class TestTimestampFormatting:
    """Test timestamp formatting functionality."""

    def test_format_timestamp_none(self):
        """Test formatting None timestamp."""
        assert format_timestamp(None) == "N/A"

    def test_format_timestamp_string_iso(self):
        """Test formatting ISO string timestamp."""
        timestamp = "2024-01-01T10:00:00Z"
        result = format_timestamp(timestamp)
        # Should return a relative time or absolute date
        assert result != "N/A"
        assert len(result) > 0

    def test_format_timestamp_string_invalid(self):
        """Test formatting invalid string timestamp."""
        timestamp = "invalid-timestamp"
        result = format_timestamp(timestamp)
        assert result == "invalid-timestamp"

    def test_format_timestamp_datetime_recent(self):
        """Test formatting recent datetime object."""
        now = datetime.datetime.now()
        recent = now - datetime.timedelta(minutes=5)
        result = format_timestamp(recent)
        assert "m ago" in result or "just now" in result

    def test_format_timestamp_datetime_hours_ago(self):
        """Test formatting datetime from hours ago."""
        now = datetime.datetime.now()
        hours_ago = now - datetime.timedelta(hours=3)
        result = format_timestamp(hours_ago)
        assert "h ago" in result

    def test_format_timestamp_datetime_days_ago(self):
        """Test formatting datetime from days ago."""
        now = datetime.datetime.now()
        days_ago = now - datetime.timedelta(days=2)
        result = format_timestamp(days_ago)
        assert "d ago" in result

    def test_format_timestamp_datetime_old(self):
        """Test formatting old datetime."""
        old_date = datetime.datetime(2023, 1, 1, 10, 0, 0)
        result = format_timestamp(old_date)
        assert "2023-01-01" in result


class TestDeploymentSummary:
    """Test deployment summary formatting."""

    def test_format_deployment_summary_empty(self):
        """Test summary with no deployments."""
        result = format_deployment_summary([])
        assert result == "No deployments"

    def test_format_deployment_summary_single_backend(self):
        """Test summary with deployments from single backend."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "running", "backend_type": "docker"},
        ]
        result = format_deployment_summary(deployments)
        assert "2 total" in result
        # No status breakdown for single status, no backend breakdown for single backend
        assert result == "2 total"

    def test_format_deployment_summary_multiple_backends(self):
        """Test summary with deployments from multiple backends."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "stopped", "backend_type": "docker"},
            {"id": "test-3", "status": "running", "backend_type": "kubernetes"},
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        assert "2 running" in result
        assert "2 docker" in result
        assert "1 kubernetes" in result

    def test_format_deployment_summary_mixed_statuses(self):
        """Test summary with mixed deployment statuses."""
        deployments = [
            {"id": "test-1", "status": "running", "backend_type": "docker"},
            {"id": "test-2", "status": "stopped", "backend_type": "docker"},
            {"id": "test-3", "status": "error", "backend_type": "docker"},
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        assert "1 running" in result


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_format_timestamp_string_truncation(self):
        """Test timestamp string truncation for long strings."""
        long_timestamp = "2024-01-01T10:00:00.123456789Z-very-long-suffix"
        result = format_timestamp(long_timestamp)
        # Should be truncated to 19 characters
        assert len(result) <= 19

    def test_get_backend_indicator_empty_string(self):
        """Test backend indicator with empty string."""
        indicator = get_backend_indicator("")
        assert "UNKNOWN" in indicator or "❓" in indicator

    def test_format_deployment_summary_missing_fields(self):
        """Test deployment summary with missing fields."""
        deployments = [
            {"id": "test-1"},  # Missing status and backend_type
            {"status": "running"},  # Missing backend_type
            {"backend_type": "docker"},  # Missing status
        ]
        result = format_deployment_summary(deployments)
        assert "3 total" in result
        # Should handle missing fields gracefully

    def test_backend_indicators_case_sensitivity(self):
        """Test that backend indicators work with different cases."""
        # Test uppercase
        assert get_backend_color("DOCKER") == "dim"  # Should default to dim for unknown
        assert get_backend_color("docker") == "blue"

        # Test mixed case
        assert get_backend_color("Docker") == "dim"
        assert get_backend_color("docker") == "blue"
