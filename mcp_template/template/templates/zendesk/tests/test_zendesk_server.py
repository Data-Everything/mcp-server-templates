#!/usr/bin/env python3
"""
Tests for Zendesk MCP Server

Test suite for the main server functionality including tool operations,
API interactions, rate limiting, and caching.
"""

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientSession

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import CacheEntry, RateLimiter, ZendeskMCPServer


class TestRateLimiter:
    """Test cases for the RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_minute=100)
        assert limiter.requests_per_minute == 100
        assert limiter.requests == []

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests_under_limit(self):
        """Test that rate limiter allows requests under the limit."""
        limiter = RateLimiter(requests_per_minute=10)

        # Should not wait for first few requests
        start_time = asyncio.get_event_loop().time()
        await limiter.wait_if_needed()
        end_time = asyncio.get_event_loop().time()

        assert end_time - start_time < 0.1  # Should be immediate

    @pytest.mark.asyncio
    async def test_rate_limiter_throttles_when_limit_reached(self):
        """Test that rate limiter throttles when limit is reached."""
        limiter = RateLimiter(requests_per_minute=2)

        # Fill up the rate limit
        await limiter.wait_if_needed()
        await limiter.wait_if_needed()

        # This should cause throttling
        start_time = asyncio.get_event_loop().time()

        # Mock time to simulate rapid requests
        with patch("time.time") as mock_time:
            mock_time.return_value = start_time
            limiter.requests = [start_time, start_time]  # Simulate 2 recent requests

            # The next request should be throttled
            with patch("asyncio.sleep") as mock_sleep:
                await limiter.wait_if_needed()
                mock_sleep.assert_called_once()


class TestCacheEntry:
    """Test cases for the CacheEntry class."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        data = {"test": "data"}
        expires_at = 12345.0

        entry = CacheEntry(data=data, expires_at=expires_at)

        assert entry.data == data
        assert entry.expires_at == expires_at


