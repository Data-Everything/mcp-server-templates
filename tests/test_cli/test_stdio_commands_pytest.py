"""
Tests for the stdio MCP commands (run-tool and tools).
"""

import json
import pytest
from unittest.mock import MagicMock, Mock, patch
from argparse import Namespace

from mcp_template.cli import EnhancedCLI, handle_enhanced_cli_commands


@pytest.fixture
def enhanced_cli():
    """Create an EnhancedCLI instance with mocked templates."""
    with patch('mcp_template.cli.TemplateDiscovery'):
        cli = EnhancedCLI()
        # Mock template data
        cli.templates = {
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
        return cli


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_run_stdio_tool_success(mock_docker_service, mock_console, enhanced_cli):
    """Test successful stdio tool execution."""
    # Mock Docker service response
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'completed',
        'stdout': '{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "Success!"}]}}',
        'stderr': '',
        'executed_at': '2024-01-01T00:00:00'
    }

    # Run the tool
    result = enhanced_cli.run_stdio_tool(
        'github', 
        'search_repositories',
        '{"query": "python"}',
        {'GITHUB_TOKEN': 'test_token'}
    )

    # Verify the call was made correctly
    mock_docker_instance.run_stdio_command.assert_called_once()
    assert result is True


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_run_stdio_tool_template_not_found(mock_docker_service, mock_console, enhanced_cli):
    """Test stdio tool execution with non-existent template."""
    result = enhanced_cli.run_stdio_tool('nonexistent', 'tool_name')
    
    assert result is False
    mock_console.print.assert_called_with(
        "[red]❌ Template 'nonexistent' not found[/red]"
    )


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_run_stdio_tool_non_stdio_template(mock_docker_service, mock_console, enhanced_cli):
    """Test stdio tool execution with non-stdio template."""
    result = enhanced_cli.run_stdio_tool('http-template', 'tool_name')
    
    assert result is False
    mock_console.print.assert_called_with(
        "[red]❌ Template 'http-template' does not support stdio transport[/red]"
    )


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_run_stdio_tool_invalid_json_args(mock_docker_service, mock_console, enhanced_cli):
    """Test stdio tool execution with invalid JSON arguments."""
    result = enhanced_cli.run_stdio_tool('github', 'tool_name', 'invalid json')
    
    assert result is False
    mock_console.print.assert_called_with(
        "[red]❌ Invalid JSON in tool arguments: invalid json[/red]"
    )


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_run_stdio_tool_docker_failure(mock_docker_service, mock_console, enhanced_cli):
    """Test stdio tool execution with Docker failure."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'failed',
        'error': 'Docker error',
        'stderr': 'Container failed',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.run_stdio_tool('github', 'tool_name')
    
    assert result is False


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_run_tool(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with run-tool command."""
    args = Namespace(
        command='run-tool',
        template='github',
        tool_name='search_repositories',
        args='{"query": "test"}',
        config=['GITHUB_TOKEN=test'],
        env=['LOG_LEVEL=debug']
    )

    with patch.object(enhanced_cli, 'run_stdio_tool') as mock_run_tool:
        mock_run_tool.return_value = True
        
        result = handle_enhanced_cli_commands(args, enhanced_cli)
        
        assert result is True
        mock_run_tool.assert_called_once_with(
            'github',
            'search_repositories',
            tool_args='{"query": "test"}',
            config_values={'GITHUB_TOKEN': 'test'},
            env_vars={'LOG_LEVEL': 'debug'}
        )


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_tools(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with tools command."""
    args = Namespace(
        command='tools',
        template='github',
        image=None,
        config=['API_KEY=test']
    )

    with patch.object(enhanced_cli, 'list_tools') as mock_list_tools:
        result = handle_enhanced_cli_commands(args, enhanced_cli)
        
        assert result is True
        mock_list_tools.assert_called_once_with(
            'github',
            no_cache=False,
            refresh=False,
            config_values={'API_KEY': 'test'}
        )


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_tools_with_image(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with tools command using image."""
    args = Namespace(
        command='tools',
        template=None,
        image='mcp/filesystem',
        server_args=['/tmp'],
        config=[]
    )

    with patch.object(enhanced_cli, 'discover_tools_from_image') as mock_discover:
        result = handle_enhanced_cli_commands(args, enhanced_cli)
        
        assert result is True
        mock_discover.assert_called_once_with(
            'mcp/filesystem',
            ['/tmp'],
            {}
        )


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_tools_no_args(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with tools command but no args."""
    args = Namespace(
        command='tools',
        template=None,
        image=None,
        config=None
    )

    result = handle_enhanced_cli_commands(args, enhanced_cli)
    
    assert result is False


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.cli.MCPDeployer')
def test_deploy_with_transport_stdio_prevention(mock_deployer, mock_console, enhanced_cli):
    """Test that stdio transport deployment is prevented with helpful message."""
    # Mock tool discovery to return some tools
    with patch.object(enhanced_cli, 'tool_discovery') as mock_tool_discovery:
        mock_discovery_result = {
            'tools': [{'name': 'example'}],
            'discovery_method': 'template_json'
        }
        mock_tool_discovery.discover_tools.return_value = mock_discovery_result

        result = enhanced_cli.deploy_with_transport(
            'github',
            transport='stdio'
        )

        assert result is False
        
        # Check that console.print was called (indicating stdio prevention worked)
        assert mock_console.print.called


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_list_tools_success(mock_docker_service, mock_console, enhanced_cli):
    """Test successful tool listing."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'completed',
        'stdout': json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "search_repositories",
                        "description": "Search for repositories",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"query": {"type": "string"}}
                        }
                    }
                ]
            }
        }),
        'stderr': '',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.list_tools('github')
    assert result is True


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_list_tools_template_not_found(mock_docker_service, mock_console, enhanced_cli):
    """Test tool listing with non-existent template."""
    result = enhanced_cli.list_tools('nonexistent')
    
    assert result is False
    mock_console.print.assert_called_with(
        "[red]❌ Template 'nonexistent' not found[/red]"
    )


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_list_tools_non_stdio_template(mock_docker_service, mock_console, enhanced_cli):
    """Test tool listing with non-stdio template."""
    result = enhanced_cli.list_tools('http-template')
    
    assert result is False
    mock_console.print.assert_called_with(
        "[red]❌ Template 'http-template' does not support stdio transport[/red]"
    )


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_list_tools_docker_failure(mock_docker_service, mock_console, enhanced_cli):
    """Test tool listing with Docker failure."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'failed',
        'error': 'Docker error',
        'stderr': 'Container failed',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.list_tools('github')
    assert result is False


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_list_tools_invalid_json_response(mock_docker_service, mock_console, enhanced_cli):
    """Test tool listing with invalid JSON response."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'completed',
        'stdout': 'invalid json response',
        'stderr': '',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.list_tools('github')
    assert result is False


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_discover_tools_from_image_success(mock_docker_service, mock_console, enhanced_cli):
    """Test successful tool discovery from image."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'completed',
        'stdout': json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "inputSchema": {"type": "object"}
                    }
                ]
            }
        }),
        'stderr': '',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.discover_tools_from_image('test/image', ['arg1'], {})
    assert result is True


@pytest.mark.docker
@patch('mcp_template.cli.console')
@patch('mcp_template.backends.docker.DockerDeploymentService')
def test_discover_tools_from_image_failure(mock_docker_service, mock_console, enhanced_cli):
    """Test tool discovery from image failure."""
    mock_docker_instance = mock_docker_service.return_value
    mock_docker_instance.run_stdio_command.return_value = {
        'status': 'failed',
        'error': 'Container error',
        'stderr': 'Failed to start',
        'executed_at': '2024-01-01T00:00:00'
    }

    result = enhanced_cli.discover_tools_from_image('test/image', ['arg1'], {})
    assert result is False


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_invalid_command(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with invalid command."""
    args = Namespace(command='invalid-command')
    
    result = handle_enhanced_cli_commands(args, enhanced_cli)
    assert result is False


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_run_tool_with_env_vars(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with run-tool and environment variables."""
    args = Namespace(
        command='run-tool',
        template='github',
        tool_name='search_repositories',
        args='{"query": "test"}',
        config=['API_KEY=secret'],
        env=['DEBUG=true', 'LOG_LEVEL=info']
    )

    with patch.object(enhanced_cli, 'run_stdio_tool') as mock_run_tool:
        mock_run_tool.return_value = True
        
        result = handle_enhanced_cli_commands(args, enhanced_cli)
        
        assert result is True
        mock_run_tool.assert_called_once_with(
            'github',
            'search_repositories',
            tool_args='{"query": "test"}',
            config_values={'API_KEY': 'secret'},
            env_vars={'DEBUG': 'true', 'LOG_LEVEL': 'info'}
        )


@pytest.mark.integration
@patch('mcp_template.cli.console')
def test_handle_enhanced_cli_commands_run_tool_no_args(mock_console, enhanced_cli):
    """Test handle_enhanced_cli_commands with run-tool but no arguments."""
    args = Namespace(
        command='run-tool',
        template='github',
        tool_name='search_repositories',
        args=None,
        config=None,
        env=None
    )

    with patch.object(enhanced_cli, 'run_stdio_tool') as mock_run_tool:
        mock_run_tool.return_value = True
        
        result = handle_enhanced_cli_commands(args, enhanced_cli)
        
        assert result is True
        mock_run_tool.assert_called_once_with(
            'github',
            'search_repositories',
            tool_args=None,
            config_values={},
            env_vars={}
        )
