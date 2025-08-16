"""
Server Registry for MCP Gateway

Manages configuration and metadata for available MCP servers.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml

logger = logging.getLogger(__name__)


class ServerRegistry:
    """
    Manages MCP server registry configuration.
    
    Supports loading from JSON/YAML files and dynamic discovery
    from the existing template system.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize server registry.
        
        Args:
            config_path: Path to registry configuration file
        """
        self.config_path = Path(config_path) if config_path else None
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.gateway_config: Dict[str, Any] = {}
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from configuration file or create default."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() in ['.yml', '.yaml']:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)
                
                self.servers = data.get('servers', {})
                self.gateway_config = data.get('gateway', {})
                
                logger.info("Loaded registry with %d servers from %s", 
                           len(self.servers), self.config_path)
            except Exception as e:
                logger.error("Failed to load registry from %s: %s", self.config_path, e)
                self._create_default_registry()
        else:
            self._create_default_registry()
    
    def _create_default_registry(self) -> None:
        """Create a default registry configuration."""
        self.servers = {
            "demo": {
                "type": "template",
                "template_name": "demo",
                "instances": 1,
                "config": {"hello_from": "Gateway"}
            }
        }
        self.gateway_config = {
            "host": "0.0.0.0",
            "port": 8000,
            "reload_registry": True,
            "health_check_interval": 30
        }
        logger.info("Created default registry with demo server")
    
    def get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific server.
        
        Args:
            server_id: Server identifier
            
        Returns:
            Server configuration or None if not found
        """
        return self.servers.get(server_id)
    
    def list_servers(self) -> List[str]:
        """
        List all available server IDs.
        
        Returns:
            List of server identifiers
        """
        return list(self.servers.keys())
    
    def add_server(self, server_id: str, config: Dict[str, Any]) -> None:
        """
        Add or update a server configuration.
        
        Args:
            server_id: Server identifier
            config: Server configuration
        """
        self.servers[server_id] = config
        logger.info("Added/updated server: %s", server_id)
    
    def remove_server(self, server_id: str) -> bool:
        """
        Remove a server from the registry.
        
        Args:
            server_id: Server identifier
            
        Returns:
            True if server was removed, False if not found
        """
        if server_id in self.servers:
            del self.servers[server_id]
            logger.info("Removed server: %s", server_id)
            return True
        return False
    
    def reload(self) -> None:
        """Reload registry from configuration file."""
        if self.config_path:
            logger.info("Reloading registry from %s", self.config_path)
            self._load_registry()
        else:
            logger.warning("No config path set, cannot reload registry")
    
    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Save registry to file.
        
        Args:
            path: File path to save to (uses instance config_path if not provided)
        """
        save_path = Path(path) if path else self.config_path
        if not save_path:
            raise ValueError("No save path provided and no config_path set")
        
        data = {
            "servers": self.servers,
            "gateway": self.gateway_config
        }
        
        with open(save_path, 'w', encoding='utf-8') as f:
            if save_path.suffix.lower() in ['.yml', '.yaml']:
                yaml.safe_dump(data, f, default_flow_style=False, indent=2)
            else:
                json.dump(data, f, indent=2)
        
        logger.info("Saved registry to %s", save_path)
    
    def validate_server_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate a server configuration.
        
        Args:
            config: Server configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        server_type = config.get('type')
        if not server_type:
            errors.append("Missing 'type' field")
            return errors
        
        if server_type == 'http':
            instances = config.get('instances', [])
            if not instances:
                errors.append("HTTP servers must have at least one instance")
            else:
                for i, instance in enumerate(instances):
                    if not isinstance(instance, dict) or 'endpoint' not in instance:
                        errors.append(f"Instance {i} missing 'endpoint' field")
        
        elif server_type == 'stdio':
            if 'command' not in config:
                errors.append("stdio servers must have 'command' field")
            elif not isinstance(config['command'], list):
                errors.append("'command' must be a list")
        
        elif server_type == 'template':
            if 'template_name' not in config:
                errors.append("Template servers must have 'template_name' field")
        
        else:
            errors.append(f"Unknown server type: {server_type}")
        
        return errors
    
    def get_gateway_config(self) -> Dict[str, Any]:
        """Get gateway configuration."""
        return self.gateway_config.copy()
    
    def update_gateway_config(self, config: Dict[str, Any]) -> None:
        """Update gateway configuration."""
        self.gateway_config.update(config)
        logger.info("Updated gateway configuration")