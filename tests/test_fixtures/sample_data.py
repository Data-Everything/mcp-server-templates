"""
Test fixtures and sample data for common module testing.
"""

# Sample template data for testing
SAMPLE_TEMPLATE_DATA = {
    "demo": {
        "name": "demo",
        "description": "Demo MCP server template",
        "version": "1.0.0",
        "author": "MCP Team",
        "tags": ["demo", "example", "basic"],
        "capabilities": ["tools", "resources"],
        "requirements": {"python": ">=3.8", "packages": ["fastmcp"]},
        "files": {
            "server.py": "main server file",
            "config.json": "server configuration",
            "requirements.txt": "python dependencies",
        },
    },
    "fastmcp-demo": {
        "name": "fastmcp-demo",
        "description": "FastMCP server demonstration",
        "version": "1.2.0",
        "author": "FastMCP Team",
        "tags": ["fastmcp", "demo", "development"],
        "capabilities": ["tools", "resources", "prompts"],
        "requirements": {"python": ">=3.9", "packages": ["fastmcp", "pydantic"]},
        "files": {
            "main.py": "FastMCP server implementation",
            "config.yaml": "YAML configuration",
            "docker-compose.yml": "Docker deployment",
        },
    },
    "filesystem": {
        "name": "filesystem",
        "description": "File system operations MCP server",
        "version": "1.1.0",
        "author": "File Operations Team",
        "tags": ["filesystem", "files", "utilities"],
        "capabilities": ["tools"],
        "requirements": {"python": ">=3.8", "packages": ["fastmcp", "pathlib"]},
        "files": {
            "server.py": "filesystem operations server",
            "config.json": "server configuration",
            "requirements.txt": "python dependencies",
        },
    },
    "development-tools": {
        "name": "development-tools",
        "description": "Development utilities MCP server",
        "version": "2.1.0",
        "author": "Dev Tools Team",
        "tags": ["development", "utilities", "tools"],
        "capabilities": ["tools"],
        "requirements": {
            "python": ">=3.10",
            "packages": ["fastmcp", "requests", "pytest"],
        },
        "files": {
            "server.py": "development tools server",
            "tools.py": "tool implementations",
            "config.json": "server configuration",
        },
    },
}

# Sample configuration data for testing
SAMPLE_CONFIG_DATA = {
    "server": {
        "name": "demo-server",
        "port": 7071,
        "host": "localhost",
        "log_level": "INFO",
        "timeout": 30,
        "capabilities": ["tools", "resources"],
    },
    "client": {
        "server_url": "http://localhost:7071",
        "timeout": 10,
        "retry_attempts": 3,
        "api_version": "1.0",
    },
    "deployment": {
        "backend": "docker",
        "image": "demo-server:latest",
        "ports": {"7071": "7071"},
        "environment": {"LOG_LEVEL": "INFO", "PORT": "7071"},
        "resources": {"memory": "512Mi", "cpu": "0.5"},
    },
}

# Sample tool data for testing
SAMPLE_TOOL_DATA = {
    "demo": {
        "tools": [
            {
                "name": "echo",
                "description": "Echo back a message with optional formatting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Message to echo back",
                        }
                    },
                    "required": ["message"],
                },
                "category": "utility",
            }
        ]
    },
    "filesystem": {
        "tools": [
            {
                "name": "read_file",
                "description": "Read contents of a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to read",
                        }
                    },
                    "required": ["path"],
                },
                "category": "file_operations",
            },
            {
                "name": "write_file",
                "description": "Write content to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file to write",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                    },
                    "required": ["path", "content"],
                },
                "category": "file_operations",
            },
        ]
    },
    "fastmcp-demo": {
        "tools": [
            {
                "name": "say_hello",
                "description": "Say hello to someone",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the person to greet",
                        }
                    },
                    "required": ["name"],
                },
                "category": "greeting",
            },
            {
                "name": "get_system_info",
                "description": "Get system information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_memory": {
                            "type": "boolean",
                            "description": "Include memory information",
                            "default": True,
                        },
                        "include_cpu": {
                            "type": "boolean",
                            "description": "Include CPU information",
                            "default": True,
                        },
                    },
                },
                "category": "system",
            },
        ]
    },
}

# Sample deployment data for testing
SAMPLE_DEPLOYMENT_DATA = {
    "demo-deployment": {
        "id": "demo-deployment-123",
        "template": "demo",
        "status": "running",
        "created": "2024-08-11T10:30:01Z",
        "updated": "2024-08-11T10:30:03Z",
        "backend": "docker",
        "container_id": "abc123def456",
        "ports": {"7071": "7071"},
        "environment": {"LOG_LEVEL": "INFO", "PORT": "7071"},
    },
    "fastmcp-deployment": {
        "id": "fastmcp-deployment-456",
        "template": "fastmcp-demo",
        "status": "stopped",
        "created": "2024-08-11T09:15:30Z",
        "updated": "2024-08-11T09:45:15Z",
        "backend": "kubernetes",
        "namespace": "mcp-servers",
        "pod_name": "fastmcp-demo-pod-789",
        "ports": {"8080": "8080"},
    },
}

