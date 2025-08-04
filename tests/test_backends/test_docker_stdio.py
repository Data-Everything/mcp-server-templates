"""
Tests for Docker backend stdio command functionality.
"""

import json
import subprocess
import unittest
from unittest.mock import MagicMock, Mock, patch

from mcp_template.backends.docker import DockerDeploymentService


class TestDockerStdioCommands(unittest.TestCase):
    """Test Docker backend stdio command execution."""

    def setUp(self):
        """Set up test fixtures."""
        with patch.object(DockerDeploymentService, '_ensure_docker_available'):
            self.docker_service = DockerDeploymentService()

    def test_run_stdio_command_success(self):
        """Test successful stdio command execution."""
        template_id = 'github'
        config = {'port': 8080}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github'],
            'environment': {}
        }
        json_input = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_repositories",
                "arguments": {"query": "python"}
            }
        })

        expected_stdout = json.dumps({"result": "success"})

        # Mock subprocess.run for Docker pull and execution
        with patch('subprocess.run') as mock_run:
            # Mock successful Docker pull
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull
                Mock(returncode=0, stdout=expected_stdout, stderr='')  # Docker run
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'completed')
            self.assertEqual(result['stdout'], expected_stdout)
            self.assertEqual(result['template_id'], template_id)

            # Verify Docker commands were called
            self.assertEqual(mock_run.call_count, 2)
            
            # Verify Docker pull was called
            pull_call = mock_run.call_args_list[0]
            self.assertIn('docker', pull_call[0][0])
            self.assertIn('pull', pull_call[0][0])
            self.assertIn('test/github:latest', pull_call[0][0])

            # Verify Docker run was called with proper MCP sequence
            run_call = mock_run.call_args_list[1]
            self.assertIn('/bin/bash', run_call[0][0])
            self.assertIn('-c', run_call[0][0])
            
            # Verify the bash command contains proper MCP handshake
            bash_command = run_call[0][0][2]
            self.assertIn('docker run -i --rm', bash_command)
            self.assertIn('initialize', bash_command)
            self.assertIn('notifications/initialized', bash_command)

    def test_run_stdio_command_docker_failure(self):
        """Test stdio command execution with Docker failure."""
        template_id = 'github'
        config = {}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github']
        }
        json_input = '{"jsonrpc": "2.0", "method": "test"}'

        with patch('subprocess.run') as mock_run:
            # Mock Docker pull success, run failure
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull success
                subprocess.CalledProcessError(1, 'docker run')  # Docker run failure
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'failed')
            self.assertIn('docker run', str(result['error']))
            self.assertEqual(result['template_id'], template_id)

    def test_run_stdio_command_skip_pull(self):
        """Test stdio command execution without pulling image."""
        template_id = 'github'
        config = {}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github']
        }
        json_input = '{"jsonrpc": "2.0", "method": "test"}'

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0, 
                stdout='{"result": "success"}', 
                stderr=''
            )

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input, pull_image=False
            )

            self.assertEqual(result['status'], 'completed')
            
            # Verify only one call (no pull, just run)
            self.assertEqual(mock_run.call_count, 1)

    def test_run_stdio_command_invalid_json_input(self):
        """Test stdio command execution with invalid JSON input."""
        template_id = 'github'
        config = {}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github']
        }
        json_input = 'invalid json'

        with patch('subprocess.run') as mock_run:
            # Don't need to mock since invalid JSON is caught before subprocess
            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'failed')
            self.assertIn('Invalid JSON input', result['error'])

    def test_run_stdio_command_with_environment_variables(self):
        """Test stdio command execution with environment variables."""
        template_id = 'github'
        config = {'GITHUB_TOKEN': 'test-token'}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github'],
            'env_vars': {'LOG_LEVEL': 'debug'}
        }
        json_input = json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "test"}
        })

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull
                Mock(returncode=0, stdout='{"result": "success"}', stderr='')  # Docker run
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'completed')
            
            # Verify environment variables were passed to Docker
            run_call = mock_run.call_args_list[1]
            bash_command = run_call[0][0][2]
            self.assertIn('--env GITHUB_TOKEN=test-token', bash_command)
            self.assertIn('--env LOG_LEVEL=debug', bash_command)

    def test_run_stdio_command_with_volumes(self):
        """Test stdio command execution with volume mounts."""
        template_id = 'filesystem'
        config = {'data_dir': '/custom/data'}
        template_data = {
            'image': 'test/filesystem:latest',
            'command': ['mcp-server-filesystem'],
            'volumes': {'/tmp/test-data': '/mnt/data'}
        }
        json_input = json.dumps({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": "list_files"}
        })

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull
                Mock(returncode=0, stdout='{"result": "success"}', stderr='')  # Docker run
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'completed')
            
            # Verify volume mounts were passed to Docker
            run_call = mock_run.call_args_list[1]
            bash_command = run_call[0][0][2]
            self.assertIn('--volume /tmp/test-data:/mnt/data', bash_command)

    def test_mcp_handshake_sequence(self):
        """Test that proper MCP handshake sequence is generated."""
        template_id = 'github'
        config = {}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github']
        }
        
        # Test tool call JSON
        tool_call = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_repositories",
                "arguments": {"query": "python"}
            }
        }
        json_input = json.dumps(tool_call)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull
                Mock(returncode=0, stdout='{"result": "success"}', stderr='')  # Docker run
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            # Verify the MCP handshake sequence was built correctly
            run_call = mock_run.call_args_list[1]
            bash_command = run_call[0][0][2]
            
            # Should contain initialize request
            self.assertIn('"method": "initialize"', bash_command)
            self.assertIn('"protocolVersion": "2024-11-05"', bash_command)
            
            # Should contain initialized notification
            self.assertIn('"method": "notifications/initialized"', bash_command)
            
            # Should contain the original tool call
            self.assertIn('"method": "tools/call"', bash_command)
            self.assertIn('"name": "search_repositories"', bash_command)

    def test_run_stdio_command_timeout(self):
        """Test stdio command execution with timeout."""
        template_id = 'github'
        config = {}
        template_data = {
            'image': 'test/github:latest',
            'command': ['mcp-server-github']
        }
        json_input = '{"jsonrpc": "2.0", "method": "test"}'

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout='', stderr=''),  # Docker pull
                subprocess.TimeoutExpired('docker run', 30)  # Timeout
            ]

            result = self.docker_service.run_stdio_command(
                template_id, config, template_data, json_input
            )

            self.assertEqual(result['status'], 'error')
            self.assertIn('timed out', str(result['error']))


if __name__ == '__main__':
    unittest.main()
