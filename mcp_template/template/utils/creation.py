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

# Constants


class TemplateCreator:
    """Create new MCP server templates with complete structure."""

    def __init__(
        self, templates_dir: Optional[Path] = None, tests_dir: Optional[Path] = None
    ):
        self.template_data = {}
        self.template_dir = None
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.tests_dir = tests_dir or TESTS_DIR

    def create_template_interactive(
        self, template_id: str = None, config_file: str = None
    ) -> bool:
        """Create a template interactively with user prompts or from config file."""

        # Load from config file if provided
        if config_file:
            return self._create_from_config_file(config_file, template_id)

        console.print(
            Panel(
                "[cyan]🚀 MCP Template Creator[/cyan]\n\n"
                "This tool will help you create a complete MCP server template\n"
                "with all necessary files, tests, and documentation.",
                title="Template Creator",
                border_style="green",
            )
        )

        # Get template basic information
        if not template_id:
            template_id = self._prompt_template_id()

        self.template_data["id"] = template_id
        self.template_dir = self.templates_dir / template_id

        # Check if template already exists
        if self.template_dir.exists():
            if not Confirm.ask(f"Template '{template_id}' already exists. Overwrite?"):
                console.print("[yellow]Template creation cancelled.[/yellow]")
                return False

        # Gather template information
        self._gather_template_info()

        # Display summary and confirm
        if not self._confirm_creation():
            console.print("[yellow]Template creation cancelled.[/yellow]")
            return False

        # Create the template
        return self._create_template_structure()

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

    def create_template(self) -> bool:
        """Create a template using the current template_data."""
        if not self.template_data:
            raise ValueError(
                "No template data provided. Set template_data before calling create_template()"
            )

        # Set template directory
        template_id = self.template_data.get("id")
        if not template_id:
            raise ValueError("Template ID is required in template_data")

        self.template_dir = self.templates_dir / template_id

        # Create the template structure
        return self._create_template_structure()

    def _create_from_config_file(
        self, config_file: str, template_id: str = None
    ) -> bool:
        """Create template from configuration file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                console.print(
                    f"[red]❌ Configuration file not found: {config_file}[/red]"
                )
                return False

            with open(config_path, "r", encoding="utf-8") as f:
                if (
                    config_path.suffix.lower() == ".yaml"
                    or config_path.suffix.lower() == ".yml"
                ):
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)

            # Validate required fields
            required_fields = ["id", "name", "description"]
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

            # Check if template already exists
            if self.template_dir.exists():
                console.print(
                    f"[yellow]⚠️  Template '{template_id}' already exists. Overwriting...[/yellow]"
                )

            return self._create_template_structure()

        except Exception as e:
            console.print(f"[red]❌ Error reading config file: {e}[/red]")
            return False

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

    def _validate_template_id(self, template_id: str) -> bool:
        """Validate template ID format."""
        return bool(re.match(r"^[a-z0-9-]+$", template_id)) and len(template_id) >= 2

    def _gather_template_info(self):
        """Gather minimal template information from user."""
        console.print("\n[cyan]📋 Template Information[/cyan]")

        self.template_data.update(
            {
                "name": Prompt.ask(
                    "Template display name",
                    default=re.sub(
                        r"[^a-zA-Z0-9]", " ", self.template_data["id"]
                    ).title(),
                ),
                "description": Prompt.ask("Template description"),
                "version": Prompt.ask("Version", default="1.0.0"),
                "author": Prompt.ask("Author name", default="Your Name"),
                "docker_image": Prompt.ask(
                    "Docker image name",
                    default=f"dataeverything/mcp-{self.template_data['id']}",
                ),
                "docker_tag": Prompt.ask(
                    "Docker tag",
                    default="latest",
                ),
                "origin": Prompt.ask(
                    "Origin: [yellow]For pre-build docker based templates, specify the origin as external else internal[/yellow]",
                    default="internal",
                    choices=["internal", "external"],
                ),
            }
        )

        # Set minimal defaults instead of asking for complex configurations
        console.print("\n[cyan]� Creating template with minimal boilerplate...[/cyan]")
        self.template_data["capabilities"] = [
            {
                "name": "example",
                "description": "A simple example tool",
                "example": "Say hello to the world",
                "example_args": {},
                "example_response": "Hello from your new MCP server!",
            }
        ]

        self.template_data["config_schema"] = {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "title": "API Key",
                    "description": "Required API key for authentication. Get from your service provider dashboard.",
                    "env_mapping": "API_KEY",
                    "sensitive": True,
                },
                "base_url": {
                    "type": "string",
                    "title": "Base URL",
                    "description": "Service base URL endpoint",
                    "default": "https://api.example.com",
                    "env_mapping": "BASE_URL",
                },
                "data_directory": {
                    "type": "string",
                    "title": "Data Directory",
                    "description": "Local directory for data storage and caching. Will be mounted as Docker volume.",
                    "default": "/tmp/data",
                    "env_mapping": "DATA_DIRECTORY",
                    "volume_mount": True,
                },
                "allowed_paths": {
                    "type": "string",
                    "title": "Allowed File Paths",
                    "description": "Space-separated list of allowed file paths for operations. Passed as command arguments.",
                    "env_mapping": "ALLOWED_PATHS",
                    "volume_mount": True,
                    "command_arg": True,
                },
                "log_level": {
                    "type": "string",
                    "title": "Log Level",
                    "description": "Logging verbosity level",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "default": "INFO",
                    "env_mapping": "LOG_LEVEL",
                },
                "enable_cache": {
                    "type": "boolean",
                    "title": "Enable Caching",
                    "description": "Enable response caching for better performance",
                    "default": True,
                    "env_mapping": "ENABLE_CACHE",
                },
                "timeout": {
                    "type": "integer",
                    "title": "Request Timeout",
                    "description": "HTTP request timeout in seconds",
                    "default": 30,
                    "env_mapping": "REQUEST_TIMEOUT",
                },
            },
            "required": ["api_key", "allowed_paths"],
        }

    def _confirm_creation(self) -> bool:
        """Display summary and confirm template creation."""
        console.print("\n[cyan]📄 Template Summary[/cyan]")

        table = Table()
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("ID", self.template_data["id"])
        table.add_row("Name", self.template_data["name"])
        table.add_row("Description", self.template_data["description"])
        table.add_row("Version", self.template_data["version"])
        table.add_row("Author", self.template_data["author"])
        table.add_row("Docker Image", self.template_data["docker_image"])
        table.add_row("Docker Tag", self.template_data["docker_tag"])
        table.add_row("Origin", self.template_data["origin"])
        table.add_row(
            "Config Parameters",
            str(len(self.template_data["config_schema"]["properties"])),
        )

        console.print(table)

        return Confirm.ask("\nCreate this template?")

    def _create_template_structure(self) -> bool:
        """Create the complete template structure."""
        try:
            console.print(
                f"\n[cyan]🏗️  Creating template structure for '{self.template_data['id']}'...[/cyan]"
            )

            # Create template directories
            self._create_directories()

            # Create template files
            self._create_template_json()
            self._create_readme()
            self._create_usage_md()
            self._create_docs_index()
            if self.template_data.get("origin", "internal") == "internal":
                self._create_dockerfile()
                self._create_requirements_txt()
                self._create_server_py()
                self._create_config_py()

            # Create test structure
            self._create_test_structure()

            console.print(
                f"[green]✅ Successfully created template '{self.template_data['id']}'[/green]"
            )
            console.print(f"[cyan]📁 Template location:[/cyan] {self.template_dir}")

            console.print(
                f"[cyan]🧪 Tests location:[/cyan] {self.template_dir / 'tests'}"
            )

            return True

        except Exception as e:
            console.print(f"[red]❌ Error creating template: {e}[/red]")
            return False

    def _create_directories(self):
        """Create template directory structure."""
        directories = [
            self.template_dir,
            self.template_dir / "tests",
            self.template_dir / "docs",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _create_template_json(self):
        """Create template.json configuration file."""
        template_config = {
            "name": self.template_data["name"],
            "description": self.template_data["description"],
            "version": self.template_data["version"],
            "author": self.template_data["author"],
            "category": self.template_data.get("category", "General"),
            "tags": self.template_data.get("tags", []),
            "docker_image": self.template_data.get(
                "docker_image", f"dataeverything/mcp-{self.template_data['id']}"
            ),
            "docker_tag": self.template_data.get("docker_tag", "latest"),
            "ports": self.template_data.get("ports", {}),
            "command": self.template_data.get("command", []),
            "transport": self.template_data.get(
                "transport", {"default": "stdio", "supported": ["stdio"]}
            ),
            "capabilities": self.template_data.get("capabilities", []),
            "config_schema": self.template_data.get(
                "config_schema", {"type": "object", "properties": {}, "required": []}
            ),
            # Add new tool discovery fields
            "tool_discovery": self.template_data.get("tool_discovery", "dynamic"),
            "tool_endpoint": self.template_data.get("tool_endpoint", "/tools"),
            "has_image": self.template_data.get("has_image", True),
            "origin": self.template_data.get("origin", "internal"),
        }

        with open(self.template_dir / "template.json", "w", encoding="utf-8") as f:
            json.dump(template_config, f, indent=2)

    def _create_readme(self):
        """Create README.md for the template."""
        capabilities = self.template_data.get("capabilities", [])
        config_properties = self.template_data.get("config_schema", {}).get(
            "properties", {}
        )
        required_config = self.template_data.get("config_schema", {}).get(
            "required", []
        )

        readme_content = f"""# {self.template_data["name"]}

