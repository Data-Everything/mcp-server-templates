# Command Documentation: logs

## Command Name
`logs` - View deployment logs

## Purpose
Retrieves and displays logs from running MCP server deployments, providing real-time monitoring and debugging capabilities for deployed templates.

## Expected Output

### CLI Output
```
📋 Logs for deployment: demo (last 100 lines)

2024-08-11 10:30:01 [INFO] MCP Server starting...
2024-08-11 10:30:01 [INFO] Loading configuration from /config/server.json
2024-08-11 10:30:02 [INFO] Initializing FastMCP server
2024-08-11 10:30:02 [INFO] Registering tools: say_hello, echo_message
2024-08-11 10:30:03 [INFO] Server listening on port 7071
2024-08-11 10:30:03 [INFO] MCP Server ready for connections

💡 Use 'mcpt logs demo --follow' to stream logs in real-time
💡 Use 'mcpt logs demo --lines 500' to see more history
```

### MCPClient Output
```python
{
    "logs": "2024-08-11 10:30:01 [INFO] MCP Server starting...\n...",
    "deployment_id": "demo-deployment-123",
    "timestamp": "2024-08-11T10:30:03Z",
    "lines_returned": 100,
    "total_lines_available": 247
}
```

## Current CLI Flow

### CLI Implementation (cli.py via __init__.py)
1. Enhanced CLI handles `logs` command in main CLI dispatcher
2. Argument parsing supports:
   - `template` (positional) - template name
   - `--name` - custom deployment name
   - `--lines` - number of log lines to retrieve (default 100)
   - `--follow` - stream logs in real-time
3. Calls `deployer.logs()` with parsed arguments

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.get_server_logs(deployment_id, lines=100)`
2. MCPClient internally:
   - Uses ServerManager for log operations
   - Calls `server_manager.get_server_logs(deployment_id, lines)`
   - Returns log content as string
3. ServerManager uses DeploymentManager to get deployment status with logs

## Common Functionality

### Shared Core Logic (To Extract)
1. **Log Retrieval**:
   - Connect to deployment backend (Docker/Kubernetes)
   - Retrieve container/pod logs with configurable line limits
   - Handle log streaming for real-time monitoring
   - Parse and format log timestamps

2. **Deployment Resolution**:
   - Find deployment by template name or custom name
   - Handle multiple deployments for same template
   - Validate deployment exists and is accessible

3. **Log Processing**:
   - Filter log levels and content
   - Handle multi-container deployments (aggregate logs)
   - Process log rotation and archival
   - Manage log encoding and character handling

4. **Error Handling**:
   - Handle non-existent deployments
   - Deal with stopped deployments (historical logs)
   - Manage permission and access issues
   - Handle backend connectivity problems

### Performance Optimization:
   - Log caching for frequently accessed deployments
   - Efficient log streaming without overwhelming clients
   - Pagination for large log files

## Specific Functionality

### CLI-Specific Logic
1. **Rich Display**:
   - Syntax highlighting for log levels (INFO, WARN, ERROR)
   - Timestamp formatting and colorization
   - Progress indicators for log retrieval
   - Scrollable output with pagination controls

2. **Interactive Features**:
   - Real-time log streaming with --follow
   - Log level filtering options
   - Search functionality within logs
   - Export logs to file options

3. **User Experience**:
   - Helpful usage examples and tips
   - Clear error messages for missing deployments
   - Keyboard shortcuts for log navigation

### MCPClient-Specific Logic
1. **Programmatic Interface**:
   - Structured log data with metadata
   - Async log streaming capabilities
   - Batch log retrieval for multiple deployments

2. **Integration Features**:
   - Log aggregation across deployments
   - Log parsing and structured extraction
   - Integration with monitoring systems

## Proposed Refactor Plan

### New Common Module: Enhanced `DeploymentManager.get_deployment_logs()`
```python
def get_deployment_logs(self,
                       deployment_id: str,
                       lines: int = 100,
                       follow: bool = False,
                       since: Optional[str] = None,
                       until: Optional[str] = None) -> Dict[str, Any]:
    """Core log retrieval with comprehensive options"""

def stream_deployment_logs(self,
                          deployment_id: str,
                          callback: Callable[[str], None],
                          lines: int = 100) -> None:
    """Real-time log streaming with callback"""

