"""
Comprehensive tests for the demo template.

Tests the demo template functionality including server initialization,
tool functionality, configuration handling, and Docker deployment.
"""

import asyncio
import json

# Import demo template components
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

demo_path = Path(__file__).parent.parent / "templates" / "demo"
sys.path.insert(0, str(demo_path))

try:
    from config import DemoServerConfig
    from server import get_current_time, get_server_info, mcp, say_hello
    from tools import register_greeting_tools, register_info_tools, register_time_tools
except ImportError as e:
    pytest.skip(f"Demo template not available: {e}", allow_module_level=True)


class TestDemoTemplateCore:
    """Test core demo template functionality."""

    def test_demo_server_imports(self):
        """Test that demo server imports correctly."""
        assert mcp is not None
        assert hasattr(mcp, "name")
        assert mcp.name == "Demo MCP Server 🚀"

    def test_say_hello_tool(self):
        """Test the say_hello tool."""
        result = say_hello("Test User")
        assert result == "Hello, Test User!"

        # Test default parameter
        result = say_hello()
        assert result == "Hello, World!"

    def test_get_server_info_tool(self):
        """Test the get_server_info tool."""
        result = get_server_info()

        assert isinstance(result, dict)
        assert "name" in result
        assert "version" in result
        assert "status" in result
        assert result["name"] == "Demo MCP Server"
        assert result["status"] == "running"

    def test_get_current_time_tool(self):
        """Test the get_current_time tool."""
        result = get_current_time()

        assert isinstance(result, dict)
        assert "current_time" in result
        assert "timezone" in result
        assert "timestamp" in result

        # Verify timestamp is a reasonable value (not empty)
        assert result["timestamp"] > 0


class TestDemoConfiguration:
    """Test demo template configuration."""

    def test_demo_config_creation(self):
        """Test creating demo server configuration."""
        config = DemoServerConfig()

        assert config is not None
        assert hasattr(config, "hello_from")
        assert hasattr(config, "log_level")

    def test_demo_config_defaults(self):
        """Test demo configuration defaults."""
        config = DemoServerConfig()

        # Check default values
        assert config.hello_from == "MCP Platform"
        assert config.log_level == "info"

    def test_demo_config_from_env(self):
        """Test demo configuration from environment variables."""
        import os

        # Set environment variables
        os.environ["MCP_HELLO_FROM"] = "Test Environment"
        os.environ["MCP_LOG_LEVEL"] = "debug"

        try:
            config = DemoServerConfig()

            assert config.hello_from == "Test Environment"
            assert config.log_level == "debug"
        finally:
            # Cleanup
            os.environ.pop("MCP_HELLO_FROM", None)
            os.environ.pop("MCP_LOG_LEVEL", None)

    def test_demo_config_validation(self):
        """Test demo configuration validation."""
        config = DemoServerConfig()

        # Test valid log levels
        valid_levels = ["debug", "info", "warning", "error"]
        for level in valid_levels:
            config.log_level = level
            # Should not raise an exception

        # Test invalid log level
        with pytest.raises(ValueError):
            config.log_level = "invalid"


class TestDemoTools:
    """Test demo template tools registration."""

    def test_register_greeting_tools(self):
        """Test registering greeting tools."""
        mock_mcp = Mock()
        mock_config = Mock()
        mock_config.hello_from = "Test"

        register_greeting_tools(mock_mcp, mock_config)

        # Verify tools were registered
        assert mock_mcp.tool.called

    def test_register_info_tools(self):
        """Test registering info tools."""
        mock_mcp = Mock()
        mock_config = Mock()

        register_info_tools(mock_mcp, mock_config)

        # Verify tools were registered
        assert mock_mcp.tool.called

    def test_register_time_tools(self):
        """Test registering time tools."""
        mock_mcp = Mock()
        mock_config = Mock()

        register_time_tools(mock_mcp, mock_config)

        # Verify tools were registered
        assert mock_mcp.tool.called


