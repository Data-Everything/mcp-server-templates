"""
Docker backend for managing deployments using Docker containers.
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
        # Prepare deployment configuration
        env_vars = self._prepare_environment_variables(config, template_data)

        # Check if this is a stdio deployment
        is_stdio = self._identify_stdio_deployment(env_vars)

        # Also check the template's default transport
        template_transport = template_data.get("transport", {})
        default_transport = template_transport.get("default", "http")
        # If stdio transport is detected, prevent deployment
        if is_stdio is True or (is_stdio is None and default_transport == "stdio"):
            # Import here to avoid circular import
            from mcp_template.tools.discovery import ToolDiscovery

            tool_discovery = ToolDiscovery()

            # Get available tools for this template
            try:
                discovery_result = tool_discovery.discover_tools(
                    template_id,
                    template_data.get("template_dir", ""),
                    template_data,
                    use_cache=True,
                    force_refresh=False,
                )
                tools = discovery_result.get("tools", [])
                tool_names = [tool.get("name", "unknown") for tool in tools]
            except Exception as e:
                logger.warning("Failed to discover tools for %s: %s", template_id, e)
                tool_names = []

            # Create error message with available tools
            console.line()
            console.print(
                Panel(
                    f"❌ [red]Cannot deploy stdio transport MCP servers[/red]\n\n"
                    f"The template [cyan]{template_id}[/cyan] uses stdio transport, which doesn't require deployment.\n"
                    f"Stdio MCP servers run interactively and cannot be deployed as persistent containers.\n\n"
                    f"[yellow]Available tools in this template:[/yellow]\n"
                    + (
                        f"{chr(10).join(f'  • {tool}' for tool in tool_names)}"
                        if tool_names
                        else "  • No tools discovered"
                    )
                    + "\n\n"
                    f"[green]To use this template, run tools directly:[/green]\n"
                    f"  mcpt interactive\n"
                    f"  mcpt> tools {template_id}                    # List available tools\n"
                    f"  mcpt> call {template_id} <tool_name>     # Run a specific tool\n"
                    f"  echo '{json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'})}' | \\\n"
                    f"    docker run -i --rm {template_data.get('image', template_data.get('docker_image', f'mcp-{template_id}:latest'))}",
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
                is_stdio=is_stdio,
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

        # First, add defaults from config schema
        config_schema = template_data.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping", prop_name.upper())
            default_value = prop_config.get("default")

            if default_value is not None:
                env_dict[env_mapping] = str(default_value)

        # Process user configuration (override defaults)
        for key, value in config.items():
            if isinstance(value, bool):
                env_value = "true" if value else "false"
            elif isinstance(value, list):
                env_value = ",".join(str(item) for item in value)
            else:
                env_value = str(value)

            # Check if this key maps to an env variable through config schema
            env_key = key
            for prop_name, prop_config in properties.items():
                if prop_name == key:
                    env_key = prop_config.get("env_mapping", key.upper())
                    break

            env_dict[env_key] = env_value

        # Add template default env vars (only if not already present)
        template_env = template_data.get("env_vars", {})
        for key, value in template_env.items():
            if key not in env_dict:  # Don't override user config or schema defaults
                env_dict[key] = str(value)

        # Convert dict to docker --env format
        for key, value in env_dict.items():
            # Properly quote values that contain spaces or special characters
            if (
                " " in value
                or '"' in value
                or "'" in value
                or "&" in value
                or "|" in value
            ):
                # Escape double quotes and wrap in double quotes
                escaped_value = value.replace('"', '\\"')
                env_vars.extend(["--env", f'{key}="{escaped_value}"'])
            else:
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
        """Prepare port mappings for container deployment, using a free port if needed."""
        ports = []
        template_ports = template_data.get("ports", {})
        for host_port, container_port in template_ports.items():
            port_to_use = int(host_port)
            # Check if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    s.bind(("", port_to_use))
                    s.listen(1)
                except OSError:
                    # Port is in use, find a free port
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as free_sock:
                        free_sock.bind(("", 0))
                        port_to_use = free_sock.getsockname()[1]
                    logger.warning(
                        "Port %s is in use, remapping to free port %s for container port %s",
                        host_port,
                        port_to_use,
                        container_port,
                    )
            ports.extend(["-p", f"{port_to_use}:{container_port}"])
        return ports

    @staticmethod
    def _identify_stdio_deployment(
        env_vars: List[str],
    ) -> bool:
        """Identify if the deployment is using stdio transport."""

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

    def _build_docker_command(
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
        """Build the Docker command with all configuration."""
        docker_command = [
            "docker",
            "run",
        ]

        if detached:
            docker_command.append("--detach")

        docker_command.extend(
            [
                "--name",
                container_name,
            ]
        )

        if not is_stdio:
            docker_command.extend(["--restart", "unless-stopped"])

        docker_command.extend(
            [
                "--label",
                f"template={template_id}",
                "--label",
                "managed-by=mcp-template",
            ]
        )

        docker_command.extend(ports)
        docker_command.extend(env_vars)
        docker_command.extend(volumes)
        docker_command.append(image_name)
        docker_command.extend(command_args)

        return docker_command

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
        """Deploy the Docker container with all configuration."""
        # Build the Docker command
        docker_command = self._build_docker_command(
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

    def run_stdio_command(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        json_input: str,
        pull_image: bool = True,
    ) -> Dict[str, Any]:
        """Run a stdio MCP command directly and return the result."""
        try:
            # Prepare deployment configuration
            env_vars = self._prepare_environment_variables(config, template_data)

            # CRITICAL: Ensure MCP_TRANSPORT=stdio is set for stdio execution
            # Convert env_vars from list format to dict to ensure we can override
            env_dict = {}
            for i in range(0, len(env_vars), 2):
                if i + 1 < len(env_vars) and env_vars[i] == "--env":
                    key_value = env_vars[i + 1]
                    if "=" in key_value:
                        key, value = key_value.split("=", 1)
                        env_dict[key] = value

            # Override with stdio transport
            env_dict["MCP_TRANSPORT"] = "stdio"

            # Convert back to docker --env format
            env_vars = []
            for key, value in env_dict.items():
                # Properly quote values that contain spaces or special characters
                if (
                    " " in value
                    or '"' in value
                    or "'" in value
                    or "&" in value
                    or "|" in value
                ):
                    # Escape double quotes and wrap in double quotes
                    escaped_value = value.replace('"', '\\"')
                    env_vars.extend(["--env", f'{key}="{escaped_value}"'])
                else:
                    env_vars.extend(["--env", f"{key}={value}"])

            volumes = self._prepare_volume_mounts(template_data)
            command_args = template_data.get("command", [])
            image_name = template_data.get("image", f"mcp-{template_id}:latest")

            # Pull image if requested
            if pull_image:
                self._run_command(["docker", "pull", image_name])

            # Generate a temporary container name for this execution
            container_name = f"mcp-{template_id}-stdio-{str(uuid.uuid4())[:8]}"

            # Build the Docker command for interactive stdio execution
            docker_command = self._build_docker_command(
                container_name,
                template_id,
                image_name,
                env_vars,
                volumes,
                [],  # No port mappings for stdio
                command_args,
                is_stdio=True,
                detached=False,  # Run interactively
            )

            # Add interactive flags for stdio
            docker_command.insert(2, "-i")  # Interactive
            docker_command.insert(3, "--rm")  # Remove container after execution

            logger.info("Running stdio command for template %s", template_id)
            logger.debug("Docker command: %s", " ".join(docker_command))

            # Parse the original JSON input to extract the tool call
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

            # Create the proper MCP initialization sequence
            mcp_commands = [
                # 1. Initialize the connection
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
                # 2. Send initialized notification
                json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
                # 3. Send the actual tool call or request
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 3,
                        "method": tool_method,
                        "params": tool_params,
                    }
                ),
            ]

            # Join commands with newlines for proper MCP communication
            full_input = "\n".join(mcp_commands)

            logger.debug("Full MCP input: %s", full_input)

            # Execute the command with MCP input sequence using bash heredoc
            # This avoids creating temporary files
            bash_command = [
                "/bin/bash",
                "-c",
                f"""docker run -i --rm {' '.join(env_vars)} {' '.join(volumes)} {' '.join(['--label', f'template={template_id}'])} {image_name} {' '.join(command_args)} << 'EOF'
{full_input}
EOF""",
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
        """Clean up a failed deployment by removing the container."""
        try:
            self._run_command(["docker", "rm", "-f", container_name], check=False)
        except Exception:
            pass  # Ignore cleanup failures

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
                # Handle both Docker (newline-separated JSON objects) and Podman (JSON array) formats
                stdout = result.stdout.strip()
                containers = []

                if stdout.startswith("["):
                    # Podman format: JSON array
                    try:
                        containers = json.loads(stdout)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON array: {e}")
                        return []
                else:
                    # Docker format: newline-separated JSON objects
                    for line in stdout.split("\n"):
                        if line.strip():
                            try:
                                containers.append(json.loads(line))
                            except json.JSONDecodeError as e:
                                logger.debug(
                                    f"Failed to parse container JSON line: {line}, error: {e}"
                                )
                                continue

                # Process each container
                for container in containers:
                    try:
                        # Parse template from labels - handle both Docker and Podman formats
                        labels = container.get("Labels", "")
                        template_name = "unknown"

                        # Handle different label formats
                        if isinstance(labels, dict):
                            # Podman format: Labels is a dictionary
                            template_name = labels.get("template", "unknown")
                        elif isinstance(labels, str) and labels:
                            # Docker format: Labels is a comma-separated string
                            if "template=" in labels:
                                for label in labels.split(","):
                                    if label.strip().startswith("template="):
                                        template_name = label.split("=", 1)[1]
                                        break

                        # Handle port parsing safely - Podman has different port format
                        ports_str = container.get("Ports", "")
                        ports_display = ""

                        if isinstance(ports_str, list):
                            # Podman format: Ports is a list of port objects
                            if ports_str:
                                try:
                                    port_obj = ports_str[0]
                                    if isinstance(port_obj, dict):
                                        host_port = port_obj.get("host_port", "")
                                        ports_display = (
                                            str(host_port) if host_port else ""
                                        )
                                except (IndexError, KeyError):
                                    ports_display = ""
                        elif isinstance(ports_str, str) and ports_str:
                            # Docker format: Ports is a string
                            try:
                                port_parts = (
                                    ports_str.split(", ")[-1].split(":")[-1].split("/")
                                )
                                ports_display = port_parts[0] if port_parts else ""
                            except (IndexError, AttributeError):
                                ports_display = str(ports_str)

                        # Handle Names field - can be array or string
                        names = container.get("Names", "unknown")
                        if isinstance(names, list) and names:
                            name = names[0]
                        else:
                            name = str(names)

                        deployments.append(
                            {
                                "id": container.get("ID", "unknown"),
                                "name": name,
                                "template": template_name,
                                "status": container.get("State", "unknown"),
                                "since": container.get("RunningFor", "unknown"),
                                "image": container.get("Image", "unknown"),
                                "ports": ports_display,
                            }
                        )
                    except (KeyError, AttributeError) as e:
                        logger.debug(
                            f"Failed to parse container data: {container}, error: {e}"
                        )
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

    def _build_internal_image(
        self, template_id: str, image_name: str, template_data: Dict[str, Any]
    ) -> None:
        """Build Docker image for internal templates."""
        import os
        from pathlib import Path

        # Get template directory
        from mcp_template.template.utils.discovery import TemplateDiscovery

        discovery = TemplateDiscovery()
        template_dir = discovery.template_root / template_id

        if not template_dir.exists() or not (template_dir / "Dockerfile").exists():
            logger.error(
                f"Dockerfile not found for internal template {template_id} in {template_dir}"
            )
            raise ValueError(f"Internal template {template_id} missing Dockerfile")

        logger.info(f"Building image {image_name} for internal template {template_id}")

        # Build the Docker image
        build_command = ["docker", "build", "-t", image_name, str(template_dir)]
        self._run_command(build_command)
