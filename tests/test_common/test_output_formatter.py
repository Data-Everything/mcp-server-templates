"""
Unit tests for OutputFormatter.

Tests the Rich formatting utilities and console output
provided by the OutputFormatter common module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rich.console import Console
from rich.table import Table
from io import StringIO

from mcp_template.common.output_formatter import OutputFormatter


@pytest.mark.unit
class TestOutputFormatter:
    """Unit tests for OutputFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Use a string buffer to capture output
        self.string_io = StringIO()
        self.console = Console(file=self.string_io, width=120, force_terminal=True)
        self.formatter = OutputFormatter(console=self.console)

    def test_format_templates_table_basic(self):
        """Test basic template table formatting."""
        templates = {
            "demo": {
                "description": "Demo template",
                "version": "1.0.0",
                "docker_image": "demo:latest"
            },
            "advanced": {
                "description": "Advanced template",
                "version": "2.0.0",
                "docker_image": "advanced:latest"
            }
        }
        
        table = self.formatter.format_templates_table(templates)
        
        assert isinstance(table, Table)
        # Check that the table has the expected columns
        column_headers = [col.header for col in table.columns]
        assert "Template" in column_headers
        assert "Description" in column_headers
        assert "Version" in column_headers
        assert "Docker Image" in column_headers

    def test_format_templates_table_with_deployment_status(self):
        """Test template table formatting with deployment status."""
        templates = {
            "demo": {
                "description": "Demo template",
                "version": "1.0.0",
                "docker_image": "demo:latest",
                "deployed": True,
                "deployment_count": 2
            }
        }
        
        table = self.formatter.format_templates_table(templates, show_deployed=True)
        
        column_headers = [col.header for col in table.columns]
        assert "Status" in column_headers
        assert "Deployments" in column_headers

    def test_format_templates_table_empty(self):
        """Test template table formatting with empty dict."""
        table = self.formatter.format_templates_table({})
        
        assert isinstance(table, Table)
        assert len(table.rows) == 0

    def test_format_templates_table_missing_fields(self):
        """Test template table with missing optional fields."""
        templates = {
            "minimal": {
                "description": "Minimal template"
                # Missing version, docker_image
            }
        }
        
        table = self.formatter.format_templates_table(templates)
        
        assert isinstance(table, Table)
        assert len(table.rows) == 1

    def test_format_tools_table_basic(self):
        """Test basic tools table formatting."""
        tools = [
            {
                "name": "say_hello",
                "description": "Say hello to someone",
                "source": "static",
                "parameters": [
                    {"name": "name", "type": "string", "required": True, "description": "Name to greet"}
                ]
            },
            {
                "name": "get_weather",
                "description": "Get weather information", 
                "source": "dynamic",
                "parameters": [
                    {"name": "location", "type": "string", "required": True, "description": "Location"},
                    {"name": "units", "type": "string", "required": False, "description": "Temperature units"}
                ]
            }
        ]
        
        table = self.formatter.format_tools_table(tools)
        
        assert isinstance(table, Table)
        column_headers = [col.header for col in table.columns]
        assert "Tool Name" in column_headers
        assert "Description" in column_headers
        assert "Parameters" in column_headers
        assert "Source" in column_headers

    def test_format_tools_table_simple(self):
        """Test tools table formatting with simple tools."""
        tools = [
            {
                "name": "test_tool",
                "description": "Test tool",
                "parameters": []
            }
        ]
        
        table = self.formatter.format_tools_table(tools)
        
        column_headers = [col.header for col in table.columns]
        assert "Tool Name" in column_headers

    def test_format_tools_table_empty(self):
        """Test tools table formatting with empty list."""
        table = self.formatter.format_tools_table([])
        
        assert isinstance(table, Table)
        assert len(table.rows) == 0

    def test_format_tools_table_no_parameters(self):
        """Test tools table with tools that have no parameters."""
        tools = [
            {
                "name": "simple_tool",
                "description": "Tool with no parameters",
                "source": "static"
                # No parameters field
            }
        ]
        
        table = self.formatter.format_tools_table(tools)
        
        assert isinstance(table, Table)
        assert len(table.rows) == 1

    def test_format_deployment_result_success(self):
        """Test deployment result formatting for success."""
        result = {
            "success": True,
            "template": "demo",
            "deployment_id": "demo-123",
            "container_id": "container-abc",
            "image": "demo:latest",
            "status": "running",
            "endpoint": "http://localhost:7071",
            "transport": "http"
        }
        
        panel = self.formatter.format_deployment_result(result)
        
        assert isinstance(panel, Panel)
        assert "🎉 Deployment Complete" in str(panel.renderable)

    def test_format_deployment_result_failure(self):
        """Test deployment result formatting for failure."""
        result = {
            "success": False,
            "error": "Container failed to start"
        }
        
        panel = self.formatter.format_deployment_result(result)
        
        assert isinstance(panel, Panel)
        assert "❌ Deployment Failed" in str(panel.renderable)

    def test_format_logs_output(self):
        """Test log formatting output."""
        logs = "2024-01-01 12:00:00 [INFO] Starting server...\n2024-01-01 12:00:01 [DEBUG] Loading configuration\n2024-01-01 12:00:02 [ERROR] Failed to connect to database\n2024-01-01 12:00:03 [INFO] Server started successfully"
        
        formatted = self.formatter.format_logs(logs)
        
        assert "Starting server" in formatted
        assert "Failed to connect" in formatted

    def test_format_logs_empty(self):
        """Test log formatting with empty logs."""
        formatted = self.formatter.format_logs("")
        
        assert "No logs available" in formatted

    def test_format_logs_with_highlighting(self):
        """Test log formatting with syntax highlighting."""
        logs = "[INFO]: Server started\n[ERROR]: Connection failed\n[WARNING]: Memory usage high\n[DEBUG]: Processing request"
        
        formatted = self.formatter.format_logs(logs, colorize=True)
        
        # Check that logs were processed
        assert "Server started" in formatted
        assert "Connection failed" in formatted

    def test_format_logs_no_highlighting(self):
        """Test log formatting without syntax highlighting."""
        logs = "[INFO]: Server started\n[ERROR]: Connection failed"
        
        formatted = self.formatter.format_logs(logs, colorize=False)
        
        # Should be unchanged when no colorization
        assert formatted == logs

    def test_format_json_output(self):
        """Test JSON formatting output."""
        data = {
            "name": "test_template",
            "version": "1.0.0",
            "config": {
                "port": 8080,
                "debug": True
            },
            "tools": ["tool1", "tool2"]
        }
        
        formatted = self.formatter.format_json(data)
        
        assert "test_template" in formatted
        assert "1.0.0" in formatted
        assert formatted.startswith('{')

    def test_print_success_message(self):
        """Test success message printing."""
        message = "Template deployed successfully!"
        
        self.formatter.print_success(message)
        
        output = self.string_io.getvalue()
        assert message in output
        # Check for success styling (green checkmark)
        assert "✅" in output

    def test_print_error_message(self):
        """Test error message printing."""
        message = "Failed to deploy template"
        
        self.formatter.print_error(message)
        
        output = self.string_io.getvalue()
        assert message in output
        # Check for error styling (red X)
        assert "❌" in output

    def test_print_warning_message(self):
        """Test warning message printing."""
        message = "Template configuration may be outdated"
        
        self.formatter.print_warning(message)
        
        output = self.string_io.getvalue()
        assert message in output
        # Check for warning styling
        assert "⚠️" in output

    def test_print_info_message(self):
        """Test info message printing."""
        message = "Loading template configuration..."
        
        self.formatter.print_info(message)
        
        output = self.string_io.getvalue()
        assert message in output
        assert "ℹ️" in output

    def test_print_panel_functionality(self):
        """Test panel printing functionality."""
        content = "Test panel content"
        title = "Test Panel"
        
        self.formatter.print_panel(content, title=title, style="blue")
        
        output = self.string_io.getvalue()
        assert content in output

    def test_print_table_functionality(self):
        """Test table printing functionality."""
        templates = {
            "demo": {
                "description": "Demo template",
                "version": "1.0.0",
                "docker_image": "demo:latest"
            }
        }
        
        table = self.formatter.format_templates_table(templates)
        self.formatter.print_table(table)
        
        output = self.string_io.getvalue()
        assert "demo" in output


