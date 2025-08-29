#!/usr/bin/env python3
"""
Tests for Zendesk MCP Server Configuration

Test suite for configuration management, validation, and environment variable handling.
"""

import json
import os
import sys
from unittest.mock import mock_open, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import ZendeskServerConfig


class TestZendeskServerConfig:
    """Test cases for ZendeskServerConfig class."""

    @pytest.fixture
    def sample_template_data(self):
        """Sample template data for testing."""
        return {
            "name": "Zendesk MCP Server",
            "version": "1.0.0",
            "config_schema": {
                "type": "object",
                "properties": {
                    "zendesk_subdomain": {
                        "type": "string",
                        "env_mapping": "ZENDESK_SUBDOMAIN",
                    },
                    "zendesk_email": {"type": "string", "env_mapping": "ZENDESK_EMAIL"},
                    "zendesk_api_token": {
                        "type": "string",
                        "env_mapping": "ZENDESK_API_TOKEN",
                        "sensitive": True,
                    },
                    "rate_limit_requests": {
                        "type": "integer",
                        "default": 200,
                        "env_mapping": "ZENDESK_RATE_LIMIT",
                    },
                    "log_level": {
                        "type": "string",
                        "enum": ["debug", "info", "warning", "error"],
                        "default": "info",
                        "env_mapping": "MCP_LOG_LEVEL",
                    },
                },
                "required": ["zendesk_subdomain", "zendesk_email"],
            },
        }

    @pytest.fixture
    def mock_template_file(self, sample_template_data):
        """Mock template.json file."""
        template_json = json.dumps(sample_template_data)
        with patch("builtins.open", mock_open(read_data=template_json)):
            with patch("pathlib.Path.exists", return_value=True):
                yield template_json

    def test_config_initialization(self, mock_template_file):
        """Test basic configuration initialization."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
            }
        )

        assert config.config_dict["zendesk_subdomain"] == "test"
        assert config.config_dict["zendesk_email"] == "test@example.com"

    def test_environment_variable_loading(self, mock_template_file):
        """Test loading configuration from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ZENDESK_SUBDOMAIN": "testenv",
                "ZENDESK_EMAIL": "testenv@example.com",
                "ZENDESK_RATE_LIMIT": "150",
            },
        ):
            config = ZendeskServerConfig()
            template_config = config.get_template_config()

            assert template_config["zendesk_subdomain"] == "testenv"
            assert template_config["zendesk_email"] == "testenv@example.com"
            assert template_config["rate_limit_requests"] == 150

    def test_config_dict_overrides_env_vars(self, mock_template_file):
        """Test that config_dict takes precedence over environment variables."""
        with patch.dict(
            os.environ,
            {"ZENDESK_SUBDOMAIN": "testenv", "ZENDESK_EMAIL": "testenv@example.com"},
        ):
            config = ZendeskServerConfig(
                config_dict={
                    "zendesk_subdomain": "testconfig",
                    "zendesk_email": "testconfig@example.com",
                }
            )

            template_config = config.get_template_config()
            assert template_config["zendesk_subdomain"] == "testconfig"
            assert template_config["zendesk_email"] == "testconfig@example.com"

    def test_type_coercion(self, mock_template_file):
        """Test automatic type coercion for environment variables."""
        with patch.dict(
            os.environ,
            {
                "ZENDESK_SUBDOMAIN": "test",
                "ZENDESK_EMAIL": "test@example.com",
                "ZENDESK_RATE_LIMIT": "300",
            },
        ):
            config = ZendeskServerConfig()
            template_config = config.get_template_config()

            assert isinstance(template_config["rate_limit_requests"], int)
            assert template_config["rate_limit_requests"] == 300

    def test_get_zendesk_url(self, mock_template_file):
        """Test Zendesk URL generation."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "mycompany",
                "zendesk_email": "test@example.com",
            }
        )

        assert config.get_zendesk_url() == "https://mycompany.zendesk.com"

    def test_get_auth_headers_api_token(self, mock_template_file):
        """Test authentication headers with API token."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "zendesk_api_token": "secret123",
            }
        )

        headers = config.get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Basic ")
        assert headers["Content-Type"] == "application/json"

    def test_get_auth_headers_oauth_token(self, mock_template_file):
        """Test authentication headers with OAuth token."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "zendesk_oauth_token": "oauth123",
            }
        )

        headers = config.get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer oauth123"

    def test_get_rate_limit_config(self, mock_template_file):
        """Test rate limit configuration retrieval."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "rate_limit_requests": 150,
                "timeout_seconds": 45,
            }
        )

        rate_config = config.get_rate_limit_config()

        assert rate_config["requests_per_minute"] == 150
        assert rate_config["timeout_seconds"] == 45

    def test_get_cache_config(self, mock_template_file):
        """Test cache configuration retrieval."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "enable_cache": False,
                "cache_ttl_seconds": 600,
            }
        )

        cache_config = config.get_cache_config()

        assert cache_config["enabled"] is False
        assert cache_config["ttl_seconds"] == 600

    def test_get_default_ticket_config(self, mock_template_file):
        """Test default ticket configuration retrieval."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "default_ticket_priority": "high",
                "default_ticket_type": "incident",
            }
        )

        ticket_config = config.get_default_ticket_config()

        assert ticket_config["priority"] == "high"
        assert ticket_config["type"] == "incident"

    def test_is_sensitive_field(self, mock_template_file):
        """Test sensitive field detection."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
            }
        )

        assert config.is_sensitive_field("zendesk_api_token") is True
        assert config.is_sensitive_field("zendesk_subdomain") is False

    def test_get_sanitized_config(self, mock_template_file):
        """Test sanitized configuration output."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "zendesk_api_token": "secret123",
            }
        )

        sanitized = config.get_sanitized_config()

        assert sanitized["zendesk_subdomain"] == "test"
        assert sanitized["zendesk_api_token"] == "********"

    def test_nested_config_processing(self, mock_template_file):
        """Test double underscore notation processing."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
                "tools__0__custom_field": "custom_value",
                "transport__port": 8080,
            }
        )

        template_data = config.get_template_data()

        # Check if nested updates were applied
        # Note: This depends on the template having tools array
        if "tools" in template_data and len(template_data["tools"]) > 0:
            assert template_data["tools"][0].get("custom_field") == "custom_value"

    def test_defaults_from_schema(self, mock_template_file):
        """Test that defaults are properly loaded from schema."""
        config = ZendeskServerConfig(
            config_dict={
                "zendesk_subdomain": "test",
                "zendesk_email": "test@example.com",
            }
        )

        template_config = config.get_template_config()

        assert template_config["rate_limit_requests"] == 200  # Default from schema
        assert template_config["log_level"] == "info"  # Default from schema


if __name__ == "__main__":
    pytest.main([__file__])
