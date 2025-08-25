"""
Multi-Backend Manager - Centralized operations across multiple deployment backends.

This module provides a unified interface for operations that span multiple backends,
enabling CLI commands to show aggregate views and auto-detect backend contexts.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from mcp_template.backends import VALID_BACKENDS, BaseDeploymentBackend, get_backend
from mcp_template.core.deployment_manager import DeploymentManager
from mcp_template.core.template_manager import TemplateManager
from mcp_template.core.tool_manager import ToolManager

logger = logging.getLogger(__name__)


class MultiBackendManager:
    """
    Manages operations across multiple deployment backends.

    This class provides a unified interface for operations that need to work
    across multiple backends (Docker, Kubernetes, Mock) simultaneously,
    such as listing all deployments or discovering tools from all active servers.
    """

    def __init__(self, enabled_backends: List[str] = None):
        """
        Initialize multi-backend manager.

        Args:
            enabled_backends: List of backend types to enable.
                            Defaults to ["docker", "kubernetes"] (production backends only)
        """

        self.enabled_backends = enabled_backends or VALID_BACKENDS

        if isinstance(self.enabled_backends, str):
            self.enabled_backends = [self.enabled_backends]

        self.backends: Dict[str, BaseDeploymentBackend] = {}
        self.deployment_managers: Dict[str, Any] = {}
        self.tool_managers: Dict[str, Any] = {}

        # Initialize available backends
        for backend_type in self.enabled_backends:
            try:
                backend = get_backend(backend_type)
                self.backends[backend_type] = backend
                self.deployment_managers[backend_type] = DeploymentManager(backend_type)
                self.tool_managers[backend_type] = ToolManager(backend_type)
                logger.debug(f"Initialized {backend_type} backend successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize {backend_type} backend: {e}")
                # Continue with other backends

    def get_available_backends(self) -> List[str]:
        """Get list of successfully initialized backends."""
        return list(self.backends.keys())

    def get_all_deployments(
        self, template_name: Optional[str] = None, status: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get deployments from all backends with backend information.

        Args:
            template_name: Optional filter by template name

        Returns:
            List of deployment dictionaries with backend_type field added
        """
        all_deployments = []

        for backend_type, deployment_manager in self.deployment_managers.items():
            try:
                deployments = deployment_manager.find_deployments_by_criteria(
                    template_name=template_name,
                    status=status,
                )

                # Add backend information to each deployment
                for deployment in deployments:
                    deployment_with_backend = deployment.copy()
                    deployment_with_backend["backend_type"] = backend_type
                    all_deployments.append(deployment_with_backend)

            except Exception as e:
                logger.warning(f"Failed to get deployments from {backend_type}: {e}")
                continue

        return all_deployments

    def detect_backend_for_deployment(self, deployment_id: str) -> Optional[str]:
        """
        Auto-detect which backend owns a deployment ID.

        Args:
            deployment_id: The deployment ID to search for

        Returns:
            Backend type that owns the deployment, or None if not found
        """
        for backend_type, deployment_manager in self.deployment_managers.items():
            try:
                deployments = deployment_manager.find_deployments_by_criteria(
                    deployment_id=deployment_id
                )
                if deployments:
                    return backend_type
            except Exception as e:
                logger.debug(
                    f"Error searching {backend_type} for deployment {deployment_id}: {e}"
                )
                continue

        return None

    def get_deployment_by_id(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """
        Find a deployment by ID across all backends.

        Args:
            deployment_id: The deployment ID to find

        Returns:
            Deployment information with backend_type, or None if not found
        """
        backend_type = self.detect_backend_for_deployment(deployment_id)
        if not backend_type:
            return None

        try:
            deployment_manager = self.deployment_managers[backend_type]
            deployments = deployment_manager.find_deployments_by_criteria(
                deployment_id=deployment_id
            )
            if deployments:
                deployment = deployments[0].copy()
                deployment["backend_type"] = backend_type
                return deployment
        except Exception as e:
            logger.error(
                f"Failed to get deployment {deployment_id} from {backend_type}: {e}"
            )

        return None

    def execute_on_backend(
        self, backend_type: str, manager_type: str, method_name: str, *args, **kwargs
    ) -> Any:
        """
        Execute a method on a specific backend manager.

        Args:
            backend_type: Backend to execute on
            manager_type: Type of manager ('deployment', 'tool')
            method_name: Method name to call
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Result of the method call

        Raises:
            ValueError: If backend or manager type is invalid
            AttributeError: If method doesn't exist
        """
        if backend_type not in self.backends:
            raise ValueError(f"Backend {backend_type} not available")

        if manager_type == "deployment":
            manager = self.deployment_managers[backend_type]
        elif manager_type == "tool":
            manager = self.tool_managers[backend_type]
        else:
            raise ValueError(f"Invalid manager type: {manager_type}")

        if not hasattr(manager, method_name):
            raise AttributeError(f"Manager {manager_type} has no method {method_name}")

        method = getattr(manager, method_name)
        return method(*args, **kwargs)

    def get_all_tools(
        self,
        template_name: Optional[str] = None,
        discovery_method: str = "auto",
        force_refresh: bool = False,
        include_static: bool = True,
        include_dynamic: bool = True,
    ) -> Dict[str, Any]:
        """
        Get tools from all backends and templates.

        Args:
            template_name: Optional filter by template name
            discovery_method: Tool discovery method
            force_refresh: Force refresh of tool cache
            include_static: Include static tools from template definitions
            include_dynamic: Include dynamic tools from running deployments

        Returns:
            Dictionary with tools organized by source
        """
        all_tools = {
            "static_tools": {},  # Tools from template definitions
            "dynamic_tools": {},  # Tools from running deployments
            "backend_summary": {},  # Summary by backend
        }

        # Use first available backend for template info (backend agnostic)
        first_backend = next(iter(self.tool_managers.keys()))
        template_manager = TemplateManager(first_backend)
        # Get dynamic tools from running deployments if requested
        if include_dynamic:
            deployments_found = False

            for backend_type, tool_manager in self.tool_managers.items():
                try:
                    # Get deployments for this backend
                    deployments = self.deployment_managers[
                        backend_type
                    ].find_deployments_by_criteria(
                        template_name=template_name, status="running"
                    )

                    backend_tools = []
                    for deployment in deployments:
                        try:
                            template_id = deployment.get("template", "unknown")
                            result = tool_manager.list_tools(
                                template_id,
                                discovery_method=discovery_method,
                                force_refresh=force_refresh,
                            )
                            tools = result.get("tools", [])
                            if tools:
                                backend_tools.extend(
                                    [
                                        {
                                            **tool,
                                            "deployment_id": deployment.get("id"),
                                            "template": template_id,
                                            "backend": backend_type,
                                        }
                                        for tool in tools
                                    ]
                                )
                        except Exception as e:
                            logger.debug(
                                f"Failed to get tools from deployment {deployment.get('id')}: {e}"
                            )

                    if backend_tools:
                        deployments_found = True
                        all_tools["dynamic_tools"][backend_type] = backend_tools
                        all_tools["backend_summary"][backend_type] = {
                            "tool_count": len(backend_tools),
                            "deployment_count": len(deployments),
                        }

                except Exception as e:
                    logger.warning(f"Failed to get tools from {backend_type}: {e}")

            # If no running deployments found and a specific template is requested,
            # try dynamic discovery by creating a temporary container
            if not deployments_found and template_name and not include_static:
                logger.info(
                    f"No running deployments found for {template_name}, attempting dynamic discovery"
                )
                try:
                    # Check if template exists and supports dynamic discovery
                    template_info = template_manager.get_template_info(template_name)
                    if template_info:
                        # Try dynamic discovery on available backends in order
                        for backend_type, tool_manager in self.tool_managers.items():
                            try:
                                result = tool_manager.list_tools(
                                    template_name,
                                    discovery_method="auto",  # Let it choose stdio/http
                                    force_refresh=force_refresh,
                                )
                                tools = result.get("tools", [])
                                if tools:
                                    all_tools["dynamic_tools"][backend_type] = [
                                        {
                                            **tool,
                                            "deployment_id": "temporary_discovery",
                                            "template": template_name,
                                            "backend": backend_type,
                                        }
                                        for tool in tools
                                    ]
                                    all_tools["backend_summary"][backend_type] = {
                                        "tool_count": len(tools),
                                        "deployment_count": 0,  # No permanent deployment
                                    }
                                    logger.info(
                                        f"Dynamic discovery found {len(tools)} tools for {template_name} on {backend_type}"
                                    )
                                    break  # Stop after first successful discovery
                            except Exception as e:
                                logger.debug(
                                    f"Dynamic discovery failed on {backend_type}: {e}"
                                )
                                continue

                except Exception as e:
                    logger.warning(f"Dynamic discovery failed for {template_name}: {e}")

        # Get static tools from templates (backend-agnostic) if requested
        if include_static:
            try:
                templates = template_manager.list_templates()

                if template_name:
                    templates = {
                        k: v for k, v in templates.items() if k == template_name
                    }

                for template_id, template_info in templates.items():
                    # Use first available backend for static discovery
                    tool_manager = ToolManager(first_backend)
                    try:
                        result = tool_manager.list_tools(
                            template_id,
                            discovery_method="static",
                            force_refresh=force_refresh,
                        )
                        tools = result.get("tools", [])
                        if tools:
                            all_tools["static_tools"][template_id] = {
                                "tools": tools,
                                "source": "template_definition",
                            }
                    except Exception as e:
                        logger.debug(
                            f"Failed to get static tools for {template_id}: {e}"
                        )

            except Exception as e:
                logger.warning(f"Failed to get template tools: {e}")

        return all_tools

    def call_tool(
        self,
        template_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        config_values: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        pull_image: bool = True,
        force_stdio: bool = False,
    ) -> Dict[str, Any]:
        """
        Call a tool using multi-backend discovery and priority.

        Discovery Priority:
        1. If backend_type specified, use that backend only
        2. Find existing deployment for template and use that backend
        3. Check if stdio is supported and use first available backend
        4. Show deployment message if template is not deployed

        Args:
            template_name: Template name or deployment name
            tool_name: Name of the tool to call
            arguments: Tool arguments
            backend_type: Specific backend to use (optional)
            config_values: Configuration values for stdio calls
            timeout: Timeout for the call
            pull_image: Whether to pull image for stdio calls
            force_stdio: Force stdio transport

        Returns:
            Tool call result with backend information
        """

        # Check if template_name is actually a deployment ID
        deployment = self.get_deployment_by_id(template_name)
        if deployment:
            deployment_backend = deployment.get("backend_type")
            deployment_template = deployment.get("template", template_name)
            if deployment_backend in self.tool_managers:
                try:
                    tool_manager = self.tool_managers[deployment_backend]
                    result = tool_manager.call_tool(
                        deployment_template,
                        tool_name,
                        arguments,
                        config_values=config_values,
                        timeout=timeout,
                        pull_image=pull_image,
                        force_stdio=force_stdio,
                    )
                    if isinstance(result, dict):
                        result["backend_type"] = deployment_backend
                        result["deployment_id"] = template_name
                    return result
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "backend_type": deployment_backend,
                        "deployment_id": template_name,
                    }

        # Priority 1: Find existing deployment for template
        all_deployments = self.get_all_deployments(template_name=template_name)
        running_deployments = [
            d for d in all_deployments if d.get("status") == "running"
        ]

        if running_deployments:
            # Use the first running deployment
            deployment = running_deployments[0]
            deployment_backend = deployment.get("backend_type")
            deployment_id = deployment.get("id")

            if deployment_backend in self.tool_managers:
                try:
                    tool_manager = self.tool_managers[deployment_backend]
                    result = tool_manager.call_tool(
                        template_name,
                        tool_name,
                        arguments,
                        config_values=config_values,
                        timeout=timeout,
                        pull_image=pull_image,
                        force_stdio=force_stdio,
                    )
                    if isinstance(result, dict):
                        result["backend_type"] = deployment_backend
                        result["deployment_id"] = deployment_id
                        result["used_existing_deployment"] = True
                    return result
                except Exception as e:
                    logger.warning(
                        f"Failed to call tool on existing deployment {deployment_id}: {e}"
                    )
                    # Fall through to stdio attempt

        # Priority 2: Check if stdio is supported and try backends in order
        first_backend = next(iter(self.tool_managers.keys()))
        template_manager = TemplateManager(first_backend)

        try:
            template_info = template_manager.get_template_info(template_name)
            if template_info:
                transport_config = template_info.get("transport", {})
                supported_transports = transport_config.get("supported", ["http"])
                default_transport = transport_config.get("default", "http")

                if "stdio" in supported_transports or default_transport == "stdio":
                    # Try each backend in order
                    last_error = None
                    for backend, tool_manager in self.tool_managers.items():
                        try:
                            result = tool_manager.call_tool(
                                template_name,
                                tool_name,
                                arguments,
                                config_values=config_values,
                                timeout=timeout,
                                pull_image=pull_image,
                                force_stdio=True,
                            )
                            if isinstance(result, dict):
                                if result.get("success"):
                                    result["backend_type"] = backend
                                    result["used_stdio"] = True
                                    return result
                                else:
                                    last_error = result.get("error", "Unknown error")
                        except Exception as e:
                            last_error = str(e)
                            logger.debug(f"Failed stdio call on {backend}: {e}")
                            continue

                    # All stdio attempts failed
                    return {
                        "success": False,
                        "error": f"All stdio backends failed. Last error: {last_error}",
                        "template_supports_stdio": True,
                    }
                else:
                    # Template doesn't support stdio
                    return {
                        "success": False,
                        "error": f"Template '{template_name}' does not support stdio transport and no running deployment found",
                        "template_supports_stdio": False,
                        "supported_transports": supported_transports,
                        "deploy_command": f"mcpt deploy {template_name}",
                    }
            else:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get template info: {e}",
            }

    def stop_deployment(self, deployment_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Stop a deployment by auto-detecting its backend.

        Args:
            deployment_id: ID of deployment to stop
            timeout: Timeout for stop operation

        Returns:
            Result of stop operation
        """
        backend_type = self.detect_backend_for_deployment(deployment_id)
        if not backend_type:
            return {
                "success": False,
                "error": f"Deployment {deployment_id} not found in any backend",
            }

        try:
            deployment_manager = self.deployment_managers[backend_type]
            result = deployment_manager.stop_deployment(deployment_id, timeout)
            result["backend_type"] = backend_type
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop deployment {deployment_id}: {e}",
                "backend_type": backend_type,
            }

    def get_deployment_logs(
        self, deployment_id: str, lines: int = 100, follow: bool = False
    ) -> Dict[str, Any]:
        """
        Get logs from a deployment by auto-detecting its backend.

        Args:
            deployment_id: ID of deployment
            lines: Number of log lines to retrieve
            follow: Whether to follow logs

        Returns:
            Log result with backend information
        """
        backend_type = self.detect_backend_for_deployment(deployment_id)
        if not backend_type:
            return {
                "success": False,
                "error": f"Deployment {deployment_id} not found in any backend",
            }

        try:
            deployment_manager = self.deployment_managers[backend_type]
            result = deployment_manager.get_deployment_logs(
                deployment_id, lines=lines, follow=follow
            )
            result["backend_type"] = backend_type
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get logs for deployment {deployment_id}: {e}",
                "backend_type": backend_type,
            }

    def cleanup_all_backends(self, force: bool = False) -> Dict[str, Any]:
        """
        Run cleanup operations on all backends.

        Args:
            force: Whether to force cleanup

        Returns:
            Summary of cleanup operations by backend
        """
        results = {}

        for backend_type, deployment_manager in self.deployment_managers.items():
            try:
                result = deployment_manager.cleanup_deployments(force=force)
                results[backend_type] = result
            except Exception as e:
                results[backend_type] = {"success": False, "error": str(e)}

        # Summary
        total_success = sum(1 for r in results.values() if r.get("success", False))
        results["summary"] = {
            "total_backends": len(self.deployment_managers),
            "successful_cleanups": total_success,
            "failed_cleanups": len(self.deployment_managers) - total_success,
        }

        return results

    def get_backend_health(self) -> Dict[str, Any]:
        """
        Check health status of all backends.

        Returns:
            Health status information for each backend
        """
        health = {}

        for backend_type, backend in self.backends.items():
            try:
                # Try a simple operation to test backend health
                deployment_manager = self.deployment_managers[backend_type]
                deployments = deployment_manager.find_deployments_by_criteria()
                health[backend_type] = {
                    "status": "healthy",
                    "deployment_count": len(deployments),
                    "error": None,
                }
            except Exception as e:
                health[backend_type] = {
                    "status": "unhealthy",
                    "deployment_count": 0,
                    "error": str(e),
                }

        return health
