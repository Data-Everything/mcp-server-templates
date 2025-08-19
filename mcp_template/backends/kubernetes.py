"""
Kubernetes deployment backend for managing deployments on Kubernetes clusters.
"""

import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from mcp_template.backends import BaseDeploymentBackend
from mcp_template.utils.image_utils import normalize_image_name

logger = logging.getLogger(__name__)


class KubernetesDeploymentService(BaseDeploymentBackend):
    """Kubernetes deployment service for managing MCP server deployments.

    This service manages Kubernetes deployments using the official Kubernetes
    Python client. It supports dynamic pod creation, scaling, and service discovery.
    """

    def __init__(
        self, namespace: str = "mcp-servers", kubeconfig_path: Optional[str] = None
    ):
        """Initialize Kubernetes service.

        Args:
            namespace: Kubernetes namespace for deployments
            kubeconfig_path: Path to kubeconfig file (optional)
        """

        super().__init__()
        self.namespace = namespace
        self.kubeconfig_path = kubeconfig_path
        self._ensure_kubernetes_available()
        self._ensure_namespace_exists()

    def _ensure_kubernetes_available(self):
        """Check if Kubernetes API is available and configure the client."""
        try:
            # Try to load configuration
            if self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                try:
                    # Try in-cluster config first (for running inside a pod)
                    config.load_incluster_config()
                except config.config_exception.ConfigException:
                    # Fall back to local kubeconfig
                    config.load_kube_config()

            # Initialize API clients
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v1 = client.AutoscalingV1Api()

            # Test connection
            version = self.core_v1.get_api_resources()
            logger.info("Connected to Kubernetes API")

        except Exception as e:
            logger.error(f"Failed to connect to Kubernetes API: {e}")
            raise RuntimeError(f"Kubernetes backend unavailable: {e}")

    def _ensure_namespace_exists(self, dry_run: bool = False):
        """Ensure the target namespace exists."""
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would check/create namespace {self.namespace}")
                return
            self.core_v1.read_namespace(name=self.namespace)
            logger.debug(f"Namespace {self.namespace} exists")
        except ApiException as e:
            if e.status == 404:
                # Create namespace
                namespace_body = client.V1Namespace(
                    metadata=client.V1ObjectMeta(
                        name=self.namespace,
                        labels={"app.kubernetes.io/managed-by": "mcp-templates"},
                    )
                )
                if dry_run:
                    logger.info(f"[DRY RUN] Would create namespace {self.namespace}")
                else:
                    self.core_v1.create_namespace(body=namespace_body)
                    logger.info(f"Created namespace {self.namespace}")
            else:
                raise

    def _generate_deployment_name(self, template_id: str) -> str:
        """Generate a unique deployment name."""
        # Use template_id as base name, add random suffix for uniqueness
        safe_name = template_id.lower().replace("_", "-").replace(" ", "-")
        # Kubernetes names must be DNS-1123 compliant
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "-")
        suffix = str(uuid.uuid4())[:8]
        return f"{safe_name}-{suffix}"

    def _create_helm_values(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        k8s_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create Helm values from template configuration and Kubernetes configuration."""
        # Extract image information
        image_repo = template_data.get("docker_image", template_id)
        image_repo = normalize_image_name(image_repo)
        if image_repo and len(image_repo.split(":")) > 1:
            image_repo = ":".join(image_repo.split(":")[:-1])
            image_tag = image_repo.split(":")[-1]
        else:
            image_tag = template_data.get("tag", "latest")

        # Determine MCP server type
        server_type = "http"  # Default to HTTP
        port = 8080
        command = []

        if "stdio" in template_data.get("transport", []):
            server_type = "stdio"
            command = template_data.get("command", [])
        elif "http" in template_data.get("transport", []):
            port = template_data.get("port", 8080)

        # Build Helm values with defaults and Kubernetes configuration overrides
        values = {
            "template_id": template_id,  # Add template ID for labeling
            "image": {
                "repository": image_repo,
                "tag": image_tag,
                "pullPolicy": (
                    "IfNotPresent"
                    if not template_data.get("pull_image", True)
                    else "Always"
                ),
            },
            "replicaCount": k8s_config.get("replicas", 1),
            "mcp": {
                "type": server_type,
                "port": port,
                "command": command,
                "env": config.get("env", {}),  # Template environment variables
                "config": config,  # Template configuration (will be passed as env vars)
            },
            "service": {
                "type": k8s_config.get("service_type", "ClusterIP"),
                "port": port,
            },
            "resources": k8s_config.get(
                "resources",
                {
                    "requests": {"cpu": "100m", "memory": "128Mi"},
                    "limits": {"cpu": "500m", "memory": "512Mi"},
                },
            ),
        }

        return values

    def _render_helm_template(
        self, deployment_name: str, values: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Render Helm chart templates with values."""
        # Get chart directory
        chart_dir = Path(__file__).parent.parent.parent / "charts" / "mcp-server"

        if not chart_dir.exists():
            raise RuntimeError(f"Helm chart not found at {chart_dir}")

        # Load templates
        templates_dir = chart_dir / "templates"
        manifests = []

        # Template context
        context = {
            "Values": values,
            "Chart": {"Name": "mcp-server", "Version": "0.1.0", "AppVersion": "1.0.0"},
            "Release": {
                "Name": deployment_name,
                "Namespace": self.namespace,
                "Service": "mcp-templates",
            },
        }

        # Simple template rendering (simplified for this implementation)
        # In a full implementation, you'd use a proper Helm template engine
        deployment_manifest = self._render_deployment(context)
        manifests.append(deployment_manifest)

        if values["mcp"]["type"] == "http":
            service_manifest = self._render_service(context)
            manifests.append(service_manifest)

        if values["mcp"]["config"]:
            configmap_manifest = self._render_configmap(context)
            manifests.append(configmap_manifest)

        return manifests

    def _render_deployment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Render Deployment manifest."""
        values = context["Values"]
        name = context["Release"]["Name"]
        namespace = context["Release"]["Namespace"]
        template_id = values.get("template_id", "unknown")

        # Create deployment specification
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                    "app.kubernetes.io/managed-by": "mcp-templates",
                    "mcp-template.io/template-name": template_id,
                },
            },
            "spec": {
                "replicas": values["replicaCount"],
                "selector": {
                    "matchLabels": {
                        "app.kubernetes.io/name": name,
                        "app.kubernetes.io/instance": name,
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app.kubernetes.io/name": name,
                            "app.kubernetes.io/instance": name,
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "mcp-server",
                                "image": f"{values['image']['repository']}:{values['image']['tag']}",
                                "imagePullPolicy": values["image"]["pullPolicy"],
                                "env": [
                                    {
                                        "name": "MCP_SERVER_TYPE",
                                        "value": values["mcp"]["type"],
                                    },
                                ]
                                + [
                                    {"name": k, "value": str(v)}
                                    for k, v in values["mcp"]["env"].items()
                                ],
                                "resources": values["resources"],
                            }
                        ]
                    },
                },
            },
        }

        # Add HTTP-specific configuration
        if values["mcp"]["type"] == "http":
            container = deployment["spec"]["template"]["spec"]["containers"][0]
            container["ports"] = [
                {
                    "name": "http",
                    "containerPort": values["mcp"]["port"],
                    "protocol": "TCP",
                }
            ]
            container["env"].append(
                {"name": "MCP_PORT", "value": str(values["mcp"]["port"])}
            )

        # Add stdio-specific configuration
        elif values["mcp"]["type"] == "stdio" and values["mcp"]["command"]:
            container = deployment["spec"]["template"]["spec"]["containers"][0]
            container["command"] = values["mcp"]["command"]

        return deployment

    def _render_service(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Render Service manifest."""
        values = context["Values"]
        name = context["Release"]["Name"]
        namespace = context["Release"]["Namespace"]

        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                    "app.kubernetes.io/managed-by": "mcp-templates",
                },
            },
            "spec": {
                "type": values["service"]["type"],
                "ports": [
                    {
                        "port": values["service"]["port"],
                        "targetPort": "http",
                        "protocol": "TCP",
                        "name": "http",
                    }
                ],
                "selector": {
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                },
            },
        }

    def _render_configmap(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Render ConfigMap manifest."""
        values = context["Values"]
        name = context["Release"]["Name"]
        namespace = context["Release"]["Namespace"]

        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": f"{name}-config",
                "namespace": namespace,
                "labels": {
                    "app.kubernetes.io/name": name,
                    "app.kubernetes.io/instance": name,
                    "app.kubernetes.io/managed-by": "mcp-templates",
                },
            },
            "data": {k: str(v) for k, v in values["mcp"]["config"].items()},
        }

    def deploy_template(
        self,
        template_id: str,
        config: Dict[str, Any],
        template_data: Dict[str, Any],
        backend_config: Dict[str, Any],
        pull_image: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Deploy a template to Kubernetes.

        Args:
            template_id: Unique identifier for the template
            config: Template configuration parameters (passed as env vars to container)
            template_data: Template metadata and configuration
            backend_config: Any banckend specific configuration
            pull_image: Whether to pull the container image before deployment
            dry_run: Whether to performm actual depolyment. False means yes, True means No

        Returns:
            Dict containing deployment information
        """
        try:
            deployment_name = self._generate_deployment_name(template_id)
            logger.info(f"Deploying template {template_id} as {deployment_name}")

            # Create Helm values using both template config and Kubernetes config
            values = self._create_helm_values(
                template_id, config, template_data, self._config
            )
            values["image"]["pullPolicy"] = "Always" if pull_image else "IfNotPresent"

            # Render manifests
            manifests = self._render_helm_template(deployment_name, values)
            # Apply manifests to cluster
            created_resources = []
            for manifest in manifests:
                try:
                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Would create {manifest['kind']} {manifest['metadata']['name']} in namespace {manifest['metadata']['namespace']}"
                        )
                        created_resources.append(
                            (manifest["kind"], manifest["metadata"]["name"])
                        )
                        continue
                    if manifest["kind"] == "Deployment":
                        # Convert manifest dict to proper Kubernetes object
                        deployment_obj = client.V1Deployment(
                            api_version=manifest["apiVersion"],
                            kind=manifest["kind"],
                            metadata=client.V1ObjectMeta(
                                name=manifest["metadata"]["name"],
                                namespace=manifest["metadata"]["namespace"],
                                labels=manifest["metadata"]["labels"],
                            ),
                            spec=client.V1DeploymentSpec(
                                replicas=manifest["spec"]["replicas"],
                                selector=client.V1LabelSelector(
                                    match_labels=manifest["spec"]["selector"][
                                        "matchLabels"
                                    ]
                                ),
                                template=client.V1PodTemplateSpec(
                                    metadata=client.V1ObjectMeta(
                                        labels=manifest["spec"]["template"]["metadata"][
                                            "labels"
                                        ]
                                    ),
                                    spec=client.V1PodSpec(
                                        containers=[
                                            client.V1Container(
                                                name=container["name"],
                                                image=container["image"],
                                                image_pull_policy=container[
                                                    "imagePullPolicy"
                                                ],
                                                env=[
                                                    client.V1EnvVar(
                                                        name=env["name"],
                                                        value=env["value"],
                                                    )
                                                    for env in container["env"]
                                                ],
                                                ports=[
                                                    client.V1ContainerPort(
                                                        name=port["name"],
                                                        container_port=port[
                                                            "containerPort"
                                                        ],
                                                        protocol=port["protocol"],
                                                    )
                                                    for port in container.get(
                                                        "ports", []
                                                    )
                                                ],
                                                resources=client.V1ResourceRequirements(
                                                    requests=container["resources"].get(
                                                        "requests"
                                                    ),
                                                    limits=container["resources"].get(
                                                        "limits"
                                                    ),
                                                ),
                                                command=container.get("command"),
                                            )
                                            for container in manifest["spec"][
                                                "template"
                                            ]["spec"]["containers"]
                                        ]
                                    ),
                                ),
                            ),
                        )
                        result = self.apps_v1.create_namespaced_deployment(
                            namespace=self.namespace, body=deployment_obj
                        )
                        created_resources.append(("Deployment", result.metadata.name))

                    elif manifest["kind"] == "Service":
                        service_obj = client.V1Service(
                            api_version=manifest["apiVersion"],
                            kind=manifest["kind"],
                            metadata=client.V1ObjectMeta(
                                name=manifest["metadata"]["name"],
                                namespace=manifest["metadata"]["namespace"],
                                labels=manifest["metadata"]["labels"],
                            ),
                            spec=client.V1ServiceSpec(
                                type=manifest["spec"]["type"],
                                ports=[
                                    client.V1ServicePort(
                                        name=port["name"],
                                        port=port["port"],
                                        target_port=port["targetPort"],
                                        protocol=port["protocol"],
                                    )
                                    for port in manifest["spec"]["ports"]
                                ],
                                selector=manifest["spec"]["selector"],
                            ),
                        )
                        result = self.core_v1.create_namespaced_service(
                            namespace=self.namespace, body=service_obj
                        )
                        created_resources.append(("Service", result.metadata.name))

                    elif manifest["kind"] == "ConfigMap":
                        configmap_obj = client.V1ConfigMap(
                            api_version=manifest["apiVersion"],
                            kind=manifest["kind"],
                            metadata=client.V1ObjectMeta(
                                name=manifest["metadata"]["name"],
                                namespace=manifest["metadata"]["namespace"],
                                labels=manifest["metadata"]["labels"],
                            ),
                            data=manifest["data"],
                        )
                        result = self.core_v1.create_namespaced_config_map(
                            namespace=self.namespace, body=configmap_obj
                        )
                        created_resources.append(("ConfigMap", result.metadata.name))

                except ApiException as e:
                    logger.error(f"Failed to create {manifest['kind']}: {e}")
                    # Cleanup any created resources
                    self._cleanup_resources(created_resources)
                    raise

            if not dry_run:
                # Wait for deployment to be ready
                self._wait_for_deployment_ready(deployment_name)

                # Get deployment info
                deployment_info = self._get_deployment_details(deployment_name)
            else:
                deployment_info = {"endpoint": None}

            return {
                "success": True,
                "template_id": template_id,
                "deployment_name": deployment_name,
                "deployment_id": deployment_name,
                "namespace": self.namespace,
                "status": "deployed" if not dry_run else "dry-run",
                "created_resources": created_resources,
                "endpoint": deployment_info.get("endpoint"),
                "replicas": values["replicaCount"],
                "image": f"{values['image']['repository']}:{values['image']['tag']}",
                "deployed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to deploy template {template_id}: {e}")
            return {
                "success": False,
                "template_id": template_id,
                "error": str(e),
                "deployed_at": datetime.now().isoformat(),
            }

    def _wait_for_deployment_ready(self, deployment_name: str, timeout: int = 300):
        """Wait for deployment to be ready."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                deployment = self.apps_v1.read_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace
                )

                if (
                    deployment.status.ready_replicas
                    and deployment.status.ready_replicas == deployment.spec.replicas
                ):
                    logger.info(f"Deployment {deployment_name} is ready")
                    return

            except ApiException:
                pass

            time.sleep(5)

        raise RuntimeError(
            f"Deployment {deployment_name} did not become ready within {timeout} seconds"
        )

    def _cleanup_resources(self, resources: List[tuple]):
        """Cleanup created resources on failure."""
        for resource_type, resource_name in resources:
            try:
                if resource_type == "Deployment":
                    self.apps_v1.delete_namespaced_deployment(
                        name=resource_name, namespace=self.namespace
                    )
                elif resource_type == "Service":
                    self.core_v1.delete_namespaced_service(
                        name=resource_name, namespace=self.namespace
                    )
                elif resource_type == "ConfigMap":
                    self.core_v1.delete_namespaced_config_map(
                        name=resource_name, namespace=self.namespace
                    )
                logger.info(f"Cleaned up {resource_type} {resource_name}")
            except ApiException as e:
                logger.warning(
                    f"Failed to cleanup {resource_type} {resource_name}: {e}"
                )

    def _get_deployment_details(self, deployment_name: str) -> Dict[str, Any]:
        """Get detailed deployment information."""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=self.namespace
            )

            # Extract template name from labels
            template_name = deployment.metadata.labels.get(
                "mcp-template.io/template-name", "unknown"
            )

            # Try to get service endpoint
            endpoint = None
            try:
                service = self.core_v1.read_namespaced_service(
                    name=deployment_name, namespace=self.namespace
                )
                if service.spec.type == "ClusterIP":
                    endpoint = f"http://{service.metadata.name}.{self.namespace}.svc.cluster.local:{service.spec.ports[0].port}"
                elif service.spec.type == "NodePort":
                    # Get node IP (simplified - in practice you'd get actual node IPs)
                    endpoint = f"http://localhost:{service.spec.ports[0].node_port}"
            except ApiException:
                pass

            # Determine transport type from endpoint
            transport = "http" if endpoint else "stdio"

            return {
                "id": deployment.metadata.name,
                "name": deployment.metadata.name,
                "template": template_name,
                "namespace": deployment.metadata.namespace,
                "replicas": deployment.spec.replicas,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "status": "running" if deployment.status.ready_replicas else "pending",
                "endpoint": endpoint,
                "transport": transport,
                "created": (
                    deployment.metadata.creation_timestamp.isoformat()
                    if deployment.metadata.creation_timestamp
                    else None
                ),
                "backend_type": "kubernetes",
            }
        except ApiException as e:
            return {"error": str(e)}

    def list_deployments(self) -> List[Dict[str, Any]]:
        """List Kubernetes deployments."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=self.namespace,
                label_selector="app.kubernetes.io/managed-by=mcp-templates",
            )

            result = []
            for deployment in deployments.items:
                details = self._get_deployment_details(deployment.metadata.name)
                result.append(details)

            return result
        except ApiException as e:
            logger.error(f"Failed to list deployments: {e}")
            return []

    def delete_deployment(self, deployment_name: str) -> bool:
        """Delete a Kubernetes deployment."""
        try:
            # Delete deployment
            try:
                self.apps_v1.delete_namespaced_deployment(
                    name=deployment_name, namespace=self.namespace
                )
                logger.info(f"Deleted deployment {deployment_name}")
            except ApiException as e:
                if e.status != 404:
                    logger.warning(
                        f"Failed to delete deployment {deployment_name}: {e}"
                    )

            # Delete service
            try:
                self.core_v1.delete_namespaced_service(
                    name=deployment_name, namespace=self.namespace
                )
                logger.info(f"Deleted service {deployment_name}")
            except ApiException as e:
                if e.status != 404:
                    logger.warning(f"Failed to delete service {deployment_name}: {e}")

            # Delete configmap
            try:
                self.core_v1.delete_namespaced_config_map(
                    name=f"{deployment_name}-config", namespace=self.namespace
                )
                logger.info(f"Deleted configmap {deployment_name}-config")
            except ApiException as e:
                if e.status != 404:
                    logger.warning(
                        f"Failed to delete configmap {deployment_name}-config: {e}"
                    )

            return True
        except Exception as e:
            logger.error(f"Failed to delete deployment {deployment_name}: {e}")
            return False

    def stop_deployment(self, deployment_name: str, force: bool = False) -> bool:
        """Stop a Kubernetes deployment (scale to 0)."""
        try:
            # Scale deployment to 0 replicas
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name, namespace=self.namespace
            )

            deployment.spec.replicas = 0
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name, namespace=self.namespace, body=deployment
            )

            logger.info(f"Scaled deployment {deployment_name} to 0 replicas")
            return True
        except ApiException as e:
            logger.error(f"Failed to stop deployment {deployment_name}: {e}")
            return False

    def get_deployment_info(
        self, deployment_name: str, include_logs: bool = False, lines: int = 10
    ) -> Dict[str, Any]:
        """Get detailed Kubernetes deployment information."""
        try:
            details = self._get_deployment_details(deployment_name)

            if include_logs:
                logs = self._get_deployment_logs(deployment_name, lines)
                details["logs"] = logs

            return details
        except Exception as e:
            return {"error": str(e)}

    def _get_deployment_logs(self, deployment_name: str, lines: int = 10) -> str:
        """Get logs from deployment pods."""
        try:
            pods = self.core_v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector=f"app.kubernetes.io/name={deployment_name}",
            )

            if not pods.items:
                return "No pods found"

            # Get logs from first pod
            pod = pods.items[0]
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod.metadata.name, namespace=self.namespace, tail_lines=lines
            )
            return logs
        except ApiException as e:
            return f"Failed to get logs: {e}"

    def connect_to_deployment(self, deployment_id: str):
        """Connect to deployment shell (not implemented for Kubernetes)."""
        raise NotImplementedError(
            "Shell connection not supported for Kubernetes deployments"
        )

    def cleanup_stopped_containers(
        self, template_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clean up stopped containers (scale 0 deployments)."""
        try:
            label_selector = "app.kubernetes.io/managed-by=mcp-templates"
            if template_name:
                label_selector += f",app.kubernetes.io/name={template_name}"

            deployments = self.apps_v1.list_namespaced_deployment(
                namespace=self.namespace, label_selector=label_selector
            )

            cleaned_up = []
            total = len(deployments.items)
            for deployment in deployments.items:
                if deployment.spec.replicas == 0:
                    if self.delete_deployment(deployment.metadata.name):
                        cleaned_up.append(deployment.metadata.name)

            return {
                "success": total == len(cleaned_up),
                "cleaned_up": cleaned_up,
                "count": len(cleaned_up),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def cleanup_dangling_images(self) -> Dict[str, Any]:
        """Clean up dangling images (not applicable for Kubernetes)."""
        return {"message": "Image cleanup not applicable for Kubernetes deployments"}
