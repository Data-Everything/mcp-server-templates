"""
Simplified integration tests for Docker tool discovery functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from mcp_template.tools.discovery import ToolDiscovery
from mcp_template.cli import EnhancedCLI


@pytest.mark.unit
@pytest.mark.docker
class TestDockerDiscoveryBasic:
    """Basic tests for Docker discovery functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.discovery = ToolDiscovery()

    @patch('mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image')
    def test_dynamic_discovery_uses_docker_when_image_available(self, mock_docker_discovery):
        """Test that dynamic discovery uses Docker when image is available."""
        # Mock Docker discovery response
        mock_docker_discovery.return_value = {
            "tools": [
                {
                    "name": "docker_tool",
                    "description": "A Docker discovered tool",
                    "category": "mcp",
                    "parameters": {}
                }
            ],
            "discovery_method": "docker_mcp_stdio",
            "timestamp": 1234567890,
            "template_name": "test_template"
        }

        # Template config with Docker image for dynamic discovery
        template_config = {
            "name": "Test Template",
            "tool_discovery": "dynamic",
            "image": "test/image",
            "docker_tag": "latest"
        }

        result = self.discovery.discover_tools(
            template_name="test_template",
            template_dir=Path("/fake/path"),
            template_config=template_config,
            use_cache=False
        )

        # Verify Docker discovery was called
        mock_docker_discovery.assert_called_once()
        
        # Verify results
        assert result is not None
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "docker_tool"
        assert result["discovery_method"] == "docker_mcp_stdio"

    def test_fallback_to_capabilities_when_docker_fails(self):
        """Test fallback to template capabilities when Docker discovery fails."""
        # Template config with capabilities but Docker will fail
        template_config = {
            "name": "Test Template",
            "tool_discovery": "dynamic",
            "capabilities": [
                {
                    "name": "fallback_tool",
                    "description": "A fallback capability"
                }
            ]
        }

        result = self.discovery.discover_tools(
            template_name="test_template",
            template_dir=None,
            template_config=template_config,
            use_cache=False
        )

        # Should fall back to template capabilities
        assert result is not None
        assert result["discovery_method"] == "template_json"
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "fallback_tool"
        assert "Using template-defined capabilities as fallback" in result["warnings"]

    @patch('mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image')
    def test_env_vars_passed_to_docker_discovery(self, mock_docker_discovery):
        """Test that environment variables are passed to Docker discovery."""
        mock_docker_discovery.return_value = {
            "tools": [{"name": "env_tool", "description": "Tool with env", "category": "mcp", "parameters": {}}],
            "discovery_method": "docker_mcp_stdio"
        }

        # Template config with environment variables
        template_config = {
            "name": "Test Template",
            "tool_discovery": "dynamic",
            "image": "test/server",
            "docker_tag": "v1.0",
            "env_vars": {"API_KEY": "test_key", "LOG_LEVEL": "DEBUG"}
        }

        result = self.discovery.discover_tools(
            template_name="test_template", 
            template_dir=None,
            template_config=template_config,
            use_cache=False
        )

        # Verify Docker discovery was called with environment variables
        mock_docker_discovery.assert_called_once()
        call_args = mock_docker_discovery.call_args
        
        # Check that environment variables were passed
        assert call_args[1]["env_vars"]["API_KEY"] == "test_key"
        assert call_args[1]["env_vars"]["LOG_LEVEL"] == "DEBUG"

    def test_env_vars_extraction_from_config_schema(self):
        """Test extraction of environment variables from config schema."""
        config = {
            "config_schema": {
                "properties": {
                    "github_token": {
                        "env_mapping": "GITHUB_PERSONAL_ACCESS_TOKEN",
                        "default": "default_token"
                    },
                    "log_level": {
                        "env_mapping": "LOG_LEVEL",
                        "default": "INFO"
                    }
                }
            }
        }

        env_vars = self.discovery._extract_env_vars_from_config(config)

        # Should extract env_vars from config schema
        assert env_vars["GITHUB_PERSONAL_ACCESS_TOKEN"] == "default_token"
        assert env_vars["LOG_LEVEL"] == "INFO"


