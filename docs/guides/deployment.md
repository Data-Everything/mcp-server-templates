# Deployment Guide

Advanced deployment options for MCP server templates.

## Local Deployment

Run templates locally for development:

```bash
# Quick local deployment
mcpt deploy demo --local

# With custom configuration
mcpt deploy demo --local --env DEBUG=true
```

## Docker Deployment

Deploy using Docker containers:

```bash
# Deploy with Docker
mcpt deploy demo --docker

# Specify custom Docker options
mcpt deploy demo --docker --port 8080:8080 --env PRODUCTION=true
```

## Production Deployment

### Using Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  mcp-demo:
    image: dataeverything/mcp-demo:latest
    ports:
      - "8080:8080"
    environment:
      - DEMO_MESSAGE=Production Hello
      - LOG_LEVEL=info
    restart: unless-stopped
```

### Using Kubernetes

Example Kubernetes deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-demo
  template:
    metadata:
      labels:
        app: mcp-demo
    spec:
      containers:
      - name: mcp-demo
        image: dataeverything/mcp-demo:latest
        ports:
        - containerPort: 8080
        env:
        - name: DEMO_MESSAGE
          value: "Kubernetes Hello"
```

## Environment Configuration

### Development
- Enable debug logging
- Use local storage
- Relaxed security settings

### Production
- Structured logging
- Persistent storage
- Security hardening
- Health checks
- Monitoring integration

## Monitoring

Templates support standard monitoring:

- Health check endpoints
- Prometheus metrics
- Structured logging
- Error tracking
