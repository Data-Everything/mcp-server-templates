"""
Unit tests for ResponseBeautifier class.
"""

import json
import os
import sys
import unittest.mock as mock
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_path not in sys.path:
    sys.path.insert(0, project_path)

from mcp_template.cli.interactive_cli import ResponseBeautifier


@pytest.mark.unit
class TestResponseBeautifier:
    """Test ResponseBeautifier class methods."""

    @pytest.fixture
    def beautifier(self):
        """Create a ResponseBeautifier instance for testing."""
        with patch("mcp_template.cli.interactive_cli.Console"):
            return ResponseBeautifier()

    def test_init(self, beautifier):
        """Test ResponseBeautifier initialization."""
        assert beautifier is not None
        assert hasattr(beautifier, "console")

    def test_is_actual_error_empty(self, beautifier):
        """Test _is_actual_error with empty string."""
        assert not beautifier._is_actual_error("")
        assert not beautifier._is_actual_error(None)

    def test_is_actual_error_with_errors(self, beautifier):
        """Test _is_actual_error with actual error messages."""
        error_messages = [
            "Error: Connection failed",
            "Exception: Invalid input",
            "Traceback (most recent call last):",
            "Failed: Unable to connect",
            "Fatal error occurred",
            "Cannot access file",
            "Permission denied",
            "File not found",
            "Invalid syntax",
            "Connection refused",
            "Timeout occurred",
        ]

        for msg in error_messages:
            assert beautifier._is_actual_error(msg), f"Should detect error: {msg}"

    def test_is_actual_error_with_info_messages(self, beautifier):
        """Test _is_actual_error with informational messages."""
        info_messages = [
            "Running on stdio",
            "Server started successfully",
            "Listening on port 8080",
            "Connected to database",
            "Initialized successfully",
            "Ready for requests",
            "Starting application",
            "Loading configuration",
            "Loaded 5 modules",
            "Using default settings",
            "Found 10 items",
        ]

        for msg in info_messages:
            assert not beautifier._is_actual_error(
                msg
            ), f"Should not detect as error: {msg}"

    def test_analyze_data_types_dict(self, beautifier):
        """Test _analyze_data_types with dictionary."""
        data = {"name": "test", "count": 5, "active": True}
        result = beautifier._analyze_data_types(data)

        assert result["primary_type"] == "dict"
        assert result["size"] == 3
        assert result["complexity"] == "simple"
        assert result["best_display"] == "key_value"

    def test_analyze_data_types_list(self, beautifier):
        """Test _analyze_data_types with list."""
        data = ["item1", "item2", "item3"]
        result = beautifier._analyze_data_types(data)

        assert result["primary_type"] == "list"
        assert result["size"] == 3
        assert result["is_homogeneous"] is True
        assert result["best_display"] == "list"

    def test_analyze_data_types_list_of_dicts(self, beautifier):
        """Test _analyze_data_types with list of dictionaries."""
        data = [{"name": "item1", "value": 1}, {"name": "item2", "value": 2}]
        result = beautifier._analyze_data_types(data)

        assert result["primary_type"] == "list"
        assert result["is_homogeneous"] is True
        assert result["best_display"] == "table"
        assert result["complexity"] == "tabular"

    def test_detect_data_structure(self, beautifier):
        """Test _detect_data_structure method."""
        # Simple dict
        assert beautifier._detect_data_structure({"key": "value"}) == "key_value"

        # List
        assert beautifier._detect_data_structure(["a", "b", "c"]) == "list"

        # Empty list
        assert beautifier._detect_data_structure([]) == "empty"

    def test_is_tabular_dict(self, beautifier):
        """Test _is_tabular_dict method."""
        # Tabular dict - columns with equal length arrays
        tabular = {
            "name": ["Alice", "Bob", "Charlie"],
            "age": [25, 30, 35],
            "city": ["NYC", "LA", "Chicago"],
        }
        assert beautifier._is_tabular_dict(tabular) is True

        # Non-tabular dict
        non_tabular = {"name": "Alice", "age": 25, "settings": {"theme": "dark"}}
        assert beautifier._is_tabular_dict(non_tabular) is False

        # Different length arrays
        different_lengths = {
            "name": ["Alice", "Bob"],
            "age": [25, 30, 35],  # Different length
        }
        assert beautifier._is_tabular_dict(different_lengths) is False

    def test_has_consistent_keys(self, beautifier):
        """Test _has_consistent_keys method."""
        # Consistent keys
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 35},
        ]
        assert beautifier._has_consistent_keys(data) is True

        # Inconsistent keys
        inconsistent = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "height": 180},  # Different key
        ]
        assert beautifier._has_consistent_keys(inconsistent) is False

        # Empty list
        assert beautifier._has_consistent_keys([]) is False

        # Non-dict items
        non_dict = ["string1", "string2"]
        assert beautifier._has_consistent_keys(non_dict) is False

    def test_create_key_value_table(self, beautifier):
        """Test _create_key_value_table method."""
        data = {
            "name": "Test Project",
            "version": 1.5,
            "active": True,
            "tags": ["python", "testing"],
            "metadata": {"created": "2024-01-01"},
        }

        result = beautifier._create_key_value_table(data, "Test Data")

        # Verify it returns a Table object
        assert result is not None
        # Check that it's a rich Table object by accessing its title
        assert hasattr(result, "title")
        assert "Test Data" in str(result.title)

    def test_create_data_table_list_of_dicts(self, beautifier):
        """Test _create_data_table with list of dictionaries."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
        ]

        result = beautifier._create_data_table(data, "Users")

        # Verify it returns a Table object
        assert result is not None
        assert hasattr(result, "title")
        assert "Users" in str(result.title)

    def test_create_data_table_tabular_dict(self, beautifier):
        """Test _create_data_table with tabular dictionary."""
        data = {"names": ["Alice", "Bob"], "ages": [25, 30], "cities": ["NYC", "LA"]}

        result = beautifier._create_data_table(data, "People")

        # Verify it returns a Table object (converted from tabular dict)
        assert result is not None
        assert hasattr(result, "title")
        assert "People" in str(result.title)

    def test_create_data_table_invalid_data(self, beautifier):
        """Test _create_data_table with invalid data."""
        # Non-list, non-dict data
        result = beautifier._create_data_table("string", "Invalid")
        assert result is None

        # Empty list
        result = beautifier._create_data_table([], "Empty")
        assert result is None

        # List of non-dict items
        result = beautifier._create_data_table(["string1", "string2"], "Strings")
        assert result is None

    def test_create_list_display_simple(self, beautifier):
        """Test _create_list_display with simple list."""
        data = ["item1", "item2", "item3"]

        result = beautifier._create_list_display(data, "Items")

        # Should return a Columns object for small simple lists
        assert result is not None
        # Check that it's a rich Columns object
        from rich.columns import Columns

        assert isinstance(result, Columns)

    def test_create_list_display_large(self, beautifier):
        """Test _create_list_display with large list."""
        data = [f"item{i}" for i in range(25)]  # Large list

        result = beautifier._create_list_display(data, "Items")

        # Should return a Panel object for large lists
        assert result is not None
        from rich.panel import Panel

        assert isinstance(result, Panel)

    def test_beautify_json_simple_dict(self, beautifier):
        """Test beautify_json with simple dictionary."""
        data = {"name": "test", "value": 42}

        with patch.object(beautifier, "_create_key_value_table") as mock_create_table:
            with patch.object(beautifier.console, "print"):
                beautifier.beautify_json(data, "Test Data")

                mock_create_table.assert_called_once_with(data, "Test Data")

    def test_beautify_json_tools_list(self, beautifier):
        """Test beautify_json with MCP tools list."""
        data = {
            "tools": [
                {"name": "tool1", "description": "First tool"},
                {"name": "tool2", "description": "Second tool"},
            ]
        }

        with patch.object(beautifier, "beautify_tools_list") as mock_beautify_tools:
            beautifier.beautify_json(data, "Response")

            mock_beautify_tools.assert_called_once_with(
                data["tools"], "MCP Server Tools"
            )

    def test_beautify_json_empty_collection(self, beautifier):
        """Test beautify_json with empty collection."""
        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_json([], "Empty Data")

            mock_print.assert_called_with("[dim]Empty Data: Empty collection[/dim]")

    def test_beautify_tools_list_empty(self, beautifier):
        """Test beautify_tools_list with empty list."""
        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_tools_list([], "Template")

            mock_print.assert_called_with("[yellow]⚠️  No tools found[/yellow]")

    def test_beautify_tools_list_with_tools(self, beautifier):
        """Test beautify_tools_list with actual tools."""
        tools = [
            {
                "name": "search",
                "description": "Search for items",
                "parameters": {"properties": {"query": {"type": "string"}}},
                "category": "search",
            }
        ]

        # Just test that it doesn't raise an exception and prints something
        with patch.object(beautifier.console, "print") as mock_print:
            result = beautifier.beautify_tools_list(tools, "GitHub")

            # Should have printed the table
            assert mock_print.call_count >= 1

    def test_beautify_deployed_servers_empty(self, beautifier):
        """Test beautify_deployed_servers with empty list."""
        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_deployed_servers([])

            mock_print.assert_called_with(
                "[yellow]⚠️  No deployed servers found[/yellow]"
            )

    def test_beautify_deployed_servers_with_servers(self, beautifier):
        """Test beautify_deployed_servers with actual servers."""
        servers = [
            {
                "id": "1",
                "name": "github-server",
                "transport": "http",
                "status": "running",
                "endpoint": "http://localhost:8080",
                "ports": "8080:8080",
                "since": "2024-01-01 10:00:00",
                "tools": ["search", "create"],
            }
        ]

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_deployed_servers(servers)

            # Should have printed the table
            assert mock_print.call_count >= 1

    def test_beautify_tool_response_completed(self, beautifier):
        """Test beautify_tool_response with completed response."""
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"text": "{\\"data\\": \\"test\\"}"}]}}',
        }

        with patch.object(beautifier, "beautify_json") as mock_beautify_json:
            beautifier.beautify_tool_response(response)

            # Should call beautify_json with parsed content
            mock_beautify_json.assert_called_once()

    def test_beautify_tool_response_with_error(self, beautifier):
        """Test beautify_tool_response with error response."""
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "error": {"code": 404, "message": "Not found"}}',
        }

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_tool_response(response)

            # Should display error information
            assert mock_print.call_count == 1

            # Get the Panel object that was printed
            from rich.panel import Panel

            panel = mock_print.call_args_list[0][0][0]
            assert isinstance(panel, Panel)

            # Check panel properties
            assert panel.title == "Tool Error"
            assert panel.border_style == "red"

            # Check panel content contains error info
            assert "Error 404: Not found" in str(panel.renderable)

    def test_beautify_tool_response_failed(self, beautifier):
        """Test beautify_tool_response with failed execution."""
        response = {
            "status": "failed",
            "error": "Connection timeout",
            "stderr": "Unable to connect to server",
        }

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier.beautify_tool_response(response)

            # Should display error messages in Panels
            assert mock_print.call_count == 2  # Error and details

            # Verify that Panel objects are printed
            from rich.panel import Panel

            assert isinstance(mock_print.call_args_list[0][0][0], Panel)
            assert isinstance(mock_print.call_args_list[1][0][0], Panel)

            # Get the Panel objects that were printed
            panel1 = mock_print.call_args_list[0][0][0]
            panel2 = mock_print.call_args_list[1][0][0]

            # Check panel properties
            assert panel1.title == "Execution Error"
            assert panel1.border_style == "red"

            assert panel2.title == "Error Details"
            assert panel2.border_style == "red"

    def test_beautify_tool_response_parse_error(self, beautifier):
        """Test beautify_tool_response with parsing error."""
        response = {"status": "completed", "stdout": "invalid json output"}

        with patch.object(beautifier.console, "print") as mock_print:
            # Should fallback to raw output display
            beautifier.beautify_tool_response(response)

            # Should print some output
            assert mock_print.call_count >= 1

    def test_display_tree_structure(self, beautifier):
        """Test _display_tree_structure method."""
        data = {
            "user": {
                "name": "Alice",
                "settings": {"theme": "dark", "notifications": True},
            },
            "items": ["item1", "item2"],
        }

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier._display_tree_structure(data, "Config")

            # Should have printed the tree
            assert mock_print.call_count >= 1

    def test_display_json_syntax(self, beautifier):
        """Test _display_json_syntax method."""
        data = {"key": "value", "number": 42}

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier._display_json_syntax(data, "JSON Data")

            # Should have printed the syntax-highlighted JSON
            assert mock_print.call_count >= 1

    def test_display_json_syntax_with_string(self, beautifier):
        """Test _display_json_syntax with JSON string."""
        json_string = '{"key": "value", "number": 42}'

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier._display_json_syntax(json_string, "JSON String")

            # Should parse string and display as JSON
            assert mock_print.call_count >= 1

    def test_display_json_syntax_invalid_string(self, beautifier):
        """Test _display_json_syntax with invalid JSON string."""
        invalid_json = "not valid json"

        with patch.object(beautifier.console, "print") as mock_print:
            beautifier._display_json_syntax(invalid_json, "Invalid JSON")

            # Should display as text panel
            assert mock_print.call_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
