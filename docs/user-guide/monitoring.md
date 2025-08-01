# Monitoring & Management

**Production monitoring, alerting, and management strategies for MCP Template Platform deployments.**

## Overview

Effective monitoring is crucial for production MCP deployments. This guide covers comprehensive monitoring strategies, alerting setup, performance optimization, and operational best practices.

### Key Monitoring Areas

- **Deployment Health**: Container status, uptime, restart counts
- **Resource Usage**: CPU, memory, disk, and network utilization
- **MCP Protocol**: Tool availability, response times, error rates
- **Application Metrics**: Tool usage, success rates, custom metrics
- **Infrastructure**: Docker daemon, system resources, network connectivity

## Built-in Monitoring Features

### CLI-Based Monitoring

```bash
# Real-time status monitoring
mcp-template status --watch --refresh 5

# Health-only monitoring
mcp-template status --health-only

# Deployment overview
mcp-template list --status

# Resource monitoring
mcp-template status deployment-name --detailed
```

### Status Monitoring Dashboard

```bash
# Interactive status dashboard
mcp-template dashboard

# Example output:
╭─────────────────── MCP Platform Dashboard ───────────────────╮
│                                                               │
│  🚀 Active Deployments: 12                                   │
│  ✅ Healthy: 10    ⚠️  Warning: 2    ❌ Failed: 0            │
│  📊 Total Memory: 2.4GB    💾 Total Disk: 15GB               │
│                                                               │
╰───────────────────────────────────────────────────────────────╯

┌──────────────────┬─────────────┬────────────┬──────────────────┐
│ Deployment       │ Template    │ Status     │ Resource Usage   │
├──────────────────┼─────────────┼────────────┼──────────────────┤
│ file-server-prod │ file-server │ ✅ Healthy │ 🟢 15% CPU, 180MB│
│ github-api       │ github      │ ✅ Healthy │ 🟢 8% CPU, 95MB  │
│ database-conn    │ database    │ ⚠️ Warning │ 🟡 65% CPU, 340MB│
│ slack-bot        │ slack       │ ✅ Healthy │ 🟢 12% CPU, 120MB│
└──────────────────┴─────────────┴────────────┴──────────────────┘

🔄 Auto-refresh: 5s    ⏰ Last Update: 2025-01-27 16:47:30 UTC
📊 Press 'd' for details, 'q' to quit, 'r' to refresh now
```

### Automated Health Checks

```bash
# Set up automated health monitoring
mcp-template monitor --config health-check.json

# Example health-check.json:
{
  "interval": 30,
  "deployments": ["critical-app", "file-server-prod"],
  "actions": {
    "on_failure": "restart",
    "on_warning": "alert",
    "max_restarts": 3
  },
  "notifications": {
    "email": "admin@company.com",
    "webhook": "https://hooks.slack.com/services/..."
  }
}
```

## Logging & Log Management

### Centralized Logging

```bash
# Stream logs from all deployments
mcp-template logs --all --follow

# Filter logs by severity
mcp-template logs --all --filter "ERROR|WARN"

# Export logs for analysis
mcp-template logs deployment --since 24h --format json > logs.json
```

### Log Aggregation Setup

```bash
# Forward logs to external systems
mcp-template logs deployment --format json --follow | \
  curl -X POST -H "Content-Type: application/json" \
  --data-binary @- \
  https://logs.company.com/mcp-platform
```

### Log Analysis Scripts