# Sample log data for testing
SAMPLE_LOG_DATA = """2024-08-11 10:30:01 [INFO] MCP Server starting...
2024-08-11 10:30:01 [INFO] Loading configuration from /config/server.json
2024-08-11 10:30:02 [INFO] Initializing FastMCP server
2024-08-11 10:30:02 [INFO] Registering tools: say_hello, echo_message
2024-08-11 10:30:03 [INFO] Server listening on port 7071
2024-08-11 10:30:03 [INFO] MCP Server ready for connections
2024-08-11 10:30:05 [DEBUG] Received client connection from 127.0.0.1
2024-08-11 10:30:06 [INFO] Tool call: say_hello with args: {"name": "World"}
2024-08-11 10:30:06 [DEBUG] Tool execution completed successfully
2024-08-11 10:30:10 [INFO] Tool call: echo_message with args: {"message": "Hello", "repeat": 3}
"""

# Configuration schemas for validation testing
CONFIG_SCHEMAS = {
    "server": {
        "type": "object",
        "required": ["name", "port"],
        "properties": {
            "name": {"type": "string"},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "host": {"type": "string"},
            "log_level": {
                "type": "string",
                "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
            },
            "timeout": {"type": "integer", "minimum": 1},
            "capabilities": {
                "type": "array",
                "items": {"type": "string", "enum": ["tools", "resources", "prompts"]},
            },
        },
    },
    "deployment": {
        "type": "object",
        "required": ["backend"],
        "properties": {
            "backend": {"type": "string", "enum": ["docker", "kubernetes"]},
            "image": {"type": "string"},
            "ports": {"type": "object"},
            "environment": {"type": "object"},
            "resources": {
                "type": "object",
                "properties": {"memory": {"type": "string"}, "cpu": {"type": "string"}},
            },
        },
    },
}

# Mock file system structure for testing
MOCK_FILE_STRUCTURE = {
    "templates/": {
        "demo/": {
            "server.py": "# Demo server implementation\nprint('Hello World')",
            "config.json": '{"name": "demo-server", "port": 7071}',
            "requirements.txt": "fastmcp\nrequests",
            "README.md": "# Demo Template\nBasic demonstration template",
            "template.json": '{"name": "demo", "version": "1.0.0"}',
        },
        "fastmcp-demo/": {
            "main.py": "# FastMCP server\nfrom fastmcp import FastMCP",
            "config.yaml": "name: fastmcp-demo\nport: 8080",
            "docker-compose.yml": "version: '3'\nservices:\n  server:",
            "template.json": '{"name": "fastmcp-demo", "version": "1.2.0"}',
        },
        "development-tools/": {
            "server.py": "# Development tools server",
            "tools.py": "# Tool implementations",
            "config.json": '{"name": "dev-tools", "port": 9090}',
            "template.json": '{"name": "development-tools", "version": "2.1.0"}',
        },
    },
    "deployments/": {
        "demo/": {
            "deployment.yaml": "apiVersion: apps/v1\nkind: Deployment",
            "service.yaml": "apiVersion: v1\nkind: Service",
        }
    },
    "config/": {
        "global.json": '{"templates_dir": "/templates", "default_backend": "docker"}',
        "docker.env": "DOCKER_HOST=unix:///var/run/docker.sock\nDOCKER_API_VERSION=1.41",
    },
}

# Error scenarios for testing
ERROR_SCENARIOS = {
    "template_not_found": {
        "template_name": "non-existent-template",
        "expected_error": "Template 'non-existent-template' not found",
    },
    "invalid_config_format": {
        "config_content": '{"name": "test", "port": "invalid"}',
        "expected_error": "Invalid configuration format",
    },
    "missing_required_field": {
        "config_content": '{"name": "test"}',
        "expected_error": "Missing required field: port",
    },
    "deployment_backend_unavailable": {
        "backend": "docker",
        "expected_error": "Docker daemon is not running",
    },
    "port_already_in_use": {
        "port": 7071,
        "expected_error": "Port 7071 is already in use",
    },
}

# Performance test data
PERFORMANCE_TEST_DATA = {
    "large_template_collection": {
        "template_count": 100,
        "max_list_time": 5.0,  # seconds
        "max_search_time": 2.0,  # seconds
    },
    "concurrent_deployments": {
        "deployment_count": 10,
        "max_deploy_time": 30.0,  # seconds
        "max_concurrent_operations": 5,
    },
    "large_log_retrieval": {
        "log_line_count": 10000,
        "max_retrieval_time": 3.0,  # seconds
    },
}
