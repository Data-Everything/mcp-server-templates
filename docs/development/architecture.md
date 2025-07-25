# Architecture

Overview of the MCP Templates system architecture.

## System Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │────│  Core Library   │────│   Templates     │
│                 │    │                 │    │                 │
│ - Commands      │    │ - Discovery     │    │ - Metadata      │
│ - User Input    │    │ - Deployment    │    │ - Source Code   │
│ - Output        │    │ - Management    │    │ - Tests         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                   ┌─────────────────┐
                   │   Deployment    │
                   │   Backends      │
                   │                 │
                   │ - Local         │
                   │ - Docker        │
                   │ - Kubernetes    │
                   └─────────────────┘
```

## Core Components

### CLI Interface (`mcp_template/__init__.py`)
- Command-line argument parsing
- User interaction and prompts
- Output formatting and display
- Error handling and logging

### Template Discovery (`TemplateDiscovery`)
- Scans template directories
- Validates template metadata
- Provides template information
- Caches template data

### Deployment Engine
- Manages template deployments
- Handles different deployment backends
- Tracks deployment state
- Provides lifecycle management

### Template Creator
- Interactive template creation
- Generates boilerplate code
- Creates proper directory structure
- Initializes documentation

## Template Structure

```
templates/template-name/
├── template.json         # Metadata and configuration
├── Dockerfile           # Container definition
├── src/                 # Source code
│   ├── __init__.py
│   └── server.py        # MCP server implementation
├── docs/                # Documentation
│   └── index.md         # Template documentation
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_units.py    # Unit tests
│   └── test_integration.py # Integration tests
├── config/              # Configuration files (optional)
├── requirements.txt     # Python dependencies
└── README.md           # Usage instructions
```

## Data Flow

### Template Discovery
1. Scan `templates/` directory
2. Read `template.json` files
3. Validate schema and structure
4. Cache template metadata
5. Return available templates

### Template Deployment
1. User selects template
2. System validates requirements
3. Generate deployment configuration
4. Choose deployment backend
5. Execute deployment
6. Track deployment state
7. Provide status feedback

### Template Testing
1. Discover templates with tests
2. Set up test environment
3. Run unit tests
4. Run integration tests
5. Generate coverage reports
6. Validate MCP compliance

## Extension Points

### Custom Deployment Backends
Implement the `DeploymentBackend` interface:

```python
class CustomBackend(DeploymentBackend):
    def deploy(self, template, config):
        # Custom deployment logic
        pass

    def stop(self, deployment_id):
        # Stop deployment
        pass

    def status(self, deployment_id):
        # Check status
        pass
```

### Template Validators
Add custom validation logic:

```python
class CustomValidator(TemplateValidator):
    def validate(self, template_path):
        # Custom validation logic
        return ValidationResult(...)
```

## Configuration Management

### Template Configuration
- Defined in `template.json`
- JSON Schema validation
- Environment variable support
- Port and resource specification

### Runtime Configuration
- Command-line overrides
- Environment variable injection
- Configuration file mounting
- Secret management

## Security Considerations

### Template Isolation
- Each template runs in isolation
- Resource limits enforced
- Network security policies
- File system restrictions

### Input Validation
- All user inputs validated
- Template metadata verification
- Configuration sanitization
- Path traversal prevention

## Performance Optimization

### Template Caching
- Metadata cached in memory
- Docker image layer caching
- Template discovery optimization
- Deployment state persistence

### Parallel Operations
- Concurrent template operations
- Parallel test execution
- Batch deployment support
- Async status monitoring