```python
#!/usr/bin/env python3
"""Analyze MCP deployment logs for patterns and issues."""

import json
import subprocess
from collections import defaultdict
from datetime import datetime, timedelta

def analyze_deployment_logs(deployment_name, hours=24):
    """Analyze logs for a specific deployment."""

    # Get logs
    result = subprocess.run([
        'python', '-m', 'mcp_template', 'logs',
        deployment_name, '--since', f'{hours}h', '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Error getting logs: {result.stderr}")
        return

    # Parse and analyze
    logs = []
    for line in result.stdout.strip().split('\n'):
        if line:
            try:
                logs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Analysis
    error_count = len([log for log in logs if log.get('level') == 'ERROR'])
    warning_count = len([log for log in logs if log.get('level') == 'WARN'])

    # Tool usage analysis
    tool_usage = defaultdict(int)
    for log in logs:
        if 'tool_call' in log.get('message', ''):
            tool_name = extract_tool_name(log['message'])
            if tool_name:
                tool_usage[tool_name] += 1

    # Report
    print(f"📊 Log Analysis for {deployment_name} (last {hours}h)")
    print(f"📝 Total entries: {len(logs)}")
    print(f"❌ Errors: {error_count}")
    print(f"⚠️  Warnings: {warning_count}")

    if tool_usage:
        print("\n🛠️  Tool Usage:")
        for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"   {tool}: {count} calls")

def extract_tool_name(message):
    """Extract tool name from log message."""
    # Implementation depends on log format
    if "tool_call:" in message:
        return message.split("tool_call:")[1].split()[0]
    return None

if __name__ == "__main__":
    import sys
    deployment = sys.argv[1] if len(sys.argv) > 1 else "all"
    hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24

    if deployment == "all":
        # Analyze all deployments
        result = subprocess.run([
            'python', '-m', 'mcp_template', 'list', '--format', 'json'
        ], capture_output=True, text=True)

        deployments = json.loads(result.stdout)
        for dep in deployments:
            analyze_deployment_logs(dep['id'], hours)
            print()
    else:
        analyze_deployment_logs(deployment, hours)
```

## Metrics Collection

### System Metrics

```bash
# Collect system metrics
mcp-template metrics --output prometheus

# Example Prometheus metrics:
# mcp_deployment_status{deployment="file-server"} 1
# mcp_deployment_uptime_seconds{deployment="file-server"} 86400
# mcp_deployment_memory_bytes{deployment="file-server"} 185073664
# mcp_deployment_cpu_percent{deployment="file-server"} 5.2
# mcp_tool_calls_total{deployment="file-server",tool="read_file"} 157
# mcp_tool_errors_total{deployment="file-server",tool="read_file"} 2
```

### Custom Metrics

```python
#!/usr/bin/env python3
"""Custom metrics collection for MCP deployments."""

import json
import subprocess
import time
from prometheus_client import start_http_server, Gauge, Counter, Histogram

# Prometheus metrics
deployment_status = Gauge('mcp_deployment_status', 'Deployment status (1=healthy, 0.5=warning, 0=error)', ['deployment', 'template'])
deployment_uptime = Gauge('mcp_deployment_uptime_seconds', 'Deployment uptime in seconds', ['deployment'])
deployment_memory = Gauge('mcp_deployment_memory_bytes', 'Memory usage in bytes', ['deployment'])
deployment_cpu = Gauge('mcp_deployment_cpu_percent', 'CPU usage percentage', ['deployment'])

tool_calls = Counter('mcp_tool_calls_total', 'Total tool calls', ['deployment', 'tool'])
tool_errors = Counter('mcp_tool_errors_total', 'Total tool errors', ['deployment', 'tool'])
tool_duration = Histogram('mcp_tool_duration_seconds', 'Tool execution duration', ['deployment', 'tool'])

def collect_metrics():
    """Collect metrics from all deployments."""
    try:
        # Get deployment status
        result = subprocess.run([
            'python', '-m', 'mcp_template', 'status', '--format', 'json'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            status_data = json.loads(result.stdout)

            for deployment in status_data.get('deployments', []):
                deployment_id = deployment['deployment_id']
                template_name = deployment['template']['name']

                # Status metrics
                health_value = {
                    'healthy': 1.0,
                    'warning': 0.5,
                    'critical': 0.0,
                    'unknown': -1.0
                }.get(deployment['status']['health'], -1.0)

                deployment_status.labels(
                    deployment=deployment_id,
                    template=template_name
                ).set(health_value)

                # Resource metrics
                deployment_uptime.labels(deployment=deployment_id).set(
                    deployment['status'].get('uptime_seconds', 0)
                )

                container = deployment.get('container', {})
                deployment_memory.labels(deployment=deployment_id).set(
                    container.get('memory_usage', 0)
                )
                deployment_cpu.labels(deployment=deployment_id).set(
                    container.get('cpu_percent', 0)
                )

        # Collect tool metrics from logs
        collect_tool_metrics()

    except Exception as e:
        print(f"Error collecting metrics: {e}")

def collect_tool_metrics():
    """Collect tool usage metrics from recent logs."""
    # Get recent logs and parse for tool usage
    result = subprocess.run([
        'python', '-m', 'mcp_template', 'logs', '--all',
        '--since', '5m', '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    log_entry = json.loads(line)
                    parse_tool_log_entry(log_entry)
                except json.JSONDecodeError:
                    continue

def parse_tool_log_entry(log_entry):
    """Parse log entry for tool metrics."""
    message = log_entry.get('message', '')
    deployment = log_entry.get('deployment', 'unknown')

    # Tool call tracking
    if 'tool_call:' in message:
        tool_name = message.split('tool_call:')[1].split()[0]
        tool_calls.labels(deployment=deployment, tool=tool_name).inc()

    # Tool error tracking
    if 'tool_error:' in message:
        tool_name = message.split('tool_error:')[1].split()[0]
        tool_errors.labels(deployment=deployment, tool=tool_name).inc()

    # Tool duration tracking
    if 'tool_duration:' in message:
        parts = message.split('tool_duration:')[1].split()
        tool_name = parts[0]
        duration = float(parts[1].replace('s', ''))
        tool_duration.labels(deployment=deployment, tool=tool_name).observe(duration)

if __name__ == '__main__':
    # Start Prometheus metrics server
    start_http_server(8000)
    print("Metrics server started on port 8000")

    # Collect metrics every 30 seconds
    while True:
        collect_metrics()
        time.sleep(30)
```

