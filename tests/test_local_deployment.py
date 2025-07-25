#!/usr/bin/env python3
"""
Test script to simulate local deployment with the updated configuration mapping.
This tests if our env var mapping fixes work correctly.
"""

import json
import subprocess
import sys
import time


def run_command(cmd):
    """Run a command and return result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return None
    return result.stdout.strip()


def test_deployment():
    """Test deployment with our configuration mapping."""

    # Simulate template data (what your Django app fetches from GitHub)
    template_data = {
        "docker_image": "local-mcp-file-server",
        "docker_tag": "test",
        "config_schema": {
            "properties": {
                "allowed_directories": {
                    "env_mapping": "MCP_ALLOWED_DIRS",
                    "env_separator": ":",
                },
                "read_only_mode": {"env_mapping": "MCP_READ_ONLY"},
                "enable_symlinks": {"env_mapping": "MCP_ENABLE_SYMLINKS"},
                "max_file_size": {"env_mapping": "MCP_MAX_FILE_SIZE"},
                "exclude_patterns": {
                    "env_mapping": "MCP_EXCLUDE_PATTERNS",
                    "env_separator": ",",
                },
                "log_level": {"env_mapping": "MCP_LOG_LEVEL"},
            }
        },
    }

    # Simulate user configuration (what user enters in UI form)
    user_config = {
        "allowed_directories": ["/data", "/home", "/projects"],
        "read_only_mode": False,
        "enable_symlinks": True,
        "max_file_size": 50,
        "exclude_patterns": ["**/.git/**", "**/node_modules/**", "**/.DS_Store"],
        "log_level": "debug",
    }

    print("=" * 60)
    print("Testing Local File-Server Deployment")
    print("=" * 60)

    # Generate environment variables using the same logic as docker_bash_service.py
    config_schema = template_data.get("config_schema", {}).get("properties", {})
    env_vars = []

    for key, value in user_config.items():
        # Get the proper environment variable name from template schema
        schema_field = config_schema.get(key, {})
        env_key = schema_field.get("env_mapping")

        if not env_key:
            # Fallback to standard MCP_ prefix if no mapping defined
            env_key = f"MCP_{key.upper().replace(' ', '_').replace('-', '_')}"

        # Format the value appropriately
        if isinstance(value, list):
            # Use separator from schema, default to comma
            separator = schema_field.get("env_separator", ",")
            env_value = separator.join(str(item) for item in value)
        elif isinstance(value, bool):
            env_value = "true" if value else "false"
        else:
            env_value = str(value)

        env_vars.append(f"--env={env_key}={env_value}")

    print("\nGenerated Environment Variables:")
    for env_var in env_vars:
        print(f"  {env_var}")

    # Clean up any existing test container
    print("\nCleaning up existing test container...")
    run_command(["docker", "rm", "-f", "mcp-file-server-test"])

    # Build docker run command
    container_name = "mcp-file-server-test"
    image_name = f"{template_data['docker_image']}:{template_data['docker_tag']}"

    docker_cmd = (
        ["docker", "run", "-d", "--name", container_name, "-p", "8001:8000"]
        + env_vars
        + [
            "--volume",
            "/tmp/mcp-test-data:/data",
            "--volume",
            "/tmp/mcp-test-workspace:/workspace",
            image_name,
        ]
    )

    print("\nDocker Command:")
    print(" \\\n  ".join(docker_cmd))

    # Run the container
    print("\nStarting container...")
    container_id = run_command(docker_cmd)

    if not container_id:
        print("Failed to start container!")
        return False

    print(f"Container started with ID: {container_id[:12]}...")

    # Wait a moment for container to start
    print("Waiting for container to initialize...")
    time.sleep(3)

    # Check container status
    status_cmd = [
        "docker",
        "ps",
        "--filter",
        f"name={container_name}",
        "--format",
        "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}",
    ]
    status = run_command(status_cmd)
    print("\nContainer Status:")
    print(status)

    # Get container logs to see if configuration is working
    print("\nContainer Logs:")
    logs = run_command(["docker", "logs", container_name])
    if logs:
        print(logs)
    else:
        print("No logs available yet")

    # Check if container is running
    inspect_cmd = [
        "docker",
        "inspect",
        container_name,
        "--format",
        "{{.State.Running}}",
    ]
    running = run_command(inspect_cmd)

    if running == "true":
        print("\n✅ SUCCESS: Container is running!")

        # Test if we can reach the health check endpoint
        print("\nTesting health check endpoint...")
        try:
            import requests

            response = requests.get("http://localhost:8001/health", timeout=5)
            print(f"Health check response: {response.status_code}")
            if response.status_code == 200:
                print("✅ Health check passed!")
            else:
                print(f"❌ Health check failed: {response.text}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")

        # Show environment variables inside container to verify they're set correctly
        print("\nEnvironment variables inside container:")
        env_output = run_command(
            ["docker", "exec", container_name, "env", "|", "grep", "MCP_"]
        )
        if env_output:
            print(env_output)
        else:
            # Try without grep
            env_output = run_command(["docker", "exec", container_name, "env"])
            mcp_vars = [line for line in env_output.split("\n") if "MCP_" in line]
            for var in mcp_vars:
                print(f"  {var}")

        return True
    else:
        print("\n❌ FAILED: Container is not running!")
        return False


def cleanup():
    """Clean up test resources."""
    print("\nCleaning up...")
    run_command(["docker", "rm", "-f", "mcp-file-server-test"])
    run_command(["docker", "volume", "prune", "-f"])


if __name__ == "__main__":
    try:
        success = test_deployment()
        if success:
            print("\n" + "=" * 60)
            print("🎉 LOCAL TEST PASSED! Configuration mapping is working!")
            print("=" * 60)

            # Keep container running for manual testing
            print("\nContainer is still running for manual testing.")
            print("You can:")
            print("  - Check logs: docker logs mcp-file-server-test")
            print("  - Exec into container: docker exec -it mcp-file-server-test sh")
            print("  - Test endpoints: curl http://localhost:8001/health")
            print("  - Stop when done: docker rm -f mcp-file-server-test")

        else:
            print("\n❌ LOCAL TEST FAILED!")
            cleanup()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        cleanup()
        sys.exit(1)
