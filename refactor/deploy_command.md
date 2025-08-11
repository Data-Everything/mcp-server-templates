# Command Documentation: deploy

## Command Name
`deploy` - Deploy a template

## Purpose
Deploys an MCP server template with specified configuration, creating a running container/service that can be connected to by MCP clients. This is the core functionality for getting templates up and running.

## Expected Output

### CLI Output
```
╭─────────────────────────────────────────────────────────────────── Deployment ───────────────────────────────────────────────────────────────────╮
│ 🚀 Deploying MCP Template: demo                                                                                                                      │
╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
⠋ Deploying demo...╭──────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 🎉 Deployment Complete ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ ✅ Successfully deployed demo!                                                                                                                       │
│                                                                                                                                                      │
│ 📋 Details:                                                                                                                                          │
│ • Container: demo-20240811-123456-abc123                                                                                                            │
│ • Image: dataeverything/mcp-demo:latest                                                                                                             │
│ • Status: running                                                                                                                                    │
│                                                                                                                                                      │
│ 🔧 MCP Configuration:                                                                                                                                │
│ Config saved to: ~/.mcp/demo.json                                                                                                                   │
│                                                                                                                                                      │
│ 💡 Management:                                                                                                                                       │
│ • View logs: mcpt logs demo                                                                                                                         │
│ • Stop: mcpt stop demo                                                                                                                              │
│ • Shell: mcpt shell demo                                                                                                                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

### MCPClient Output
```python
{
    "deployment_id": "demo-20240811-123456-abc123",
    "template": "demo",
    "status": "running",
    "container_id": "abc123def456",
    "image": "dataeverything/mcp-demo:latest",
    "ports": {"7071": 7071},
    "config": {
        "hello_from": "MCP Platform",
        "debug_mode": False
    },
    "mcp_config_path": "~/.mcp/demo.json",
    "transport": "http",
    "endpoint": "http://localhost:7071"
}
```

## Current CLI Flow

### CLI Implementation (__init__.py → cli.py)
1. Parse `deploy` command with multiple arguments:
   - `template` (required)
   - `--name`, `--data-dir`, `--config-dir`
   - `--env` (multiple), `--config` (multiple), `--override` (multiple)
   - `--transport`, `--port`, `--config-file`
   - `--show-config`, `--no-pull`

2. Handle enhanced CLI through `handle_enhanced_cli_commands()`:
   - Split command args for env, config, override values
   - Call `enhanced_cli.deploy_with_transport()`

3. Enhanced CLI deployment:
   - Template validation and discovery
   - Configuration processing and merging
   - Docker network setup
   - Container deployment with proper transport setup
   - Rich console output with progress indicators
   - Error handling and rollback

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.start_server(template_id, config, name, timeout)`
2. MCPClient internally:
   - Uses ServerManager for deployment orchestration
   - Calls backend deployment service
   - Returns structured deployment information
   - No console output - just data

## Common Functionality

### Shared Core Logic (To Extract)
1. **Template Validation**:
   - Check template exists
   - Validate template structure
   - Load template metadata and configuration schema

2. **Configuration Processing**:
   - Merge multiple config sources (file, env, CLI args, overrides)
   - Apply template defaults
   - Validate against config schema
   - Handle double-underscore notation for nested configs
   - Environment variable mapping

3. **Image Management**:
   - Docker image pull/validation
   - Image tag resolution
   - Registry authentication

4. **Deployment Orchestration**:
   - Container/service creation
   - Port mapping and networking
   - Volume mounting
   - Environment variable setup
   - Health checks and readiness

5. **Transport Configuration**:
   - HTTP vs stdio transport setup
   - Port allocation and binding
   - Protocol-specific configuration

6. **MCP Configuration Generation**:
   - Generate MCP client config files
   - Handle different transport protocols
   - Store configuration in appropriate locations

### Container Management:
   - Container lifecycle (create, start, monitor)
   - Resource allocation
   - Logging setup
   - Error handling and cleanup

## Specific Functionality

### CLI-Specific Logic
1. **Argument Parsing and Validation**:
   - Command line argument processing
   - Multi-value argument handling (env, config, override)
   - Flag interpretation and defaults

2. **Interactive Features**:
   - Progress indicators and spinners
   - Rich console output with panels and colors
   - Error message formatting
   - Help and guidance display

3. **Configuration Display**:
   - `--show-config` option handling
   - Configuration option enumeration
   - Help text and examples

### MCPClient-Specific Logic
1. **Programmatic Interface**:
   - Method signature design
   - Return value structure
   - Exception handling strategy

2. **Async Support**:
   - Async deployment operations
   - Background task management
   - Timeout handling

3. **Connection Management**:
   - Track active deployments
   - Connection pooling
   - Resource cleanup

## Proposed Refactor Plan