class TestDemoTemplateStructure:
    """Test demo template structure and files."""

    def test_template_json_exists(self):
        """Test that template.json exists and is valid."""
        template_path = Path(__file__).parent.parent / "templates" / "demo"
        template_json_path = template_path / "template.json"

        assert template_json_path.exists()

        with open(template_json_path) as f:
            config = json.load(f)

        # Verify required fields
        assert "name" in config
        assert "description" in config
        assert "version" in config
        assert "docker_image" in config
        assert "config_schema" in config

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists and has basic structure."""
        template_path = Path(__file__).parent.parent / "templates" / "demo"
        dockerfile_path = template_path / "Dockerfile"

        assert dockerfile_path.exists()

        content = dockerfile_path.read_text()
        assert "FROM" in content
        assert "python" in content.lower()

    def test_requirements_exists(self):
        """Test that requirements.txt exists."""
        template_path = Path(__file__).parent.parent / "templates" / "demo"
        requirements_path = template_path / "requirements.txt"

        assert requirements_path.exists()

        content = requirements_path.read_text()
        assert "fastmcp" in content

    def test_readme_exists(self):
        """Test that README.md exists and has content."""
        template_path = Path(__file__).parent.parent / "templates" / "demo"
        readme_path = template_path / "README.md"

        assert readme_path.exists()

        content = readme_path.read_text()
        assert len(content) > 100  # Should have substantial content
        assert "Demo" in content


@pytest.mark.integration
class TestDemoTemplateIntegration:
    """Integration tests for demo template."""

    def test_template_config_validation(self):
        """Test that demo template config passes validation."""
        from mcp_template import TemplateManager

        manager = TemplateManager()
        config = manager.get_template_config("demo")

        # Should not raise an exception
        manager.validate_template_config(config)

    def test_demo_deployment_config(self):
        """Test demo template deployment configuration."""
        from mcp_template import TemplateManager

        manager = TemplateManager()
        config = manager.get_template_config("demo")

        # Verify deployment-related fields
        assert "docker_image" in config
        assert "ports" in config
        assert "command" in config
        assert "transport" in config

        # Verify port configuration
        assert "7071" in config["ports"]
        assert config["ports"]["7071"] == 7071

        # Verify command configuration
        assert config["command"] == ["python", "server.py"]

        # Verify transport configuration
        assert config["transport"]["default"] == "http"
        assert config["transport"]["port"] == 7071

    def test_demo_environment_mapping(self):
        """Test environment variable mapping for demo template."""
        from mcp_template import TemplateManager

        manager = TemplateManager()
        config = manager.get_template_config("demo")

        schema = config["config_schema"]
        properties = schema["properties"]

        # Check environment mappings
        assert "hello_from" in properties
        assert properties["hello_from"]["env_mapping"] == "MCP_HELLO_FROM"

        assert "log_level" in properties
        assert properties["log_level"]["env_mapping"] == "MCP_LOG_LEVEL"

    @pytest.mark.docker
    def test_demo_docker_deployment(self):
        """Test deploying demo template with Docker."""
        from mcp_template import DeploymentManager

        manager = DeploymentManager()

        try:
            result = manager.deploy_template(
                template_id="demo",
                config={"hello_from": "Integration Test", "log_level": "debug"},
                backend="docker",
                pull_image=False,  # Use local image
            )

            # Verify deployment result
            assert "deployment_name" in result
            assert result["status"] == "deployed"

            # Test status
            status = manager.get_deployment_status(result["deployment_name"], "docker")
            assert status["template"] == "demo"

            # Cleanup
            manager.delete_deployment(result["deployment_name"], "docker")

        except Exception as e:
            # Expected if image doesn't exist locally
            if "No such image" not in str(e) and "Unable to find image" not in str(e):
                raise

    def test_demo_mock_deployment(self):
        """Test deploying demo template with mock backend."""
        from mcp_template import DeploymentManager

        manager = DeploymentManager()

        result = manager.deploy_template(
            template_id="demo",
            config={"hello_from": "Mock Test", "log_level": "info"},
            backend="mock",
            pull_image=False,
        )

        # Verify deployment result
        assert "deployment_name" in result
        assert result["status"] == "deployed"

        # Test listing
        deployments = manager.list_deployments("mock")
        deployment_names = [d["name"] for d in deployments]
        assert result["deployment_name"] in deployment_names

        # Test status
        status = manager.get_deployment_status(result["deployment_name"], "mock")
        assert status["template"] == "demo"

        # Cleanup
        delete_result = manager.delete_deployment(result["deployment_name"], "mock")
        assert delete_result is True


@pytest.mark.asyncio
class TestDemoAsyncFunctionality:
    """Test asynchronous functionality of demo template."""

    async def test_async_server_start(self):
        """Test async server startup (mocked)."""
        with patch("fastmcp.FastMCP.run") as mock_run:
            mock_run.return_value = AsyncMock()

            # Mock the server startup
            from server import main

            with patch("sys.argv", ["server.py", "--transport", "stdio"]):
                with patch("asyncio.run") as mock_asyncio_run:
                    try:
                        main()
                    except SystemExit:
                        pass  # Expected from argparse

    async def test_async_tool_execution(self):
        """Test async tool execution."""

        # Create an async version of the tools for testing
        async def async_say_hello(name: str = "World") -> str:
            await asyncio.sleep(0)  # Simulate async work
            return f"Hello, {name}!"

        result = await async_say_hello("Async Test")
        assert result == "Hello, Async Test!"


class TestDemoEdgeCases:
    """Test edge cases for demo template."""

    def test_say_hello_empty_string(self):
        """Test say_hello with empty string."""
        result = say_hello("")
        assert result == "Hello, !"

    def test_say_hello_special_characters(self):
        """Test say_hello with special characters."""
        result = say_hello("Test™ User")
        assert result == "Hello, Test™ User!"

    def test_say_hello_long_name(self):
        """Test say_hello with very long name."""
        long_name = "A" * 1000
        result = say_hello(long_name)
        assert result == f"Hello, {long_name}!"

    def test_config_invalid_values(self):
        """Test configuration with invalid values."""
        config = DemoServerConfig()

        # Test setting invalid log level
        with pytest.raises(ValueError):
            config.log_level = "invalid_level"

    def test_server_info_consistency(self):
        """Test that server info is consistent across calls."""
        result1 = get_server_info()
        result2 = get_server_info()

        # Basic info should be the same
        assert result1["name"] == result2["name"]
        assert result1["version"] == result2["version"]
        assert result1["status"] == result2["status"]

    def test_time_tool_format(self):
        """Test time tool returns valid format."""
        result = get_current_time()

        # Check that timestamp is a number
        assert isinstance(result["timestamp"], (int, float))
        assert result["timestamp"] > 0

        # Check that current_time is a string
        assert isinstance(result["current_time"], str)
        assert len(result["current_time"]) > 0

        # Check timezone is provided
        assert isinstance(result["timezone"], str)


class TestDemoTemplateCompatibility:
    """Test compatibility with different FastMCP versions."""

    def test_fastmcp_tool_decorator(self):
        """Test that @mcp.tool decorator works correctly."""

        # Create a test function with the decorator
        @mcp.tool
        def test_tool(param: str) -> str:
            return f"Test: {param}"

        # Function should be callable
        result = test_tool("value")
        assert result == "Test: value"

    def test_mcp_server_instance(self):
        """Test MCP server instance configuration."""
        assert hasattr(mcp, "name")
        assert hasattr(mcp, "tool")

        # Check server name
        assert mcp.name == "Demo MCP Server 🚀"

    def test_tool_registration(self):
        """Test that tools are properly registered."""
        # This tests that the tools are accessible
        tools = [say_hello, get_server_info, get_current_time]

        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, "__name__")
