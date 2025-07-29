#!/usr/bin/env python3
"""
Test script to validate the configuration mapping strategy.

This script demonstrates how the enhanced configuration system works
and can be used to test different configuration scenarios.
"""

import json


# Mock the config mapper functionality for testing
class MockTemplateConfigMapper:
    """Mock version of TemplateConfigMapper for testing."""

    def __init__(self, template_data):
        self.template_data = template_data
        self.config_schema = template_data.get("config_schema", {}).get(
            "properties", {}
        )
        self.env_variables = template_data.get("environment_variables", {})

    def map_user_config_to_deployment(self, user_config):
        """Map user config to deployment parameters."""
        env_vars = []
        config_file_data = {}

        # Add default env vars from template
        for env_name, env_value in self.env_variables.items():
            if env_name.startswith("MCP_"):
                env_vars.append(f"--env={env_name}={env_value}")

        # Process user config
        for config_key, config_value in user_config.items():
            if self._is_simple_config(config_key, config_value):
                env_name = f"MCP_{config_key.upper().replace('-', '_')}"
                env_value = self._format_env_value(config_value)
                # Replace existing env var
                env_vars = [
                    var for var in env_vars if not var.startswith(f"--env={env_name}=")
                ]
                env_vars.append(f"--env={env_name}={env_value}")
            else:
                config_file_data[config_key] = config_value

        return {"env_vars": env_vars, "config_file_data": config_file_data}

    def _is_simple_config(self, config_key, config_value):
        """Determine if config should use env var."""
        if isinstance(config_value, (str, int, float, bool)):
            return True

        if isinstance(config_value, list):
            return len(config_value) <= 5 and all(
                isinstance(x, str) for x in config_value
            )

        return False

    def _format_env_value(self, value):
        """Format value for environment variable."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, list):
            return ",".join(str(x) for x in value)
        else:
            return str(value)


def test_configuration_scenarios():
    """Test different configuration scenarios."""

    # Load template data (simulated)
    template_data = {
        "config_schema": {
            "properties": {
                "allowed_directories": {"type": "array", "items": {"type": "string"}},
                "read_only_mode": {"type": "boolean"},
                "max_file_size": {"type": "integer"},
                "exclude_patterns": {"type": "array", "items": {"type": "string"}},
                "log_level": {"type": "string"},
                "performance_settings": {"type": "object"},
                "monitoring_config": {"type": "object"},
            }
        },
        "environment_variables": {
            "NODE_ENV": "production",
            "MCP_ALLOWED_DIRS": "/data:/workspace",
            "MCP_READ_ONLY": "false",
            "MCP_MAX_FILE_SIZE": "104857600",
        },
    }

    # Test scenarios
    scenarios = [
        {
            "name": "Simple Configuration (All Env Vars)",
            "user_config": {
                "allowed_directories": ["/data", "/home"],
                "read_only_mode": True,
                "max_file_size": 50,
                "log_level": "debug",
            },
        },
        {
            "name": "Mixed Configuration (Env Vars + Config File)",
            "user_config": {
                "allowed_directories": ["/data", "/home", "/projects"],
                "read_only_mode": False,
                "exclude_patterns": ["**/.git/**", "**/node_modules/**"],
                "performance_settings": {
                    "max_concurrent_operations": 20,
                    "timeout_ms": 45000,
                    "cache_settings": {"enabled": True, "ttl_ms": 600000},
                },
            },
        },
        {
            "name": "Complex Configuration (Mostly Config File)",
            "user_config": {
                "log_level": "info",
                "performance_settings": {
                    "max_concurrent_operations": 15,
                    "timeout_ms": 30000,
                    "rate_limiting": {"enabled": True, "max_requests_per_minute": 1000},
                },
                "monitoring_config": {
                    "health_check_interval": 30,
                    "metrics_enabled": True,
                    "alert_thresholds": {
                        "memory_usage_mb": 512,
                        "disk_usage_percent": 90,
                    },
                },
            },
        },
    ]

    mapper = MockTemplateConfigMapper(template_data)

    print("Configuration Mapping Test Results")
    print("=" * 50)

    for scenario in scenarios:
        print(f"\n{scenario['name']}")
        print("-" * len(scenario["name"]))

        result = mapper.map_user_config_to_deployment(scenario["user_config"])

        print(f"Environment Variables ({len(result['env_vars'])}):")
        for env_var in result["env_vars"]:
            print(f"  {env_var}")

        if result["config_file_data"]:
            print("\nConfig File Data:")
            print(json.dumps(result["config_file_data"], indent=2))
        else:
            print("\nConfig File: Not needed")

        print(
            f"\nDeployment Strategy: {'Hybrid (Env + File)' if result['config_file_data'] else 'Environment Variables Only'}"
        )


def demonstrate_deployment_command():
    """Show what the actual Docker deployment command would look like."""

    print("\n" + "=" * 50)
    print("Docker Deployment Command Example")
    print("=" * 50)

    # Simulate enhanced configuration
    env_vars = [
        "--env=MCP_ALLOWED_DIRECTORIES=/data,/home,/projects",
        "--env=MCP_READ_ONLY=false",
        "--env=MCP_MAX_FILE_SIZE=104857600",
        "--env=MCP_LOG_LEVEL=debug",
    ]

    config_file_path = "/tmp/mcp_config_12345.yaml"
    volumes = [f"--volume={config_file_path}:/app/config/config.yaml:ro"]

    # Construct docker command
    docker_cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        "mcp-file-server-abc123",
        "--restart",
        "unless-stopped",
    ]

    docker_cmd.extend(env_vars)
    docker_cmd.extend(volumes)
    docker_cmd.extend(["--volume", "/tmp/mcp-file-server-data:/data"])
    docker_cmd.extend(["-p", "8001:8000"])
    docker_cmd.append("data-everything/mcp-file-server:latest")

    print("Generated Docker Command:")
    print(" \\\n  ".join(docker_cmd))

    print(f"\nConfig file would be created at: {config_file_path}")
    print(
        "Config file would contain complex settings like performance tuning, monitoring, etc."
    )


if __name__ == "__main__":
    test_configuration_scenarios()
    demonstrate_deployment_command()
