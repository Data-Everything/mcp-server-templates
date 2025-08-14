# Kubernetes Backend Guide

The MCP Template Platform now supports Kubernetes as a deployment backend, enabling production-scale deployments with automatic scaling, load balancing, and service discovery.

## Quick Start

### Prerequisites

1. **Kubernetes Cluster**: Access to a Kubernetes cluster (local or remote)
2. **kubectl**: Configured and connected to your cluster
3. **Python Dependencies**: `kubernetes` package (automatically installed)

### Basic Usage

```bash
# Deploy to Kubernetes using default namespace (mcp-servers)
mcpt --backend kubernetes deploy github-server

# Deploy to custom namespace
mcpt --backend kubernetes --namespace production deploy github-server

# Use specific kubeconfig
mcpt --backend kubernetes --kubeconfig ~/.kube/prod-config deploy github-server
```

## Architecture

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   Gateway/LB    │    │  Kubernetes     │
│                 │────│                 │────│  Cluster        │
│  (CLI/API)      │    │  (Service)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                               │
                       ┌─────────────────────────┼─────────────────┐
                       │                         │                 │
                   ┌───▼───┐               ┌───▼───┐         ┌───▼───┐
                   │ Pod 1 │               │ Pod 2 │   ...   │ Pod N │
                   │       │               │       │         │       │
                   │MCP Srv│               │MCP Srv│         │MCP Srv│
                   └───────┘               └───────┘         └───────┘
```

### Kubernetes Resources

For each MCP server deployment, the following Kubernetes resources are created:

1. **Deployment**: Manages pod lifecycle and scaling
2. **Service**: Provides load balancing and service discovery
3. **ConfigMap**: Stores configuration data (optional)
4. **ServiceAccount**: For pod security (optional)

## Configuration

### Backend Selection

```bash
# Global backend selection
export MCP_BACKEND=kubernetes
export MCP_NAMESPACE=production

# Or per-command
mcpt --backend kubernetes --namespace production deploy template
```

### Registry Configuration

Update your MCP server registry to include Kubernetes-specific metadata:

```json
{
  "github-server": {
    "type": "k8s",
    "chart": "mcp-server",
    "namespace": "mcp-servers",
    "replicas": 2,
    "resources": {
      "requests": {
        "cpu": "100m",
        "memory": "128Mi"
      },
      "limits": {
        "cpu": "500m",
        "memory": "512Mi"
      }
    },
    "service": {
      "type": "ClusterIP",
      "port": 8080
    },
    "env": {
      "LOG_LEVEL": "INFO",
      "MAX_CONNECTIONS": "100"
    },
    "config": {
      "database_url": "postgresql://localhost:5432/mydb"
    }
  }
}
```

### Helm Values Customization

The platform uses a generic Helm chart that can be customized per deployment:

```yaml
# values.yaml equivalent (generated automatically)
image:
  repository: "github-server"
  tag: "latest"
  pullPolicy: "IfNotPresent"

replicaCount: 2

mcp:
  type: "http"
  port: 8080
  env:
    LOG_LEVEL: "INFO"
  config:
    database_url: "postgresql://localhost:5432/mydb"

service:
  type: ClusterIP
  port: 8080

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

## Advanced Features

### Scaling

```bash
# Deploy with specific replica count
mcpt --backend kubernetes deploy github-server --config replicas=5

# Scale existing deployment
kubectl scale deployment github-server-abc123 --replicas=3 -n mcp-servers
```

### Service Types

Choose different service types based on your needs:

```json
{
  "service": {
    "type": "ClusterIP",    // Internal cluster access only
    "port": 8080
  }
}
```

```json
{
  "service": {
    "type": "NodePort",     // External access via node ports
    "port": 8080,
    "nodePort": 30080
  }
}
```

```json
{
  "service": {
    "type": "LoadBalancer", // Cloud provider load balancer
    "port": 8080
  }
}
```

### Resource Management

Configure CPU and memory for optimal performance:

```json
{
  "resources": {
    "requests": {
      "cpu": "200m",        // 0.2 CPU cores minimum
      "memory": "256Mi"     // 256MB memory minimum
    },
    "limits": {
      "cpu": "1000m",       // 1 CPU core maximum
      "memory": "1Gi"       // 1GB memory maximum
    }
  }
}
```

### Health Checks

HTTP servers automatically get health checks configured:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 5
```

## Management Commands

### List Deployments

```bash
# List all Kubernetes deployments
mcpt --backend kubernetes list

# List deployments in specific namespace
mcpt --backend kubernetes --namespace production list
```

### View Logs

```bash
# View logs from Kubernetes pods
mcpt --backend kubernetes logs github-server

# Follow logs in real-time
mcpt --backend kubernetes logs github-server -f
```

### Stop/Delete Deployments

```bash
# Scale to zero (stop)
mcpt --backend kubernetes stop github-server

# Delete completely
kubectl delete deployment,service,configmap -l app.kubernetes.io/managed-by=mcp-templates -n mcp-servers
```

### Cleanup

```bash
# Clean up stopped deployments (replicas=0)
mcpt --backend kubernetes cleanup

# Clean up specific template
mcpt --backend kubernetes cleanup github-server
```

## Service Discovery

### Internal Discovery

Services are accessible within the cluster using DNS:

```
http://{service-name}.{namespace}.svc.cluster.local:{port}
```

Example:
```
http://github-server-abc123.mcp-servers.svc.cluster.local:8080
```

### External Access

For external access, use NodePort or LoadBalancer services:

```bash
# Get external access information
kubectl get services -n mcp-servers

