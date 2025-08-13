"""
Unit tests for CLI class methods.

Tests the CLI class functionality including method implementations
and configuration handling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from mcp_template.cli import CLI, EnhancedCLI


@pytest.mark.unit
class TestCLIClass:
    """Unit tests for CLI class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cli = CLI()
        self.enhanced_cli = EnhancedCLI()

    def test_show_config_options_method_exists(self):
        """Test that show_config_options method exists and is callable."""
        # This test ensures the method we added exists
        assert hasattr(self.cli, 'show_config_options')
        assert callable(getattr(self.cli, 'show_config_options'))
        
        # Also check in EnhancedCLI
        assert hasattr(self.enhanced_cli, 'show_config_options')
        assert callable(getattr(self.enhanced_cli, 'show_config_options'))

    @patch('rich.console.Console')
    def test_show_config_options_with_template(self, mock_console_class):
        """Test show_config_options with template parameter."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        with patch.object(self.enhanced_cli, 'template_manager') as mock_tm:
            mock_tm.get_template_config_schema.return_value = {
                'properties': {
                    'greeting': {
                        'type': 'string',
                        'description': 'Greeting message',
                        'default': 'Hello'
                    }
                }
            }
            
            # Call the method through EnhancedCLI which is used in the actual command
            self.enhanced_cli.show_config_options("demo")
            
            # Verify it was called
            mock_tm.get_template_config_schema.assert_called_once_with("demo")

    @patch('rich.console.Console')
    def test_show_config_options_no_schema(self, mock_console_class):
        """Test show_config_options when no schema is found."""
        mock_console = Mock()
        mock_console_class.return_value = mock_console
        
        with patch.object(self.enhanced_cli, 'template_manager') as mock_tm:
            mock_tm.get_template_config_schema.return_value = None
            
            # Call the method
            self.enhanced_cli.show_config_options("nonexistent")
            
            # Verify it handled the case gracefully
            mock_tm.get_template_config_schema.assert_called_once_with("nonexistent")

    def test_cli_inheritance_structure(self):
        """Test that CLI classes have proper inheritance structure."""
        # Verify CLI class exists and has expected methods
        assert hasattr(CLI, 'show_config_options')
        assert hasattr(CLI, '_show_config_options')  # private method
        assert hasattr(CLI, 'handle_deploy_command')
        assert hasattr(CLI, 'handle_logs_command')
        assert hasattr(CLI, 'handle_stop_command')
        assert hasattr(CLI, 'handle_list_command')
        
        # Verify EnhancedCLI inherits from CLI
        assert issubclass(EnhancedCLI, CLI)
        assert hasattr(EnhancedCLI, 'show_config_options')

    def test_enhanced_cli_is_used_for_config_command(self):
        """Test that EnhancedCLI is the class used for config command handling."""
        # Import the function that handles enhanced CLI commands
        from mcp_template.cli import handle_enhanced_cli_commands
        
        # Create mock args for config command
        mock_args = Mock()
        mock_args.command = "config"
        mock_args.template = "demo"
        
        with patch('mcp_template.cli.EnhancedCLI') as mock_enhanced_cli_class:
            mock_enhanced_cli = Mock()
            mock_enhanced_cli_class.return_value = mock_enhanced_cli
            
            # Call the enhanced CLI handler
            result = handle_enhanced_cli_commands(mock_args)
            
            # Verify it handled the config command
            assert result is True
            mock_enhanced_cli_class.assert_called_once()
            mock_enhanced_cli.show_config_options.assert_called_once_with("demo")
