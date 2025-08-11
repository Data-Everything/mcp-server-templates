#!/usr/bin/env python3
"""
Integration tests for Zendesk MCP Server

These tests verify the integration between the server and the MCP template system.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import ZendeskMCPServer


class TestZendeskMCPIntegration:
    """Integration tests for Zendesk MCP Server."""

    @pytest.fixture
    def mock_config_data(self):
        """Mock configuration data for integration tests."""
        return {
            "zendesk_subdomain": "testcompany",
            "zendesk_email": "support@testcompany.com",
            "zendesk_api_token": "test_api_token_123",
            "rate_limit_requests": 100,
            "timeout_seconds": 30,
            "log_level": "info",
            "enable_cache": True,
            "cache_ttl_seconds": 300,
            "default_ticket_priority": "normal",
            "default_ticket_type": "question",
        }

    @pytest.fixture
    def integration_server(self, mock_config_data):
        """Create server instance for integration testing."""
        with patch("server.ZendeskServerConfig") as mock_config_class:
            # Create a comprehensive mock configuration
            mock_config_instance = MagicMock()

            # Mock all the required methods
            mock_config_instance.get_template_config.return_value = mock_config_data
            mock_config_instance.get_template_data.return_value = {
                "name": "Zendesk MCP Server",
                "version": "1.0.0",
                "transport": {"default": "http", "port": 7072},
            }
            mock_config_instance.get_zendesk_url.return_value = (
                "https://testcompany.zendesk.com"
            )
            mock_config_instance.get_auth_headers.return_value = {
                "Authorization": "Basic dGVzdEB0ZXN0Y29tcGFueS5jb20vdG9rZW46dGVzdF9hcGlfdG9rZW5fMTIz",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            mock_config_instance.get_rate_limit_config.return_value = {
                "requests_per_minute": 100,
                "timeout_seconds": 30,
            }
            mock_config_instance.get_cache_config.return_value = {
                "enabled": True,
                "ttl_seconds": 300,
            }
            mock_config_instance.get_default_ticket_config.return_value = {
                "priority": "normal",
                "type": "question",
            }
            mock_config_instance.logger = MagicMock()

            mock_config_class.return_value = mock_config_instance

            # Create the server
            server = ZendeskMCPServer(config_dict=mock_config_data)
            return server

    def test_server_initialization_with_all_tools(self, integration_server):
        """Test that server initializes with all expected tools."""
        server = integration_server

        # Verify server properties
        assert server.base_url == "https://testcompany.zendesk.com"
        assert server.api_url == "https://testcompany.zendesk.com/api/v2"
        assert server.cache_enabled is True
        assert server.cache_ttl == 300
        assert server.timeout == 30

        # Verify FastMCP instance
        assert server.mcp is not None
        assert server.mcp.name == "Zendesk MCP Server"

    def test_tool_registration(self, integration_server):
        """Test that all tools are properly registered."""
        server = integration_server

        # The tools should be registered with the MCP instance
        # This is a basic check that the registration process completes without error
        # In a real test, we'd verify the specific tools are available
        assert hasattr(server, "mcp")

        # Verify key tool methods exist
        assert hasattr(server, "create_ticket")
        assert hasattr(server, "get_ticket")
        assert hasattr(server, "update_ticket")
        assert hasattr(server, "search_tickets")
        assert hasattr(server, "add_ticket_comment")
        assert hasattr(server, "create_user")
        assert hasattr(server, "get_user")
        assert hasattr(server, "search_users")
        assert hasattr(server, "search_articles")
        assert hasattr(server, "get_article")
        assert hasattr(server, "get_ticket_metrics")
        assert hasattr(server, "list_organizations")

    @pytest.mark.asyncio
    async def test_ticket_workflow_integration(self, integration_server):
        """Test a complete ticket workflow integration."""
        server = integration_server

        # Mock the HTTP requests for a complete workflow
        with patch.object(server, "_make_request") as mock_request:
            # Mock responses for create, get, update workflow
            mock_request.side_effect = [
                # Create ticket response
                {
                    "ticket": {
                        "id": 123,
                        "subject": "Integration Test Ticket",
                        "status": "new",
                        "priority": "normal",
                        "created_at": "2024-01-01T00:00:00Z",
                        "url": "https://testcompany.zendesk.com/api/v2/tickets/123.json",
                    }
                },
                # Get ticket response
                {
                    "ticket": {
                        "id": 123,
                        "subject": "Integration Test Ticket",
                        "status": "new",
                        "priority": "normal",
                        "requester_id": 456,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
                # Get comments response
                {
                    "comments": [
                        {
                            "id": 1,
                            "body": "Initial ticket description",
                            "public": True,
                            "author_id": 456,
                            "created_at": "2024-01-01T00:00:00Z",
                        }
                    ]
                },
                # Update ticket response
                {
                    "ticket": {
                        "id": 123,
                        "status": "solved",
                        "priority": "normal",
                        "assignee_id": 789,
                        "updated_at": "2024-01-01T12:00:00Z",
                    }
                },
            ]

            # Test create ticket
            create_result = await server.create_ticket(
                subject="Integration Test Ticket",
                description="This is a test ticket for integration testing",
                priority="normal",
            )

            assert create_result["ticket_id"] == 123
            assert create_result["status"] == "new"

            # Test get ticket
            get_result = await server.get_ticket(ticket_id=123, include_comments=True)

            assert get_result["ticket_id"] == 123
            assert get_result["subject"] == "Integration Test Ticket"
            assert len(get_result["comments"]) == 1

            # Test update ticket
            update_result = await server.update_ticket(
                ticket_id=123, status="solved", assignee_id=789
            )

            assert update_result["ticket_id"] == 123
            assert update_result["status"] == "solved"
            assert update_result["assignee_id"] == 789

            # Verify all API calls were made
            assert mock_request.call_count == 4

    @pytest.mark.asyncio
    async def test_user_management_integration(self, integration_server):
        """Test user management workflow integration."""
        server = integration_server

        with patch.object(server, "_make_request") as mock_request:
            mock_request.side_effect = [
                # Create user response
                {
                    "user": {
                        "id": 456,
                        "name": "Test User",
                        "email": "testuser@example.com",
                        "role": "end-user",
                        "organization_id": 101,
                        "created_at": "2024-01-01T00:00:00Z",
                    }
                },
                # Get user response
                {
                    "user": {
                        "id": 456,
                        "name": "Test User",
                        "email": "testuser@example.com",
                        "role": "end-user",
                        "organization_id": 101,
                        "active": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
            ]

            # Test create user
            create_result = await server.create_user(
                name="Test User",
                email="testuser@example.com",
                role="end-user",
                organization_id=101,
            )

            assert create_result["user_id"] == 456
            assert create_result["name"] == "Test User"
            assert create_result["email"] == "testuser@example.com"
            assert create_result["role"] == "end-user"

            # Test get user
            get_result = await server.get_user(user_id=456)

            assert get_result["user_id"] == 456
            assert get_result["name"] == "Test User"
            assert get_result["active"] is True

            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_knowledge_base_integration(self, integration_server):
        """Test knowledge base workflow integration."""
        server = integration_server

        with patch.object(server, "_make_request") as mock_request:
            mock_request.side_effect = [
                # Search articles response
                {
                    "results": [
                        {
                            "id": 789,
                            "title": "How to use the API",
                            "body": "API usage instructions...",
                            "section_id": 201,
                            "locale": "en-us",
                        },
                        {
                            "id": 790,
                            "title": "Troubleshooting Guide",
                            "body": "Common troubleshooting steps...",
                            "section_id": 202,
                            "locale": "en-us",
                        },
                    ]
                },
                # Get specific article response
                {
                    "article": {
                        "id": 789,
                        "title": "How to use the API",
                        "body": "<p>Detailed API usage instructions...</p>",
                        "section_id": 201,
                        "locale": "en-us",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                    }
                },
            ]

            # Test search articles
            search_result = await server.search_articles(query="API", locale="en-us")

            assert search_result["article_count"] == 2
            assert search_result["query"] == "API"
            assert search_result["locale"] == "en-us"

            # Test get specific article
            article_result = await server.get_article(article_id=789, locale="en-us")

            assert article_result["article_id"] == 789
            assert article_result["title"] == "How to use the API"
            assert "Detailed API usage instructions" in article_result["body"]

            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_analytics_integration(self, integration_server):
        """Test analytics and metrics integration."""
        server = integration_server

        with patch.object(server, "_make_request") as mock_request:
            mock_request.return_value = {
                "results": [
                    {
                        "id": 123,
                        "status": "solved",
                        "priority": "normal",
                        "type": "question",
                    },
                    {
                        "id": 124,
                        "status": "open",
                        "priority": "high",
                        "type": "incident",
                    },
                    {
                        "id": 125,
                        "status": "closed",
                        "priority": "low",
                        "type": "question",
                    },
                    {
                        "id": 126,
                        "status": "pending",
                        "priority": "normal",
                        "type": "task",
                    },
                ],
                "count": 4,
            }

            # Test get ticket metrics
            metrics_result = await server.get_ticket_metrics(
                start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T23:59:59Z"
            )

            assert metrics_result["total_tickets"] == 4

            # Verify status breakdown
            status_breakdown = metrics_result["status_breakdown"]
            assert status_breakdown["solved"] == 1
            assert status_breakdown["open"] == 1
            assert status_breakdown["closed"] == 1
            assert status_breakdown["pending"] == 1

            # Verify priority breakdown
            priority_breakdown = metrics_result["priority_breakdown"]
            assert priority_breakdown["normal"] == 2
            assert priority_breakdown["high"] == 1
            assert priority_breakdown["low"] == 1

            # Verify type breakdown
            type_breakdown = metrics_result["type_breakdown"]
            assert type_breakdown["question"] == 2
            assert type_breakdown["incident"] == 1
            assert type_breakdown["task"] == 1

            # Verify resolution stats
            resolution_stats = metrics_result["resolution_stats"]
            assert resolution_stats["solved_count"] == 2  # solved + closed
            assert resolution_stats["open_count"] == 2  # open + pending
            assert resolution_stats["resolution_rate"] == 50.0  # 2/4 * 100

    def test_error_handling_integration(self, integration_server):
        """Test error handling in integration scenarios."""
        server = integration_server

        # Test missing required parameters
        with pytest.raises(ValueError):
            asyncio.run(
                server.update_ticket(ticket_id=123)
            )  # No update fields provided

        # Test invalid user lookup
        with pytest.raises(ValueError):
            asyncio.run(server.get_user())  # No user_id or email provided

    def test_configuration_integration(self, integration_server):
        """Test that configuration is properly integrated throughout the server."""
        server = integration_server

        # Verify configuration values are properly set
        assert server.base_url == "https://testcompany.zendesk.com"
        assert server.cache_enabled is True
        assert server.cache_ttl == 300
        assert server.timeout == 30

        # Verify default ticket configuration
        assert server.default_ticket_config["priority"] == "normal"
        assert server.default_ticket_config["type"] == "question"

        # Verify rate limiter configuration
        assert server.rate_limiter.requests_per_minute == 100


if __name__ == "__main__":
    pytest.main([__file__])
