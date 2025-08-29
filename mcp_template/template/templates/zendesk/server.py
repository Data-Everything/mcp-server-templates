#!/usr/bin/env python3
"""
Zendesk MCP Server - Comprehensive Implementation

A comprehensive Zendesk MCP server that provides:
1. Complete ticket management (CRUD operations)
2. User and organization management
3. Knowledge base article access
4. Analytics and reporting capabilities
5. Comment and note management
6. Rate limiting and caching for optimal performance

This server uses FastMCP for modern MCP protocol implementation.
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import aiohttp
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from .config import ZendeskServerConfig
except ImportError:
    try:
        from config import ZendeskServerConfig
    except ImportError:
        # Fallback for Docker or direct script execution
        sys.path.append(os.path.dirname(__file__))
        from config import ZendeskServerConfig


@dataclass
class CacheEntry:
    """Cache entry with expiration."""

    data: Any
    expires_at: float


class RateLimiter:
    """Simple rate limiter for API requests."""

    def __init__(self, requests_per_minute: int = 200):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def wait_if_needed(self):
        """Wait if we're hitting rate limits."""
        now = time.time()
        # Remove requests older than 1 minute
        self.requests = [req_time for req_time in self.requests if now - req_time < 60]

        if len(self.requests) >= self.requests_per_minute:
            # Calculate how long to wait
            oldest_request = min(self.requests)
            wait_time = 60 - (now - oldest_request)
            if wait_time > 0:
                logger.info(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)

        self.requests.append(now)


