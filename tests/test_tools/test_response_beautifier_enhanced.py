"""
Tests for enhanced response beautifier functionality.
"""

from unittest.mock import Mock, patch

import pytest
from rich.console import Console

from mcp_template.interactive_cli import ResponseBeautifier


@pytest.mark.unit
class TestResponseBeautifierEnhancements:
    """Test enhanced response beautifier functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.beautifier = ResponseBeautifier()

    def test_beautify_tool_response_with_newline_fix(self):
        """Test that response beautification properly handles newlines in output."""
        # Mock the console to capture output
        with patch.object(self.beautifier, 'console') as mock_console:
            # Simulate stdout with multiple JSON-RPC messages
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Hello World!"}],"isError":false}}',
                "stderr": "INFO: Server started\nINFO: Processing request"
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should have called print for both tool result and stderr
            assert mock_console.print.call_count >= 2

            # Check that tool result was extracted correctly
            calls = mock_console.print.call_args_list
            tool_result_call = None
            stderr_call = None

            for call in calls:
                panel = call[0][0]  # First argument to print should be a Panel
                if hasattr(panel, 'title') and panel.title == "Tool Result 1":
                    tool_result_call = call
                elif hasattr(panel, 'title') and panel.title == "Standard Error":
                    stderr_call = call

            assert tool_result_call is not None, "Tool result should be displayed"
            assert stderr_call is not None, "Standard error should be displayed"

    def test_beautify_tool_response_multiple_content_items(self):
        """Test handling of multiple content items in MCP response."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"First item"},{"type":"text","text":"Second item"}],"isError":false}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should display multiple tool results
            calls = mock_console.print.call_args_list
            tool_result_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'title') and call[0][0].title.startswith("Tool Result")
            ]
            
            assert len(tool_result_calls) >= 2

    def test_beautify_tool_response_with_error(self):
        """Test handling of error responses in MCP format."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":3,"error":{"code":-32603,"message":"Internal error during tool execution"}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            calls = mock_console.print.call_args_list
            # Should display with red border for error
            error_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'border_style') and call[0][0].border_style == "red"
            ]
            
            assert len(error_calls) >= 1

    def test_beautify_tool_response_structured_content(self):
        """Test handling of structured content in MCP responses."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Simple text"}],"structuredContent":{"result":"Structured result","metadata":"Extra info"},"isError":false}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should display the text content
            calls = mock_console.print.call_args_list
            assert any(
                hasattr(call[0][0], 'title') and call[0][0].title.startswith("Tool Result")
                for call in calls
            )

    def test_beautify_json_with_syntax_highlighting(self):
        """Test JSON beautification with syntax highlighting."""
        with patch.object(self.beautifier, 'console') as mock_console:
            json_data = {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {"type": "object", "properties": {"param1": {"type": "string"}}}
            }

            self.beautifier.beautify_json(json_data, "Test JSON")

            # Should have called print with Panel containing Syntax
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert hasattr(call_args, 'title')
            assert call_args.title == "Test JSON"

    def test_beautify_json_with_invalid_json_string(self):
        """Test handling of invalid JSON strings."""
        with patch.object(self.beautifier, 'console') as mock_console:
            invalid_json = "This is not JSON"

            self.beautifier.beautify_json(invalid_json, "Invalid JSON")

            # Should display as text panel instead of JSON
            mock_console.print.assert_called_once()
            call_args = mock_console.print.call_args[0][0]
            assert hasattr(call_args, 'title')
            assert call_args.title == "Invalid JSON"
            assert hasattr(call_args, 'border_style')
            assert call_args.border_style == "blue"

    def test_beautify_tool_response_fallback_to_raw_output(self):
        """Test fallback to raw output when no valid JSON is found."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": "No JSON here, just plain text output",
                "stderr": "Some error messages"
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should display raw output
            calls = mock_console.print.call_args_list
            raw_output_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'title') and call[0][0].title == "Raw Output"
            ]
            
            assert len(raw_output_calls) >= 1

    def test_beautify_tool_response_no_stderr(self):
        """Test handling when there's no stderr output."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Hello World!"}],"isError":false}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should not display stderr panel
            calls = mock_console.print.call_args_list
            stderr_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'title') and call[0][0].title == "Standard Error"
            ]
            
            assert len(stderr_calls) == 0

    def test_beautify_tool_response_mixed_json_and_text(self):
        """Test handling of mixed JSON and text in stdout."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": 'Starting server...\n{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\nServer ready\n{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Hello World!"}],"isError":false}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should find and display the tool response despite non-JSON lines
            calls = mock_console.print.call_args_list
            tool_result_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'title') and call[0][0].title.startswith("Tool Result")
            ]
            
            assert len(tool_result_calls) >= 1

    def test_beautify_tool_response_with_initialization_response(self):
        """Test proper handling of MCP initialization responses."""
        with patch.object(self.beautifier, 'console') as mock_console:
            response_data = {
                "status": "completed",
                "stdout": '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{"listChanged":true}},"serverInfo":{"name":"test-server"}}}\n{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Tool executed successfully"}],"isError":false}}',
                "stderr": ""
            }

            self.beautifier.beautify_tool_response(response_data)

            # Should display the tool result (id=3), not the initialization (id=1)
            calls = mock_console.print.call_args_list
            tool_result_calls = [
                call for call in calls 
                if hasattr(call[0][0], 'title') and call[0][0].title.startswith("Tool Result")
            ]
            
            assert len(tool_result_calls) >= 1

    def test_console_initialization(self):
        """Test that the console is properly initialized."""
        beautifier = ResponseBeautifier()
        assert isinstance(beautifier.console, Console)


@pytest.mark.integration  
class TestResponseBeautifierIntegration:
    """Integration tests for response beautifier with real data."""

    def setup_method(self):
        """Set up integration test environment."""
        self.beautifier = ResponseBeautifier()

    def test_beautify_real_demo_server_response(self):
        """Test beautification with real demo server response format."""
        # Based on actual demo server output format
        real_response = {
            "status": "completed", 
            "stdout": '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":true}},"serverInfo":{"name":"Demo Hello MCP Server","version":"1.0.0"},"instructions":"Demo server showing config patterns"}}\n{"jsonrpc":"2.0","id":3,"result":{"content":[{"type":"text","text":"Hello World! Greetings from \\"MCP Platform\\"!"}],"structuredContent":{"result":"Hello World! Greetings from \\"MCP Platform\\"!"},"isError":false}}',
            "stderr": "INFO:config:Demo server configuration loaded\nINFO:__main__:Demo MCP server Demo Hello MCP Server created\nINFO:__main__:Tools registered with MCP server\n\n\n╭─ FastMCP 2.0 ──────────────────────────────────────────────────────────────╮\n│                                                                            │\n│        _ __ ___ ______           __  __  _____________    ____    ____     │\n│       _ __ ___ / ____/___ ______/ /_/  |/  / ____/ __ \\  |___ \\  / __ \\    │\n│      _ __ ___ / /_  / __ `/ ___/ __/ /|_/ / /   / /_/ /  ___/ / / / / /    │\n│     _ __ ___ / __/ / /_/ (__  ) /_/ /  / / /___/ ____/  /  __/_/ /_/ /     │\n│    _ __ ___ /_/    \\__,_/____/\\__/_/  /_/\\____/_/      /_____(_)____/      │\n│                                                                            │\n│                                                                            │\n│                                                                            │\n│    🖥️  Server name:     Demo Hello MCP Server                               │\n│    📦 Transport:       STDIO                                               │\n│                                                                            │\n│    📚 Docs:            https://gofastmcp.com                               │\n│    🚀 Deploy:          https://fastmcp.cloud                               │\n│                                                                            │\n│    🏎️  FastMCP version: 2.11.1                                              │\n│    🤝 MCP version:     1.12.3                                              │\n│                                                                            │\n│╰────────────────────────────────────────────────────────────────────────────╯\n\n\n[08/05/25 04:51:29] INFO     Starting MCP server 'Demo Hello MCP  server.py:1442\n                             Server' with transport 'stdio'\nINFO:mcp.server.lowlevel.server:Processing request of type CallToolRequest"
        }

        # Should not raise any exceptions
        with patch.object(self.beautifier, 'console'):
            self.beautifier.beautify_tool_response(real_response)

        # Test passes if no exception is raised
