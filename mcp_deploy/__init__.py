#!/usr/bin/env python3
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
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

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

    def _generate_template_config(self, template_data: Dict[str, Any], template_dir: Path) -> Dict[str, Any]:
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
        
        # Generate MCP client configuration
        config["example_config"] = self._generate_mcp_config(template_data, template_dir.name)
        
        return config

    def _get_docker_image(self, template_data: Dict[str, Any], template_name: str) -> str:
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
                        env_vars[env_mapping] = separator.join(str(item) for item in default_value)
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
            if prop_config.get("type") == "array" and "directories" in prop_name.lower():
                # This is likely a directory configuration
                default_dirs = prop_config.get("default", [])
                for i, directory in enumerate(default_dirs):
                    host_path = f"~/mcp-data/{prop_name}_{i}" if len(default_dirs) > 1 else "~/mcp-data"
                    volumes[host_path] = directory
        
        # Fallback default volumes
        if not volumes:
            volumes = {
                "~/mcp-data": DEFAULT_DATA_PATH,
                "~/.mcp/logs": DEFAULT_LOGS_PATH
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

    def _generate_mcp_config(self, template_data: Dict[str, Any], template_name: str) -> str:
        """Generate MCP client configuration JSON."""
        config = {
            "servers": {
                f"{template_name}-server": {
                    "command": "docker",
                    "args": ["exec", "-i", f"mcp-{template_name}", "python", "-m", "src.server"]
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
                    env_vars[env_mapping] = f"your-{prop_name.lower().replace('_', '-')}-here"
        
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
            logger.info("Deploying template %s with configuration: %s", template_id, configuration)

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

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run a command and return the result."""
        try:
            logger.debug(f"Running command: {' '.join(command)}")
            result = subprocess.run(
                command, capture_output=True, text=True, check=check
            )
            logger.debug(f"Command output: {result.stdout}")
            if result.stderr:
                logger.debug(f"Command stderr: {result.stderr}")
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Exit code: {e.returncode}")
            logger.error(f"Stdout: {e.stdout}")
            logger.error(f"Stderr: {e.stderr}")
            raise

    def _ensure_docker_available(self):
        """Check if Docker is available and running."""
        try:
            result = self._run_command(["docker", "version", "--format", "json"])
            version_info = json.loads(result.stdout)
            logger.info(
                f"Docker client version: {version_info.get('Client', {}).get('Version', 'unknown')}"
            )
            logger.info(
                f"Docker server version: {version_info.get('Server', {}).get('Version', 'unknown')}"
            )
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Docker is not available or not running: {e}")
            raise RuntimeError("Docker daemon is not available or not running")

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
            env_key = f"MCP_{key.upper().replace(' ', '_').replace('-', '_')}"
            if isinstance(value, bool):
                env_value = 'true' if value else 'false'
            elif isinstance(value, list):
                env_value = ','.join(str(item) for item in value)
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
                    "managed-by=mcp-deploy",
                ]
                + env_vars
                + volumes
                + [image_name]
            )

            # Run the container
            result = self._run_command(docker_command)
            container_id = result.stdout.strip()

            logger.info(f"Started container {container_name} with ID {container_id}")

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
                    "label=managed-by=mcp-deploy",
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
                        
                        deployments.append({
                            "name": container["Names"],
                            "template": template_name,
                            "status": container["State"],
                            "created": container["CreatedAt"],
                            "image": container["Image"],
                        })
                    except json.JSONDecodeError:
                        continue

            return deployments

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list deployments: {e}")
            return []

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a deployment."""
        try:
            # Stop and remove the container
            self._run_command(["docker", "stop", deployment_name], check=False)
            self._run_command(["docker", "rm", deployment_name], check=False)
            logger.info(f"Deleted deployment {deployment_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to delete deployment {deployment_name}: {e}")
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
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to get container info for {deployment_name}: {e}")
            raise ValueError(f"Deployment {deployment_name} not found")


class KubernetesDeploymentService:
    """Kubernetes deployment service (placeholder for future implementation)."""

    def __init__(self):
        """Initialize Kubernetes service."""
        raise ImportError("Kubernetes backend not yet implemented")

    def deploy_template(self, template_id: str, config: Dict[str, Any], template_data: Dict[str, Any]) -> Dict[str, Any]:
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
        self, template_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock template deployment."""
        deployment_name = f"mcp-{template_id}-{datetime.now().strftime('%m%d-%H%M')}-{str(uuid.uuid4())[:8]}"

        deployment_info = {
            "deployment_name": deployment_name,
            "template_id": template_id,
            "configuration": config,
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

    def deploy(self, template_name: str, data_dir: Optional[str] = None, 
               config_dir: Optional[str] = None, env_vars: Optional[Dict[str, str]] = None):
        """Deploy a template using the unified deployment manager."""
        if template_name not in self.templates:
            console.print(f"[red]❌ Template '{template_name}' not found[/red]")
            console.print(f"Available templates: {', '.join(self.templates.keys())}")
            return False

        template = self.templates[template_name]
        
        console.print(Panel(f"🚀 Deploying MCP Template: [cyan]{template_name}[/cyan]", 
                          title="Deployment", border_style="blue"))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Deploying {template_name}...", total=None)

            try:
                # Prepare configuration
                config = {}
                if env_vars:
                    config.update(env_vars)

                # Check for required tokens
                if "requires_token" in template:
                    token_name = template["requires_token"]
                    if token_name not in config and token_name not in os.environ:
                        console.print(f"[red]❌ Required environment variable {token_name} not provided[/red]")
                        console.print(f"Set it with: --env {token_name}=your-token-here")
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
                                template_copy["volumes"][key] = template_copy["volumes"][key].replace(
                                    "/data", data_dir
                                )

                    if config_dir:
                        for key in template_copy["volumes"]:
                            if "/config" in template_copy["volumes"][key]:
                                template_copy["volumes"][key] = template_copy["volumes"][key].replace(
                                    "/config", config_dir
                                )

                # Deploy using unified manager
                result = self.deployment_manager.deploy_template(
                    template_id=template_name,
                    configuration=config,
                    template_data=template_copy
                )

                progress.update(task, completed=True)
                
                # Generate MCP config
                self._generate_mcp_config(template_name, result['deployment_name'], template)
                
                # Success message
                console.print(Panel(
                    f"[green]✅ Successfully deployed {template_name}![/green]\n\n"
                    f"[cyan]📋 Details:[/cyan]\n"
                    f"• Container: {result['deployment_name']}\n"
                    f"• Image: {result.get('image', template['image'])}\n"
                    f"• Status: {result.get('status', 'deployed')}\n\n"
                    f"[cyan]🔧 MCP Configuration:[/cyan]\n"
                    f"Config saved to: ~/.mcp/{template_name}.json\n\n"
                    f"[cyan]💡 Management:[/cyan]\n"
                    f"• View logs: mcp-deploy logs {template_name}\n"
                    f"• Stop: mcp-deploy stop {template_name}\n"
                    f"• Shell: mcp-deploy shell {template_name}",
                    title="🎉 Deployment Complete",
                    border_style="green"
                ))
                
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
            target_deployments = [d for d in deployments if d["template"] == template_name]
            
            if not target_deployments:
                console.print(f"[yellow]⚠️  No running deployments found for {template_name}[/yellow]")
                return False

            # If custom name provided, find exact match
            if custom_name:
                target_deployments = [d for d in target_deployments if custom_name in d["name"]]
                if not target_deployments:
                    console.print(f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]")
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
            target_deployments = [d for d in deployments if d["template"] == template_name]
            
            if not target_deployments:
                console.print(f"[yellow]⚠️  No deployments found for {template_name}[/yellow]")
                return

            if custom_name:
                target_deployments = [d for d in target_deployments if custom_name in d["name"]]
                if not target_deployments:
                    console.print(f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]")
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
            target_deployments = [d for d in deployments if d["template"] == template_name]
            
            if not target_deployments:
                console.print(f"[yellow]⚠️  No deployments found for {template_name}[/yellow]")
                return

            if custom_name:
                target_deployments = [d for d in target_deployments if custom_name in d["name"]]
                if not target_deployments:
                    console.print(f"[yellow]⚠️  No deployment found with name containing '{custom_name}'[/yellow]")
                    return

            deployment = target_deployments[0]
            container_name = deployment["name"]
            
            console.print(f"[blue]🐚 Opening shell in {container_name}...[/blue]")
            subprocess.run(["docker", "exec", "-it", container_name, "/bin/sh"], check=True)
            
        except subprocess.CalledProcessError:
            console.print("[red]❌ Failed to open shell[/red]")
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")

    def cleanup(self, template_name: Optional[str] = None, all_containers: bool = False):
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
                console.print(f"[yellow]🧹 Cleaning up all {len(deployments)} MCP deployments...[/yellow]")
            elif template_name:
                target_deployments = [d for d in deployments if d["template"] == template_name]
                if not target_deployments:
                    console.print(f"[yellow]⚠️  No deployments found for template '{template_name}'[/yellow]")
                    return True
                console.print(f"[yellow]🧹 Cleaning up {len(target_deployments)} '{template_name}' deployments...[/yellow]")
            else:
                # Interactive mode - show list and ask
                console.print("\n[cyan]📋 Current deployments:[/cyan]")
                for i, deployment in enumerate(deployments, 1):
                    console.print(f"  {i}. {deployment['name']} ({deployment['template']}) - {deployment['status']}")
                
                # For now, cleanup all stopped/failed containers
                target_deployments = [d for d in deployments if d["status"] in ["exited", "dead", "restarting"]]
                if not target_deployments:
                    console.print("[green]✅ No stopped or failed containers to cleanup[/green]")
                    return True
                console.print(f"[yellow]🧹 Cleaning up {len(target_deployments)} stopped/failed containers...[/yellow]")

            # Clean up deployments
            success_count = 0
            for deployment in target_deployments:
                if self.deployment_manager.delete_deployment(deployment["name"]):
                    console.print(f"[green]✅ Cleaned up {deployment['name']}[/green]")
                    success_count += 1
                else:
                    console.print(f"[red]❌ Failed to cleanup {deployment['name']}[/red]")

            if success_count > 0:
                console.print(f"\n[green]🎉 Successfully cleaned up {success_count} deployments![/green]")
            else:
                console.print("\n[yellow]⚠️  No deployments were cleaned up[/yellow]")
                
            return success_count > 0

        except Exception as e:
            console.print(f"[red]❌ Error during cleanup: {e}[/red]")
            return False

    def _generate_mcp_config(self, template_name: str, container_name: str, template: Dict):
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

def main():
    parser = argparse.ArgumentParser(
        description="Deploy MCP server templates with zero configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-deploy list                    # List available templates
  mcp-deploy file-server             # Deploy file server with defaults
  mcp-deploy file-server --name fs   # Deploy with custom name
  mcp-deploy logs file-server        # View logs
  mcp-deploy stop file-server        # Stop deployment
  mcp-deploy shell file-server       # Open shell in container
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    subparsers.add_parser("list", help="List available templates")
    
    # Deploy command (default)
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a template")
    deploy_parser.add_argument("template", help="Template name to deploy")
    deploy_parser.add_argument("--name", help=CUSTOM_NAME_HELP)
    deploy_parser.add_argument("--data-dir", help="Custom data directory")
    deploy_parser.add_argument("--config-dir", help="Custom config directory")
    deploy_parser.add_argument("--env", action="append", help="Environment variables (KEY=VALUE)")
    
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
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up stopped/failed deployments")
    cleanup_parser.add_argument("template", nargs="?", help="Template name to clean up (optional)")
    cleanup_parser.add_argument("--all", action="store_true", help="Clean up all deployments")
    
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
        elif args.command == "deploy" or args.command in available_templates:
            template = args.template if hasattr(args, 'template') else args.command
            
            env_vars = {}
            if hasattr(args, 'env') and args.env:
                for env_var in args.env:
                    key, value = env_var.split('=', 1)
                    env_vars[key] = value
            
            deployer.deploy(
                template,
                data_dir=getattr(args, 'data_dir', None),
                config_dir=getattr(args, 'config_dir', None),
                env_vars=env_vars
            )
        elif args.command == "stop":
            deployer.stop(args.template, custom_name=getattr(args, 'name', None))
        elif args.command == "logs":
            deployer.logs(args.template, custom_name=getattr(args, 'name', None))
        elif args.command == "shell":
            deployer.shell(args.template, custom_name=getattr(args, 'name', None))
        elif args.command == "cleanup":
            deployer.cleanup(
                template_name=getattr(args, 'template', None),
                all_containers=getattr(args, 'all', False)
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