def find_deployment_for_logs(self,
                            template_name: Optional[str] = None,
                            custom_name: Optional[str] = None) -> Optional[str]:
    """Find deployment ID for log operations"""

def aggregate_logs_from_deployments(self,
                                   deployment_ids: List[str],
                                   lines: int = 100) -> Dict[str, Any]:
    """Aggregate logs from multiple deployments"""
```

### New Common Module: `LogFormatter` class
```python
class LogFormatter:
    def format_logs_for_display(self, logs: str, colorize: bool = True) -> str:
        """Format logs for rich CLI display"""

    def parse_log_entries(self, logs: str) -> List[Dict[str, Any]]:
        """Parse logs into structured entries"""

    def filter_logs_by_level(self, logs: str, level: str) -> str:
        """Filter logs by log level"""
```

### Updated CLI Logic
```python
def handle_logs_command(args):
    manager = DeploymentManager()

    # Find deployment
    deployment_id = manager.find_deployment_for_logs(
        template_name=args.template,
        custom_name=getattr(args, 'name', None)
    )

    if not deployment_id:
        show_deployment_not_found_error(args.template)
        return

    # Get logs
    if args.follow:
        stream_logs_with_rich_display(manager, deployment_id)
    else:
        result = manager.get_deployment_logs(deployment_id, lines=args.lines)
        display_logs_with_formatting(result)
```

### Updated MCPClient Logic
```python
def get_server_logs(self, deployment_id: str, lines: int = 100, follow: bool = False) -> Dict[str, Any]:
    manager = DeploymentManager(self.backend_type)
    return manager.get_deployment_logs(deployment_id, lines=lines, follow=follow)

def stream_server_logs(self, deployment_id: str, callback: Callable[[str], None], lines: int = 100) -> None:
    manager = DeploymentManager(self.backend_type)
    return manager.stream_deployment_logs(deployment_id, callback, lines)
```

## Implementation Plan

1. **Enhance DeploymentManager** with comprehensive log operations
2. **Create LogFormatter class** for display formatting
3. **Extract log streaming logic** to common module
4. **Add log aggregation capabilities** for multi-deployment scenarios
5. **Update CLI** to use DeploymentManager with rich log display
6. **Update MCPClient** to use DeploymentManager directly
7. **Remove duplicate log logic** from deployer and server_manager

## Unit Test Plan

### Tests Location: `tests/test_common/test_deployment_manager_logs.py`

### Test Categories:
```python
@pytest.mark.unit
class TestDeploymentManagerLogs:
    def test_get_deployment_logs_success()
    def test_get_deployment_logs_not_found()
    def test_get_deployment_logs_with_limits()
    def test_stream_deployment_logs()
    def test_find_deployment_for_logs()
    def test_aggregate_logs_from_deployments()
    def test_log_filtering_and_formatting()

@pytest.mark.integration
class TestLogsIntegration:
    def test_logs_with_real_deployment()
    def test_log_streaming_integration()
    def test_multi_deployment_log_aggregation()
```

### Test Coverage for LogFormatter:
```python
@pytest.mark.unit
class TestLogFormatter:
    def test_format_logs_for_display()
    def test_parse_log_entries()
    def test_filter_logs_by_level()
    def test_log_colorization()
    def test_timestamp_formatting()
```

### Mock Requirements:
- Mock core DeploymentManager backend operations
- Mock container log retrieval (Docker logs, kubectl logs)
- Mock log streaming and follow operations
- Mock deployment discovery and resolution
- Mock log parsing and formatting

## Dependencies / Risks

### Dependencies:
- Core DeploymentManager for backend operations
- Container runtime APIs (Docker API, Kubernetes API)
- Log streaming libraries and utilities
- Text processing for log formatting
- Real-time streaming infrastructure

### Risks:
1. **Large log volumes** - deployments may have massive log files
2. **Log streaming performance** - real-time streaming may impact performance
3. **Log format variations** - different services may log in different formats
4. **Backend connectivity** - network issues may interrupt log retrieval
5. **Memory usage** - large log retrievals may consume significant memory
6. **Log rotation** - active log rotation may affect streaming

### Mitigation:
1. Implement log pagination and streaming limits
2. Efficient streaming with buffering and backpressure handling
3. Flexible log parsing with configurable formats
4. Robust error handling and retry mechanisms for connectivity
5. Memory-efficient log processing with streaming parsers
6. Smart log rotation detection and handling
7. Caching strategies for frequently accessed logs