### New Common Module: `mcp_template/common/deployment_manager.py`
```python
class DeploymentManager:
    def __init__(self, backend_type: str = "docker"):
        self.backend = get_backend(backend_type)
        self.config_processor = ConfigProcessor()
        self.template_manager = TemplateManager()

    def deploy_template(self,
                       template_id: str,
                       config_sources: Dict[str, Any],
                       deployment_options: DeploymentOptions) -> DeploymentResult:
        """Core deployment logic with all configuration processing"""

    def validate_deployment_config(self, template_id: str, config: Dict) -> ValidationResult:
        """Validate deployment configuration against template schema"""

    def prepare_deployment(self, template_id: str, config: Dict) -> DeploymentSpec:
        """Prepare deployment specification"""

    def execute_deployment(self, spec: DeploymentSpec) -> DeploymentResult:
        """Execute the actual deployment"""
```

### New Common Module: `mcp_template/common/config_manager.py`
```python
class ConfigManager:
    def merge_config_sources(self,
                           template_config: Dict,
                           config_file: Optional[str],
                           env_vars: Dict[str, str],
                           config_values: Dict[str, str],
                           override_values: Dict[str, str]) -> Dict[str, Any]:
        """Merge all configuration sources with proper precedence"""

    def validate_config(self, config: Dict, schema: Dict) -> ValidationResult:
        """Validate configuration against template schema"""

    def process_overrides(self, config: Dict, overrides: Dict[str, str]) -> Dict:
        """Apply template overrides with double-underscore notation"""
```

### Updated CLI Logic
```python
def handle_deploy_command(args):
    # Parse CLI arguments into structured config
    config_sources = {
        'config_file': args.config_file,
        'env_vars': split_command_args(args.env or []),
        'config_values': split_command_args(args.config or []),
        'override_values': split_command_args(args.override or [])
    }

    deployment_options = DeploymentOptions(
        name=args.name,
        transport=args.transport,
        port=args.port,
        data_dir=args.data_dir,
        config_dir=args.config_dir,
        pull_image=not args.no_pull
    )

    manager = DeploymentManager()
    result = manager.deploy_template(args.template, config_sources, deployment_options)

    # CLI-specific formatting and display
    format_and_display_deployment_result(result)
```

### Updated MCPClient Logic
```python
def start_server(self, template_id: str, config: Dict = None, name: str = None, timeout: int = None) -> Dict:
    config_sources = {'config_values': config or {}}
    deployment_options = DeploymentOptions(name=name, timeout=timeout)

    manager = DeploymentManager(self.backend_type)
    result = manager.deploy_template(template_id, config_sources, deployment_options)

    return result.to_dict()
```

## Implementation Plan

1. **Create DeploymentManager class** in `mcp_template/common/deployment_manager.py`
2. **Create ConfigManager class** in `mcp_template/common/config_manager.py`
3. **Extract config processing logic** from ConfigProcessor and deployer
4. **Move deployment orchestration** from MCPDeployer to DeploymentManager
5. **Update CLI** to use common managers with display layer
6. **Update MCPClient** to use common managers directly
7. **Remove duplicate deployment logic**

## Unit Test Plan

### Tests Location: `tests/test_common/test_deployment_manager.py`, `tests/test_common/test_config_manager.py`

### Test Categories:
```python
@pytest.mark.unit
class TestDeploymentManager:
    def test_deploy_template_basic()
    def test_deploy_template_with_custom_config()
    def test_deploy_template_with_overrides()
    def test_validate_deployment_config()
    def test_prepare_deployment()
    def test_execute_deployment()

@pytest.mark.unit
class TestConfigManager:
    def test_merge_config_sources_precedence()
    def test_validate_config_schema()
    def test_process_overrides_nested()
    def test_environment_variable_mapping()

@pytest.mark.integration
class TestDeploymentIntegration:
    def test_full_deployment_flow()
    def test_deployment_with_real_backend()
    def test_deployment_error_handling()
```

### Mock Requirements:
- Mock backend services (Docker, Kubernetes)
- Mock template discovery
- Mock file system for config files
- Mock container runtime operations
- Mock network operations

## Dependencies / Risks

### Dependencies:
- Backend deployment services
- Template discovery and validation
- Configuration schema processing
- Container runtime (Docker/Kubernetes)
- Network configuration
- File system access

### Risks:
1. **Complex configuration merging logic** - Multiple precedence rules
2. **Backend-specific deployment differences** - Docker vs Kubernetes vs Mock
3. **Transport protocol complexity** - HTTP vs stdio configuration
4. **Error handling during deployment** - Partial failures and rollback
5. **Resource conflicts** - Port conflicts, name conflicts
6. **Performance impact** - Template validation and image pulls

### Mitigation:
1. Comprehensive config merging tests with all source combinations
2. Abstract backend differences through common interface
3. Transport configuration abstraction layer
4. Atomic deployment operations with proper cleanup
5. Resource conflict detection and resolution
6. Async operations for performance-critical tasks
7. Integration tests with real backends
