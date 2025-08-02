#!/usr/bin/env python3
"""
MCP Template Creator - CLI tool for creating new MCP server templates.

This tool creates a complete template structure with boilerplate code,
configuration files, tests, and documentation.
"""

import json
import re
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from mcp_template.utils import TEMPLATES_DIR, TESTS_DIR

console = Console()


class TemplateCreator:
    """Create new MCP server templates with complete structure."""

    def __init__(
        self, templates_dir: Optional[Path] = None, tests_dir: Optional[Path] = None
    ):
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.tests_dir = tests_dir or TESTS_DIR
        self.template_data = None
        self.template_dir = None

    def _create_config_py(self):
        """Create config.py for the template by loading demo config and adapting it."""
        # Load the demo config.py as a template
        demo_config_path = self.templates_dir.parent / "utils" / "config.py"
        with open(demo_config_path, "r", encoding="utf-8") as f:
            config_content = f.read()

        # Generate template-specific names
        config_class_name = (
            "".join(word.capitalize() for word in self.template_data["id"].split("-"))
            + "ServerConfig"
        )
        template_name = self.template_data["name"]
        template_id = self.template_data["id"]
        template_name_lower = template_name.lower()
        template_id_lower = template_id.lower()

        # Replace demo-specific references with template-specific ones
        replacements = {
            "DemoServerConfig": config_class_name,
            "Demo MCP Server": f"{template_name} MCP Server",
            "demo template": f"{template_name_lower} template",
            "demo server": f"{template_name_lower} server",
            "Demo server": f"{template_name} server",
            '"demo"': f'"{template_id_lower}"',
            "'demo'": f"'{template_id_lower}'",
            "demo_": f"{template_id_lower}_",
            '"Demo"': f'"{template_name}"',
            "'Demo'": f"'{template_name}'",
        }

        # Apply replacements
        for old_text, new_text in replacements.items():
            config_content = config_content.replace(old_text, new_text)

        # Write the adapted config file
        with open(self.template_dir / "config.py", "w", encoding="utf-8") as f:
            f.write(config_content)

    def _prompt_template_id(self) -> str:
        """Prompt for template ID with validation."""
        while True:
            template_id = Prompt.ask(
                "Enter template ID (use lowercase letters, numbers, and hyphens only)"
            )
            if self._validate_template_id(template_id):
                return template_id
            console.print(
                "[red]Invalid template ID. Use lowercase letters, numbers, and hyphens only.[/red]"
            )

    def _create_usage_md(self):
        """Create USAGE.md for the template."""
        capabilities = self.template_data.get("capabilities", [])
        config_properties = self.template_data.get("config_schema", {}).get(
            "properties", {}
        )

        usage_content = f"""# {self.template_data["name"]} Usage Guide

## Overview

{self.template_data["description"]}

## Installation

Deploy this template using the MCP platform:

```bash
mcp-template deploy {self.template_data["id"]}
```

## Tools Available

"""

        for capability in capabilities:
            tool_name = capability["name"].lower().replace(" ", "_").replace("-", "_")
            usage_content += f"""### {capability["name"]}

{capability["description"]}

**Usage**: `{tool_name}`

**Example**: {capability["example"]}

"""
            if capability.get("example_args"):
                usage_content += "**Parameters**:\n"
                for arg_name, arg_value in capability["example_args"].items():
                    usage_content += f"- `{arg_name}`: {type(arg_value).__name__}\n"
                usage_content += "\n"

        usage_content += """## Configuration

### Environment Variables

"""

        for param_name, param_config in config_properties.items():
            env_name = param_config.get("env_mapping", param_name.upper())
            required = (
                " (required)"
                if param_name
                in self.template_data.get("config_schema", {}).get("required", [])
                else ""
            )
            usage_content += (
                f"- `{env_name}`: {param_config['description']}{required}\n"
            )

        if not config_properties:
            usage_content += "- No environment variables required\n"

        usage_content += """

### Configuration File

You can also use a configuration file in JSON format:

```json
{
"""

        for param_name, param_config in config_properties.items():
            default_val = param_config.get("default", "null")
            if isinstance(default_val, str):
                default_val = f'"{default_val}"'
            usage_content += f'  "{param_name}": {default_val},\n'

        if config_properties:
            usage_content = usage_content.rstrip(",\n") + "\n"

        usage_content += """
}
```

## Examples

### Basic Usage

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_server():
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", [tool.name for tool in tools.tools])

            # Use a tool
            result = await session.call_tool("example_tool", {})
            print("Result:", result)
```

### Docker Usage

```bash
# Build and run
docker build -t {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")} .
docker run {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")}
```

## Troubleshooting

### Common Issues

1. **Configuration not loaded**: Check environment variables are set correctly
2. **Tool not found**: Verify the tool name matches exactly
3. **Connection failed**: Ensure the server is running and accessible

### Debug Mode

Set `DEBUG=1` environment variable for verbose logging.
"""

        with open(self.template_dir / "USAGE.md", "w", encoding="utf-8") as f:
            f.write(usage_content)

    def _create_docs_index(self):
        """Create docs/index.md for the template."""
        capabilities = self.template_data.get("capabilities", [])
        config_properties = self.template_data.get("config_schema", {}).get(
            "properties", {}
        )

        docs_content = f"""# {self.template_data["name"]} Documentation

## Overview

{self.template_data["description"]}

## Quick Start

### Installation

Deploy this template using the MCP platform:

```bash
mcp-template deploy {self.template_data["id"]}
```

### Configuration

"""

        if config_properties:
            docs_content += "This template requires the following configuration:\n\n"
            for param_name, param_config in config_properties.items():
                env_name = param_config.get("env_mapping", param_name.upper())
                required = (
                    " (required)"
                    if param_name
                    in self.template_data.get("config_schema", {}).get("required", [])
                    else ""
                )
                docs_content += (
                    f"- **{env_name}**: {param_config['description']}{required}\n"
                )
        else:
            docs_content += "No configuration required for this template.\n"

        docs_content += """

### Usage

"""

        for capability in capabilities:
            docs_content += f"""#### {capability["name"]}

{capability["description"]}

**Example**: {capability["example"]}

"""
            if capability.get("example_args"):
                docs_content += "**Parameters**:\n"
                for arg_name, arg_value in capability["example_args"].items():
                    docs_content += f"- `{arg_name}`: {type(arg_value).__name__}\n"
                docs_content += "\n"

        docs_content += """## API Reference

### Available Tools

"""

        for capability in capabilities:
            tool_name = capability["name"].lower().replace(" ", "_").replace("-", "_")
            docs_content += f"""#### `{tool_name}`

{capability["description"]}

**Response**: {capability.get("example_response", "Operation completed successfully")}

"""

        docs_content += f"""## Development

### Local Development

```bash
# Clone the template
git clone <repository-url>
cd {self.template_data["id"]}

# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/ -m "not integration"

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

### Docker

```bash
# Build the image
docker build -t {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")} .

# Run the container
docker run {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")}
```

## Troubleshooting

### Common Issues

1. **Server won't start**: Check that all required environment variables are set
2. **Tool not found**: Verify the MCP client is connected properly
3. **Permission errors**: Ensure the server has appropriate file system permissions

### Debug Mode

Enable debug logging by setting the `LOG_LEVEL` environment variable to `DEBUG`.

## Contributing

Contributions are welcome! Please see the main repository's contributing guidelines.

## License

This template is part of the MCP Server Templates project.

## Support

For support, please open an issue in the main repository or contact the maintainers.
"""

        with open(self.template_dir / "docs" / "index.md", "w", encoding="utf-8") as f:
            f.write(docs_content)

    def _create_test_structure(self):
        """Create test structure for the template."""
        test_dir = self.template_dir / "tests"

        # Create test files
        self._create_unit_tests(test_dir)
        self._create_integration_tests(test_dir)
        self._create_conftest(test_dir)

        # Create __init__.py for the test directory
        with open(test_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(f'"""\nTests for {self.template_data["name"]} template.\n"""\n')

    def _create_unit_tests(self, test_dir: Path):
        """Create unit tests for the template."""
        # Convert template name to valid Python identifier for class names
        class_name_base = (
            self.template_data["id"].replace("-", "_").title().replace("_", "")
        )
        test_file_prefix = self.template_data["id"].replace("-", "_")

        # Generate class names for f-strings
        class_name = (
            "".join(word.capitalize() for word in self.template_data["id"].split("-"))
            + "Server"
        )
        config_class_name = (
            "".join(word.capitalize() for word in self.template_data["id"].split("-"))
            + "ServerConfig"
        )

        test_content = f'''"""
Unit tests for {self.template_data["name"]} template.
"""

import pytest
from unittest.mock import Mock, patch

# Import the server module
import sys
sys.path.insert(0, str({repr(str(self.template_dir))}))

from server import {class_name}, {config_class_name}


class Test{class_name_base}Unit:
    """Unit tests for {self.template_data["name"]} template."""

    def test_config_loading(self):
        """Test configuration loading."""
        config = {config_class_name}()
        assert config is not None
        assert hasattr(config, 'template_data')
        assert hasattr(config, 'config_data')

    def test_server_initialization(self):
        """Test server initialization."""
        server = {class_name}()
        assert server is not None
        assert hasattr(server, 'app')
        assert hasattr(server, 'config')

    def test_template_data_loading(self):
        """Test template data loading."""
        server = {class_name}()
        template_data = server.template_data
        assert template_data is not None
        assert template_data.get("name") == "{self.template_data["name"]}"

'''

        # Add tests for each capability
        capabilities = self.template_data.get("capabilities", [])
        for capability in capabilities:
            tool_name = capability["name"].lower().replace(" ", "_").replace("-", "_")
            test_content += f'''
    def test_{tool_name}(self):
        """Test {capability["name"]} functionality."""
        # TODO: Implement unit test for {capability["name"]}
        pass
'''

        # Add default test if no capabilities
        if not capabilities:
            test_content += '''
    def test_hello(self):
        """Test hello tool functionality."""
        # TODO: Implement unit test for hello tool
        pass
'''

        with open(
            test_dir / f"test_{test_file_prefix}_unit.py", "w", encoding="utf-8"
        ) as f:
            f.write(test_content)

    def _create_integration_tests(self, test_dir: Path):
        """Create integration tests for the template."""
        class_name_base = (
            self.template_data["id"].replace("-", "_").title().replace("_", "")
        )
        test_file_prefix = self.template_data["id"].replace("-", "_")

        test_content = f'''"""
Integration tests for {self.template_data["name"]} template.
"""

import pytest
import pytest_asyncio
import asyncio
from pathlib import Path

# Import MCP testing utilities
import sys
sys.path.insert(0, str({repr(str(self.tests_dir.parent / "tests" / "utils"))}))

from mcp_test_utils import MCPTestClient


@pytest.mark.integration
@pytest.mark.asyncio
class Test{class_name_base}Integration:
    """Integration tests for {self.template_data["name"]} template."""

    @pytest_asyncio.fixture
    async def mcp_client(self):
        """Create MCP test client."""
        template_dir = Path({repr(str(self.template_dir))})
        client = MCPTestClient(template_dir / "server.py")
        await client.start()
        yield client
        await client.stop()

    async def test_server_connection(self, mcp_client):
        """Test MCP server connection."""
        tools = await mcp_client.list_tools()
        assert len(tools) >= 0  # Server should be accessible

'''

        # Add integration tests for each capability
        capabilities = self.template_data.get("capabilities", [])
        for capability in capabilities:
            tool_name = capability["name"].lower().replace(" ", "_").replace("-", "_")
            test_content += f'''
    async def test_{tool_name}_integration(self, mcp_client):
        """Test {capability["name"]} integration."""
        result = await mcp_client.call_tool("{tool_name}", {capability.get("example_args", {})})
        assert result is not None
        # TODO: Add specific assertions for {capability["name"]}
'''

        # Add default integration test if no capabilities
        if not capabilities:
            test_content += '''
    async def test_hello_integration(self, mcp_client):
        """Test hello tool integration."""
        result = await mcp_client.call_tool("hello", {})
        assert result is not None
        # TODO: Add specific assertions for hello tool
'''

        with open(
            test_dir / f"test_{test_file_prefix}_integration.py", "w", encoding="utf-8"
        ) as f:
            f.write(test_content)

    def _create_conftest(self, test_dir: Path):
        """Create conftest.py for pytest configuration."""
        conftest_content = f'''"""
Pytest configuration for {self.template_data["name"]} template tests.
"""

import pytest
import sys
from pathlib import Path

# Add template directory to Python path
template_dir = Path(__file__).parent.parent
sys.path.insert(0, str(template_dir))


@pytest.fixture(scope="session")
def template_config():
    """Load template configuration for tests."""
    import json

    config_file = template_dir / "template.json"
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
'''

        # Add environment variable mocking for config parameters
        config_properties = self.template_data.get("config_schema", {}).get(
            "properties", {}
        )
        for param_name, param_config in config_properties.items():
            env_name = param_config.get("env_mapping", param_name.upper())
            default_val = param_config.get("default", "test_value")
            if isinstance(default_val, str):
                default_val = f'"{default_val}"'
            conftest_content += f'    monkeypatch.setenv("{env_name}", {default_val})\n'

        # Add a pass statement if no environment variables
        if not config_properties:
            conftest_content += "    pass  # No environment variables to mock\n"

        with open(test_dir / "conftest.py", "w", encoding="utf-8") as f:
            f.write(conftest_content)

    def _validate_template_id(self, template_id: str) -> bool:
        """Validate template ID format."""
        return bool(re.match(r"^[a-z0-9-]+$", template_id))

    def create_template_interactive(
        self, template_id: str = None, config_file: str = None
    ) -> bool:
        """Create a template interactively."""
        try:
            if config_file:
                # Load from config file
                with open(config_file, "r", encoding="utf-8") as f:
                    if config_file.endswith(".yaml") or config_file.endswith(".yml"):
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)

                # Validate required fields
                required_fields = ["id", "name", "description", "version", "author"]
                for field in required_fields:
                    if field not in config_data:
                        console.print(
                            f"[red]❌ Missing required field in config: {field}[/red]"
                        )
                        return False

                # Use provided template_id or from config
                template_id = template_id or config_data["id"]
                self.template_data = config_data.copy()
                self.template_data["id"] = template_id
                self.template_dir = self.templates_dir / template_id
            else:
                # Interactive mode
                if not template_id:
                    template_id = self._prompt_template_id()

                self.template_dir = self.templates_dir / template_id
                self.template_data = {
                    "id": template_id,
                    "name": template_id.replace("-", " ").title(),
                    "description": f"MCP server template for {template_id}",
                    "version": "1.0.0",
                    "author": "Unknown",
                    "capabilities": [],
                }

            # Create template directory structure
            self.template_dir.mkdir(parents=True, exist_ok=True)
            (self.template_dir / "docs").mkdir(exist_ok=True)
            (self.template_dir / "tests").mkdir(exist_ok=True)

            # Create all template files
            self._create_config_py()
            self._create_usage_md()
            self._create_docs_index()
            self._create_test_structure()

            console.print(
                f"[green]✅ Template '{template_id}' created successfully![/green]"
            )
            console.print(f"[blue]📁 Location: {self.template_dir}[/blue]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Error creating template: {e}[/red]")
            return False


def validate_template_data(template_data: dict) -> None:
    """Validate template data contains required fields and formats."""
    required_fields = ["id", "name", "description", "version", "author"]

    for field in required_fields:
        if field not in template_data:
            raise ValueError(f"Missing required field: {field}")

    # Validate template ID format
    template_id = template_data["id"]
    if not re.match(r"^[a-z0-9_-]+$", template_id):
        raise ValueError(
            f"Invalid template ID: {template_id}. Use lowercase letters, numbers, underscores, and hyphens only."
        )

    # Validate version format
    version = template_data["version"]
    if not re.match(r"^\d+\.\d+\.\d+(-[\w\.-]+)?$", version):
        raise ValueError(
            f"Invalid version format: {version}. Use semantic versioning (e.g., 1.0.0)"
        )


def create_template_interactive(
    template_id: str = None, config_file: str = None, output_dir: Path = None
) -> bool:
    """Standalone function to create a template interactively."""
    templates_dir = output_dir or Path(__file__).parent.parent / "templates"
    tests_dir = Path(__file__).parent.parent / "tests"

    creator = TemplateCreator(templates_dir=templates_dir, tests_dir=tests_dir)
    return creator.create_template_interactive(
        template_id=template_id, config_file=config_file
    )
