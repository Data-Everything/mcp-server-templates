"""
Tests for cleanup command functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mcp_template.cli import CLI


@pytest.mark.unit
class TestCleanupCommand:
    """Test cleanup command functionality."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return CLI()

    @pytest.fixture
    def mock_args(self):
        """Create mock args for cleanup command."""
        args = Mock()
        args.template = None
        args.all = False
        return args

    def test_cleanup_all_containers_success(self, cli, mock_args):
        """Test successful cleanup of all containers."""
        mock_args.all = True
        
        # Mock successful cleanup results
        cleanup_result = {
            "success": True,
            "cleaned_containers": [
                {"id": "container1", "name": "demo_1", "status": "exited"},
                {"id": "container2", "name": "demo_2", "status": "exited"}
            ],
            "failed_cleanups": [],
            "message": "Cleaned up 2 containers"
        }
        
        images_result = {
            "success": True,
            "cleaned_images": ["img1", "img2"],
            "message": "Cleaned up 2 dangling images"
        }
        
        with patch.object(cli.deployment_manager, 'cleanup_stopped_deployments', return_value=cleanup_result), \
             patch.object(cli.deployment_manager, 'cleanup_dangling_images', return_value=images_result), \
             patch.object(cli.console, 'print') as mock_print:
            
            cli.handle_cleanup_command(mock_args)
            
            # Verify cleanup methods were called
            cli.deployment_manager.cleanup_stopped_deployments.assert_called_once_with()
            cli.deployment_manager.cleanup_dangling_images.assert_called_once_with()

    def test_cleanup_specific_template(self, cli, mock_args):
        """Test cleanup for specific template."""
        mock_args.template = "demo"
        
        cleanup_result = {
            "success": True,
            "cleaned_containers": [
                {"id": "container1", "name": "demo_1", "status": "exited"}
            ],
            "failed_cleanups": [],
            "message": "Cleaned up 1 containers"
        }
        
        with patch.object(cli.deployment_manager, 'cleanup_stopped_deployments', return_value=cleanup_result), \
             patch.object(cli.console, 'print') as mock_print:
            
            cli.handle_cleanup_command(mock_args)
            
            # Verify cleanup was called with template name
            cli.deployment_manager.cleanup_stopped_deployments.assert_called_once_with("demo")

    def test_cleanup_no_containers_found(self, cli, mock_args):
        """Test cleanup when no containers are found."""
        mock_args.all = True
        
        cleanup_result = {
            "success": True,
            "cleaned_containers": [],
            "failed_cleanups": [],
            "message": "No stopped containers to clean up"
        }
        
        images_result = {
            "success": True,
            "cleaned_images": [],
            "message": "No dangling images to clean up"
        }
        
        with patch.object(cli.deployment_manager, 'cleanup_stopped_deployments', return_value=cleanup_result), \
             patch.object(cli.deployment_manager, 'cleanup_dangling_images', return_value=images_result), \
             patch.object(cli.formatter, 'print_info') as mock_info:
            
            cli.handle_cleanup_command(mock_args)
            
            # Verify appropriate messages were shown
            mock_info.assert_any_call("No stopped containers found to clean up")
            mock_info.assert_any_call("No dangling images found to clean up")

    def test_cleanup_with_failures(self, cli, mock_args):
        """Test cleanup with some failures."""
        mock_args.all = True
        
        cleanup_result = {
            "success": True,  # success=True but with failed_cleanups to trigger warning
            "cleaned_containers": [
                {"id": "container1", "name": "demo_1", "status": "exited"}
            ],
            "failed_cleanups": [
                {
                    "container": {"id": "container2", "name": "demo_2", "status": "exited"},
                    "error": "Permission denied"
                }
            ],
            "message": "Cleaned up 1 containers"
        }
        
        images_result = {
            "success": True,
            "cleaned_images": [],
            "message": "No dangling images to clean up"
        }
        
        with patch.object(cli.deployment_manager, 'cleanup_stopped_deployments', return_value=cleanup_result), \
             patch.object(cli.deployment_manager, 'cleanup_dangling_images', return_value=images_result), \
             patch.object(cli.formatter, 'print_warning') as mock_warning:
            
            cli.handle_cleanup_command(mock_args)
            
            # Verify warning was shown for failures
            mock_warning.assert_called()

    def test_cleanup_error_handling(self, cli, mock_args):
        """Test error handling in cleanup command."""
        mock_args.all = True
        
        with patch.object(cli.deployment_manager, 'cleanup_stopped_deployments', side_effect=Exception("Test error")), \
             patch.object(cli.formatter, 'print_error') as mock_error, \
             pytest.raises(SystemExit):
            
            cli.handle_cleanup_command(mock_args)
            
            mock_error.assert_called_with("Error during cleanup: Test error")

    def test_cleanup_requires_template_or_all(self, cli, mock_args):
        """Test that cleanup requires either template name or --all flag."""
        # Neither template nor all flag set
        mock_args.template = None
        mock_args.all = False
        
        with patch.object(cli.formatter, 'print_error') as mock_error, \
             pytest.raises(SystemExit):
            
            cli.handle_cleanup_command(mock_args)
            
            mock_error.assert_called_with("Please specify a template name or use --all flag")