@pytest.mark.integration
class TestOutputFormatterIntegration:
    """Integration tests for OutputFormatter."""

    def test_console_initialization(self):
        """Test that OutputFormatter can initialize its own console."""
        formatter = OutputFormatter()
        assert formatter.console is not None
        assert isinstance(formatter.console, Console)

    def test_end_to_end_table_rendering(self):
        """Test complete table rendering process."""
        string_io = StringIO()
        console = Console(file=string_io, width=120)
        formatter = OutputFormatter(console=console)
        
        templates = {
            "demo": {
                "description": "Demo template for testing",
                "version": "1.0.0",
                "docker_image": "demo:latest"
            }
        }
        
        table = formatter.format_templates_table(templates)
        console.print(table)
        
        output = string_io.getvalue()
        assert "demo" in output
        assert "Demo template" in output

    def test_mixed_output_formatting(self):
        """Test mixing different output types."""
        string_io = StringIO()
        console = Console(file=string_io, width=120)
        formatter = OutputFormatter(console=console)
        
        # Mix different output types
        formatter.print_info("Starting operation...")
        
        # Create and print a table
        templates = {"test": {"description": "Test template", "version": "1.0.0", "docker_image": "test:latest"}}
        table = formatter.format_templates_table(templates)
        console.print(table)
        
        formatter.print_success("Operation completed!")
        
        output = string_io.getvalue()
        assert "Starting operation" in output
        assert "test" in output
        assert "Operation completed" in output

    def test_formatter_with_real_rich_features(self):
        """Test formatter using actual Rich features."""
        formatter = OutputFormatter()
        
        # Should not raise exceptions with real Rich console
        formatter.print_info("Test message")
        formatter.print_success("Success message")
        formatter.print_error("Error message")
        formatter.print_warning("Warning message")
