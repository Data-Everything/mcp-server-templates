"""
Tests for the MCP Client programmatic interface.

These tests validate that the MCPClient provides the expected programmatic
interface without breaking existing functionality.
"""

import pytest
from unittest.mock import Mock, patch

from mcp_template.client import MCPClient


class TestMCPClient:
    """Test the MCPClient programmatic interface."""

    def test_client_initialization(self):
        """Test that MCPClient initializes correctly."""
        client = MCPClient()
        
        assert client.backend_type == "docker"
        assert client.config_dir.name == ".mcp"
        assert hasattr(client, "deployment_manager")
        assert hasattr(client, "template_discovery")
        assert hasattr(client, "tool_discovery")
        assert hasattr(client, "config_processor")

    def test_client_initialization_with_custom_backend(self):
        """Test MCPClient with custom backend."""
        client = MCPClient(backend_type="mock")
        assert client.backend_type == "mock"

    @patch('mcp_template.client.TemplateDiscovery')
    def test_list_templates_as_dict(self, mock_discovery):
        """Test listing templates as dictionary."""
        # Mock template discovery
        mock_templates = {
            "demo": {
                "name": "demo",
                "description": "Demo template",
                "version": "1.0.0"
            },
            "github": {
                "name": "github", 
                "description": "GitHub template",
                "version": "1.0.0"
            }
        }
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = mock_templates
        mock_discovery.return_value = mock_discovery_instance
        
        client = MCPClient()
        templates = client.list_templates(as_dict=True)
        
        assert isinstance(templates, dict)
        assert "demo" in templates
        assert "github" in templates
        assert templates["demo"]["description"] == "Demo template"

    @patch('mcp_template.client.TemplateDiscovery')
    @patch('mcp_template.client.DeploymentManager')
    def test_list_templates_as_list(self, mock_manager, mock_discovery):
        """Test listing templates as list with status info."""
        # Mock template discovery
        mock_templates = {
            "demo": {
                "name": "demo",
                "description": "Demo template",
                "version": "1.0.0"
            }
        }
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = mock_templates
        mock_discovery.return_value = mock_discovery_instance
        
        # Mock deployment manager
        mock_manager_instance = Mock()
        mock_manager_instance.list_deployments.return_value = []
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        templates = client.list_templates(as_dict=False)
        
        assert isinstance(templates, list)
        assert len(templates) == 1
        template_info = templates[0]
        assert template_info["name"] == "demo"
        assert template_info["status"] == "not_deployed"
        assert template_info["running_count"] == 0

    @patch('mcp_template.client.TemplateDiscovery')
    def test_get_template_config(self, mock_discovery):
        """Test getting template configuration."""
        mock_templates = {
            "demo": {
                "name": "demo",
                "config_schema": {
                    "type": "object",
                    "properties": {
                        "api_key": {"type": "string"}
                    }
                }
            }
        }
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = mock_templates
        mock_discovery.return_value = mock_discovery_instance
        
        client = MCPClient()
        config = client.get_template_config("demo")
        
        assert "properties" in config
        assert "api_key" in config["properties"]

    @patch('mcp_template.client.TemplateDiscovery')
    def test_get_template_config_not_found(self, mock_discovery):
        """Test getting config for non-existent template."""
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = {}
        mock_discovery.return_value = mock_discovery_instance
        
        client = MCPClient()
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            client.get_template_config("nonexistent")

    @patch('mcp_template.client.TemplateDiscovery')
    @patch('mcp_template.client.DeploymentManager')
    def test_deploy_template(self, mock_manager, mock_discovery):
        """Test deploying a template."""
        # Mock template discovery
        mock_templates = {
            "demo": {
                "name": "demo",
                "description": "Demo template"
            }
        }
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = mock_templates
        mock_discovery.return_value = mock_discovery_instance
        
        # Mock deployment manager
        mock_manager_instance = Mock()
        mock_deployment_result = {
            "name": "demo",
            "status": "running",
            "endpoint": "http://localhost:8080"
        }
        mock_manager_instance.deploy_template.return_value = mock_deployment_result
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        result = client.deploy("demo", config={"api_key": "test"})
        
        assert result == mock_deployment_result
        mock_manager_instance.deploy_template.assert_called_once()

    @patch('mcp_template.client.TemplateDiscovery')
    def test_deploy_template_not_found(self, mock_discovery):
        """Test deploying non-existent template."""
        mock_discovery_instance = Mock()
        mock_discovery_instance.discover_templates.return_value = {}
        mock_discovery.return_value = mock_discovery_instance
        
        client = MCPClient()
        
        with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
            client.deploy("nonexistent")

    @patch('mcp_template.client.DeploymentManager')
    def test_list_deployments(self, mock_manager):
        """Test listing deployments."""
        mock_deployments = [
            {"name": "demo", "status": "running"},
            {"name": "github", "status": "stopped"}
        ]
        mock_manager_instance = Mock()
        mock_manager_instance.list_deployments.return_value = mock_deployments
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        deployments = client.list_deployments()
        
        assert deployments == mock_deployments

    @patch('mcp_template.client.DeploymentManager')
    def test_stop_deployment(self, mock_manager):
        """Test stopping a deployment."""
        mock_manager_instance = Mock()
        mock_manager_instance.delete_deployment.return_value = True
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        result = client.stop("demo")
        
        assert result is True
        mock_manager_instance.delete_deployment.assert_called_once_with("demo")

    @patch('mcp_template.client.DeploymentManager')
    def test_get_deployment_status(self, mock_manager):
        """Test getting deployment status."""
        mock_status = {"name": "demo", "status": "running", "uptime": "5m"}
        mock_manager_instance = Mock()
        mock_manager_instance.get_deployment_status.return_value = mock_status
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        status = client.get_deployment_status("demo")
        
        assert status == mock_status

    @patch('mcp_template.client.ToolDiscovery')
    @patch('mcp_template.client.DeploymentManager')
    def test_discover_tools(self, mock_manager, mock_tool_discovery):
        """Test tool discovery."""
        # Mock deployments to provide endpoint
        mock_deployments = [
            {"template": "demo", "endpoint": "http://localhost:8080"}
        ]
        mock_manager_instance = Mock()
        mock_manager_instance.list_deployments.return_value = mock_deployments
        mock_manager.return_value = mock_manager_instance
        
        # Mock tool discovery
        mock_tools = [
            {"name": "greet", "description": "Greeting tool"},
            {"name": "echo", "description": "Echo tool"}
        ]
        mock_tool_discovery_instance = Mock()
        mock_tool_discovery_instance.discover_tools.return_value = mock_tools
        mock_tool_discovery.return_value = mock_tool_discovery_instance
        
        client = MCPClient()
        tools = client.discover_tools("demo")
        
        assert tools == mock_tools
        mock_tool_discovery_instance.discover_tools.assert_called_once_with("http://localhost:8080")

    @patch('mcp_template.client.DeploymentManager')
    def test_discover_tools_no_deployment(self, mock_manager):
        """Test tool discovery when no deployment exists."""
        mock_manager_instance = Mock()
        mock_manager_instance.list_deployments.return_value = []
        mock_manager.return_value = mock_manager_instance
        
        client = MCPClient()
        
        with pytest.raises(RuntimeError, match="No running deployments found"):
            client.discover_tools("demo")

    def test_refresh_templates(self):
        """Test refreshing templates cache."""
        with patch('mcp_template.client.TemplateDiscovery') as mock_discovery:
            mock_templates = {"demo": {"name": "demo"}}
            mock_discovery_instance = Mock()
            mock_discovery_instance.discover_templates.return_value = mock_templates
            mock_discovery.return_value = mock_discovery_instance
            
            client = MCPClient()
            
            # First call should cache templates
            first_templates = client.templates
            assert first_templates == mock_templates
            
            # Refresh should clear cache and reload
            refreshed_templates = client.refresh_templates()
            assert refreshed_templates == mock_templates
            
            # Verify discovery was called multiple times
            assert mock_discovery_instance.discover_templates.call_count >= 2


class TestMCPClientIntegration:
    """Integration tests for MCPClient with real components."""

    def test_client_import(self):
        """Test that MCPClient can be imported from the main package."""
        from mcp_template import MCPClient
        
        # Should be able to instantiate
        client = MCPClient(backend_type="mock")  # Use mock to avoid Docker dependency
        assert isinstance(client, MCPClient)

    def test_client_templates_discovery(self):
        """Test that client can discover real templates."""
        # Use mock backend to avoid Docker dependency
        client = MCPClient(backend_type="mock")
        
        # Should be able to list templates
        templates = client.list_templates()
        assert isinstance(templates, dict)
        
        # Should have some built-in templates
        template_names = list(templates.keys())
        expected_templates = ["demo", "github", "gitlab", "zendesk", "filesystem"]
        
        # At least some of the expected templates should be found
        found_templates = [t for t in expected_templates if t in template_names]
        assert len(found_templates) > 0, f"Expected some of {expected_templates}, found {template_names}"