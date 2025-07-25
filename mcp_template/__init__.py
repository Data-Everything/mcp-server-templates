#!/usr/bin/env python3
# mypy: ignore-errors
"""
MCP Template Deployment Tool

A unified deployment system that provides:
- Rich CLI interface for standalone users
- Backend abstraction for different deployment targets
- Dynamic template discovery and configuration management
- Zero-configuration deployment experience
"""

import argparse
import json
import logging
import os
import subprocess  # nosec B404
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .create_template import TemplateCreator

# Constants
DEFAULT_DATA_PATH = "/data"
DEFAULT_LOGS_PATH = "/logs"
DEFAULT_CONFIG_PATH = "/config"
CUSTOM_NAME_HELP = "Custom container name"

console = Console()
logger = logging.getLogger(__name__)


class TemplateDiscovery:
    """Dynamic template discovery from templates directory."""

    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize template discovery."""
        if templates_dir is None:
            # Default to templates directory relative to this file
            self.templates_dir = Path(__file__).parent.parent / "templates"
        else:
            self.templates_dir = templates_dir

    def discover_templates(self) -> Dict[str, Dict[str, Any]]:
        """Discover all valid templates in the templates directory."""
        templates = {}

        if not self.templates_dir.exists():
            logger.warning("Templates directory not found: %s", self.templates_dir)
            return templates

        for template_dir in self.templates_dir.iterdir():
            if not template_dir.is_dir():
                continue

            template_name = template_dir.name
            template_config = self._load_template_config(template_dir)

            if template_config:
                templates[template_name] = template_config
                logger.debug("Discovered template: %s", template_name)
            else:
                logger.debug("Skipped invalid template: %s", template_name)

        return templates

    def _load_template_config(self, template_dir: Path) -> Optional[Dict[str, Any]]:
        """Load and validate a template configuration."""
        template_json = template_dir / "template.json"
        dockerfile = template_dir / "Dockerfile"

        # Basic validation: must have template.json and Dockerfile
        if not template_json.exists():
            logger.debug("Template %s missing template.json", template_dir.name)
            return None

        if not dockerfile.exists():
            logger.debug("Template %s missing Dockerfile", template_dir.name)
            return None

        try:
            # Load template metadata
            with open(template_json, encoding="utf-8") as f:
                template_data = json.load(f)

            # Generate deployment configuration
            config = self._generate_template_config(template_data, template_dir)

            return config

        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.debug("Failed to load template %s: %s", template_dir.name, e)
            return None

    def _generate_template_config(
        self, template_data: Dict[str, Any], template_dir: Path
    ) -> Dict[str, Any]:
        """Generate deployment configuration from template metadata."""

        # Extract basic info
        config = {
            "name": template_data.get("name", template_dir.name.title()),
            "description": template_data.get("description", "MCP server template"),
            "version": template_data.get("version", "latest"),
            "category": template_data.get("category", "general"),
            "tags": template_data.get("tags", []),
        }

        # Docker image configuration
        config["image"] = self._get_docker_image(template_data, template_dir.name)

        # Environment variables from config schema
        config["env_vars"] = self._extract_env_vars(template_data)

        # Volume mounts
        config["volumes"] = self._extract_volumes(template_data)

        # Port mappings
        config["ports"] = self._extract_ports(template_data)

        # Required tokens/secrets
        config.update(self._extract_requirements(template_data))

        # Include the original config schema for CLI usage
        config["config_schema"] = template_data.get("config_schema", {})

        # Generate MCP client configuration
        config["example_config"] = self._generate_mcp_config(
            template_data, template_dir.name
        )

        return config

    def _get_docker_image(
        self, template_data: Dict[str, Any], template_name: str
    ) -> str:
        """Get Docker image name for template."""
        if "docker_image" in template_data:
            docker_tag = template_data.get("docker_tag", "latest")
            return f"{template_data['docker_image']}:{docker_tag}"
        else:
            # Fallback to standard naming
            return f"dataeverything/mcp-{template_name}:latest"

    def _extract_env_vars(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract default environment variables from config schema."""
        env_vars = {}

        # Get environment variables from template
        if "environment_variables" in template_data:
            env_vars.update(template_data["environment_variables"])

        # Extract defaults from config schema
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for _, prop_config in properties.items():
            if "default" in prop_config:
                # Map to environment variable if mapping exists
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    default_value = prop_config["default"]
                    if isinstance(default_value, list):
                        separator = prop_config.get("env_separator", ",")
                        env_vars[env_mapping] = separator.join(
                            str(item) for item in default_value
                        )
                    else:
                        env_vars[env_mapping] = str(default_value)

        return env_vars

    def _extract_volumes(self, template_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract volume mounts from template configuration."""
        volumes = {}

        # Default volumes
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # Look for directory-type configurations
        for prop_name, prop_config in properties.items():
            if (
                prop_config.get("type") == "array"
                and "directories" in prop_name.lower()
            ):
                # This is likely a directory configuration
                default_dirs = prop_config.get("default", [])
                for i, directory in enumerate(default_dirs):
                    host_path = (
                        f"~/mcp-data/{prop_name}_{i}"
                        if len(default_dirs) > 1
                        else "~/mcp-data"
                    )
                    volumes[host_path] = directory

        # Fallback default volumes
        if not volumes:
            volumes = {
                "~/mcp-data": DEFAULT_DATA_PATH,
                "~/.mcp/logs": DEFAULT_LOGS_PATH,
            }

        return volumes

    def _extract_ports(self, template_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract port mappings from template configuration."""
        ports = {}

        # Check if template specifies ports
        if "ports" in template_data:
            ports.update(template_data["ports"])

        # Most MCP servers don't need exposed ports by default
        return ports

    def _extract_requirements(self, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements like tokens from template configuration."""
        requirements = {}

        # Check config schema for required tokens
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            if "token" in prop_name.lower() or "key" in prop_name.lower():
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    requirements["requires_token"] = env_mapping
                    break

        return requirements

    def _generate_mcp_config(
        self, template_data: Dict[str, Any], template_name: str
    ) -> str:
        """Generate MCP client configuration JSON."""
        config = {
            "servers": {
                f"{template_name}-server": {
                    "command": "docker",
                    "args": [
                        "exec",
                        "-i",
                        f"mcp-{template_name}",
                        "python",
                        "-m",
                        "src.server",
                    ],
                }
            }
        }

        # Add environment variables if template requires tokens
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        env_vars = {}
        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            if "token" in prop_name.lower() or "key" in prop_name.lower():
                env_mapping = prop_config.get("env_mapping")
                if env_mapping:
                    env_vars[env_mapping] = (
                        f"your-{prop_name.lower().replace('_', '-')}-here"
                    )

        if env_vars:
            config["servers"][f"{template_name}-server"]["env"] = env_vars

        return json.dumps(config, indent=2)


class DeploymentManager:
    """Unified deployment manager with backend abstraction."""

    def __init__(self, backend_type: str = "docker"):
        """Initialize deployment manager with specified backend."""
        self.backend_type = backend_type
        self.deployment_backend = self._get_deployment_backend()

    def _get_deployment_backend(self):
        """Get the appropriate deployment backend."""
        if self.backend_type == "docker":
            return DockerDeploymentService()
        elif self.backend_type == "kubernetes":
            try:
                return KubernetesDeploymentService()
            except ImportError as e:
                logger.warning(
                    "Kubernetes client not available, falling back to Docker: %s", e
                )
                return DockerDeploymentService()
        else:
            return MockDeploymentService()

    def deploy_template(
        self,
        template_id: str,
        configuration: Dict[str, Any],
        template_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Deploy an MCP server template."""
        try:
            logger.info(
                "Deploying template %s with configuration: %s",
                template_id,
                configuration,
            )

            result = self.deployment_backend.deploy_template(
                template_id=template_id,
                config=configuration,
                template_data=template_data,
            )

            logger.info("Successfully deployed template %s", template_id)
            return result

        except Exception as e:
            logger.error("Failed to deploy template %s: %s", template_id, e)
            raise

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all active deployments."""
        return self.deployment_backend.list_deployments()

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a deployment."""
        return self.deployment_backend.delete_deployment(deployment_name)

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get the status of a deployment."""
        return self.deployment_backend.get_deployment_status(deployment_name)


class DockerDeploymentService:
    """Docker deployment service using CLI commands."""

    def __init__(self):
        """Initialize Docker service."""
        self._ensure_docker_available()

    def _run_command(
        self, command: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            logger.debug("Running command: %s", " ".join(command))
            result = subprocess.run(  # nosec B603
                command, capture_output=True, text=True, check=check
            )
            logger.debug("Command output: %s", result.stdout)
            if result.stderr:
                logger.debug("Command stderr: %s", result.stderr)
            return result
        except subprocess.CalledProcessError as e:
            logger.error("Command failed: %s", " ".join(command))
            logger.error("Exit code: %d", e.returncode)
            logger.error("Stdout: %s", e.stdout)
            logger.error("Stderr: %s", e.stderr)
            raise

    def _ensure_docker_available(self):
        """Check if Docker is available and running."""
        try:
            result = self._run_command(["docker", "version", "--format", "json"])
            version_info = json.loads(result.stdout)
            logger.info(
                "Docker client version: %s",
                version_info.get("Client", {}).get("Version", "unknown"),
            )
            logger.info(
                "Docker server version: %s",
                version_info.get("Server", {}).get("Version", "unknown"),
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            logger.error("Docker is not available or not running: %s", exc)
            raise RuntimeError("Docker daemon is not available or not running") from exc

    def deploy_template(
        self, template_id: str, config: Dict[str, Any], template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy a template using Docker CLI."""
        # Generate container name
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        container_name = f"mcp-{template_id}-{timestamp}-{str(uuid.uuid4())[:8]}"

        # Prepare environment variables
        env_vars = []
        for key, value in config.items():
            # Avoid double MCP_ prefix
            if key.startswith("MCP_"):
                env_key = key
            else:
                env_key = f"MCP_{key.upper().replace(' ', '_').replace('-', '_')}"

            if isinstance(value, bool):
                env_value = "true" if value else "false"
            elif isinstance(value, list):
                env_value = ",".join(str(item) for item in value)
            else:
                env_value = str(value)
            env_vars.extend(["--env", f"{env_key}={env_value}"])

        # Add template default env vars
        template_env = template_data.get("env_vars", {})
        for key, value in template_env.items():
            env_vars.extend(["--env", f"{key}={value}"])

        # Prepare volumes
        volumes = []
        template_volumes = template_data.get("volumes", {})
        for host_path, container_path in template_volumes.items():
            # Expand user paths
            expanded_path = os.path.expanduser(host_path)
            os.makedirs(expanded_path, exist_ok=True)
            volumes.extend(["--volume", f"{expanded_path}:{container_path}"])

        # Get image
        image_name = template_data.get("image", f"mcp-{template_id}:latest")

        try:
            # Pull image
            self._run_command(["docker", "pull", image_name])

            # Build Docker run command
            docker_command = (
                [
                    "docker",
                    "run",
                    "--detach",
                    "--name",
                    container_name,
                    "--restart",
                    "unless-stopped",
                    "--label",
                    f"template={template_id}",
                    "--label",
                    "managed-by=mcp-template",
                ]
                + env_vars
                + volumes
                + [image_name]
            )

            # Run the container
            result = self._run_command(docker_command)
            container_id = result.stdout.strip()

            logger.info("Started container %s with ID %s", container_name, container_id)

            # Wait a moment for container to start
            import time

            time.sleep(2)

            return {
                "deployment_name": container_name,
                "container_id": container_id,
                "template_id": template_id,
                "configuration": config,
                "status": "deployed",
                "created_at": datetime.now().isoformat(),
                "image": image_name,
            }

        except Exception as e:
            # Cleanup on failure
            try:
                self._run_command(["docker", "rm", "-f", container_name], check=False)
            except Exception:
                pass
            raise e

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all MCP deployments."""
        try:
            # Get containers with the managed-by label
            result = self._run_command(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--filter",
                    "label=managed-by=mcp-template",
                    "--format",
                    "json",
                ]
            )

            deployments = []
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    try:
                        container = json.loads(line)
                        # Parse template from labels
                        labels = container.get("Labels", "")
                        template_name = "unknown"
                        if "template=" in labels:
                            # Extract template value from labels string
                            for label in labels.split(","):
                                if label.strip().startswith("template="):
                                    template_name = label.split("=", 1)[1]
                                    break

                        deployments.append(
                            {
                                "name": container["Names"],
                                "template": template_name,
                                "status": container["State"],
                                "created": container["CreatedAt"],
                                "image": container["Image"],
                            }
                        )
                    except json.JSONDecodeError:
                        continue

            return deployments

        except subprocess.CalledProcessError as e:
            logger.error("Failed to list deployments: %s", e)
            return []

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a deployment."""
        try:
            # Stop and remove the container
            self._run_command(["docker", "stop", deployment_name], check=False)
            self._run_command(["docker", "rm", deployment_name], check=False)
            logger.info("Deleted deployment %s", deployment_name)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to delete deployment %s: %s", deployment_name, e)
            return False

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get deployment status."""
        try:
            # Get container info
            result = self._run_command(
                ["docker", "inspect", deployment_name, "--format", "json"]
            )
            container_data = json.loads(result.stdout)[0]

            # Get container logs (last 10 lines)
            try:
                log_result = self._run_command(
                    ["docker", "logs", "--tail", "10", deployment_name], check=False
                )
                logs = log_result.stdout
            except Exception:
                logs = "Unable to fetch logs"

            return {
                "name": container_data["Name"].lstrip("/"),
                "status": container_data["State"]["Status"],
                "running": container_data["State"]["Running"],
                "created": container_data["Created"],
                "image": container_data["Config"]["Image"],
                "logs": logs,
            }
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as exc:
            logger.error(
                "Failed to get container info for %s: %s", deployment_name, exc
            )
            raise ValueError(f"Deployment {deployment_name} not found") from exc


class KubernetesDeploymentService:
    """Kubernetes deployment service (placeholder for future implementation)."""

    def __init__(self):
        """Initialize Kubernetes service."""
        raise ImportError("Kubernetes backend not yet implemented")

    def deploy_template(
        self, template_id: str, config: Dict[str, Any], template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy template to Kubernetes."""
        raise NotImplementedError

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List Kubernetes deployments."""
        raise NotImplementedError

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete Kubernetes deployment."""
        raise NotImplementedError

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get Kubernetes deployment status."""
        raise NotImplementedError


class MockDeploymentService:
    """Mock deployment service for testing."""

    def __init__(self):
        """Initialize mock service."""
        self.deployments = {}

    def deploy_template(
        self, template_id: str, config: Dict[str, Any], template_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock template deployment."""
        deployment_name = f"mcp-{template_id}-{datetime.now().strftime('%m%d-%H%M')}-{str(uuid.uuid4())[:8]}"

        deployment_info = {
            "deployment_name": deployment_name,
            "template_id": template_id,
            "configuration": config,
            "template_data": template_data,
            "status": "deployed",
            "created_at": datetime.now().isoformat(),
            "mock": True,
        }

        self.deployments[deployment_name] = deployment_info
        logger.info("Mock deployment created: %s", deployment_name)
        return deployment_info

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List mock deployments."""
        return [
            {
                "name": name,
                "template": info["template_id"],
                "status": "running",
                "created": info["created_at"],
                "mock": True,
            }
            for name, info in self.deployments.items()
        ]

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete mock deployment."""
        if deployment_name in self.deployments:
            del self.deployments[deployment_name]
            logger.info("Mock deployment deleted: %s", deployment_name)
            return True
        return False

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """Get mock deployment status."""
        if deployment_name in self.deployments:
            info = self.deployments[deployment_name]
            return {
                "name": deployment_name,
                "status": "running",
                "created": info["created_at"],
                "mock": True,
            }
        raise ValueError(f"Deployment {deployment_name} not found")


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

                # Deploy using unified manager
                result = self.deployment_manager.deploy_template(
                    template_id=template_name,
                    configuration=config,
                    template_data=template_copy,
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

    def _handle_nested_cli_config(
        self, nested_key: str, value: str, properties: Dict[str, Any]
    ) -> Optional[str]:
        """Handle nested CLI configuration using double underscore notation."""
        # Convert security__read_only to find read_only_mode in properties
        parts = nested_key.split("__")
        if len(parts) != 2:
            return None

        category, prop_name = parts

        # Try different property name patterns
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

        # If no direct match, try to construct environment variable name
        return f"MCP_{category.upper()}_{prop_name.upper()}"

    def _generate_mcp_config(
        self, template_name: str, container_name: str, template: Dict
    ):
        """Generate MCP configuration file."""
        config_file = self.config_dir / f"{template_name}.json"

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


def main():
    """
    Main entry point for the MCP deployer CLI.
    """

    parser = argparse.ArgumentParser(
        description="Deploy MCP server templates with zero configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-template list                    # List available templates
  mcp-template file-server             # Deploy file server with defaults
  mcp-template file-server --name fs   # Deploy with custom name
  mcp-template logs file-server        # View logs
  mcp-template stop file-server        # Stop deployment
  mcp-template shell file-server       # Open shell in container
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    subparsers.add_parser("list", help="List available templates")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new template")
    create_parser.add_argument(
        "template_id", nargs="?", help="Template ID (e.g., 'my-api-server')"
    )
    create_parser.add_argument(
        "--config-file", help="Path to template configuration file"
    )
    create_parser.add_argument(
        "--non-interactive", action="store_true", help="Run in non-interactive mode"
    )

    # Deploy command (default)
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a template")
    deploy_parser.add_argument("template", help="Template name to deploy")
    deploy_parser.add_argument("--name", help=CUSTOM_NAME_HELP)
    deploy_parser.add_argument("--data-dir", help="Custom data directory")
    deploy_parser.add_argument("--config-dir", help="Custom config directory")
    deploy_parser.add_argument(
        "--env", action="append", help="Environment variables (KEY=VALUE)"
    )
    deploy_parser.add_argument(
        "--config-file", help="Path to JSON/YAML configuration file"
    )
    deploy_parser.add_argument(
        "--config", action="append", help="Configuration values (KEY=VALUE)"
    )
    deploy_parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show available configuration options",
    )

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop a deployed template")
    stop_parser.add_argument("template", help="Template name to stop")
    stop_parser.add_argument("--name", help=CUSTOM_NAME_HELP)

    # Logs command
    logs_parser = subparsers.add_parser("logs", help="Show template logs")
    logs_parser.add_argument("template", help="Template name")
    logs_parser.add_argument("--name", help=CUSTOM_NAME_HELP)
    logs_parser.add_argument("-f", "--follow", action="store_true", help="Follow logs")

    # Shell command
    shell_parser = subparsers.add_parser("shell", help="Open shell in template")
    shell_parser.add_argument("template", help="Template name")
    shell_parser.add_argument("--name", help=CUSTOM_NAME_HELP)

    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        "cleanup", help="Clean up stopped/failed deployments"
    )
    cleanup_parser.add_argument(
        "template", nargs="?", help="Template name to clean up (optional)"
    )
    cleanup_parser.add_argument(
        "--all", action="store_true", help="Clean up all deployments"
    )

    # Parse arguments
    args = parser.parse_args()

    # Initialize deployer to check available templates
    deployer = MCPDeployer()
    available_templates = deployer.templates.keys()

    # Handle direct template deployment (backwards compatibility)
    if not args.command and len(sys.argv) > 1:
        template_name = sys.argv[1]
        if template_name in available_templates:
            args.command = "deploy"
            args.template = template_name

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == "list":
            deployer.list_templates()
        elif args.command == "create":
            creator = TemplateCreator()
            success = creator.create_template_interactive(
                template_id=getattr(args, "template_id", None),
                config_file=getattr(args, "config_file", None),
            )
            if not success:
                sys.exit(1)
        elif args.command == "deploy" or args.command in available_templates:
            template = args.template if hasattr(args, "template") else args.command

            # Show configuration options if requested
            if hasattr(args, "show_config") and args.show_config:
                deployer._show_config_options(template)
                return

            env_vars = {}
            if hasattr(args, "env") and args.env:
                for env_var in args.env:
                    key, value = env_var.split("=", 1)
                    env_vars[key] = value

            config_values = {}
            if hasattr(args, "config") and args.config:
                for config_var in args.config:
                    key, value = config_var.split("=", 1)
                    config_values[key] = value

            deployer.deploy(
                template,
                data_dir=getattr(args, "data_dir", None),
                config_dir=getattr(args, "config_dir", None),
                env_vars=env_vars,
                config_file=getattr(args, "config_file", None),
                config_values=config_values,
            )
        elif args.command == "stop":
            deployer.stop(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "logs":
            deployer.logs(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "shell":
            deployer.shell(args.template, custom_name=getattr(args, "name", None))
        elif args.command == "cleanup":
            deployer.cleanup(
                template_name=getattr(args, "template", None),
                all_containers=getattr(args, "all", False),
            )
        else:
            console.print(f"[red]❌ Unknown command: {args.command}[/red]")
            parser.print_help()

    except KeyboardInterrupt:
        console.print("\n[yellow]⏹️  Operation cancelled[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
