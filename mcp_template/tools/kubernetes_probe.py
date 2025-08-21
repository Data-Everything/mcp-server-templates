"""
Kubernetes probe for discovering MCP server tools from Kubernetes pods.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from .base_probe import (
    DISCOVERY_RETRIES,
    DISCOVERY_RETRY_SLEEP,
    DISCOVERY_TIMEOUT,
    BaseProbe,
)

logger = logging.getLogger(__name__)

# Kubernetes-specific constants
POD_READY_TIMEOUT = 60
SERVICE_PORT_RANGE = (8000, 9000)


class KubernetesProbe(BaseProbe):
    """Probe Kubernetes pods to discover MCP server tools."""

    def __init__(self, namespace: str = "mcp-servers"):
        """Initialize Kubernetes probe.

        Args:
            namespace: Kubernetes namespace to use for probe operations
        """
        super().__init__()
        self.namespace = namespace
        self._init_kubernetes_client()

    def _init_kubernetes_client(self):
        """Initialize Kubernetes client configuration."""
        try:
            # Try to load in-cluster config first
            config.load_incluster_config()
            logger.debug("Loaded in-cluster Kubernetes config")
        except config.ConfigException:
            try:
                # Fall back to kubeconfig
                config.load_kube_config()
                logger.debug("Loaded kubeconfig")
            except config.ConfigException as e:
                logger.error("Failed to load Kubernetes config: %s", e)
                raise

        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()

    def discover_tools_from_image(
        self,
        image_name: str,
        server_args: Optional[List[str]] = None,
        env_vars: Optional[Dict[str, str]] = None,
        timeout: int = DISCOVERY_TIMEOUT,
    ) -> Optional[Dict[str, Any]]:
        """
        Discover tools from MCP server Kubernetes image.

        Args:
            image_name: Container image name to probe
            server_args: Arguments to pass to the MCP server
            env_vars: Environment variables to pass to the pod
            timeout: Timeout for discovery process

        Returns:
            Dictionary containing discovered tools and metadata, or None if failed
        """
        logger.info("Discovering tools from MCP Kubernetes image: %s", image_name)

        try:
            # Try MCP stdio first
            result = self._try_mcp_stdio_discovery(image_name, server_args, env_vars)
            if result:
                return result

            # Fallback to HTTP probe (for non-standard MCP servers)
            return self._try_http_discovery(image_name, timeout, env_vars)

        except (ApiException, Exception) as e:
            if isinstance(e, ApiException):
                logger.warning(
                    "Tool discovery timed out for image %s after %d seconds",
                    image_name,
                    timeout,
                )
            else:
                logger.error(
                    "Failed to discover tools from image %s: %s", image_name, e
                )
            return None

    @retry(
        stop=stop_after_attempt(DISCOVERY_RETRIES),
        wait=wait_fixed(DISCOVERY_RETRY_SLEEP),
        retry=retry_if_exception_type((ApiException, OSError, Exception)),
        reraise=True,
    )
    def _try_mcp_stdio_discovery(
        self,
        image_name: str,
        server_args: Optional[List[str]],
        env_vars: Optional[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using MCP stdio protocol via Kubernetes Job."""
        try:
            args = server_args or []

            # Create a temporary Job to run MCP stdio discovery
            job_name = self._generate_job_name(image_name)

            # Create job manifest
            job_manifest = self._create_discovery_job_manifest(
                job_name, image_name, args, env_vars
            )

            # Create and run the job
            job = self.k8s_apps_v1.create_namespaced_job(
                namespace=self.namespace, body=job_manifest
            )

            try:
                # Wait for job completion
                result = self._wait_for_job_completion(job_name, timeout=60)

                if result and "tools" in result:
                    logger.info(
                        "Successfully discovered tools via MCP stdio from %s",
                        image_name,
                    )
                    result["discovery_method"] = "kubernetes_mcp_stdio"
                    return result

            finally:
                # Cleanup job
                self._cleanup_job(job_name)

            return None

        except (ApiException, Exception) as e:
            logger.debug("MCP stdio discovery failed for %s: %s", image_name, e)
            return None

    @retry(
        stop=stop_after_attempt(DISCOVERY_RETRIES),
        wait=wait_fixed(DISCOVERY_RETRY_SLEEP),
        retry=retry_if_exception_type((ApiException, OSError, Exception)),
        reraise=True,
    )
    def _try_http_discovery(
        self, image_name: str, timeout: int, env_vars: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using HTTP endpoints (fallback)."""
        pod_name = None
        service_name = None

        try:
            # Generate unique names
            pod_name = self._generate_pod_name(image_name)
            service_name = self._generate_service_name(image_name)

            # Find available port
            port = self._find_available_port()
            if not port:
                logger.error("No available ports found for service")
                return None

            # Create pod
            if not self._create_http_pod(pod_name, image_name, port, env_vars):
                return None

            # Create service
            if not self._create_service(service_name, pod_name, port):
                return None

            # Wait for pod to be ready
            if not self._wait_for_pod_ready(pod_name, timeout):
                return None

            # Discover tools from running pod via service
            service_url = self._get_service_url(service_name, port)
            result = self._probe_endpoints(service_url, self._get_default_endpoints())

            if result:
                result.update(
                    {
                        "discovery_method": "kubernetes_http_probe",
                        "timestamp": time.time(),
                        "source_image": image_name,
                        "pod_name": pod_name,
                        "service_name": service_name,
                        "port": port,
                    }
                )

            return result

        except (ApiException, Exception) as e:
            logger.debug("HTTP discovery failed for %s: %s", image_name, e)
            return None

        finally:
            # Always cleanup resources
            if pod_name:
                self._cleanup_pod(pod_name)
            if service_name:
                self._cleanup_service(service_name)

    def _generate_job_name(self, image_name: str) -> str:
        """Generate unique job name."""
        clean_name = image_name.replace("/", "-").replace(":", "-")
        timestamp = int(time.time())
        return f"mcp-tool-discovery-job-{clean_name}-{timestamp}"[:63]  # K8s name limit

    def _generate_pod_name(self, image_name: str) -> str:
        """Generate unique pod name."""
        clean_name = image_name.replace("/", "-").replace(":", "-")
        timestamp = int(time.time())
        return f"mcp-tool-discovery-{clean_name}-{timestamp}"[:63]  # K8s name limit

    def _generate_service_name(self, image_name: str) -> str:
        """Generate unique service name."""
        clean_name = image_name.replace("/", "-").replace(":", "-")
        timestamp = int(time.time())
        return f"mcp-discovery-svc-{clean_name}-{timestamp}"[:63]  # K8s name limit

    def _find_available_port(self) -> Optional[int]:
        """Find an available port for the service."""
        # For Kubernetes, we can use any port since it's internal
        # Just return a port from our range
        return SERVICE_PORT_RANGE[0]

    def _create_discovery_job_manifest(
        self,
        job_name: str,
        image_name: str,
        args: List[str],
        env_vars: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Create a Kubernetes Job manifest for MCP stdio discovery."""
        env_list = []
        if env_vars:
            env_list = [{"name": k, "value": v} for k, v in env_vars.items()]

        return {
            "apiVersion": "batch/v1",
            "kind": "Job",
            "metadata": {
                "name": job_name,
                "namespace": self.namespace,
                "labels": {"app": "mcp-tool-discovery", "type": "stdio-probe"},
            },
            "spec": {
                "ttlSecondsAfterFinished": 300,  # Cleanup after 5 minutes
                "backoffLimit": 1,
                "template": {
                    "spec": {
                        "restartPolicy": "Never",
                        "containers": [
                            {
                                "name": "mcp-stdio-probe",
                                "image": image_name,
                                "args": args,
                                "env": env_list,
                                "resources": {
                                    "requests": {"memory": "64Mi", "cpu": "100m"},
                                    "limits": {"memory": "256Mi", "cpu": "500m"},
                                },
                            }
                        ],
                    }
                },
            },
        }

    def _create_http_pod(
        self,
        pod_name: str,
        image_name: str,
        port: int,
        env_vars: Optional[Dict[str, str]],
    ) -> bool:
        """Create pod with HTTP server (fallback method)."""
        try:
            env_list = []
            if env_vars:
                env_list = [{"name": k, "value": v} for k, v in env_vars.items()]

            pod_manifest = {
                "apiVersion": "v1",
                "kind": "Pod",
                "metadata": {
                    "name": pod_name,
                    "namespace": self.namespace,
                    "labels": {"app": "mcp-tool-discovery", "type": "http-probe"},
                },
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "mcp-http-probe",
                            "image": image_name,
                            "ports": [{"containerPort": port}],
                            "env": env_list,
                            "resources": {
                                "requests": {"memory": "64Mi", "cpu": "100m"},
                                "limits": {"memory": "256Mi", "cpu": "500m"},
                            },
                        }
                    ],
                },
            }

            self.k8s_core_v1.create_namespaced_pod(
                namespace=self.namespace, body=pod_manifest
            )

            logger.debug("Pod %s created successfully", pod_name)
            return True

        except ApiException as e:
            logger.error("Failed to create pod %s: %s", pod_name, e)
            return False

    def _create_service(self, service_name: str, pod_name: str, port: int) -> bool:
        """Create service to expose the pod."""
        try:
            service_manifest = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": service_name,
                    "namespace": self.namespace,
                    "labels": {"app": "mcp-tool-discovery"},
                },
                "spec": {
                    "selector": {"app": "mcp-tool-discovery", "type": "http-probe"},
                    "ports": [{"protocol": "TCP", "port": port, "targetPort": port}],
                    "type": "ClusterIP",
                },
            }

            self.k8s_core_v1.create_namespaced_service(
                namespace=self.namespace, body=service_manifest
            )

            logger.debug("Service %s created successfully", service_name)
            return True

        except ApiException as e:
            logger.error("Failed to create service %s: %s", service_name, e)
            return False

    def _wait_for_job_completion(
        self, job_name: str, timeout: int
    ) -> Optional[Dict[str, Any]]:
        """Wait for job to complete and extract results."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                job = self.k8s_apps_v1.read_namespaced_job_status(
                    name=job_name, namespace=self.namespace
                )

                if job.status.succeeded:
                    # Job completed successfully, get logs
                    return self._extract_mcp_tools_from_job_logs(job_name)
                elif job.status.failed:
                    logger.debug("Job %s failed", job_name)
                    return None

                time.sleep(1)

            except ApiException as e:
                logger.debug("Error checking job status: %s", e)
                return None

        logger.warning("Job %s did not complete within %d seconds", job_name, timeout)
        return None

    def _wait_for_pod_ready(self, pod_name: str, timeout: int) -> bool:
        """Wait for pod to be ready to accept requests."""
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                pod = self.k8s_core_v1.read_namespaced_pod_status(
                    name=pod_name, namespace=self.namespace
                )

                if pod.status.phase == "Running":
                    # Check if all containers are ready
                    if pod.status.container_statuses:
                        all_ready = all(
                            container.ready
                            for container in pod.status.container_statuses
                        )
                        if all_ready:
                            logger.debug("Pod %s is ready", pod_name)
                            return True

                elif pod.status.phase in ["Failed", "Succeeded"]:
                    logger.debug(
                        "Pod %s finished with phase %s", pod_name, pod.status.phase
                    )
                    return False

                time.sleep(1)

            except ApiException as e:
                logger.debug("Error checking pod status: %s", e)
                return False

        logger.warning(
            "Pod %s did not become ready within %d seconds",
            pod_name,
            timeout,
        )
        return False

    def _extract_mcp_tools_from_job_logs(
        self, job_name: str
    ) -> Optional[Dict[str, Any]]:
        """Extract MCP tools information from job logs."""
        try:
            # Get pods for this job
            pods = self.k8s_core_v1.list_namespaced_pod(
                namespace=self.namespace, label_selector=f"job-name={job_name}"
            )

            if not pods.items:
                logger.debug("No pods found for job %s", job_name)
                return None

            # Get logs from the first pod
            pod_name = pods.items[0].metadata.name
            logs = self.k8s_core_v1.read_namespaced_pod_log(
                name=pod_name, namespace=self.namespace
            )

            # Try to parse MCP tools from logs
            # This is a simplified implementation - in practice you'd need
            # to implement proper MCP protocol parsing
            return self._parse_mcp_tools_from_logs(logs)

        except ApiException as e:
            logger.debug("Failed to get job logs: %s", e)
            return None

    def _parse_mcp_tools_from_logs(self, logs: str) -> Optional[Dict[str, Any]]:
        """Parse MCP tools from container logs."""
        # This is a placeholder implementation
        # In practice, you'd implement proper MCP protocol parsing
        try:
            # Look for JSON output in logs
            for line in logs.split("\n"):
                if line.strip().startswith("{") and "tools" in line:
                    return json.loads(line.strip())
        except (json.JSONDecodeError, Exception) as e:
            logger.debug("Failed to parse tools from logs: %s", e)

        return None

    def _get_service_url(self, service_name: str, port: int) -> str:
        """Get the URL for accessing the service."""
        return f"http://{service_name}.{self.namespace}.svc.cluster.local:{port}"

    def _probe_endpoints(
        self, base_url: str, endpoints: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Probe service endpoints for tool information."""
        for endpoint in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    data = response.json()
                    if "tools" in data:
                        return data

            except (requests.RequestException, json.JSONDecodeError, Exception) as e:
                logger.debug("Failed to probe endpoint %s: %s", endpoint, e)
                continue

        return None

    def _cleanup_job(self, job_name: str):
        """Clean up the discovery job."""
        try:
            self.k8s_apps_v1.delete_namespaced_job(
                name=job_name, namespace=self.namespace, propagation_policy="Background"
            )
            logger.debug("Cleaned up job %s", job_name)
        except ApiException as e:
            logger.debug("Failed to cleanup job %s: %s", job_name, e)

    def _cleanup_pod(self, pod_name: str):
        """Clean up the discovery pod."""
        try:
            self.k8s_core_v1.delete_namespaced_pod(
                name=pod_name, namespace=self.namespace
            )
            logger.debug("Cleaned up pod %s", pod_name)
        except ApiException as e:
            logger.debug("Failed to cleanup pod %s: %s", pod_name, e)

    def _cleanup_service(self, service_name: str):
        """Clean up the discovery service."""
        try:
            self.k8s_core_v1.delete_namespaced_service(
                name=service_name, namespace=self.namespace
            )
            logger.debug("Cleaned up service %s", service_name)
        except ApiException as e:
            logger.debug("Failed to cleanup service %s: %s", service_name, e)
