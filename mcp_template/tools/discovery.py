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

    def __init__(self, timeout: int = 30, cache_dir: Optional[Path] = None):
        """
        Initialize ToolDiscovery with configuration
        """
        self.timeout = timeout
        self.cache_dir = cache_dir or Path.home() / ".mcp" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = {}  # In-memory cache for this session

    def discover_tools(
        self,
        template_name: str,
        template_dir: str,
        template_config: Dict[str, Any],
        use_cache: bool = True,
        force_refresh: bool = False,
        force_server_discovery: bool = False,
    ) -> Dict[str, Any]:
        """
        Enhanced tool discovery with multiple strategies.

        Args:
            template_name: Name of the template
            template_dir: Path to template directory
            template_config: Template configuration
            use_cache: Whether to use cached results
            force_refresh: Whether to force refresh cached results
            force_server_discovery: If True, only use MCP server probing (skip static fallback)

        Returns:
            Dictionary containing discovered tools and metadata
        """

        # Convert template_dir to Path object if it's a string
        if isinstance(template_dir, str):
            template_dir = Path(template_dir)

        # Check cache if not forcing refresh and not in force server discovery mode
        if use_cache and not force_refresh and not force_server_discovery:
            cached_result = self._load_from_cache(template_name)
            if cached_result:
                logger.info("Using cached tool discovery for %s", template_name)
                return cached_result

        # Parse template configuration
        config = template_config or {}
        discovery_type = config.get("tool_discovery", "dynamic")
        origin = config.get("origin", "internal")

        # Force server discovery mode - only use MCP server probing
        if force_server_discovery:
            logger.info(
                "Force server discovery mode for %s - attempting MCP server probing only",
                template_name,
            )
            result = self._discover_dynamic_tools(template_name, config)
            if result and result.get("tools"):
                result["discovery_method"] = "server_probe"
                result["force_server_discovery"] = True
                result["notes"] = ["Forced server discovery - MCP server probing only"]
                self._save_to_cache(template_name, result)
                return result
            else:
                logger.error(
                    "Force server discovery failed for %s - no fallback allowed",
                    template_name,
                )
                return {
                    "tools": [],
                    "discovery_method": "server_probe",
                    "force_server_discovery": True,
                    "error": "MCP server probing failed and no fallback allowed",
                    "notes": [
                        "Force server discovery mode",
                        "MCP server unreachable or invalid configuration",
                    ],
                }

        # Strategy 1: Try dynamic discovery first if we have credentials
        if discovery_type == "dynamic" and self._has_valid_credentials(
            template_name, config
        ):
            logger.info(
                "Using dynamic tool discovery for %s (credentials available)",
                template_name,
            )
            result = self._discover_dynamic_tools(template_name, config)
            if result and result.get("tools"):
                # Mark as dynamic discovery with fallback available if not already set
                if "discovery_method" not in result:
                    result["discovery_method"] = "dynamic"
                result["fallback_available"] = (
                    template_dir and (template_dir / "tools.json").exists()
                )
                self._save_to_cache(template_name, result)
                return result
            else:
                logger.warning(
                    "Dynamic discovery failed for %s, trying static fallback",
                    template_name,
                )

        # Strategy 1.5: Try dynamic discovery with dummy credentials for tool discovery
        elif discovery_type == "dynamic":
            logger.info(
                "Attempting dynamic tool discovery for %s with placeholder credentials",
                template_name,
            )
            config_with_dummies = self._add_dummy_credentials(template_name, config)
            if self._has_valid_credentials(template_name, config_with_dummies):
                result = self._discover_dynamic_tools(
                    template_name, config_with_dummies
                )
                if result and result.get("tools"):
                    result["discovery_method"] = "server_probe"
                    result["notes"] = result.get("notes", []) + [
                        "Used placeholder credentials for discovery"
                    ]
                    result["fallback_available"] = (
                        template_dir and (template_dir / "tools.json").exists()
                    )
                    self._save_to_cache(template_name, result)
                    return result
                else:
                    logger.warning(
                        "Dynamic discovery with placeholders failed for %s, trying static fallback",
                        template_name,
                    )

        # Strategy 2: Static discovery from tools.json (preferred fallback)
        if template_dir and (template_dir / "tools.json").exists():
            logger.info("Using static tool discovery for %s", template_name)
            result = self._discover_static_tools(template_name, template_dir)
            if result and result.get("tools"):
                # Mark as static discovery with dynamic capability
                result["discovery_method"] = "static"
                result["dynamic_available"] = discovery_type == "dynamic"
                result["notes"] = [
                    "Static discovery used",
                    "Provide valid credentials for dynamic discovery",
                ]
                self._save_to_cache(template_name, result)
                return result

        # Strategy 3: Dynamic discovery as last resort (even without credentials)
        if discovery_type == "dynamic":
            logger.info(
                "Attempting dynamic tool discovery for %s without credentials",
                template_name,
            )
            result = self._discover_dynamic_tools(template_name, config)
            if result and result.get("tools"):
                self._save_to_cache(template_name, result)
                return result

        # Strategy 3: Fallback to template.json capabilities (last resort)
        if template_config and (
            "tools" in template_config or "capabilities" in template_config
        ):
            logger.warning(
                "Using template capabilities as fallback for %s", template_name
            )
            # Extract tools or capabilities from template
            tools_data = template_config.get("tools") or template_config.get(
                "capabilities", []
            )
            logger.debug("Found tools_data: %s", tools_data)
            if tools_data:
                normalized_tools = self._normalize_tools(tools_data)
                logger.debug("Normalized tools: %s", normalized_tools)
                result = {
                    "tools": normalized_tools,
                    "discovery_method": "template_json",
                    "timestamp": time.time(),
                    "template_name": template_name,
                    "source": "template.json",
                    "warnings": [
                        "Using template-defined capabilities as fallback",
                        "This may not reflect actual server capabilities",
                    ],
                }
                # Only save to cache if tools were found
                if result.get("tools"):
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
        """Discover tools by probing live server endpoints and Docker containers."""

        # Check transport configuration to determine discovery strategy
        transport_config = config.get("transport", {})
        default_transport = transport_config.get("default", "http")
        supported_transports = transport_config.get("supported", ["http"])

        # Strategy 2a: Use stdio-based Docker discovery if template supports stdio
        if ("stdio" in supported_transports or default_transport == "stdio") and (
            "docker_image" in config or "image" in config
        ):
            logger.info("Using stdio-based Docker discovery for %s", template_name)
            stdio_result = self._try_stdio_docker_discovery(template_name, config)
            if stdio_result and stdio_result.get("tools"):
                return stdio_result

        # Strategy 2b: Try HTTP-based Docker discovery if image is available and supports HTTP
        elif ("http" in supported_transports or default_transport == "http") and (
            "docker_image" in config or "image" in config
        ):
            logger.info("Using HTTP-based Docker discovery for %s", template_name)
            docker_result = self._try_http_docker_discovery(template_name, config)
            if docker_result and docker_result.get("tools"):
                return docker_result

        # Strategy 2c: Try HTTP endpoints if server URL is available
        base_url = self._get_server_url(config)
        if base_url:
            http_result = self._try_http_endpoints(template_name, config, base_url)
            if http_result and http_result.get("tools"):
                return http_result

        logger.debug("No responsive dynamic discovery methods for %s", template_name)
        return None

    def _try_stdio_docker_discovery(
        self, template_name: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using stdio-based Docker probe."""
        try:
            from .docker_probe import DockerProbe

            # Get Docker image
            docker_image = config.get("docker_image")
            if not docker_image:
                # Try to construct from image + docker_tag
                image = config.get("image")
                if image and ":" not in image:
                    docker_tag = config.get("docker_tag", "latest")
                    docker_image = f"{image}:{docker_tag}"
                else:
                    docker_image = image

            if not docker_image:
                logger.debug(
                    "No Docker image found for stdio discovery: %s", template_name
                )
                return None

            # Prepare environment variables for stdio mode
            env_vars = {}

            # CRITICAL: Set MCP_TRANSPORT=stdio for stdio mode
            env_vars["MCP_TRANSPORT"] = "stdio"

            # Add environment variables from config schema defaults and user config
            config_schema = config.get("config_schema", {})
            properties = config_schema.get("properties", {})

            # First add defaults from schema
            for prop_name, prop_config in properties.items():
                env_mapping = prop_config.get("env_mapping", prop_name.upper())
                default_value = prop_config.get("default")
                if default_value is not None:
                    env_vars[env_mapping] = str(default_value)

            # Add explicit env_vars from config (can override defaults)
            template_env = config.get("env_vars", {})
            env_vars.update(template_env)

            # Add any user-provided config values (converted to env vars)
            user_config = config.get("user_config", {})
            for prop_name, value in user_config.items():
                # Map config property to environment variable
                prop_config = properties.get(prop_name, {})
                env_mapping = prop_config.get("env_mapping", prop_name.upper())
                env_vars[env_mapping] = str(value)

            logger.debug(
                "Using stdio Docker discovery for %s with image %s and env vars: %s",
                template_name,
                docker_image,
                list(env_vars.keys()),
            )

            # Use Docker probe for stdio discovery
            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image(
                docker_image, server_args=None, env_vars=env_vars, timeout=15
            )

            if result:
                result["template_name"] = template_name
                logger.info(
                    "Successfully discovered tools via stdio Docker for %s",
                    template_name,
                )

            return result

        except Exception as e:
            logger.debug("Stdio Docker discovery failed for %s: %s", template_name, e)
            return None

    def _try_http_docker_discovery(
        self, template_name: str, config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using HTTP-based Docker probe."""
        try:
            from .docker_probe import DockerProbe

            # Get Docker image
            docker_image = config.get("docker_image")
            if not docker_image:
                # Try to construct from image + docker_tag
                image = config.get("image")
                if image and ":" not in image:
                    docker_tag = config.get("docker_tag", "latest")
                    docker_image = f"{image}:{docker_tag}"
                else:
                    docker_image = image

            if not docker_image:
                logger.debug("No Docker image specified for %s", template_name)
                return None

            logger.info(
                "Trying Docker discovery for %s with image %s",
                template_name,
                docker_image,
            )

            # Create environment variables from config schema defaults
            env_vars = self._extract_env_vars_from_config(config)

            # Use Docker probe to discover tools
            docker_probe = DockerProbe()
            result = docker_probe.discover_tools_from_image(
                docker_image,
                server_args=None,  # Let the probe handle default args
                env_vars=env_vars,
            )

            if result:
                result["template_name"] = template_name
                logger.info(
                    "Successfully discovered tools via HTTP Docker for %s",
                    template_name,
                )
                return result
            else:
                logger.debug("HTTP Docker discovery failed for %s", template_name)
                return None

        except ImportError:
            logger.warning("DockerProbe not available for %s", template_name)
            return None
        except Exception as e:
            logger.debug("HTTP Docker discovery error for %s: %s", template_name, e)
            return None
        except Exception as e:
            logger.debug("Docker discovery error for %s: %s", template_name, e)
            return None

    def _try_http_endpoints(
        self, template_name: str, config: Dict[str, Any], base_url: str
    ) -> Optional[Dict[str, Any]]:
        """Try to discover tools using HTTP endpoints."""
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
                            "discovery_method": "dynamic_http",
                            "timestamp": time.time(),
                            "template_name": template_name,
                            "source_endpoint": url,
                        }

            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.debug(
                    "Failed to probe %s for %s: %s", endpoint, template_name, e
                )
                continue

        logger.debug("No responsive HTTP endpoints found for %s", template_name)
        return None

    def _extract_env_vars_from_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Extract environment variables from template config schema."""
        env_vars = {}

        # Get existing env_vars if any
        if "env_vars" in config:
            env_vars.update(config["env_vars"])

        # Extract from config schema properties with env_mapping
        config_schema = config.get("config_schema", {})
        properties = config_schema.get("properties", {})

        for prop_name, prop_config in properties.items():
            env_mapping = prop_config.get("env_mapping")
            if env_mapping and "default" in prop_config:
                env_vars[env_mapping] = str(prop_config["default"])

        return env_vars

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

    def _has_valid_credentials(
        self, template_name: str, config: Dict[str, Any]
    ) -> bool:
        """Check if template has valid credentials for dynamic discovery."""
        # Get user config and environment variables
        user_config = config.get("user_config", {})
        env_vars = config.get("env_vars", {})

        # Get config schema to understand what credentials this template expects
        config_schema = config.get("config_schema", {})
        properties = config_schema.get("properties", {})

        # If we have a config schema, validate against it (schema-based validation)
        if properties:
            # Check if any expected credential properties have valid values
            for prop_name, prop_config in properties.items():
                if any(
                    keyword in prop_name.lower()
                    for keyword in ["token", "key", "secret", "password", "email"]
                ):
                    # Check in user_config
                    if prop_name in user_config:
                        value = user_config[prop_name]
                        if value and str(value).strip() and str(value).strip() != "":
                            return True

                    # Check in env_vars using env_mapping
                    env_mapping = prop_config.get("env_mapping", prop_name.upper())
                    if env_mapping in env_vars:
                        value = env_vars[env_mapping]
                        if value and str(value).strip() and str(value).strip() != "":
                            return True

            return False

        # No config schema - be conservative and only check for very generic credentials
        # This avoids assuming that any random token is valid for any template

        # Check for very generic tokens in env_vars (avoid template-specific ones)
        for key, value in env_vars.items():
            # Only accept very generic credential names
            if key.upper() in [
                "API_TOKEN",
                "ACCESS_TOKEN",
                "AUTH_TOKEN",
                "API_KEY",
                "SECRET",
            ]:
                if value and str(value).strip() and str(value).strip() != "":
                    return True

        # Check for generic credentials in user_config
        for key, value in user_config.items():
            # Only accept very generic credential names
            if key.lower() in ["token", "api_token", "access_token", "key", "api_key"]:
                if value and str(value).strip() and str(value).strip() != "":
                    return True

        return False

    def _add_dummy_credentials(
        self, template_name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add dummy/placeholder credentials for tool discovery purposes based on config schema."""
        config_with_dummies = config.copy()

        # Get or create env_vars section
        env_vars = config_with_dummies.get("env_vars", {})

        # Get config schema to understand what credentials are needed
        config_schema = config.get("config_schema", {})
        properties = config_schema.get("properties", {})
        required = config_schema.get("required", [])

        # Add dummy values for required properties that look like credentials
        for prop_name in required:
            prop_config = properties.get(prop_name, {})
            env_mapping = prop_config.get("env_mapping", prop_name.upper())

            # Skip if already has a value
            if env_vars.get(env_mapping) or config.get(prop_name):
                continue

            # Generate dummy value based on property name/type
            if any(
                keyword in prop_name.lower()
                for keyword in ["token", "key", "secret", "password"]
            ):
                env_vars[env_mapping] = (
                    f"dummy-{prop_name.lower().replace('_', '-')}-for-discovery"
                )
            elif any(keyword in prop_name.lower() for keyword in ["email"]):
                env_vars[env_mapping] = "dummy@example.com"
            elif any(
                keyword in prop_name.lower() for keyword in ["subdomain", "domain"]
            ):
                env_vars[env_mapping] = "dummy-subdomain"
            elif any(keyword in prop_name.lower() for keyword in ["url", "endpoint"]):
                env_vars[env_mapping] = "https://dummy-endpoint.example.com"
            elif any(keyword in prop_name.lower() for keyword in ["username", "user"]):
                env_vars[env_mapping] = "dummy-user"
            else:
                # Generic dummy value
                env_vars[env_mapping] = f"dummy-{prop_name.lower().replace('_', '-')}"

            logger.debug(f"Added dummy {env_mapping} for tool discovery")

        # Also add dummy values for non-required credential-looking properties
        for prop_name, prop_config in properties.items():
            if prop_name in required:
                continue  # Already handled above

            env_mapping = prop_config.get("env_mapping", prop_name.upper())

            # Skip if already has a value
            if env_vars.get(env_mapping) or config.get(prop_name):
                continue

            # Only add if it looks like a credential
            if any(
                keyword in prop_name.lower()
                for keyword in ["token", "key", "secret", "password"]
            ):
                env_vars[env_mapping] = (
                    f"dummy-{prop_name.lower().replace('_', '-')}-for-discovery"
                )
                logger.debug(f"Added dummy {env_mapping} for tool discovery")

        config_with_dummies["env_vars"] = env_vars
        return config_with_dummies

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