## Alerting & Notifications

### Alert Configuration

```yaml
# alerts.yaml
alerts:
  - name: deployment_down
    condition: mcp_deployment_status == 0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "MCP deployment {{ $labels.deployment }} is down"
      description: "Deployment {{ $labels.deployment }} has been down for more than 5 minutes"

  - name: high_memory_usage
    condition: mcp_deployment_memory_bytes / (1024*1024*1024) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage for {{ $labels.deployment }}"
      description: "Memory usage is {{ $value }}GB for deployment {{ $labels.deployment }}"

  - name: high_error_rate
    condition: rate(mcp_tool_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate for {{ $labels.deployment }}"
      description: "Error rate is {{ $value }} per second for deployment {{ $labels.deployment }}"
```

### Notification Integration

```python
#!/usr/bin/env python3
"""Alert notification system for MCP deployments."""

import json
import subprocess
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

class AlertManager:
    def __init__(self, config_file='alert-config.json'):
        with open(config_file) as f:
            self.config = json.load(f)

    def check_deployments(self):
        """Check all deployments and send alerts if needed."""
        result = subprocess.run([
            'python', '-m', 'mcp_template', 'status', '--format', 'json'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            status_data = json.loads(result.stdout)

            for deployment in status_data.get('deployments', []):
                self.check_deployment_health(deployment)

    def check_deployment_health(self, deployment):
        """Check individual deployment health and alert if needed."""
        deployment_id = deployment['deployment_id']
        health = deployment['status']['health']

        # Check for critical issues
        if health == 'critical' or deployment['status']['state'] == 'failed':
            self.send_critical_alert(deployment)

        # Check for warnings
        elif health == 'warning':
            self.send_warning_alert(deployment)

        # Check resource usage
        container = deployment.get('container', {})
        memory_usage = container.get('memory_usage', 0)
        memory_limit = container.get('memory_limit', 1024*1024*1024)  # 1GB default

        if memory_usage / memory_limit > 0.9:
            self.send_resource_alert(deployment, 'memory', memory_usage / memory_limit * 100)

    def send_critical_alert(self, deployment):
        """Send critical alert for deployment failure."""
        message = {
            'severity': 'critical',
            'deployment': deployment['deployment_id'],
            'template': deployment['template']['name'],
            'status': deployment['status']['state'],
            'health': deployment['status']['health'],
            'timestamp': datetime.utcnow().isoformat()
        }

        self.send_notification('Critical: MCP Deployment Down', message)

    def send_warning_alert(self, deployment):
        """Send warning alert for deployment issues."""
        message = {
            'severity': 'warning',
            'deployment': deployment['deployment_id'],
            'template': deployment['template']['name'],
            'health': deployment['status']['health'],
            'timestamp': datetime.utcnow().isoformat()
        }

        self.send_notification('Warning: MCP Deployment Issue', message)

    def send_resource_alert(self, deployment, resource_type, usage_percent):
        """Send alert for high resource usage."""
        message = {
            'severity': 'warning',
            'deployment': deployment['deployment_id'],
            'resource_type': resource_type,
            'usage_percent': usage_percent,
            'timestamp': datetime.utcnow().isoformat()
        }

        self.send_notification(f'High {resource_type.title()} Usage', message)

    def send_notification(self, subject, message):
        """Send notification via configured channels."""
        # Slack webhook
        if 'slack_webhook' in self.config:
            self.send_slack_notification(subject, message)

        # Email
        if 'email' in self.config:
            self.send_email_notification(subject, message)

        # PagerDuty
        if 'pagerduty_key' in self.config and message['severity'] == 'critical':
            self.send_pagerduty_alert(subject, message)

    def send_slack_notification(self, subject, message):
        """Send Slack notification."""
        webhook_url = self.config['slack_webhook']

        color = 'danger' if message['severity'] == 'critical' else 'warning'

        payload = {
            'attachments': [{
                'color': color,
                'title': subject,
                'fields': [
                    {'title': 'Deployment', 'value': message['deployment'], 'short': True},
                    {'title': 'Severity', 'value': message['severity'].upper(), 'short': True},
                    {'title': 'Time', 'value': message['timestamp'], 'short': True}
                ],
                'text': json.dumps(message, indent=2)
            }]
        }

        requests.post(webhook_url, json=payload)

    def send_email_notification(self, subject, message):
        """Send email notification."""
        email_config = self.config['email']

        msg = MIMEText(json.dumps(message, indent=2))
        msg['Subject'] = f"[MCP Platform] {subject}"
        msg['From'] = email_config['from']
        msg['To'] = email_config['to']

        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        if email_config.get('username'):
            server.starttls()
            server.login(email_config['username'], email_config['password'])

        server.send_message(msg)
        server.quit()

    def send_pagerduty_alert(self, subject, message):
        """Send PagerDuty alert for critical issues."""
        routing_key = self.config['pagerduty_key']

        payload = {
            'routing_key': routing_key,
            'event_action': 'trigger',
            'payload': {
                'summary': subject,
                'source': 'mcp-platform',
                'severity': 'critical',
                'custom_details': message
            }
        }

        requests.post('https://events.pagerduty.com/v2/enqueue', json=payload)

# Example usage
if __name__ == '__main__':
    alert_manager = AlertManager()
    alert_manager.check_deployments()
```