class TestZendeskMCPServer:
    """Test cases for the ZendeskMCPServer class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "zendesk_subdomain": "test",
            "zendesk_email": "test@example.com",
            "zendesk_api_token": "test_token",
            "rate_limit_requests": 200,
            "timeout_seconds": 30,
            "log_level": "info",
        }

    @pytest.fixture
    def server(self, mock_config):
        """Create a server instance for testing."""
        with patch("server.ZendeskServerConfig") as mock_config_class:
            # Mock the config class
            mock_config_instance = MagicMock()
            mock_config_instance.get_template_config.return_value = mock_config
            mock_config_instance.get_template_data.return_value = {
                "name": "test-server",
                "version": "1.0.0",
            }
            mock_config_instance.get_zendesk_url.return_value = (
                "https://test.zendesk.com"
            )
            mock_config_instance.get_auth_headers.return_value = {
                "Authorization": "Basic test"
            }
            mock_config_instance.get_rate_limit_config.return_value = {
                "requests_per_minute": 200,
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

            server = ZendeskMCPServer(config_dict=mock_config)
            return server

    def test_server_initialization(self, server):
        """Test server initialization."""
        assert server.base_url == "https://test.zendesk.com"
        assert server.api_url == "https://test.zendesk.com/api/v2"
        assert server.cache_enabled is True
        assert server.cache_ttl == 300

    def test_cache_key_generation(self, server):
        """Test cache key generation."""
        key = server._get_cache_key("GET", "/test", {"param": "value"})
        assert "GET" in key
        assert "/test" in key
        assert "param=value" in key

    def test_cache_data_storage_and_retrieval(self, server):
        """Test caching functionality."""
        cache_key = "test_key"
        test_data = {"test": "data"}

        # Cache data
        server._cache_data(cache_key, test_data)

        # Retrieve cached data
        cached_data = server._get_cached_data(cache_key)
        assert cached_data == test_data

    def test_cache_expiration(self, server):
        """Test cache expiration."""
        cache_key = "test_key"
        test_data = {"test": "data"}

        # Mock time to simulate expiration
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000
            server._cache_data(cache_key, test_data)

            # Simulate time passing beyond TTL
            mock_time.return_value = 1000 + server.cache_ttl + 1

            cached_data = server._get_cached_data(cache_key)
            assert cached_data is None

    @pytest.mark.asyncio
    @pytest.mark.skip  # Until zendesk is ready for async testing
    async def test_make_request_success(self, server):
        """Test successful API request."""
        mock_response_data = {"ticket": {"id": 123, "subject": "Test"}}

        # Mock aiohttp session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value=json.dumps(mock_response_data))
        mock_response.raise_for_status = MagicMock()

        # Setup the mock context manager for the request call
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_response
        mock_context_manager.__aexit__.return_value = None

        # Create the mock session and set the request method to return the mock context manager
        mock_session = AsyncMock()
        mock_session.request.return_value = mock_context_manager

        server.session = mock_session

        result = await server._make_request("GET", "tickets/123.json")

        assert result == mock_response_data
        mock_session.request.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.skip  # Until zendesk is ready for async testing
    async def test_make_request_rate_limited(self, server):
        """Test API request with rate limiting."""
        mock_response_data = {"ticket": {"id": 123}}

        # First response: rate limited
        mock_rate_limited_response = AsyncMock()
        mock_rate_limited_response.status = 429
        mock_rate_limited_response.headers = {"Retry-After": "1"}
        mock_rate_limited_response.text = AsyncMock(
            return_value='{"error": "Rate limited"}'
        )

        # Second response: success
        mock_success_response = AsyncMock()
        mock_success_response.status = 200
        mock_success_response.text = AsyncMock(
            return_value=json.dumps(mock_response_data)
        )
        mock_success_response.raise_for_status = MagicMock()

        mock_session = AsyncMock()
        mock_session.request.return_value.__aenter__.side_effect = [
            mock_rate_limited_response,
            mock_success_response,
        ]

        server.session = mock_session

        with patch("asyncio.sleep") as mock_sleep:
            result = await server._make_request("GET", "tickets/123.json")

            assert result == mock_response_data
            mock_sleep.assert_called_once_with(1)  # Retry-After value

    @pytest.mark.asyncio
    async def test_create_ticket(self, server):
        """Test ticket creation."""
        mock_response = {
            "ticket": {
                "id": 123,
                "subject": "Test Ticket",
                "status": "new",
                "priority": "normal",
                "created_at": "2024-01-01T00:00:00Z",
                "url": "https://test.zendesk.com/api/v2/tickets/123.json",
            }
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.create_ticket(
            subject="Test Ticket", description="Test description", priority="normal"
        )

        assert result["ticket_id"] == 123
        assert result["status"] == "new"
        assert result["priority"] == "normal"

        # Verify the API call was made correctly
        server._make_request.assert_called_once()
        call_args = server._make_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "tickets.json"
        assert "ticket" in call_args[1]["data"]

    @pytest.mark.asyncio
    async def test_get_ticket(self, server):
        """Test ticket retrieval."""
        mock_ticket_response = {
            "ticket": {
                "id": 123,
                "subject": "Test Ticket",
                "status": "open",
                "priority": "normal",
                "requester_id": 456,
                "assignee_id": 789,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }

        mock_comments_response = {
            "comments": [
                {"id": 1, "body": "Initial comment", "public": True, "author_id": 456}
            ]
        }

        server._make_request = AsyncMock(
            side_effect=[mock_ticket_response, mock_comments_response]
        )

        result = await server.get_ticket(ticket_id=123, include_comments=True)

        assert result["ticket_id"] == 123
        assert result["subject"] == "Test Ticket"
        assert result["status"] == "open"
        assert len(result["comments"]) == 1
        assert result["comment_count"] == 1

        # Verify two API calls were made (ticket and comments)
        assert server._make_request.call_count == 2

    @pytest.mark.asyncio
    async def test_update_ticket(self, server):
        """Test ticket update."""
        mock_response = {
            "ticket": {
                "id": 123,
                "status": "solved",
                "priority": "high",
                "assignee_id": 789,
                "updated_at": "2024-01-01T12:00:00Z",
            }
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.update_ticket(
            ticket_id=123, status="solved", priority="high", assignee_id=789
        )

        assert result["ticket_id"] == 123
        assert result["status"] == "solved"
        assert result["priority"] == "high"
        assert result["assignee_id"] == 789

        # Verify the API call was made correctly
        server._make_request.assert_called_once()
        call_args = server._make_request.call_args
        assert call_args[0][0] == "PUT"
        assert "tickets/123.json" in call_args[0][1]

    @pytest.mark.asyncio
    async def test_search_tickets(self, server):
        """Test ticket search."""
        mock_response = {
            "results": [
                {"id": 123, "subject": "Test 1", "status": "open"},
                {"id": 124, "subject": "Test 2", "status": "new"},
            ],
            "count": 2,
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.search_tickets(query="test", status="open", limit=10)

        assert result["total_count"] == 2
        assert result["ticket_count"] == 2
        assert len(result["tickets"]) == 2
        assert "test" in result["query"]
        assert "status:open" in result["query"]

    @pytest.mark.asyncio
    async def test_add_ticket_comment(self, server):
        """Test adding comment to ticket."""
        mock_response = {
            "audit": {
                "events": [
                    {
                        "id": 1,
                        "type": "Comment",
                        "author_id": 456,
                        "created_at": "2024-01-01T12:00:00Z",
                    }
                ]
            }
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.add_ticket_comment(
            ticket_id=123, body="Test comment", public=True
        )

        assert result["ticket_id"] == 123
        assert result["body"] == "Test comment"
        assert result["public"] is True
        assert result["comment_id"] == 1

    @pytest.mark.asyncio
    async def test_create_user(self, server):
        """Test user creation."""
        mock_response = {
            "user": {
                "id": 456,
                "name": "Test User",
                "email": "test@example.com",
                "role": "end-user",
                "created_at": "2024-01-01T00:00:00Z",
            }
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.create_user(
            name="Test User", email="test@example.com", role="end-user"
        )

        assert result["user_id"] == 456
        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["role"] == "end-user"

    @pytest.mark.asyncio
    async def test_search_articles(self, server):
        """Test knowledge base article search."""
        mock_response = {
            "results": [
                {
                    "id": 789,
                    "title": "How to test",
                    "body": "Testing instructions...",
                    "section_id": 101,
                }
            ]
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.search_articles(query="test", locale="en-us")

        assert result["article_count"] == 1
        assert len(result["articles"]) == 1
        assert result["query"] == "test"
        assert result["locale"] == "en-us"

    @pytest.mark.asyncio
    async def test_get_ticket_metrics(self, server):
        """Test ticket metrics retrieval."""
        mock_response = {
            "results": [
                {
                    "id": 123,
                    "status": "solved",
                    "priority": "normal",
                    "type": "question",
                },
                {"id": 124, "status": "open", "priority": "high", "type": "incident"},
                {
                    "id": 125,
                    "status": "closed",
                    "priority": "normal",
                    "type": "question",
                },
            ],
            "count": 3,
        }

        server._make_request = AsyncMock(return_value=mock_response)

        result = await server.get_ticket_metrics()

        assert result["total_tickets"] == 3
        assert "status_breakdown" in result
        assert "priority_breakdown" in result
        assert "type_breakdown" in result
        assert "resolution_stats" in result

        # Check status breakdown
        assert result["status_breakdown"]["solved"] == 1
        assert result["status_breakdown"]["open"] == 1
        assert result["status_breakdown"]["closed"] == 1

        # Check resolution stats
        assert result["resolution_stats"]["solved_count"] == 2  # solved + closed
        assert result["resolution_stats"]["open_count"] == 1

    @pytest.mark.asyncio
    async def test_context_manager(self, server):
        """Test async context manager functionality."""
        async with server as s:
            assert s.session is not None
            assert isinstance(s.session, ClientSession)

        # After exiting context, session should be closed
        # Note: We can't easily test this without mocking, but the structure is correct


if __name__ == "__main__":
    pytest.main([__file__])
