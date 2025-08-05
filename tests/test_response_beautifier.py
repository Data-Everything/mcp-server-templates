"""
Tests for the ResponseBeautifier class and its generic data structure handling.
"""

import pytest
import json
from unittest.mock import Mock, patch
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.columns import Columns

from mcp_template.interactive_cli import ResponseBeautifier


@pytest.mark.unit
class TestResponseBeautifier:
    """Test cases for ResponseBeautifier class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.beautifier = ResponseBeautifier()

    def test_init(self):
        """Test ResponseBeautifier initialization."""
        assert isinstance(self.beautifier.console, Console)

    def test_is_actual_error(self):
        """Test error detection in stderr."""
        # Actual errors
        assert self.beautifier._is_actual_error("Error: something went wrong")
        assert self.beautifier._is_actual_error("Exception: failed to connect")
        assert self.beautifier._is_actual_error("Traceback (most recent call last):")
        assert self.beautifier._is_actual_error("FATAL: cannot start server")
        assert self.beautifier._is_actual_error("Permission denied")
        
        # Informational messages (not errors)
        assert not self.beautifier._is_actual_error("Server started successfully")
        assert not self.beautifier._is_actual_error("Running on stdio")
        assert not self.beautifier._is_actual_error("Connected to database")
        assert not self.beautifier._is_actual_error("Initialized properly")
        
        # Empty or None
        assert not self.beautifier._is_actual_error("")
        assert not self.beautifier._is_actual_error(None)

    def test_analyze_data_types_simple_dict(self):
        """Test data type analysis for simple dictionaries."""
        data = {"name": "test", "version": "1.0", "active": True}
        analysis = self.beautifier._analyze_data_types(data)
        
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
            "config": {"timeout": 30}
        }
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["primary_type"] == "dict"
        assert analysis["best_display"] == "tree"
        assert analysis["complexity"] == "nested"
        assert "hierarchical" in analysis["structure_hints"]

    def test_analyze_data_types_tabular_list(self):
        """Test data type analysis for tabular data (list of dicts)."""
        data = [
            {"id": 1, "name": "Alice", "active": True},
            {"id": 2, "name": "Bob", "active": False},
            {"id": 3, "name": "Charlie", "active": True}
        ]
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "table"
        assert analysis["complexity"] == "tabular"
        assert "record_list" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is True

    def test_analyze_data_types_simple_list(self):
        """Test data type analysis for simple lists."""
        data = ["apple", "banana", "cherry"]
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "list"
        assert analysis["complexity"] == "simple"
        assert "value_list" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is True

    def test_analyze_data_types_mixed_list(self):
        """Test data type analysis for mixed type lists."""
        data = ["text", 123, {"key": "value"}, True]
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["primary_type"] == "list"
        assert analysis["best_display"] == "json"
        assert analysis["complexity"] == "heterogeneous"
        assert "mixed_types" in analysis["structure_hints"]
        assert analysis["is_homogeneous"] is False

    def test_analyze_data_types_json_string(self):
        """Test data type analysis for JSON strings."""
        data = '{"name": "test", "value": 42}'
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["best_display"] == "key_value"
        assert "json_string" in analysis["structure_hints"]

    def test_analyze_data_types_plain_text(self):
        """Test data type analysis for plain text."""
        data = "This is just plain text"
        analysis = self.beautifier._analyze_data_types(data)
        
        assert analysis["best_display"] == "text"
        assert "plain_text" in analysis["structure_hints"]

    def test_detect_data_structure(self):
        """Test the detect data structure method."""
        # Simple dict
        assert self.beautifier._detect_data_structure({"a": 1, "b": 2}) == "key_value"
        
        # Complex dict
        complex_data = {"a": {"nested": True}, "b": [1, 2, 3]}
        assert self.beautifier._detect_data_structure(complex_data) == "tree"
        
        # List of dicts
        tabular = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert self.beautifier._detect_data_structure(tabular) == "table"
        
        # Simple list
        assert self.beautifier._detect_data_structure([1, 2, 3]) == "list"

    def test_is_tabular_dict(self):
        """Test tabular dictionary detection."""
        # Tabular dict
        tabular = {
            "names": ["Alice", "Bob", "Charlie"],
            "ages": [25, 30, 35],
            "active": [True, False, True]
        }
        assert self.beautifier._is_tabular_dict(tabular) is True
        
        # Non-tabular dict
        non_tabular = {"name": "test", "config": {"port": 8080}}
        assert self.beautifier._is_tabular_dict(non_tabular) is False
        
        # Mixed length lists (not tabular)
        mixed = {
            "names": ["Alice", "Bob"],
            "ages": [25, 30, 35]  # Different length
        }
        assert self.beautifier._is_tabular_dict(mixed) is False

    def test_has_consistent_keys(self):
        """Test consistent keys detection for list of dicts."""
        # Consistent keys
        consistent = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
            {"name": "Charlie", "age": 35}
        ]
        assert self.beautifier._has_consistent_keys(consistent) is True
        
        # Inconsistent keys
        inconsistent = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "score": 95},  # Different key
            {"title": "Charlie", "age": 35}  # Different key
        ]
        assert self.beautifier._has_consistent_keys(inconsistent) is False
        
        # Empty list
        assert self.beautifier._has_consistent_keys([]) is False
        
        # Non-dict items
        assert self.beautifier._has_consistent_keys(["a", "b", "c"]) is False

    @patch('mcp_template.interactive_cli.Console')
    def test_create_key_value_table(self, mock_console_class):
        """Test key-value table creation."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        # Create beautifier with mocked console
        beautifier = ResponseBeautifier()
        
        data = {
            "name": "test-server",
            "version": "1.0.0",
            "active": True,
            "port": 8080,
            "url": "https://example.com",
            "config": {"timeout": 30},
            "tags": ["python", "mcp"],
            "score": 95.567,
            "nullable": None
        }
        
        table = beautifier._create_key_value_table(data, "Test Data")
        
        assert isinstance(table, Table)
        assert table.title == "Test Data (9 properties)"
        # Verify table has correct number of columns
        assert len(table.columns) == 3  # Property, Value, Type

    @patch('mcp_template.interactive_cli.Console')
    def test_create_data_table(self, mock_console_class):
        """Test data table creation from list of dicts."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = [
            {"id": 1, "name": "Alice", "active": True, "score": 95.5, "url": "https://alice.example.com"},
            {"id": 2, "name": "Bob", "active": False, "score": 87.2, "url": "https://bob.example.com"},
            {"id": 3, "name": "Charlie", "active": True, "score": 92.8, "url": "https://charlie.example.com"}
        ]
        
        table = beautifier._create_data_table(data, "User Data")
        
        assert isinstance(table, Table)
        assert table.title == "User Data (3 rows)"
        # Should have 5 columns: id, name, active, score, url
        assert len(table.columns) == 5

    @patch('mcp_template.interactive_cli.Console')
    def test_create_data_table_tabular_dict(self, mock_console_class):
        """Test data table creation from tabular dictionary."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = {
            "names": ["Alice", "Bob", "Charlie"],
            "ages": [25, 30, 35],
            "active": [True, False, True]
        }
        
        table = beautifier._create_data_table(data, "User Data")
        
        assert isinstance(table, Table)
        assert table.title == "User Data (3 rows)"
        assert len(table.columns) == 3

    @patch('mcp_template.interactive_cli.Console')
    def test_create_list_display_simple(self, mock_console_class):
        """Test list display for simple values."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = ["apple", "banana", "cherry", "date"]
        
        display = beautifier._create_list_display(data, "Fruits")
        
        assert isinstance(display, Columns)

    @patch('mcp_template.interactive_cli.Console')
    def test_create_list_display_large(self, mock_console_class):
        """Test list display for large lists."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = [f"item_{i}" for i in range(25)]
        
        display = beautifier._create_list_display(data, "Items")
        
        assert isinstance(display, Panel)

    @patch('mcp_template.interactive_cli.Console')
    def test_display_tree_structure(self, mock_console_class):
        """Test tree structure display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = {
            "server": {
                "name": "test-server",
                "config": {
                    "port": 8080,
                    "timeout": 30
                }
            },
            "tools": ["search", "create", "update"],
            "active": True
        }
        
        # Should not raise an exception
        beautifier._display_tree_structure(data, "Server Config")
        
        # Verify console.print was called
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_display_json_syntax(self, mock_console_class):
        """Test JSON syntax display."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = {"name": "test", "value": 42}
        analysis = {"complexity": "simple", "size": 2, "structure_hints": ["simple_mapping"]}
        
        beautifier._display_json_syntax(data, "Test Data", analysis)
        
        # Verify console.print was called
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_display_json_syntax_string_input(self, mock_console_class):
        """Test JSON syntax display with string input."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = '{"name": "test", "value": 42}'
        
        beautifier._display_json_syntax(data, "Test Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_display_json_syntax_invalid_json_string(self, mock_console_class):
        """Test JSON syntax display with invalid JSON string."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = "This is not JSON"
        
        beautifier._display_json_syntax(data, "Test Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_key_value(self, mock_console_class):
        """Test beautify_json with key-value data."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = {"name": "test", "version": "1.0", "active": True}
        
        beautifier.beautify_json(data, "Test Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_table(self, mock_console_class):
        """Test beautify_json with tabular data."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"}
        ]
        
        beautifier.beautify_json(data, "User Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_tree(self, mock_console_class):
        """Test beautify_json with hierarchical data."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = {
            "server": {"name": "test", "port": 8080},
            "tools": ["search", "create"],
            "config": {"timeout": 30, "retries": 3}
        }
        
        beautifier.beautify_json(data, "Server Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_list(self, mock_console_class):
        """Test beautify_json with simple list."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = ["apple", "banana", "cherry"]
        
        beautifier.beautify_json(data, "Fruits")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_empty(self, mock_console_class):
        """Test beautify_json with empty collection."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = []
        
        beautifier.beautify_json(data, "Empty Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_text(self, mock_console_class):
        """Test beautify_json with plain text."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        data = "This is plain text"
        
        beautifier.beautify_json(data, "Text Data")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_tools_list(self, mock_console_class):
        """Test beautify_json with MCP tools list."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        # The current logic expects tools to be dict objects with "name"
        data = {
            "tools": [
                {"name": "search", "description": "Search function"},
                {"name": "create", "description": "Create function"}
            ]
        }
        
        with patch.object(beautifier, 'beautify_tools_list') as mock_beautify_tools:
            beautifier.beautify_json(data, "Tools Data")
            # The tools list should be called because tools[0] has "name"
            mock_beautify_tools.assert_called_once_with(
                [
                    {"name": "search", "description": "Search function"},
                    {"name": "create", "description": "Create function"}
                ],
                "MCP Server Tools"
            )

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_json_tools_list_names_only(self, mock_console_class):
        """Test beautify_json with tools list that contains only names."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        # Tools list with just names (not dicts with "name" key)
        data = {
            "tools": ["search", "create", "update"]
        }
        
        # This should NOT call beautify_tools_list, but use generic display
        with patch.object(beautifier, 'beautify_tools_list') as mock_beautify_tools:
            beautifier.beautify_json(data, "Tools Data")
            # Should not call beautify_tools_list
            mock_beautify_tools.assert_not_called()
            # Should call console.print instead
            mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tools_list(self, mock_console_class):
        """Test tools list beautification."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        tools = [
            {
                "name": "search",
                "description": "Search for items",
                "parameters": {
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {"type": "integer", "description": "Result limit"}
                    },
                    "required": ["query"]
                },
                "category": "query"
            },
            {
                "name": "create",
                "description": "Create new item",
                "inputSchema": {
                    "properties": {
                        "name": {"type": "string", "description": "Item name"}
                    },
                    "required": ["name"]
                },
                "category": "action"
            }
        ]
        
        beautifier.beautify_tools_list(tools, "Test Tools")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tools_list_empty(self, mock_console_class):
        """Test tools list beautification with empty list."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        tools = []
        
        beautifier.beautify_tools_list(tools, "Empty Tools")
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_deployed_servers(self, mock_console_class):
        """Test deployed servers beautification."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        servers = [
            {
                "template_name": "github",
                "transport": "stdio",
                "status": "running",
                "endpoint": "stdio://github-server",
                "tools": ["search_repositories", "get_repository"]
            },
            {
                "template_name": "demo",
                "transport": "http",
                "status": "failed",
                "endpoint": "http://localhost:8080",
                "tools": []
            }
        ]
        
        beautifier.beautify_deployed_servers(servers)
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_deployed_servers_empty(self, mock_console_class):
        """Test deployed servers beautification with empty list."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        servers = []
        
        beautifier.beautify_deployed_servers(servers)
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_completed(self, mock_console_class):
        """Test tool response beautification for completed execution."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"text": "{\\"name\\": \\"test\\", \\"value\\": 42}"}]}}',
            "stderr": ""
        }
        
        beautifier.beautify_tool_response(response)
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_structured_content(self, mock_console_class):
        """Test tool response beautification with structured content."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"structuredContent": {"name": "test", "value": 42}}}',
            "stderr": ""
        }
        
        with patch.object(beautifier, 'beautify_json') as mock_beautify:
            beautifier.beautify_tool_response(response)
            mock_beautify.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_error(self, mock_console_class):
        """Test tool response beautification with error."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "error": {"code": -1, "message": "Tool execution failed"}}',
            "stderr": ""
        }
        
        beautifier.beautify_tool_response(response)
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_failed(self, mock_console_class):
        """Test tool response beautification for failed execution."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "failed",
            "error": "Execution failed",
            "stderr": "Error details here"
        }
        
        beautifier.beautify_tool_response(response)
        
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_with_actual_stderr(self, mock_console_class):
        """Test tool response beautification with actual error in stderr."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"text": "success"}]}}',
            "stderr": "Error: something went wrong"
        }
        
        beautifier.beautify_tool_response(response)
        
        # Should print both result and error
        assert mock_console.print.call_count >= 2

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_with_info_stderr(self, mock_console_class):
        """Test tool response beautification with informational stderr."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"text": "success"}]}}',
            "stderr": "Server started successfully"
        }
        
        beautifier.beautify_tool_response(response)
        
        # Should not show the informational stderr unless verbose
        # (We can't easily test the verbose condition without setting it)
        mock_console.print.assert_called()

    @patch('mcp_template.interactive_cli.Console')
    def test_beautify_tool_response_parsing_error(self, mock_console_class):
        """Test tool response beautification with parsing error."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        beautifier = ResponseBeautifier()
        
        response = {
            "status": "completed",
            "stdout": "invalid json output",
            "stderr": ""
        }
        
        beautifier.beautify_tool_response(response)
        
        # Should handle parsing error gracefully and show raw output
        mock_console.print.assert_called()
