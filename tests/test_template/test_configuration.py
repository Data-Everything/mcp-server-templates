"""
Tests for configuration mapping and type conversion functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mcp_template import MCPDeployer


@pytest.mark.unit
class TestConfigurationMapping:
    """Test configuration mapping functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

        # Mock template with comprehensive schema
        self.mock_template = {
            "name": "test-server",
            "config_schema": {
                "properties": {
                    "log_level": {
                        "type": "string",
                        "default": "info",
                        "env_mapping": "MCP_LOG_LEVEL",
                        "description": "Logging level",
                    },
                    "read_only_mode": {
                        "type": "boolean",
                        "default": False,
                        "env_mapping": "MCP_READ_ONLY",
                        "description": "Enable read-only mode",
                    },
                    "max_file_size": {
                        "type": "integer",
                        "default": 100,
                        "env_mapping": "MCP_MAX_FILE_SIZE",
                        "description": "Maximum file size in MB",
                    },
                    "allowed_directories": {
                        "type": "array",
                        "default": ["/data"],
                        "env_mapping": "MCP_ALLOWED_DIRS",
                        "env_separator": ":",
                        "description": "Allowed directories",
                    },
                    "custom_property": {
                        "type": "string",
                        "env_mapping": "MCP_CUSTOM",
                        "file_mapping": "custom.nested.value",
                        "description": "Custom property with explicit file mapping",
                    },
                },
                "required": ["log_level"],
            },
        }


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployer = MCPDeployer()

    def test_file_server_template_config_mapping(self):
        """Test configuration mapping for file-server template."""
        if "file-server" not in self.deployer.templates:
            pytest.skip("file-server template not available")

        template = self.deployer.templates["file-server"]

        # Test with realistic file-server config
        file_config = {
            "security": {
                "allowedDirs": ["/data", "/workspace"],
                "readOnly": False,
                "maxFileSize": 100,
                "excludePatterns": ["*.tmp", "*.log"],
            },
            "logging": {"level": "info", "enableAudit": True},
        }

        result = self.deployer._map_file_config_to_env(file_config, template)

        # Should map to appropriate environment variables
        assert "MCP_ALLOWED_DIRECTORIES" in result or "MCP_ALLOWED_DIRS" in result
        assert "MCP_READ_ONLY_MODE" in result or "MCP_READ_ONLY" in result
        assert "MCP_LOG_LEVEL" in result
