# Complete Examples

This section provides comprehensive examples demonstrating real-world usage patterns of the MCPClient for various scenarios.

## DevOps Automation

### CI/CD Pipeline Integration

```python
"""
CI/CD Pipeline Example: Deploy and test MCP servers as part of deployment pipeline
"""
import asyncio
from typing import Dict, List
from mcp_template.client import MCPClient
from mcp_template.exceptions import DeploymentError, ToolCallError

class MCPPipeline:
    """MCP deployment pipeline for CI/CD"""
    
    def __init__(self, environment: str = "staging"):
        self.environment = environment
        self.deployed_services: List[str] = []
    
    async def deploy_stack(self, services: List[Dict]) -> bool:
        """Deploy a complete stack of MCP services"""
        async with MCPClient() as client:
            try:
                for service_config in services:
                    template = service_config["template"]
                    config = service_config.get("config", {})
                    config["environment"] = self.environment
                    
                    print(f"🚀 Deploying {template} for {self.environment}")
                    result = await client.start_server(template, config)
                    
                    if result["success"]:
                        deployment_id = result["deployment_id"]
                        self.deployed_services.append(deployment_id)
                        print(f"✅ Deployed {template}: {deployment_id}")
                        
                        # Health check
                        if not await self._health_check(client, template, deployment_id):
                            raise DeploymentError(f"Health check failed for {template}")
                    else:
                        raise DeploymentError(f"Failed to deploy {template}: {result['error']}")
                
                print(f"🎉 Stack deployment complete: {len(self.deployed_services)} services")
                return True
                
            except Exception as e:
                print(f"❌ Stack deployment failed: {e}")
                await self._cleanup_stack(client)
                return False
    
    async def _health_check(self, client: MCPClient, template: str, deployment_id: str) -> bool:
        """Perform health check on deployed service"""
        try:
            # Wait for service to start
            await asyncio.sleep(3)
            
            # Check if tools are available
            tools = await client.list_tools(template)
            if not tools:
                print(f"⚠️  No tools found for {template}")
                return False
            
            # Test a basic tool if available
            basic_tools = ["health", "ping", "echo", "status"]
            test_tool = next((t for t in tools if t["name"] in basic_tools), None)
            
            if test_tool:
                result = await client.call_tool(template, test_tool["name"], {})
                if not result["success"]:
                    print(f"⚠️  Health check tool failed for {template}")
                    return False
            
            print(f"✅ Health check passed for {template}")
            return True
            
        except Exception as e:
            print(f"❌ Health check error for {template}: {e}")
            return False
    
    async def run_integration_tests(self) -> bool:
        """Run integration tests against deployed stack"""
        async with MCPClient() as client:
            try:
                print("🧪 Running integration tests...")
                
                # Test service connectivity
                servers = client.list_servers()
                active_servers = [s for s in servers if s["status"] == "running"]
                
                if len(active_servers) != len(self.deployed_services):
                    print(f"❌ Expected {len(self.deployed_services)} services, found {len(active_servers)}")
                    return False
                
                # Test cross-service functionality
                for server in active_servers:
                    template = server["template"]
                    tools = await client.list_tools(template)
                    
                    # Test tool execution
                    if tools:
                        test_tool = tools[0]  # Test first available tool
                        result = await client.call_tool(template, test_tool["name"], {})
                        
                        if not result["success"]:
                            print(f"❌ Integration test failed for {template}: {result['error']}")
                            return False
                
                print("✅ All integration tests passed")
                return True
                
            except Exception as e:
                print(f"❌ Integration tests failed: {e}")
                return False
    
    async def _cleanup_stack(self, client: MCPClient):
        """Clean up deployed services"""
        print("🧹 Cleaning up deployed services...")
        for deployment_id in self.deployed_services:
            try:
                await client.stop_server(deployment_id)
                print(f"🗑️  Stopped {deployment_id}")
            except Exception as e:
                print(f"⚠️  Failed to stop {deployment_id}: {e}")
        
        self.deployed_services.clear()

# Usage in CI/CD pipeline
async def run_deployment_pipeline():
    """Complete CI/CD pipeline example"""
    pipeline = MCPPipeline("staging")
    
    # Define services to deploy
    services = [
        {
            "template": "demo",
            "config": {
                "port": 8080,
                "debug": True,
                "log_level": "INFO"
            }
        },
        {
            "template": "filesystem", 
            "config": {
                "allowed_dirs": ["/tmp/staging"],
                "read_only": False
            }
        },
        {
            "template": "github",
            "config": {
                "api_endpoint": "https://api.github.com",
                "rate_limit": 5000
            }
        }
    ]
    
    # Run pipeline
    if await pipeline.deploy_stack(services):
        if await pipeline.run_integration_tests():
            print("🎉 Pipeline completed successfully!")
            return True
        else:
            print("❌ Pipeline failed at integration tests")
            return False
    else:
        print("❌ Pipeline failed at deployment")
        return False

# Run the pipeline
if __name__ == "__main__":
    success = asyncio.run(run_deployment_pipeline())
    exit(0 if success else 1)
```