## Performance Monitoring

### Resource Optimization

```bash
# Monitor resource usage trends
mcp-template metrics --format csv --duration 24h > usage-trends.csv

# Analyze performance bottlenecks
mcp-template analyze-performance deployment-name

# Optimize resource allocation
mcp-template deploy template --memory 512m --cpu 0.5 --optimize
```

### Performance Benchmarking

```python
#!/usr/bin/env python3
"""Performance benchmarking for MCP deployments."""

import time
import json
import subprocess
import statistics
from concurrent.futures import ThreadPoolExecutor
import requests

def benchmark_deployment(deployment_name, test_duration=60):
    """Benchmark a deployment's performance."""

    print(f"🚀 Starting benchmark for {deployment_name}")

    # Get deployment info
    result = subprocess.run([
        'python', '-m', 'mcp_template', 'status',
        deployment_name, '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to get deployment status: {result.stderr}")
        return

    deployment_info = json.loads(result.stdout)

    # Get available tools
    result = subprocess.run([
        'python', '-m', 'mcp_template', 'tools',
        deployment_name, '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Failed to get tools: {result.stderr}")
        return

    tools_info = json.loads(result.stdout)
    tools = [tool['name'] for tool in tools_info.get('tools', [])]

    if not tools:
        print("❌ No tools found for benchmarking")
        return

    print(f"📊 Benchmarking {len(tools)} tools for {test_duration}s")

    # Run benchmark
    results = {}
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=5) as executor:
        while time.time() - start_time < test_duration:
            futures = []

            for tool in tools[:3]:  # Test top 3 tools
                future = executor.submit(call_tool, deployment_name, tool)
                futures.append((tool, future))

            for tool, future in futures:
                try:
                    duration = future.result(timeout=10)
                    if tool not in results:
                        results[tool] = []
                    results[tool].append(duration)
                except Exception as e:
                    print(f"⚠️  Tool {tool} failed: {e}")

            time.sleep(1)  # Rate limiting

    # Analyze results
    print("\n📈 Benchmark Results:")
    for tool, durations in results.items():
        if durations:
            avg_duration = statistics.mean(durations)
            median_duration = statistics.median(durations)
            p95_duration = sorted(durations)[int(len(durations) * 0.95)]

            print(f"🛠️  {tool}:")
            print(f"   Calls: {len(durations)}")
            print(f"   Avg: {avg_duration:.3f}s")
            print(f"   Median: {median_duration:.3f}s")
            print(f"   P95: {p95_duration:.3f}s")

    # Resource usage during benchmark
    final_status = subprocess.run([
        'python', '-m', 'mcp_template', 'status',
        deployment_name, '--format', 'json'
    ], capture_output=True, text=True)

    if final_status.returncode == 0:
        final_info = json.loads(final_status.stdout)
        container = final_info.get('container', {})

        print(f"\n💾 Resource Usage:")
        print(f"   Memory: {container.get('memory_usage', 0) / 1024 / 1024:.1f} MB")
        print(f"   CPU: {container.get('cpu_percent', 0):.1f}%")

def call_tool(deployment_name, tool_name):
    """Call a specific tool and measure response time."""
    start_time = time.time()

    # This would need to be implemented based on your tool calling mechanism
    # For now, we'll simulate a tool call
    time.sleep(0.1)  # Simulate tool execution

    return time.time() - start_time

if __name__ == "__main__":
    import sys
    deployment = sys.argv[1] if len(sys.argv) > 1 else "demo"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    benchmark_deployment(deployment, duration)
```

