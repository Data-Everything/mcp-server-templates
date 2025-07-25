# Filesystem MCP Server - Real-World Usage Guide

## Overview

The Filesystem MCP Server provides secure file system access through the Model Context Protocol (MCP). This guide covers practical usage scenarios, stdio handling, and production deployment considerations.

## Quick Start

### 1. Deploy the Server

```bash
# Using the MCP deployment tool
python -m mcp_template deploy file-server --name my-file-server

# Or with custom configuration
python -m mcp_template deploy file-server \
  --name my-file-server \
  --config '{"allowed_directories": ["/home/user/documents", "/tmp"], "max_file_size": "10MB"}'
```

### 2. Configure Your MCP Client

**Claude Desktop Configuration:**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "docker",
      "args": ["exec", "-i", "my-file-server", "python", "-m", "src.server"]
    }
  }
}
```

**Python Client:**
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_filesystem_server():
    server_params = StdioServerParameters(
        command="docker",
        args=["exec", "-i", "my-file-server", "python", "-m", "src.server"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List files in a directory
            result = await session.call_tool("list_directory", {"path": "/home/user/documents"})
            print("Directory contents:", result.content[0].text)

            # Read a file
            result = await session.call_tool("read_file", {"path": "/home/user/documents/readme.txt"})
            print("File contents:", result.content[0].text)

asyncio.run(use_filesystem_server())
```

## Real-World Use Cases

### 1. Document Processing and Analysis

**Scenario:** Analyze and process documents in a corporate environment

```python
# Example: Batch process legal documents
async def process_legal_documents():
    async with get_filesystem_session() as session:
        # List all PDF files in the legal directory
        files = await session.call_tool("list_directory", {
            "path": "/legal/contracts",
            "pattern": "*.pdf"
        })

        for file_path in files:
            # Read document metadata
            metadata = await session.call_tool("get_file_info", {"path": file_path})

            # Process if modified recently
            if is_recently_modified(metadata):
                # Extract text content (if supported)
                content = await session.call_tool("read_file", {"path": file_path})

                # Analyze with AI/ML pipeline
                analysis = await analyze_legal_document(content)

                # Save analysis results
                result_path = file_path.replace(".pdf", "_analysis.json")
                await session.call_tool("write_file", {
                    "path": result_path,
                    "content": json.dumps(analysis, indent=2)
                })
```

**Claude Desktop Usage:**
```
User: "Please analyze all PDF files in /legal/contracts that were modified in the last week. For each file, extract key contract terms, identify parties, and highlight any unusual clauses."

Claude: "I'll help you analyze the recent legal documents. Let me start by listing the PDF files in the contracts directory and checking their modification dates."

[Claude automatically uses the filesystem tools to:]
1. List files in /legal/contracts
2. Check modification dates
3. Read PDF contents (if text-extractable)
4. Analyze each document
5. Create summary reports
```

### 2. Configuration Management

**Scenario:** Manage application configurations across environments

```python
async def manage_app_configs():
    async with get_filesystem_session() as session:
        environments = ["dev", "staging", "prod"]

        for env in environments:
            config_path = f"/configs/{env}/app.json"

            # Read current configuration
            current_config = await session.call_tool("read_file", {"path": config_path})
            config_data = json.loads(current_config.content[0].text)

            # Update database connection strings
            config_data["database"]["host"] = f"db-{env}.company.com"
            config_data["database"]["ssl"] = True if env == "prod" else False

            # Write updated configuration
            await session.call_tool("write_file", {
                "path": config_path,
                "content": json.dumps(config_data, indent=2)
            })

            # Create backup
            backup_path = f"/configs/{env}/backups/app_{datetime.now().isoformat()}.json"
            await session.call_tool("write_file", {
                "path": backup_path,
                "content": json.dumps(config_data, indent=2)
            })
```

### 3. Log Analysis and Monitoring

**Scenario:** Real-time log analysis and alerting

```python
async def analyze_application_logs():
    async with get_filesystem_session() as session:
        log_files = [
            "/var/log/app/application.log",
            "/var/log/app/error.log",
            "/var/log/nginx/access.log"
        ]

        for log_file in log_files:
            # Read recent log entries (last 1000 lines)
            recent_logs = await session.call_tool("tail_file", {
                "path": log_file,
                "lines": 1000
            })

            # Parse and analyze for error patterns
            error_patterns = analyze_log_for_errors(recent_logs.content[0].text)

            if error_patterns:
                # Create alert summary
                alert_summary = create_alert_summary(error_patterns)

                # Save alert to monitoring directory
                alert_path = f"/monitoring/alerts/{datetime.now().strftime('%Y%m%d_%H%M%S')}_alert.json"
                await session.call_tool("write_file", {
                    "path": alert_path,
                    "content": json.dumps(alert_summary, indent=2)
                })
```

### 4. Development Workflow Automation

**Scenario:** Automate code review and documentation tasks