### Infrastructure Monitoring

```python
"""
Infrastructure Monitoring Example: Monitor MCP server health and performance
"""
import asyncio
import time
from datetime import datetime
from typing import Dict, List
from mcp_template.client import MCPClient

class MCPMonitor:
    """Monitor MCP infrastructure health and performance"""
    
    def __init__(self, alert_threshold: float = 5.0):
        self.alert_threshold = alert_threshold  # seconds
        self.metrics: Dict[str, List] = {}
    
    async def monitor_services(self, duration: int = 300, interval: int = 30):
        """Monitor services for specified duration"""
        async with MCPClient() as client:
            print(f"🔍 Starting monitoring for {duration}s (interval: {interval}s)")
            
            end_time = time.time() + duration
            
            while time.time() < end_time:
                await self._collect_metrics(client)
                await self._check_alerts(client)
                await asyncio.sleep(interval)
            
            await self._generate_report()
    
    async def _collect_metrics(self, client: MCPClient):
        """Collect performance metrics from all services"""
        timestamp = datetime.now()
        servers = client.list_servers()
        
        for server in servers:
            server_id = server["id"]
            template = server["template"]
            
            if server_id not in self.metrics:
                self.metrics[server_id] = []
            
            # Health check with timing
            start_time = time.time()
            try:
                tools = await client.list_tools(template)
                
                if tools:
                    # Test tool response time
                    test_tool = tools[0]
                    tool_start = time.time()
                    result = await client.call_tool(template, test_tool["name"], {})
                    tool_duration = time.time() - tool_start
                    
                    health_status = "healthy" if result["success"] else "degraded"
                else:
                    tool_duration = None
                    health_status = "no_tools"
                
                response_time = time.time() - start_time
                
            except Exception as e:
                response_time = time.time() - start_time
                tool_duration = None
                health_status = "error"
                print(f"⚠️  Health check failed for {server_id}: {e}")
            
            # Record metrics
            metric = {
                "timestamp": timestamp,
                "server_id": server_id,
                "template": template,
                "status": server["status"],
                "health_status": health_status,
                "response_time": response_time,
                "tool_duration": tool_duration
            }
            
            self.metrics[server_id].append(metric)
            
            # Log performance
            if response_time > self.alert_threshold:
                print(f"🐌 Slow response from {server_id}: {response_time:.2f}s")
    
    async def _check_alerts(self, client: MCPClient):
        """Check for alert conditions"""
        servers = client.list_servers()
        
        # Check for failed servers
        failed_servers = [s for s in servers if s["status"] != "running"]
        if failed_servers:
            print(f"🚨 ALERT: {len(failed_servers)} servers not running:")
            for server in failed_servers:
                print(f"  - {server['name']} ({server['template']}): {server['status']}")
        
        # Check for performance degradation
        for server_id, metrics in self.metrics.items():
            if len(metrics) >= 3:
                recent_metrics = metrics[-3:]
                avg_response_time = sum(m["response_time"] for m in recent_metrics) / 3
                
                if avg_response_time > self.alert_threshold:
                    server_name = recent_metrics[-1]["template"]
                    print(f"🚨 ALERT: High response time for {server_name}: {avg_response_time:.2f}s")
    
    async def _generate_report(self):
        """Generate monitoring report"""
        print("\n📊 MONITORING REPORT")
        print("=" * 50)
        
        for server_id, metrics in self.metrics.items():
            if not metrics:
                continue
            
            template = metrics[0]["template"]
            print(f"\n🖥️  Server: {template} ({server_id})")
            
            # Calculate statistics
            response_times = [m["response_time"] for m in metrics]
            tool_durations = [m["tool_duration"] for m in metrics if m["tool_duration"]]
            
            print(f"   Checks: {len(metrics)}")
            print(f"   Avg Response Time: {sum(response_times)/len(response_times):.2f}s")
            print(f"   Max Response Time: {max(response_times):.2f}s")
            
            if tool_durations:
                print(f"   Avg Tool Duration: {sum(tool_durations)/len(tool_durations):.2f}s")
            
            # Health status distribution
            health_counts = {}
            for metric in metrics:
                status = metric["health_status"]
                health_counts[status] = health_counts.get(status, 0) + 1
            
            print(f"   Health Distribution: {health_counts}")

# Usage
async def run_monitoring():
    monitor = MCPMonitor(alert_threshold=3.0)
    await monitor.monitor_services(duration=600, interval=30)  # 10 minutes

asyncio.run(run_monitoring())
```

