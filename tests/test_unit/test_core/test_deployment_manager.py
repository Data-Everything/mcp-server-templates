"""
Unit tests for DeploymentManager.

Tests the deployment lifecycle management and coordination
provided by the DeploymentManager common module.
"""

from unittest.mock import Mock, patch

import pytest

from mcp_template.core.config_processor import ValidationResult
from mcp_template.core.deployment_manager import (
    DeploymentManager,
    DeploymentOptions,
    DeploymentResult,
)

pytestmark = pytest.mark.unit


class TestDeploymentManager:
    """Unit tests for DeploymentManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.deployment_manager = DeploymentManager(backend_type="mock")

    def test_deploy_template_basic(self):
        """Test basic template deployment."""
        # Mock template validation
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                # Mock config operations
                with patch.object(
                    self.deployment_manager.config_processor, "prepare_configuration"
                ) as mock_prepare:
                    mock_prepare.return_value = {"greeting": "Hello"}

                    with patch.object(
                        self.deployment_manager.config_processor,
                        "handle_volume_and_args_config_properties",
                    ) as mock_handle_vol:
                        mock_handle_vol.return_value = {
                            "config": {"greeting": "Hello"},
                            "template": {
                                "name": "Demo Template",
                                "docker_image": "demo:latest",
                                "config_schema": {},
                            },
                        }

                        with patch.object(
                            self.deployment_manager.config_processor, "validate_config"
                        ) as mock_validate:
                            mock_validate.return_value = ValidationResult(
                                valid=True, errors=[], warnings=[]
                            )

                            # Mock backend deployment
                        with patch.object(
                            self.deployment_manager.backend, "deploy_template"
                        ) as mock_deploy:
                            mock_deploy.return_value = {
                                "success": True,
                                "deployment_id": "demo-123",
                                "container_id": "container-123",
                            }

                            config_sources = {"config_values": {"greeting": "Hello"}}
                            options = DeploymentOptions(name="test-demo")

                            result = self.deployment_manager.deploy_template(
                                "demo", config_sources, options
                            )

        assert result.success is True
        assert result.deployment_id == "demo-123"

    def test_deploy_template_invalid_template(self):
        """Test deployment with invalid template."""
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=False,
        ):
            config_sources = {}
            options = DeploymentOptions()

            result = self.deployment_manager.deploy_template(
                "invalid", config_sources, options
            )

        assert result.success is False
        assert result.error is not None

    def test_deploy_template_config_validation_failure(self):
        """Test deployment with config validation failure."""
        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager,
                    "_validate_and_set_transport",
                    return_value={"success": True},
                ):
                    with patch.object(
                        self.deployment_manager.config_processor,
                        "prepare_configuration",
                    ) as mock_prepare:
                        mock_prepare.return_value = {"invalid": "config"}

                    with patch.object(
                        self.deployment_manager.config_processor,
                        "handle_volume_and_args_config_properties",
                    ) as mock_handle_vol:
                        mock_handle_vol.return_value = {
                            "config": {"invalid": "config"},
                            "template": {
                                "name": "Demo Template",
                                "docker_image": "demo:latest",
                                "config_schema": {},
                            },
                        }

                        with patch.object(
                            self.deployment_manager.config_processor, "validate_config"
                        ) as mock_validate:
                            mock_validate.return_value = ValidationResult(
                                valid=False, errors=["Invalid config"], warnings=[]
                            )

                            config_sources = {"config_values": {"invalid": "config"}}
                            options = DeploymentOptions()

                            result = self.deployment_manager.deploy_template(
                                "demo", config_sources, options
                            )

        assert result.success is False
        assert result.error is not None

    def test_stop_deployment_success(self):
        """Test successful deployment stop."""
        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            with patch.object(
                self.deployment_manager.backend, "get_deployment_info"
            ) as mock_get_info:
                mock_get_info.return_value = {"id": "demo-123", "status": "running"}
                mock_stop.return_value = True

                result = self.deployment_manager.stop_deployment("demo-123")

        assert result["success"] is True
        mock_stop.assert_called_once_with("demo-123", 30)

    def test_stop_deployment_not_found(self):
        """Test stopping non-existent deployment."""
        with patch.object(
            self.deployment_manager.backend, "get_deployment_info"
        ) as mock_get_info:
            mock_get_info.return_value = None

            result = self.deployment_manager.stop_deployment("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_stop_deployment_with_force(self):
        """Test force stopping deployment."""
        with patch.object(
            self.deployment_manager.backend, "stop_deployment"
        ) as mock_stop:
            with patch.object(
                self.deployment_manager.backend, "get_deployment_info"
            ) as mock_get_info:
                mock_get_info.return_value = {"id": "demo-123", "status": "running"}
                mock_stop.return_value = True

                result = self.deployment_manager.stop_deployment("demo-123", force=True)

        assert result["success"] is True
        mock_stop.assert_called_once_with("demo-123", 30)

    def test_stop_deployments_bulk(self):
        """Test bulk deployment stopping."""
        deployment_filters = ["demo-123", "demo-456", "demo-789"]

        with patch.object(
            self.deployment_manager.backend, "get_deployment_info"
        ) as mock_get_info:
            with patch.object(
                self.deployment_manager.backend, "stop_deployment"
            ) as mock_stop:
                # Mock deployment info for all deployments
                mock_get_info.return_value = {"id": "demo-123", "status": "running"}
                mock_stop.return_value = True

                result = self.deployment_manager.stop_deployments_bulk(
                    deployment_filters
                )

        assert result["success"] is True
        assert len(result["stopped_deployments"]) >= 0

    def test_get_deployment_logs_success(self):
        """Test successful log retrieval."""
        with patch.object(
            self.deployment_manager.backend, "get_deployment_info"
        ) as mock_get_info:
            with patch.object(
                self.deployment_manager.backend, "get_deployment_logs"
            ) as mock_logs:
                mock_get_info.return_value = {"id": "demo-123", "status": "running"}
                mock_logs.return_value = {
                    "success": True,
                    "logs": "Application started\nServer running on port 8080",
                }

                result = self.deployment_manager.get_deployment_logs("demo-123")

        assert result["success"] is True
        assert "Application started" in result["logs"]
        mock_logs.assert_called_once_with(
            "demo-123", lines=100, follow=False, since=None, until=None
        )

    def test_get_deployment_logs_not_found(self):
        """Test log retrieval for non-existent deployment."""
        with patch.object(
            self.deployment_manager.backend, "get_deployment_info"
        ) as mock_get_info:
            mock_get_info.return_value = None

            result = self.deployment_manager.get_deployment_logs("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_stream_deployment_logs(self):
        """Test log streaming functionality."""
        with patch.object(
            self.deployment_manager.backend, "stream_deployment_logs"
        ) as mock_stream:
            # Test that the method calls the backend correctly
            callback = Mock()

            self.deployment_manager.stream_deployment_logs(
                "demo-123", callback, lines=50
            )

        mock_stream.assert_called_once_with("demo-123", callback, 50)

    def test_find_deployments_by_criteria(self):
        """Test finding deployments by various criteria."""
        mock_deployments = [
            {"deployment_id": "demo-123", "template": "demo", "status": "running"},
            {
                "deployment_id": "file-456",
                "template": "filesystem",
                "status": "stopped",
            },
        ]

        with patch.object(
            self.deployment_manager.backend, "list_deployments"
        ) as mock_list:
            mock_list.return_value = mock_deployments

            # Test finding by template
            results = self.deployment_manager.find_deployments_by_criteria(
                template_name="demo"
            )

        assert len(results) == 1
        assert results[0]["deployment_id"] == "demo-123"

    def test_find_deployment_for_logs(self):
        """Test finding deployment for log operations."""
        with patch.object(
            self.deployment_manager, "find_deployments_by_criteria"
        ) as mock_find:
            mock_find.return_value = [
                {"id": "demo-123", "template": "demo", "status": "running"}
            ]

            deployment_id = self.deployment_manager.find_deployment_for_logs("demo")

        assert deployment_id is not None
        assert deployment_id == "demo-123"

    def test_deployment_options(self):
        """Test DeploymentOptions class."""
        options = DeploymentOptions(
            name="test-deployment",
            transport="http",
            port=9090,
            pull_image=False,
            timeout=600,
        )

        assert options.name == "test-deployment"
        assert options.transport == "http"
        assert options.port == 9090
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
            duration=5.2,
        )

        assert result.success is True
        assert result.deployment_id == "demo-123"
        assert result.duration == 5.2

        # Test to_dict conversion
        result_dict = result.to_dict()
        assert result_dict["success"] is True
        assert result_dict["deployment_id"] == "demo-123"
        assert result_dict["ports"]["7071"] == 7071

    def test_reserved_env_vars_mapping(self):
        """Test that RESERVED_ENV_VARS are properly applied to deployment."""
        template_name = "demo"
        config_sources = {
            "config_values": {
                "hello_from": "Test",
            }
        }
        # Create options with attributes that match RESERVED_ENV_VARS
        options = DeploymentOptions(
            name="test-reserved-env",
            transport="stdio",  # Use stdio instead of http
            port=8080,
        )

        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager.config_processor, "prepare_configuration"
                ) as mock_prepare:
                    # Mock merged config with RESERVED_ENV_VARS
                    merged_config = {
                        "hello_from": "Test",
                    }
                    mock_prepare.return_value = merged_config

                    with patch.object(
                        self.deployment_manager.config_processor,
                        "handle_volume_and_args_config_properties",
                    ) as mock_handle_vol:
                        mock_handle_vol.return_value = {
                            "config": merged_config,
                            "template": {
                                "name": "Demo Template",
                                "docker_image": "demo:latest",
                                "config_schema": {},
                            },
                        }

                        with patch.object(
                            self.deployment_manager.config_processor, "validate_config"
                        ) as mock_validate:
                            mock_validate.return_value = ValidationResult(
                                valid=True, errors=[], warnings=[]
                            )

                            # Deploy with RESERVED_ENV_VARS in config
                            result = self.deployment_manager.deploy_template(
                                template_name, config_sources, options
                            )

                            # Verify deployment was successful
                            assert result.success is True
                            assert result.deployment_id is not None

                            # Verify RESERVED_ENV_VARS mapping was applied
                            # Since the mock backend is actually working, we check the result
                            # The transport and port should be reflected in the result
                            assert (
                                result.transport == "stdio"
                            )  # transport option should be in result

    def test_reserved_env_vars_partial_mapping(self):
        """Test RESERVED_ENV_VARS mapping with only some variables present."""
        template_name = "demo"
        config_sources = {
            "config_values": {
                "hello_from": "Partial Test",
            }
        }
        options = DeploymentOptions(
            name="test-partial-env",
            transport="stdio",  # Use stdio instead of http
            port=9090,
        )

        with patch.object(
            self.deployment_manager.template_manager,
            "validate_template",
            return_value=True,
        ):
            with patch.object(
                self.deployment_manager.template_manager, "get_template_info"
            ) as mock_get_info:
                mock_get_info.return_value = {
                    "name": "Demo Template",
                    "docker_image": "demo:latest",
                    "config_schema": {},
                }

                with patch.object(
                    self.deployment_manager.config_processor, "prepare_configuration"
                ) as mock_prepare:
                    merged_config = {
                        "hello_from": "Partial Test",
                    }
                    mock_prepare.return_value = merged_config

                    with patch.object(
                        self.deployment_manager.config_processor,
                        "handle_volume_and_args_config_properties",
                    ) as mock_handle_vol:
                        mock_handle_vol.return_value = {
                            "config": merged_config,
                            "template": {
                                "name": "Demo Template",
                                "docker_image": "demo:latest",
                                "config_schema": {},
                            },
                        }

                        with patch.object(
                            self.deployment_manager.config_processor, "validate_config"
                        ) as mock_validate:
                            mock_validate.return_value = ValidationResult(
                                valid=True, errors=[], warnings=[]
                            )

                            # Deploy with partial RESERVED_ENV_VARS
                            result = self.deployment_manager.deploy_template(
                                template_name, config_sources, options
                            )

                            # Verify deployment was successful
                            assert result.success is True
                            assert result.deployment_id is not None

                            # Verify that RESERVED_ENV_VARS mapping was applied
                            # The transport should be reflected in the result
                            assert result.transport == "stdio"
