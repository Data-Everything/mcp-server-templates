"""
Deployer
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.exceptions import StdIoTransportDeploymentError
from mcp_template.template.utils.discovery import TemplateDiscovery
from mcp_template.utils.config_processor import ConfigProcessor

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

        # Initialize configuration processor
        self.config_processor = ConfigProcessor()

    def list_templates(self, deployed_only: bool = False):
        """List available templates."""

        table = Table(
            title=f"{'Available' if not deployed_only else 'Deployed'} MCP Templates"
        )
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Status", style="green")
        for name, template in self.templates.items():
            if deployed_only:
                add_row = False
            else:
                add_row = True
            # Check deployment status
            try:
                deployments = self.deployment_manager.list_deployments()
                template_deployments = [d for d in deployments if d["template"] == name]
                if template_deployments:
                    status = f"✅ Running ({len(template_deployments)})"
                    add_row = True
                else:
                    status = "⚪ Not deployed"
            except Exception:
                status = "⚪ Not deployed"

            if add_row:
                table.add_row(name, template["description"], status)

        console.print(table)

    @staticmethod
    def list_missing_properties(
        template: Dict[str, Any], config: Dict[str, Any]
    ) -> List[str]:
        """Check for missing required properties in the configuration."""

        missing_properties = []
        required_properties = template.get("config_schema", {}).get("required", [])
        required_properties_env_vars = {
            prop: template["config_schema"]["properties"][prop].get("env_mapping")
            for prop in required_properties
            if prop in template.get("config_schema", {}).get("properties", {})
            and template["config_schema"]["properties"][prop].get("env_mapping")
        }
        for prop in required_properties:
            if (
                prop not in config
                and required_properties_env_vars.get(prop) not in config
            ):
                missing_properties.append(prop)
        return missing_properties

    @staticmethod
    def append_volume_mounts_to_template(
        template: Dict[str, Any],
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get volume mounts from the template and configuration."""

        template_copy = template.copy()
        if data_dir or config_dir:
            template_copy["volumes"] = template["volumes"].copy()

            if data_dir:
                for key in template_copy["volumes"]:
                    if "/data" in template_copy["volumes"][key]:
                        template_copy["volumes"][key] = template_copy["volumes"][
                            key
                        ].replace("/data", data_dir)

            if config_dir:
                for key in template_copy["volumes"]:
                    if "/config" in template_copy["volumes"][key]:
                        template_copy["volumes"][key] = template_copy["volumes"][
                            key
                        ].replace("/config", config_dir)

        return template_copy

    def generate_run_config(
        self,
        template_data: Dict[str, Any],
        transport: Optional[Literal["http", "stdio", "sse", "http-stream"]] = None,
        port: Optional[int] = None,
        configuration: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
        data_dir: Optional[str] = None,
        config_dir: Optional[str] = None,
        override_values: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Generate configuration for running a server.

        Args:
            template_data: Template data to use
            transport: Transport type (e.g., "http", "stdio")
            port: Port for HTTP transport
            configuration: Configuration values to apply
            config_file: Optional configuration file to use
            env_vars: Environment variables to set for the server
            data_dir: Data directory for the server
            config_dir: Configuration directory for the server
            override_values: Optional values to override in the configuration

        Returns:
            Configuration dictionary or None if failed
        """

        template_id = template_data.get("id")
        supported_transports = template_data.get("transport", {}).get("supported", [])
        default_transport = template_data.get("transport", {}).get("default", "http")
        if not transport:
            # Default to HTTP transport if not specified
            transport = default_transport
        else:
            if transport not in supported_transports:
                logger.error(
                    "Transport %s not supported by template %s",
                    transport,
                    template_id,
                )
                return None

        if transport == "stdio":
            raise StdIoTransportDeploymentError()

        if not port and transport == "http":
            from mcp_template.tools.docker_probe import DockerProbe

            port = template_data.get("transport", {}).get(
                "port", DockerProbe._find_available_port()
            )

        # Use provided configuration or empty dict
        config = configuration or {}
        env_vars = env_vars or {}

        config["transport"] = transport
        if port:
            # Ensure port is a string for JSON serialization
            config["port"] = str(port)

        config = self.config_processor.prepare_configuration(
            template=template_data,
            env_vars=env_vars,
            config_file=config_file,
            config_values=config,
            override_values=override_values,
        )
        missing_properties = MCPDeployer.list_missing_properties(template_data, config)
        template_copy = MCPDeployer.append_volume_mounts_to_template(
            template=template_data,
            data_dir=data_dir,
            config_dir=config_dir,
        )
        template_config_dict = (
            self.config_processor.handle_volume_and_args_config_properties(
                template_copy, config
            )
        )
        config = template_config_dict.get("config", config)
        template_copy = template_config_dict.get("template", template_copy)

        return {
            "template": template_copy,
            "config": config,
            "transport": transport,
            "port": port,
            "missing_properties": missing_properties,
        }

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

                config_dict = self.generate_run_config(
                    template_data=template,
                    transport=template.get("transport", {}).get("default", "http"),
                    port=None,  # Port will be determined by the template
                    configuration=config_values,
                    config_file=config_file,
                    env_vars=env_vars,
                    data_dir=data_dir,
                    config_dir=config_dir,
                    override_values=override_values,
                )
                config = config_dict.get("config", {})
                template_copy = config_dict.get("template", {})
                missing_properties = config_dict.get("missing_properties", [])

                if missing_properties:
                    console.print(
                        f"[red]❌ Missing required properties: {', '.join(missing_properties)}[/red]"
                    )
                    return False

                # Deploy using unified manager
                from mcp_template.core.deployment_manager import DeploymentOptions

                deployment_options = DeploymentOptions(
                    pull_image=pull_image,
                    data_dir=data_dir,
                    config_dir=config_dir,
                )

                config_sources = {
                    "config_values": config,
                    "config_file": config_file,
                    "env_vars": env_vars,
                    "override_values": override_values,
                }

                result = self.deployment_manager.deploy_template(
                    template_id=template_name,
                    config_sources=config_sources,
                    deployment_options=deployment_options,
                )

                progress.update(task, completed=True)

                # Check deployment success
                if not result.success:
                    console.print(
                        f"[red]❌ Failed to deploy {template_name}: {result.error}[/red]"
                    )
                    return False

                # Generate MCP config
                self._generate_mcp_config(template_name, result.deployment_id, template)

                # Success message
                console.print(
                    Panel(
                        f"[green]✅ Successfully deployed {template_name}![/green]\n\n"
                        f"[cyan]📋 Details:[/cyan]\n"
                        f"• Container: {result.deployment_id}\n"
                        f"• Image: {result.image or template['image']}\n"
                        f"• Status: {result.status or 'deployed'}\n\n"
                        f"[cyan]🔧 MCP Configuration:[/cyan]\n"
                        f"Config saved to: ~/.mcp/{template_name}.json\n\n"
                        f"[cyan]💡 Management:[/cyan]\n"
                        f"• View logs: mcpt logs {template_name}\n"
                        f"• Stop: mcpt stop {template_name}\n"
                        f"• Shell: mcpt shell {template_name}",
                        title="🎉 Deployment Complete",
                        border_style="green",
                    )
                )

                return True

            except Exception as e:
                progress.update(task, completed=True)
                console.print(f"[red]❌ Failed to deploy {template_name}: {e}[/red]")
                return False

    def stop(
        self,
        template_name: str = None,
        custom_name: Optional[str] = None,
        all_containers: bool = False,
    ):
        """Stop a deployed template."""
        try:
            # List deployments to find the right one
            deployments = self.deployment_manager.list_deployments()

            if not (template_name or custom_name or all_containers):
                console.print(
                    "[red]❌ You must provide at least one of: template, --name, or --all[/red]"
                )
                return False

            # Find deployment by template name
            if template_name:
                target_deployments = [
                    d for d in deployments if d["template"] == template_name
                ]
            else:
                target_deployments = deployments

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
                if self.deployment_manager.stop_deployment(deployment["name"]):
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
                if self.deployment_manager.stop_deployment(deployment["name"]):
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
        """Apply template data overrides using the config processor."""
        return self.config_processor._apply_template_overrides(
            template_data, override_values
        )
