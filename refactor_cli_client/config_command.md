# Command Documentation: config

## Command Name
`config` - Manage template configurations

## Purpose
Create, view, edit, and validate MCP server template configurations, providing a centralized interface for configuration management across templates.

## Expected Output

### CLI Output
```
🔧 Configuration Management for Template: demo

Available configuration files:
┌─────────────────┬──────────────┬──────────────────────────┬─────────────┐
│ Config File     │ Type         │ Last Modified            │ Status      │
├─────────────────┼──────────────┼──────────────────────────┼─────────────┤
│ server.json     │ Server       │ 2024-08-11 10:30:01 UTC │ ✅ Valid    │
│ client.json     │ Client       │ 2024-08-11 10:25:30 UTC │ ✅ Valid    │
│ deployment.yaml │ Deployment   │ 2024-08-11 10:20:15 UTC │ ⚠️ Warning  │
│ docker.env      │ Environment  │ 2024-08-11 10:15:45 UTC │ ✅ Valid    │
└─────────────────┴──────────────┴──────────────────────────┴─────────────┘

💡 Use 'mcpt config demo --edit server.json' to edit configuration
💡 Use 'mcpt config demo --validate' to check all configurations
💡 Use 'mcpt config demo --export' to export configuration package
```

### MCPClient Output
```python
{
    "template": "demo",
    "configurations": [
        {
            "file": "server.json",
            "type": "server",
            "path": "/templates/demo/config/server.json",
            "last_modified": "2024-08-11T10:30:01Z",
            "status": "valid",
            "content": {...}
        }
    ],
    "validation_result": {
        "valid": True,
        "warnings": ["Port 7071 is already in use"],
        "errors": []
    }
}
```

## Current CLI Flow

### CLI Implementation (cli.py via __init__.py)
1. Enhanced CLI handles `config` command in main CLI dispatcher
2. Argument parsing supports:
   - `template` (positional) - template name
   - `--edit <file>` - edit specific configuration file
   - `--validate` - validate all configurations
   - `--export` - export configuration package
   - `--import <path>` - import configuration package
   - `--reset` - reset to default configuration
3. Calls appropriate configuration methods based on flags

## Current MCPClient Flow

### MCPClient Implementation (client.py)
1. Call `client.get_template_config(template_name)`
2. MCPClient internally:
   - Uses TemplateManager for configuration operations
   - Calls `template_manager.get_template_configuration(template_name)`
   - Returns configuration data with validation status
3. Configuration validation uses internal template validation

## Common Functionality

### Shared Core Logic (To Extract)
1. **Configuration Discovery**:
   - Scan template directory for configuration files
   - Identify configuration types (server, client, deployment, environment)
   - Parse configuration metadata and schema
   - Track configuration file relationships

2. **Configuration Validation**:
   - Schema validation for each configuration type
   - Cross-configuration consistency checks
   - Environment variable resolution and validation
   - Port and resource conflict detection

3. **Configuration Editing**:
   - Safe configuration file modification
   - Backup and rollback capabilities
   - Configuration merging and templating
   - Environment-specific configuration generation

4. **Configuration Export/Import**:
   - Package configurations for sharing
   - Import configurations with validation
   - Configuration versioning and migration
   - Template-to-template configuration copying

### Performance Optimization:
   - Configuration caching with change detection
   - Lazy loading of large configuration files
   - Efficient configuration validation pipelines

## Specific Functionality

### CLI-Specific Logic
1. **Interactive Editing**:
   - Launch preferred editor for configuration files
   - Real-time configuration validation during editing
   - Configuration diff display for changes
   - Guided configuration creation wizards

2. **Rich Display**:
   - Formatted configuration tables with status indicators
   - Syntax-highlighted configuration preview
   - Visual configuration validation reports
   - Interactive configuration comparison tools

3. **User Experience**:
   - Configuration templates and examples
   - Step-by-step configuration guides
   - Error-specific help and suggestions
   - Configuration backup management

### MCPClient-Specific Logic
1. **Programmatic Interface**:
   - Structured configuration access and manipulation
   - Batch configuration operations across templates
   - Configuration monitoring and change detection

2. **Integration Features**:
   - Configuration synchronization across environments
   - Automated configuration deployment
   - Configuration compliance checking
   - Template configuration inheritance

## Proposed Refactor Plan

### Enhanced Common Module: `ConfigManager` (already created)
```python
# Already implemented comprehensive config management
def load_configuration_for_template(self, template_name: str) -> Dict[str, Any]:
    """Load all configurations for a template"""

def validate_template_configuration(self, template_name: str) -> Dict[str, Any]:
    """Comprehensive configuration validation"""

def edit_configuration_file(self, template_name: str, config_file: str) -> bool:
    """Safe configuration editing with validation"""

def export_configuration_package(self, template_name: str, output_path: str) -> bool:
    """Export complete configuration package"""

def import_configuration_package(self, package_path: str, template_name: str) -> bool:
    """Import and validate configuration package"""
```

