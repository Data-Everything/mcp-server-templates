# Test utilities for MCP Server Templates

import os
import json
import tempfile
import subprocess
import contextlib
import time
import requests
from typing import Dict, Any, Optional, Generator
from pathlib import Path

class TemplateTestError(Exception):
    """Exception raised during template testing."""
    pass

class TemplateTestContainer:
    """Context manager for testing template containers."""
    
    def __init__(self, template_name: str, config: Dict[str, Any], port: int = 8000):
        self.template_name = template_name
        self.config = config
        self.port = port
        self.container_id: Optional[str] = None
        self.image_name = f"mcp-{template_name}-test"
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def start(self):
        """Build and start the container."""
        try:
            # Build the container
            self._build_container()
            
            # Start the container
            self._start_container()
            
            # Wait for health check
            self._wait_for_healthy()
            
        except Exception as e:
            self.cleanup()
            raise TemplateTestError(f"Failed to start container: {e}")
    
    def _build_container(self):
        """Build the Docker container."""
        template_dir = Path(__file__).parent.parent / "templates" / self.template_name
        
        if not template_dir.exists():
            raise TemplateTestError(f"Template directory not found: {template_dir}")
        
        cmd = [
            "docker", "build",
            "-t", self.image_name,
            str(template_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise TemplateTestError(f"Build failed: {result.stderr}")
    
    def _start_container(self):
        """Start the Docker container."""
        cmd = [
            "docker", "run", "-d",
            "--name", f"{self.image_name}-{int(time.time())}",
            "-p", f"{self.port}:8000"
        ]
        
        # Add environment variables
        for key, value in self.config.items():
            if isinstance(value, list):
                value = ",".join(str(v) for v in value)
            cmd.extend(["--env", f"{key}={value}"])
        
        cmd.append(self.image_name)
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise TemplateTestError(f"Failed to start container: {result.stderr}")
        
        self.container_id = result.stdout.strip()
    
    def _wait_for_healthy(self, timeout: int = 60):
        """Wait for the container to become healthy."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{self.port}/health", timeout=5)
                if response.status_code == 200:
                    return
            except requests.RequestException:
                pass
            
            time.sleep(2)
        
        raise TemplateTestError(f"Container did not become healthy within {timeout} seconds")
    
    def cleanup(self):
        """Clean up the container and image."""
        if self.container_id:
            # Stop and remove container
            subprocess.run(["docker", "rm", "-f", self.container_id], 
                         capture_output=True)
        
        # Remove test image
        subprocess.run(["docker", "rmi", "-f", self.image_name], 
                     capture_output=True)
    
    def get_logs(self) -> str:
        """Get container logs."""
        if not self.container_id:
            return ""
        
        result = subprocess.run([
            "docker", "logs", self.container_id
        ], capture_output=True, text=True)
        
        return result.stdout + result.stderr
    
    def exec_command(self, command: str) -> str:
        """Execute a command in the container."""
        if not self.container_id:
            raise TemplateTestError("Container not running")
        
        result = subprocess.run([
            "docker", "exec", self.container_id, "sh", "-c", command
        ], capture_output=True, text=True)
        
        return result.stdout

@contextlib.contextmanager
def build_and_run_template(
    template_name: str, 
    config: Optional[Dict[str, Any]] = None,
    port: int = 8000
) -> Generator[TemplateTestContainer, None, None]:
    """Context manager for building and running a template for testing."""
    
    if config is None:
        config = get_default_test_config(template_name)
    
    container = TemplateTestContainer(template_name, config, port)
    
    with container:
        yield container

def get_default_test_config(template_name: str) -> Dict[str, Any]:
    """Get default test configuration for a template."""
    
    # Load template.json to get configuration schema
    template_dir = Path(__file__).parent.parent / "templates" / template_name
    template_json_path = template_dir / "template.json"
    
    if not template_json_path.exists():
        raise TemplateTestError(f"template.json not found for {template_name}")
    
    with open(template_json_path) as f:
        template_data = json.load(f)
    
    config_schema = template_data.get("config_schema", {})
    properties = config_schema.get("properties", {})
    
    # Build default config from schema
    config = {}
    
    for prop_name, prop_def in properties.items():
        env_mapping = prop_def.get("env_mapping")
        if not env_mapping:
            continue
        
        # Use default value if available
        if "default" in prop_def:
            config[env_mapping] = prop_def["default"]
        # Use test values for required fields
        elif prop_name in config_schema.get("required", []):
            if prop_def.get("type") == "string":
                if prop_def.get("secret"):
                    config[env_mapping] = "test-secret-value"
                else:
                    config[env_mapping] = f"test-{prop_name}"
            elif prop_def.get("type") == "integer":
                config[env_mapping] = 42
            elif prop_def.get("type") == "boolean":
                config[env_mapping] = "true"
            elif prop_def.get("type") == "array":
                config[env_mapping] = ["test-item1", "test-item2"]
    
    return config

def validate_template_structure(template_name: str) -> bool:
    """Validate that a template has the required structure."""
    
    template_dir = Path(__file__).parent.parent / "templates" / template_name
    
    required_files = [
        "template.json",
        "Dockerfile",
        "README.md"
    ]
    
    for file_name in required_files:
        file_path = template_dir / file_name
        if not file_path.exists():
            raise TemplateTestError(f"Required file missing: {file_name}")
    
    # Validate template.json structure
    template_json_path = template_dir / "template.json"
    with open(template_json_path) as f:
        template_data = json.load(f)
    
    required_fields = ["name", "description", "docker_image", "config_schema"]
    
    for field in required_fields:
        if field not in template_data:
            raise TemplateTestError(f"Required field missing in template.json: {field}")
    
    return True

def run_template_tests(template_name: str) -> Dict[str, Any]:
    """Run comprehensive tests for a template."""
    
    results = {
        "template_name": template_name,
        "structure_valid": False,
        "build_successful": False,
        "container_starts": False,
        "health_check_passes": False,
        "config_validation": {},
        "errors": []
    }
    
    try:
        # Validate structure
        validate_template_structure(template_name)
        results["structure_valid"] = True
        
        # Test with default config
        with build_and_run_template(template_name) as container:
            results["build_successful"] = True
            results["container_starts"] = True
            
            # Test health check
            response = requests.get(f"http://localhost:{container.port}/health")
            if response.status_code == 200:
                results["health_check_passes"] = True
            
            # Test various configuration scenarios
            results["config_validation"] = test_configuration_scenarios(
                template_name, container
            )
    
    except Exception as e:
        results["errors"].append(str(e))
    
    return results

def test_configuration_scenarios(template_name: str, container: TemplateTestContainer) -> Dict[str, Any]:
    """Test various configuration scenarios."""
    
    scenarios = {
        "default_config": True,  # Already tested by getting here
        "empty_config": False,
        "invalid_config": False,
        "config_file": False
    }
    
    # Additional test scenarios would go here
    # This is a placeholder for more comprehensive testing
    
    return scenarios

class MockMCPClient:
    """Mock MCP client for testing MCP protocol interactions."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
    
    async def list_resources(self):
        """Test listing resources."""
        # Implementation would go here
        pass
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Test calling a tool."""
        # Implementation would go here
        pass

# Utility functions for common test operations
def get_template_list() -> list[str]:
    """Get list of available templates."""
    templates_dir = Path(__file__).parent.parent / "templates"
    
    templates = []
    for item in templates_dir.iterdir():
        if item.is_dir() and (item / "template.json").exists():
            templates.append(item.name)
    
    return sorted(templates)