## Data Processing Workflows

### ETL Pipeline with MCP Tools

```python
"""
ETL Pipeline Example: Extract, transform, and load data using MCP tools
"""
import asyncio
import json
from typing import List, Dict, Any
from mcp_template.client import MCPClient

class MCPETLPipeline:
    """ETL pipeline using MCP tools for data processing"""
    
    def __init__(self):
        self.processed_records = 0
        self.failed_records = 0
        self.errors = []
    
    async def run_pipeline(self, source_config: Dict, transform_config: Dict, 
                          destination_config: Dict) -> Dict:
        """Run complete ETL pipeline"""
        async with MCPClient() as client:
            print("🔄 Starting ETL Pipeline")
            
            # Setup services
            await self._setup_services(client, source_config, destination_config)
            
            try:
                # Extract data
                raw_data = await self._extract_data(client, source_config)
                print(f"📥 Extracted {len(raw_data)} records")
                
                # Transform data
                transformed_data = await self._transform_data(client, raw_data, transform_config)
                print(f"🔄 Transformed {len(transformed_data)} records")
                
                # Load data
                load_result = await self._load_data(client, transformed_data, destination_config)
                print(f"📤 Loaded {load_result['loaded']} records")
                
                return {
                    "success": True,
                    "extracted": len(raw_data),
                    "transformed": len(transformed_data), 
                    "loaded": load_result["loaded"],
                    "errors": self.errors
                }
                
            except Exception as e:
                print(f"❌ Pipeline failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "processed": self.processed_records,
                    "failed": self.failed_records,
                    "errors": self.errors
                }
    
    async def _setup_services(self, client: MCPClient, source_config: Dict, dest_config: Dict):
        """Setup required MCP services"""
        services = [
            ("filesystem", {"allowed_dirs": ["/tmp/etl", source_config.get("data_dir", "/data")]}),
            ("github", {"api_endpoint": "https://api.github.com"}) if source_config.get("source") == "github" else None
        ]
        
        for service in services:
            if service:
                template, config = service
                result = await client.start_server(template, config)
                if not result["success"]:
                    raise Exception(f"Failed to start {template}: {result['error']}")
                print(f"✅ Started {template} service")
    
    async def _extract_data(self, client: MCPClient, config: Dict) -> List[Dict]:
        """Extract data from source"""
        source_type = config.get("source", "filesystem")
        
        if source_type == "filesystem":
            return await self._extract_from_filesystem(client, config)
        elif source_type == "github":
            return await self._extract_from_github(client, config)
        else:
            raise Exception(f"Unsupported source type: {source_type}")
    
    async def _extract_from_filesystem(self, client: MCPClient, config: Dict) -> List[Dict]:
        """Extract data from filesystem"""
        file_path = config["file_path"]
        
        result = await client.call_tool("filesystem", "read_file", {
            "path": file_path
        })
        
        if not result["success"]:
            raise Exception(f"Failed to read file {file_path}: {result['error']}")
        
        content = result["output"]
        
        # Parse based on file type
        if file_path.endswith(".json"):
            return json.loads(content)
        elif file_path.endswith(".csv"):
            # Simple CSV parsing (in real scenario, use proper CSV parser)
            lines = content.strip().split('\n')
            headers = lines[0].split(',')
            return [dict(zip(headers, line.split(','))) for line in lines[1:]]
        else:
            # Line-by-line text processing
            return [{"line": line, "line_number": i+1} for i, line in enumerate(content.split('\n'))]
    
    async def _extract_from_github(self, client: MCPClient, config: Dict) -> List[Dict]:
        """Extract data from GitHub"""
        query = config["query"]
        
        result = await client.call_tool("github", "search_repositories", {
            "query": query,
            "per_page": config.get("limit", 100)
        })
        
        if not result["success"]:
            raise Exception(f"GitHub search failed: {result['error']}")
        
        return result["output"]
    
    async def _transform_data(self, client: MCPClient, data: List[Dict], config: Dict) -> List[Dict]:
        """Transform extracted data"""
        transformed = []
        transformations = config.get("transformations", [])
        
        for record in data:
            try:
                transformed_record = record.copy()
                
                # Apply transformations
                for transform in transformations:
                    transformed_record = await self._apply_transformation(
                        client, transformed_record, transform
                    )
                
                transformed.append(transformed_record)
                self.processed_records += 1
                
            except Exception as e:
                self.failed_records += 1
                self.errors.append(f"Transform error for record {self.processed_records}: {e}")
                print(f"⚠️  Transform failed for record: {e}")
        
        return transformed
    
    async def _apply_transformation(self, client: MCPClient, record: Dict, transform: Dict) -> Dict:
        """Apply a single transformation to a record"""
        transform_type = transform["type"]
        
        if transform_type == "add_field":
            record[transform["field"]] = transform["value"]
            
        elif transform_type == "rename_field":
            if transform["from"] in record:
                record[transform["to"]] = record.pop(transform["from"])
                
        elif transform_type == "filter_field":
            # Keep only specified fields
            keep_fields = transform["fields"]
            record = {k: v for k, v in record.items() if k in keep_fields}
            
        elif transform_type == "format_date":
            # Format date field
            from datetime import datetime
            field = transform["field"]
            if field in record:
                # Simple date formatting example
                record[field] = datetime.now().isoformat()
                
        elif transform_type == "enrich_github":
            # Enrich GitHub data with additional details
            if "owner" in record and "name" in record:
                detail_result = await client.call_tool("github", "get_repository", {
                    "owner": record["owner"],
                    "repo": record["name"]
                })
                
                if detail_result["success"]:
                    repo_details = detail_result["output"]
                    record.update({
                        "detailed_description": repo_details.get("description"),
                        "topics": repo_details.get("topics", []),
                        "license": repo_details.get("license", {}).get("name")
                    })
        
        return record
    
    async def _load_data(self, client: MCPClient, data: List[Dict], config: Dict) -> Dict:
        """Load transformed data to destination"""
        destination_type = config.get("destination", "filesystem")
        
        if destination_type == "filesystem":
            return await self._load_to_filesystem(client, data, config)
        else:
            raise Exception(f"Unsupported destination type: {destination_type}")
    
    async def _load_to_filesystem(self, client: MCPClient, data: List[Dict], config: Dict) -> Dict:
        """Load data to filesystem"""
        output_path = config["output_path"]
        output_format = config.get("format", "json")
        
        if output_format == "json":
            content = json.dumps(data, indent=2)
        elif output_format == "csv":
            # Simple CSV output
            if data:
                headers = list(data[0].keys())
                lines = [','.join(headers)]
                for record in data:
                    line = ','.join(str(record.get(h, '')) for h in headers)
                    lines.append(line)
                content = '\n'.join(lines)
            else:
                content = ""
        else:
            raise Exception(f"Unsupported output format: {output_format}")
        
        result = await client.call_tool("filesystem", "write_file", {
            "path": output_path,
            "content": content
        })
        
        if not result["success"]:
            raise Exception(f"Failed to write output file: {result['error']}")
        
        return {"loaded": len(data)}

# Usage example
async def run_etl_example():
    """Run ETL pipeline example"""
    pipeline = MCPETLPipeline()
    
    # Configuration
    source_config = {
        "source": "github",
        "query": "machine learning python",
        "limit": 50
    }
    
    transform_config = {
        "transformations": [
            {"type": "add_field", "field": "processed_at", "value": "2024-01-01"},
            {"type": "filter_field", "fields": ["name", "owner", "description", "stars", "language"]},
            {"type": "enrich_github"}
        ]
    }
    
    destination_config = {
        "destination": "filesystem",
        "output_path": "/tmp/etl/processed_repos.json",
        "format": "json"
    }
    
    # Run pipeline
    result = await pipeline.run_pipeline(source_config, transform_config, destination_config)
    
    print("\n📊 ETL PIPELINE RESULTS")
    print("=" * 40)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Extracted: {result['extracted']} records")
        print(f"Transformed: {result['transformed']} records") 
        print(f"Loaded: {result['loaded']} records")
    else:
        print(f"Error: {result['error']}")
    
    if result.get('errors'):
        print(f"Errors: {len(result['errors'])}")
        for error in result['errors'][:5]:  # Show first 5 errors
            print(f"  - {error}")

# Run the example
asyncio.run(run_etl_example())
```

