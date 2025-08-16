"""
Load Balancer for MCP Gateway

Provides load balancing strategies for HTTP servers and connection pooling for stdio servers.
"""

import asyncio
import logging
import random
import time
from typing import Any, Dict, List, Optional, Union
from itertools import cycle

logger = logging.getLogger(__name__)


class LoadBalancer:
    """
    Load balancer for MCP servers.
    
    Supports different strategies for HTTP and stdio servers.
    """
    
    def __init__(self):
        """Initialize load balancer."""
        self.http_balancers: Dict[str, 'HTTPLoadBalancer'] = {}
        self.stdio_pools: Dict[str, 'StdioConnectionPool'] = {}
    
    def get_http_balancer(self, server_id: str, instances: List[Dict[str, Any]], 
                         strategy: str = "round_robin") -> 'HTTPLoadBalancer':
        """
        Get or create HTTP load balancer for a server.
        
        Args:
            server_id: Server identifier
            instances: List of server instances with endpoints
            strategy: Load balancing strategy
            
        Returns:
            HTTP load balancer instance
        """
        if server_id not in self.http_balancers:
            self.http_balancers[server_id] = HTTPLoadBalancer(instances, strategy)
        else:
            self.http_balancers[server_id].update_instances(instances)
        
        return self.http_balancers[server_id]
    
    def get_stdio_pool(self, server_id: str, config: Dict[str, Any]) -> 'StdioConnectionPool':
        """
        Get or create stdio connection pool for a server.
        
        Args:
            server_id: Server identifier
            config: Server configuration
            
        Returns:
            Stdio connection pool instance
        """
        if server_id not in self.stdio_pools:
            pool_size = config.get('pool_size', 3)
            self.stdio_pools[server_id] = StdioConnectionPool(config, pool_size)
        
        return self.stdio_pools[server_id]
    
    async def cleanup(self) -> None:
        """Clean up all load balancers and connection pools."""
        # Clean up stdio pools
        cleanup_tasks = []
        for pool in self.stdio_pools.values():
            cleanup_tasks.append(pool.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.http_balancers.clear()
        self.stdio_pools.clear()
        logger.info("Load balancer cleanup completed")


class HTTPLoadBalancer:
    """
    Load balancer for HTTP MCP servers.
    """
    
    def __init__(self, instances: List[Dict[str, Any]], strategy: str = "round_robin"):
        """
        Initialize HTTP load balancer.
        
        Args:
            instances: List of server instances
            strategy: Load balancing strategy
        """
        self.instances = instances
        self.strategy = strategy
        self.healthy_instances = instances.copy()
        self._iterator = cycle(self.healthy_instances) if self.healthy_instances else cycle([])
        self.health_check_times: Dict[str, float] = {}
    
    def get_next_instance(self) -> Optional[Dict[str, Any]]:
        """
        Get next instance according to load balancing strategy.
        
        Returns:
            Next instance to use or None if no healthy instances
        """
        if not self.healthy_instances:
            return None
        
        if self.strategy == "round_robin":
            return next(self._iterator)
        elif self.strategy == "random":
            return random.choice(self.healthy_instances)
        else:
            # Default to round robin
            return next(self._iterator)
    
    def mark_unhealthy(self, endpoint: str) -> None:
        """
        Mark an instance as unhealthy.
        
        Args:
            endpoint: Endpoint URL of the unhealthy instance
        """
        self.healthy_instances = [
            inst for inst in self.healthy_instances 
            if inst.get('endpoint') != endpoint
        ]
        self._iterator = cycle(self.healthy_instances) if self.healthy_instances else cycle([])
        logger.warning("Marked instance as unhealthy: %s", endpoint)
    
    def mark_healthy(self, endpoint: str) -> None:
        """
        Mark an instance as healthy.
        
        Args:
            endpoint: Endpoint URL of the healthy instance
        """
        # Find the instance in the original list
        for instance in self.instances:
            if instance.get('endpoint') == endpoint:
                if instance not in self.healthy_instances:
                    self.healthy_instances.append(instance)
                    self._iterator = cycle(self.healthy_instances)
                    logger.info("Marked instance as healthy: %s", endpoint)
                break
    
    def update_instances(self, instances: List[Dict[str, Any]]) -> None:
        """
        Update the list of instances.
        
        Args:
            instances: New list of instances
        """
        self.instances = instances
        # Keep only healthy instances that are still in the new list
        self.healthy_instances = [
            inst for inst in self.healthy_instances 
            if inst in instances
        ]
        # Add new instances as healthy by default
        for instance in instances:
            if instance not in self.healthy_instances:
                self.healthy_instances.append(instance)
        
        self._iterator = cycle(self.healthy_instances) if self.healthy_instances else cycle([])
        logger.info("Updated instances for HTTP load balancer")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics."""
        return {
            "total_instances": len(self.instances),
            "healthy_instances": len(self.healthy_instances),
            "strategy": self.strategy,
            "instance_endpoints": [inst.get('endpoint') for inst in self.healthy_instances]
        }


class StdioConnectionPool:
    """
    Connection pool for stdio MCP servers.
    """
    
    def __init__(self, config: Dict[str, Any], pool_size: int = 3):
        """
        Initialize stdio connection pool.
        
        Args:
            config: Server configuration
            pool_size: Maximum number of connections in pool
        """
        self.config = config
        self.pool_size = pool_size
        self.connections: List['StdioConnection'] = []
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.busy_connections: List['StdioConnection'] = []
        self._lock = asyncio.Lock()
    
    async def get_connection(self) -> Optional['StdioConnection']:
        """
        Get an available connection from the pool.
        
        Returns:
            Available connection or None if pool is exhausted
        """
        async with self._lock:
            # Try to get an existing available connection
            if not self.available_connections.empty():
                connection = await self.available_connections.get()
                self.busy_connections.append(connection)
                return connection
            
            # Create new connection if pool not at capacity
            if len(self.connections) < self.pool_size:
                connection = await self._create_connection()
                if connection:
                    self.connections.append(connection)
                    self.busy_connections.append(connection)
                    return connection
            
            # Pool exhausted, wait for a connection to become available
            try:
                connection = await asyncio.wait_for(
                    self.available_connections.get(), 
                    timeout=30.0
                )
                self.busy_connections.append(connection)
                return connection
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for stdio connection")
                return None
    
    async def return_connection(self, connection: 'StdioConnection') -> None:
        """
        Return a connection to the pool.
        
        Args:
            connection: Connection to return
        """
        async with self._lock:
            if connection in self.busy_connections:
                self.busy_connections.remove(connection)
                
                # Check if connection is still healthy
                if connection.is_healthy():
                    await self.available_connections.put(connection)
                else:
                    # Remove unhealthy connection
                    if connection in self.connections:
                        self.connections.remove(connection)
                    await connection.cleanup()
                    logger.info("Removed unhealthy stdio connection")
    
    async def _create_connection(self) -> Optional['StdioConnection']:
        """
        Create a new stdio connection.
        
        Returns:
            New connection or None if creation failed
        """
        try:
            # Import here to avoid circular imports
            from mcp_template.core.mcp_connection import MCPConnection
            
            connection = StdioConnection(self.config)
            if await connection.connect():
                logger.info("Created new stdio connection")
                return connection
            else:
                logger.error("Failed to create stdio connection")
                return None
        except Exception as e:
            logger.error("Error creating stdio connection: %s", e)
            return None
    
    async def cleanup(self) -> None:
        """Clean up all connections in the pool."""
        async with self._lock:
            cleanup_tasks = []
            for connection in self.connections:
                cleanup_tasks.append(connection.cleanup())
            
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            self.connections.clear()
            self.busy_connections.clear()
            
            # Clear the queue
            while not self.available_connections.empty():
                try:
                    self.available_connections.get_nowait()
                except asyncio.QueueEmpty:
                    break
            
            logger.info("Stdio connection pool cleanup completed")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "pool_size": self.pool_size,
            "total_connections": len(self.connections),
            "available_connections": self.available_connections.qsize(),
            "busy_connections": len(self.busy_connections)
        }


class StdioConnection:
    """
    Wrapper for stdio MCP connection with health tracking.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize stdio connection wrapper.
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.mcp_connection = None
        self.created_at = time.time()
        self.last_used = time.time()
        self.error_count = 0
        self.max_errors = 5
    
    async def connect(self) -> bool:
        """
        Establish the MCP connection.
        
        Returns:
            True if connection successful
        """
        try:
            # Import here to avoid circular imports
            from mcp_template.core.mcp_connection import MCPConnection
            
            self.mcp_connection = MCPConnection()
            command = self.config['command']
            working_dir = self.config.get('working_dir')
            env_vars = self.config.get('env_vars')
            
            success = await self.mcp_connection.connect_stdio(
                command=command,
                working_dir=working_dir,
                env_vars=env_vars
            )
            
            if success:
                self.last_used = time.time()
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            logger.error("Error connecting stdio MCP: %s", e)
            self.error_count += 1
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool response or None if failed
        """
        if not self.mcp_connection:
            return None
        
        try:
            self.last_used = time.time()
            result = await self.mcp_connection.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error("Error calling tool %s: %s", tool_name, e)
            self.error_count += 1
            return None
    
    async def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """
        List available tools.
        
        Returns:
            List of tools or None if failed
        """
        if not self.mcp_connection:
            return None
        
        try:
            self.last_used = time.time()
            result = await self.mcp_connection.list_tools()
            return result
        except Exception as e:
            logger.error("Error listing tools: %s", e)
            self.error_count += 1
            return None
    
    def is_healthy(self) -> bool:
        """
        Check if connection is healthy.
        
        Returns:
            True if connection is healthy
        """
        # Connection is unhealthy if too many errors or too old
        max_age = 3600  # 1 hour
        age = time.time() - self.created_at
        
        return (
            self.error_count < self.max_errors and
            age < max_age and
            self.mcp_connection is not None
        )
    
    async def cleanup(self) -> None:
        """Clean up the connection."""
        if self.mcp_connection and hasattr(self.mcp_connection, 'process'):
            if self.mcp_connection.process:
                try:
                    self.mcp_connection.process.terminate()
                    await asyncio.wait_for(self.mcp_connection.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    if self.mcp_connection.process:
                        self.mcp_connection.process.kill()
                except Exception as e:
                    logger.error("Error cleaning up stdio connection: %s", e)
        
        self.mcp_connection = None