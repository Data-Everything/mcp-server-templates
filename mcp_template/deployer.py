"""
Deployer
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_template.manager import DeploymentManager
from mcp_template.template.discovery import TemplateDiscovery

console = Console()
logger = logging.getLogger(__name__)


class MCPDeployer:
    """CLI interface for MCP template deployment using unified backend."""

    templates: Dict[str, Dict[str, Any]]  # type: ignore[var-annotated]

    def __init__(self):
        """Initialize the MCP deployer."""
        self.config_dir = Path.home() / ".mcp"
        self.data_dir = Path.home() / "mcp-data"
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        # Use the unified deployment manager
        self.deployment_manager = DeploymentManager(backend_type="docker")

        # Initialize template discovery
        self.template_discovery = TemplateDiscovery()
        self.templates = self.template_discovery.discover_templates()

    def list_templates(self):
        """List available templates."""
        table = Table(title="Available MCP Templates")
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")

        for name, template in self.templates.items():
            # Check deployment status
            try:
                deployments = self.deployment_manager.list_deployments()
                template_deployments = [d for d in deployments if d["template"] == name]
                if template_deployments:
                    status = f"✅ Running ({len(template_deployments)})"
                else:
                    status = "⚪ Not deployed"
            except Exception:
                status = "⚪ Not deployed"

            table.add_row(name, template["description"], status)

        console.print(table)

    def deploy(
        self,
        template_name: str,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
        config_values: Optional[Dict[str, str]] = None,
        override_values: Optional[Dict[str, str]] = None,
        pull_image: bool = True,
    ):
        """Deploy a template using the unified deployment manager."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            console.print(f"Available templates: {', '.join(self.templates.keys())}")
            return False

        template = self.templates[template_name]

        console.print(
            Panel(
                f"🚀 Deploying MCP Template: [cyan]{template_name}[/cyan]",
                title="Deployment",
                border_style="blue",
            )
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Deploying {template_name}...", total=None)

            try:
                # Prepare configuration from multiple sources
                config = self._prepare_configuration(
                    template, env_vars, config_file, config_values
                )

                # Check for required tokens
                if "requires_token" in template:
                    token_name = template["requires_token"]
                    if token_name not in config and token_name not in os.environ:
                        console.print(
                            f"[red]❌ Required environment variable {token_name} not provided[/red]"
                        )
                        console.print(
                            f"Set it with: --env {token_name}=your-token-here"
                        )
                        return False
                    elif token_name not in config:
                        config[token_name] = os.environ[token_name]

                # Override directories if provided
                template_copy = template.copy()
                if data_dir or config_dir:
                    template_copy["volumes"] = template["volumes"].copy()

                    if data_dir:
                        for key in template_copy["volumes"]:
                            if "/data" in template_copy["volumes"][key]:
                                template_copy["volumes"][key] = template_copy[
                                    "volumes"
                                ][key].replace("/data", data_dir)

                    if config_dir:
                        for key in template_copy["volumes"]:
                            if "/config" in template_copy["volumes"][key]:
                                template_copy["volumes"][key] = template_copy[
                                    "volumes"
                                ][key].replace("/config", config_dir)

                # Pass template overrides as environment variables to the template
                if override_values:
                    override_env_vars = self._convert_overrides_to_env_vars(
                        override_values
                    )
                    config.update(override_env_vars)

                # Deploy using unified manager
                result = self.deployment_manager.deploy_template(
                    template_id=template_name,
                    configuration=config,
                    template_data=template_copy,
                    pull_image=pull_image,
                )

                progress.update(task, completed=True)

                # Generate MCP config
                self._generate_mcp_config(
                    template_name, result["deployment_name"], template
                )

                # Success message
                console.print(
                    Panel(
                        f"[green]✅ Successfully deployed {template_name}![/green]\n\n"
                        f"[cyan]📋 Details:[/cyan]\n"
                        f"• Container: {result['deployment_name']}\n"
                        f"• Image: {result.get('image', template['image'])}\n"
                        f"• Status: {result.get('status', 'deployed')}\n\n"
                        f"[cyan]🔧 MCP Configuration:[/cyan]\n"
                        f"Config saved to: ~/.mcp/{template_name}.json\n\n"
                        f"[cyan]💡 Management:[/cyan]\n"
                        f"• View logs: mcp-template logs {template_name}\n"
                        f"• Stop: mcp-template stop {template_name}\n"
                        f"• Shell: mcp-template shell {template_name}",
                        title="🎉 Deployment Complete",
                        border_style="green",
                    )
                )

                return True

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]❌ Failed to deploy {template_name}: {e}[/red]")
                return False

    def stop(self, template_name: str, custom_name: Optional[str] = None):
        """Stop a deployed template."""
        try:
            # List deployments to find the right one
            deployments = self.deployment_manager.list_deployments()

            # Find deployment by template name
            target_deployments = [
                d for d in deployments if d["template"] == template_name
            ]

            if not target_deployments:
                console.print(
                    f"[yellow]⚠️  No running deployments found for {template_name}[/yellow]"
                )
                return False

            # If custom name provided, find exact match
            if custom_name:
                target_deployments = [
                    d for d in target_deployments if custom_name in d["name"]
                ]
                if not target_deployments:
                    console.print(
                        f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]"
                    )
                    return False

            # Stop the deployment(s)
            success_count = 0
            for deployment in target_deployments:
                if self.deployment_manager.delete_deployment(deployment["name"]):
                    console.print(f"[green]✅ Stopped {deployment['name']}[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]❌ Failed to stop {deployment['name']}[/red]")

            return success_count > 0

        except Exception as e:
            console.print(f"[red]❌ Error stopping {template_name}: {e}[/red]")
            return False

    def logs(self, template_name: str, custom_name: Optional[str] = None):
        """Show logs for a deployed template."""
        try:
            # Find deployment
            deployments = self.deployment_manager.list_deployments()
            target_deployments = [
                d for d in deployments if d["template"] == template_name
            ]

            if not target_deployments:
                console.print(
                    f"[yellow]⚠️  No deployments found for {template_name}[/yellow]"
                )
                return

            if custom_name:
                target_deployments = [
                    d for d in target_deployments if custom_name in d["name"]
                ]
                if not target_deployments:
                    console.print(
                        f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]"
                    )
                    return

            deployment = target_deployments[0]
            status = self.deployment_manager.get_deployment_status(deployment["name"])

            console.print(f"[blue]📋 Logs for {deployment['name']}:[/blue]")
            logs = status.get("logs", "No logs available")
            if logs:
                console.print(logs)
            else:
                console.print("[yellow]No logs available[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ Error getting logs: {e}[/red]")

    def shell(self, template_name: str, custom_name: Optional[str] = None):
        """Open shell in deployed template."""
        try:
            # Find deployment
            deployments = self.deployment_manager.list_deployments()
            target_deployments = [
                d for d in deployments if d["template"] == template_name
            ]

            if not target_deployments:
                console.print(
                    f"[yellow]⚠️  No deployments found for {template_name}[/yellow]"
                )
                return

            if custom_name:
                target_deployments = [
                    d for d in target_deployments if custom_name in d["name"]
                ]
                if not target_deployments:
                    console.print(
                        f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]"
                    )
                    return

            deployment = target_deployments[0]
            container_name = deployment["name"]

            console.print(f"[blue]🐚 Opening shell in {container_name}...[/blue]")
            subprocess.run(  # nosec B603 B607
                ["docker", "exec", "-it", container_name, "/bin/sh"], check=True
            )

        except subprocess.CalledProcessError:
            console.print("[red]❌ Failed to open shell[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    def cleanup(
        self, template_name: Optional[str] = None, all_containers: bool = False
    ):
        """Clean up deployments - stop and remove containers."""
        try:
            # List all deployments
            deployments = self.deployment_manager.list_deployments()

            if not deployments:
                console.print("[yellow]⚠️  No deployments found to cleanup[/yellow]")
                return True

            # Filter deployments
            if all_containers:
                target_deployments = deployments
                console.print(
                    f"[yellow]🧹 Cleaning up all {len(deployments)} MCP deployments...[/yellow]"
                )
            elif template_name:
                target_deployments = [
                    d for d in deployments if d["template"] == template_name
                ]
                if not target_deployments:
                    console.print(
                        f"[yellow]⚠️  No deployments found for template '{template_name}'[/yellow]"
                    )
                    return True
                console.print(
                    f"[yellow]🧹 Cleaning up {len(target_deployments)} '{template_name}' deployments...[/yellow]"
                )
            else:
                # Interactive mode - show list and ask
                console.print("\n[cyan]📋 Current deployments:[/cyan]")
                for i, deployment in enumerate(deployments, 1):
                    console.print(
                        f"  {i}. {deployment['name']} ({deployment['template']}) - {deployment['status']}"
                    )

                # For now, cleanup all stopped/failed containers
                target_deployments = [
                    d
                    for d in deployments
                    if d["status"] in ["exited", "dead", "restarting"]
                ]
                if not target_deployments:
                    console.print(
                        "[green]✅ No stopped or failed containers to cleanup[/green]"
                    )
                    return True
                console.print(
                    f"[yellow]🧹 Cleaning up {len(target_deployments)} stopped/failed containers...[/yellow]"
                )

            # Clean up deployments
            success_count = 0
            for deployment in target_deployments:
                if self.deployment_manager.delete_deployment(deployment["name"]):
                    console.print(f"[green]✅ Cleaned up {deployment['name']}[/green]")
                    success_count += 1
                else:
                    console.print(
                        f"[red]❌ Failed to cleanup {deployment['name']}[/red]"
                    )

            if success_count > 0:
                console.print(
                    f"\n[green]🎉 Successfully cleaned up {success_count} deployments![/green]"
                )
            else:
                console.print("\n[yellow]⚠️  No deployments were cleaned up[/yellow]")

            return success_count > 0

        except Exception as e:
            console.print(f"[red]❌ Error during cleanup: {e}[/red]")
            return False

    def _prepare_configuration(
        self,
        template: Dict[str, Any],
        env_vars: Optional[Dict[str, str]] = None,
        config_file: Optional[str] = None,
        config_values: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Prepare configuration from multiple sources with proper type conversion."""
        config = {}

        # Start with template defaults
        template_env = template.get("env_vars", {})
        for key, value in template_env.items():
            config[key] = value

        # Load from config file if provided
        if config_file:
            config.update(self._load_config_file(config_file, template))

        # Apply CLI config values with type conversion
        if config_values:
            config.update(self._convert_config_values(config_values, template))

        # Apply environment variables (highest priority)
        if env_vars:
            config.update(env_vars)

        return config

    def _load_config_file(
        self, config_file: str, template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Load configuration from JSON/YAML file and map to environment variables."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                # Try relative to template directory
                template_dir = (
                    Path(__file__).parent.parent
                    / "templates"
                    / template.get("name", "")
                )
                config_path = template_dir / "config" / config_file
                if not config_path.exists():
                    raise FileNotFoundError(f"Config file not found: {config_file}")

            with open(config_path, encoding="utf-8") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    file_config = yaml.safe_load(f)
                else:
                    file_config = json.load(f)

            # Map config file values to environment variables based on template schema
            return self._map_file_config_to_env(file_config, template)

        except Exception as e:
            console.print(
                f"[red]❌ Failed to load config file {config_file}: {e}[/red]"
            )
            raise

    def _map_file_config_to_env(
        self, file_config: Dict[str, Any], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map config file values to environment variables based on template schema."""
        env_config = {}

        # Get the config schema from template
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Generic mapping: try to map config values directly to properties
        # First, try direct property name mapping
        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping")
            if not env_mapping:
                continue

            # Try direct property name match in config
            if prop_name in file_config:
                value = file_config[prop_name]
                env_config[env_mapping] = self._convert_value_to_env_string(
                    value, prop_config
                )
                continue

            # Try snake_case to camelCase conversion
            camel_name = self._snake_to_camel(prop_name)
            if camel_name in file_config:
                value = file_config[camel_name]
                env_config[env_mapping] = self._convert_value_to_env_string(
                    value, prop_config
                )
                continue

            # Try nested path mapping (e.g., "security.readOnly" -> "read_only_mode")
            nested_value = self._find_nested_config_value(
                file_config, prop_name, prop_config
            )
            if nested_value is not None:
                env_config[env_mapping] = self._convert_value_to_env_string(
                    nested_value, prop_config
                )

        return env_config

    def _snake_to_camel(self, snake_str: str) -> str:
        """Convert snake_case to camelCase."""
        components = snake_str.split("_")
        return components[0] + "".join(word.capitalize() for word in components[1:])

    def _find_nested_config_value(
        self, file_config: Dict[str, Any], prop_name: str, prop_config: Dict[str, Any]
    ) -> Any:
        """Find config value using common nested patterns."""
        # Check if property config has a file_mapping hint
        if "file_mapping" in prop_config:
            return self._get_nested_value(file_config, prop_config["file_mapping"])

        # Try common nested patterns based on property name
        common_patterns = self._generate_common_patterns(prop_name)
        for pattern in common_patterns:
            value = self._get_nested_value(file_config, pattern)
            if value is not None:
                return value

        return None

    def _generate_common_patterns(self, prop_name: str) -> List[str]:
        """Generate common nested configuration patterns for a property."""
        patterns = []

        # Common category mappings
        category_mappings = {
            "log_level": ["logging.level", "log.level"],
            "enable_audit_logging": [
                "logging.enableAudit",
                "logging.audit",
                "log.audit",
            ],
            "read_only_mode": ["security.readOnly", "security.readonly", "readonly"],
            "max_file_size": [
                "security.maxFileSize",
                "limits.maxFileSize",
                "performance.maxFileSize",
            ],
            "allowed_directories": [
                "security.allowedDirs",
                "security.directories",
                "paths.allowed",
            ],
            "exclude_patterns": [
                "security.excludePatterns",
                "security.exclude",
                "filters.exclude",
            ],
            "max_concurrent_operations": [
                "performance.maxConcurrentOperations",
                "limits.concurrent",
            ],
            "timeout_ms": [
                "performance.timeoutMs",
                "performance.timeout",
                "limits.timeout",
            ],
        }

        if prop_name in category_mappings:
            patterns.extend(category_mappings[prop_name])

        # Generate generic patterns
        camel_name = self._snake_to_camel(prop_name)
        patterns.extend(
            [
                f"config.{prop_name}",
                f"settings.{prop_name}",
                f"options.{prop_name}",
                f"config.{camel_name}",
                f"settings.{camel_name}",
                f"options.{camel_name}",
            ]
        )

        return patterns

    def _convert_value_to_env_string(
        self, value: Any, prop_config: Dict[str, Any]
    ) -> str:
        """Convert a value to environment variable string format."""
        if isinstance(value, list):
            separator = prop_config.get("env_separator", ",")
            return separator.join(str(item) for item in value)
        elif isinstance(value, bool):
            return "true" if value else "false"
        else:
            return str(value)

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    def _convert_config_values(
        self, config_values: Dict[str, str], template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert CLI config values to proper types based on template schema."""
        converted_config = {}

        # Get the config schema from template
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for key, value in config_values.items():
            # Handle nested configuration with double underscore notation
            # e.g., security__read_only -> security.readOnly
            if "__" in key:
                env_mapping = self._handle_nested_cli_config(key, value, properties)
                if env_mapping:
                    converted_config[env_mapping] = value
                    continue

            # Find the property in schema by name or env_mapping
            prop_config = None
            env_mapping = None

            # First try direct property name match
            if key in properties:
                prop_config = properties[key]
                env_mapping = prop_config.get("env_mapping", f"MCP_{key.upper()}")
            else:
                # Then try to find by env_mapping
                for prop_name, prop_data in properties.items():
                    if prop_data.get("env_mapping") == key:
                        prop_config = prop_data
                        env_mapping = key
                        break

            if prop_config and env_mapping:
                # Convert based on type
                prop_type = prop_config.get("type", "string")
                try:
                    if prop_type == "boolean":
                        converted_value = value.lower() in ("true", "1", "yes", "on")
                    elif prop_type == "integer":
                        converted_value = int(value)
                    elif prop_type == "number":
                        converted_value = float(value)
                    elif prop_type == "array":
                        separator = prop_config.get("env_separator", ",")
                        converted_value = value.split(separator)
                    else:
                        converted_value = value

                    # Store as string for environment variable
                    if isinstance(converted_value, list):
                        separator = prop_config.get("env_separator", ",")
                        converted_config[env_mapping] = separator.join(
                            str(item) for item in converted_value
                        )
                    else:
                        converted_config[env_mapping] = str(converted_value)

                except (ValueError, TypeError) as e:
                    console.print(
                        f"[yellow]⚠️  Failed to convert {key}={value} to {prop_type}: {e}[/yellow]"
                    )
                    converted_config[env_mapping] = str(value)
            else:
                # Unknown property, store as-is with MCP_ prefix if not already present
                env_key = key if key.startswith("MCP_") else f"MCP_{key.upper()}"
                converted_config[env_key] = value

        return converted_config

    def _convert_overrides_to_env_vars(
        self, override_values: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Convert override values to environment variables with OVERRIDE_ prefix.

        This allows the template's config.py to handle the override processing
        instead of the deployer trying to modify template.json directly.

        Args:
            override_values: Override values from CLI (e.g., {'capabilities__0__name': 'Hello Tool'})

        Returns:
            Dict with OVERRIDE_ prefixed environment variables
        """
        override_env_vars = {}

        for key, value in override_values.items():
            # Convert to environment variable with OVERRIDE_ prefix
            env_var_name = f"OVERRIDE_{key}"
            override_env_vars[env_var_name] = str(value)

        return override_env_vars

    def _handle_nested_cli_config(
        self, nested_key: str, value: str, properties: Dict[str, Any]
    ) -> Optional[str]:
        """Handle nested CLI configuration using double underscore notation."""
        # Convert security__read_only to find read_only_mode in properties
        # Also supports template__property notation for template-level overrides
        parts = nested_key.split("__")
        if len(parts) < 2:
            return None

        # Handle template-level overrides (template_name__property)
        if len(parts) == 2:
            category, prop_name = parts

            # Check if this is a template-level override
            # This allows any property to be overridden with template_name__property=value
            if prop_name in properties:
                prop_config = properties[prop_name]
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    return env_mapping

            # Try different property name patterns for nested configurations
            possible_names = [
                f"{category}_{prop_name}",  # security__read_only -> security_read_only
                f"{prop_name}_mode",  # security__read_only -> read_only_mode
                f"{category}_{prop_name}_mode",  # security__read_only -> security_read_only_mode
                prop_name,  # security__read_only -> read_only
            ]

            for prop_name_candidate in possible_names:
                if prop_name_candidate in properties:
                    prop_config = properties[prop_name_candidate]
                    env_mapping = prop_config.get("env_mapping")
                    if env_mapping:
                        return env_mapping

            # If no direct match, construct environment variable name
            return f"MCP_{category.upper()}_{prop_name.upper()}"

        # Handle deeper nesting (category__subcategory__property)
        elif len(parts) == 3:
            category, subcategory, prop_name = parts
            # Try to find matching property with deeper nesting
            possible_names = [
                f"{category}_{subcategory}_{prop_name}",
                f"{subcategory}_{prop_name}",
                prop_name,
            ]

            for prop_name_candidate in possible_names:
                if prop_name_candidate in properties:
                    prop_config = properties[prop_name_candidate]
                    env_mapping = prop_config.get("env_mapping")
                    if env_mapping:
                        return env_mapping

            # Construct nested environment variable name
            return f"MCP_{category.upper()}_{subcategory.upper()}_{prop_name.upper()}"

        return None

    def _generate_mcp_config(
        self, template_name: str, container_name: str, template: Dict
    ):
        """Generate MCP configuration file."""
        config_file = self.config_dir / f"{template_name}.json"

        # Check if template has example_config
        if "example_config" not in template:
            # Generate a basic config if no example is provided
            config = {
                "mcpServers": {
                    template_name: {
                        "command": "docker",
                        "args": ["exec", "-i", container_name, "python", "-m", "mcp"],
                        "env": {"MCP_CONTAINER_NAME": container_name},
                    }
                }
            }
        else:
            config = json.loads(template["example_config"])

            # Update the container name in the config
            if "servers" in config:
                for server_name in config["servers"]:
                    if "args" in config["servers"][server_name]:
                        # Replace the container name in args
                        args = config["servers"][server_name]["args"]
                        for i, arg in enumerate(args):
                            if arg.startswith("mcp-"):
                                args[i] = container_name

        config_file.write_text(json.dumps(config, indent=2))
        console.print(f"[green]📝 MCP config saved to: {config_file}[/green]")

    def _show_config_options(self, template_name: str):
        """Show available configuration options for a template."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            return

        template = self.templates[template_name]
        config_schema = template.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        if not properties:
            console.print(
                f"[yellow]⚠️  No configuration options available for {template_name}[/yellow]"
            )
            return

        console.print(f"\n[cyan]📋 Configuration Options for {template_name}:[/cyan]\n")

        table = Table(title=f"{template_name} Configuration")
        table.add_column("Property", style="cyan")
        table.add_column("Type", style="yellow")
        table.add_column("Env Variable", style="green")
        table.add_column("Default", style="blue")
        table.add_column("Required", style="red")
        table.add_column("Description", style="white")

        for prop_name, prop_config in properties.items():
            prop_type = prop_config.get("type", "string")
            env_mapping = prop_config.get("env_mapping", "")
            default = str(prop_config.get("default", ""))
            is_required = "✓" if prop_name in required else ""
            description = prop_config.get("description", "")

            table.add_row(
                prop_name, prop_type, env_mapping, default, is_required, description
            )

        console.print(table)

        console.print("\n[cyan]💡 Usage Examples:[/cyan]")
        console.print("  # Using config file:")
        console.print(
            f"  python -m mcp_template deploy {template_name} --config-file config.json"
        )
        console.print("  # Using CLI options:")
        example_configs = []
        for prop_name, prop_config in list(properties.items())[
            :2
        ]:  # Show first 2 as examples
            if prop_config.get("default"):
                example_configs.append(f"{prop_name}={prop_config['default']}")
        if example_configs:
            config_str = " ".join([f"--config {cfg}" for cfg in example_configs])
            console.print(
                f"  python -m mcp_template deploy {template_name} {config_str}"
            )

        console.print("  # Using double underscore notation for nested config:")
        nested_examples = []

        # Generate some common nested notation examples based on actual properties
        for prop_name, prop_config in properties.items():
            if len(nested_examples) >= 2:  # Limit to 2 examples
                break
            if prop_config.get("default"):
                # Map properties to their nested equivalents
                nested_mapping = {
                    "read_only_mode": "security__read_only",
                    "log_level": "logging__level",
                    "max_file_size": "security__max_file_size",
                    "enable_audit": "logging__enable_audit",
                    "allowed_directories": "security__allowed_dirs",
                    "max_concurrent_operations": "performance__max_concurrent",
                    "timeout_ms": "performance__timeout_ms",
                    "cache_enabled": "performance__cache_enabled",
                }

                if prop_name in nested_mapping:
                    nested_examples.append(
                        f"{nested_mapping[prop_name]}={prop_config['default']}"
                    )

        if nested_examples:
            nested_str = " ".join([f"--config {cfg}" for cfg in nested_examples])
            console.print(
                f"  python -m mcp_template deploy {template_name} {nested_str}"
            )
        else:
            # Fallback examples if no specific mappings found
            console.print(
                f"  python -m mcp_template deploy {template_name} --config security__read_only=true --config logging__level=debug"
            )

        console.print("  # Using environment variables:")
        example_envs = []
        for prop_name, prop_config in list(properties.items())[
            :2
        ]:  # Show first 2 as examples
            env_mapping = prop_config.get("env_mapping")
            if env_mapping and prop_config.get("default"):
                example_envs.append(f"{env_mapping}={prop_config['default']}")

        if example_envs:
            env_str = " ".join([f"--env {env}" for env in example_envs])
            console.print(f"  python -m mcp_template deploy {template_name} {env_str}")

    def _apply_template_overrides(
        self, template_data: Dict[str, Any], override_values: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Apply template data overrides using double underscore notation."""
        import copy

        if not override_values:
            return copy.deepcopy(template_data)

        template_copy = copy.deepcopy(template_data)

        for key, value in override_values.items():
            # Split on double underscores to create nested path
            key_parts = key.split("__")

            # Navigate/create the nested structure
            current = template_copy
            for i, part in enumerate(key_parts[:-1]):
                # Check if this part is a numeric index for array access
                if part.isdigit():
                    index = int(part)
                    if isinstance(current, list):
                        # Extend list if needed
                        while len(current) <= index:
                            current.append({})
                        if i == len(key_parts) - 2:  # This is the parent of final key
                            if not isinstance(current[index], dict):
                                current[index] = {}
                        current = current[index]
                    else:
                        # DEBUG: Add more details about the failing field
                        console.print(
                            f"[yellow]⚠️ Warning: Cannot index non-list field with {part} (field type: {type(current)}, key_parts so far: {key_parts[:i+1]})[/yellow]"
                        )
                        break
                else:
                    # Regular dictionary key access
                    if part not in current:
                        current[part] = {}
                    elif not isinstance(current[part], (dict, list)):
                        # Can't override non-dict/list with nested structure
                        console.print(
                            f"[yellow]⚠️ Warning: Cannot override non-dict field {'.'.join(key_parts[:i+1])} with nested structure[/yellow]"
                        )
                        break
                    current = current[part]
            else:
                # Set the final value, converting types appropriately
                final_key = key_parts[-1]
                converted_value = self._convert_override_value(value)

                # Handle final array index
                if final_key.isdigit() and isinstance(current, list):
                    index = int(final_key)
                    while len(current) <= index:
                        current.append(None)
                    current[index] = converted_value
                else:
                    current[final_key] = converted_value

        return template_copy

    def _extract_config_overrides(
        self, override_values: Dict[str, str], template_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract config-related overrides that should be converted to environment variables.

        Args:
            override_values: Raw override values from CLI
            template_data: Template data with config_schema

        Returns:
            Dictionary of config overrides to be converted to env vars
        """
        config_overrides = {}
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for key, value in override_values.items():
            # Check if this override key corresponds to a config schema property
            parts = key.split("__")

            # Direct property match
            if key in properties:
                config_overrides[key] = value
                continue

            # Check for nested property matches
            for prop_name, prop_config in properties.items():
                env_mapping = prop_config.get("env_mapping", "")

                # Match by environment mapping
                if env_mapping and (
                    key == env_mapping
                    or key.upper() == env_mapping.upper()
                    or key.replace("__", "_").upper() == env_mapping.upper()
                ):
                    config_overrides[prop_name] = value
                    break

                # Match nested structure patterns
                if len(parts) >= 2:
                    potential_matches = [
                        "_".join(parts),
                        "_".join(parts[1:]),
                        parts[-1],
                    ]

                    if prop_name in potential_matches:
                        config_overrides[prop_name] = value
                        break

        return config_overrides

    def _convert_override_value(self, value: str) -> Any:
        """Convert string override value to appropriate type."""
        # Handle boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

        # Handle numeric values
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # Handle JSON structures
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Default to string
        return value
        # Handle JSON structures
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Default to string
        return value