### New Common Module: `ConfigurationEditor` class
```python
class ConfigurationEditor:
    def launch_editor(self, config_path: str, editor: Optional[str] = None) -> bool:
        """Launch external editor for configuration"""

    def create_configuration_backup(self, config_path: str) -> str:
        """Create timestamped configuration backup"""

    def restore_configuration_backup(self, backup_path: str, config_path: str) -> bool:
        """Restore configuration from backup"""

    def diff_configurations(self, old_path: str, new_path: str) -> str:
        """Generate configuration diff"""
```

### New Common Module: `ConfigurationValidator` class
```python
class ConfigurationValidator:
    def validate_server_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate MCP server configuration"""

    def validate_client_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate MCP client configuration"""

    def validate_deployment_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment configuration"""

    def check_cross_configuration_consistency(self, configs: Dict[str, Dict]) -> List[str]:
        """Check consistency across all configurations"""
```

### Updated CLI Logic
```python
def handle_config_command(args):
    manager = ConfigManager()

    if args.edit:
        result = manager.edit_configuration_file(args.template, args.edit)
        display_edit_result(result)
    elif args.validate:
        result = manager.validate_template_configuration(args.template)
        display_validation_results(result)
    elif args.export:
        result = manager.export_configuration_package(args.template, args.export_path)
        display_export_result(result)
    elif args.import_config:
        result = manager.import_configuration_package(args.import_config, args.template)
        display_import_result(result)
    else:
        configs = manager.load_configuration_for_template(args.template)
        display_configuration_overview(configs)
```

### Updated MCPClient Logic
```python
def get_template_configuration(self, template_name: str) -> Dict[str, Any]:
    manager = ConfigManager()
    return manager.load_configuration_for_template(template_name)

def validate_template_configuration(self, template_name: str) -> Dict[str, Any]:
    manager = ConfigManager()
    return manager.validate_template_configuration(template_name)

def update_template_configuration(self, template_name: str, config_updates: Dict[str, Any]) -> bool:
    manager = ConfigManager()
    return manager.update_configuration_safely(template_name, config_updates)
```

## Implementation Plan

1. **Extend ConfigManager** with template-specific configuration operations
2. **Create ConfigurationEditor class** for safe editing operations
3. **Create ConfigurationValidator class** for comprehensive validation
4. **Add configuration packaging** (export/import) capabilities
5. **Update CLI** to use ConfigManager with rich configuration display
6. **Update MCPClient** to use ConfigManager directly
7. **Remove duplicate configuration logic** from template_manager

## Unit Test Plan

### Tests Location: `tests/test_common/test_config_manager_templates.py`

### Test Categories:
```python
@pytest.mark.unit
class TestConfigManagerTemplates:
    def test_load_configuration_for_template()
    def test_validate_template_configuration()
    def test_edit_configuration_file()
    def test_export_configuration_package()
    def test_import_configuration_package()
    def test_configuration_backup_restore()

@pytest.mark.integration
class TestConfigIntegration:
    def test_config_editing_with_real_templates()
    def test_configuration_package_roundtrip()
    def test_cross_configuration_validation()
```

### Test Coverage for ConfigurationValidator:
```python
@pytest.mark.unit
class TestConfigurationValidator:
    def test_validate_server_config()
    def test_validate_client_config()
    def test_validate_deployment_config()
    def test_check_cross_configuration_consistency()
    def test_configuration_schema_validation()
```

### Test Coverage for ConfigurationEditor:
```python
@pytest.mark.unit
class TestConfigurationEditor:
    def test_launch_editor()
    def test_create_configuration_backup()
    def test_restore_configuration_backup()
    def test_diff_configurations()
    def test_safe_editing_workflow()
```

### Mock Requirements:
- Mock file system operations for configuration files
- Mock external editor launching and interaction
- Mock configuration validation schemas and rules
- Mock configuration packaging and extraction
- Mock template directory structures

## Dependencies / Risks

### Dependencies:
- Enhanced ConfigManager for core configuration operations
- File system access for configuration reading/writing
- Schema validation libraries (jsonschema, cerberus)
- External editor integration (subprocess, environment detection)
- Configuration packaging tools (tar, zip)

### Risks:
1. **Configuration corruption** - editing may corrupt critical configurations
2. **Schema evolution** - configuration schemas may change over time
3. **Editor compatibility** - external editors may not be available/configured
4. **Concurrent editing** - multiple users editing same configuration
5. **Configuration complexity** - templates may have complex interdependent configs
6. **Backup management** - configuration backups may accumulate

### Mitigation:
1. Implement atomic configuration updates with rollback
2. Version-aware schema validation with migration support
3. Fallback to built-in editors and validation-only mode
4. File locking and change detection for concurrent access
5. Configuration dependency mapping and validation
6. Automated backup cleanup and retention policies
7. Comprehensive configuration testing and validation
