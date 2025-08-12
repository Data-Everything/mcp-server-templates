"""
Unit tests for DeploymentManager.

Tests the deployment lifecycle management and coordination
provided by the DeploymentManager common module.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from mcp_template.core.deployment_manager import DeploymentManager, DeploymentOptions, DeploymentResult


@pytest.mark.unit
class TestDeploymentManager:
    """Unit tests for DeploymentManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployment_manager = DeploymentManager(backend_type="mock")

    def test_deploy_template_basic(self):
        """Test basic template deployment."""
        template_name = "demo"
        config_sources = {"config_values": {"greeting": "Hello"}}
        options = DeploymentOptions(name="test-demo")
        
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=True):
            with patch.object(self.deployment_manager.template_manager, 'get_template_info') as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {}
                }
                
                with patch.object(self.deployment_manager.config_manager, 'merge_config_sources') as mock_merge:
                    mock_merge.return_value = {"greeting": "Hello"}
                    
                    with patch.object(self.deployment_manager.config_manager, 'validate_config') as mock_validate:
                        mock_validate.return_value = {"valid": True}
                        
                        # Mock backend deployment - use the correct method name
                        with patch.object(self.deployment_manager.backend, 'deploy_template') as mock_deploy:
                            mock_deploy.return_value = {
                                "deployment_name": "demo-123",
                                "template_id": "demo", 
                                "status": "deployed",
                                "container_id": "container-123"
                            }
                            
                            result = self.deployment_manager.deploy_template(template_name, config_sources, options)
        
        assert result.success is True
        assert result.deployment_id == "demo-123"

    def test_deploy_template_invalid_template(self):
        """Test deployment with invalid template."""
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=False):
            config_sources = {}
            options = DeploymentOptions()
            
            result = self.deployment_manager.deploy_template("invalid", config_sources, options)
        
        assert result.success is False
        assert "not found or invalid" in result.error

    def test_deploy_template_config_validation_failure(self):
        """Test deployment with config validation failure."""
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=True):
            with patch.object(self.deployment_manager.template_manager, 'get_template_info') as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {"required": ["required_field"]}
                }
                
                with patch.object(self.deployment_manager.config_manager, 'merge_config_sources') as mock_merge:
                    mock_merge.return_value = {"greeting": "Hello"}  # Missing required_field
                    
                    with patch.object(self.deployment_manager.config_manager, 'validate_config') as mock_validate:
                        mock_validate.return_value = {
                            "valid": False,
                            "errors": ["Required field 'required_field' is missing"]
                        }
                        
                        config_sources = {}
                        options = DeploymentOptions()
                        
                        result = self.deployment_manager.deploy_template("demo", config_sources, options)
        
        assert result.success is False
        assert "Configuration validation failed" in result.error

    def test_stop_deployment_success(self):
        """Test successful deployment stop."""
        deployment_id = "demo-123"
        
        # Mock finding the deployment
        mock_deployment_info = {
            "name": deployment_id,
            "template": "demo",
            "status": "running"
        }
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'delete_deployment', return_value=True):
                result = self.deployment_manager.stop_deployment(deployment_id)
        
        assert result.success is True
        assert deployment_id in result.stopped_deployments

    def test_stop_deployment_not_found(self):
        """Test stopping non-existent deployment."""
        deployment_id = "nonexistent"
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status', side_effect=ValueError("Not found")):
            result = self.deployment_manager.stop_deployment(deployment_id)
        
        assert result.success is False
        assert "not found" in result.error

    def test_stop_deployment_with_force(self):
        """Test force stopping deployment."""
        deployment_id = "demo-123"
        
        mock_deployment_info = {
            "name": deployment_id,
            "template": "demo",
            "status": "running"
        }
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'delete_deployment', return_value=True):
                result = self.deployment_manager.stop_deployment(deployment_id, force=True)
        
        assert result.success is True

    def test_stop_deployments_bulk(self):
        """Test bulk deployment stopping."""
        deployment_ids = ["demo-123", "demo-456"]
        
        mock_deployment_info = {
            "name": "demo-123",
            "template": "demo", 
            "status": "running"
        }
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'delete_deployment', return_value=True):
                results = self.deployment_manager.stop_deployments(deployment_ids)
        
        assert len(results) == 2
        assert all(result.success for result in results)

    def test_get_deployment_logs_success(self):
        """Test successful log retrieval."""
        deployment_id = "demo-123"
        mock_logs = "Sample log output"
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status') as mock_status:
            mock_status.return_value = {"name": deployment_id, "status": "running"}
            
            # Mock the actual log method in the deployment manager
            with patch.object(self.deployment_manager, '_get_logs_from_backend', return_value=mock_logs):
                logs = self.deployment_manager.get_deployment_logs(deployment_id)
        
        assert logs == mock_logs

    def test_get_deployment_logs_not_found(self):
        """Test log retrieval for non-existent deployment.""" 
        deployment_id = "nonexistent"
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status', side_effect=ValueError("Not found")):
            with pytest.raises(ValueError, match="not found"):
                self.deployment_manager.get_deployment_logs(deployment_id)

    def test_stream_deployment_logs(self):
        """Test log streaming functionality."""
        deployment_id = "demo-123"
        
        def mock_log_generator():
            yield "Log line 1"
            yield "Log line 2"
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_status') as mock_status:
            mock_status.return_value = {"name": deployment_id, "status": "running"}
            
            with patch.object(self.deployment_manager, '_stream_logs_from_backend', return_value=mock_log_generator()):
                logs = list(self.deployment_manager.stream_deployment_logs(deployment_id))
        
        assert len(logs) == 2
        assert "Log line 1" in logs

    def test_find_deployments_by_criteria(self):
        """Test finding deployments by criteria."""
        mock_deployments = [
            {"name": "demo-123", "template": "demo", "status": "running"},
            {"name": "demo-456", "template": "demo", "status": "stopped"},
            {"name": "other-789", "template": "other", "status": "running"}
        ]
        
        with patch.object(self.deployment_manager.backend, 'list_deployments', return_value=mock_deployments):
            # Find running demo deployments
            found = self.deployment_manager.find_deployments_by_criteria(
                template="demo", 
                status="running"
            )
        
        assert len(found) == 1
        assert found[0]["name"] == "demo-123"

    def test_find_deployment_for_logs(self):
        """Test finding deployment for log retrieval."""
        template_name = "demo"
        
        mock_deployments = [
            {"name": "demo-123", "template": "demo", "status": "running"}
        ]
        
        with patch.object(self.deployment_manager, 'find_deployments_by_criteria', return_value=mock_deployments):
            deployment_id = self.deployment_manager.find_deployment_for_logs(template_name)
        
        assert deployment_id == "demo-123"

    def test_deployment_options(self):
        """Test DeploymentOptions data class."""
        options = DeploymentOptions(
            name="test-deployment",
            force=True,
            pull_image=False,
            environment={"VAR": "value"}
        )
        
        assert options.name == "test-deployment"
        assert options.force is True
        assert options.pull_image is False
        assert options.environment["VAR"] == "value"

    def test_deployment_result(self):
        """Test DeploymentResult data class."""
        result = DeploymentResult(
            success=True,
            deployment_id="demo-123",
            template="demo",
            message="Deployment successful"
        )
        
        assert result.success is True
        assert result.deployment_id == "demo-123"
        assert result.template == "demo"
        assert result.message == "Deployment successful"


