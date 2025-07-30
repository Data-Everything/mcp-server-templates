"""
Docker backend for managing deployments using Docker containers.
"""

import json
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel

from mcp_template.backends import BaseDeploymentBackend

logger = logging.getLogger(__name__)
console = Console()


class DockerDeploymentService(BaseDeploymentBackend):
    """Docker deployment service using CLI commands.

    This service manages container deployments using Docker CLI commands.
    It handles image pulling, container lifecycle, and provides status monitoring.
    """

    def __init__(self):
        """Initialize Docker service and verify Docker is available."""
        self._ensure_docker_available()

    # Docker Infrastructure Methods
    def _run_command(
        self, command: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute a shell command and return the result.

        Args:
            command: List of command parts to execute
            check: Whether to raise exception on non-zero exit code

        Returns:
            CompletedProcess with stdout, stderr, and return code

        Raises:
            subprocess.CalledProcessError: If command fails and check=True
        """

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
        """Check if Docker is available and running.

        Raises:
            RuntimeError: If Docker daemon is not available or not running
        """
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

    # Template Deployment Methods
    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """Deploy a template using Docker CLI.

        Args:
            template_id: Unique identifier for the template
            config: Configuration parameters for the deployment
            template_data: Template metadata including image, ports, commands, etc.
            pull_image: Whether to pull the container image before deployment

        Returns:
            Dict containing deployment information

        Raises:
            Exception: If deployment fails for any reason
        """
        container_name = self._generate_container_name(template_id)

        try:
            # Prepare deployment configuration
            env_vars = self._prepare_environment_variables(config, template_data)
            volumes = self._prepare_volume_mounts(template_data)
            ports = self._prepare_port_mappings(template_data)
            command_args = template_data.get("command", [])
            image_name = template_data.get("image", f"mcp-{template_id}:latest")

            # Pull image if requested
            if pull_image:
                self._run_command(["docker", "pull", image_name])

            # Deploy the container
            container_id = self._deploy_container(
                container_name,
                template_id,
                image_name,
                env_vars,
                volumes,
                ports,
                command_args,
            )

            # Wait for container to stabilize
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
            self._cleanup_failed_deployment(container_name)
            raise e

    def _generate_container_name(self, template_id: str) -> str:
        """Generate a unique container name for the template."""
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        return f"mcp-{template_id}-{timestamp}-{str(uuid.uuid4())[:8]}"

    def _prepare_environment_variables(
        self, config: Dict[str, Any], template_data: Dict[str, Any]
    ) -> List[str]:
        """Prepare environment variables for container deployment."""
        env_vars = []
        env_dict = {}  # Use dict to prevent duplicates

        # Process user configuration
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

            env_dict[env_key] = env_value

        # Add template default env vars (only if not already present)
        template_env = template_data.get("env_vars", {})
        for key, value in template_env.items():
            if key not in env_dict:  # Don't override user config
                env_dict[key] = str(value)

        # Convert dict to docker --env format
        for key, value in env_dict.items():
            env_vars.extend(["--env", f"{key}={value}"])

        return env_vars

    def _prepare_volume_mounts(self, template_data: Dict[str, Any]) -> List[str]:
        """Prepare volume mounts for container deployment."""
        volumes = []
        template_volumes = template_data.get("volumes", {})
        for host_path, container_path in template_volumes.items():
            # Expand user paths
            expanded_path = os.path.expanduser(host_path)
            os.makedirs(expanded_path, exist_ok=True)
            volumes.extend(["--volume", f"{expanded_path}:{container_path}"])
        return volumes

    def _prepare_port_mappings(self, template_data: Dict[str, Any]) -> List[str]:
        """Prepare port mappings for container deployment."""
        ports = []
        template_ports = template_data.get("ports", {})
        for host_port, container_port in template_ports.items():
            ports.extend(["-p", f"{host_port}:{container_port}"])
        return ports

    def _deploy_container(
        self,
        container_name: str,
        template_id: str,
        image_name: str,
        env_vars: List[str],
        volumes: List[str],
        ports: List[str],
        command_args: List[str],
    ) -> str:
        """Deploy the Docker container with all configuration."""
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
            + ports
            + env_vars
            + volumes
            + [image_name]
            + command_args
        )

        console.line()
        console.print(
            Panel(
                f"Running command: {' '.join(docker_command)}",
                title="Docker Command Execution",
                style="magenta",
            )
        )
        # Run the container
        result = self._run_command(docker_command)
        container_id = result.stdout.strip()

        logger.info("Started container %s with ID %s", container_name, container_id)
        return container_id

    def _cleanup_failed_deployment(self, container_name: str):
        """Clean up a failed deployment by removing the container."""
        try:
            self._run_command(["docker", "rm", "-f", container_name], check=False)
        except Exception:
            pass  # Ignore cleanup failures

    # Container Management Methods

    # Container Management Methods
    def list_deployments(self) -> List[Dict[str, Any]]:
        """List all MCP deployments managed by this Docker service.

        Returns:
            List of deployment information dictionaries
        """
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
        """Delete a deployment by stopping and removing the container.

        Args:
            deployment_name: Name of the deployment to delete

        Returns:
            True if deletion was successful, False otherwise
        """
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
        """Get detailed status of a deployment including logs.

        Args:
            deployment_name: Name of the deployment

        Returns:
            Dict containing deployment status, logs, and metadata

        Raises:
            ValueError: If deployment is not found
        """
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