@pytest.mark.integration
@pytest.mark.docker
class TestCLIConfigIntegration:
    """Test CLI integration with config values."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = EnhancedCLI()

    def test_cli_merges_config_values_with_template(self):
        """Test that CLI properly merges config values with template configuration."""
        # Mock the CLI's templates
        self.cli.templates = {
            "github": {
                "name": "GitHub Template",
                "tool_discovery": "dynamic",
                "image": "ghcr.io/github/github-mcp-server",
                "docker_tag": "0.9.1"
            }
        }
        
        # Mock the discovery system
        with patch.object(self.cli.tool_discovery, 'discover_tools') as mock_discover:
            mock_discover.return_value = {
                "tools": [{"name": "github_tool", "description": "GitHub tool", "category": "mcp", "parameters": {}}],
                "discovery_method": "docker_mcp_stdio"
            }

            # Mock console output
            with patch('mcp_template.cli.console'):
                # Test list_tools with config values
                self.cli.list_tools(
                    template_name="github",
                    config_values={"GITHUB_PERSONAL_ACCESS_TOKEN": "secret_token"}
                )

            # Verify discover_tools was called with merged config
            mock_discover.assert_called_once()
            call_kwargs = mock_discover.call_args[1]
            
            # Check that config values were merged into template config
            template_config = call_kwargs["template_config"]
            assert "env_vars" in template_config
            assert template_config["env_vars"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "secret_token"


@pytest.mark.e2e
@pytest.mark.docker
class TestEndToEndBehavior:
    """Test end-to-end behavior for real scenarios."""

    def test_github_template_scenario(self):
        """Test the GitHub template scenario end-to-end."""
        discovery = ToolDiscovery()
        
        # Realistic GitHub template config (like what CLI loads)
        github_template_config = {
            "name": "GitHub",
            "description": "Official GitHub MCP server implementation",
            "version": "1.0.0",
            "category": "General",
            "tool_discovery": "dynamic",
            "docker_image": "ghcr.io/github/github-mcp-server",
            "docker_tag": "0.9.1",
            "capabilities": [
                {
                    "name": "example",
                    "description": "A simple example tool"
                }
            ],
            "config_schema": {
                "properties": {
                    "github_token": {
                        "env_mapping": "GITHUB_PERSONAL_ACCESS_TOKEN"
                    }
                }
            },
            # Simulate config values merged by CLI
            "env_vars": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": "test_token"
            }
        }

        # Test discovery behavior
        with patch('mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image') as mock_docker:
            # First test: Docker succeeds (normal case)
            mock_docker.return_value = {
                "tools": [
                    {"name": "get_issue", "description": "Get GitHub issue", "category": "mcp", "parameters": {}},
                    {"name": "create_pr", "description": "Create pull request", "category": "mcp", "parameters": {}}
                ],
                "discovery_method": "docker_mcp_stdio"
            }

            result = discovery.discover_tools(
                template_name="github",
                template_dir=None,
                template_config=github_template_config,
                use_cache=False
            )

            # Should get Docker discovery results
            assert result["discovery_method"] == "docker_mcp_stdio"
            assert len(result["tools"]) == 2
            assert result["tools"][0]["name"] == "get_issue"
            
            # Verify environment variables were passed to Docker
            mock_docker.assert_called_once()
            call_args = mock_docker.call_args
            assert call_args[1]["env_vars"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "test_token"

        # Second test: Docker fails, should fall back to capabilities
        with patch('mcp_template.tools.docker_probe.DockerProbe.discover_tools_from_image') as mock_docker:
            mock_docker.return_value = None  # Docker discovery fails

            result = discovery.discover_tools(
                template_name="github",
                template_dir=None,
                template_config=github_template_config,
                use_cache=False
            )

            # Should fall back to template capabilities
            assert result["discovery_method"] == "template_json"
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "example"
            assert "Using template-defined capabilities as fallback" in result["warnings"]


if __name__ == "__main__":
    pytest.main([__file__])