# Port forward for testing
kubectl port-forward service/github-server-abc123 8080:8080 -n mcp-servers
```

## Troubleshooting

### Common Issues

**1. Connection Refused**
```bash
# Check if kubeconfig is properly configured
kubectl cluster-info

# Verify namespace exists
kubectl get namespaces

# Check pod status
kubectl get pods -n mcp-servers
```

**2. Pods Not Starting**
```bash
# Check pod events
kubectl describe pod <pod-name> -n mcp-servers

# View pod logs
kubectl logs <pod-name> -n mcp-servers

# Check resource constraints
kubectl top pods -n mcp-servers
```

**3. Service Not Accessible**
```bash
# Check service endpoints
kubectl get endpoints -n mcp-servers

# Test service connectivity
kubectl run test-pod --image=busybox -n mcp-servers -- sleep 3600
kubectl exec -it test-pod -n mcp-servers -- wget -O- http://github-server:8080/health
```

### Debug Mode

Enable debug logging for detailed information:

```bash
# Set log level
export MCP_LOG_LEVEL=DEBUG

# Run with verbose output
mcpt --backend kubernetes deploy template --verbose
```

### Manual Resource Inspection

```bash
# Check all MCP-managed resources
kubectl get all -l app.kubernetes.io/managed-by=mcp-templates -n mcp-servers

# View detailed deployment info
kubectl describe deployment github-server-abc123 -n mcp-servers

# Check resource usage
kubectl top pods -n mcp-servers
```

## Best Practices

### Production Deployment

1. **Use Dedicated Namespace**
   ```bash
   mcpt --backend kubernetes --namespace mcp-production deploy template
   ```

2. **Set Resource Limits**
   ```json
   {
     "resources": {
       "requests": {"cpu": "100m", "memory": "128Mi"},
       "limits": {"cpu": "500m", "memory": "512Mi"}
     }
   }
   ```

3. **Configure Health Checks**
   - Ensure your MCP servers expose `/health` endpoint
   - Set appropriate timeout values

4. **Use ConfigMaps for Configuration**
   ```json
   {
     "config": {
       "database_url": "postgresql://db.production:5432/mcp",
       "log_level": "INFO"
     }
   }
   ```

### Security

1. **Use ServiceAccounts**
   ```yaml
   serviceAccount:
     create: true
     name: mcp-server-sa
   ```

2. **Network Policies**
   ```yaml
   kind: NetworkPolicy
   apiVersion: networking.k8s.io/v1
   metadata:
     name: mcp-server-netpol
   spec:
     podSelector:
       matchLabels:
         app.kubernetes.io/managed-by: mcp-templates
     ingress:
     - from:
       - namespaceSelector:
           matchLabels:
             name: gateway
   ```

3. **Pod Security Context**
   ```yaml
   securityContext:
     runAsNonRoot: true
     runAsUser: 1000
     fsGroup: 2000
   ```

### Monitoring

1. **Resource Monitoring**
   ```bash
   # Monitor resource usage
   kubectl top pods -n mcp-servers
   kubectl top nodes
   ```

2. **Application Monitoring**
   - Use Prometheus metrics if available
   - Monitor application logs
   - Set up alerting for pod failures

## Migration from Docker

### Comparison

| Feature | Docker | Kubernetes |
|---------|--------|------------|
| Single Host | ✅ | ❌ |
| Multi-Host | ❌ | ✅ |
| Auto-Scaling | ❌ | ✅ |
| Load Balancing | External | Built-in |
| Service Discovery | Manual | Automatic |
| Health Checks | Basic | Advanced |
| Rolling Updates | Manual | Automatic |

### Migration Steps

1. **Test in Development**
   ```bash
   # Start with local cluster (minikube/kind)
   mcpt --backend kubernetes deploy template
   ```

2. **Update Configurations**
   - Add Kubernetes-specific metadata to registry
   - Configure resource limits
   - Set up health checks

3. **Deploy to Staging**
   ```bash
   mcpt --backend kubernetes --namespace staging deploy template
   ```

4. **Production Deployment**
   ```bash
   mcpt --backend kubernetes --namespace production deploy template
   ```

5. **Migrate Traffic**
   - Use rolling updates for zero-downtime migration
   - Monitor application metrics during migration

## Examples

### Simple HTTP Server

```bash
# Deploy basic HTTP MCP server
mcpt --backend kubernetes deploy file-server
```

### Scaled Production Deployment

```bash
# Deploy with custom configuration
mcpt --backend kubernetes --namespace production deploy github-server \
  --config replicas=3 \
  --config 'resources={"requests":{"cpu":"200m","memory":"256Mi"},"limits":{"cpu":"1000m","memory":"1Gi"}}' \
  --config 'service={"type":"LoadBalancer","port":8080}'
```

### Multi-Server Setup

```bash
# Deploy multiple MCP servers
mcpt --backend kubernetes deploy github-server --config replicas=2
mcpt --backend kubernetes deploy file-server --config replicas=1
mcpt --backend kubernetes deploy database-server --config replicas=3

# List all deployments
mcpt --backend kubernetes list
```

This guide provides comprehensive coverage of the Kubernetes backend functionality. For additional help, refer to the [FAQ](faq.md) or check the [troubleshooting section](#troubleshooting).