{self.template_data["description"]}

## Features

"""

        for capability in capabilities:
            readme_content += (
                f"- **{capability['name']}**: {capability['description']}\n"
            )

        if not capabilities:
            readme_content += "- Basic MCP server functionality\n"

        readme_content += """

## Configuration

This template supports the following configuration parameters:

"""

        for param_name, param_config in config_properties.items():
            required = " (required)" if param_name in required_config else ""
            readme_content += (
                f"- `{param_name}`: {param_config['description']}{required}\n"
            )

        if not config_properties:
            readme_content += "- No configuration parameters required\n"

        readme_content += f"""

## Usage

1. Deploy the template using the MCP platform
2. Configure the required parameters
3. Connect your MCP client to the deployed server

## Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m server
```

### Running Tests

```bash
# Run template-specific tests
pytest templates/{self.template_data["id"]}/tests/
```

## Docker

```bash
# Build the image
docker build -t {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")} .

# Run the container
docker run -p 8000:8000 {self.template_data.get("docker_image", f"dataeverything/mcp-{self.template_data['id']}")}
```

## Author

{self.template_data.get("author", "Unknown")}

## Version

{self.template_data.get("version", "1.0.0")}
"""

        with open(self.template_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    def _create_dockerfile(self):
        """Create Dockerfile for the template."""
        dockerfile_content = """FROM python:3.11-slim

LABEL maintainer="Data Everything <tooling@dataeverything.com>"
LABEL description="Demo MCP Server using FastMCP"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy demo template source code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
RUN chown -R mcp:mcp /app
USER mcp

# Expose the default HTTP port
EXPOSE 7071

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7071/health || exit 1

# Set environment variables
ENV MCP_LOG_LEVEL=info
ENV MCP_HELLO_FROM="MCP Platform"

# Default command
CMD ["python", "server.py"]
"""

        with open(self.template_dir / "Dockerfile", "w", encoding="utf-8") as f:
            f.write(dockerfile_content)

    def _create_requirements_txt(self):
        """Create requirements.txt for the template."""
        requirements = [
            "fastmcp>=0.9.0",
            "mcp>=1.0.0",
            "pydantic>=2.0.0",
            "python-dotenv>=1.0.0",
        ]

        with open(self.template_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(requirements) + "\n")

    def _create_server_py(self):
        """Create the main server.py file."""
        self.template_data.get("capabilities", [])
        self.template_data.get("config_schema", {}).get("properties", {})
        class_name = (
            "".join(word.capitalize() for word in self.template_data["id"].split("-"))
            + "MCPServer"
        )

        server_content = f'''#!/usr/bin/env python3
"""
{self.template_data["name"]} - MCP Server Implementation.

{self.template_data["description"]}
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .config import ServerConfig
except ImportError:
    try:
        from config import ServerConfig
    except ImportError:
        # Fallback for Docker or direct script execution
        sys.path.append(os.path.dirname(__file__))
        from config import ServerConfig

class {class_name}:
    """
    {self.template_data["name"]} MCP Server implementation using FastMCP.
    """

    def __init__(self, config_dict: dict = None):
        """Initialize the {self.template_data["name"]} MCP Server with configuration."""
        self.config = ServerConfig(config_dict=config_dict or {{}})

        # Standard configuration data from config_schema
        self.config_data = self.config.get_template_config()

        # Full template data (potentially modified by double underscore notation)
        self.template_data = self.config.get_template_data()

        self.logger = self.config.logger

        self.mcp = FastMCP(
            name=self.template_data.get("name", "demo-server"),
            instructions={self.template_data.get("description", None)},
            version={self.template_data.get("version", "1.0.0")},
        )
        logger.info("%s MCP server %s created", self.template_data["name"], self.mcp.name)
        self.register_tools()

    def register_tools(self):
        """Register tools with the MCP server."""
        self.mcp.tool(self.example, tags=["example"])

    def example(self, message: str) -> str:
        """
        Example tool
        """

        return "Example tool executed successfully"

    def run(self):
        """Run the MCP server with the configured transport and port."""
        self.mcp.run(
            transport=os.getenv(
                "MCP_TRANSPORT",
                self.template_data.get("transport", {{}}).get("default", "http"),
            ),
            port=int(
                os.getenv(
                    "MCP_PORT",
                    self.template_data.get("transport", {{}}).get("port", 7071),
                )
            ),
            log_level=self.config_data.get("log_level", "info"),
        )


# Create the server instance
server = {class_name}(config_dict={{}})

if __name__ == "__main__":
    server.run()
'''

        with open(self.template_dir / "server.py", "w", encoding="utf-8") as f:
            f.write(server_content)

        # Create __init__.py
        with open(self.template_dir / "__init__.py", "w", encoding="utf-8") as f:
            f.write(f'"""\n{self.template_data["name"]} MCP Server.\n"""\n')

    def _create_usage_md(self):
        """Create USAGE.md with detailed usage examples."""
        capabilities = self.template_data.get("capabilities", [])
        config_properties = self.template_data.get("config_schema", {}).get(
            "properties", {}
        )

        usage_content = f"""# {self.template_data["name"]} Usage Guide

## Overview

{self.template_data["description"]}

## Available Tools

"""

        for capability in capabilities:
            usage_content += f"""### {capability["name"]}

**Description**: {capability["description"]}

**Example Usage**: {capability["example"]}

**Parameters**:
"""
            if capability.get("example_args"):
                for arg_name, arg_value in capability["example_args"].items():
                    usage_content += f"- `{arg_name}`: {type(arg_value).__name__}\n"
            else:
                usage_content += "- No parameters required\n"

            usage_content += "\n"

        if not capabilities:
            usage_content += """### hello

**Description**: A simple hello world tool

**Example Usage**: Basic greeting

**Parameters**:
- No parameters required

"""

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
        args=["-m", "server"]
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
mcpt deploy {self.template_data["id"]}
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
python -m server
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

        test_content = f'''"""
Unit tests for {self.template_data["name"]} template.
"""

import pytest
from unittest.mock import Mock, patch

# Import the server module
import sys
sys.path.insert(0, str({repr(str(self.template_dir))}))

from server import app, load_config


class Test{class_name_base}Unit:
    """Unit tests for {self.template_data["name"]} template."""

    def test_config_loading(self):
        """Test configuration loading."""
        config = load_config()
        assert config is not None

    def test_server_initialization(self):
        """Test server initialization."""
        assert app is not None
        assert app.name == "{self.template_data["id"]}"

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

from mcp_template.utils import TESTS_DIR

# Import MCP testing utilities
import sys
sys.path.insert(0, str(TESTS_DIR / "utils"))


@pytest.mark.integration
@pytest.mark.asyncio
class Test{class_name_base}Integration:
    """Integration tests for {self.template_data["name"]} template."""

    @pytest_asyncio.fixture
    async def mcp_client(self):
        """Create MCP test client."""
        template_dir = Path({repr(str(self.template_dir))})
        client = MCPTestClient(template_dir  / "server.py")
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