class ZendeskMCPServer:
    """
    Comprehensive Zendesk MCP Server implementation using FastMCP.

    This server provides full Zendesk integration capabilities including:
    - Ticket management (create, read, update, search)
    - User and organization management
    - Knowledge base access
    - Comments and notes
    - Analytics and reporting
    - Rate limiting and caching
    """

    def __init__(self, config_dict: dict = None):
        """Initialize the Zendesk MCP Server with configuration."""
        self.config = ZendeskServerConfig(config_dict=config_dict or {})

        # Standard configuration data from config_schema
        self.config_data = self.config.get_template_config()

        # Full template data (potentially modified by double underscore notation)
        self.template_data = self.config.get_template_data()

        self.logger = self.config.logger

        # Initialize HTTP session
        self.session = None

        # Initialize rate limiter
        rate_config = self.config.get_rate_limit_config()
        self.rate_limiter = RateLimiter(rate_config["requests_per_minute"])
        self.timeout = rate_config["timeout_seconds"]

        # Initialize cache
        cache_config = self.config.get_cache_config()
        self.cache_enabled = cache_config["enabled"]
        self.cache_ttl = cache_config["ttl_seconds"]
        self.cache = {}

        # Zendesk configuration
        self.base_url = self.config.get_zendesk_url()
        self.api_url = f"{self.base_url}/api/v2"
        self.auth_headers = self.config.get_auth_headers()
        self.default_ticket_config = self.config.get_default_ticket_config()

        self.mcp = FastMCP(
            name=self.template_data.get("name", "zendesk-server"),
            instructions="Comprehensive Zendesk integration server",
            version=self.template_data.get("version", "1.0.0"),
            host=os.getenv("MCP_HOST", "0.0.0.0"),
            port=(
                int(
                    os.getenv(
                        "MCP_PORT",
                        self.template_data.get("transport", {}).get("port", 7071),
                    )
                )
                if not os.getenv("MCP_TRANSPORT") == "stdio"
                else None
            ),
        )

        logger.info(
            "Zendesk MCP server %s created for %s", self.mcp.name, self.base_url
        )
        self.register_tools()

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout), headers=self.auth_headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def register_tools(self):
        """Register all tools with the MCP server."""
        # Ticket management tools
        self.mcp.tool(self.create_ticket, tags=["tickets", "create"])
        self.mcp.tool(self.get_ticket, tags=["tickets", "read"])
        self.mcp.tool(self.update_ticket, tags=["tickets", "update"])
        self.mcp.tool(self.search_tickets, tags=["tickets", "search"])
        self.mcp.tool(self.add_ticket_comment, tags=["tickets", "comments"])

        # User management tools
        self.mcp.tool(self.create_user, tags=["users", "create"])
        self.mcp.tool(self.get_user, tags=["users", "read"])
        self.mcp.tool(self.search_users, tags=["users", "search"])

        # Knowledge base tools
        self.mcp.tool(self.search_articles, tags=["knowledge", "search"])
        self.mcp.tool(self.get_article, tags=["knowledge", "read"])

        # Analytics and reporting tools
        self.mcp.tool(self.get_ticket_metrics, tags=["analytics", "metrics"])

        # Organization tools
        self.mcp.tool(self.list_organizations, tags=["organizations", "list"])

        logger.info("All tools registered with Zendesk MCP server")

    def _get_cache_key(self, method: str, url: str, params: dict = None) -> str:
        """Generate cache key for request."""
        key_parts = [method, url]
        if params:
            key_parts.append(urlencode(sorted(params.items())))
        return "|".join(key_parts)

    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if available and not expired."""
        if not self.cache_enabled:
            return None

        entry = self.cache.get(cache_key)
        if entry and time.time() < entry.expires_at:
            self.logger.debug(f"Cache hit for {cache_key}")
            return entry.data
        elif entry:
            # Expired entry
            del self.cache[cache_key]

        return None

    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with expiration."""
        if self.cache_enabled:
            expires_at = time.time() + self.cache_ttl
            self.cache[cache_key] = CacheEntry(data=data, expires_at=expires_at)
            self.logger.debug(f"Cached data for {cache_key}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Make authenticated request to Zendesk API with rate limiting and caching."""
        if not self.session:
            raise RuntimeError(
                "HTTP session not initialized. Use 'async with' context manager."
            )

        url = f"{self.api_url}/{endpoint.lstrip('/')}"

        # Check cache for GET requests
        cache_key = None
        if method.upper() == "GET" and use_cache:
            cache_key = self._get_cache_key(method, url, params)
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data

        # Apply rate limiting
        await self.rate_limiter.wait_if_needed()

        try:
            self.logger.debug(f"Making {method} request to {url}")

            kwargs = {}
            if params:
                kwargs["params"] = params
            if data:
                kwargs["json"] = data

            async with self.session.request(method, url, **kwargs) as response:
                response_text = await response.text()

                if response.status == 429:
                    # Rate limited, wait and retry once
                    retry_after = int(response.headers.get("Retry-After", 60))
                    self.logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    await asyncio.sleep(retry_after)

                    async with self.session.request(
                        method, url, **kwargs
                    ) as retry_response:
                        retry_text = await retry_response.text()
                        retry_response.raise_for_status()
                        result = json.loads(retry_text)
                elif response.status >= 400:
                    self.logger.error(f"API error {response.status}: {response_text}")
                    response.raise_for_status()
                else:
                    result = json.loads(response_text)

                # Cache successful GET requests
                if method.upper() == "GET" and use_cache and cache_key:
                    self._cache_data(cache_key, result)

                return result

        except aiohttp.ClientError as e:
            self.logger.error(f"HTTP request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            raise

    # Ticket Management Tools

    async def create_ticket(
        self,
        subject: str,
        description: str,
        requester_email: Optional[str] = None,
        priority: Optional[str] = None,
        type: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new support ticket in Zendesk.

        Args:
            subject: Subject/title of the ticket
            description: Initial description or comment for the ticket
            requester_email: Email address of the person requesting support
            priority: Priority level (low, normal, high, urgent)
            type: Type of ticket (incident, problem, question, task)
            tags: List of tags to associate with the ticket

        Returns:
            Dictionary containing the created ticket information
        """
        self.logger.info(f"Creating ticket: {subject}")

        ticket_data = {
            "subject": subject,
            "comment": {"body": description},
            "priority": priority or self.default_ticket_config["priority"],
            "type": type or self.default_ticket_config["type"],
        }

        if requester_email:
            ticket_data["requester"] = {"email": requester_email}

        if tags:
            ticket_data["tags"] = tags

        result = await self._make_request(
            "POST", "tickets.json", data={"ticket": ticket_data}, use_cache=False
        )

        ticket = result.get("ticket", {})
        self.logger.info(f"Created ticket #{ticket.get('id')}")

        return {
            "ticket_id": ticket.get("id"),
            "url": ticket.get("url"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "created_at": ticket.get("created_at"),
            "ticket": ticket,
        }

    async def get_ticket(
        self, ticket_id: int, include_comments: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific ticket.

        Args:
            ticket_id: ID of the ticket to retrieve
            include_comments: Whether to include ticket comments

        Returns:
            Dictionary containing ticket information and optionally comments
        """
        self.logger.info(f"Retrieving ticket #{ticket_id}")

        # Get ticket details
        result = await self._make_request("GET", f"tickets/{ticket_id}.json")
        ticket = result.get("ticket", {})

        response = {
            "ticket": ticket,
            "ticket_id": ticket.get("id"),
            "subject": ticket.get("subject"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "requester_id": ticket.get("requester_id"),
            "assignee_id": ticket.get("assignee_id"),
            "created_at": ticket.get("created_at"),
            "updated_at": ticket.get("updated_at"),
        }

        # Get comments if requested
        if include_comments:
            try:
                comments_result = await self._make_request(
                    "GET", f"tickets/{ticket_id}/comments.json"
                )
                response["comments"] = comments_result.get("comments", [])
                response["comment_count"] = len(response["comments"])
            except Exception as e:
                self.logger.warning(
                    f"Failed to retrieve comments for ticket #{ticket_id}: {e}"
                )
                response["comments"] = []
                response["comment_count"] = 0

        return response

    async def update_ticket(
        self,
        ticket_id: int,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing ticket's properties.

        Args:
            ticket_id: ID of the ticket to update
            status: New status (new, open, pending, hold, solved, closed)
            priority: New priority (low, normal, high, urgent)
            assignee_id: ID of the agent to assign the ticket to
            tags: Tags to add to the ticket

        Returns:
            Dictionary containing the updated ticket information
        """
        self.logger.info(f"Updating ticket #{ticket_id}")

        update_data = {}

        if status:
            update_data["status"] = status
        if priority:
            update_data["priority"] = priority
        if assignee_id:
            update_data["assignee_id"] = assignee_id
        if tags:
            update_data["tags"] = tags

        if not update_data:
            raise ValueError("At least one field must be provided for update")

        result = await self._make_request(
            "PUT",
            f"tickets/{ticket_id}.json",
            data={"ticket": update_data},
            use_cache=False,
        )

        ticket = result.get("ticket", {})
        self.logger.info(f"Updated ticket #{ticket_id}")

        return {
            "ticket_id": ticket.get("id"),
            "status": ticket.get("status"),
            "priority": ticket.get("priority"),
            "assignee_id": ticket.get("assignee_id"),
            "updated_at": ticket.get("updated_at"),
            "ticket": ticket,
        }

    async def search_tickets(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        requester_email: Optional[str] = None,
        created_after: Optional[str] = None,
        limit: int = 25,
    ) -> Dict[str, Any]:
        """
        Search for tickets using various criteria.

        Args:
            query: Search query using Zendesk search syntax
            status: Filter by ticket status
            priority: Filter by priority
            requester_email: Filter by requester email
            created_after: Filter tickets created after this date (ISO format)
            limit: Maximum number of tickets to return

        Returns:
            Dictionary containing search results
        """
        self.logger.info("Searching tickets")

        search_terms = []

        if query:
            search_terms.append(query)
        if status:
            search_terms.append(f"status:{status}")
        if priority:
            search_terms.append(f"priority:{priority}")
        if requester_email:
            search_terms.append(f"requester:{requester_email}")
        if created_after:
            search_terms.append(f"created>{created_after}")

        # Add type filter to only get tickets
        search_terms.append("type:ticket")

        search_query = " ".join(search_terms) if search_terms else "type:ticket"

        params = {
            "query": search_query,
            "per_page": min(limit, 100),  # Zendesk API limit
        }

        result = await self._make_request("GET", "search.json", params=params)

        tickets = result.get("results", [])

        return {
            "query": search_query,
            "total_count": result.get("count", 0),
            "tickets": tickets,
            "ticket_count": len(tickets),
        }

    async def add_ticket_comment(
        self,
        ticket_id: int,
        body: str,
        public: bool = True,
        author_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Add a comment to an existing ticket.

        Args:
            ticket_id: ID of the ticket to comment on
            body: Content of the comment
            public: Whether comment is public (visible to requester) or internal
            author_id: ID of the comment author

        Returns:
            Dictionary containing the comment information
        """
        self.logger.info(f"Adding comment to ticket #{ticket_id}")

        comment_data = {"body": body, "public": public}

        if author_id:
            comment_data["author_id"] = author_id

        update_data = {"comment": comment_data}

        result = await self._make_request(
            "PUT",
            f"tickets/{ticket_id}.json",
            data={"ticket": update_data},
            use_cache=False,
        )

        # Get the latest comment from the response
        comments = result.get("audit", {}).get("events", [])
        comment_events = [e for e in comments if e.get("type") == "Comment"]
        latest_comment = comment_events[-1] if comment_events else {}

        return {
            "ticket_id": ticket_id,
            "comment_id": latest_comment.get("id"),
            "body": body,
            "public": public,
            "created_at": latest_comment.get("created_at"),
            "author_id": latest_comment.get("author_id"),
        }

    # User Management Tools

    async def create_user(
        self,
        name: str,
        email: str,
        role: str = "end-user",
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new user in Zendesk.

        Args:
            name: Full name of the user
            email: Email address of the user
            role: Role for the user (end-user, agent, admin)
            organization_id: ID of organization to associate user with

        Returns:
            Dictionary containing the created user information
        """
        self.logger.info(f"Creating user: {email}")

        user_data = {"name": name, "email": email, "role": role}

        if organization_id:
            user_data["organization_id"] = organization_id

        result = await self._make_request(
            "POST", "users.json", data={"user": user_data}, use_cache=False
        )

        user = result.get("user", {})
        self.logger.info(f"Created user #{user.get('id')}")

        return {
            "user_id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "organization_id": user.get("organization_id"),
            "created_at": user.get("created_at"),
            "user": user,
        }

    async def get_user(
        self, user_id: Optional[int] = None, email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve information about a specific user.

        Args:
            user_id: ID of the user to retrieve
            email: Email address of the user to retrieve

        Returns:
            Dictionary containing user information
        """
        if not user_id and not email:
            raise ValueError("Either user_id or email must be provided")

        if user_id:
            self.logger.info(f"Retrieving user #{user_id}")
            result = await self._make_request("GET", f"users/{user_id}.json")
        else:
            self.logger.info(f"Retrieving user by email: {email}")
            params = {"query": f"email:{email}"}
            result = await self._make_request("GET", "search.json", params=params)

            users = [
                r for r in result.get("results", []) if r.get("result_type") == "user"
            ]
            if not users:
                raise ValueError(f"User not found with email: {email}")

            user_data = users[0]
            result = {"user": user_data}

        user = result.get("user", {})

        return {
            "user_id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "organization_id": user.get("organization_id"),
            "active": user.get("active"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
            "user": user,
        }

    async def search_users(
        self,
        query: Optional[str] = None,
        role: Optional[str] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Search for users in Zendesk.

        Args:
            query: Search query for users
            role: Filter by user role
            organization_id: Filter by organization ID

        Returns:
            Dictionary containing search results
        """
        self.logger.info("Searching users")

        search_terms = ["type:user"]

        if query:
            search_terms.append(query)
        if role:
            search_terms.append(f"role:{role}")
        if organization_id:
            search_terms.append(f"organization_id:{organization_id}")

        search_query = " ".join(search_terms)
        params = {"query": search_query}

        result = await self._make_request("GET", "search.json", params=params)

        users = [r for r in result.get("results", []) if r.get("result_type") == "user"]

        return {
            "query": search_query,
            "total_count": result.get("count", 0),
            "users": users,
            "user_count": len(users),
        }

    # Knowledge Base Tools

    async def search_articles(
        self, query: str, locale: str = "en-us", section_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search knowledge base articles.

        Args:
            query: Search query for articles
            locale: Language locale for articles
            section_id: Filter by specific section ID

        Returns:
            Dictionary containing article search results
        """
        self.logger.info(f"Searching articles: {query}")

        params = {"query": query, "locale": locale}

        if section_id:
            params["section"] = section_id

        result = await self._make_request(
            "GET", "help_center/articles/search.json", params=params
        )

        articles = result.get("results", [])

        return {
            "query": query,
            "locale": locale,
            "section_id": section_id,
            "articles": articles,
            "article_count": len(articles),
        }

    async def get_article(
        self, article_id: int, locale: str = "en-us"
    ) -> Dict[str, Any]:
        """
        Retrieve a specific knowledge base article.

        Args:
            article_id: ID of the article to retrieve
            locale: Language locale for the article

        Returns:
            Dictionary containing article information
        """
        self.logger.info(f"Retrieving article #{article_id}")

        params = {"locale": locale}
        result = await self._make_request(
            "GET", f"help_center/articles/{article_id}.json", params=params
        )

        article = result.get("article", {})

        return {
            "article_id": article.get("id"),
            "title": article.get("title"),
            "body": article.get("body"),
            "section_id": article.get("section_id"),
            "locale": article.get("locale"),
            "created_at": article.get("created_at"),
            "updated_at": article.get("updated_at"),
            "article": article,
        }

    # Analytics and Reporting Tools

    async def get_ticket_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: str = "day",
    ) -> Dict[str, Any]:
        """
        Get metrics and analytics for tickets.

        Args:
            start_date: Start date for metrics (ISO format)
            end_date: End date for metrics (ISO format)
            group_by: Group metrics by field (day, week, month, assignee, priority, status)

        Returns:
            Dictionary containing ticket metrics
        """
        self.logger.info("Retrieving ticket metrics")

        # Set default date range if not provided
        if not end_date:
            end_date = datetime.now().isoformat()
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()

        # Build search query for date range
        search_query = f"type:ticket created>{start_date} created<{end_date}"

        params = {"query": search_query, "per_page": 100}

        result = await self._make_request("GET", "search.json", params=params)
        tickets = result.get("results", [])

        # Process tickets for metrics
        metrics = {
            "date_range": {"start_date": start_date, "end_date": end_date},
            "total_tickets": len(tickets),
            "status_breakdown": {},
            "priority_breakdown": {},
            "type_breakdown": {},
            "resolution_stats": {},
        }

        # Calculate breakdowns
        for ticket in tickets:
            # Status breakdown
            status = ticket.get("status", "unknown")
            metrics["status_breakdown"][status] = (
                metrics["status_breakdown"].get(status, 0) + 1
            )

            # Priority breakdown
            priority = ticket.get("priority", "unknown")
            metrics["priority_breakdown"][priority] = (
                metrics["priority_breakdown"].get(priority, 0) + 1
            )

            # Type breakdown
            ticket_type = ticket.get("type", "unknown")
            metrics["type_breakdown"][ticket_type] = (
                metrics["type_breakdown"].get(ticket_type, 0) + 1
            )

        # Calculate resolution statistics
        solved_tickets = [t for t in tickets if t.get("status") in ["solved", "closed"]]
        metrics["resolution_stats"] = {
            "solved_count": len(solved_tickets),
            "resolution_rate": (
                len(solved_tickets) / len(tickets) * 100 if tickets else 0
            ),
            "open_count": len(
                [
                    t
                    for t in tickets
                    if t.get("status") in ["new", "open", "pending", "hold"]
                ]
            ),
        }

        return metrics

    # Organization Tools

    async def list_organizations(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        List organizations in Zendesk.

        Args:
            query: Search query for organizations

        Returns:
            Dictionary containing organization list
        """
        self.logger.info("Listing organizations")

        if query:
            params = {"query": f"type:organization {query}"}
            result = await self._make_request("GET", "search.json", params=params)
            organizations = [
                r
                for r in result.get("results", [])
                if r.get("result_type") == "organization"
            ]
        else:
            result = await self._make_request("GET", "organizations.json")
            organizations = result.get("organizations", [])

        return {
            "query": query,
            "organizations": organizations,
            "organization_count": len(organizations),
        }

    def run(self):
        """Run the MCP server with the configured transport and port."""
        self.mcp.run(
            transport=os.getenv(
                "MCP_TRANSPORT",
                self.template_data.get("transport", {}).get("default", "http"),
            ),
            port=int(
                os.getenv(
                    "MCP_PORT",
                    self.template_data.get("transport", {}).get("port", 7072),
                )
            ),
            log_level=self.config_data.get("log_level", "info"),
        )


# Create the server instance
server = ZendeskMCPServer(config_dict={})

if __name__ == "__main__":
    server.run()