```python
async def automated_code_review():
    async with get_filesystem_session() as session:
        # Find all Python files in the project
        python_files = await session.call_tool("find_files", {
            "path": "/project/src",
            "pattern": "*.py",
            "recursive": True
        })

        review_results = []

        for file_path in python_files:
            # Read source code
            source_code = await session.call_tool("read_file", {"path": file_path})

            # Perform static analysis
            analysis = perform_static_analysis(source_code.content[0].text)

            # Generate documentation
            docs = generate_function_docs(source_code.content[0].text)

            # Save results
            review_results.append({
                "file": file_path,
                "analysis": analysis,
                "documentation": docs
            })

        # Generate comprehensive review report
        report_path = "/project/reports/code_review_report.md"
        report_content = generate_review_report(review_results)

        await session.call_tool("write_file", {
            "path": report_path,
            "content": report_content
        })
```

## Handling stdio Transport and Container Lifecycle

### Understanding stdio Transport

The filesystem server uses stdio (standard input/output) transport, which means:

1. **No HTTP endpoints** - Communication happens through stdin/stdout
2. **Process-based** - Each client connection starts a new server process
3. **Stateless** - No persistent connections between calls

### Container Lifecycle Management

#### Automatic Shutdown Behavior

The container shuts down automatically because:
- stdio transport completes when client disconnects
- No persistent HTTP server running
- Container exits when main process ends

#### Keeping Container Running

**Option 1: Long-running Mode (Recommended)**
```bash
# Deploy with keep-alive configuration
python -m mcp_template deploy file-server \
  --name my-file-server \
  --config '{"keep_alive": true, "idle_timeout": 3600}'

# This keeps a background process running to prevent container shutdown
```

**Option 2: On-demand Mode**
```bash
# Start container only when needed
docker run -d --name file-server-pool \
  -v /host/data:/container/data \
  your-org/file-server:latest \
  sleep infinity

# Use with exec for each MCP call
docker exec -i file-server-pool python -m src.server
```

**Option 3: Service Mode with Restart Policy**
```yaml
# docker-compose.yml
version: '3.8'
services:
  file-server:
    image: your-org/file-server:latest
    container_name: my-file-server
    restart: unless-stopped
    command: tail -f /dev/null  # Keep container alive
    volumes:
      - ./data:/app/data
    environment:
      - MCP_ALLOWED_DIRECTORIES=/app/data
```

### Production Deployment Patterns

#### Pattern 1: Pool of Worker Containers

```bash
# Create a pool of file server containers
for i in {1..5}; do
  docker run -d --name file-server-worker-$i \
    -v /data:/app/data \
    your-org/file-server:latest \
    sleep infinity
done

# Load balancer script for client connections
#!/bin/bash
WORKER_ID=$((RANDOM % 5 + 1))
docker exec -i file-server-worker-$WORKER_ID python -m src.server
```

#### Pattern 2: Docker Swarm Service

```yaml
# docker-stack.yml
version: '3.8'
services:
  file-server:
    image: your-org/file-server:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
    volumes:
      - type: bind
        source: /host/data
        target: /app/data
    command: tail -f /dev/null
```

#### Pattern 3: Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: file-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: file-server
  template:
    metadata:
      labels:
        app: file-server
    spec:
      containers:
      - name: file-server
        image: your-org/file-server:latest
        command: ["tail", "-f", "/dev/null"]
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      volumes:
      - name: data-volume
        hostPath:
          path: /host/data
```

## Security Considerations

### Directory Access Control

```json
{
  "allowed_directories": [
    "/app/data",
    "/home/user/documents",
    "/tmp/workspace"
  ],
  "denied_directories": [
    "/etc",
    "/var/lib",
    "/root",
    "/home/user/.ssh"
  ],
  "read_only_directories": [
    "/app/config",
    "/app/templates"
  ]
}
```

### File Size and Operation Limits

```json
{
  "max_file_size": "10MB",
  "max_files_per_operation": 100,
  "allowed_extensions": [".txt", ".json", ".md", ".py", ".js"],
  "denied_extensions": [".exe", ".bat", ".sh"],
  "max_directory_depth": 10
}
```

### Audit Logging

```python
# Enable comprehensive audit logging
{
  "audit_logging": {
    "enabled": true,
    "log_file": "/app/logs/filesystem_audit.log",
    "log_level": "INFO",
    "include_content": false,  # Don't log file contents for privacy
    "log_failed_attempts": true
  }
}
```

## Monitoring and Troubleshooting

### Health Checks

```bash
# Check if container is responsive
docker exec my-file-server python -c "
import sys
from src.server import health_check
print('Health:', health_check())
"

# Test MCP protocol response
echo '{"method": "tools/list", "params": {}}' | \
  docker exec -i my-file-server python -m src.server
```

### Performance Monitoring

```python
async def monitor_filesystem_performance():
    start_time = time.time()

    # Measure file operation latency
    async with get_filesystem_session() as session:
        result = await session.call_tool("list_directory", {"path": "/app/data"})

    latency = time.time() - start_time

    # Log performance metrics
    performance_log = {
        "timestamp": datetime.now().isoformat(),
        "operation": "list_directory",
        "latency_ms": latency * 1000,
        "status": "success" if result else "error"
    }

    # Send to monitoring system
    await send_to_monitoring(performance_log)
