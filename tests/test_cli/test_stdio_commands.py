"""
Tests for the stdio MCP commands (run-tool and tools).
"""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch
from argparse import Namespace

from mcp_template.cli import EnhancedCLI, handle_enhanced_cli_commands


class TestStdioCommands(unittest.TestCase):
    """Test stdio MCP command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('mcp_template.cli.TemplateDiscovery'):
            self.enhanced_cli = EnhancedCLI()
            # Mock template data
            self.enhanced_cli.templates = {
                'github': {
                    'image': 'test/github:latest',
                    'command': ['mcp-server-github'],
                    'transport': {
                        'default': 'stdio',
                        'supported': ['stdio']
                    },
                    'tools': [
                        {'name': 'search_repositories'},
                        {'name': 'create_issue'}
                    ]
                },
                'http-template': {
                    'image': 'test/http:latest',
                    'command': ['mcp-server-http'],
                    'transport': {
                        'default': 'http',
                        'supported': ['http']
                    }
                }
            }

    @patch('mcp_template.cli.console')
    @patch('mcp_template.backends.docker.DockerDeploymentService')
    def test_run_stdio_tool_success(self, mock_docker_service, mock_console):
        """Test successful stdio tool execution."""
        # Mock Docker service response
        mock_docker_instance = mock_docker_service.return_value
        mock_docker_instance.run_stdio_command.return_value = {
            'status': 'completed',
            'stdout': json.dumps({
                "jsonrpc": "2.0",
                "id": 3,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps({"total_count": 1, "items": []})}
                    ]
                }
            }),
            'stderr': '',
            'template_id': 'github'
        }

        # Execute the method
        result = self.enhanced_cli.run_stdio_tool(
            'github',
            'search_repositories',
            tool_args='{"query": "python"}',
            env_vars={'GITHUB_TOKEN': 'test-token'}
        )

        # Verify the Docker service was called correctly
        mock_docker_instance.run_stdio_command.assert_called_once()
        
        # Verify success console output
        mock_console.print.assert_any_call("[green]✅ Tool executed successfully[/green]")
        
        self.assertTrue(result)

    @patch('mcp_template.cli.console')
    def test_run_stdio_tool_template_not_found(self, mock_console):
        """Test stdio tool execution with missing template."""
        result = self.enhanced_cli.run_stdio_tool('nonexistent', 'test_tool')
        
        mock_console.print.assert_any_call(
            "[red]❌ Template 'nonexistent' not found[/red]"
        )
        self.assertFalse(result)

    @patch('mcp_template.cli.console')
    def test_run_stdio_tool_non_stdio_template(self, mock_console):
        """Test stdio tool execution with non-stdio template."""
        result = self.enhanced_cli.run_stdio_tool('http-template', 'test_tool')
        
        mock_console.print.assert_any_call(
            "[red]❌ Template 'http-template' does not support stdio transport[/red]"
        )
        self.assertFalse(result)

    @patch('mcp_template.cli.console')
    @patch('mcp_template.backends.docker.DockerDeploymentService')
    def test_run_stdio_tool_docker_failure(self, mock_docker_service, mock_console):
        """Test stdio tool execution with Docker failure."""
        # Mock Docker service failure
        mock_docker_instance = mock_docker_service.return_value
        mock_docker_instance.run_stdio_command.return_value = {
            'status': 'failed',
            'stdout': '',
            'stderr': 'Container failed to start',
            'error': 'Docker error',
            'template_id': 'github'
        }

        result = self.enhanced_cli.run_stdio_tool('github', 'search_repositories')
        
        mock_console.print.assert_any_call("[red]❌ Tool execution failed: Docker error[/red]")
        self.assertFalse(result)

    @patch('mcp_template.cli.console')
    def test_run_stdio_tool_invalid_json_args(self, mock_console):
        """Test stdio tool execution with invalid JSON arguments."""
        result = self.enhanced_cli.run_stdio_tool(
            'github', 
            'search_repositories',
            tool_args='invalid-json'
        )
        
        mock_console.print.assert_any_call(
            "[red]❌ Invalid JSON in tool arguments: invalid-json[/red]"
        )
        self.assertFalse(result)

    def test_handle_enhanced_cli_commands_run_tool(self):
        """Test run-tool command handling."""
        args = Namespace(
            command='run-tool',
            template='github',
            tool_name='search_repositories',
            args='{"query": "python"}',
            config=['debug=true'],
            env=['GITHUB_TOKEN=test']
        )

        with patch.object(self.enhanced_cli, 'run_stdio_tool') as mock_run_tool:
            mock_run_tool.return_value = True
            result = handle_enhanced_cli_commands(args, self.enhanced_cli)
            
            self.assertTrue(result)
            mock_run_tool.assert_called_once_with(
                'github',
                'search_repositories',
                tool_args='{"query": "python"}',
                config_values={'debug': 'true'},
                env_vars={'GITHUB_TOKEN': 'test'}
            )

    def test_handle_enhanced_cli_commands_tools(self):
        """Test tools command handling."""
        args = Namespace(
            command='tools',
            template='github',
            image=None,
            config=None,
            no_cache=False,
            refresh=False
        )

        with patch.object(self.enhanced_cli, 'list_tools') as mock_list_tools:
            result = handle_enhanced_cli_commands(args, self.enhanced_cli)
            
            self.assertTrue(result)
            mock_list_tools.assert_called_once_with(
                'github',
                no_cache=False,
                refresh=False,
                config_values={}
            )

    def test_handle_enhanced_cli_commands_tools_with_image(self):
        """Test tools command handling with Docker image."""
        args = Namespace(
            command='tools',
            template=None,
            image='test/github:latest',
            server_args=['--config', 'test'],
            config=['debug=true']
        )

        with patch.object(self.enhanced_cli, 'discover_tools_from_image') as mock_discover:
            result = handle_enhanced_cli_commands(args, self.enhanced_cli)
            
            self.assertTrue(result)
            mock_discover.assert_called_once_with(
                'test/github:latest',
                ['--config', 'test'],
                {'debug': 'true'}
            )

    @patch('mcp_template.cli.console')
    def test_handle_enhanced_cli_commands_tools_no_args(self, mock_console):
        """Test tools command handling with no template or image."""
        args = Namespace(
            command='tools',
            template=None,
            image=None,
            config=None
        )

        result = handle_enhanced_cli_commands(args, self.enhanced_cli)
        
        self.assertFalse(result)
        # Test that it doesn't crash and returns False for invalid args

    @patch('mcp_template.cli.console')
    @patch('mcp_template.cli.MCPDeployer')
    def test_deploy_with_transport_stdio_prevention(self, mock_deployer, mock_console):
        """Test that stdio templates cannot be deployed."""
        result = self.enhanced_cli.deploy_with_transport(
            'github',
            transport='stdio'
        )

        self.assertFalse(result)
        
        # Check that console.print was called (indicating stdio prevention worked)
        self.assertTrue(mock_console.print.called)


if __name__ == '__main__':
    unittest.main()