@pytest.mark.integration  
class TestDeploymentManagerIntegration:
    """Integration tests for DeploymentManager."""

    def test_deployment_manager_with_real_backend(self):
        """Test deployment manager with actual backend."""
        deployment_manager = DeploymentManager(backend_type="mock")
        
        # Should initialize without errors
        assert deployment_manager.backend is not None
        assert deployment_manager.template_manager is not None
        assert deployment_manager.config_manager is not None

    def test_deployment_error_handling(self):
        """Test deployment error handling."""
        deployment_manager = DeploymentManager(backend_type="mock") 
        
        # Test with invalid template should return failed result
        result = deployment_manager.deploy_template("nonexistent", {}, DeploymentOptions())
        assert result.success is False
        assert result.error is not None

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from mcp_template.core.deployment_manager import (
    DeploymentManager,
    DeploymentOptions,
    DeploymentResult
)


@pytest.mark.unit
class TestDeploymentManager:
    """Unit tests for DeploymentManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployment_manager = DeploymentManager(backend_type="mock")

    def test_deploy_template_basic(self):
        """Test basic template deployment."""
        # Mock template validation
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=True):
            with patch.object(self.deployment_manager.template_manager, 'get_template_info') as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {}
                }
                
                # Mock config operations
                with patch.object(self.deployment_manager.config_manager, 'merge_config_sources') as mock_merge:
                    mock_merge.return_value = {"greeting": "Hello"}
                    
                    with patch.object(self.deployment_manager.config_manager, 'validate_config') as mock_validate:
                        mock_validate.return_value = {"valid": True}
                        
                        # Mock backend deployment
                        with patch.object(self.deployment_manager.backend, 'deploy') as mock_deploy:
                            mock_deploy.return_value = {
                                "success": True,
                                "deployment_id": "demo-123",
                                "template": "demo",
                                "status": "running"
                            }
                            
                            config_sources = {"config_values": {"greeting": "Hello"}}
                            options = DeploymentOptions(name="test-demo")
                            
                            result = self.deployment_manager.deploy_template("demo", config_sources, options)
        
        assert result.success is True
        assert result.deployment_id == "demo-123"
        assert result.template == "demo"

    def test_deploy_template_invalid_template(self):
        """Test deployment with invalid template."""
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=False):
            config_sources = {}
            options = DeploymentOptions()
            
            result = self.deployment_manager.deploy_template("invalid", config_sources, options)
        
        assert result.success is False
        assert "not found or invalid" in result.error

    def test_deploy_template_config_validation_failure(self):
        """Test deployment with config validation failure."""
        with patch.object(self.deployment_manager.template_manager, 'validate_template', return_value=True):
            with patch.object(self.deployment_manager.template_manager, 'get_template_info') as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {"required": ["required_field"]}
                }
                
                with patch.object(self.deployment_manager.config_manager, 'merge_config_sources') as mock_merge:
                    mock_merge.return_value = {"greeting": "Hello"}  # Missing required_field
                    
                    with patch.object(self.deployment_manager.config_manager, 'validate_config') as mock_validate:
                        mock_validate.return_value = {
                            "valid": False,
                            "errors": ["Required field 'required_field' is missing"]
                        }
                        
                        config_sources = {}
                        options = DeploymentOptions()
                        
                        result = self.deployment_manager.deploy_template("demo", config_sources, options)
        
        assert result.success is False
        assert "Configuration validation failed" in result.error

    def test_stop_deployment_success(self):
        """Test successful deployment stop."""
        mock_deployment_info = {
            "id": "demo-123",
            "template": "demo",
            "status": "running"
        }
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_info', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'stop_deployment', return_value=True):
                result = self.deployment_manager.stop_deployment("demo-123")
        
        assert result["success"] is True
        assert result["deployment_id"] == "demo-123"
        assert "demo-123" in result["stopped_deployments"]

    def test_stop_deployment_not_found(self):
        """Test stopping non-existent deployment."""
        with patch.object(self.deployment_manager.backend, 'get_deployment_info', return_value=None):
            result = self.deployment_manager.stop_deployment("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_stop_deployment_with_force(self):
        """Test force stopping deployment."""
        mock_deployment_info = {
            "id": "demo-123",
            "template": "demo",
            "status": "running"
        }
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_info', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'stop_deployment', return_value=False):
                with patch.object(self.deployment_manager.backend, 'force_stop_deployment', return_value=True):
                    result = self.deployment_manager.stop_deployment("demo-123", force=True)
        
        assert result["success"] is True

    def test_stop_deployments_bulk(self):
        """Test bulk deployment stopping."""
        deployment_ids = ["demo-123", "demo-456", "invalid-789"]
        
        def mock_stop_deployment(deployment_id, timeout, force):
            if deployment_id == "invalid-789":
                return {
                    "success": False,
                    "error": "Deployment not found",
                    "duration": 0.1
                }
            else:
                return {
                    "success": True,
                    "deployment_id": deployment_id,
                    "stopped_deployments": [deployment_id],
                    "duration": 0.5
                }
        
        with patch.object(self.deployment_manager, 'stop_deployment', side_effect=mock_stop_deployment):
            result = self.deployment_manager.stop_deployments_bulk(deployment_ids)
        
        assert result["success"] is False  # Because one failed
        assert len(result["stopped_deployments"]) == 2
        assert len(result["failed_deployments"]) == 1

    def test_get_deployment_logs_success(self):
        """Test successful log retrieval."""
        mock_deployment_info = {
            "id": "demo-123",
            "template": "demo"
        }
        
        mock_logs = "2024-01-01 10:00:00 [INFO] Server started\n2024-01-01 10:00:01 [INFO] Ready for connections"
        
        with patch.object(self.deployment_manager.backend, 'get_deployment_info', return_value=mock_deployment_info):
            with patch.object(self.deployment_manager.backend, 'get_deployment_logs', return_value=mock_logs):
                result = self.deployment_manager.get_deployment_logs("demo-123", lines=50)
        
        assert result["success"] is True
        assert result["logs"] == mock_logs
        assert result["lines_returned"] == 2

    def test_get_deployment_logs_not_found(self):
        """Test log retrieval for non-existent deployment."""
        with patch.object(self.deployment_manager.backend, 'get_deployment_info', return_value=None):
            result = self.deployment_manager.get_deployment_logs("nonexistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_stream_deployment_logs(self):
        """Test log streaming functionality."""
        log_lines = []
        
        def callback(line):
            log_lines.append(line)
        
        with patch.object(self.deployment_manager.backend, 'stream_deployment_logs') as mock_stream:
            self.deployment_manager.stream_deployment_logs("demo-123", callback)
            mock_stream.assert_called_once_with("demo-123", callback, 100)

    def test_find_deployments_by_criteria(self):
        """Test finding deployments by various criteria."""
        mock_deployments = [
            {"id": "demo-123", "template": "demo", "name": "my-demo"},
            {"id": "demo-456", "template": "demo", "name": "another-demo"},
            {"id": "fs-789", "template": "filesystem", "name": "my-fs"}
        ]
        
        with patch.object(self.deployment_manager.backend, 'list_all_deployments', return_value=mock_deployments):
            # Filter by template name
            results = self.deployment_manager.find_deployments_by_criteria(template_name="demo")
            assert len(results) == 2
            
            # Filter by custom name
            results = self.deployment_manager.find_deployments_by_criteria(custom_name="my-demo")
            assert len(results) == 1
            assert results[0]["id"] == "demo-123"
            
            # Filter by deployment ID
            results = self.deployment_manager.find_deployments_by_criteria(deployment_id="fs-789")
            assert len(results) == 1
            assert results[0]["template"] == "filesystem"

    def test_find_deployment_for_logs(self):
        """Test finding deployment for log operations."""
        mock_deployments = [
            {"id": "demo-123", "template": "demo", "name": "my-demo"}
        ]
        
        with patch.object(self.deployment_manager, 'find_deployments_by_criteria', return_value=mock_deployments):
            deployment_id = self.deployment_manager.find_deployment_for_logs(template_name="demo")
            assert deployment_id == "demo-123"
            
            deployment_id = self.deployment_manager.find_deployment_for_logs(custom_name="my-demo")
            assert deployment_id == "demo-123"
        
        # Test with no deployments found
        with patch.object(self.deployment_manager, 'find_deployments_by_criteria', return_value=[]):
            deployment_id = self.deployment_manager.find_deployment_for_logs(template_name="nonexistent")
            assert deployment_id is None

    def test_deployment_options(self):
        """Test DeploymentOptions class."""
        options = DeploymentOptions(
            name="test-deployment",
            transport="http",
            port=8080,
            pull_image=False,
            timeout=600
        )
        
        assert options.name == "test-deployment"
        assert options.transport == "http"
        assert options.port == 8080
        assert options.pull_image is False
        assert options.timeout == 600

    def test_deployment_result(self):
        """Test DeploymentResult class."""
        result = DeploymentResult(
            success=True,
            deployment_id="demo-123",
            template="demo",
            status="running",
            container_id="abc123",
            image="demo:latest",
            ports={"7071": 7071},
            config={"greeting": "Hello"},
            transport="http",
            endpoint="http://localhost:7071",
            duration=5.2
        )
        
        assert result.success is True
        assert result.deployment_id == "demo-123"
        assert result.duration == 5.2
        
        # Test to_dict conversion
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["deployment_id"] == "demo-123"
        assert result_dict["ports"]["7071"] == 7071


@pytest.mark.integration
class TestDeploymentManagerIntegration:
    """Integration tests for DeploymentManager."""

    def test_deployment_manager_with_real_backend(self):
        """Test deployment manager with mock backend."""
        deployment_manager = DeploymentManager(backend_type="mock")
        
        # Should be able to find deployments without errors
        deployments = deployment_manager.find_deployments_by_criteria()
        assert isinstance(deployments, list)

    def test_deployment_error_handling(self):
        """Test deployment error handling in integration scenarios."""
        deployment_manager = DeploymentManager(backend_type="mock")
        
        # Test with invalid configuration
        config_sources = {"config_values": {"invalid": "config"}}
        options = DeploymentOptions()
        
        result = deployment_manager.deploy_template("nonexistent", config_sources, options)
        assert result.success is False
        assert result.error is not None
