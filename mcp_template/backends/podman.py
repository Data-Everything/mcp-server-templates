"""
Podman backend for managing deployments using Podman containers.

This module provides the PodmanDeploymentService class, which manages container deployments
using the Podman CLI. It supports image pulling, container lifecycle management, status monitoring,
and stdio tool execution for MCP server templates. The API is designed to mirror the Docker backend
for drop-in replacement and compatibility.
"""

import json
import logging
import os
import socket
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

STDIO_TIMEOUT = os.getenv("MCP_STDIO_TIMEOUT", 30)
if isinstance(STDIO_TIMEOUT, str):
    try:
        STDIO_TIMEOUT = int(STDIO_TIMEOUT)
    except ValueError:
        logger.warning(
            "Invalid MCP_STDIO_TIMEOUT value '%s', using default 30 seconds",
            os.getenv("MCP_STDIO_TIMEOUT", "30"),
        )
        STDIO_TIMEOUT = 30


class PodmanDeploymentService(BaseDeploymentBackend):
    """Podman deployment service using CLI commands.

    This service manages container deployments using Podman CLI commands.
    It handles image pulling, container lifecycle, and provides status monitoring.
    """

    def __init__(self):
        """
        Initialize Podman service and verify Podman is available.
        Raises:
            RuntimeError: If Podman is not available or not running.
        """
        self._ensure_podman_available()

    def _run_command(
        self, command: List[str], check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Execute a shell command and return the result.

        Args:
            command: List of command parts to execute.
            check: Whether to raise exception on non-zero exit code.

        Returns:
            CompletedProcess with stdout, stderr, and return code.

        Raises:
            subprocess.CalledProcessError: If command fails and check=True.
        """
        try:
            logger.debug("Running command: %s", " ".join(command))
            result = subprocess.run(
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

    def _ensure_podman_available(self):
        """
        Check if Podman is available and running.

        Raises:
            RuntimeError: If Podman is not available or not running.
        """
        try:
            # Podman --version is the only reliable way to check availability in all environments
            result = self._run_command(["podman", "--version"])
            version_line = result.stdout.strip() or result.stderr.strip()
            if not version_line or "podman version" not in version_line.lower():
                logger.error("Podman --version output unexpected: %s", version_line)
                raise RuntimeError("Podman is not available or not running")
            logger.info("Podman version detected: %s", version_line)
        except subprocess.CalledProcessError as exc:
            logger.error("Podman is not available or not running: %s", exc)
            raise RuntimeError("Podman daemon is not available or not running") from exc

    def _generate_container_name(self, template_id: str) -> str:
        """
        Generate a unique container name for the template.

        Args:
            template_id: Unique identifier for the template.

        Returns:
            A unique container name string.
        """
        timestamp = datetime.now().strftime("%m%d-%H%M%S")
        return f"mcp-{template_id}-{timestamp}-{str(uuid.uuid4())[:8]}"

    def _prepare_environment_variables(
        self, config: Dict[str, Any], template_data: Dict[str, Any]
    ) -> List[str]:
        """
        Prepare environment variables for container deployment.

        Args:
            config: User configuration for the deployment.
            template_data: Template metadata including config schema and env vars.

        Returns:
            List of --env arguments for Podman CLI.
        """
        env_vars = []
        env_dict = {}
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})
        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping", prop_name.upper())
            default_value = prop_config.get("default")
            if default_value is not None:
                env_dict[env_mapping] = str(default_value)
        for key, value in config.items():
            if isinstance(value, bool):
                env_value = "true" if value else "false"
            elif isinstance(value, list):
                env_value = ",".join(str(item) for item in value)
            else:
                env_value = str(value)
            env_key = key
            for prop_name, prop_config in properties.items():
                if prop_name == key:
                    env_key = prop_config.get("env_mapping", key.upper())
                    break
            env_dict[env_key] = env_value
        template_env = template_data.get("env_vars", {})
        for key, value in template_env.items():
            if key not in env_dict:
                env_dict[key] = str(value)
        for key, value in env_dict.items():
            if (
                " " in value
                or '"' in value
                or "'" in value
                or "&" in value
                or "|" in value
            ):
                escaped_value = value.replace('"', '\\"')
                env_vars.extend(["--env", f'{key}="{escaped_value}"'])
            else:
                env_vars.extend(["--env", f"{key}={value}"])
        return env_vars

    def _prepare_volume_mounts(self, template_data: Dict[str, Any]) -> List[str]:
        """
        Prepare volume mounts for container deployment.

        Args:
            template_data: Template metadata including volume mappings.

        Returns:
            List of --volume arguments for Podman CLI.
        """
        volumes = []
        template_volumes = template_data.get("volumes", {})
        for host_path, container_path in template_volumes.items():
            expanded_path = os.path.expanduser(host_path)
            os.makedirs(expanded_path, exist_ok=True)
            volumes.extend(["--volume", f"{expanded_path}:{container_path}"])
        return volumes

    def _prepare_port_mappings(self, template_data: Dict[str, Any]) -> List[str]:
        """
        Prepare port mappings for container deployment, using a free port if needed.

        Args:
            template_data: Template metadata including port mappings.

        Returns:
            List of -p arguments for Podman CLI.
        """
        ports = []
        template_ports = template_data.get("ports", {})
        for host_port, container_port in template_ports.items():
            port_to_use = int(host_port)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("", port_to_use))
                    s.listen(1)
                except OSError:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free_sock:
                        free_sock.bind(("", 0))
                        port_to_use = free_sock.getsockname()[1]
                    logger.warning(
                        f"Port {host_port} is in use, remapping to free port {port_to_use} for container port {container_port}"
                    )
            ports.extend(["-p", f"{port_to_use}:{container_port}"])
        return ports

    @staticmethod
    def _identify_stdio_deployment(env_vars: List[str]) -> bool:
        """
        Identify if the deployment is using stdio transport.

        Args:
            env_vars: List of environment variable arguments.

        Returns:
            True if stdio transport is detected, False otherwise or None if not set.
        """
        is_stdio = None
        for env_var in env_vars:
            if len(env_var.split("=")) == 2:
                key, value = env_var.split("=", 1)
                if key == "MCP_TRANSPORT":
                    if value == "stdio":
                        is_stdio = True
                    else:
                        is_stdio = False
                    break
        return is_stdio

    def _build_podman_command(
        self,
        container_name: str,
        template_id: str,
        image_name: str,
        env_vars: List[str],
        volumes: List[str],
        ports: List[str],
        command_args: List[str],
        is_stdio: bool = False,
        detached: bool = True,
    ) -> List[str]:
        """
        Build the Podman command with all configuration.

        Args:
            container_name: Name for the container.
            template_id: Template identifier.
            image_name: Name of the image to run.
            env_vars: List of environment variable arguments.
            volumes: List of volume mount arguments.
            ports: List of port mapping arguments.
            command_args: List of command arguments for the container.
            is_stdio: Whether this is a stdio deployment.
            detached: Whether to run the container in detached mode.

        Returns:
            List of command parts for subprocess execution.
        """
        podman_command = [
            "podman",
            "run",
        ]
        if detached:
            podman_command.append("--detach")
        podman_command.extend(
            [
                "--name",
                container_name,
            ]
        )
        if not is_stdio:
            podman_command.extend(["--restart", "unless-stopped"])
        podman_command.extend(
            [
                "--label",
                f"template={template_id}",
                "--label",
                "managed-by=mcp-template",
            ]
        )
        podman_command.extend(ports)
        podman_command.extend(env_vars)
        podman_command.extend(volumes)
        podman_command.append(image_name)
        podman_command.extend(command_args)
        return podman_command

    def _deploy_container(
        self,
        container_name: str,
        template_id: str,
        image_name: str,
        env_vars: List[str],
        volumes: List[str],
        ports: List[str],
        command_args: List[str],
        is_stdio: bool = False,
    ) -> str:
        """
        Deploy the Podman container with all configuration.

        Args:
            container_name: Name for the container.
            template_id: Template identifier.
            image_name: Name of the image to run.
            env_vars: List of environment variable arguments.
            volumes: List of volume mount arguments.
            ports: List of port mapping arguments.
            command_args: List of command arguments for the container.
            is_stdio: Whether this is a stdio deployment.

        Returns:
            The container ID as a string.
        """
        podman_command = self._build_podman_command(
            container_name,
            template_id,
            image_name,
            env_vars,
            volumes,
            ports,
            command_args,
            is_stdio,
            detached=True,
        )
        console.line()
        console.print(
            Panel(
                f"Running command: {' '.join(podman_command)}",
                title="Podman Command Execution",
                style="magenta",
            )
        )
        result = self._run_command(podman_command)
        container_id = result.stdout.strip()
        logger.info("Started container %s with ID %s", container_name, container_id)
        return container_id

    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Deploy a template using Podman CLI.

        Args:
            template_id: Unique identifier for the template.
            config: Configuration parameters for the deployment.
            template_data: Template metadata including image, ports, commands, etc.
            pull_image: Whether to pull the container image before deployment.

        Returns:
            Dict containing deployment information.

        Raises:
            Exception: If deployment fails for any reason.
        """
        env_vars = self._prepare_environment_variables(config, template_data)
        is_stdio = self._identify_stdio_deployment(env_vars)
        template_transport = template_data.get("transport", {})
        default_transport = template_transport.get("default", "http")
        if is_stdio is True or (is_stdio is None and default_transport == "stdio"):
            from mcp_template.tools.discovery import ToolDiscovery

            tool_discovery = ToolDiscovery()
            try:
                discovery_result = tool_discovery.discover_tools(
                    template_id,
                    template_data,
                    use_cache=True,
                    force_refresh=False,
                )
                tools = discovery_result.get("tools", [])
                tool_names = [tool.get("name", "unknown") for tool in tools]
            except Exception as e:
                logger.warning("Failed to discover tools for %s: %s", template_id, e)
                tool_names = []
            console.line()
            console.print(
                Panel(
                    f"❌ [red]Cannot deploy stdio transport MCP servers[/red]\n\n"
                    f"The template [cyan]{template_id}[/cyan] uses stdio transport, which doesn't require deployment.\n"
                    f"Stdio MCP servers run interactively and cannot be deployed as persistent containers.\n\n"
                    f"[yellow]Available tools in this template:[/yellow]\n"
                    + (
                        f"  • {chr(10).join(f'  • {tool}' for tool in tool_names)}"
                        if tool_names
                        else "  • No tools discovered"
                    )
                    + "\n\n"
                    f"[green]To use this template, run tools directly:[/green]\n"
                    f"  mcpt> tools {template_id}                    # List available tools\n"
                    f"  mcpt run-tool {template_id} <tool_name>     # Run a specific tool\n"
                    f"  echo '{json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})}' | \\\n"
                    f"    podman run -i --rm {template_data.get('image', template_data.get('podman_image', f'mcp-{template_id}:latest'))}",
                    title="Stdio Transport Detected",
                    border_style="yellow",
                )
            )
            raise ValueError(
                f"Cannot deploy stdio transport template '{template_id}'. "
                "Stdio templates run interactively and don't support persistent deployment."
            )
        container_name = self._generate_container_name(template_id)
        try:
            volumes = self._prepare_volume_mounts(template_data)
            ports = self._prepare_port_mappings(template_data)
            command_args = template_data.get("command", [])
            image_name = template_data.get("image", f"mcp-{template_id}:latest")
            if pull_image:
                self._run_command(["podman", "pull", image_name])
            container_id = self._deploy_container(
                container_name,
                template_id,
                image_name,
                env_vars,
                volumes,
                ports,
                command_args,
                is_stdio=is_stdio,
            )
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
            self._cleanup_failed_deployment(container_name)
            raise e

    def run_stdio_command(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        json_input: str,
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """
        Run a stdio MCP command directly and return the result.

        Args:
            template_id: Unique identifier for the template.
            config: Configuration parameters for the deployment.
            template_data: Template metadata including image, ports, commands, etc.
            json_input: JSON-RPC input for the tool call.
            pull_image: Whether to pull the container image before execution.

        Returns:
            Dict containing execution result, stdout, stderr, and status.
        """
        try:
            env_vars = self._prepare_environment_variables(config, template_data)
            env_dict = {}
            for i in range(0, len(env_vars), 2):
                if i + 1 < len(env_vars) and env_vars[i] == "--env":
                    key_value = env_vars[i + 1]
                    if "=" in key_value:
                        key, value = key_value.split("=", 1)
                        env_dict[key] = value
            env_dict["MCP_TRANSPORT"] = "stdio"
            env_vars = []
            for key, value in env_dict.items():
                if (
                    " " in value
                    or '"' in value
                    or "'" in value
                    or "&" in value
                    or "|" in value
                ):
                    escaped_value = value.replace('"', '\\"')
                    env_vars.extend(["--env", f'{key}="{escaped_value}"'])
                else:
                    env_vars.extend(["--env", f"{key}={value}"])
            volumes = self._prepare_volume_mounts(template_data)
            command_args = template_data.get("command", [])
            image_name = template_data.get("image", f"mcp-{template_id}:latest")
            if pull_image:
                self._run_command(["podman", "pull", image_name])
            container_name = f"mcp-{template_id}-stdio-{str(uuid.uuid4())[:8]}"
            podman_command = self._build_podman_command(
                container_name,
                template_id,
                image_name,
                env_vars,
                volumes,
                [],
                command_args,
                is_stdio=True,
                detached=False,
            )
            podman_command.insert(2, "-i")
            podman_command.insert(3, "--rm")
            logger.info("Running stdio command for template %s", template_id)
            logger.debug("Podman command: %s", " ".join(podman_command))
            try:
                tool_request = json.loads(json_input)
                tool_method = tool_request.get("method")
                tool_params = tool_request.get("params", {})
            except json.JSONDecodeError:
                return {
                    "template_id": template_id,
                    "status": "failed",
                    "error": "Invalid JSON input",
                    "executed_at": datetime.now().isoformat(),
                }
            mcp_commands = [
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "mcp-template", "version": "1.0.0"},
                        },
                    }
                ),
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": tool_method,
                        "params": tool_params,
                    }
                ),
            ]
            full_input = "\n".join(mcp_commands)
            logger.debug("Full MCP input: %s", full_input)
            bash_command = [
                "/bin/bash",
                "-c",
                f"podman run -i --rm {' '.join(env_vars)} {' '.join(volumes)} {' '.join(['--label', f'template={template_id}'])} {image_name} {' '.join(command_args)} << 'EOF'\n{full_input}\nEOF",
            ]
            result = subprocess.run(
                bash_command,
                capture_output=True,
                text=True,
                check=True,
                timeout=STDIO_TIMEOUT,
            )
            return {
                "template_id": template_id,
                "status": "completed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "executed_at": datetime.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logger.error("Stdio command failed for template %s: %s", template_id, e)
            return {
                "template_id": template_id,
                "status": "failed",
                "stdout": e.stdout or "",
                "stderr": e.stderr or "",
                "error": str(e),
                "executed_at": datetime.now().isoformat(),
            }
        except subprocess.TimeoutExpired:
            logger.error(
                "Stdio command timed out for template %s after %d seconds",
                template_id,
                STDIO_TIMEOUT,
            )
            return {
                "template_id": template_id,
                "status": "timeout",
                "error": f"Command execution timed out after {STDIO_TIMEOUT} seconds",
                "executed_at": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error("Unexpected error running stdio command: %s", e)
            return {
                "template_id": template_id,
                "status": "error",
                "error": str(e),
                "executed_at": datetime.now().isoformat(),
            }

    def _cleanup_failed_deployment(self, container_name: str):
        """
        Clean up a failed deployment by removing the container.

        Args:
            container_name: Name of the container to remove.
        """
        try:
            self._run_command(["podman", "rm", "-f", container_name], check=False)
        except Exception:
            pass

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List all MCP deployments managed by this Podman service.

        Returns:
            List of deployment information dictionaries.
        """
        try:
            result = self._run_command(
                [
                    "podman",
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
                        labels = container.get("Labels", "")
                        template_name = "unknown"
                        if "template=" in labels:
                            for label in labels.split(","):
                                if label.strip().startswith("template="):
                                    template_name = label.split("=", 1)[1]
                                    break
                        deployments.append(
                            {
                                "id": container["ID"],
                                "name": container["Names"],
                                "template": template_name,
                                "status": container["State"],
                                "since": container["RunningFor"],
                                "image": container["Image"],
                                "ports": container.get("Ports", "")
                                .split(", ")[-1]
                                .split(":")[-1]
                                .split("/")[0],
                            }
                        )
                    except json.JSONDecodeError:
                        continue
            return deployments
        except subprocess.CalledProcessError as e:
            logger.error("Failed to list deployments: %s", e)
            return []

    def delete_deployment(self, deployment_name: str) -> bool:
        """
        Delete a deployment by stopping and removing the container.

        Args:
            deployment_name: Name of the deployment to delete.

        Returns:
            True if deletion was successful, False otherwise.
        """
        try:
            self._run_command(["podman", "stop", deployment_name], check=False)
            self._run_command(["podman", "rm", deployment_name], check=False)
            logger.info("Deleted deployment %s", deployment_name)
            return True
        except subprocess.CalledProcessError as e:
            logger.error("Failed to delete deployment %s: %s", deployment_name, e)
            return False

    def get_deployment_status(self, deployment_name: str) -> Dict[str, Any]:
        """
        Get detailed status of a deployment including logs.

        Args:
            deployment_name: Name of the deployment.

        Returns:
            Dict containing deployment status, logs, and metadata.

        Raises:
            ValueError: If deployment is not found.
        """
        try:
            result = self._run_command(
                ["podman", "inspect", deployment_name, "--format", "json"]
            )
            container_data = json.loads(result.stdout)[0]
            try:
                log_result = self._run_command(
                    ["podman", "logs", "--tail", "10", deployment_name], check=False
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

    def _build_internal_image(
        self, template_id: str, image_name: str, template_data: Dict[str, Any]
    ) -> None:
        """
        Build Podman image for internal templates.

        Args:
            template_id: Template identifier.
            image_name: Name of the image to build.
            template_data: Template metadata.

        Raises:
            ValueError: If Dockerfile is missing for the template.
        """
        import os
        from pathlib import Path

        from mcp_template.template.utils.discovery import TemplateDiscovery

        discovery = TemplateDiscovery()
        template_dir = discovery.template_root / template_id
        if not template_dir.exists() or not (template_dir / "Dockerfile").exists():
            logger.error(
                f"Dockerfile not found for internal template {template_id} in {template_dir}"
            )
            raise ValueError(f"Internal template {template_id} missing Dockerfile")
        logger.info(f"Building image {image_name} for internal template {template_id}")
        build_command = ["podman", "build", "-t", image_name, str(template_dir)]
        self._run_command(build_command)