## Multi-Service Orchestration

### Microservices Coordination

```python
"""
Microservices Orchestration Example: Coordinate multiple MCP services for complex workflows
"""
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from mcp_template.client import MCPClient

@dataclass
class ServiceStep:
    """Represents a step in service orchestration"""
    service: str
    tool: str
    params: Dict[str, Any]
    depends_on: Optional[List[str]] = None
    retry_count: int = 3
    timeout: float = 30.0

class MCPOrchestrator:
    """Orchestrate complex workflows across multiple MCP services"""
    
    def __init__(self):
        self.step_results: Dict[str, Any] = {}
        self.service_deployments: Dict[str, str] = {}
    
    async def execute_workflow(self, workflow_definition: Dict) -> Dict:
        """Execute a complete workflow with multiple coordinated steps"""
        async with MCPClient() as client:
            workflow_name = workflow_definition["name"]
            steps = workflow_definition["steps"]
            services = workflow_definition.get("services", {})
            
            print(f"🚀 Starting workflow: {workflow_name}")
            
            try:
                # Setup required services
                await self._setup_services(client, services)
                
                # Execute workflow steps
                for step_name, step_config in steps.items():
                    step = ServiceStep(
                        service=step_config["service"],
                        tool=step_config["tool"],
                        params=step_config.get("params", {}),
                        depends_on=step_config.get("depends_on", []),
                        retry_count=step_config.get("retry_count", 3),
                        timeout=step_config.get("timeout", 30.0)
                    )
                    
                    print(f"🔄 Executing step: {step_name}")
                    result = await self._execute_step(client, step_name, step)
                    
                    if not result["success"]:
                        raise Exception(f"Step {step_name} failed: {result['error']}")
                    
                    self.step_results[step_name] = result["output"]
                    print(f"✅ Step {step_name} completed")
                
                print(f"🎉 Workflow {workflow_name} completed successfully")
                return {
                    "success": True,
                    "workflow": workflow_name,
                    "results": self.step_results
                }
                
            except Exception as e:
                print(f"❌ Workflow {workflow_name} failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "partial_results": self.step_results
                }
            
            finally:
                await self._cleanup_services(client)
    
    async def _setup_services(self, client: MCPClient, services: Dict):
        """Setup all required services for the workflow"""
        for service_name, config in services.items():
            print(f"🚀 Starting service: {service_name}")
            result = await client.start_server(service_name, config)
            
            if result["success"]:
                self.service_deployments[service_name] = result["deployment_id"]
                print(f"✅ Service {service_name} ready")
            else:
                raise Exception(f"Failed to start service {service_name}: {result['error']}")
    
    async def _execute_step(self, client: MCPClient, step_name: str, step: ServiceStep) -> Dict:
        """Execute a single workflow step with dependencies and retries"""
        # Wait for dependencies
        await self._wait_for_dependencies(step.depends_on)
        
        # Resolve parameters with previous step results
        resolved_params = self._resolve_parameters(step.params)
        
        # Execute with retry logic
        for attempt in range(step.retry_count):
            try:
                result = await asyncio.wait_for(
                    client.call_tool(step.service, step.tool, resolved_params),
                    timeout=step.timeout
                )
                
                if result["success"]:
                    return result
                else:
                    print(f"⚠️  Step {step_name} attempt {attempt + 1} failed: {result['error']}")
                    if attempt < step.retry_count - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except asyncio.TimeoutError:
                print(f"⏱️  Step {step_name} attempt {attempt + 1} timed out")
                if attempt < step.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
            
            except Exception as e:
                print(f"❌ Step {step_name} attempt {attempt + 1} error: {e}")
                if attempt < step.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return {"success": False, "error": f"Step failed after {step.retry_count} attempts"}
    
    async def _wait_for_dependencies(self, dependencies: Optional[List[str]]):
        """Wait for dependent steps to complete"""
        if not dependencies:
            return
        
        max_wait = 300  # 5 minutes max wait
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < max_wait:
            if all(dep in self.step_results for dep in dependencies):
                return
            await asyncio.sleep(1)
        
        missing = [dep for dep in dependencies if dep not in self.step_results]
        raise Exception(f"Dependencies not satisfied after {max_wait}s: {missing}")
    
    def _resolve_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameters with references to previous step results"""
        resolved = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("${"):
                # Parameter reference: ${step_name.field}
                ref = value[2:-1]  # Remove ${ and }
                if "." in ref:
                    step_name, field = ref.split(".", 1)
                    if step_name in self.step_results:
                        step_result = self.step_results[step_name]
                        resolved[key] = self._get_nested_value(step_result, field)
                    else:
                        raise Exception(f"Referenced step not found: {step_name}")
                else:
                    if ref in self.step_results:
                        resolved[key] = self.step_results[ref]
                    else:
                        raise Exception(f"Referenced step not found: {ref}")
            else:
                resolved[key] = value
        
        return resolved
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get nested value from data using dot notation"""
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    raise Exception(f"List index out of range: {index}")
            else:
                raise Exception(f"Path not found: {path}")
        
        return current
    
    async def _cleanup_services(self, client: MCPClient):
        """Clean up all deployed services"""
        for service_name, deployment_id in self.service_deployments.items():
            try:
                await client.stop_server(deployment_id)
                print(f"🧹 Cleaned up service: {service_name}")
            except Exception as e:
                print(f"⚠️  Failed to cleanup {service_name}: {e}")

# Complex workflow example
async def run_content_analysis_workflow():
    """Complex workflow: GitHub repository analysis and report generation"""
    orchestrator = MCPOrchestrator()
    
    workflow = {
        "name": "Repository Content Analysis",
        "services": {
            "github": {
                "api_endpoint": "https://api.github.com",
                "rate_limit": 5000
            },
            "filesystem": {
                "allowed_dirs": ["/tmp/analysis"],
                "read_only": False
            }
        },
        "steps": {
            "search_repositories": {
                "service": "github",
                "tool": "search_repositories",
                "params": {
                    "query": "machine learning python",
                    "sort": "stars",
                    "per_page": 10
                }
            },
            "analyze_top_repo": {
                "service": "github", 
                "tool": "get_repository",
                "params": {
                    "owner": "${search_repositories.0.owner}",
                    "repo": "${search_repositories.0.name}"
                },
                "depends_on": ["search_repositories"]
            },
            "get_repo_contents": {
                "service": "github",
                "tool": "list_repository_contents",
                "params": {
                    "owner": "${search_repositories.0.owner}",
                    "repo": "${search_repositories.0.name}",
                    "path": ""
                },
                "depends_on": ["search_repositories"]
            },
            "generate_report": {
                "service": "filesystem",
                "tool": "write_file",
                "params": {
                    "path": "/tmp/analysis/repository_analysis.json",
                    "content": {
                        "repository": "${analyze_top_repo}",
                        "contents": "${get_repo_contents}",
                        "analysis_date": "2024-01-01",
                        "search_results": "${search_repositories}"
                    }
                },
                "depends_on": ["analyze_top_repo", "get_repo_contents"]
            }
        }
    }
    
    result = await orchestrator.execute_workflow(workflow)
    
    print("\n📊 WORKFLOW RESULTS")
    print("=" * 40)
    print(f"Success: {result['success']}")
    
    if result['success']:
        print("Completed steps:")
        for step_name in result['results'].keys():
            print(f"  ✅ {step_name}")
        print(f"\n📄 Analysis report generated at: /tmp/analysis/repository_analysis.json")
    else:
        print(f"Error: {result['error']}")
        if result.get('partial_results'):
            print("Partial results available for:")
            for step_name in result['partial_results'].keys():
                print(f"  ✅ {step_name}")

# Run the complex workflow
asyncio.run(run_content_analysis_workflow())
```

These examples demonstrate comprehensive usage patterns of MCPClient for real-world scenarios including:

1. **DevOps Automation**: Complete CI/CD pipeline with deployment, health checks, and integration testing
2. **Infrastructure Monitoring**: Real-time monitoring with metrics collection and alerting
3. **Data Processing**: ETL pipelines with extract, transform, and load operations
4. **Service Orchestration**: Complex workflows with dependencies, retries, and parameter resolution

Each example shows production-ready patterns with proper error handling, resource cleanup, and monitoring capabilities.