```

### Common Issues and Solutions

#### Issue: Container Exits Immediately

**Cause:** No process keeping container alive
**Solution:** Use keep-alive configuration or persistent command

```bash
# Wrong: Container exits after MCP call
docker run your-org/file-server:latest python -m src.server

# Right: Keep container running
docker run -d your-org/file-server:latest tail -f /dev/null
```

#### Issue: Permission Denied Errors

**Cause:** File ownership or directory permissions
**Solution:** Set proper permissions and user mapping

```bash
# Fix file permissions
docker exec my-file-server chown -R app:app /app/data
docker exec my-file-server chmod -R 755 /app/data

# Run container with correct user ID
docker run --user $(id -u):$(id -g) your-org/file-server:latest
```

#### Issue: Slow File Operations

**Cause:** Large files or deep directory structures
**Solution:** Implement pagination and streaming

```python
# Use streaming for large files
async def read_large_file_streaming(file_path, chunk_size=8192):
    async with get_filesystem_session() as session:
        file_info = await session.call_tool("get_file_info", {"path": file_path})
        file_size = file_info["size"]

        chunks = []
        for offset in range(0, file_size, chunk_size):
            chunk = await session.call_tool("read_file_chunk", {
                "path": file_path,
                "offset": offset,
                "size": min(chunk_size, file_size - offset)
            })
            chunks.append(chunk.content[0].text)

        return "".join(chunks)
```

## Integration Examples

### With Data Processing Pipelines

```python
async def data_pipeline_integration():
    """Integrate filesystem server with data processing pipeline."""

    async with get_filesystem_session() as session:
        # Stage 1: Data Ingestion
        raw_files = await session.call_tool("list_directory", {
            "path": "/data/raw",
            "pattern": "*.csv"
        })

        processed_files = []

        for raw_file in raw_files:
            # Read raw data
            raw_data = await session.call_tool("read_file", {"path": raw_file})

            # Process data (transform, clean, validate)
            processed_data = process_csv_data(raw_data.content[0].text)

            # Save processed data
            processed_file = raw_file.replace("/raw/", "/processed/").replace(".csv", "_processed.json")
            await session.call_tool("write_file", {
                "path": processed_file,
                "content": json.dumps(processed_data, indent=2)
            })

            processed_files.append(processed_file)

        # Stage 2: Generate Summary Report
        summary = generate_processing_summary(processed_files)
        await session.call_tool("write_file", {
            "path": "/data/reports/processing_summary.json",
            "content": json.dumps(summary, indent=2)
        })
```

### With Machine Learning Workflows

```python
async def ml_workflow_integration():
    """Use filesystem server for ML data management."""

    async with get_filesystem_session() as session:
        # Load training data
        training_files = await session.call_tool("find_files", {
            "path": "/ml/datasets/training",
            "pattern": "*.jsonl",
            "recursive": True
        })

        # Prepare data for training
        training_data = []
        for file_path in training_files:
            data = await session.call_tool("read_file", {"path": file_path})
            training_data.extend(parse_jsonl(data.content[0].text))

        # Train model (external ML framework)
        model = train_model(training_data)

        # Save model artifacts
        model_path = f"/ml/models/{datetime.now().strftime('%Y%m%d_%H%M%S')}_model.pkl"
        await session.call_tool("write_file", {
            "path": model_path,
            "content": serialize_model(model)
        })

        # Create model metadata
        metadata = {
            "created_at": datetime.now().isoformat(),
            "training_files": training_files,
            "model_type": type(model).__name__,
            "performance_metrics": evaluate_model(model, training_data)
        }

        await session.call_tool("write_file", {
            "path": model_path.replace(".pkl", "_metadata.json"),
            "content": json.dumps(metadata, indent=2)
        })
```

## Best Practices

### 1. Resource Management

- **Limit concurrent operations** to prevent resource exhaustion
- **Use streaming** for large files to manage memory usage
- **Implement timeouts** for long-running operations
- **Monitor disk space** and implement cleanup policies

### 2. Security

- **Validate all paths** to prevent directory traversal attacks
- **Sanitize file names** to prevent injection attacks
- **Use least privilege** - only grant necessary directory access
- **Audit all operations** for security monitoring

### 3. Performance

- **Cache frequently accessed files** when appropriate
- **Use batch operations** for multiple file operations
- **Implement pagination** for large directory listings
- **Optimize for your use case** - read-heavy vs write-heavy

### 4. Reliability

- **Implement retry logic** for transient failures
- **Use health checks** to monitor server status
- **Plan for graceful degradation** when server is unavailable
- **Backup critical data** regularly

This comprehensive guide should help users understand how to effectively deploy and use the filesystem MCP server in real-world scenarios while handling the stdio transport characteristics properly.
