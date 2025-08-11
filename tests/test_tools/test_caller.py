"""
Unit tests for the enhanced ToolCaller.
"""

import json
from unittest.mock import Mock, patch

import pytest

from mcp_template.core.tool_caller import ToolCaller, ToolCallResult
from mcp_template.exceptions import ToolCallError


@pytest.mark.unit
class TestToolCaller:
    """Test cases for ToolCaller functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool_caller = ToolCaller(caller_type="client")

    def test_initialization(self):
        """Test ToolCaller initialization."""
        # Test default initialization
        tool_caller = ToolCaller()
        assert tool_caller.caller_type == "client"
        assert tool_caller.timeout == 30

        # Test custom initialization
        tool_caller = ToolCaller(caller_type="cli", timeout=60)
        assert tool_caller.caller_type == "cli"
        assert tool_caller.timeout == 60

    def test_validate_template_stdio_support(self):
        """Test template stdio support validation."""
        # Template with stdio support
        template_with_stdio = {
            "transport": {"default": "stdio", "supported": ["stdio", "http"]}
        }
        assert self.tool_caller.validate_template_stdio_support(template_with_stdio)

        # Template without stdio support
        template_without_stdio = {
            "transport": {"default": "http", "supported": ["http"]}
        }
        assert not self.tool_caller.validate_template_stdio_support(
            template_without_stdio
        )

        # Template with stdio in supported list
        template_stdio_supported = {
            "transport": {"default": "http", "supported": ["http", "stdio"]}
        }
        assert self.tool_caller.validate_template_stdio_support(
            template_stdio_supported
        )

    def test_call_tool_stdio_success(self):
        """Test successful tool call via stdio."""
        # Mock the docker service directly on the instance
        self.tool_caller.docker_service = Mock()
        self.tool_caller.docker_service.run_stdio_command.return_value = {
            "status": "completed",
            "stdout": '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "Hello World!"}], "isError": false}}',
            "stderr": "",
        }

        template_config = {"transport": {"supported": ["stdio"], "default": "stdio"}}

        result = self.tool_caller.call_tool_stdio(
            template_name="test",
            tool_name="test_tool",
            arguments={"message": "Hello"},
            template_config=template_config,
        )

        assert isinstance(result, ToolCallResult)
        assert result.success
        assert not result.is_error
        assert result.result is not None
        assert "content" in result.result

    def test_call_tool_stdio_error(self):
        """Test tool call error handling."""
        # Mock Docker execution failure
        self.tool_caller.docker_service = Mock()
        self.tool_caller.docker_service.run_stdio_command.return_value = {
            "status": "failed",
            "error": "Container execution failed",
            "stderr": "Error output",
        }

        template_config = {"transport": {"supported": ["stdio"], "default": "stdio"}}

        result = self.tool_caller.call_tool_stdio(
            template_name="test",
            tool_name="test_tool",
            arguments={"message": "Hello"},
            template_config=template_config,
        )

        assert isinstance(result, ToolCallResult)
        assert not result.success
        assert result.is_error
        assert result.error_message is not None

    def test_call_tool_stdio_unsupported_transport(self):
        """Test error when template doesn't support stdio."""
        template_config = {"transport": {"supported": ["http"], "default": "http"}}

        with pytest.raises(ToolCallError, match="does not support stdio transport"):
            self.tool_caller.call_tool_stdio(
                template_name="test",
                tool_name="test_tool",
                arguments={},
                template_config=template_config,
            )

    def test_extract_structured_content(self):
        """Test structured content extraction."""
        # Test simple text content
        content = [{"type": "text", "text": "Hello World"}]
        structured = self.tool_caller._extract_structured_content(content)
        assert structured == {"result": "Hello World"}

        # Test JSON content
        json_content = [
            {"type": "text", "text": '{"message": "Hello", "status": "ok"}'}
        ]
        structured = self.tool_caller._extract_structured_content(json_content)
        assert structured == {"message": "Hello", "status": "ok"}

        # Test multiple content items
        multi_content = [
            {"type": "text", "text": "Item 1"},
            {"type": "text", "text": "Item 2"},
        ]
        structured = self.tool_caller._extract_structured_content(multi_content)
        assert "item_0" in structured
        assert "item_1" in structured

        # Test empty content
        empty_content = []
        structured = self.tool_caller._extract_structured_content(empty_content)
        assert structured == {}


@pytest.mark.unit
class TestToolCallResult:
    """Test cases for ToolCallResult dataclass."""

    def test_tool_call_result_creation(self):
        """Test ToolCallResult creation and attributes."""
        # Test successful result
        result = ToolCallResult(
            success=True,
            result={"content": [{"type": "text", "text": "Success"}]},
            content=[{"type": "text", "text": "Success"}],
            is_error=False,
        )

        assert result.success
        assert not result.is_error
        assert result.result is not None
        assert result.content is not None
        assert result.error_message is None

        # Test error result
        error_result = ToolCallResult(
            success=False, is_error=True, error_message="Tool failed"
        )

        assert not error_result.success
        assert error_result.is_error
        assert error_result.error_message == "Tool failed"
        assert error_result.result is None


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