## Production Best Practices

### Deployment Strategies

```bash
# Blue-green deployment
mcp-template deploy template --name template-blue
mcp-template deploy template --name template-green

# Rolling updates
mcp-template deploy template --strategy rolling --instances 3

# Canary deployment
mcp-template deploy template --canary 10%
```

### Backup & Recovery

```bash
# Backup deployment configurations
mcp-template backup --output backup-$(date +%Y%m%d).tar.gz

# Backup specific deployment
mcp-template backup deployment-name --include-data

# Restore from backup
mcp-template restore backup-20250127.tar.gz

# Disaster recovery
mcp-template restore --disaster-recovery --cluster-config
```

### High Availability Setup

```yaml
# ha-config.yaml
high_availability:
  load_balancer:
    enabled: true
    algorithm: round_robin
    health_check_interval: 30s

  replication:
    min_replicas: 2
    max_replicas: 5
    scale_trigger: cpu_usage > 70%

  failover:
    enabled: true
    timeout: 30s
    max_failures: 3
```

```bash
# Deploy with high availability
mcp-template deploy template --ha-config ha-config.yaml
```

## Integration with External Systems

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "MCP Platform Monitoring",
    "panels": [
      {
        "title": "Deployment Status",
        "type": "stat",
        "targets": [{
          "expr": "mcp_deployment_status",
          "legendFormat": "{{deployment}}"
        }]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [{
          "expr": "mcp_deployment_memory_bytes / 1024 / 1024",
          "legendFormat": "{{deployment}} Memory (MB)"
        }]
      },
      {
        "title": "Tool Call Rate",
        "type": "graph",
        "targets": [{
          "expr": "rate(mcp_tool_calls_total[5m])",
          "legendFormat": "{{deployment}}/{{tool}}"
        }]
      }
    ]
  }
}
```

### ELK Stack Integration

```yaml
# filebeat.yml
filebeat.inputs:
- type: docker
  containers.ids:
  - "*"
  containers.path: "/var/lib/docker/containers"
  containers.stream: "stdout"
  json.keys_under_root: true
  json.add_error_key: true
  processors:
  - add_docker_metadata: ~

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "mcp-platform-%{+yyyy.MM.dd}"

logging.level: info
```

By implementing comprehensive monitoring and management practices, you can ensure reliable, performant, and observable MCP Platform deployments in production environments.
