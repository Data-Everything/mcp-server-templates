"""
Tool discovery module for MCP Platform.

This module provides dynamic discovery and normalization of "tools" (capabilities)
from MCP-compliant servers across different implementations (FastMCP, LangServe,
Flask, Docker containers).
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# Configuration constants
CACHE_MAX_AGE_HOURS = 6
DEFAULT_TIMEOUT_SECONDS = 10
DEFAULT_ENDPOINTS = [
    "/tools",
    "/get_tools",
    "/capabilities",
    "/metadata",
    "/openapi.json",
]


class ToolDiscovery:
    """
    Discovers and normalizes tools from MCP servers using multiple strategies.

    Supports:
    - Static discovery from tools.json files
    - Dynamic discovery from live endpoints
    - Cached discovery for remote/Docker servers
    - Fallback strategies with timeout handling
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize tool discovery with optional cache directory."""
        self.cache_dir = cache_dir or Path.home() / ".mcp" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def discover_tools(
        self,
        template_name: str,
        template_dir: Optional[Path] = None,
        template_config: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """
        Discover tools for a given template using prioritized fallback strategies.

        Args:
            template_name: Name of the template
            template_dir: Path to template directory (for static files)
            template_config: Template configuration dict
            use_cache: Whether to use cached results
            force_refresh: Force refresh cached results

        Returns:
            Dictionary containing discovered tools and metadata
        """
        logger.info("Discovering tools for template: %s", template_name)

        # Parse template configuration
        config = template_config or {}
        discovery_type = config.get("tool_discovery", "dynamic")
        origin = config.get("origin", "internal")

        # Check cache first (if enabled and not forcing refresh)
        if use_cache and not force_refresh:
            cached_result = self._load_from_cache(template_name)
            if cached_result:
                logger.info("Using cached tool discovery for %s", template_name)
                return cached_result

        # Strategy 1: Static discovery from tools.json
        if discovery_type == "static" or (
            template_dir and (template_dir / "tools.json").exists()
        ):
            logger.info("Using static tool discovery for %s", template_name)
            result = self._discover_static_tools(template_name, template_dir)
            if result:
                self._save_to_cache(template_name, result)
                return result

        # Strategy 2: Dynamic discovery from live endpoints
        if discovery_type == "dynamic":
            logger.info("Using dynamic tool discovery for %s", template_name)
            result = self._discover_dynamic_tools(template_name, config)
            if result:
                self._save_to_cache(template_name, result)
                return result

        # Strategy 3: Try extracting from template.json if available
        if template_config and "tools" in template_config:
            logger.info("Using tools from template.json for %s", template_name)
            result = {
                "tools": self._normalize_tools(template_config["tools"]),
                "discovery_method": "template_json",
                "timestamp": time.time(),
                "template_name": template_name,
                "source": "template.json",
            }
            self._save_to_cache(template_name, result)
            return result

        # Strategy 4: Fallback to empty tools with warning
        logger.warning("No tools discovered for template %s", template_name)
        if origin == "external":
            logger.warning(
                "External template %s may require manual tool configuration",
                template_name,
            )

        return {
            "tools": [],
            "discovery_method": "none",
            "timestamp": time.time(),
            "template_name": template_name,
            "warnings": ["No tools could be discovered"],
        }

    def _discover_static_tools(
        self, template_name: str, template_dir: Optional[Path]
    ) -> Optional[Dict[str, Any]]:
        """Discover tools from static tools.json file."""
        if not template_dir:
            logger.debug(
                "No template directory provided for static discovery: %s", template_name
            )
            return None

        tools_file = template_dir / "tools.json"
        if not tools_file.exists():
            logger.debug("No tools.json found in %s", template_dir)
            return None

        try:
            with open(tools_file, "r", encoding="utf-8") as f:
                tools_data = json.load(f)

            return {
                "tools": self._normalize_tools(tools_data),
                "discovery_method": "static",
                "timestamp": time.time(),
                "template_name": template_name,
                "source_file": str(tools_file),
            }

        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load static tools from %s: %s", tools_file, e)
            return None

    def _discover_dynamic_tools(
        self, template_name: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Discover tools by probing live server endpoints."""
        # Check if we have connection info
        base_url = self._get_server_url(config)
        if not base_url:
            logger.debug(
                "No server URL available for dynamic discovery: %s", template_name
            )
            return None

        # Try each endpoint in priority order
        custom_endpoint = config.get("tool_endpoint")
        endpoints = [custom_endpoint] if custom_endpoint else DEFAULT_ENDPOINTS

        for endpoint in endpoints:
            if not endpoint:
                continue

            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                logger.debug("Probing endpoint: %s", url)

                response = requests.get(
                    url,
                    timeout=DEFAULT_TIMEOUT_SECONDS,
                    headers={"Accept": "application/json"},
                )

                if response.status_code == 200:
                    tools_data = response.json()
                    if self._is_valid_tools_response(tools_data):
                        return {
                            "tools": self._normalize_tools(tools_data),
                            "discovery_method": "dynamic",
                            "timestamp": time.time(),
                            "template_name": template_name,
                            "source_endpoint": url,
                        }

            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.debug(
                    "Failed to probe %s for %s: %s", endpoint, template_name, e
                )
                continue

        logger.debug("No responsive endpoints found for %s", template_name)
        return None

    def _get_server_url(self, config: Dict[str, Any]) -> Optional[str]:
        """Get server URL for dynamic discovery."""
        # Try to get URL from various sources
        # This could be enhanced to check running containers, etc.

        # For now, check common patterns
        if "server_url" in config:
            return config["server_url"]

        # Could check for running Docker containers here
        # and construct URLs like http://localhost:PORT

        return None

    def _is_valid_tools_response(self, data: Any) -> bool:
        """Check if response conforms to expected tools format."""
        if not isinstance(data, dict):
            return False

        # Look for common tool response patterns
        if "tools" in data and isinstance(data["tools"], list):
            return True

        if isinstance(data, dict) and any(
            key in data
            for key in ["capabilities", "functions", "methods", "operations"]
        ):
            return True

        # Check for OpenAPI format
        if "paths" in data and isinstance(data["paths"], dict):
            return True

        return False

    def _normalize_tools(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize tools data to consistent format."""
        if isinstance(raw_data, list):
            # Already a list of tools
            return [self._normalize_single_tool(tool) for tool in raw_data]

        if isinstance(raw_data, dict):
            # Handle different response formats
            if "tools" in raw_data:
                return [self._normalize_single_tool(tool) for tool in raw_data["tools"]]

            elif "capabilities" in raw_data:
                return [
                    self._normalize_single_tool(tool)
                    for tool in raw_data["capabilities"]
                ]

            elif "functions" in raw_data:
                return [
                    self._normalize_single_tool(tool) for tool in raw_data["functions"]
                ]

            elif "paths" in raw_data:
                # OpenAPI format
                return self._normalize_openapi_tools(raw_data)

        return []

    def _normalize_single_tool(self, tool: Any) -> Dict[str, Any]:
        """Normalize a single tool to consistent format."""
        if not isinstance(tool, dict):
            return {"name": str(tool), "description": ""}

        # Extract common fields with fallbacks
        return {
            "name": tool.get("name")
            or tool.get("function_name")
            or tool.get("id", "unknown"),
            "description": tool.get("description") or tool.get("summary", ""),
            "parameters": tool.get("parameters")
            or tool.get("args")
            or tool.get("schema", {}),
            "category": tool.get("category", "general"),
            "raw": tool,  # Keep original for reference
        }

    def _normalize_openapi_tools(
        self, openapi_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Normalize OpenAPI specification to tools format."""
        tools = []
        paths = openapi_data.get("paths", {})

        for path, methods in paths.items():
            if not isinstance(methods, dict):
                continue

            for method, spec in methods.items():
                if not isinstance(spec, dict):
                    continue

                tool = {
                    "name": f"{method.upper()} {path}",
                    "description": spec.get("summary") or spec.get("description", ""),
                    "parameters": spec.get("parameters", []),
                    "category": "api",
                    "method": method.upper(),
                    "path": path,
                    "raw": spec,
                }
                tools.append(tool)

        return tools

    def _load_from_cache(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Load cached tool discovery results."""
        cache_file = self.cache_dir / f"{template_name}.tools.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Check if cache is still valid
            cache_age_hours = (time.time() - cached_data.get("timestamp", 0)) / 3600
            if cache_age_hours > CACHE_MAX_AGE_HOURS:
                logger.debug(
                    "Cache expired for %s (age: %.1fh)", template_name, cache_age_hours
                )
                return None

            logger.debug("Loaded cached tools for %s", template_name)
            return cached_data

        except (json.JSONDecodeError, IOError, KeyError) as e:
            logger.debug("Failed to load cache for %s: %s", template_name, e)
            return None

    def _save_to_cache(self, template_name: str, data: Dict[str, Any]) -> None:
        """Save tool discovery results to cache."""
        cache_file = self.cache_dir / f"{template_name}.tools.json"

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug("Cached tools for %s", template_name)

        except IOError as e:
            logger.warning("Failed to cache tools for %s: %s", template_name, e)

    def clear_cache(self, template_name: Optional[str] = None) -> None:
        """Clear cached tool discovery results."""
        if template_name:
            cache_file = self.cache_dir / f"{template_name}.tools.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.info("Cleared cache for %s", template_name)
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.tools.json"):
                cache_file.unlink()
            logger.info("Cleared all tool discovery cache")
