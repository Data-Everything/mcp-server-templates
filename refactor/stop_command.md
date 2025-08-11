# Command Documentation: stop

## Command Name
`stop` - Stop deployed templates

## Purpose
Stops running MCP server deployments, allowing users to gracefully shut down deployed templates either individually by name/ID or in bulk.

## Expected Output

### CLI Output
```
🛑 Stopping deployment: demo
Template: demo

✅ Deployment stopped successfully!

Summary:
  • Stopped: demo-deployment-123
  • Duration: 2.3 seconds
```

### MCPClient Output
```python
{
    "success": True,
    "stopped_deployments": ["demo-deployment-123"],
    "duration": 2.3
}
```

## Current CLI Flow

### CLI Implementation (cli.py via __init__.py)
1. Enhanced CLI handles `stop` command in main CLI dispatcher
2. Argument parsing supports:
   - `template` (positional) - template name to stop
   - `--name` - custom deployment name filter
   - `--all` - stop all deployments (with optional template filter)
3. Validation requires at least one of: template, --name, or --all
4. Calls `deployer.stop()` with parsed arguments

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.stop_server(deployment_id)`
2. MCPClient internally:
   - Uses ServerManager for deployment operations
   - Calls `server_manager.stop_server(deployment_id)`
   - Returns boolean success result
3. ServerManager uses DeploymentManager to actually stop deployment

## Common Functionality

### Shared Core Logic (To Extract)
1. **Deployment Discovery**:
   - List running deployments to find targets
   - Match deployments by template name, custom name, or ID
   - Handle multiple deployment scenarios

2. **Stop Orchestration**:
   - Graceful shutdown procedures
   - Container/service lifecycle management
   - Resource cleanup (volumes, networks, etc.)
   - Timeout handling for unresponsive deployments

3. **Status Tracking**:
   - Monitor stop progress
   - Report stop success/failure
   - Track stop duration and metrics

4. **Error Handling**:
   - Handle non-existent deployments
   - Deal with already stopped deployments
   - Manage partial failures in bulk stops

### Validation Logic:
   - Verify deployment exists before attempting stop
   - Check user permissions for stop operations
   - Validate stop parameters and options

## Specific Functionality

### CLI-Specific Logic
1. **User Interface**:
   - Rich progress indicators during stop operations
   - Colored status messages and confirmations
   - Bulk stop confirmation prompts
   - Summary tables for multiple stops

2. **Argument Processing**:
   - Parse multiple stop target formats
   - Handle --all flag with safety checks
   - Process custom name filters

3. **Interactive Features**:
   - Confirmation prompts for bulk operations
   - Force stop options for unresponsive deployments

### MCPClient-Specific Logic
1. **Programmatic Interface**:
   - Simple boolean return values
   - Structured error information
   - Batch stop operations with detailed results

2. **Integration Friendly**:
   - Async stop operations support
   - Callback mechanisms for long-running stops
   - Detailed stop metadata for monitoring

## Proposed Refactor Plan

### New Common Module: Enhanced `DeploymentManager.stop_deployment()`
```python
def stop_deployment(self, deployment_id: str, timeout: int = 30, force: bool = False) -> Dict[str, Any]:
    """Core stop logic with comprehensive result information"""

def stop_deployments_bulk(self,
                         deployment_filters: List[str],
                         timeout: int = 30,
                         force: bool = False) -> Dict[str, Any]:
    """Bulk stop operations with detailed results"""

def find_deployments_by_criteria(self,
                                template_name: Optional[str] = None,
                                custom_name: Optional[str] = None,
                                deployment_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Find deployments matching stop criteria"""
```

### Updated CLI Logic
```python
def handle_stop_command(args):
    manager = DeploymentManager()

    # Find target deployments
    if args.all:
        targets = manager.find_deployments_by_criteria(template_name=args.template)
    elif args.name:
        targets = manager.find_deployments_by_criteria(custom_name=args.name)
    else:
        targets = manager.find_deployments_by_criteria(template_name=args.template)

    # Confirm bulk operations
    if len(targets) > 1:
        confirm_bulk_stop(targets)

    # Execute stops
    if len(targets) == 1:
        result = manager.stop_deployment(targets[0]["id"])
        display_stop_result(result)
    else:
        result = manager.stop_deployments_bulk([t["id"] for t in targets])
        display_bulk_stop_results(result)
```

### Updated MCPClient Logic
```python
def stop_server(self, deployment_id: str, timeout: int = 30) -> Dict[str, Any]:
    manager = DeploymentManager(self.backend_type)
    return manager.stop_deployment(deployment_id, timeout)

def stop_servers_by_template(self, template_name: str) -> Dict[str, Any]:
    manager = DeploymentManager(self.backend_type)
    targets = manager.find_deployments_by_criteria(template_name=template_name)
    return manager.stop_deployments_bulk([t["id"] for t in targets])
```

## Implementation Plan

1. **Enhance DeploymentManager** with advanced stop operations
2. **Extract deployment discovery logic** to common module
3. **Move stop orchestration** to DeploymentManager
4. **Add bulk stop capabilities** with proper error handling
5. **Update CLI** to use DeploymentManager with rich UI
6. **Update MCPClient** to use DeploymentManager directly
7. **Remove duplicate stop logic** from deployer and server_manager

## Unit Test Plan

### Tests Location: `tests/test_common/test_deployment_manager.py`

### Test Categories:
```python
@pytest.mark.unit
class TestDeploymentManagerStop:
    def test_stop_deployment_success()
    def test_stop_deployment_not_found()
    def test_stop_deployment_timeout()
    def test_stop_deployment_force()
    def test_stop_deployments_bulk()
    def test_find_deployments_by_criteria()
    def test_stop_validation()

@pytest.mark.integration
class TestStopIntegration:
    def test_stop_with_real_deployment()
    def test_bulk_stop_operations()
    def test_stop_error_recovery()
```

### Mock Requirements:
- Mock core DeploymentManager for backend operations
- Mock deployment listing and status calls
- Mock container/service stop operations
- Mock timeout scenarios
- Mock network cleanup operations

## Dependencies / Risks

### Dependencies:
- Core DeploymentManager for backend operations
- Container runtime (Docker/Kubernetes) for actual stops
- Network and volume cleanup utilities
- Deployment status monitoring

### Risks:
1. **Graceful shutdown failures** - containers may not respond to stop signals
2. **Resource cleanup issues** - volumes or networks may remain after stop
3. **Partial failure handling** - some deployments in bulk may fail
4. **Timeout management** - long-running stops may exceed timeouts
5. **Concurrent stop conflicts** - multiple stop requests for same deployment

### Mitigation:
1. Implement force stop with SIGKILL as fallback
2. Comprehensive resource cleanup with verification
3. Detailed error reporting for each deployment in bulk operations
4. Configurable timeouts with progress monitoring
5. Deployment locking to prevent concurrent operations
6. Proper error handling and rollback procedures
